#!/usr/bin/env node

/** Update slide 35 speaker notes without changing visible slide content. */

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
  "results/presentations/09162026_slide35_script_refresh/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slide35_script_refresh/output/09162026_sex_apoe_kda_fine_broad_slide35_notes_refreshed_20260919.pptx",
);
const EXPECTED_SLIDES = 160;
const SLIDE_NUMBER = 35;

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

function slide35Notes() {
  return structuredNotes({
    goal:
      "Define an arm and show the numerical impact of raising the minimum donor requirement from three to five in both cohorts.",
    walkthrough:
      "An arm is one disease-status group within a comparison. In ROSMAP, the two arms are AD and NCI. In SEA-AD, they are dementia and no dementia. A contrast is eligible only when each arm meets the stated donor minimum. Raising that minimum from three to five reduces ROSMAP from 42 to 40 eligible contrasts and from three to two KDA runs. Its returned driver rows fall from 39 to 13, and its unique non-mitochondrial drivers fall from 33 to 13. SEA-AD falls from 28 to 20 eligible contrasts, but its five KDA runs, 24 returned rows, and 18 unique non-mitochondrial drivers remain unchanged.",
    boundary:
      "The threshold test changes only the donor eligibility gate. It does not change the retained contrast models, DEG queries, networks, or KDA settings. A contrast with fewer than five donors in either arm becomes unavailable under the stricter threshold; that exclusion is not a negative KDA result. Source: Phase 22 and VH14 run manifests and returns; donor-per-arm 3-versus-5 sensitivity assessment dated 2026-09-11.",
    transition:
      "Interpret why the two cohorts respond differently to the donor threshold.",
  });
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
  const notesPart = relation.Target.startsWith("/")
    ? relation.Target.slice(1)
    : path.posix.normalize(path.posix.join(path.posix.dirname(slidePart), relation.Target));
  return notesPart;
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

  const targetSlide = slides[SLIDE_NUMBER - 1];
  const beforeInspect = await presentation.inspect({
    kind: "slide,textbox,notes,chart,layout",
    search: "Donor-threshold sensitivity|An arm is one disease-status group",
    maxChars: 18000,
  });
  if (!beforeInspect.ndjson?.includes(`"slide":${SLIDE_NUMBER}`)) {
    throw new Error("Could not verify slide 35 content and notes");
  }
  await fs.writeFile(path.join(BUILD_DIR, "before.ndjson"), beforeInspect.ndjson || "", "utf8");

  const beforePng = await blobBuffer(
    await presentation.export({ slide: targetSlide, format: "png", scale: 2 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-35-before.png"), beforePng);

  targetSlide.speakerNotes.textFrame.setText(slide35Notes());
  targetSlide.speakerNotes.setVisible(true);

  const afterPng = await blobBuffer(
    await presentation.export({ slide: targetSlide, format: "png", scale: 2 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-35-after.png"), afterPng);
  if (sha256(beforePng) !== sha256(afterPng)) {
    throw new Error("Visible slide 35 content changed while updating speaker notes");
  }

  const afterInspect = await presentation.inspect({
    kind: "slide,textbox,notes,chart,layout",
    search: "Define an arm and show the numerical impact|An arm is one disease-status group within a comparison",
    maxChars: 18000,
  });
  await fs.writeFile(path.join(BUILD_DIR, "after.ndjson"), afterInspect.ndjson || "", "utf8");

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);

  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const sourceSlidePart = await visibleSlidePart(sourceZip, SLIDE_NUMBER);
  const artifactSlidePart = await visibleSlidePart(artifactZip, SLIDE_NUMBER);
  const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
  const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
  const updatedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
  if (!updatedNotesXml?.includes("An arm is one disease-status group within a comparison")) {
    throw new Error("Artifact candidate does not contain the updated slide 35 notes");
  }
  sourceZip.file(sourceNotesPart, updatedNotesXml);
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
    nativeChartTargetApplication: "powerpoint",
    workspaceDir: WORKSPACE_DIR,
    candidatePath,
    finalPath: FINAL_PPTX,
    pythonExecutable:
      "/Users/rzhuang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
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
      "09162026_sex_apoe_kda_fine_broad_slide35_notes_refreshed_20260919.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const finalPng = await blobBuffer(
    await reopened.export({ slide: reopenedSlides[SLIDE_NUMBER - 1], format: "png", scale: 2 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-35-final.png"), finalPng);
  if (sha256(beforePng) !== sha256(finalPng)) {
    throw new Error("Finalized deck changed visible slide 35 content");
  }

  const finalInspect = await reopened.inspect({
    kind: "slide,textbox,notes,chart",
    search: "Define an arm and show the numerical impact|An arm is one disease-status group within a comparison",
    maxChars: 18000,
  });
  await fs.writeFile(path.join(BUILD_DIR, "final.ndjson"), finalInspect.ndjson || "", "utf8");
  if (!finalInspect.ndjson?.includes(`"slide":${SLIDE_NUMBER}`)) {
    throw new Error("Updated slide 35 notes were not found after finalization");
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
  if (changedParts.length !== 1 || changedParts[0] !== sourceNotesPart) {
    throw new Error(`Unexpected package changes: ${changedParts.join(", ")}`);
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sha256(sourceBuffer),
        output: FINAL_PPTX,
        slideCount: EXPECTED_SLIDES,
        updatedSlide: SLIDE_NUMBER,
        visibleSlidePreserved: true,
        changedParts,
        validation: result,
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
