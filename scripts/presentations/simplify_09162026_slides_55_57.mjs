#!/usr/bin/env node

/** Simplify wording on slides 55–57 and keep their speaker notes synchronized. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const SKILL_DIR =
  "/Users/rzhuang/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations";
const WORKSPACE_DIR = "/Users/rzhuang/Documents/VscodeProjects/alzheimer";
const SOURCE = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_notes_refresh_20260922_v1/output/09162026_sex_apoe_kda_fine_broad_notes52_57_refreshed_20260922_v1.pptx",
);
const BUILD_DIR = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_notes_refresh_20260922_v4/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_notes_refresh_20260922_v4/output/09162026_sex_apoe_kda_fine_broad_slides55_57_simplified_20260922_v4.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "14a648cb340807fff62aac6095f01c53c69494012f51bfe0f9d484107968abe5";
const SLIDE_COUNT = 160;

const SHAPE_REPLACEMENTS = [
  [
    "These genes recur among KDA calls from multiple sex/APOE groups or connect a repeated mitochondrial theme to network genes.",
    "These genes were returned from KDA calls in several sex/APOE groups or were repeatedly connected to mitochondrial genes.",
  ],
  [
    "Genes returned from KDA calls are hypotheses: network proximity does not establish causal regulation.",
    "Genes returned from KDA calls are candidates. Network connections do not prove regulation or causality.",
  ],
  [
    "These findings remain useful, but their network evidence is narrow, context-dependent, or sparse.",
    "These findings remain useful, but each is based on few genes, few KDA calls, or patterns that change across groups.",
  ],
  [
    "Finding 18 is a secondary gene returned from a KDA call and supported by the completed Phase 19b genetic-support analysis.",
    "Finding 18 remains secondary. INTS8 is a gene returned from one KDA call with Phase 19b genetic support.",
  ],
];

const TABLE_EDITS = new Map([
  [
    55,
    [
      [
        1,
        2,
        "LAMTOR5 connects genes that sense nutrients at lysosomes, the cell’s recycling compartments, with OXPHOS genes.",
      ],
      [
        3,
        2,
        "SELENOW, a gene involved in controlling oxidative stress, was connected to genes involved in mitochondrial respiration, protein production, and removal of damaged mitochondrial proteins.",
      ],
      [
        4,
        2,
        "PGK1 connects astrocyte glycolysis and low-oxygen signaling with genes involved in removing damaged mitochondria.",
      ],
      [
        5,
        2,
        "FTL and ANKRD11 connect iron handling in oligodendrocyte precursor cells with genes that protect against oxidative damage and recycle damaged cell components.",
      ],
    ],
  ],
  [
    56,
    [
      [
        1,
        2,
        "PLCG2 has strong AD genetic evidence, but only one MitoCarta MT gene, MT-CO1, was connected to it in the KDA result.",
      ],
      [
        2,
        2,
        "Astrocyte APOE expression changes in opposite directions across groups, so the result is not specific to ε4.",
      ],
      [
        3,
        2,
        "A small group of genes that respond to protein damage and cellular stress appears in only two female ε4 vascular-cell KDA calls.",
      ],
      [
        4,
        2,
        "INTS8 was returned from one inhibitory-neuron KDA call. Human genetics supports follow-up, but it was not returned from additional KDA calls.",
      ],
    ],
  ],
  [
    57,
    [
      [
        1,
        2,
        "RPL11, RPS15, and related genes that help ribosomes outside mitochondria make proteins are connected to nuclear-encoded OXPHOS genes.",
      ],
      [
        2,
        2,
        "SELENOM, which helps control oxidative stress and calcium inside the endoplasmic reticulum, is connected to genes used for mitochondrial protein production.",
      ],
    ],
  ],
]);

const NOTES = new Map([
  [
    55,
    [
      "This slide summarizes recurring genes returned from KDA calls in selected sex/APOE groups.",
      "",
      "LAMTOR5 connects genes that sense nutrients at lysosomes, the cell’s recycling compartments, with OXPHOS genes. WDR82 is connected to a small set of core MT genes that are upregulated in AD in excitatory neurons.",
      "",
      "SELENOW helps control oxidative stress. Its network connections include genes involved in mitochondrial respiration and protein production, as well as removal of damaged mitochondrial proteins.",
      "",
      "PGK1 connects astrocyte glycolysis and low-oxygen signaling with genes involved in removing damaged mitochondria. FTL and ANKRD11 connect iron handling in oligodendrocyte precursor cells with protection from oxidative damage and recycling of damaged cell components.",
      "",
      "Genes returned from KDA calls are candidates. Network connections do not prove that one gene regulates another or causes the AD-related change.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 8, 9, and 11–13.",
    ].join("\n"),
  ],
  [
    56,
    [
      "These genes remain useful, but each result depends on few genes, few KDA calls, or a pattern that changes across groups.",
      "",
      "PLCG2 has strong Alzheimer’s disease genetic evidence, but only one MitoCarta MT gene, MT-CO1, was connected to it in the KDA result. Astrocyte APOE expression changes in opposite directions across groups, so the result is not specific to ε4.",
      "",
      "A small group of genes that respond to protein damage and cellular stress appears in only two female ε4 vascular-cell KDA calls. INTS8 was returned from one male ε2 inhibitory-neuron KDA call. Human genetics supports follow-up, but INTS8 was not returned from additional KDA calls.",
      "",
      "These findings remain secondary or targeted follow-up candidates. Gene-level genetic evidence does not confirm the cell type, sex/APOE context, or network connection.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 14–16 and 18.",
    ].join("\n"),
  ],
  [
    57,
    [
      "Findings 7, 10, and 17 receive lower priority only because this presentation focuses on differences among sex/APOE groups.",
      "",
      "Findings 7 and 10 occur across all six groups. Finding 7 links RPL11, RPS15, and related genes that help ribosomes outside mitochondria make proteins with nuclear-encoded OXPHOS genes.",
      "",
      "Finding 10 links SELENOM with genes used for mitochondrial protein production. SELENOM helps control oxidative stress and calcium inside the endoplasmic reticulum, the cellular compartment where many proteins are processed.",
      "",
      "Finding 17 compares ROSMAP with SEA-AD. The cohorts agree more clearly on mitochondrial gene-set patterns than on the exact genes returned from KDA calls.",
      "",
      "These findings may still be biologically important or useful as supporting evidence. They simply do not identify a distinct sex/APOE group. Direct interaction models would be needed to test quantitative group differences.",
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

async function replaceUniqueShapeText(presentation, before, after) {
  const records = parseNdjson(
    (await presentation.inspect({ kind: "textbox,shape", search: before, maxChars: 20000 }))
      .ndjson,
  ).filter((record) => (record.text ?? record.textPreview ?? "").includes(before));
  if (records.length !== 1) {
    throw new Error(`Expected one shape containing ${JSON.stringify(before)}, found ${records.length}`);
  }
  const shape = presentation.resolve(records[0].id);
  shape.text.replace(before, after);
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
    throw new Error(`Source deck changed before the edit: ${sourceHash}`);
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

  for (const [before, after] of SHAPE_REPLACEMENTS) {
    await replaceUniqueShapeText(presentation, before, after);
  }

  const tableRecords = parseNdjson(
    (await presentation.inspect({ kind: "table", maxChars: 500000 })).ndjson,
  );
  for (const [slideNumber, edits] of TABLE_EDITS) {
    const records = tableRecords.filter(
      (record) => record.kind === "table" && record.slide === slideNumber,
    );
    if (records.length !== 1) {
      throw new Error(`Expected one table on slide ${slideNumber}, found ${records.length}`);
    }
    const table = presentation.resolve(records[0].id);
    for (const [row, column, value] of edits) table.cells.set(row, column, value);
  }

  for (const [slideNumber, text] of NOTES) {
    const slide = slides[slideNumber - 1];
    slide.speakerNotes.textFrame.setText(text);
    slide.speakerNotes.setVisible(true);
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);

  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed during the edit");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const changedParts = [];
  for (const slideNumber of [55, 56, 57]) {
    for (const partName of [
      `ppt/slides/slide${slideNumber}.xml`,
      `ppt/notesSlides/notesSlide${slideNumber}.xml`,
    ]) {
      const content = await artifactZip.file(partName)?.async("string");
      if (!content) throw new Error(`Artifact candidate is missing ${partName}`);
      sourceZip.file(partName, content);
      changedParts.push(partName);
    }
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
    receiptPath: path.join(BUILD_DIR, "slides55_57.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalNotes = new Map(
    parseNdjson((await reopened.inspect({ kind: "notes", maxChars: 5000000 })).ndjson)
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text]),
  );
  for (const [slideNumber, expectedText] of NOTES) {
    if (finalNotes.get(slideNumber)?.trim() !== expectedText.trim()) {
      throw new Error(`Speaker notes do not match on slide ${slideNumber}`);
    }
  }

  const finalSnapshot = await reopened.inspect({
    kind: "slide,table,textbox,shape",
    maxChars: 1000000,
  });
  const finalText = parseNdjson(finalSnapshot.ndjson)
    .filter((record) => Number.isInteger(record.slide) && record.slide >= 55 && record.slide <= 57)
    .map((record) => record.text ?? record.textPreview ?? record.preview ?? "")
    .join("\n");
  for (const phrase of ["quality control", "heat-shock module", "network recurrence", "ER redox biology"] ) {
    if (finalText.includes(phrase)) throw new Error(`Confusing phrase remains: ${phrase}`);
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const actualChangedParts = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) actualChangedParts.push(name);
  }
  actualChangedParts.sort();
  changedParts.sort();
  if (
    actualChangedParts.length !== changedParts.length ||
    actualChangedParts.some((name, index) => name !== changedParts[index])
  ) {
    throw new Error(`Unexpected package changes: ${actualChangedParts.join(", ")}`);
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
        updatedSlides: [55, 56, 57],
        changedParts: actualChangedParts,
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
