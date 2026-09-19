#!/usr/bin/env node

/** Update slide 8 speaker notes without changing any visible slide content. */

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
  "results/presentations/09162026_script_sync_after_manual_edit/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_script_sync_after_manual_edit/output/09162026_sex_apoe_kda_fine_broad_slide8_notes_synced.pptx",
);
const EXPECTED_TITLE = "How to calculate pathway and sex/APOE overlap";
const EXPECTED_SLIDES = 160;

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

function notesText() {
  return [
    "Teaching goal: Explain the overlap formula and its worked example.",
    "",
    "Walk through: This percentage summarizes one pathway within one sex/APOE group. The numerator is the number of unique pathway genes that were significant DEGs in at least one fine-cell comparison in that group. The denominator is the total number of genes in the pathway. Multiplying by 100 converts the ratio to a percentage. In the male epsilon-2 mitochondrial-translation example, 130 of the 155 pathway genes appeared as DEGs. Therefore, 130 divided by 155 times 100 equals 84 percent.",
    "",
    "Scientific boundary: Each gene counts once, regardless of how many fine cell types contain it. The percentage does not show the percentage of fine cell types, the direction of change, recurrence across cell types, or pathway enrichment.",
    "",
    "Transition: Now inspect the calculated pathway-gene coverage across the six sex/APOE groups.",
  ].join("\n");
}

async function main() {
  const { importRuntimeModule } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href
  );
  const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const slides = slidesFromPresentation(presentation);
  if (slides.length !== EXPECTED_SLIDES) {
    throw new Error(`Expected ${EXPECTED_SLIDES} slides, found ${slides.length}`);
  }

  const slide = slides[7];
  const titleCheck = await presentation.inspect({
    kind: "slide",
    search: EXPECTED_TITLE,
    maxChars: 2000,
  });
  if (!titleCheck.ndjson?.includes('"slide":8')) {
    throw new Error(`Slide 8 title does not match ${EXPECTED_TITLE}`);
  }

  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
  const outputStat = await fs.stat(FINAL_PPTX).catch(() => undefined);
  if (outputStat) throw new Error(`Output already exists: ${FINAL_PPTX}`);

  const beforePng = await blobBuffer(
    await presentation.export({ slide, format: "png", scale: 1 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-08-before.png"), beforePng);

  slide.speakerNotes.textFrame.setText(notesText());
  slide.speakerNotes.setVisible(true);

  const afterPng = await blobBuffer(
    await presentation.export({ slide, format: "png", scale: 1 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-08-after.png"), afterPng);
  if (sha256(beforePng) !== sha256(afterPng)) {
    throw new Error("Visible slide 8 content changed while updating speaker notes");
  }

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
  const sourceBuffer = await fs.readFile(SOURCE);

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const result = await finalizePresentation({
    explicitTotalSlideCount: EXPECTED_SLIDES,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [],
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
      referenceSha256: sha256(sourceBuffer),
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(
      BUILD_DIR,
      "09162026_sex_apoe_kda_fine_broad_slide8_notes_synced.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlide = slidesFromPresentation(reopened)[7];
  const finalPng = await blobBuffer(
    await reopened.export({ slide: reopenedSlide, format: "png", scale: 1 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-08-final.png"), finalPng);
  if (sha256(beforePng) !== sha256(finalPng)) {
    throw new Error("Finalized deck changed visible slide 8 content");
  }
  const notesCheck = await reopened.inspect({
    kind: "notes",
    search: "130 divided by 155 times 100 equals 84 percent",
    maxChars: 4000,
  });
  if (!notesCheck.ndjson?.includes('"slide":8')) {
    throw new Error("Updated slide 8 notes were not found after finalization");
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        output: FINAL_PPTX,
        slide: 8,
        visibleSlidePreserved: true,
        validation: result,
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});
