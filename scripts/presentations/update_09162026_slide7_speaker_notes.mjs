#!/usr/bin/env node

/** Update slide 7 speaker notes without changing visible slide content. */

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
  "results/presentations/09162026_slide7_script_update/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slide7_script_update/output/09162026_sex_apoe_kda_fine_broad_slide7_notes_synced.pptx",
);
const EXPECTED_TITLE = "How the pathway analysis was done";
const EXPECTED_SLIDES = 161;

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
    "Teaching goal: Explain the two-stage pathway analysis and define a significant result.",
    "",
    "Walk through: Each estimable fine-cell sex/APOE contrast was analyzed separately. For each contrast, the analysis created three mitochondrial DEG lists: all significant DEGs, genes up-regulated in AD, and genes down-regulated in AD. It then tested each pathway to ask whether the DEG list contained more pathway genes than expected among genes detectable in the same contrast. A significant result means that the greater-than-expected overlap remained significant after Benjamini-Hochberg correction across the pathways in the same collection for that DEG list, with a false-discovery rate below 5 percent. Twelve of the 46 Level 1 and Level 2 pathways and 18 of the 149 complete pathways had at least one significant result. Most significant results involved overlapping OXPHOS pathways. Non-OXPHOS signals were fewer and more localized.",
    "",
    "Scientific boundary: The complete 149-pathway collection contains the 46 Level 1 and Level 2 pathways, so the two reported scopes overlap. At least one significant result means enrichment in at least one fine-cell, sex/APOE, and DEG direction list. It does not mean significance in every group or prove altered pathway activity.",
    "",
    "Transition: Focus next on four mitochondrial pathways used repeatedly in the later findings.",
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

  const slide = slides[6];
  const titleCheck = await presentation.inspect({
    kind: "slide,textbox,notes",
    search: EXPECTED_TITLE,
    maxChars: 6000,
  });
  if (!titleCheck.ndjson?.includes('"slide":7')) {
    throw new Error(`Slide 7 title does not match ${EXPECTED_TITLE}`);
  }

  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
  if (await fs.stat(FINAL_PPTX).catch(() => undefined)) {
    throw new Error(`Output already exists: ${FINAL_PPTX}`);
  }

  await fs.writeFile(path.join(BUILD_DIR, "before.ndjson"), titleCheck.ndjson || "", "utf8");
  const beforePng = await blobBuffer(
    await presentation.export({ slide, format: "png", scale: 1 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-07-before.png"), beforePng);

  slide.speakerNotes.textFrame.setText(notesText());
  slide.speakerNotes.setVisible(true);

  const afterPng = await blobBuffer(
    await presentation.export({ slide, format: "png", scale: 1 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-07-after.png"), afterPng);
  if (sha256(beforePng) !== sha256(afterPng)) {
    throw new Error("Visible slide 7 content changed while updating speaker notes");
  }

  const afterInspect = await presentation.inspect({
    kind: "slide,textbox,notes",
    search: "Explain the two-stage pathway analysis|Non-OXPHOS signals were fewer",
    maxChars: 8000,
  });
  await fs.writeFile(
    path.join(BUILD_DIR, "after.ndjson"),
    afterInspect.ndjson || "",
    "utf8",
  );

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
      "09162026_sex_apoe_kda_fine_broad_slide7_notes_synced.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlide = slidesFromPresentation(reopened)[6];
  const finalPng = await blobBuffer(
    await reopened.export({ slide: reopenedSlide, format: "png", scale: 1 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-07-final.png"), finalPng);
  if (sha256(beforePng) !== sha256(finalPng)) {
    throw new Error("Finalized deck changed visible slide 7 content");
  }
  const notesCheck = await reopened.inspect({
    kind: "notes",
    search: "Non-OXPHOS signals were fewer and more localized",
    maxChars: 5000,
  });
  if (!notesCheck.ndjson?.includes('"slide":7')) {
    throw new Error("Updated slide 7 notes were not found after finalization");
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        output: FINAL_PPTX,
        slide: 7,
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
