#!/usr/bin/env node

/** Add an explicit sex/APOE scope label to each finding divider slide. */

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
  "results/presentations/09162026_finding_scope_labels_20260921_v2/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_finding_scope_labels_20260921_v2/output/09162026_sex_apoe_kda_fine_broad_finding_scope_labels_20260921_v2.pptx",
);
const EXPECTED_SLIDES = 155;
const EXPECTED_SOURCE_SHA256 =
  "5bea0be278ddafa97a22ab5a21b012a4abcd001be98d22e7af0cc58e76e52570";

const FINDING_SCOPE = new Map([
  [53, "Observed in: female ε3/ε3"],
  [59, "Observed in: male ε3/ε3"],
  [66, "Observed in: female ε2"],
  [72, "Observed in: female ε4"],
  [78, "Observed in: male ε2"],
  [84, "Observed in: male ε4"],
  [90, "Not sex/APOE-specific; observed across all six groups"],
  [96, "Observed in: female ε2, female ε3/ε3, female ε4, and male ε2"],
  [102, "Observed in: female ε2, female ε3/ε3, male ε3/ε3, and male ε4"],
  [108, "Not sex/APOE-specific; observed across all six groups"],
  [114, "Observed in: female ε2, female ε4, male ε2, and male ε3/ε3"],
  [120, "Observed in: female ε3/ε3, female ε4, and male ε4"],
  [126, "Observed in: female ε3/ε3 and male ε2"],
  [132, "Observed in: female ε2, female ε3/ε3, and female ε4"],
  [138, "Observed in: female ε2, male ε2, and male ε4"],
  [144, "Observed in: female ε4"],
  [150, "Not sex/APOE-specific; cross-cohort validation finding"],
]);

const EXPECTED_TITLES = new Map(
  [...FINDING_SCOPE.keys()].map((slideNumber, index) => [
    slideNumber,
    `FINDING ${index + 1}`,
  ]),
);

function labelStyle(label) {
  return {
    typeface: "Arial",
    fontSize: label.length > 58 ? 16 : 18,
    bold: true,
    color: "#E6A700",
    alignment: "left",
    verticalAlignment: "top",
    autoFit: "shrinkText",
    wrap: "square",
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
  };
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

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

async function blobBuffer(blob) {
  return Buffer.from(await blob.arrayBuffer());
}

function relationshipAttributes(tag) {
  return Object.fromEntries(
    [...tag.matchAll(/([A-Za-z:]+)="([^"]*)"/g)].map((match) => [match[1], match[2]]),
  );
}

async function visibleSlideParts(zip) {
  const presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  const presentationRels = await zip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  if (!presentationXml || !presentationRels) {
    throw new Error("Presentation ordering metadata is missing");
  }
  const slideIds = [...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g)].map(
    (match) => match[1],
  );
  const relationships = [...presentationRels.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map(
    (match) => relationshipAttributes(match[0]),
  );
  return slideIds.map((relationshipId) => {
    const relation = relationships.find(
      (item) => item.Id === relationshipId && item.Type?.endsWith("/slide"),
    );
    if (!relation?.Target) {
      throw new Error(`Slide relationship ${relationshipId} was not found`);
    }
    return relation.Target.startsWith("/")
      ? relation.Target.slice(1)
      : path.posix.normalize(path.posix.join("ppt", relation.Target));
  });
}

async function notesPartForSlide(zip, slidePart) {
  const relsPath = path.posix.join(
    path.posix.dirname(slidePart),
    "_rels",
    `${path.posix.basename(slidePart)}.rels`,
  );
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing slide relationships: ${relsPath}`);
  const relationships = [...relsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map(
    (match) => relationshipAttributes(match[0]),
  );
  const relation = relationships.find((item) => item.Type?.endsWith("/notesSlide"));
  if (!relation?.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return relation.Target.startsWith("/")
    ? relation.Target.slice(1)
    : path.posix.normalize(path.posix.join(path.posix.dirname(slidePart), relation.Target));
}

function withScopeLine(notes, label) {
  const clean = (notes ?? "").trim();
  if (/^Scope:.*$/m.test(clean)) {
    return clean.replace(/^Scope:.*$/m, `Scope: ${label}`);
  }
  if (clean.includes("\n\nTransition:")) {
    return clean.replace("\n\nTransition:", `\n\nScope: ${label}\n\nTransition:`);
  }
  return `${clean}\n\nScope: ${label}`.trim();
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
    throw new Error(`Source deck changed before the finding-scope edit: ${sourceHash}`);
  }

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

  const slideSnapshot = await presentation.inspect({ kind: "slides", maxChars: 500000 });
  const slideRecords = new Map(
    parseNdjson(slideSnapshot.ndjson)
      .filter((record) => record.kind === "slide" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record]),
  );
  for (const [slideNumber, expectedTitle] of EXPECTED_TITLES) {
    if (slideRecords.get(slideNumber)?.title !== expectedTitle) {
      throw new Error(
        `Unexpected title on slide ${slideNumber}: ${slideRecords.get(slideNumber)?.title}`,
      );
    }
  }

  const textSnapshot = await presentation.inspect({
    kind: "textbox",
    include: "id,slide,name,text,textPreview,bbox",
    maxChars: 3000000,
  });
  const textRecords = parseNdjson(textSnapshot.ndjson).filter(
    (record) => record.kind === "textbox" && FINDING_SCOPE.has(record.slide),
  );
  const notesSnapshot = await presentation.inspect({ kind: "notes", maxChars: 3000000 });
  const notesBySlide = new Map(
    parseNdjson(notesSnapshot.ndjson)
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text ?? ""]),
  );

  const beforePngs = new Map();
  const updatedNotes = new Map();
  for (const [slideNumber, label] of FINDING_SCOPE) {
    const png = await blobBuffer(
      await presentation.export({ slide: slides[slideNumber - 1], format: "png", scale: 1.5 }),
    );
    beforePngs.set(slideNumber, png);
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-before.png`), png);

    const existing = textRecords.find(
      (record) => record.slide === slideNumber && record.name === "TextBox 4",
    );
    let shape;
    if (existing?.id) {
      shape = presentation.resolve(existing.id);
    } else {
      shape = slides[slideNumber - 1].shapes.add({
        geometry: "textbox",
        name: "TextBox 4",
        position: { left: 115.2, top: 259.2, width: 777.6, height: 96 },
        fill: "none",
        line: { style: "solid", fill: "none", width: 0 },
      });
    }
    shape.text = label;
    shape.text.style = labelStyle(label);

    const revisedNotes = withScopeLine(notesBySlide.get(slideNumber), label);
    updatedNotes.set(slideNumber, revisedNotes);
    slides[slideNumber - 1].speakerNotes.textFrame.setText(revisedNotes);
    slides[slideNumber - 1].speakerNotes.setVisible(true);
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed during the finding-scope edit");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const [sourceSlideParts, artifactSlideParts] = await Promise.all([
    visibleSlideParts(sourceZip),
    visibleSlideParts(artifactZip),
  ]);
  const expectedChangedParts = [];
  for (const [slideNumber, label] of FINDING_SCOPE) {
    const sourceSlidePart = sourceSlideParts[slideNumber - 1];
    const artifactSlidePart = artifactSlideParts[slideNumber - 1];
    const updatedSlideXml = await artifactZip.file(artifactSlidePart)?.async("string");
    if (!updatedSlideXml?.includes(label)) {
      throw new Error(`Updated visible slide ${slideNumber} lacks its scope label`);
    }
    sourceZip.file(sourceSlidePart, updatedSlideXml);
    expectedChangedParts.push(sourceSlidePart);

    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const updatedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!updatedNotesXml?.includes("Scope:")) {
      throw new Error(`Updated notes are missing the scope line on slide ${slideNumber}`);
    }
    sourceZip.file(sourceNotesPart, updatedNotesXml);
    expectedChangedParts.push(sourceNotesPart);
  }

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
    await sourceZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const validation = await finalizePresentation({
    explicitTotalSlideCount: EXPECTED_SLIDES,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [19],
    requiredEmbeddedWorkbookChartOwnerSlides: [19],
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
    receiptPath: path.join(BUILD_DIR, "finding_scope_labels.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const finalTextSnapshot = await reopened.inspect({
    kind: "textbox",
    include: "id,slide,name,text,textPreview,bbox",
    maxChars: 3000000,
  });
  const finalTextRecords = parseNdjson(finalTextSnapshot.ndjson).filter(
    (record) => record.kind === "textbox" && FINDING_SCOPE.has(record.slide),
  );
  for (const [slideNumber, label] of FINDING_SCOPE) {
    const matches = finalTextRecords.filter(
      (record) =>
        record.slide === slideNumber && record.name === "TextBox 4" && record.text === label,
    );
    if (matches.length !== 1) {
      throw new Error(`Expected one scope label on slide ${slideNumber}, found ${matches.length}`);
    }
  }

  const finalNotesSnapshot = await reopened.inspect({ kind: "notes", maxChars: 3000000 });
  const finalNotes = new Map(
    parseNdjson(finalNotesSnapshot.ndjson)
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text]),
  );
  for (const [slideNumber, expectedNotes] of updatedNotes) {
    if (finalNotes.get(slideNumber)?.trim() !== expectedNotes.trim()) {
      throw new Error(`Final speaker notes do not match on slide ${slideNumber}`);
    }
    const finalPng = await blobBuffer(
      await reopened.export({
        slide: reopenedSlides[slideNumber - 1],
        format: "png",
        scale: 1.5,
      }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-final.png`), finalPng);
    if (sha256(finalPng) === sha256(beforePngs.get(slideNumber))) {
      throw new Error(`Visible slide ${slideNumber} did not change`);
    }
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const sourceFiles = Object.keys(originalZip.files)
    .filter((name) => !originalZip.files[name].dir)
    .sort();
  const finalFiles = Object.keys(finalZip.files)
    .filter((name) => !finalZip.files[name].dir)
    .sort();
  if (
    sourceFiles.length !== finalFiles.length ||
    sourceFiles.some((name, index) => name !== finalFiles[index])
  ) {
    throw new Error("The final package file list differs from the source package");
  }
  const changedParts = [];
  for (const name of sourceFiles) {
    const [sourceData, finalData] = await Promise.all([
      originalZip.file(name).async("nodebuffer"),
      finalZip.file(name).async("nodebuffer"),
    ]);
    if (sha256(sourceData) !== sha256(finalData)) changedParts.push(name);
  }
  const expectedParts = [...new Set(expectedChangedParts)].sort();
  if (
    changedParts.length !== expectedParts.length ||
    changedParts.some((part, index) => part !== expectedParts[index])
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
        slideCount: EXPECTED_SLIDES,
        updatedSlides: [...FINDING_SCOPE.keys()],
        scopeLabels: Object.fromEntries(FINDING_SCOPE),
        changedParts,
        warnings: validation.warnings ?? [],
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
