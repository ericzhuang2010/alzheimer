#!/usr/bin/env node

/** Remove the repeated limitation slides for Findings 6 through 17. */

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
const RESULT_DIR = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_remove_findings6_17_limitation_slides_20260920",
);
const BUILD_DIR = path.join(RESULT_DIR, "build");
const FINAL_PPTX = path.join(
  RESULT_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_without_findings6_17_limitation_slides_20260920.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "08a0c8039e8e47019dd945acd5565b68c2f060252d6c76718e5eb99834c498d8";
const SOURCE_SLIDE_COUNT = 157;
const REMOVED_SOURCE_SLIDES = [79, 86, 93, 100, 107, 114, 121, 128, 135, 142, 149, 156];
const PRECEDING_SOURCE_SLIDES = REMOVED_SOURCE_SLIDES.map((slideNumber) => slideNumber - 1);
const FINAL_SLIDE_COUNT = SOURCE_SLIDE_COUNT - REMOVED_SOURCE_SLIDES.length;
const OLD_TRANSITION = "Transition: Separate the observation from what remains unproven.";
const NEW_TRANSITION =
  "Transition: Place the result in prior research and summarize its evidence level.";

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
  return [...xml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map((match) => match[0]);
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

async function relatedPartPath(zip, ownerPartPath, relationshipTypeSuffix) {
  const relsPath = relationshipPartPath(ownerPartPath);
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing ${relsPath}`);
  for (const tag of relationshipTags(relsXml)) {
    const type = relationshipAttribute(tag, "Type");
    if (!type?.endsWith(`/relationships/${relationshipTypeSuffix}`)) continue;
    const target = relationshipAttribute(tag, "Target");
    if (!target) continue;
    if (target.startsWith("/")) return target.slice(1);
    return path.posix.normalize(path.posix.join(path.posix.dirname(ownerPartPath), target));
  }
  throw new Error(`${ownerPartPath} lacks a ${relationshipTypeSuffix} relationship`);
}

async function visibleSlidePart(zip, ordinal) {
  const presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  const presentationRelsXml = await zip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  if (!presentationXml || !presentationRelsXml) {
    throw new Error("Presentation ordering metadata is missing");
  }
  const slideIds = [...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g)]
    .map((match) => match[1]);
  const relationshipId = slideIds[ordinal - 1];
  if (!relationshipId) throw new Error(`Visible slide ${ordinal} was not found`);
  const relation = relationshipTags(presentationRelsXml).find(
    (tag) =>
      relationshipAttribute(tag, "Id") === relationshipId &&
      relationshipAttribute(tag, "Type")?.endsWith("/slide"),
  );
  const target = relation && relationshipAttribute(relation, "Target");
  if (!target) throw new Error(`Slide relationship ${relationshipId} was not found`);
  return target.startsWith("/")
    ? target.slice(1)
    : path.posix.normalize(path.posix.join("ppt", target));
}

function removeContentTypeOverride(contentTypesXml, partPath) {
  const partName = `/${partPath}`;
  const target = [...contentTypesXml.matchAll(/<Override\b[^>]*\/?\s*>/g)]
    .map((match) => match[0])
    .find((tag) => relationshipAttribute(tag, "PartName") === partName);
  if (!target) throw new Error(`Missing content-type override for ${partName}`);
  return contentTypesXml.replace(target, "");
}

function updateAppProperties(appXml) {
  let updated = appXml
    .replace(/<Slides>157<\/Slides>/, `<Slides>${FINAL_SLIDE_COUNT}</Slides>`)
    .replace(/<Notes>157<\/Notes>/, `<Notes>${FINAL_SLIDE_COUNT}</Notes>`)
    .replace(
      /(<vt:lpstr>Slide Titles<\/vt:lpstr>\s*<\/vt:variant>\s*<vt:variant>\s*<vt:i4>)157(<\/vt:i4>)/,
      `$1${FINAL_SLIDE_COUNT}$2`,
    );

  const titlesMatch = updated.match(
    /(<TitlesOfParts>\s*<vt:vector size=")160(" baseType="lpstr">)([\s\S]*?)(<\/vt:vector>\s*<\/TitlesOfParts>)/,
  );
  if (!titlesMatch) throw new Error("Could not locate TitlesOfParts metadata");
  let entriesXml = titlesMatch[3];
  const entries = [...entriesXml.matchAll(/<vt:lpstr>[\s\S]*?<\/vt:lpstr>/g)];
  if (entries.length !== 160) {
    throw new Error(`Expected 160 TitlesOfParts entries, found ${entries.length}`);
  }
  const entryIndexes = REMOVED_SOURCE_SLIDES.map((slideNumber) => slideNumber + 2)
    .sort((a, b) => b - a);
  for (const entryIndex of entryIndexes) {
    const entry = entries[entryIndex];
    entriesXml =
      entriesXml.slice(0, entry.index) + entriesXml.slice(entry.index + entry[0].length);
  }
  updated = updated.replace(
    titlesMatch[0],
    `${titlesMatch[1]}${FINAL_SLIDE_COUNT + 3}${titlesMatch[2]}${entriesXml}${titlesMatch[4]}`,
  );
  return updated;
}

function finalSlideNumber(sourceSlideNumber) {
  return sourceSlideNumber - REMOVED_SOURCE_SLIDES.filter((n) => n < sourceSlideNumber).length;
}

function expectedLimitationTitle(sourceSlideNumber) {
  const findingNumber = 6 + REMOVED_SOURCE_SLIDES.indexOf(sourceSlideNumber);
  return `What Finding ${findingNumber} does not prove, and the next evidence needed`;
}

async function main() {
  const sourceStat = await fs.stat(SOURCE).catch(() => undefined);
  if (!sourceStat?.isFile()) throw new Error(`Missing source deck: ${SOURCE}`);
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
  if (slides.length !== SOURCE_SLIDE_COUNT) {
    throw new Error(`Expected ${SOURCE_SLIDE_COUNT} slides, found ${slides.length}`);
  }

  const sourceSnapshot = await presentation.inspect({
    kind: "slide,notes",
    maxChars: 4000000,
  });
  const sourceRecords = parseNdjson(sourceSnapshot.ndjson);
  for (const slideNumber of REMOVED_SOURCE_SLIDES) {
    const title = sourceRecords.find(
      (record) => record.kind === "slide" && record.slide === slideNumber,
    )?.title;
    const expected = expectedLimitationTitle(slideNumber);
    if (title !== expected) {
      throw new Error(`Expected slide ${slideNumber} to be '${expected}', found '${title}'`);
    }
  }

  const updatedNotesBySourceSlide = new Map();
  for (const slideNumber of PRECEDING_SOURCE_SLIDES) {
    const sourceNotes = sourceRecords.find(
      (record) => record.kind === "notes" && record.slide === slideNumber,
    )?.text;
    if (!sourceNotes?.includes(OLD_TRANSITION)) {
      throw new Error(`Slide ${slideNumber} lacks the expected transition`);
    }
    const updatedNotes = sourceNotes.replace(OLD_TRANSITION, NEW_TRANSITION);
    updatedNotesBySourceSlide.set(slideNumber, updatedNotes);
    slides[slideNumber - 1].speakerNotes.textFrame.setText(updatedNotes);
    slides[slideNumber - 1].speakerNotes.setVisible(true);
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed during the edit");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  for (const slideNumber of PRECEDING_SOURCE_SLIDES) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const sourceNotesPart = await relatedPartPath(sourceZip, sourceSlidePart, "notesSlide");
    const artifactNotesPart = await relatedPartPath(artifactZip, artifactSlidePart, "notesSlide");
    const revisedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!revisedNotesXml?.includes("Place the result in prior research")) {
      throw new Error(`Artifact candidate lacks the revised notes for slide ${slideNumber}`);
    }
    sourceZip.file(sourceNotesPart, revisedNotesXml);
  }

  const presentationPath = "ppt/presentation.xml";
  const presentationRelsPath = "ppt/_rels/presentation.xml.rels";
  let presentationXml = await sourceZip.file(presentationPath)?.async("string");
  let presentationRelsXml = await sourceZip.file(presentationRelsPath)?.async("string");
  let contentTypesXml = await sourceZip.file("[Content_Types].xml")?.async("string");
  const appXml = await sourceZip.file("docProps/app.xml")?.async("string");
  if (!presentationXml || !presentationRelsXml || !contentTypesXml || !appXml) {
    throw new Error("The source PPTX is missing required package parts");
  }

  const slideIdTags = [...presentationXml.matchAll(/<p:sldId\b[^>]*\/?\s*>/g)]
    .map((match) => match[0]);
  if (slideIdTags.length !== SOURCE_SLIDE_COUNT) {
    throw new Error(`Expected ${SOURCE_SLIDE_COUNT} slide IDs, found ${slideIdTags.length}`);
  }
  const presentationRelationships = relationshipTags(presentationRelsXml);
  for (const slideNumber of [...REMOVED_SOURCE_SLIDES].sort((a, b) => b - a)) {
    const slideIdTag = slideIdTags[slideNumber - 1];
    const relationshipId = relationshipAttribute(slideIdTag, "r:id");
    const relationshipTag = presentationRelationships.find(
      (tag) => relationshipAttribute(tag, "Id") === relationshipId,
    );
    const target = relationshipTag && relationshipAttribute(relationshipTag, "Target");
    if (!relationshipTag || !target) {
      throw new Error(`Could not resolve slide ${slideNumber} relationship`);
    }
    const slidePartPath = target.startsWith("/")
      ? target.slice(1)
      : path.posix.normalize(path.posix.join("ppt", target));
    const slideRelsPath = relationshipPartPath(slidePartPath);
    const notesPartPath = await relatedPartPath(sourceZip, slidePartPath, "notesSlide");
    const notesRelsPath = relationshipPartPath(notesPartPath);

    sourceZip.remove(slidePartPath);
    sourceZip.remove(slideRelsPath);
    sourceZip.remove(notesPartPath);
    sourceZip.remove(notesRelsPath);
    contentTypesXml = removeContentTypeOverride(contentTypesXml, slidePartPath);
    contentTypesXml = removeContentTypeOverride(contentTypesXml, notesPartPath);
    presentationXml = presentationXml.replace(slideIdTag, "");
    presentationRelsXml = presentationRelsXml.replace(relationshipTag, "");
  }

  sourceZip.file(presentationPath, presentationXml);
  sourceZip.file(presentationRelsPath, presentationRelsXml);
  sourceZip.file("[Content_Types].xml", contentTypesXml);
  sourceZip.file("docProps/app.xml", updateAppProperties(appXml));

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
    await sourceZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const validation = await finalizePresentation({
    explicitTotalSlideCount: FINAL_SLIDE_COUNT,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [14],
    requiredEmbeddedWorkbookChartOwnerSlides: [14],
    nativeChartTargetApplication: "powerpoint",
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
    receiptPath: path.join(BUILD_DIR, "remove_findings6_17_limitation_slides.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalSlides = slidesFromPresentation(reopened);
  if (finalSlides.length !== FINAL_SLIDE_COUNT) {
    throw new Error(`Final deck has ${finalSlides.length} slides, expected ${FINAL_SLIDE_COUNT}`);
  }
  const finalSnapshot = await reopened.inspect({
    kind: "slide,textbox,notes,chart,layout",
    maxChars: 6000000,
  });
  await fs.writeFile(path.join(BUILD_DIR, "final.inspect.ndjson"), finalSnapshot.ndjson, "utf8");
  const finalRecords = parseNdjson(finalSnapshot.ndjson);

  const remainingLimitationSlides = finalRecords.filter(
    (record) =>
      record.kind === "slide" &&
      /^What Finding (?:[6-9]|1[0-7]) does not prove, and the next evidence needed$/.test(
        record.title || "",
      ),
  );
  if (remainingLimitationSlides.length) {
    throw new Error("One or more requested limitation slides remain in the final deck");
  }

  const expectedFindingStarts = new Map(
    Array.from({ length: 12 }, (_, index) => [74 + index * 6, `FINDING ${index + 6}`]),
  );
  for (const [slideNumber, title] of expectedFindingStarts) {
    const actual = finalRecords.find(
      (record) => record.kind === "slide" && record.slide === slideNumber,
    )?.title;
    if (actual !== title) {
      throw new Error(`Expected '${title}' on slide ${slideNumber}, found '${actual}'`);
    }
  }

  for (const [sourceSlideNumber, expectedNotes] of updatedNotesBySourceSlide) {
    const finalSlide = finalSlideNumber(sourceSlideNumber);
    const record = finalRecords.find(
      (item) => item.kind === "notes" && item.slide === finalSlide,
    );
    if (record?.text?.trim() !== expectedNotes.trim()) {
      throw new Error(`Final notes validation failed for slide ${finalSlide}`);
    }
  }

  const renderSlideNumbers = [];
  for (let findingIndex = 0; findingIndex < 12; findingIndex += 1) {
    const findingStart = 74 + findingIndex * 6;
    renderSlideNumbers.push(findingStart, findingStart + 4, findingStart + 5);
  }
  for (const slideNumber of renderSlideNumbers) {
    const png = await blobBuffer(
      await reopened.export({
        slide: finalSlides[slideNumber - 1],
        format: "png",
        scale: 1,
      }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-final.png`), png);
  }

  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed before installation");
  }
  await fs.copyFile(FINAL_PPTX, SOURCE);

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        previousSourceSha256: sourceHash,
        installedSourceSha256: sha256(await fs.readFile(SOURCE)),
        output: FINAL_PPTX,
        removedSourceSlides: REMOVED_SOURCE_SLIDES,
        finalSlideCount: FINAL_SLIDE_COUNT,
        updatedNotesSourceSlides: PRECEDING_SOURCE_SLIDES,
        validation,
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
