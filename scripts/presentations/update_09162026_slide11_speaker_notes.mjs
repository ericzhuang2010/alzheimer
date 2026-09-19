#!/usr/bin/env node

/** Update slide 11 speaker notes without changing visible slide content. */

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
  "results/presentations/09162026_slide11_script_refresh/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slide11_script_refresh/output/09162026_sex_apoe_kda_fine_broad_slide11_notes_refreshed.pptx",
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
    goal:
      "Define an occurrence and show how the upregulated OXPHOS occurrence percentage is calculated.",
    walkthrough:
      "Begin with the counting unit highlighted on the slide. One occurrence means that one pathway gene is a significant DEG in one fine-cell comparison. If the same gene is significant in another fine cell type, it contributes another occurrence. The calculation is performed separately for each sex/APOE group and each OXPHOS gene set. Divide the upregulated occurrences by all upregulated plus downregulated occurrences, then multiply by 100. In the male epsilon-3 homozygous mtDNA-encoded OXPHOS example, 70 occurrences were upregulated and 11 were downregulated. Seventy divided by 81 equals 86 percent upregulated. A value of 50 percent means the two directions occur equally often. Values above 50 percent favor upregulation, while values below 50 percent favor downregulation.",
    boundary:
      "This occurrence-based summary gives more weight to genes that recur across fine-cell comparisons. It is not a fold change, the percentage of unique genes, cells, donors, or fine cell types, an enrichment result, or a measure of OXPHOS activity. Repeated occurrences are not independent biological replications.",
    transition:
      "Compare the upregulated occurrence percentage across the six sex/APOE groups.",
  });
}

async function main() {
  const sourceStat = await fs.stat(SOURCE).catch(() => undefined);
  if (!sourceStat?.isFile()) throw new Error(`Missing source deck: ${SOURCE}`);
  if (await fs.stat(FINAL_PPTX).catch(() => undefined)) {
    throw new Error(`Output already exists: ${FINAL_PPTX}`);
  }
  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });

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

  const beforeInspect = await presentation.inspect({
    kind: "slide,textbox,notes,chart,layout",
    search:
      "How the upregulated occurrence percentage is calculated|Define the percentage of OXPHOS DEG occurrences",
    maxChars: 18000,
  });
  if (!beforeInspect.ndjson?.includes('"slide":11')) {
    throw new Error("Could not verify the slide 11 title and notes");
  }
  await fs.writeFile(
    path.join(BUILD_DIR, "before.ndjson"),
    beforeInspect.ndjson || "",
    "utf8",
  );

  const beforePng = await blobBuffer(
    await presentation.export({ slide: slides[10], format: "png", scale: 1 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-11-before.png"), beforePng);

  slides[10].speakerNotes.textFrame.setText(slide11Notes());
  slides[10].speakerNotes.setVisible(true);

  const afterPng = await blobBuffer(
    await presentation.export({ slide: slides[10], format: "png", scale: 1 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-11-after.png"), afterPng);
  if (sha256(beforePng) !== sha256(afterPng)) {
    throw new Error("Visible slide 11 content changed while updating speaker notes");
  }

  const afterInspect = await presentation.inspect({
    kind: "slide,textbox,notes,chart,layout",
    search:
      "Define an occurrence and show how|Begin with the counting unit highlighted on the slide",
    maxChars: 18000,
  });
  await fs.writeFile(
    path.join(BUILD_DIR, "after.ndjson"),
    afterInspect.ndjson || "",
    "utf8",
  );

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  const sourceBuffer = await fs.readFile(SOURCE);
  const artifactCandidateBuffer = await fs.readFile(artifactCandidatePath);
  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(artifactCandidateBuffer);
  const slide11RelsPath = "ppt/slides/_rels/slide11.xml.rels";
  const slide11Rels = await sourceZip.file(slide11RelsPath)?.async("string");
  const notesTarget = slide11Rels?.match(
    /Type="[^"]*\/notesSlide"\s+Target="([^"]+)"/,
  )?.[1];
  if (!notesTarget) {
    throw new Error("Could not resolve slide 11 notes relationship");
  }
  const notesPath = path.posix.normalize(path.posix.join("ppt/slides", notesTarget));
  const updatedNotesXml = await artifactZip.file(notesPath)?.async("string");
  if (!updatedNotesXml?.includes("Begin with the counting unit highlighted on the slide")) {
    throw new Error("Artifact candidate does not contain the updated slide 11 notes");
  }
  sourceZip.file(notesPath, updatedNotesXml);
  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
    await sourceZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const result = await finalizePresentation({
    explicitTotalSlideCount: EXPECTED_SLIDES,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [12],
    requiredEmbeddedWorkbookChartOwnerSlides: [12],
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
      "09162026_sex_apoe_kda_fine_broad_slide11_notes_refreshed.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const finalPng = await blobBuffer(
    await reopened.export({ slide: reopenedSlides[10], format: "png", scale: 1 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-11-final.png"), finalPng);
  if (sha256(beforePng) !== sha256(finalPng)) {
    throw new Error("Finalized deck changed visible slide 11 content");
  }

  const finalInspect = await reopened.inspect({
    kind: "slide,textbox,notes,chart",
    search:
      "Define an occurrence and show how|Begin with the counting unit highlighted on the slide",
    maxChars: 18000,
  });
  await fs.writeFile(
    path.join(BUILD_DIR, "final.ndjson"),
    finalInspect.ndjson || "",
    "utf8",
  );
  if (!finalInspect.ndjson?.includes('"slide":11')) {
    throw new Error("Updated slide 11 notes were not found after finalization");
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sha256(sourceBuffer),
        output: FINAL_PPTX,
        slideCount: EXPECTED_SLIDES,
        updatedSlide: 11,
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
