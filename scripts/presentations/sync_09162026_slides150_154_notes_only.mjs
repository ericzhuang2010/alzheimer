#!/usr/bin/env node

/** Update only the speaker notes for slides 150–154 to match the current visible slides. */

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
  "results/presentations/09162026_slides150_154_notes_20260922_v1",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_slides150_154_notes_20260922_v1.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "e1ae2705e1a850d1b6140b6afc708645be4284841b9ec7e1441a43b8995bcd0b";
const SLIDE_COUNT = 154;

const NOTES_BY_SLIDE = new Map([
  [
    150,
    [
      "This slide introduces the genes returned from the vascular KDA calls.",
      "",
      "The labels across the top define the analysis context. The donors are female and belong to the APOE epsilon-4-containing group. The analyzed cell category is vascular cells, and two eligible KDA calls contribute.",
      "",
      "HSPA1A helps proteins fold correctly or recover during stress. HSPH1 works with other heat-shock proteins to help damaged proteins refold. PTGES3 also has protein-folding functions in addition to its other cellular roles.",
      "",
      "Heat-shock genes respond to many forms of cellular stress. Their names do not mean that the cells experienced high temperature.",
      "",
      "Next, I will show how pathway analysis interprets these returned genes.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
  [
    151,
    [
      "This slide summarizes the counts and the two overlapping pathway results.",
      "",
      "Five unique non-MitoCarta genes were returned from vascular KDA calls in the female APOE epsilon-4-containing donor group. Three are stress-response genes: HSPH1, HSPA1A, and PTGES3. Only two eligible KDA calls contribute.",
      "",
      "Pathway analysis tests whether the returned genes occur more often than expected in known gene sets. The first result is genes controlled by HSF1, with a BH-adjusted P value of 4.07 times 10 to the minus 4. HSF1 controls genes that protect proteins during cellular stress.",
      "",
      "The second result is cellular response to heat stress, with a BH-adjusted P value of 0.00383. This pathway contains genes activated by cellular stress, including stress from damaged proteins. It does not imply exposure to high temperature.",
      "",
      "The two pathway results overlap because HSPH1, HSPA1A, and PTGES3 contribute to both. The two adjusted P values therefore describe related analyses rather than independent biological findings.",
      "",
      "Next, I will explain why this result remains preliminary.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
  [
    152,
    [
      "This slide explains the main limitations of the Finding 16 result.",
      "",
      "First, only two ROSMAP fine-cell KDA calls contribute to the vascular result in the female APOE epsilon-4-containing group.",
      "",
      "Second, the two pathway results are driven by the same three genes: HSPH1, HSPA1A, and PTGES3. The HSF1-controlled and heat-stress results therefore provide overlapping evidence.",
      "",
      "Third, SEA-AD had no vascular category available for KDA, so it could not test this result. Missing SEA-AD coverage is neutral and does not count as failed validation.",
      "",
      "Together, these points make the result a low-confidence ROSMAP clue.",
      "",
      "Next, I will explain why an HSF1-linked response in vascular cells may still matter biologically.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
  [
    153,
    [
      "This slide explains the possible biological relevance of the pathway result.",
      "",
      "Vascular cells help regulate blood flow in the brain and support blood-brain barrier function.",
      "",
      "HSPH1, HSPA1A, and PTGES3 help protect proteins during cellular stress. Their expression may indicate protein damage or a general protective response in vascular cells.",
      "",
      "Many stresses can activate HSF1. These include inflammation, oxidative stress, and stress caused by damaged proteins. The analysis does not identify which trigger produced this result.",
      "",
      "This interpretation does not show that APOE epsilon-4 caused the response. It also does not establish causal regulation or demonstrate a functional vascular effect.",
      "",
      "Next, I will compare the current finding with the supporting literature.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
  [
    154,
    [
      "This slide summarizes the current result and the supporting literature.",
      "",
      "The current analysis produced two overlapping pathway results: genes controlled by HSF1 and cellular response to heat stress. Vascular KDA calls from female donors in the APOE epsilon-4-containing group returned HSPH1, HSPA1A, and PTGES3. These three genes contribute to both pathway results. Only two KDA calls contribute, which limits the evidence.",
      "",
      "Guo and colleagues support analyzing Alzheimer’s disease networks separately by cell type and sex. Their study does not report this specific group of stress-response genes in vascular cells.",
      "",
      "Mathys and colleagues show that Alzheimer’s-related gene expression differs among brain cell populations. That study uses ROSMAP and does not independently confirm this group of genes.",
      "",
      "The current result has moderate provisional novelty. The available evidence does not establish an APOE epsilon-4 interaction or prove that these genes cause vascular dysfunction.",
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
    throw new Error(`Source deck changed before notes edit: ${sourceHash}`);
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
  for (const [slideNumber, notes] of NOTES_BY_SLIDE) {
    slides[slideNumber - 1].speakerNotes.textFrame.setText(notes);
    slides[slideNumber - 1].speakerNotes.setVisible(true);
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("Source changed during notes editing");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const expectedChangedParts = [];
  for (const slideNumber of NOTES_BY_SLIDE.keys()) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const notesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!notesXml) throw new Error(`Updated notes are missing for slide ${slideNumber}`);
    sourceZip.file(sourceNotesPart, notesXml);
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
  const expectedChanged = [...expectedChangedParts].sort();
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
        updatedNotesSlides: [...NOTES_BY_SLIDE.keys()],
        visibleSlidePartsChanged: [],
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
