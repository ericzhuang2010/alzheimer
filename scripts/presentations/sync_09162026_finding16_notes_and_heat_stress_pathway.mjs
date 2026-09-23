#!/usr/bin/env node

/** Sync Finding 16 notes with slides 150–154 and restore the exact heat-stress pathway name. */

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
const RUN_DIR = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_finding16_heat_stress_20260922_v1",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_finding16_heat_stress_20260922_v1.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "90bb745b244f292ba5f437b86f445c02469ff78dcb70b92e87ed5eb54f78a081";
const SLIDE_COUNT = 154;
const CHANGED_SLIDES = [151, 152, 154];

const TEXT_REPLACEMENTS = [
  {
    slide: 151,
    before: "Three of five returned genes map to HSF1-linked protein-stress pathways",
    after: "Three of five returned genes map to two overlapping stress-response pathways",
  },
  {
    slide: 151,
    before: "Pathway result: cellular response to protein stress",
    after: "Pathway result: cellular response to heat stress",
  },
  {
    slide: 151,
    before:
      "This pathway name reflects shared stress-response genes; it does not mean the cells were exposed to high temperature",
    after:
      "This pathway contains genes activated by cellular stress, including stress from damaged proteins. It does not imply exposure to high temperature",
  },
  {
    slide: 151,
    before: "WHY THE PATHWAY RESULTS ARE NOT INDEPENDENT",
    after: "WHY THE TWO PATHWAY RESULTS OVERLAP",
  },
  {
    slide: 151,
    before: "The same three genes contribute",
    after: "The same three genes contribute to both",
  },
  {
    slide: 151,
    before: "The same three genes contribute to several related pathway results",
    after:
      "HSPH1, HSPA1A, and PTGES3 contribute to both the HSF1-controlled and heat-stress pathway results",
  },
  {
    slide: 152,
    before:
      "Only two ROSMAP vascular KDA calls support the protein-stress pathway result. SEA-AD had no vascular KDA category.",
    after:
      "Only two ROSMAP vascular KDA calls support the two overlapping stress-response pathway results. SEA-AD had no vascular KDA category.",
  },
  {
    slide: 152,
    before: "Related terms share genes",
    after: "The same three genes drive both results",
  },
  {
    slide: 152,
    before:
      "The HSF1 and protein-stress pathway results share genes and should not be counted as independent findings.",
    after:
      "The HSF1-controlled and heat-stress pathway results are both driven by HSPH1, HSPA1A, and PTGES3.",
  },
  {
    slide: 154,
    before: "Current pathway result",
    after: "Current pathway results",
  },
  {
    slide: 154,
    before: "HSF1-linked protein-stress genes",
    after: "HSF1-controlled and heat-stress gene sets",
  },
  {
    slide: 154,
    before:
      "Shows that vascular KDA calls from female donors in the APOE ε4-containing group return several genes controlled by HSF1.",
    after:
      "Shows that vascular KDA calls from female donors in the APOE ε4-containing group return three genes that contribute to both pathway results.",
  },
];

const NOTES_BY_SLIDE = new Map([
  [
    150,
    [
      "This slide defines the analysis context before describing the three returned genes.",
      "",
      "The first two labels identify the donor group: female donors with an APOE epsilon-4-containing genotype. The third label identifies the analyzed cell category, vascular cells. Two eligible KDA calls contribute to this result.",
      "",
      "HSPA1A helps proteins fold correctly or recover during stress. HSPH1 works with other heat-shock proteins to help damaged proteins refold. PTGES3 also has protein-folding functions.",
      "",
      "Heat-shock genes can respond to many forms of cellular stress. Their name does not imply literal exposure to high temperature.",
      "",
      "The pathway interpretation comes from these three related genes, so this result remains a focused clue rather than evidence for a broad vascular stress response.",
      "",
      "Next, I will show the two pathway results produced by these genes.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
  [
    151,
    [
      "Five unique non-MitoCarta genes were returned from vascular KDA calls in the female APOE epsilon-4-containing donor group. Three are stress-response genes: HSPH1, HSPA1A, and PTGES3. Only two eligible KDA calls contribute.",
      "",
      "Pathway analysis tests whether the returned genes occur more often than expected in known gene sets. The first result is genes controlled by HSF1, with a BH-adjusted P value of 4.07 times 10 to the minus 4. HSF1 regulates genes that protect proteins during cellular stress.",
      "",
      "The second result is cellular response to heat stress, with a BH-adjusted P value of 0.00383. The pathway name refers to a shared cellular stress-response system. Damaged or misfolded proteins and other cellular stresses can activate these genes, so the result does not imply exposure to high temperature.",
      "",
      "The two pathway results overlap. HSPH1, HSPA1A, and PTGES3 contribute to both. Therefore, the two adjusted P values describe related analyses rather than two independent biological findings.",
      "",
      "APOE epsilon-4 identifies the donor group. It is not the pathway being tested, and this subgroup result does not establish an APOE epsilon-4 interaction.",
      "",
      "Next, I will explain why the evidence remains preliminary.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
  [
    152,
    [
      "This slide explains why the Finding 16 result remains preliminary.",
      "",
      "Only two ROSMAP fine-cell KDA calls contribute to the vascular result in the female APOE epsilon-4-containing group. The same three genes, HSPH1, HSPA1A, and PTGES3, drive both the HSF1-controlled and cellular response to heat stress pathway results. The two pathway results therefore provide overlapping evidence.",
      "",
      "SEA-AD had no vascular KDA category, so it could not test this result. Missing SEA-AD coverage is neutral and does not count as a failed validation.",
      "",
      "The low confidence comes from the limited number of ROSMAP KDA calls and the shared genes underlying both pathway results.",
      "",
      "Next, I will explain why an HSF1-linked response in vascular cells may still be biologically relevant.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
  [
    153,
    [
      "Vascular cells help regulate blood flow in the brain and support blood-brain barrier function.",
      "",
      "The three returned genes help protect proteins during cellular stress. Their expression may indicate protein damage or a protective response in vascular cells.",
      "",
      "Many stresses can activate HSF1, including inflammation, oxidative stress, and stress caused by damaged proteins. The analysis does not identify which trigger produced this result.",
      "",
      "This biological interpretation does not show that APOE epsilon-4 caused the response. It also does not establish causal regulation or demonstrate a functional vascular effect.",
      "",
      "Spatial protein measurements could test whether these stress-response proteins increase near vascular Alzheimer’s pathology.",
      "",
      "Next, I will compare the current result with the supporting literature.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
  [
    154,
    [
      "The current analysis produced two overlapping pathway results: genes controlled by HSF1 and cellular response to heat stress.",
      "",
      "Vascular KDA calls from female donors in the APOE epsilon-4-containing group returned HSPH1, HSPA1A, and PTGES3. These three genes contribute to both pathway results. Because only two KDA calls contribute, this remains a focused hypothesis.",
      "",
      "Guo and colleagues support analyzing Alzheimer’s disease networks separately by cell type and sex. Mathys and colleagues show that Alzheimer’s-related gene expression differs among brain cell populations. Neither study independently reports this particular group of vascular stress-response genes.",
      "",
      "The current result has moderate provisional novelty. It does not establish an APOE epsilon-4 interaction or prove that the returned genes cause vascular dysfunction.",
      "",
      "This concludes the detailed findings.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
]);

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function parseNdjson(ndjson) {
  return (ndjson || "")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
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

function relationshipAttributes(tag) {
  return Object.fromEntries(
    [...tag.matchAll(/([A-Za-z:]+)="([^"]*)"/g)].map((match) => [match[1], match[2]]),
  );
}

function relationships(xml) {
  return [...xml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map((match) => ({
    attrs: relationshipAttributes(match[0]),
  }));
}

function normalizePart(basePart, target) {
  if (target.startsWith("/")) return target.slice(1);
  return path.posix.normalize(path.posix.join(path.posix.dirname(basePart), target));
}

async function visibleSlidePart(zip, ordinal) {
  const presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  const presentationRels = await zip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  if (!presentationXml || !presentationRels) {
    throw new Error("Presentation ordering metadata is missing");
  }
  const slideIds = [
    ...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g),
  ].map((match) => match[1]);
  const relationshipId = slideIds[ordinal - 1];
  const relation = relationships(presentationRels).find(
    (item) => item.attrs.Id === relationshipId && item.attrs.Type?.endsWith("/slide"),
  );
  if (!relation?.attrs.Target) throw new Error(`Visible slide ${ordinal} was not found`);
  return normalizePart("ppt/presentation.xml", relation.attrs.Target);
}

async function notesPartForSlide(zip, slidePart) {
  const relsPath = path.posix.join(
    path.posix.dirname(slidePart),
    "_rels",
    `${path.posix.basename(slidePart)}.rels`,
  );
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing slide relationships: ${relsPath}`);
  const relation = relationships(relsXml).find((item) =>
    item.attrs.Type?.endsWith("/notesSlide"),
  );
  if (!relation?.attrs.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return normalizePart(slidePart, relation.attrs.Target);
}

async function main() {
  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
  if (await fs.stat(FINAL_PPTX).catch(() => undefined)) {
    throw new Error(`Output already exists: ${FINAL_PPTX}`);
  }

  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceHash = sha256(sourceBuffer);
  if (sourceHash !== EXPECTED_SOURCE_SHA256) {
    throw new Error(`Source deck changed before edit: ${sourceHash}`);
  }
  await fs.writeFile(path.join(BUILD_DIR, "source-original.pptx"), sourceBuffer);

  const { importRuntimeModule } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href
  );
  const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");
  const JSZipModule = await importRuntimeModule("jszip");
  const JSZip = JSZipModule.default ?? JSZipModule;

  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const slides = slidesFromPresentation(presentation);
  if (slides.length !== SLIDE_COUNT) {
    throw new Error(`Expected ${SLIDE_COUNT} slides, found ${slides.length}`);
  }
  const snapshot = parseNdjson(
    (await presentation.inspect({ kind: "textbox,notes", maxChars: 7000000 })).ndjson,
  );

  for (const replacement of TEXT_REPLACEMENTS) {
    const matches = snapshot.filter(
      (record) =>
        record.kind === "textbox" &&
        record.slide === replacement.slide &&
        record.text === replacement.before,
    );
    if (matches.length !== 1) {
      throw new Error(
        `Expected one text match on slide ${replacement.slide}, found ${matches.length}: ${replacement.before}`,
      );
    }
    presentation.resolve(matches[0].id).text.replace(replacement.before, replacement.after);
  }

  for (const [slideNumber, notes] of NOTES_BY_SLIDE) {
    slides[slideNumber - 1].speakerNotes.textFrame.setText(notes);
    slides[slideNumber - 1].speakerNotes.setVisible(true);
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("Source changed during Finding 16 editing");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const expectedChangedParts = [];

  for (const slideNumber of CHANGED_SLIDES) {
    const sourcePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactPart = await visibleSlidePart(artifactZip, slideNumber);
    const updatedXml = await artifactZip.file(artifactPart)?.async("string");
    if (!updatedXml) throw new Error(`Updated slide XML is missing for slide ${slideNumber}`);
    sourceZip.file(sourcePart, updatedXml);
    expectedChangedParts.push(sourcePart);
  }

  for (const slideNumber of NOTES_BY_SLIDE.keys()) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const updatedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!updatedNotesXml) throw new Error(`Updated notes are missing for slide ${slideNumber}`);
    sourceZip.file(sourceNotesPart, updatedNotesXml);
    expectedChangedParts.push(sourceNotesPart);
  }

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
    await sourceZip.generateAsync({
      type: "nodebuffer",
      compression: "DEFLATE",
      compressionOptions: { level: 6 },
    }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  await finalizePresentation({
    explicitTotalSlideCount: SLIDE_COUNT,
    requiredNativeTableOwnerSlides: [53, 54, 55, 56, 57],
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
      ...[53, 54, 55, 56, 57].flatMap((number) => [
        "--require-native-table-slide",
        String(number),
      ]),
    ],
    fontPolicy: {
      basis: "reference",
      families: ["Arial"],
      referencePath: SOURCE,
      referenceSha256: sourceHash,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD_DIR, "validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalSnapshot = parseNdjson(
    (await reopened.inspect({ kind: "textbox,notes", maxChars: 8000000 })).ndjson,
  );
  const slide151Text = finalSnapshot
    .filter((record) => record.kind === "textbox" && record.slide === 151)
    .map((record) => record.text)
    .join("\n");
  for (const phrase of [
    "Pathway result: cellular response to heat stress",
    "HSPH1, HSPA1A, and PTGES3 contribute to both",
  ]) {
    if (!slide151Text.includes(phrase)) {
      throw new Error(`Required phrase missing from slide 151: ${phrase}`);
    }
  }

  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const actualChanged = [];
  const actualDeleted = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) {
      actualDeleted.push(name);
      continue;
    }
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) actualChanged.push(name);
  }
  actualChanged.sort();
  actualDeleted.sort();
  const expectedChanged = [...new Set(expectedChangedParts)].sort();
  if (
    actualChanged.length !== expectedChanged.length ||
    actualChanged.some((name, index) => name !== expectedChanged[index])
  ) {
    throw new Error(`Unexpected changed package parts: ${actualChanged.join(", ")}`);
  }
  if (actualDeleted.length) {
    throw new Error(`Unexpected deleted package parts: ${actualDeleted.join(", ")}`);
  }

  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("Source changed before installation");
  }
  await fs.copyFile(FINAL_PPTX, SOURCE);

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        originalSha256: sourceHash,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
        finalSlideCount: SLIDE_COUNT,
        updatedSlides: CHANGED_SLIDES,
        updatedNotesSlides: [...NOTES_BY_SLIDE.keys()],
        changedParts: actualChanged,
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
