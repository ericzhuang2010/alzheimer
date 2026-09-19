#!/usr/bin/env node

/** Update slide 12 speaker notes without changing visible slide content. */

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
  "results/presentations/09162026_slide12_script_refresh/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slide12_script_refresh/output/09162026_sex_apoe_kda_fine_broad_slide12_notes_refreshed.pptx",
);
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
    "Teaching goal: Interpret OXPHOS DEG direction across sex/APOE groups and highlight the contrasting epsilon-3 homozygous patterns.",
    "",
    "Walk through: OXPHOS, or oxidative phosphorylation, is the mitochondrial process that produces most cellular ATP. Blue bars summarize the 13 OXPHOS genes encoded by mitochondrial DNA, and orange bars summarize 86 structural OXPHOS genes encoded by nuclear DNA. Every bar starts at the 50 percent line, where upregulated and downregulated occurrences are equally common. Bars extend upward when more than half of the occurrences are upregulated and downward when fewer than half are upregulated. The label at the end of each bar gives the actual upregulated percentage, while bar length shows its percentage-point distance from 50 percent. The key contrast is shown in the callout. In female epsilon-3 homozygous, both gene sets are predominantly upregulated: 100 percent for the mitochondrial-DNA set and 85 percent for the nuclear-DNA set. In male epsilon-3 homozygous, the two sets diverge: 86 percent of mitochondrial-DNA occurrences are upregulated, but only 12 percent of nuclear-DNA occurrences are upregulated, which means 88 percent are downregulated. The broader pattern is that female epsilon-2 is predominantly upregulated in both sets, female epsilon-4 and male epsilon-2 are predominantly downregulated in both, and male epsilon-4 shows a weaker version of the male epsilon-3 homozygous split.",
    "",
    "Scientific boundary: The bars show the share of repeated gene-by-fine-cell DEG occurrences that are upregulated. The vertical displacement from 50 percent is a descriptive percentage-point difference, not an effect size. The chart does not show percent expression change, percent of cells or donors, percent of unique genes, pathway enrichment, OXPHOS activity, or a direct statistical interaction between disease, sex, and APOE.",
    "",
    "Transition: Now move to Part 3, where mitochondrial DEGs become network-analysis queries.",
  ].join("\n");
}

function relationshipTarget(relsXml, relationshipTypeSuffix) {
  for (const match of relsXml.matchAll(/<Relationship\b[^>]*>/g)) {
    const tag = match[0];
    if (!tag.includes(`/relationships/${relationshipTypeSuffix}`)) continue;
    const target = tag.match(/\bTarget="([^"]+)"/)?.[1];
    if (target) return target;
  }
  return undefined;
}

async function main() {
  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceHash = sha256(sourceBuffer);
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
      "Share of OXPHOS DEG occurrences that are upregulated|Female ε3/ε3: both OXPHOS sets mostly rise",
    maxChars: 18000,
  });
  if (!beforeInspect.ndjson?.includes('"slide":12')) {
    throw new Error("Could not verify the revised slide 12");
  }
  await fs.writeFile(
    path.join(BUILD_DIR, "before.ndjson"),
    beforeInspect.ndjson || "",
    "utf8",
  );

  const beforePng = await blobBuffer(
    await presentation.export({ slide: slides[11], format: "png", scale: 1 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-12-before.png"), beforePng);

  slides[11].speakerNotes.textFrame.setText(notesText());
  slides[11].speakerNotes.setVisible(true);

  const afterPng = await blobBuffer(
    await presentation.export({ slide: slides[11], format: "png", scale: 1 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-12-after.png"), afterPng);
  if (sha256(beforePng) !== sha256(afterPng)) {
    throw new Error("Visible slide 12 content changed while updating speaker notes");
  }

  const afterInspect = await presentation.inspect({
    kind: "slide,textbox,notes,chart,layout",
    search:
      "The key contrast is shown in the callout|which means 88 percent are downregulated",
    maxChars: 18000,
  });
  await fs.writeFile(
    path.join(BUILD_DIR, "after.ndjson"),
    afterInspect.ndjson || "",
    "utf8",
  );

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  const currentSourceBuffer = await fs.readFile(SOURCE);
  if (sha256(currentSourceBuffer) !== sourceHash) {
    throw new Error("The source presentation changed during the notes update");
  }

  const artifactCandidateBuffer = await fs.readFile(artifactCandidatePath);
  const sourceZip = await JSZip.loadAsync(currentSourceBuffer);
  const artifactZip = await JSZip.loadAsync(artifactCandidateBuffer);
  const slideRelsPath = "ppt/slides/_rels/slide12.xml.rels";
  const slideRels = await sourceZip.file(slideRelsPath)?.async("string");
  if (!slideRels) throw new Error(`Missing ${slideRelsPath}`);
  const notesTarget = relationshipTarget(slideRels, "notesSlide");
  if (!notesTarget) throw new Error("Could not resolve the slide 12 notes relationship");
  const notesPath = path.posix.normalize(path.posix.join("ppt/slides", notesTarget));
  const updatedNotesXml = await artifactZip.file(notesPath)?.async("string");
  if (!updatedNotesXml?.includes("The key contrast is shown in the callout")) {
    throw new Error("Artifact candidate does not contain the updated slide 12 notes");
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
      referenceSha256: sourceHash,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(
      BUILD_DIR,
      "09162026_sex_apoe_kda_fine_broad_slide12_notes_refreshed.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const finalPng = await blobBuffer(
    await reopened.export({ slide: reopenedSlides[11], format: "png", scale: 1 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-12-final.png"), finalPng);
  if (sha256(beforePng) !== sha256(finalPng)) {
    throw new Error("Finalized deck changed visible slide 12 content");
  }

  const finalInspect = await reopened.inspect({
    kind: "slide,textbox,notes,chart",
    search:
      "The key contrast is shown in the callout|which means 88 percent are downregulated",
    maxChars: 18000,
  });
  await fs.writeFile(
    path.join(BUILD_DIR, "final.ndjson"),
    finalInspect.ndjson || "",
    "utf8",
  );
  if (!finalInspect.ndjson?.includes('"slide":12')) {
    throw new Error("Updated slide 12 notes were not found after finalization");
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        slideCount: EXPECTED_SLIDES,
        updatedSlide: 12,
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
