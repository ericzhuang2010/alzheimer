#!/usr/bin/env node

/** Append Finding 1–6 slides from the 2026-09-23 deck to the HSR deck. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

const SKILL_DIR =
  "/Users/rzhuang/.codex/plugins/cache/openai-primary-runtime/presentations/26.923.10815/skills/presentations";
const WORKSPACE_DIR = "/Users/rzhuang/Documents/VscodeProjects/alzheimer";
const SOURCE = path.join(
  WORKSPACE_DIR,
  "docs/presentations/09232026/09232026_alzheimer_sex_apoe.pptx",
);
const DESTINATION = path.join(
  WORKSPACE_DIR,
  "docs/presentations/HSR_second_presentation.pptx",
);
const RUN_DIR = path.join(
  WORKSPACE_DIR,
  "results/presentations/09242026_append_findings_1_6",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const OUTPUT_DIR = path.join(RUN_DIR, "output");
const DRAFT = path.join(BUILD_DIR, "HSR_second_presentation_draft_v2.pptx");
const FINAL_PPTX = path.join(
  OUTPUT_DIR,
  "HSR_second_presentation_with_findings_1_6_v3.pptx",
);
const APPLESCRIPT = path.join(BUILD_DIR, "append_findings.applescript");

const EXPECTED_SOURCE_SHA256 =
  "39c932512c206d2f3545194f653ec8defe4c25eb0b3a3a65e9e813c25d6bfe27";
const EXPECTED_DESTINATION_SHA256 =
  "475b0f6b0f202e7c84bc1c4bf05dea9d649a4d9b148e95281bdc036abe1ba34d";
const SOURCE_FIRST_SLIDE = 58;
const SOURCE_LAST_SLIDE = 94;
const ORIGINAL_DESTINATION_SLIDES = 13;
const APPENDED_SLIDES = SOURCE_LAST_SLIDE - SOURCE_FIRST_SLIDE + 1;
const FINAL_SLIDE_COUNT = ORIGINAL_DESTINATION_SLIDES + APPENDED_SLIDES;
const FINDING_OPENING_SLIDES = [14, 20, 27, 33, 39, 45];
const EXPECTED_OPENING_TITLES = [
  "FINDING 1",
  "FINDING 2",
  "FINDING 3",
  "FINDING 4",
  "FINDING 5",
  "FINDING 6",
];

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
    ...options,
  });
  if (result.status !== 0) {
    throw new Error(
      [result.stderr, result.stdout, `${command} exited with ${result.status}`]
        .filter(Boolean)
        .join("\n")
        .trim(),
    );
  }
  return result.stdout.trim();
}

function slidePartCount(pptxPath) {
  const names = run("unzip", ["-Z1", pptxPath]).split(/\r?\n/);
  return names.filter((name) => /^ppt\/slides\/slide\d+\.xml$/.test(name)).length;
}

function slidesFromPresentation(presentation) {
  if (Array.isArray(presentation.slides?.items)) return presentation.slides.items;
  if (
    Number.isInteger(presentation.slides?.count) &&
    typeof presentation.slides.getItem === "function"
  ) {
    return Array.from(
      { length: presentation.slides.count },
      (_, index) => presentation.slides.getItem(index),
    );
  }
  throw new Error("Could not enumerate presentation slides");
}

function normalizedColor(fill) {
  if (typeof fill === "string") return fill.toUpperCase();
  const candidates = [
    fill?.color,
    fill?.foregroundColor,
    fill?.rgb,
    fill?.value,
  ];
  const value = candidates.find((item) => typeof item === "string");
  return value?.toUpperCase() ?? "";
}

async function main() {
  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  if (await fs.stat(FINAL_PPTX).catch(() => undefined)) {
    throw new Error(`Output already exists: ${FINAL_PPTX}`);
  }

  const [sourceBuffer, destinationBuffer] = await Promise.all([
    fs.readFile(SOURCE),
    fs.readFile(DESTINATION),
  ]);
  const sourceHash = sha256(sourceBuffer);
  const destinationHash = sha256(destinationBuffer);
  if (sourceHash !== EXPECTED_SOURCE_SHA256) {
    throw new Error(`Source deck changed: ${sourceHash}`);
  }
  if (destinationHash !== EXPECTED_DESTINATION_SHA256) {
    throw new Error(`Destination deck changed: ${destinationHash}`);
  }

  const existingDraft = await fs.stat(DRAFT).catch(() => undefined);
  if (!existingDraft || slidePartCount(DRAFT) !== FINAL_SLIDE_COUNT) {
    await fs.writeFile(DRAFT, destinationBuffer);
    const appleScript = `on run argv
  set sourcePath to item 1 of argv
  set targetPath to item 2 of argv
  tell application "Microsoft PowerPoint"
    activate
    set targetName to "HSR_second_presentation_draft_v2.pptx"
    set sourceName to "09232026_alzheimer_sex_apoe.pptx"
    if not (exists presentation targetName) then
      open (POSIX file targetPath)
    end if
    if not (exists presentation sourceName) then
      open (POSIX file sourcePath)
    end if
    set sourceCount to count of slides of presentation sourceName
    set targetCount to count of slides of presentation targetName
    if sourceCount is not 154 then error "Unexpected source slide count: " & sourceCount
    if targetCount is not ${ORIGINAL_DESTINATION_SLIDES} then error "Unexpected destination slide count: " & targetCount
    repeat with sourceIndex from ${SOURCE_FIRST_SLIDE} to ${SOURCE_LAST_SLIDE}
      copy object slide sourceIndex of presentation sourceName
      paste object presentation targetName
    end repeat
    set finalCount to count of slides of presentation targetName
    if finalCount is not ${FINAL_SLIDE_COUNT} then error "Unexpected final slide count: " & finalCount
    save presentation targetName
    return finalCount as text
  end tell
end run
`;
    await fs.writeFile(APPLESCRIPT, appleScript, "utf8");
    const reportedCount = run("osascript", [APPLESCRIPT, SOURCE, DRAFT]);
    if (reportedCount !== String(FINAL_SLIDE_COUNT)) {
      throw new Error(`PowerPoint reported unexpected slide count: ${reportedCount}`);
    }
  }

  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("Source deck changed during the append operation");
  }
  if (sha256(await fs.readFile(DESTINATION)) !== destinationHash) {
    throw new Error("Destination deck changed during the append operation");
  }

  const { importRuntimeModule } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href
  );
  const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");
  const JSZipModule = await importRuntimeModule("jszip");
  const JSZip = JSZipModule.default ?? JSZipModule;
  const draftPresentation = await PresentationFile.importPptx(await FileBlob.load(DRAFT));
  const draftSlides = slidesFromPresentation(draftPresentation);
  if (draftSlides.length !== FINAL_SLIDE_COUNT) {
    throw new Error(`Expected ${FINAL_SLIDE_COUNT} slides, found ${draftSlides.length}`);
  }

  const inspection = await draftPresentation.inspect({
    kind: "slide",
    maxChars: 500000,
  });
  const records = inspection.ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  const slideRecords = new Map(
    records
      .filter((record) => record.kind === "slide")
      .map((record) => [record.slideIndex + 1, record]),
  );
  for (let index = 0; index < FINDING_OPENING_SLIDES.length; index += 1) {
    const slideNumber = FINDING_OPENING_SLIDES[index];
    const record = slideRecords.get(slideNumber);
    if (!record) throw new Error(`Missing Finding opening slide ${slideNumber}`);
    if (!String(record.title).toUpperCase().startsWith(EXPECTED_OPENING_TITLES[index])) {
      throw new Error(`Unexpected Finding opening title on slide ${slideNumber}: ${record.title}`);
    }
    const slide = draftSlides[slideNumber - 1];
    slide.background.fill = "#0F233D";
    const color = normalizedColor(slide.background.fill);
    if (color && color !== "#0F233D") {
      throw new Error(`Could not restore dark-blue background on slide ${slideNumber}`);
    }
  }
  for (let slideNumber = ORIGINAL_DESTINATION_SLIDES + 1; slideNumber <= FINAL_SLIDE_COUNT; slideNumber += 1) {
    draftSlides[slideNumber - 1].background.fill = FINDING_OPENING_SLIDES.includes(slideNumber)
      ? "#0F233D"
      : "#F7F9FC";
  }

  const chartInspection = await draftPresentation.inspect({
    kind: "chart",
    maxChars: 50000,
  });
  const slide12Charts = chartInspection.ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .filter((record) => record.kind === "chart" && record.slideIndex === 11);
  if (slide12Charts.length !== 1) {
    throw new Error(`Expected one native chart on slide 12, found ${slide12Charts.length}`);
  }

  const correctedCandidate = path.join(
    BUILD_DIR,
    "HSR_second_presentation_corrected_candidate.pptx",
  );
  await (await PresentationFile.exportPptx(draftPresentation)).save(correctedCandidate);
  const candidateZip = await JSZip.loadAsync(await fs.readFile(correctedCandidate));
  const chartPartPath = "ppt/slides/charts/chart1.xml";
  const chartPart = candidateZip.file(chartPartPath);
  if (!chartPart) throw new Error("Slide 12 chart part is missing");
  let chartXml = await chartPart.async("string");
  let stringReferenceCount = 0;
  let numericReferenceCount = 0;
  chartXml = chartXml.replace(
    /<c:strRef>\s*<c:f>[\s\S]*?<\/c:f>\s*<c:strCache>([\s\S]*?)<\/c:strCache>\s*<\/c:strRef>/g,
    (_match, cache) => {
      stringReferenceCount += 1;
      return `<c:strLit>${cache}</c:strLit>`;
    },
  );
  chartXml = chartXml.replace(
    /<c:numRef>\s*<c:f>[\s\S]*?<\/c:f>\s*<c:numCache>([\s\S]*?)<\/c:numCache>\s*<\/c:numRef>/g,
    (_match, cache) => {
      numericReferenceCount += 1;
      return `<c:numLit>${cache}</c:numLit>`;
    },
  );
  if (stringReferenceCount !== 2 || numericReferenceCount !== 2) {
    throw new Error(
      `Unexpected chart references: ${stringReferenceCount} string and ${numericReferenceCount} numeric`,
    );
  }
  if (/<c:(?:strRef|numRef|f)>/.test(chartXml)) {
    throw new Error("Chart still contains worksheet references after literal-data conversion");
  }
  candidateZip.file(chartPartPath, chartXml);
  const literalChartCandidate = path.join(
    BUILD_DIR,
    "HSR_second_presentation_literal_chart_candidate.pptx",
  );
  await fs.writeFile(
    literalChartCandidate,
    await candidateZip.generateAsync({
      type: "nodebuffer",
      compression: "DEFLATE",
      compressionOptions: { level: 6 },
    }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  await finalizePresentation({
    explicitTotalSlideCount: FINAL_SLIDE_COUNT,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [12],
    nativeChartTargetApplication: "powerpoint",
    workspaceDir: WORKSPACE_DIR,
    candidatePath: literalChartCandidate,
    finalPath: FINAL_PPTX,
    pythonExecutable:
      "/Users/rzhuang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
    integrityValidatorPath: path.join(
      SKILL_DIR,
      "container_tools/inspect_presentation_package_integrity.py",
    ),
    layoutValidatorPath: path.join(
      SKILL_DIR,
      "container_tools/inspect_presentation_layout_geometry.py",
    ),
    layoutArgs: [
      "--expected-slide-size-emu",
      "12192000,6858000",
      "--validate-bullet-geometry",
      "--validate-heading-fit",
    ],
    fontPolicy: {
      basis: "reference",
      families: ["Arial"],
      referencePath: DESTINATION,
      referenceSha256: destinationHash,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD_DIR, "validation_v3.json"),
  });

  const finalPresentation = await PresentationFile.importPptx(
    await FileBlob.load(FINAL_PPTX),
  );
  const finalSlides = slidesFromPresentation(finalPresentation);
  if (finalSlides.length !== FINAL_SLIDE_COUNT) {
    throw new Error(`Final deck has ${finalSlides.length} slides`);
  }
  const finalInspection = await finalPresentation.inspect({
    kind: "slide",
    maxChars: 50000,
  });
  const finalSlideRecords = finalInspection.ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .filter((record) => record.kind === "slide");
  for (const slideNumber of FINDING_OPENING_SLIDES) {
    const record = finalSlideRecords.find(
      (item) => item.slideIndex + 1 === slideNumber,
    );
    if (record?.backgroundColor !== "rgba(15,35,61,1)") {
      throw new Error(`Final slide ${slideNumber} is not dark blue`);
    }
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        destination: DESTINATION,
        output: FINAL_PPTX,
        sourceSlides: `${SOURCE_FIRST_SLIDE}-${SOURCE_LAST_SLIDE}`,
        appendedSlides: APPENDED_SLIDES,
        finalSlideCount: FINAL_SLIDE_COUNT,
        findingOpeningSlides: FINDING_OPENING_SLIDES,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exitCode = 1;
});
