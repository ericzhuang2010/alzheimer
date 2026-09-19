#!/usr/bin/env node

/** Update slides 11 and 12 speaker notes without changing visible content. */

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
  "results/presentations/09162026_slides11_12_script_update/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slides11_12_script_update/output/09162026_sex_apoe_kda_fine_broad_slides11_12_notes_synced.pptx",
);
const EXPECTED_SLIDES = 162;

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

function structuredNotes({ goal, walkthrough, boundary, transition }) {
  return [
    `Teaching goal: ${goal}`,
    "",
    `Walk through: ${walkthrough}`,
    "",
    `Scientific boundary: ${boundary}`,
    "",
    `Transition: ${transition}`,
  ].join("\n");
}

function slide11Notes() {
  return structuredNotes({
    goal: "Define the OXPHOS dominant direction percentage before showing the bars.",
    walkthrough:
      "The calculation is performed separately for each sex/APOE group and each OXPHOS gene set. One occurrence means that one pathway gene is a significant DEG in one fine-cell comparison. A gene can therefore contribute again when it is significant in another fine cell type. Count the upregulated and downregulated occurrences. The dominant direction percentage equals the larger count divided by the total number of upregulated plus downregulated occurrences, multiplied by 100. For male epsilon-3 homozygous mtDNA-encoded OXPHOS, 70 occurrences increased and 11 decreased. Seventy divided by 81 equals 86 percent, so upregulation is the dominant direction. On the next chart, positive bars mean upregulation is dominant, negative bars mean downregulation is dominant, and color identifies the OXPHOS gene set.",
    boundary:
      "This percentage is not a fold change, the percentage of unique genes, cells, donors, or fine cell types, an enrichment result, or a measure of OXPHOS activity. Repeated occurrences across fine cell types are not independent biological replications.",
    transition: "Apply this percentage across the six sex/APOE groups.",
  });
}

function slide12Notes() {
  return structuredNotes({
    goal: "Interpret OXPHOS DEG direction across the six sex/APOE groups.",
    walkthrough:
      "OXPHOS, or oxidative phosphorylation, is the mitochondrial process that produces most cellular ATP. Blue bars summarize the 13 OXPHOS genes encoded by mitochondrial DNA, and striped orange bars summarize 86 structural OXPHOS genes encoded by nuclear DNA. Using the percentage defined on the previous slide, positive bars mean upregulation is more common and negative bars mean downregulation is more common. Female epsilon-2 is up in both gene sets, at 99 and 98 percent. Female epsilon-3 homozygous is also up in both, at 100 and 85 percent. Female epsilon-4 is down in both, at 59 and 95 percent, and male epsilon-2 is down in both, at 90 and 87 percent. Male epsilon-3 homozygous shows the clearest split: 86 percent up for mitochondrial-DNA genes and 88 percent down for nuclear-encoded genes. Male epsilon-4 shows the same split more weakly, at 79 percent up and 62 percent down.",
    boundary:
      "The bar labels show the share of repeated gene-by-fine-cell DEG occurrences in the more common direction. They are not percent expression change, percent of cells or donors, percent of unique genes, an effect size, pathway enrichment, OXPHOS activity, or a direct statistical interaction between disease, sex, and APOE.",
    transition: "Focus first on the female epsilon-3 homozygous mitochondrial increase.",
  });
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

  const titleCheck = await presentation.inspect({
    kind: "slide,textbox,notes",
    search: "How the OXPHOS direction percentage is calculated|OXPHOS gene directions vary across sex/APOE groups",
    maxChars: 14000,
  });
  if (!titleCheck.ndjson?.includes('"slide":11')) {
    throw new Error("Could not verify the slide 11 title");
  }
  if (!titleCheck.ndjson?.includes('"slide":12')) {
    throw new Error("Could not verify the slide 12 title");
  }

  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
  if (await fs.stat(FINAL_PPTX).catch(() => undefined)) {
    throw new Error(`Output already exists: ${FINAL_PPTX}`);
  }
  await fs.writeFile(path.join(BUILD_DIR, "before.ndjson"), titleCheck.ndjson || "", "utf8");

  const targets = [slides[10], slides[11]];
  const beforePngs = [];
  for (let index = 0; index < targets.length; index += 1) {
    const slideNumber = index + 11;
    const png = await blobBuffer(
      await presentation.export({ slide: targets[index], format: "png", scale: 1 }),
    );
    beforePngs.push(png);
    await fs.writeFile(
      path.join(BUILD_DIR, `slide-${String(slideNumber).padStart(2, "0")}-before.png`),
      png,
    );
  }

  targets[0].speakerNotes.textFrame.setText(slide11Notes());
  targets[0].speakerNotes.setVisible(true);
  targets[1].speakerNotes.textFrame.setText(slide12Notes());
  targets[1].speakerNotes.setVisible(true);

  for (let index = 0; index < targets.length; index += 1) {
    const slideNumber = index + 11;
    const afterPng = await blobBuffer(
      await presentation.export({ slide: targets[index], format: "png", scale: 1 }),
    );
    await fs.writeFile(
      path.join(BUILD_DIR, `slide-${String(slideNumber).padStart(2, "0")}-after.png`),
      afterPng,
    );
    if (sha256(beforePngs[index]) !== sha256(afterPng)) {
      throw new Error(`Visible slide ${slideNumber} content changed while updating notes`);
    }
  }

  const afterInspect = await presentation.inspect({
    kind: "slide,textbox,notes",
    search: "Define the OXPHOS dominant direction percentage|Female epsilon-2 is up in both gene sets",
    maxChars: 14000,
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
      "09162026_sex_apoe_kda_fine_broad_slides11_12_notes_synced.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  for (let index = 0; index < 2; index += 1) {
    const slideNumber = index + 11;
    const finalPng = await blobBuffer(
      await reopened.export({
        slide: reopenedSlides[slideNumber - 1],
        format: "png",
        scale: 1,
      }),
    );
    await fs.writeFile(
      path.join(BUILD_DIR, `slide-${String(slideNumber).padStart(2, "0")}-final.png`),
      finalPng,
    );
    if (sha256(beforePngs[index]) !== sha256(finalPng)) {
      throw new Error(`Finalized deck changed visible slide ${slideNumber} content`);
    }
  }

  const notesCheck = await reopened.inspect({
    kind: "notes",
    search: "Seventy divided by 81 equals 86 percent|Female epsilon-4 is down in both",
    maxChars: 12000,
  });
  if (!notesCheck.ndjson?.includes('"slide":11')) {
    throw new Error("Updated slide 11 notes were not found after finalization");
  }
  if (!notesCheck.ndjson?.includes('"slide":12')) {
    throw new Error("Updated slide 12 notes were not found after finalization");
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        output: FINAL_PPTX,
        slides: [11, 12],
        visibleSlidesPreserved: true,
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
