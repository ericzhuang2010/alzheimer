#!/usr/bin/env node

/** Add genetic support to the slide 3 workflow while preserving the deck's visual language. */

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
const RUN_DIR = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slide3_genetic_support_20260922_v1",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_slide3_genetic_support_20260922_v1.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "3630de00ea942f19939c228d22f9bdb196bcc7804af3eabb3fadd1d5213446e2";
const SLIDE_COUNT = 154;
const SLIDE_NUMBER = 3;

const COLORS = {
  background: "#11263F",
  white: "#FFFFFF",
  body: "#CED8E5",
  line: "#72869C",
  blue: "#0087C8",
  lightBlue: "#55B5E3",
  green: "#00A87E",
  purple: "#7D4FA1",
  yellow: "#F5B000",
  orange: "#F97300",
};

const STEPS = [
  {
    number: "1",
    title: "DEG analysis",
    description: "Identify genes with higher or lower RNA abundance in AD.",
    fill: COLORS.blue,
  },
  {
    number: "2",
    title: "Pathway analysis",
    description: "Summarize mitochondrial processes represented among the DEGs.",
    fill: COLORS.lightBlue,
  },
  {
    number: "3",
    title: "Key driver analysis\n(KDA)",
    description: "Use gene networks to nominate genes connected to MitoCarta MT DEGs.",
    fill: COLORS.green,
  },
  {
    number: "4",
    title: "Genetic support",
    description:
      "Evaluate candidate genes using Alzheimer’s genetic-association and gene-regulation evidence.",
    fill: COLORS.purple,
  },
  {
    number: "5",
    title: "Human validation",
    description: "Compare ROSMAP findings with SEA-AD and direct broad-cell analyses.",
    fill: COLORS.yellow,
  },
  {
    number: "6",
    title: "Mouse validation",
    description: "Test selected candidates and mitochondrial function in targeted models.",
    fill: COLORS.background,
    outline: COLORS.orange,
  },
];

const SPEAKER_NOTES = [
  "Teaching goal: Show how the study moves from cell-level gene expression to candidate prioritization and validation.",
  "",
  "Walk through: First, DEG analysis identifies genes with higher or lower RNA abundance in Alzheimer’s disease within each fine-cell, sex, and APOE comparison. Second, pathway analysis summarizes the mitochondrial processes represented among those DEGs. Third, key driver analysis, abbreviated KDA, uses gene networks to nominate genes connected to the MitoCarta MT DEGs.",
  "",
  "Fourth, genetic support evaluates candidate genes using Alzheimer’s genetic-association and gene-regulation evidence. This provides gene-level support. It does not by itself validate the cell type, sex or APOE group, or network connections from the KDA calls.",
  "",
  "Fifth, human validation compares the ROSMAP findings with SEA-AD and with direct broad-cell analyses. The final stage shown here is mouse validation, which would test selected candidates and mitochondrial function in targeted models.",
  "",
  "Scientific boundary: DEG analysis, pathway analysis, KDA, genetic support, and human validation contribute evidence presented in this deck. Mouse validation remains a potential next step and does not contribute evidence to the current findings.",
  "",
  "Transition: Next, introduce the two human brain cohorts.",
].join("\n");

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

function relationshipAttributes(tag) {
  return Object.fromEntries(
    [...tag.matchAll(/([A-Za-z:]+)="([^"]*)"/g)].map((match) => [match[1], match[2]]),
  );
}

function relationships(xml) {
  return [...xml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map((match) => ({
    attrs: relationshipAttributes(match[0]),
  }));
}

function normalizePart(basePart, target) {
  if (target.startsWith("/")) return target.slice(1);
  return path.posix.normalize(path.posix.join(path.posix.dirname(basePart), target));
}

async function visibleSlidePart(zip, ordinal) {
  const presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  const presentationRels = await zip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  if (!presentationXml || !presentationRels) {
    throw new Error("Presentation ordering metadata is missing");
  }
  const slideIds = [
    ...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g),
  ].map((match) => match[1]);
  const relationshipId = slideIds[ordinal - 1];
  const relation = relationships(presentationRels).find(
    (item) => item.attrs.Id === relationshipId && item.attrs.Type?.endsWith("/slide"),
  );
  if (!relation?.attrs.Target) throw new Error(`Visible slide ${ordinal} was not found`);
  return normalizePart("ppt/presentation.xml", relation.attrs.Target);
}

async function notesPartForSlide(zip, slidePart) {
  const relsPath = path.posix.join(
    path.posix.dirname(slidePart),
    "_rels",
    `${path.posix.basename(slidePart)}.rels`,
  );
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing slide relationships: ${relsPath}`);
  const relation = relationships(relsXml).find((item) =>
    item.attrs.Type?.endsWith("/notesSlide"),
  );
  if (!relation?.attrs.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return normalizePart(slidePart, relation.attrs.Target);
}

function addText(slide, name, text, position, style) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: "Arial",
    color: COLORS.white,
    alignment: "left",
    verticalAlignment: "middle",
    autoFit: "shrinkText",
    wrap: "square",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
    ...style,
  };
  return shape;
}

function rebuildWorkflowSlide(slide) {
  for (const shape of [...slide.shapes.items]) {
    slide.shapes.deleteById(shape.id);
  }
  slide.background.fill = COLORS.background;

  addText(
    slide,
    "Part Label",
    "PART 1",
    { left: 75, top: 68, width: 100, height: 20 },
    { fontSize: 11, color: COLORS.blue, bold: false, verticalAlignment: "top" },
  );
  addText(
    slide,
    "Slide Title",
    "Overall workflow",
    { left: 75, top: 132, width: 600, height: 58 },
    { fontSize: 43, bold: true, verticalAlignment: "top" },
  );
  addText(
    slide,
    "Slide Subtitle",
    "From cell-level gene expression to candidate prioritization and validation",
    { left: 75, top: 218, width: 1020, height: 34 },
    { fontSize: 20, color: COLORS.body, verticalAlignment: "top" },
  );

  slide.shapes.add({
    geometry: "rect",
    name: "Workflow Line",
    position: { left: 115, top: 339, width: 1050, height: 3 },
    fill: COLORS.line,
    line: { fill: "none", width: 0 },
  });

  const columnLefts = [15, 225, 435, 645, 855, 1065];
  const centers = columnLefts.map((left) => left + 100);
  for (let index = 0; index < STEPS.length; index += 1) {
    const step = STEPS[index];
    const circle = slide.shapes.add({
      geometry: "ellipse",
      name: `Workflow Step ${step.number}`,
      position: { left: centers[index] - 24, top: 316, width: 48, height: 48 },
      fill: step.fill,
      line: step.outline
        ? { style: "solid", fill: step.outline, width: 2.5 }
        : { fill: "none", width: 0 },
    });
    circle.text = step.number;
    circle.text.style = {
      typeface: "Arial",
      fontSize: 18,
      bold: true,
      color: COLORS.white,
      alignment: "center",
      verticalAlignment: "middle",
      autoFit: "shrinkText",
      insets: { left: 0, right: 0, top: 0, bottom: 0 },
    };

    addText(
      slide,
      `Workflow Step ${step.number} Title`,
      step.title,
      { left: columnLefts[index], top: 401, width: 200, height: 54 },
      { fontSize: 19, bold: true, alignment: "center", verticalAlignment: "top" },
    );
    addText(
      slide,
      `Workflow Step ${step.number} Description`,
      step.description,
      { left: columnLefts[index] + 4, top: 454, width: 192, height: 84 },
      {
        fontSize: 14,
        color: COLORS.body,
        alignment: "center",
        verticalAlignment: "top",
      },
    );
  }

  addText(
    slide,
    "Potential Next Step Label",
    "POTENTIAL NEXT STEP",
    { left: 1060, top: 281, width: 210, height: 20 },
    { fontSize: 12, bold: true, color: COLORS.orange, alignment: "center" },
  );

  slide.speakerNotes.textFrame.setText(SPEAKER_NOTES);
  slide.speakerNotes.setVisible(true);
}

async function main() {
  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
  if (await fs.stat(FINAL_PPTX).catch(() => undefined)) {
    throw new Error(`Output already exists: ${FINAL_PPTX}`);
  }

  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceHash = sha256(sourceBuffer);
  if (sourceHash !== EXPECTED_SOURCE_SHA256) {
    throw new Error(`Source deck changed before slide 3 edit: ${sourceHash}`);
  }
  await fs.writeFile(path.join(BUILD_DIR, "source-original.pptx"), sourceBuffer);

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
  rebuildWorkflowSlide(slides[SLIDE_NUMBER - 1]);

  const preview = Buffer.from(
    await (
      await presentation.export({
        slide: slides[SLIDE_NUMBER - 1],
        format: "png",
        scale: 1.5,
      })
    ).arrayBuffer(),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-3-edited.png"), preview);

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("Source changed during slide 3 editing");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const sourceSlidePart = await visibleSlidePart(sourceZip, SLIDE_NUMBER);
  const artifactSlidePart = await visibleSlidePart(artifactZip, SLIDE_NUMBER);
  const slideXml = await artifactZip.file(artifactSlidePart)?.async("string");
  if (!slideXml) throw new Error("Updated slide 3 XML is missing");
  sourceZip.file(sourceSlidePart, slideXml);

  const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
  const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
  const notesXml = await artifactZip.file(artifactNotesPart)?.async("string");
  if (!notesXml) throw new Error("Updated slide 3 notes are missing");
  sourceZip.file(sourceNotesPart, notesXml);

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
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
    receiptPath: path.join(BUILD_DIR, "validation.json"),
  });

  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const actualChanged = [];
  const actualDeleted = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) {
      actualDeleted.push(name);
      continue;
    }
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) actualChanged.push(name);
  }
  actualChanged.sort();
  actualDeleted.sort();
  const expectedChanged = [sourceNotesPart, sourceSlidePart].sort();
  if (
    actualChanged.length !== expectedChanged.length ||
    actualChanged.some((name, index) => name !== expectedChanged[index])
  ) {
    throw new Error(`Unexpected changed package parts: ${actualChanged.join(", ")}`);
  }
  if (actualDeleted.length) {
    throw new Error(`Unexpected deleted package parts: ${actualDeleted.join(", ")}`);
  }

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const inspection = (
    await reopened.inspect({ kind: "textbox,notes", search: "Genetic support", maxChars: 10000 })
  ).ndjson;
  if (!inspection.includes("Genetic support")) {
    throw new Error("Genetic support was not found in the finalized deck");
  }

  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("Source changed before installation");
  }
  await fs.copyFile(FINAL_PPTX, SOURCE);

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        originalSha256: sourceHash,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
        finalSlideCount: SLIDE_COUNT,
        updatedSlide: SLIDE_NUMBER,
        updatedNotesSlide: SLIDE_NUMBER,
        changedParts: actualChanged,
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
