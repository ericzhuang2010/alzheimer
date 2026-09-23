#!/usr/bin/env node

/** Refresh speaker notes for slides 52–57 while preserving every slide object. */

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
  "results/presentations/09162026_notes_refresh_20260922_v1/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_notes_refresh_20260922_v1/output/09162026_sex_apoe_kda_fine_broad_notes52_57_refreshed_20260922_v1.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "a4031c9277c0330140697f5f505417b71c5732793e14ec8314489923130750ae";
const SLIDE_COUNT = 160;

const NOTES = new Map([
  [
    52,
    [
      "This section presents the 18 findings and explains how much weight to give each type of evidence.",
      "",
      "The next five slides provide a map before the detailed findings begin. Findings 1–6 summarize DEG and pathway results. Findings 7–16 and 18 summarize genes returned from KDA calls. Finding 17 evaluates which ROSMAP patterns recur in SEA-AD.",
      "",
      "Keep the evidence levels separate. DEG and pathway results describe gene-expression patterns. KDA calls nominate network candidates. Human validation asks whether a pattern appears in another cohort. None of these analyses alone establishes causality or mitochondrial function.",
      "",
      "Next, review how the 18 findings are organized.",
    ].join("\n"),
  ],
  [
    53,
    [
      "The 18 findings fall into three categories.",
      "",
      "Findings 1–6 are the primary DEG and pathway results. They ask how mitochondrial genes and pathways change within each analyzed sex/APOE group before making KDA calls.",
      "",
      "Findings 7–16 and 18 come from KDA calls made with MitoCarta MT DEGs. These calls return candidate genes that may help explain the mitochondrial changes. KDA does not show that a candidate gene causes or drives the change. That remains a hypothesis for follow-up.",
      "",
      "Finding 17 is the cross-cohort comparison with SEA-AD. Fifteen findings are linked to one or more analyzed sex/APOE groups. Findings 7, 10, and 17 do not distinguish a particular group, so they receive lower priority in this sex/APOE-focused presentation.",
      "",
      "A result found in selected groups is not, by itself, proof of a statistical sex or APOE interaction.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 1–18.",
    ].join("\n"),
  ],
  [
    54,
    [
      "Findings 1–6 summarize DEG and pathway results. KDA calls are not involved in these findings.",
      "",
      "Female ε3/ε3 shows increased core MT genes, and nuclear-encoded OXPHOS genes also mostly increase in ROSMAP. Male ε3/ε3 shows a mismatch: core MT genes increase while nuclear-encoded OXPHOS genes decrease. Female ε2 shows increases in both sets. Female ε4 shows a strong decrease in nuclear-encoded OXPHOS genes.",
      "",
      "For male ε2, the two OXPHOS sets are the 13 core MT genes and the nuclear-encoded OXPHOS genes. Both sets show broad decreases. Male ε4 shows increased core MT genes with a more modest decrease in nuclear-encoded OXPHOS genes.",
      "",
      "These patterns summarize DEG occurrences and pathway direction across fine cell types. They do not establish ATP production, mitochondrial performance, or a formal interaction between groups.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 1–6.",
    ].join("\n"),
  ],
  [
    55,
    [
      "This slide summarizes recurring genes returned from KDA calls in selected sex/APOE groups.",
      "",
      "LAMTOR5 connects lysosomal nutrient sensing with OXPHOS-related genes. WDR82 is connected in the network to a small set of core MT genes that are upregulated in AD in excitatory neurons.",
      "",
      "SELENOW is a redox-related gene. Redox refers to the balance of oxidation and reduction reactions, including control of oxidative stress. Its network neighborhoods include genes involved in mitochondrial respiration, mitochondrial protein production, and removal of damaged mitochondrial proteins.",
      "",
      "PGK1 connects astrocyte glycolysis and low-oxygen signaling with mitochondrial quality control. FTL and ANKRD11 connect iron handling in oligodendrocyte precursor cells with GPX4 and autophagy-related genes.",
      "",
      "These are network associations. A KDA call does not establish direct regulation or causality, and recurrence across related calls is not independent replication.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 8, 9, and 11–13.",
    ].join("\n"),
  ],
  [
    56,
    [
      "These genes remain useful, but each result has an important qualification.",
      "",
      "PLCG2 has strong Alzheimer’s disease genetic evidence, but its KDA network neighborhood contains only one overlapping mitochondrial gene, MT-CO1. Astrocyte APOE changes direction across groups, so this is not an ε4-only pattern.",
      "",
      "The female ε4 vascular heat-shock result is a small connected group of stress-response genes supported by only two eligible KDA calls. INTS8 was returned from one male ε2 inhibitory-neuron KDA call. Human genetics supports follow-up, but the gene does not recur across KDA calls.",
      "",
      "These findings are secondary or targeted follow-up candidates. Gene-level genetic evidence does not validate the inferred cell type, sex/APOE context, or network relationship.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 14–16 and 18.",
    ].join("\n"),
  ],
  [
    57,
    [
      "Findings 7, 10, and 17 receive lower priority only because this presentation focuses on differences among sex/APOE groups.",
      "",
      "Findings 7 and 10 occur across all six groups. Finding 7 links cytosolic-ribosome genes such as RPL11 and RPS15 with nuclear-encoded OXPHOS genes. Finding 10 links SELENOM, an endoplasmic-reticulum redox and calcium gene, with genes used for mitochondrial protein production.",
      "",
      "Finding 17 compares ROSMAP with SEA-AD. The cohorts agree more clearly on mitochondrial gene-set patterns than on the exact genes returned from KDA calls.",
      "",
      "These findings may still be biologically important or useful as supporting evidence. They simply do not identify a distinct sex/APOE group. Direct interaction models would be needed to test whether quantitative group differences exist.",
      "",
      "Next, begin the detailed finding sequence with the female ε3/ε3 DEG and pathway result.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 7, 10, and 17.",
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

function parseNdjson(ndjson) {
  return (ndjson || "")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

async function main() {
  if (await fs.stat(FINAL_PPTX).catch(() => undefined)) {
    throw new Error(`Output already exists: ${FINAL_PPTX}`);
  }
  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });

  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceHash = sha256(sourceBuffer);
  if (sourceHash !== EXPECTED_SOURCE_SHA256) {
    throw new Error(`Source deck changed before the notes edit: ${sourceHash}`);
  }

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

  for (const [slideNumber, text] of NOTES) {
    const slide = slides[slideNumber - 1];
    slide.speakerNotes.textFrame.setText(text);
    slide.speakerNotes.setVisible(true);
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);

  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed during the notes edit");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  for (const slideNumber of NOTES.keys()) {
    const partName = `ppt/notesSlides/notesSlide${slideNumber}.xml`;
    const notesXml = await artifactZip.file(partName)?.async("string");
    if (!notesXml) throw new Error(`Artifact candidate is missing ${partName}`);
    sourceZip.file(partName, notesXml);
  }

  const hybridCandidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    hybridCandidatePath,
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
    candidatePath: hybridCandidatePath,
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
    receiptPath: path.join(BUILD_DIR, "notes52_57.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalNotes = parseNdjson(
    (await reopened.inspect({ kind: "notes", maxChars: 5000000 })).ndjson,
  );
  const notesBySlide = new Map(
    finalNotes
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text]),
  );
  for (const [slideNumber, expectedText] of NOTES) {
    if (notesBySlide.get(slideNumber)?.trim() !== expectedText.trim()) {
      throw new Error(`Speaker notes do not match on slide ${slideNumber}`);
    }
  }

  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const expectedChangedParts = new Set(
    [...NOTES.keys()].map((number) => `ppt/notesSlides/notesSlide${number}.xml`),
  );
  const changedParts = [];
  for (const [name, entry] of Object.entries(sourceZip.files)) {
    if (entry.dir) continue;
    const sourceEntry = originalZip.file(name);
    const finalEntry = finalZip.file(name);
    if (!sourceEntry || !finalEntry) throw new Error(`Missing package part: ${name}`);
    const [before, after] = await Promise.all([
      sourceEntry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) changedParts.push(name);
  }
  changedParts.sort();
  const expected = [...expectedChangedParts].sort();
  if (
    changedParts.length !== expected.length ||
    changedParts.some((name, index) => name !== expected[index])
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
        updatedSlides: [...NOTES.keys()],
        changedParts,
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
