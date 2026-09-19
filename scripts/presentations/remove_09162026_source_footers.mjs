#!/usr/bin/env node

/** Remove visible bottom-of-slide Source: text boxes while retaining citations in notes. */

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
  "results/presentations/09162026_remove_source_footers/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_remove_source_footers/output/09162026_sex_apoe_kda_fine_broad_no_source_footers.pptx",
);
const EXPECTED_SLIDES = 160;
const EXPECTED_SOURCE_FOOTERS = 95;
const SENSITIVITY_SOURCES = new Map([
  [
    35,
    "Source: Phase 22 and VH14 run manifests/returns; donor-per-arm 3-vs-5 sensitivity assessment (2026-09-11).",
  ],
  [
    36,
    "Source: Phase 22 and VH14 run manifests/returns; donor-per-arm 3-vs-5 sensitivity assessment (2026-09-11).",
  ],
  [
    37,
    "Source: validated Phase 22 and VH14 run manifests and significant-return tables (2026-09-11).",
  ],
  [
    38,
    "Source: validated Phase 22 and VH14 run manifests and significant-return tables (2026-09-11).",
  ],
  [
    39,
    "Source: validated Phase 22 and VH14 run manifests and significant-return tables (2026-09-11).",
  ],
]);

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

function parseNdjson(ndjson) {
  return (ndjson || "")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function relationshipTags(xml) {
  return [...xml.matchAll(/<Relationship\b[^>]*\/>/g)].map((match) => match[0]);
}

function relationshipAttribute(tag, name) {
  return tag.match(new RegExp(`\\b${name}="([^"]+)"`))?.[1];
}

function relationshipPartPath(ownerPartPath) {
  return path.posix.join(
    path.posix.dirname(ownerPartPath),
    "_rels",
    `${path.posix.basename(ownerPartPath)}.rels`,
  );
}

function targetPartPath(ownerPartPath, target) {
  if (target.startsWith("/")) return target.slice(1);
  return path.posix.normalize(
    path.posix.join(path.posix.dirname(ownerPartPath), target),
  );
}

async function relatedPartPath(zip, ownerPartPath, relationshipTypeSuffix) {
  const relsPath = relationshipPartPath(ownerPartPath);
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing ${relsPath}`);
  for (const tag of relationshipTags(relsXml)) {
    const type = relationshipAttribute(tag, "Type");
    if (!type?.endsWith(`/relationships/${relationshipTypeSuffix}`)) continue;
    const target = relationshipAttribute(tag, "Target");
    if (target) return targetPartPath(ownerPartPath, target);
  }
  throw new Error(`${ownerPartPath} lacks a ${relationshipTypeSuffix} relationship`);
}

async function orderedSlidePartPaths(zip) {
  const presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  const presentationRelsXml = await zip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  if (!presentationXml || !presentationRelsXml) {
    throw new Error("The presentation package lacks slide-order metadata");
  }
  const targetsById = new Map();
  for (const tag of relationshipTags(presentationRelsXml)) {
    const type = relationshipAttribute(tag, "Type");
    if (!type?.endsWith("/relationships/slide")) continue;
    const id = relationshipAttribute(tag, "Id");
    const target = relationshipAttribute(tag, "Target");
    if (id && target) targetsById.set(id, targetPartPath("ppt/presentation.xml", target));
  }
  const slideIdTags = [...presentationXml.matchAll(/<p:sldId\b[^>]*\/>/g)].map(
    (match) => match[0],
  );
  return slideIdTags.map((tag) => {
    const id = relationshipAttribute(tag, "r:id");
    const partPath = id && targetsById.get(id);
    if (!partPath) throw new Error(`Could not resolve slide relationship ${id}`);
    return partPath;
  });
}

function removeSourceFooterShapes(slideXml) {
  let removed = 0;
  const xml = slideXml.replace(/<p:sp\b[\s\S]*?<\/p:sp>/g, (shapeXml) => {
    if (!shapeXml.includes("<a:t>Source:")) return shapeXml;
    removed += 1;
    return "";
  });
  return { xml, removed };
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
    kind: "textbox,shape,layout",
    search: "Source:",
    maxChars: 150000,
  });
  const sourceFooters = parseNdjson(beforeInspect.ndjson).filter(
    (record) =>
      record.kind === "textbox" &&
      typeof record.text === "string" &&
      record.text.trimStart().startsWith("Source:") &&
      Array.isArray(record.bbox) &&
      record.bbox[1] >= 650,
  );
  if (sourceFooters.length !== EXPECTED_SOURCE_FOOTERS) {
    throw new Error(
      `Expected ${EXPECTED_SOURCE_FOOTERS} bottom Source footers, found ${sourceFooters.length}`,
    );
  }
  await fs.writeFile(
    path.join(BUILD_DIR, "source-footers-before.ndjson"),
    sourceFooters.map((record) => JSON.stringify(record)).join("\n") + "\n",
    "utf8",
  );

  const representativeSlideNumbers = [35, 57, 160];
  const beforePngs = new Map();
  for (const slideNumber of representativeSlideNumbers) {
    const png = await blobBuffer(
      await presentation.export({
        slide: slides[slideNumber - 1],
        format: "png",
        scale: 1,
      }),
    );
    beforePngs.set(slideNumber, png);
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-before.png`), png);
  }

  for (const footer of sourceFooters) {
    const target = presentation.resolve(footer.id);
    if (!target || typeof target.delete !== "function") {
      throw new Error(`Could not resolve deletable shape ${footer.id}`);
    }
    target.delete();
  }

  for (const [slideNumber, sourceText] of SENSITIVITY_SOURCES) {
    const slide = slides[slideNumber - 1];
    const notesText = slide.speakerNotes.textFrame.paragraphs.toPlainText();
    if (!notesText.includes(sourceText)) {
      if (!notesText.includes("\n\nTransition:")) {
        throw new Error(`Slide ${slideNumber} notes lack the structured transition`);
      }
      slide.speakerNotes.textFrame.setText(
        notesText.replace("\n\nTransition:", ` ${sourceText}\n\nTransition:`),
      );
      slide.speakerNotes.setVisible(true);
    }
  }

  const afterInspect = await presentation.inspect({
    kind: "textbox,shape,layout",
    search: "Source:",
    maxChars: 150000,
  });
  const remainingVisibleSources = parseNdjson(afterInspect.ndjson).filter(
    (record) => record.kind === "textbox",
  );
  if (remainingVisibleSources.length !== 0) {
    throw new Error(
      `Artifact Tool edit left ${remainingVisibleSources.length} visible Source text boxes`,
    );
  }
  await fs.writeFile(
    path.join(BUILD_DIR, "source-footers-after.ndjson"),
    afterInspect.ndjson || "",
    "utf8",
  );

  for (const slideNumber of representativeSlideNumbers) {
    const png = await blobBuffer(
      await presentation.export({
        slide: slides[slideNumber - 1],
        format: "png",
        scale: 1,
      }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-after.png`), png);
    if (sha256(beforePngs.get(slideNumber)) === sha256(png)) {
      throw new Error(`Representative slide ${slideNumber} did not change visually`);
    }
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  const currentSourceBuffer = await fs.readFile(SOURCE);
  if (sha256(currentSourceBuffer) !== sourceHash) {
    throw new Error("The source presentation changed during the footer removal");
  }

  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const artifactSlideParts = await orderedSlidePartPaths(artifactZip);
  const sourceZip = await JSZip.loadAsync(currentSourceBuffer);
  const sourceSlideParts = await orderedSlidePartPaths(sourceZip);
  if (
    artifactSlideParts.length !== EXPECTED_SLIDES ||
    sourceSlideParts.length !== EXPECTED_SLIDES
  ) {
    throw new Error("Slide-order metadata changed unexpectedly");
  }

  let removedFromPackage = 0;
  for (const slidePartPath of sourceSlideParts) {
    const slideXml = await sourceZip.file(slidePartPath)?.async("string");
    if (!slideXml) throw new Error(`Missing ${slidePartPath}`);
    const result = removeSourceFooterShapes(slideXml);
    removedFromPackage += result.removed;
    if (result.removed) sourceZip.file(slidePartPath, result.xml);
  }
  if (removedFromPackage !== EXPECTED_SOURCE_FOOTERS) {
    throw new Error(
      `Expected to remove ${EXPECTED_SOURCE_FOOTERS} package shapes, removed ${removedFromPackage}`,
    );
  }

  for (const slideNumber of SENSITIVITY_SOURCES.keys()) {
    const artifactSlidePart = artifactSlideParts[slideNumber - 1];
    const sourceSlidePart = sourceSlideParts[slideNumber - 1];
    const artifactNotesPart = await relatedPartPath(
      artifactZip,
      artifactSlidePart,
      "notesSlide",
    );
    const sourceNotesPart = await relatedPartPath(sourceZip, sourceSlidePart, "notesSlide");
    const updatedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    const expectedSource = SENSITIVITY_SOURCES.get(slideNumber);
    if (!updatedNotesXml?.includes(expectedSource)) {
      throw new Error(`Artifact candidate lacks the slide ${slideNumber} source note`);
    }
    sourceZip.file(sourceNotesPart, updatedNotesXml);
  }

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
      "09162026_sex_apoe_kda_fine_broad_no_source_footers.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  if (reopenedSlides.length !== EXPECTED_SLIDES) {
    throw new Error(`Final deck has ${reopenedSlides.length} slides`);
  }
  const finalVisibleSourceCheck = await reopened.inspect({
    kind: "textbox,shape,layout",
    search: "Source:",
    maxChars: 150000,
  });
  if (
    parseNdjson(finalVisibleSourceCheck.ndjson).some(
      (record) => record.kind === "textbox",
    )
  ) {
    throw new Error("Visible Source text remains in the finalized presentation");
  }
  const finalNotesCheck = await reopened.inspect({
    kind: "notes",
    search: "Phase 22 and VH14|validated Phase 22",
    maxChars: 30000,
  });
  const sensitivityNoteSlides = new Set(
    parseNdjson(finalNotesCheck.ndjson).map((record) => record.slide),
  );
  for (const slideNumber of SENSITIVITY_SOURCES.keys()) {
    if (!sensitivityNoteSlides.has(slideNumber)) {
      throw new Error(`Could not verify the source note on slide ${slideNumber}`);
    }
  }
  await fs.writeFile(
    path.join(BUILD_DIR, "final-notes-check.ndjson"),
    finalNotesCheck.ndjson || "",
    "utf8",
  );

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        removedVisibleSourceFooters: EXPECTED_SOURCE_FOOTERS,
        sensitivitySourcesRetainedInNotes: [...SENSITIVITY_SOURCES.keys()],
        slideCount: EXPECTED_SLIDES,
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
