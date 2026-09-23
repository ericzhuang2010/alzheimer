#!/usr/bin/env node

/** Clarify that APOE defines the donor group and HSF1/protein stress is the Finding 16 pathway result. */

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
  "results/presentations/09162026_clarify_finding16_20260922_v1",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_finding16_clarified_20260922_v1.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "6cc7755b9368bb6c22bb1a6baefa51c96513a910aa46a18d82f985b525a81ff4";
const SLIDE_COUNT = 154;
const CHANGED_SLIDES = [149, 150, 151, 152, 153, 154];

const TEXT_REPLACEMENTS = [
  {
    slide: 149,
    before: "Female APOE ε4 vascular cells show a small group of stress-response genes",
    after: "Finding 16: vascular stress-response genes in the female APOE ε4 group",
  },
  {
    slide: 149,
    before: "Observed in: female ε4",
    after: "Donor group: female, APOE ε4-containing",
  },
  {
    slide: 149,
    before:
      "HSPH1, HSPA1A, and PTGES3 are returned from KDA calls in female ε4 vascular cells, but only two KDA calls contribute.",
    after:
      "APOE ε4 identifies the donor group, not a pathway. Two vascular-cell KDA calls return HSPH1, HSPA1A, and PTGES3.",
  },
  {
    slide: 150,
    before: "Female ε4 vascular KDA calls return a small group of protein-stress genes",
    after: "Vascular KDA calls in the female APOE ε4 group return three protein-stress genes",
  },
  {
    slide: 150,
    before:
      "Heat-shock genes protect protein folding during many forms of cell stress. Literal high temperature is not required.",
    after:
      "The sex and APOE labels define the donor group. These genes point to protein stress, and literal heat is not required.",
  },
  { slide: 150, before: "Female", after: "Female donors" },
  { slide: 150, before: "APOE ε4", after: "APOE ε4-containing" },
  {
    slide: 150,
    before:
      "These three related genes give a focused clue, not evidence of a broad stress response in vascular cells.",
    after:
      "The pathway interpretation comes from these three related genes, so the result remains a focused clue.",
  },
  {
    slide: 151,
    before:
      "ROSMAP: three of five genes returned from female ε4 vascular KDA calls respond to cell stress",
    after: "Three of five returned genes map to HSF1-linked protein-stress pathways",
  },
  {
    slide: 151,
    before:
      "The pathway test compares the five returned genes with all genes available in the vascular network; the result is exploratory.",
    after:
      "For this donor group, pathway analysis tests whether the five returned genes occur more often than expected in known gene sets.",
  },
  {
    slide: 151,
    before: "unique non-MitoCarta genes returned from\nvascular KDA calls",
    after: "unique non-MitoCarta genes returned from\nvascular KDA calls",
    optionalIdentity: true,
  },
  { slide: 151, before: "female ε4", after: "female APOE ε4-containing donor group" },
  {
    slide: 151,
    before: "Genes controlled by HSF1",
    after: "Pathway result: genes controlled by HSF1",
  },
  {
    slide: 151,
    before: "HSF1 controls many genes that protect proteins during cell stress",
    after: "HSF1 controls genes that protect proteins during cell stress",
  },
  {
    slide: 151,
    before: "Cellular response to protein stress",
    after: "Pathway result: cellular response to protein stress",
  },
  {
    slide: 152,
    before: "Only two KDA calls and no SEA-AD vascular analysis make this result preliminary",
    after: "Two KDA calls make the female ε4 subgroup result preliminary",
  },
  {
    slide: 152,
    before:
      "The low confidence comes from very limited ROSMAP evidence, not from a failed comparison with SEA-AD.",
    after:
      "Only two ROSMAP vascular KDA calls support the protein-stress pathway result. SEA-AD had no vascular KDA category.",
  },
  { slide: 152, before: "ROSMAP EVIDENCE", after: "ROSMAP EVIDENCE IN THIS GROUP" },
  {
    slide: 152,
    before: "Very few fine-cell comparisons contribute to the vascular result.",
    after: "Only two fine-cell KDA calls contribute to the vascular result.",
  },
  {
    slide: 153,
    before: "Why this matters: vascular cells protect blood flow and the blood-brain barrier",
    after: "Why the HSF1-linked stress response in vascular cells may matter",
  },
  {
    slide: 153,
    before: "A protein-protection response could mark vascular strain near Alzheimer’s pathology.",
    after:
      "This hypothesis concerns protein protection in vascular cells. The analysis does not identify the trigger.",
  },
  {
    slide: 154,
    before: "How prior research supports and limits Finding 16",
    after: "Evidence supporting the HSF1-linked vascular stress-response finding",
  },
  { slide: 154, before: "Current pathway test", after: "Current pathway result" },
  {
    slide: 154,
    before: "Genes controlled by HSF1",
    after: "HSF1-linked protein-stress genes",
  },
  {
    slide: 154,
    before:
      "Shows that female ε4 vascular KDA calls return several genes controlled by HSF1.",
    after:
      "Shows that vascular KDA calls from female donors in the APOE ε4-containing group return several genes controlled by HSF1.",
  },
];

const NOTES_BY_SLIDE = new Map([
  [
    149,
    [
      "Teaching goal: Introduce Finding 16 while separating the donor group from the biological pathway result.",
      "",
      "Walk through: Female and APOE epsilon-4-containing identify the donor group. Vascular cells identify the cell category. APOE is not the pathway in this finding. The biological result is that two vascular-cell KDA calls returned HSPH1, HSPA1A, and PTGES3, three genes related to cellular protein stress.",
      "",
      "Scientific boundary: Observing the result in this subgroup does not prove that APOE epsilon-4 caused it or that the result differs statistically from other sex or APOE groups.",
      "",
      "Transition: Explain the three returned genes and the donor context.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16.",
    ].join("\n"),
  ],
  [
    150,
    [
      "Teaching goal: Explain the genes returned from vascular-cell KDA calls in the female APOE epsilon-4-containing donor group.",
      "",
      "Walk through: The top labels define the analysis context. The donors are female and carry an APOE epsilon-4-containing genotype. The analyzed cell category is vascular cells, and two eligible KDA calls contribute. HSPA1A helps proteins fold correctly or recover during stress. HSPH1 works with other heat-shock proteins to help damaged proteins refold. PTGES3 also has protein-folding functions.",
      "",
      "Heat-shock genes can respond to many forms of cellular stress. The result does not imply literal exposure to high temperature.",
      "",
      "Scientific boundary: The pathway interpretation comes from only three related genes returned by two KDA calls, so it remains a focused clue.",
      "",
      "Transition: Show how pathway analysis interprets the five returned genes.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
  [
    151,
    [
      "Teaching goal: Distinguish the donor subgroup from the pathway result and present the pathway statistics.",
      "",
      "Walk through: Female APOE epsilon-4-containing identifies the donor group. It is not a pathway label. Five unique non-MitoCarta genes were returned from vascular KDA calls in this group. Three are stress-response genes: HSPH1, HSPA1A, and PTGES3. Only two eligible KDA calls contribute.",
      "",
      "The pathway analysis asks whether the returned genes occur more often than expected in known gene sets. The HSF1-controlled gene set has a BH-adjusted P value of 4.07 times 10 to the minus 4. The cellular response to protein stress gene set has a BH-adjusted P value of 0.00383.",
      "",
      "Scientific boundary: The same three genes contribute to several related pathway results, so the pathway results are not independent observations. The analysis does not show that APOE itself is a pathway or that APOE epsilon-4 caused this response.",
      "",
      "Transition: Explain why the evidence remains preliminary.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
  [
    152,
    [
      "Teaching goal: Explain the limited evidence supporting the pathway result in this donor subgroup.",
      "",
      "Walk through: Only two ROSMAP fine-cell KDA calls contribute to the vascular result in the female APOE epsilon-4-containing group. The HSF1 and protein-stress pathway terms share genes and should not be counted as independent findings. SEA-AD had no vascular KDA category, so it could not test this result.",
      "",
      "Scientific boundary: The low confidence comes from limited ROSMAP evidence. Missing SEA-AD coverage is neutral and does not count as a failed validation.",
      "",
      "Transition: Explain the possible biological relevance of an HSF1-linked response in vascular cells.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
  [
    153,
    [
      "Teaching goal: Explain why an HSF1-linked protein-stress response in vascular cells may matter.",
      "",
      "Walk through: Vascular cells help regulate brain blood flow and blood-brain barrier function. The three returned genes may indicate protein damage or a protective response. Many possible stresses can activate HSF1, so the analysis does not identify the trigger.",
      "",
      "Scientific boundary: This is a biological interpretation of the pathway result. It does not show that APOE epsilon-4 caused the response, establish causal regulation, or demonstrate a functional vascular effect.",
      "",
      "Transition: Place the pathway result in the context of prior research.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
  [
    154,
    [
      "Teaching goal: Summarize the evidence for the HSF1-linked vascular stress-response finding.",
      "",
      "Walk through: The current pathway result shows that vascular-cell KDA calls from female donors in the APOE epsilon-4-containing group returned several genes controlled by HSF1. APOE epsilon-4 identifies the donor group. HSF1-linked protein stress is the pathway result. Guo and colleagues support analyzing AD networks separately by cell type and sex. Mathys and colleagues show that AD-related gene expression differs among brain cell populations. Neither study independently reports this particular vascular gene set.",
      "",
      "Scientific boundary: The result depends on three related genes from only two KDA calls. It should be treated as a focused hypothesis. The current analysis does not prove an APOE epsilon-4 interaction.",
      "",
      "Transition: This concludes the detailed findings.",
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
    tag: match[0],
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
  if (!relationshipId) throw new Error(`Visible slide ${ordinal} was not found`);
  const relation = relationships(presentationRels).find(
    (item) => item.attrs.Id === relationshipId && item.attrs.Type?.endsWith("/slide"),
  );
  if (!relation?.attrs.Target) throw new Error(`Slide relationship ${relationshipId} was not found`);
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
    (await presentation.inspect({ kind: "textbox,notes", maxChars: 6000000 })).ndjson,
  );
  for (const replacement of TEXT_REPLACEMENTS) {
    if (replacement.optionalIdentity) continue;
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

  for (const [slideNumber, revisedNotes] of NOTES_BY_SLIDE) {
    slides[slideNumber - 1].speakerNotes.textFrame.setText(revisedNotes);
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
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const updatedSlideXml = await artifactZip.file(artifactSlidePart)?.async("string");
    if (!updatedSlideXml) throw new Error(`Updated slide XML is missing for slide ${slideNumber}`);
    sourceZip.file(sourceSlidePart, updatedSlideXml);
    expectedChangedParts.push(sourceSlidePart);

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
  const finalSlides = slidesFromPresentation(reopened);
  if (finalSlides.length !== SLIDE_COUNT) {
    throw new Error(`Final deck has ${finalSlides.length} slides`);
  }
  const finalSnapshot = parseNdjson(
    (await reopened.inspect({ kind: "textbox,notes", maxChars: 8000000 })).ndjson,
  );

  const requiredPhrases = new Map([
    [149, ["Donor group: female, APOE ε4-containing", "APOE ε4 identifies the donor group, not a pathway."]],
    [150, ["Female donors", "APOE ε4-containing"]],
    [151, ["Pathway result: genes controlled by HSF1", "Pathway result: cellular response to protein stress"]],
    [154, ["HSF1-linked protein-stress genes"]],
  ]);
  for (const [slideNumber, phrases] of requiredPhrases) {
    const slideText = finalSnapshot
      .filter((record) => record.kind === "textbox" && record.slide === slideNumber)
      .map((record) => record.text)
      .join("\n");
    for (const phrase of phrases) {
      if (!slideText.includes(phrase)) {
        throw new Error(`Required phrase missing from slide ${slideNumber}: ${phrase}`);
      }
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
        updatedNotesSlides: CHANGED_SLIDES,
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
