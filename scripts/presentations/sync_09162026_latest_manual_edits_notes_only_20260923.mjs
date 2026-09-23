#!/usr/bin/env node

/** Update speaker notes for the latest manual edits on slides 1, 3, and 144–147 only. */

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
  "results/presentations/09162026_latest_manual_edits_notes_only_20260923_v2",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_notes_synced_20260923_v2.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "b20aa0d09897e64b431e41e1173fc816dfbe8077df1468a063ca802c37212cb8";
const SLIDE_COUNT = 154;
const FINDING15_SOURCES =
  "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 15; " +
  "https://doi.org/10.1016/j.neuron.2019.03.075; " +
  "https://doi.org/10.1016/j.celrep.2023.113183; " +
  "https://doi.org/10.1038/s41419-020-02776-4";
const APOE_CELL_SOURCE = "https://pubmed.ncbi.nlm.nih.gov/3539206/";

function notes({ goal, walkthrough, boundary, transition, sources }) {
  const sections = [
    `Teaching goal: ${goal}`,
    "",
    `Walk through: ${walkthrough}`,
    "",
    `Scientific boundary: ${boundary}`,
    "",
    `Transition: ${transition}`,
  ];
  if (sources) sections.push("", `Sources: ${sources}`);
  return sections.join("\n");
}

const NOTES_BY_SLIDE = new Map([
  [
    1,
    notes({
      goal:
        "Introduce the research question and the scope of the presentation.",
      walkthrough:
        "This study asks how sex, APOE genotype, and brain cell type shape mitochondrial gene-expression changes in Alzheimer’s disease. The analysis uses cell-level differential expression, pathway analysis, and KDA. ROSMAP provides the primary results, while SEA-AD provides supplemental human validation. The presentation develops 16 biological findings. Mouse experiments remain a possible future validation step.",
      boundary:
        "The evidence is transcriptomic and exploratory. Separate results within sex and APOE groups do not establish a statistical interaction, and RNA abundance does not directly measure mitochondrial function.",
      transition:
        "Begin Part 1 with the study overview and the concepts needed to interpret the results.",
    }),
  ],
  [
    3,
    notes({
      goal:
        "Show how the study moves from cell-level gene expression to human validation.",
      walkthrough:
        "First, DEG analysis identifies genes with higher or lower RNA abundance in Alzheimer’s disease within fine cell types and sex and APOE groups. Second, pathway analysis summarizes the mitochondrial processes represented among the DEGs. Third, KDA uses gene networks to nominate genes connected to MitoCarta MT DEGs. Fourth, human validation compares the ROSMAP results with SEA-AD and direct broad-cell analyses. Mouse validation would test selected candidates and mitochondrial function in targeted models.",
      boundary:
        "The first four stages summarize analyses presented in this deck. Mouse validation is a proposed next step and does not contribute evidence to the current findings.",
      transition:
        "Introduce ROSMAP as the primary cohort and SEA-AD as the supplemental human validation cohort.",
    }),
  ],
  [
    144,
    notes({
      goal:
        "Show that the APOE DEG direction differs among the three supporting astrocyte groups.",
      walkthrough:
        "Here APOE refers to the gene, and the DEG result measures APOE RNA. APOE is upregulated in the supporting female epsilon-2 astrocyte KDA call, with log2 fold change plus 0.79. It is downregulated in male epsilon-2, with log2 fold change minus 0.51, and in male epsilon-4, with log2 fold change minus 1.25. These opposite directions show why the result should not be described as epsilon-4-only.",
      boundary:
        "Each value comes from an AD-versus-NCI comparison within one sex and APOE group and one fine astrocyte type. Separate within-group results do not establish that the disease effect differs statistically across groups.",
      transition:
        "Show the three KDA calls and the mitochondrial genes directly connected to APOE.",
      sources: FINDING15_SOURCES,
    }),
  ],
  [
    145,
    notes({
      goal:
        "Present the primary ROSMAP DEG and KDA evidence for Finding 15.",
      walkthrough:
        "APOE is a DEG and a gene returned from one astrocyte KDA call in each of three groups: female epsilon-2, male epsilon-2, and male epsilon-4. Thus, three KDA calls support the result, and APOE meets the DEG criteria in all three. One result is upregulated and two are downregulated. Across the calls, five named mitochondrial genes connect directly to APOE. TUFM supports mitochondrial protein production. LDHB and CHCHD10 relate to metabolism, mitochondrial structure, or stress responses. ATP5PB and ATP5F1A encode nuclear OXPHOS components of ATP synthase.",
      boundary:
        "Each group contributes only one KDA call, and the connected genes differ among groups. The three calls therefore do not establish one repeated APOE mitochondrial pathway or causal regulation by APOE.",
      transition:
        "Explain the log2 fold changes and the lack of matching SEA-AD coverage.",
      sources: FINDING15_SOURCES,
    }),
  ],
  [
    146,
    notes({
      goal:
        "Define the APOE log2 fold changes and distinguish within-group expression from a direct group comparison.",
      walkthrough:
        "Log2 fold change compares modeled APOE RNA expression in AD with NCI within the indicated fine astrocyte type. The ordinary expression ratio is two raised to the log2 fold change. In female epsilon-2 Ast GRM3, plus 0.79 corresponds to about 1.72 times the expression in NCI, or 72 percent higher. In male epsilon-2 Ast GRM3, minus 0.51 corresponds to about 0.70 times the expression in NCI, or 30 percent lower. In male epsilon-4 Ast CHI3L1, minus 1.25 corresponds to about 0.42 times the expression in NCI, or 58 percent lower. SEA-AD had no KDA calls in the same sex, APOE, and cell categories.",
      boundary:
        "The three values are not percentages, KDA scores, or direct comparisons between groups. Different fine astrocyte types contribute, and missing SEA-AD coverage is neutral rather than failed validation.",
      transition:
        "Separate the APOE gene-expression result from the biological fact that astrocytes produce ApoE protein.",
      sources: FINDING15_SOURCES,
    }),
  ],
  [
    147,
    notes({
      goal:
        "Distinguish the APOE gene and its RNA from the ApoE protein produced by astrocytes.",
      walkthrough:
        "APOE is the gene, APOE expression refers to its RNA, and ApoE is the encoded protein. Astrocytes are a major source of ApoE protein in the brain, where ApoE participates in lipid transport. The DEG analysis on the preceding slides measures APOE RNA, not ApoE protein abundance. The different RNA directions may reflect differences in astrocyte state or response to pathology. A formal interaction model must directly compare the disease effects across sex and APOE groups.",
      boundary:
        "Astrocytes are not the only cells that can produce ApoE. RNA abundance does not determine how much ApoE protein is secreted, and the three separate group analyses do not prove a sex-by-APOE interaction.",
      transition:
        "Compare the context-specific result with prior APOE genetics and experimental astrocyte studies.",
      sources: `${FINDING15_SOURCES}; ${APOE_CELL_SOURCE}`,
    }),
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
  return [...xml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map((match) =>
    relationshipAttributes(match[0]),
  );
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
    (item) => item.Id === relationshipId && item.Type?.endsWith("/slide"),
  );
  if (!relation?.Target) throw new Error(`Visible slide ${ordinal} was not found`);
  return normalizePart("ppt/presentation.xml", relation.Target);
}

async function notesPartForSlide(zip, slidePart) {
  const relsPath = path.posix.join(
    path.posix.dirname(slidePart),
    "_rels",
    `${path.posix.basename(slidePart)}.rels`,
  );
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing slide relationships: ${relsPath}`);
  const relation = relationships(relsXml).find((item) => item.Type?.endsWith("/notesSlide"));
  if (!relation?.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return normalizePart(slidePart, relation.Target);
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
  for (const [slideNumber, updatedNotes] of NOTES_BY_SLIDE) {
    slides[slideNumber - 1].speakerNotes.textFrame.setText(updatedNotes);
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

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const snapshot = await reopened.inspect({ kind: "notes", maxChars: 5000000 });
  const finalNotesBySlide = new Map(
    snapshot.ndjson
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text || ""]),
  );
  for (const [slideNumber, expectedNotes] of NOTES_BY_SLIDE) {
    if (finalNotesBySlide.get(slideNumber) !== expectedNotes) {
      throw new Error(`Final speaker notes do not match for slide ${slideNumber}`);
    }
  }

  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const actualChanged = [];
  const actualDeleted = [];
  const actualAdded = [];
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
  for (const [name, entry] of Object.entries(finalZip.files)) {
    if (!entry.dir && !originalZip.file(name)) actualAdded.push(name);
  }
  actualChanged.sort();
  actualDeleted.sort();
  actualAdded.sort();
  const expectedChanged = [...expectedChangedParts].sort();
  if (
    actualChanged.length !== expectedChanged.length ||
    actualChanged.some((name, index) => name !== expectedChanged[index])
  ) {
    throw new Error(`Unexpected changed package parts: ${actualChanged.join(", ")}`);
  }
  if (actualDeleted.length || actualAdded.length) {
    throw new Error(
      `Unexpected package membership changes. Added: ${actualAdded.join(", ")}; deleted: ${actualDeleted.join(", ")}`,
    );
  }
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("Source changed before completion");
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        originalSha256: sourceHash,
        output: FINAL_PPTX,
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
