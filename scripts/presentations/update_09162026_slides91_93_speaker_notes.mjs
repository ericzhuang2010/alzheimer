#!/usr/bin/env node

/** Update only slides 91–93 speaker notes after the user revised the slides. */

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
  "results/presentations/09162026_slides91_93_notes_20260922_v1/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slides91_93_notes_20260922_v1/output/09162026_sex_apoe_kda_fine_broad_slides91_93_notes_refreshed_20260922_v1.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "abfcb264092ffed4b53387c1616621aeeb1bdc491ec2f26162ed18f54c69ddb0";
const SLIDE_COUNT = 160;

const NOTES = new Map([
  [
    91,
    [
      "Teaching goal: Present the primary ROSMAP evidence for Finding 6 and explain why the opposite-direction pattern remains provisional.",
      "",
      "Walk through: Core MT genes contributed 110 DEG occurrences, with 87 upregulated and 23 downregulated, so 79 percent were upregulated. Nuclear-encoded OXPHOS genes contributed 89 occurrences, with 34 upregulated and 55 downregulated, so 62 percent were downregulated.",
      "",
      "Evidence of opposite direction means that the dominant direction differs between the two gene sets: core MT genes are mainly upregulated, while nuclear-encoded OXPHOS genes are mainly downregulated. This is a qualitative interpretation, not a separate statistical score. The nuclear result is fairly mixed, which makes the pattern weaker than Finding 2 and supports the label possible rather than definitive.",
      "",
      "The enrichment counts provide a second view. Core MT enrichment appeared broadly across the eligible calls, whereas significant nuclear-encoded OXPHOS enrichment appeared in only three eligible calls.",
      "",
      "Scientific boundary: DEG occurrences can repeat the same gene across fine cell types. They are not counts of unique genes, donors, or cells, and the percentages do not measure expression magnitude or mitochondrial function.",
      "",
      "Transition: Next, compare the fine-cell summary with the direct broad-cell results in ROSMAP and SEA-AD.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 6. Literature: https://doi.org/10.1016/j.neuron.2019.03.075; https://doi.org/10.1016/j.celrep.2023.113183; https://doi.org/10.1186/s13024-023-00624-5",
    ].join("\n"),
  ],
  [
    92,
    [
      "Teaching goal: Compare the male APOE ε4 opposite-direction pattern across analysis resolutions and cohorts.",
      "",
      "Walk through: In the direct ROSMAP excitatory-neuron analysis, the core MT pathway had a positive normalized enrichment score of 2.03 and the nuclear-encoded OXPHOS pathway had a negative score of 1.72. Both results remained significant after adjustment for broad-cell composition, so the ROSMAP broad-cell result supports the same opposite directions shown by the fine-cell summary.",
      "",
      "SEA-AD did not reproduce the nuclear direction. Its excitatory-neuron nuclear-encoded OXPHOS score was positive 2.46, and its core MT result was not significant. SEA-AD also had no active male APOE ε4 fine-cell KDA query, so it cannot test the finding at the same fine-cell KDA resolution.",
      "",
      "Cross-resolution disagreement means that the fine-cell summary and direct broad-cell analyses do not give a consistent result across both cohorts. This keeps the male APOE ε4 mismatch provisional.",
      "",
      "Scientific boundary: A direct broad-cell result is calculated from donor-level expression for the broad cell type. It is different from aggregating results across fine cell types. Differences in cohort composition and cell resolution can contribute to disagreement.",
      "",
      "Transition: Explain what the weaker pattern could mean and why direct group comparisons are required.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 6. Literature: https://doi.org/10.1016/j.neuron.2019.03.075; https://doi.org/10.1016/j.celrep.2023.113183; https://doi.org/10.1186/s13024-023-00624-5",
    ].join("\n"),
  ],
  [
    93,
    [
      "Teaching goal: Explain why Finding 6 may matter without overstating the evidence.",
      "",
      "Walk through: Finding 6 resembles Finding 2 because core MT genes mainly increase while nuclear-encoded OXPHOS genes mainly decrease. The APOE ε4 pattern is weaker because its nuclear component contains many more upregulated occurrences than the male APOE ε3/ε3 result.",
      "",
      "Separate analyses of male APOE ε3/ε3 and male APOE ε4 cannot determine whether the pattern is a general male response or differs by APOE genotype. That question requires a direct statistical comparison across groups.",
      "",
      "A prespecified balance score would summarize the relative directions of the core MT and nuclear-encoded OXPHOS gene sets using a rule defined before comparing groups. Applying the same score to every group would provide a direct test of whether the opposite-direction evidence differs across sex and APOE groups.",
      "",
      "Scientific boundary: This remains a hypothesis. RNA direction does not establish OXPHOS protein imbalance, mitochondrial dysfunction, or an APOE-dependent effect.",
      "",
      "Transition: Place Finding 6 in the context of prior research and summarize its evidence level.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 6. Literature: https://doi.org/10.1016/j.neuron.2019.03.075; https://doi.org/10.1016/j.celrep.2023.113183; https://doi.org/10.1186/s13024-023-00624-5",
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
  const notesParts = [];
  for (const slideNumber of NOTES.keys()) {
    const partName = `ppt/notesSlides/notesSlide${slideNumber}.xml`;
    const notesXml = await artifactZip.file(partName)?.async("string");
    if (!notesXml) throw new Error(`Artifact candidate is missing ${partName}`);
    sourceZip.file(partName, notesXml);
    notesParts.push(partName);
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
    receiptPath: path.join(BUILD_DIR, "slides91_93_notes.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const notesBySlide = new Map(
    parseNdjson((await reopened.inspect({ kind: "notes", maxChars: 5000000 })).ndjson)
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
  const changedParts = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) changedParts.push(name);
  }
  changedParts.sort();
  notesParts.sort();
  if (
    changedParts.length !== notesParts.length ||
    changedParts.some((name, index) => name !== notesParts[index])
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
