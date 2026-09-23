#!/usr/bin/env node

/** Mark Findings 7, 10, and 17 as not sex/APOE-specific on their divider slides. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const SKILL_DIR =
  "/Users/rzhuang/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations";
const WORKSPACE_DIR = "/Users/rzhuang/Documents/VscodeProjects/alzheimer";
const SOURCE = path.join(
  WORKSPACE_DIR,
  "docs/presentations/09162026/09162026_sex_apoe_kda_fine_broad.pptx",
);
const BUILD_DIR = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_not_sex_apoe_specific_20260921/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_not_sex_apoe_specific_20260921/output/09162026_sex_apoe_kda_fine_broad_scope_labels_20260921.pptx",
);
const EXPECTED_SLIDES = 155;
const EXPECTED_SOURCE_SHA256 =
  "32dd7b910450ce3daa55d9d6d70da77e921cdac94f29120c966276f43c3136d3";
const LABEL = "Not sex/APOE-specific";
const TARGET_SLIDES = [90, 108, 150];

const LABEL_STYLE = {
  typeface: "Arial",
  fontSize: 18,
  bold: true,
  color: "#E6A700",
  alignment: "left",
  verticalAlignment: "top",
  autoFit: "shrinkText",
  wrap: "square",
  insets: { top: 0, right: 0, bottom: 0, left: 0 },
};

const NOTES_BY_SLIDE = new Map([
  [
    90,
    [
      "Teaching goal: Introduce Finding 7 and clarify that it is not sex/APOE-specific.",
      "",
      "Walk through: RPL11, RPS15, and related cytosolic-ribosome genes recur near nuclear-encoded OXPHOS query genes. The ribosome module appears across all six sex/APOE strata rather than being confined to one group. The label on this slide therefore identifies Finding 7 as a cross-group network finding.",
      "",
      "Scientific boundary: Cross-group recurrence does not prove an identical effect in every group or independent replication, because stratified KDA calls can share donors. KDA also does not establish that the ribosome genes causally regulate OXPHOS genes.",
      "",
      "Transition: State the recurrent ribosome-to-OXPHOS finding in plain language.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 7; https://doi.org/10.1523/JNEUROSCI.3040-05.2005; https://doi.org/10.1128/MCB.23.23.8902-8912.2003.",
    ].join("\n"),
  ],
  [
    108,
    [
      "Teaching goal: Introduce Finding 10 and clarify that it is not sex/APOE-specific.",
      "",
      "Walk through: SELENOM repeatedly sits near decreased mitochondrial-translation genes in neuronal KDA queries. It was returned from KDA calls across seven categories and all six sex/APOE strata. The label on this slide therefore identifies Finding 10 as a broadly recurrent network finding rather than a subgroup-specific result.",
      "",
      "Scientific boundary: Recurrence across groups does not establish an identical effect in every group, independent replication, or causal regulation of mitochondrial translation by SELENOM.",
      "",
      "Transition: Explain the ER redox and mitochondrial protein-production connection in plain language.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 10; https://doi.org/10.1074/jbc.M511386200; https://doi.org/10.3892/ijmm_00000211; https://doi.org/10.3390/ijms14034385.",
    ].join("\n"),
  ],
  [
    150,
    [
      "Teaching goal: Introduce Finding 17 and clarify that it is not a sex/APOE-specific biological finding.",
      "",
      "Walk through: Finding 17 compares reproducibility across ROSMAP and SEA-AD. Mitochondrial gene-set patterns agree more strongly than exact driver identities across the two cohort-specific network analyses. Although individual comparisons retain their sex/APOE and cell contexts, the overall finding concerns cross-cohort support across contexts and is not assigned to one sex/APOE group.",
      "",
      "Scientific boundary: Cross-context recurrence does not confirm the original sex/APOE context, and similar mitochondrial gene sets do not prove a shared upstream driver. The comparison is analytical rather than a subgroup-specific mechanism.",
      "",
      "Transition: Explain the difference between exact-context driver matching and broader gene-set agreement.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 17.",
    ].join("\n"),
  ],
]);

const EXPECTED_TITLES = new Map([
  [90, "FINDING 7"],
  [108, "FINDING 10"],
  [150, "FINDING 17"],
]);

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

function parseNdjson(ndjson) {
  return (ndjson || "")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

async function blobBuffer(blob) {
  return Buffer.from(await blob.arrayBuffer());
}

function relationshipAttributes(tag) {
  return Object.fromEntries(
    [...tag.matchAll(/([A-Za-z:]+)="([^"]*)"/g)].map((match) => [match[1], match[2]]),
  );
}

async function visibleSlideParts(zip) {
  const presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  const presentationRels = await zip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  if (!presentationXml || !presentationRels) {
    throw new Error("Presentation ordering metadata is missing");
  }
  const slideIds = [...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g)].map(
    (match) => match[1],
  );
  const relationships = [...presentationRels.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map(
    (match) => relationshipAttributes(match[0]),
  );
  return slideIds.map((relationshipId) => {
    const relation = relationships.find(
      (item) => item.Id === relationshipId && item.Type?.endsWith("/slide"),
    );
    if (!relation?.Target) {
      throw new Error(`Slide relationship ${relationshipId} was not found`);
    }
    return relation.Target.startsWith("/")
      ? relation.Target.slice(1)
      : path.posix.normalize(path.posix.join("ppt", relation.Target));
  });
}

async function notesPartForSlide(zip, slidePart) {
  const relsPath = path.posix.join(
    path.posix.dirname(slidePart),
    "_rels",
    `${path.posix.basename(slidePart)}.rels`,
  );
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing slide relationships: ${relsPath}`);
  const relationships = [...relsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map(
    (match) => relationshipAttributes(match[0]),
  );
  const relation = relationships.find((item) => item.Type?.endsWith("/notesSlide"));
  if (!relation?.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return relation.Target.startsWith("/")
    ? relation.Target.slice(1)
    : path.posix.normalize(path.posix.join(path.posix.dirname(slidePart), relation.Target));
}

function applyLabelStyle(shape) {
  shape.text = LABEL;
  shape.text.style = LABEL_STYLE;
}

async function main() {
  const sourceStat = await fs.stat(SOURCE).catch(() => undefined);
  if (!sourceStat?.isFile()) throw new Error(`Missing source deck: ${SOURCE}`);
  if (await fs.stat(FINAL_PPTX).catch(() => undefined)) {
    throw new Error(`Output already exists: ${FINAL_PPTX}`);
  }
  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });

  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceHash = sha256(sourceBuffer);
  if (sourceHash !== EXPECTED_SOURCE_SHA256) {
    throw new Error(`Source deck changed before the scope-label edit: ${sourceHash}`);
  }

  const { importRuntimeModule } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href
  );
  const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");
  const JSZipModule = await importRuntimeModule("jszip");
  const JSZip = JSZipModule.default ?? JSZipModule;
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const slides = slidesFromPresentation(presentation);
  if (slides.length !== EXPECTED_SLIDES) {
    throw new Error(`Expected ${EXPECTED_SLIDES} slides, found ${slides.length}`);
  }

  const slideSnapshot = await presentation.inspect({ kind: "slides", maxChars: 500000 });
  const slideRecords = new Map(
    parseNdjson(slideSnapshot.ndjson)
      .filter((record) => record.kind === "slide" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record]),
  );
  for (const [slideNumber, expectedTitle] of EXPECTED_TITLES) {
    if (slideRecords.get(slideNumber)?.title !== expectedTitle) {
      throw new Error(`Unexpected title on slide ${slideNumber}`);
    }
  }

  const textSnapshot = await presentation.inspect({
    kind: "textbox",
    include: "id,slide,name,text,textPreview,bbox",
    maxChars: 3000000,
  });
  const textRecords = parseNdjson(textSnapshot.ndjson).filter(
    (record) => record.kind === "textbox" && TARGET_SLIDES.includes(record.slide),
  );
  const subtitle108 = textRecords.find(
    (record) => record.slide === 108 && record.name === "TextBox 4",
  );
  const subtitle150 = textRecords.find(
    (record) => record.slide === 150 && record.name === "TextBox 4",
  );
  if (!subtitle108?.id || !subtitle150?.id) {
    throw new Error("Could not locate the existing divider subtitles");
  }
  if (textRecords.some((record) => record.slide === 90 && record.name === "TextBox 4")) {
    throw new Error("Slide 90 already contains the scope-label text box");
  }

  const beforePngs = new Map();
  for (const slideNumber of TARGET_SLIDES) {
    const png = await blobBuffer(
      await presentation.export({ slide: slides[slideNumber - 1], format: "png", scale: 1.5 }),
    );
    beforePngs.set(slideNumber, png);
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-before.png`), png);
  }

  const slide90Label = slides[89].shapes.add({
    geometry: "textbox",
    name: "TextBox 4",
    position: { left: 115.2, top: 259.2, width: 777.6, height: 96 },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  applyLabelStyle(slide90Label);
  applyLabelStyle(presentation.resolve(subtitle108.id));
  applyLabelStyle(presentation.resolve(subtitle150.id));

  for (const [slideNumber, revisedNotes] of NOTES_BY_SLIDE) {
    slides[slideNumber - 1].speakerNotes.textFrame.setText(revisedNotes);
    slides[slideNumber - 1].speakerNotes.setVisible(true);
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed during the scope-label edit");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const [sourceSlideParts, artifactSlideParts] = await Promise.all([
    visibleSlideParts(sourceZip),
    visibleSlideParts(artifactZip),
  ]);
  const expectedChangedParts = [];
  for (const slideNumber of TARGET_SLIDES) {
    const sourceSlidePart = sourceSlideParts[slideNumber - 1];
    const artifactSlidePart = artifactSlideParts[slideNumber - 1];
    const updatedSlideXml = await artifactZip.file(artifactSlidePart)?.async("string");
    if (!updatedSlideXml?.includes(LABEL)) {
      throw new Error(`Updated visible slide ${slideNumber} lacks the scope label`);
    }
    sourceZip.file(sourceSlidePart, updatedSlideXml);
    expectedChangedParts.push(sourceSlidePart);

    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const updatedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!updatedNotesXml?.includes("sex/APOE-specific")) {
      throw new Error(`Updated notes are missing for slide ${slideNumber}`);
    }
    sourceZip.file(sourceNotesPart, updatedNotesXml);
    expectedChangedParts.push(sourceNotesPart);
  }

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
    await sourceZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const validation = await finalizePresentation({
    explicitTotalSlideCount: EXPECTED_SLIDES,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [19],
    requiredEmbeddedWorkbookChartOwnerSlides: [19],
    nativeChartTargetApplication: "powerpoint",
    workspaceDir: WORKSPACE_DIR,
    candidatePath,
    finalPath: FINAL_PPTX,
    pythonExecutable:
      "/Users/rzhuang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12",
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
      referencePath: SOURCE,
      referenceSha256: sourceHash,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD_DIR, "scope_labels.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const finalTextSnapshot = await reopened.inspect({
    kind: "textbox",
    include: "id,slide,name,text,textPreview,bbox",
    maxChars: 3000000,
  });
  const finalLabels = parseNdjson(finalTextSnapshot.ndjson).filter(
    (record) =>
      record.kind === "textbox" &&
      TARGET_SLIDES.includes(record.slide) &&
      record.text === LABEL,
  );
  if (finalLabels.length !== 3) {
    throw new Error(`Expected three visible scope labels, found ${finalLabels.length}`);
  }
  const finalNotesSnapshot = await reopened.inspect({ kind: "notes", maxChars: 3000000 });
  const finalNotes = new Map(
    parseNdjson(finalNotesSnapshot.ndjson)
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text]),
  );
  for (const [slideNumber, expectedNotes] of NOTES_BY_SLIDE) {
    if (finalNotes.get(slideNumber)?.trim() !== expectedNotes.trim()) {
      throw new Error(`Final speaker notes do not match on slide ${slideNumber}`);
    }
    const finalPng = await blobBuffer(
      await reopened.export({
        slide: reopenedSlides[slideNumber - 1],
        format: "png",
        scale: 1.5,
      }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-final.png`), finalPng);
    if (sha256(finalPng) === sha256(beforePngs.get(slideNumber))) {
      throw new Error(`Visible slide ${slideNumber} did not change`);
    }
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const sourceFiles = Object.keys(originalZip.files)
    .filter((name) => !originalZip.files[name].dir)
    .sort();
  const changedParts = [];
  for (const name of sourceFiles) {
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [sourceData, finalData] = await Promise.all([
      originalZip.file(name).async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(sourceData) !== sha256(finalData)) changedParts.push(name);
  }
  const expectedParts = [...new Set(expectedChangedParts)].sort();
  if (
    changedParts.length !== expectedParts.length ||
    changedParts.some((part, index) => part !== expectedParts[index])
  ) {
    throw new Error(`Unexpected package changes: ${changedParts.join(", ")}`);
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
        slideCount: EXPECTED_SLIDES,
        updatedSlides: TARGET_SLIDES,
        label: LABEL,
        changedParts,
        warnings: validation.warnings ?? [],
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
