#!/usr/bin/env node

/** Refresh speaker notes for the manually revised slides 56–62. */

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
  "results/presentations/09162026_slides56_62_notes_refresh_20260920/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slides56_62_notes_refresh_20260920/output/09162026_sex_apoe_kda_fine_broad_slides56_62_notes_refreshed_20260920.pptx",
);
const EXPECTED_SLIDES = 159;
const EXPECTED_SOURCE_SHA256 =
  "b91cb750cddde55e02345eab5540dc21c1709c00573a78b0e2acdf2034c71f80";

function notes({ goal, walkthrough, boundary, transition, sources }) {
  return [
    `Teaching goal: ${goal}`,
    "",
    `Walk through: ${walkthrough}`,
    "",
    `Scientific boundary: ${boundary}`,
    "",
    `Transition: ${transition}`,
    ...(sources ? ["", `Sources: ${sources}`] : []),
  ].join("\n");
}

const FINDING_3_SOURCE =
  "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 3. Literature: https://doi.org/10.1016/j.neuron.2019.03.075; https://doi.org/10.1016/j.celrep.2023.113183; https://doi.org/10.1186/s13024-023-00624-5";
const FINDING_4_SOURCE =
  "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 4. Literature: https://doi.org/10.1038/s41419-020-02776-4; https://doi.org/10.1016/j.celrep.2023.113183; https://doi.org/10.1038/s41586-024-07606-7";

const NOTES_BY_SLIDE = new Map([
  [
    56,
    notes({
      goal: "Introduce Finding 3 and distinguish it from the male APOE ε3/ε3 pattern.",
      walkthrough:
        "Finding 3 concerns female APOE ε2 cells. In the ROSMAP fine-cell analysis, core MT genes and nuclear-encoded OXPHOS genes were both predominantly upregulated in Alzheimer’s disease. The two OXPHOS gene sets therefore move together, unlike the opposite directions observed in male APOE ε3/ε3 cells. This section first states the result, then shows the occurrence counts, resolution checks, biological interpretation, and supporting literature.",
      boundary:
        "These within-stratum results do not establish a disease-by-sex or disease-by-APOE interaction. Coordinated gene expression also does not demonstrate greater OXPHOS protein abundance, increased ATP production, or improved mitochondrial function.",
      transition: "State the female APOE ε2 result and define the two gene sets being compared.",
      sources: FINDING_3_SOURCE,
    }),
  ],
  [
    57,
    notes({
      goal: "Explain the coordinated increase across the two OXPHOS gene sets.",
      walkthrough:
        "Core MT genes are the 13 protein-coding mitochondrial-DNA genes that encode structural OXPHOS subunits. Nuclear-encoded OXPHOS genes are the 86 nuclear genes that encode the remaining structural subunits used in this analysis. Across eligible female APOE ε2 fine-cell comparisons, 127 of 128 core MT gene occurrences and 239 of 243 nuclear-encoded OXPHOS gene occurrences were upregulated in AD. The result is therefore a coordinated transcript-level pattern across both gene sets.",
      boundary:
        "An occurrence is one pathway gene identified as a DEG in one eligible fine-cell comparison, so the same gene may appear more than once across cell types. These counts do not measure unique genes, protein assembly, respiration, or ATP production.",
      transition: "Show the complete ROSMAP occurrence and enrichment counts.",
      sources: FINDING_3_SOURCE,
    }),
  ],
  [
    58,
    notes({
      goal: "Quantify the ROSMAP evidence for Finding 3.",
      walkthrough:
        "The core MT gene set contributes 128 DEG occurrences: 127 AD-up and one AD-down, or 99 percent upregulated. Nuclear-encoded OXPHOS genes contribute 243 occurrences: 239 AD-up and four AD-down, or 98 percent upregulated. The analysis also identified 29 significant pathway-enrichment results across KDA calls, comprising 20 for core MT genes and nine for nuclear-encoded OXPHOS genes. Within fine excitatory neurons, nine of 12 fine cell types support core MT upregulation and eight of 12 support nuclear-encoded OXPHOS upregulation.",
      boundary:
        "Occurrence counts can repeat genes across fine-cell KDA queries and do not represent independent donors or expression effect sizes. The number of enriched KDA calls can also depend on query size and the genes available in each network background.",
      transition: "Compare the primary fine-cell result with direct broad-cell and SEA-AD evidence.",
      sources: FINDING_3_SOURCE,
    }),
  ],
  [
    59,
    notes({
      goal: "Explain how cell resolution and cohort coverage affect Finding 3.",
      walkthrough:
        "The project treats fine-cell results as primary and direct broad-cell results as sensitivity evidence. In the fine-cell analysis, nine of 12 excitatory fine cell types support core MT upregulation and eight of 12 support nuclear-encoded OXPHOS upregulation. In the direct broad-cell ROSMAP analysis, the nuclear-encoded OXPHOS increase remains strong, but the core MT component is not significant. SEA-AD has no active matched female APOE ε2 category, so it cannot test this finding.",
      boundary:
        "The broad-cell disagreement limits how broadly the coordinated two-gene-set result can be generalized. Missing SEA-AD coverage is neutral: it provides neither validation nor contradictory evidence.",
      transition: "Explain why coordinated upregulation may be biologically interesting without calling it protective.",
      sources: FINDING_3_SOURCE,
    }),
  ],
  [
    60,
    notes({
      goal: "Interpret the female APOE ε2 pattern cautiously.",
      walkthrough:
        "APOE ε2 lowers Alzheimer’s disease risk at the population level, but the current data come from diseased tissue. Both OXPHOS gene sets move upward rather than separating as they do in the male APOE ε3/ε3 finding. This coordinated response could reflect compensation for inefficient mitochondria or another altered disease state. It motivates a protective-response hypothesis for future testing.",
      boundary:
        "The observed gene-expression pattern does not establish that the response is protective, that mitochondria work more efficiently, or that APOE ε2 caused the response. Separate female APOE ε2 analyses also do not establish a statistical sex-by-APOE interaction.",
      transition: "Place the result in the context of APOE risk, mitochondrial biology, and sex-aware Alzheimer’s research.",
      sources: FINDING_3_SOURCE,
    }),
  ],
  [
    61,
    notes({
      goal: "Summarize the literature context and the novelty boundary for Finding 3.",
      walkthrough:
        "Belloy and colleagues establish that Alzheimer’s disease risk differs substantially across APOE alleles, but that work does not explain this female APOE ε2 expression pattern. Lee and colleagues show that APOE state can alter mitochondrial homeostasis in another experimental context. Guo and colleagues support analyzing Alzheimer’s molecular networks by sex and cell type, but they do not report this exact female APOE ε2 OXPHOS result. The novelty label is therefore high but provisional.",
      boundary:
        "These studies make the interpretation plausible, but none independently reproduces the same sex, APOE, cell-type, and disease comparison. The novelty assessment comes from a focused review rather than a systematic literature search.",
      transition: "Move to Finding 4, which shows a different OXPHOS direction in female APOE ε4 fine-cell results.",
      sources: FINDING_3_SOURCE,
    }),
  ],
  [
    62,
    notes({
      goal: "Introduce Finding 4 and contrast it with the preceding coordinated increase.",
      walkthrough:
        "Finding 4 concerns female APOE ε4 fine-cell results. Its strongest signal is lower expression of nuclear-encoded OXPHOS genes, while core MT genes show a smaller and more mixed pattern. The following slides show the ROSMAP occurrence counts, the disagreement with direct broad-cell results, and the limits of the interpretation.",
      boundary:
        "This is primarily a fine-cell transcriptomic and pathway result. It does not demonstrate reduced respiratory function, a uniform decrease across all MitoCarta MT genes, or a disease-by-APOE interaction.",
      transition: "State the female APOE ε4 result in plain language.",
      sources: FINDING_4_SOURCE,
    }),
  ],
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

async function visibleSlidePart(zip, ordinal) {
  const presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  const presentationRels = await zip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  if (!presentationXml || !presentationRels) {
    throw new Error("Presentation ordering metadata is missing");
  }
  const slideIds = [...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g)]
    .map((match) => match[1]);
  const relationshipId = slideIds[ordinal - 1];
  if (!relationshipId) throw new Error(`Visible slide ${ordinal} was not found`);
  const relationships = [...presentationRels.matchAll(/<Relationship\b[^>]*\/?\s*>/g)]
    .map((match) => relationshipAttributes(match[0]));
  const relation = relationships.find(
    (item) => item.Id === relationshipId && item.Type?.endsWith("/slide"),
  );
  if (!relation?.Target) throw new Error(`Slide relationship ${relationshipId} was not found`);
  return relation.Target.startsWith("/")
    ? relation.Target.slice(1)
    : path.posix.normalize(path.posix.join("ppt", relation.Target));
}

async function notesPartForSlide(zip, slidePart) {
  const relsPath = path.posix.join(
    path.posix.dirname(slidePart),
    "_rels",
    `${path.posix.basename(slidePart)}.rels`,
  );
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing slide relationships: ${relsPath}`);
  const relationships = [...relsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)]
    .map((match) => relationshipAttributes(match[0]));
  const relation = relationships.find((item) => item.Type?.endsWith("/notesSlide"));
  if (!relation?.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return relation.Target.startsWith("/")
    ? relation.Target.slice(1)
    : path.posix.normalize(path.posix.join(path.posix.dirname(slidePart), relation.Target));
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
    throw new Error(`Source deck changed before the notes refresh: ${sourceHash}`);
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

  const beforePngs = new Map();
  for (const [slideNumber, updatedNotes] of NOTES_BY_SLIDE) {
    const slide = slides[slideNumber - 1];
    const beforePng = await blobBuffer(
      await presentation.export({ slide, format: "png", scale: 1.5 }),
    );
    beforePngs.set(slideNumber, beforePng);
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-before.png`), beforePng);
    slide.speakerNotes.textFrame.setText(updatedNotes);
    slide.speakerNotes.setVisible(true);
    const afterPng = await blobBuffer(
      await presentation.export({ slide, format: "png", scale: 1.5 }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-after.png`), afterPng);
    if (sha256(beforePng) !== sha256(afterPng)) {
      throw new Error(`Visible slide ${slideNumber} changed while updating notes`);
    }
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed during the notes refresh");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const changedNotesParts = [];
  for (const slideNumber of NOTES_BY_SLIDE.keys()) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const updatedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!updatedNotesXml) throw new Error(`Updated notes are missing for slide ${slideNumber}`);
    sourceZip.file(sourceNotesPart, updatedNotesXml);
    changedNotesParts.push(sourceNotesPart);
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
    requiredNativeChartOwnerSlides: [14],
    requiredEmbeddedWorkbookChartOwnerSlides: [14],
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
    receiptPath: path.join(BUILD_DIR, "slides56_62_notes_refresh.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const notesSnapshot = await reopened.inspect({ kind: "notes", maxChars: 3000000 });
  const finalNotesBySlide = new Map(
    notesSnapshot.ndjson
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text]),
  );
  for (const [slideNumber, expectedNotes] of NOTES_BY_SLIDE) {
    const finalPng = await blobBuffer(
      await reopened.export({
        slide: reopenedSlides[slideNumber - 1],
        format: "png",
        scale: 1.5,
      }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-final.png`), finalPng);
    if (sha256(beforePngs.get(slideNumber)) !== sha256(finalPng)) {
      throw new Error(`Finalized deck changed visible slide ${slideNumber}`);
    }
    const actualNotes = finalNotesBySlide.get(slideNumber);
    if (typeof actualNotes !== "string" || actualNotes.trim() !== expectedNotes.trim()) {
      throw new Error(`Finalized notes do not match on slide ${slideNumber}`);
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
  const expectedParts = [...changedNotesParts].sort();
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
        updatedSlides: [...NOTES_BY_SLIDE.keys()],
        visibleSlidesPreserved: true,
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
