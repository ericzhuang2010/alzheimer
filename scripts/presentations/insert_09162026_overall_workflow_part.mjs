#!/usr/bin/env node

/** Insert an overall-workflow Part 1 and renumber the existing Part labels. */

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
  "results/presentations/09162026_insert_workflow_part_20260920_v3",
);
const BUILD_DIR = path.join(RESULT_DIR, "build");
const FINAL_PPTX = path.join(
  RESULT_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_with_overall_workflow_20260920.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "46bf2885c3bdb7600459d0671f0d66a4dd67effe40a97574c7af7b7f85232153";
const SOURCE_SLIDE_COUNT = 145;
const FINAL_SLIDE_COUNT = 146;
const FONT_FAMILY = "Arial";

const COLORS = {
  navy: "#0F233D",
  white: "#FFFFFF",
  muted: "#CBD8E5",
  line: "#58718B",
  panel: "#193A5A",
  blue: "#0072B2",
  cyan: "#56B4E9",
  green: "#009E73",
  gold: "#E6A700",
  orange: "#D55E00",
};

const PART_TEXT_UPDATES = [
  { sourceSlide: 2, oldText: "PART 1", newText: "PART 2" },
  { sourceSlide: 5, oldText: "PART 2", newText: "PART 3" },
  { sourceSlide: 15, oldText: "PART 3", newText: "PART 4" },
  { sourceSlide: 29, oldText: "PART 4", newText: "PART 5" },
  { sourceSlide: 36, oldText: "PART 4", newText: "PART 5" },
  { sourceSlide: 42, oldText: "PART 5", newText: "PART 6" },
];

const TITLE_SLIDE_NOTES = [
  "Teaching goal: Introduce the research question and presentation scope.",
  "",
  "Walk through: This study asks how sex, APOE genotype, and brain cell type shape mitochondrial gene-expression changes in Alzheimer’s disease. ROSMAP provides the primary analysis, and SEA-AD provides supplemental human support. The presentation begins with the overall workflow, then moves through DEG analysis, pathway analysis, KDA, human validation, sensitivity analyses, and 17 biological findings. Mouse validation is a potential future step.",
  "",
  "Scientific boundary: The evidence is transcriptomic and exploratory. Separate results within sex/APOE strata do not by themselves establish a disease-by-sex or disease-by-APOE interaction, and RNA abundance does not measure mitochondrial function directly.",
  "",
  "Transition: Preview the overall workflow before beginning the DEG analysis.",
].join("\n");

const WORKFLOW_NOTES = [
  "Teaching goal: Show how the analysis moves from cell-level gene expression to validation.",
  "",
  "Walk through: First, differential-expression analysis identifies genes with higher or lower RNA abundance in Alzheimer’s disease within each fine-cell, sex, and APOE comparison. Second, pathway analysis summarizes the mitochondrial processes represented among those genes. Third, key driver analysis, abbreviated KDA, uses gene networks to nominate genes connected to the MitoCarta MT DEGs. Fourth, human validation compares the ROSMAP findings with SEA-AD and direct broad-cell analyses. A potential future step is mouse validation of selected candidates and mitochondrial function.",
  "",
  "Scientific boundary: The first four stages summarize analyses presented in this deck. Mouse validation is a proposed next step and does not contribute evidence to the current findings.",
  "",
  "Transition: Begin Part 2 with the differential-expression analysis.",
].join("\n");

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

function addText(
  slide,
  name,
  text,
  position,
  {
    fontSize = 18,
    bold = false,
    color = COLORS.white,
    alignment = "left",
    verticalAlignment = "top",
    autoFit = "shrinkText",
  } = {},
) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: FONT_FAMILY,
    fontSize,
    bold,
    color,
    alignment,
    verticalAlignment,
    autoFit,
    wrap: "square",
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
  };
  return shape;
}

function addWorkflowStage(slide, { index, centerX, accent, title, description, potential }) {
  const nodeSize = 48;
  slide.shapes.add({
    geometry: "ellipse",
    name: `workflow-stage-${index}-node`,
    position: { left: centerX - nodeSize / 2, top: 316, width: nodeSize, height: nodeSize },
    fill: potential ? COLORS.panel : accent,
    line: { style: "solid", fill: accent, width: potential ? 2.5 : 0 },
  });
  addText(
    slide,
    `workflow-stage-${index}-number`,
    String(index),
    { left: centerX - 24, top: 316, width: 48, height: 48 },
    {
      fontSize: 18,
      bold: true,
      color: COLORS.white,
      alignment: "center",
      verticalAlignment: "middle",
    },
  );
  if (potential) {
    addText(
      slide,
      "workflow-potential-label",
      "POTENTIAL NEXT STEP",
      { left: centerX - 99, top: 277, width: 198, height: 24 },
      {
        fontSize: 12,
        bold: true,
        color: accent,
        alignment: "center",
        verticalAlignment: "middle",
      },
    );
  }
  addText(
    slide,
    `workflow-stage-${index}-title`,
    title,
    { left: centerX - 104, top: 387, width: 208, height: 56 },
    {
      fontSize: 19,
      bold: true,
      color: COLORS.white,
      alignment: "center",
      verticalAlignment: "middle",
    },
  );
  addText(
    slide,
    `workflow-stage-${index}-description`,
    description,
    { left: centerX - 104, top: 452, width: 208, height: 112 },
    {
      fontSize: 14,
      color: COLORS.muted,
      alignment: "center",
      verticalAlignment: "top",
    },
  );
}

function buildWorkflowSlide(slide) {
  const background = slide.shapes.add({
    geometry: "rect",
    name: "workflow-background",
    position: { left: 0, top: 0, width: 1280, height: 720 },
    fill: COLORS.navy,
    line: { style: "solid", fill: "none", width: 0 },
  });
  background.sendToBack();

  addText(
    slide,
    "workflow-title",
    "Overall workflow",
    { left: 75, top: 123, width: 850, height: 70 },
    { fontSize: 42, bold: true, color: COLORS.white, verticalAlignment: "middle" },
  );
  addText(
    slide,
    "workflow-part-label",
    "PART 1",
    { left: 75, top: 64, width: 230, height: 24 },
    { fontSize: 11, bold: true, color: COLORS.blue, verticalAlignment: "middle" },
  );
  addText(
    slide,
    "workflow-subtitle",
    "From cell-level gene expression to human validation, with mouse experiments as a potential next step",
    { left: 76, top: 207, width: 1120, height: 42 },
    { fontSize: 19, color: COLORS.muted, verticalAlignment: "middle" },
  );

  slide.shapes.add({
    geometry: "line",
    name: "workflow-connector",
    position: { left: 146, top: 340, width: 986, height: 0 },
    fill: "none",
    line: { style: "solid", fill: COLORS.line, width: 3 },
  });

  const stages = [
    {
      index: 1,
      centerX: 146,
      accent: COLORS.blue,
      title: "DEG analysis",
      description:
        "Find differentially expressed genes with higher or lower RNA abundance in AD.",
    },
    {
      index: 2,
      centerX: 393,
      accent: COLORS.cyan,
      title: "Pathway analysis",
      description: "Summarize the mitochondrial processes represented among the DEGs.",
    },
    {
      index: 3,
      centerX: 640,
      accent: COLORS.green,
      title: "Key driver analysis (KDA)",
      description: "Use gene networks to nominate genes connected to MitoCarta MT DEGs.",
    },
    {
      index: 4,
      centerX: 887,
      accent: COLORS.gold,
      title: "Human validation",
      description: "Compare ROSMAP findings with SEA-AD and direct broad-cell analyses.",
    },
    {
      index: 5,
      centerX: 1134,
      accent: COLORS.orange,
      title: "Mouse validation",
      description: "Test selected candidates and mitochondrial function in targeted models.",
      potential: true,
    },
  ];
  for (const stage of stages) addWorkflowStage(slide, stage);

  slide.speakerNotes.textFrame.setText(WORKFLOW_NOTES);
  slide.speakerNotes.setVisible(true);
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

function rewriteRelationshipTarget(relsXml, relationshipTypeSuffix, newTarget) {
  const tag = relationshipTags(relsXml).find((candidate) =>
    relationshipAttribute(candidate, "Type")?.endsWith(`/relationships/${relationshipTypeSuffix}`),
  );
  if (!tag) throw new Error(`Missing ${relationshipTypeSuffix} relationship`);
  const oldTarget = relationshipAttribute(tag, "Target");
  if (!oldTarget) throw new Error(`Missing target for ${relationshipTypeSuffix} relationship`);
  return relsXml.replace(tag, tag.replace(`Target="${oldTarget}"`, `Target="${newTarget}"`));
}

function addContentTypeOverride(contentTypesXml, partName, contentType) {
  if (contentTypesXml.includes(`PartName="${partName}"`)) {
    throw new Error(`Content-type override already exists for ${partName}`);
  }
  const tag = `<Override PartName="${partName}" ContentType="${contentType}"/>`;
  return contentTypesXml.replace("</Types>", `${tag}</Types>`);
}

function updateAppProperties(appXml) {
  let updated = appXml
    .replace(/<Slides>145<\/Slides>/, "<Slides>146</Slides>")
    .replace(/<Notes>145<\/Notes>/, "<Notes>146</Notes>")
    .replace(
      /(<vt:lpstr>Slide Titles<\/vt:lpstr>\s*<\/vt:variant>\s*<vt:variant>\s*<vt:i4>)145(<\/vt:i4>)/,
      "$1146$2",
    );

  const titlesMatch = updated.match(
    /(<TitlesOfParts>\s*<vt:vector size=")148(" baseType="lpstr">)([\s\S]*?)(<\/vt:vector>\s*<\/TitlesOfParts>)/,
  );
  if (!titlesMatch) throw new Error("Could not locate TitlesOfParts metadata");
  let entriesXml = titlesMatch[3];
  const entries = [...entriesXml.matchAll(/<vt:lpstr>[\s\S]*?<\/vt:lpstr>/g)];
  if (entries.length !== 148) {
    throw new Error(`Expected 148 TitlesOfParts entries, found ${entries.length}`);
  }
  const firstSlideEntry = entries[3];
  const insertPosition = firstSlideEntry.index + firstSlideEntry[0].length;
  entriesXml =
    entriesXml.slice(0, insertPosition) +
    firstSlideEntry[0] +
    entriesXml.slice(insertPosition);
  updated = updated.replace(
    titlesMatch[0],
    `${titlesMatch[1]}149${titlesMatch[2]}${entriesXml}${titlesMatch[4]}`,
  );
  return updated;
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
  const sourceSlides = slidesFromPresentation(presentation);
  if (sourceSlides.length !== SOURCE_SLIDE_COUNT) {
    throw new Error(`Expected ${SOURCE_SLIDE_COUNT} slides, found ${sourceSlides.length}`);
  }

  const sourceSnapshot = await presentation.inspect({
    kind: "slide,textbox,notes,layout",
    maxChars: 6000000,
  });
  const sourceRecords = parseNdjson(sourceSnapshot.ndjson);

  for (const update of PART_TEXT_UPDATES) {
    const matches = sourceRecords.filter(
      (record) =>
        record.kind === "textbox" &&
        record.slide === update.sourceSlide &&
        record.text === update.oldText,
    );
    if (matches.length !== 1) {
      throw new Error(
        `Expected one '${update.oldText}' label on slide ${update.sourceSlide}, found ${matches.length}`,
      );
    }
    presentation.resolve(matches[0].id).text.replace(update.oldText, update.newText);
  }

  sourceSlides[0].speakerNotes.textFrame.setText(TITLE_SLIDE_NOTES);
  sourceSlides[0].speakerNotes.setVisible(true);

  const notesUpdates = new Map();
  for (const [slideNumber, oldText, newText] of [
    [14, "Part 3", "Part 4"],
    [15, "Part 3", "Part 4"],
    [42, "Part 5", "Part 6"],
  ]) {
    const currentNotes = sourceRecords.find(
      (record) => record.kind === "notes" && record.slide === slideNumber,
    )?.text;
    if (!currentNotes?.includes(oldText)) {
      throw new Error(`Slide ${slideNumber} notes do not contain '${oldText}'`);
    }
    const updatedNotes = currentNotes.split(oldText).join(newText);
    notesUpdates.set(slideNumber, updatedNotes);
    sourceSlides[slideNumber - 1].speakerNotes.textFrame.setText(updatedNotes);
    sourceSlides[slideNumber - 1].speakerNotes.setVisible(true);
  }
  notesUpdates.set(1, TITLE_SLIDE_NOTES);

  presentation.slides.insert({
    after: sourceSlides[0],
    layoutId: "/ppt/slideLayouts/slideLayout7.xml",
  });
  const workflowSlide = presentation.slides.getItem(1);
  buildWorkflowSlide(workflowSlide);

  const artifactSlides = slidesFromPresentation(presentation);
  if (artifactSlides.length !== FINAL_SLIDE_COUNT) {
    throw new Error(`Expected ${FINAL_SLIDE_COUNT} artifact slides, found ${artifactSlides.length}`);
  }
  const workflowBeforePng = await blobBuffer(
    await workflowSlide.export({ format: "png", scale: 1.5 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "workflow-artifact.png"), workflowBeforePng);
  await fs.writeFile(
    path.join(BUILD_DIR, "workflow-artifact.layout.json"),
    Buffer.from(await (await workflowSlide.export({ format: "layout" })).arrayBuffer()),
  );

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed during the edit");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));

  for (const update of PART_TEXT_UPDATES) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, update.sourceSlide);
    const artifactSlidePart = await visibleSlidePart(artifactZip, update.sourceSlide + 1);
    const revisedSlideXml = await artifactZip.file(artifactSlidePart)?.async("string");
    if (!revisedSlideXml) throw new Error(`Missing revised slide XML for slide ${update.sourceSlide}`);
    sourceZip.file(sourceSlidePart, revisedSlideXml);
  }
  for (const sourceSlideNumber of notesUpdates.keys()) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, sourceSlideNumber);
    const artifactVisibleSlide = sourceSlideNumber === 1 ? 1 : sourceSlideNumber + 1;
    const artifactSlidePart = await visibleSlidePart(artifactZip, artifactVisibleSlide);
    const sourceNotesPart = await relatedPartPath(sourceZip, sourceSlidePart, "notesSlide");
    const artifactNotesPart = await relatedPartPath(artifactZip, artifactSlidePart, "notesSlide");
    const revisedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!revisedNotesXml) throw new Error(`Missing revised notes for slide ${sourceSlideNumber}`);
    sourceZip.file(sourceNotesPart, revisedNotesXml);
  }

  const artifactNewSlidePart = await visibleSlidePart(artifactZip, 2);
  const artifactNewSlideRelsPart = relationshipPartPath(artifactNewSlidePart);
  const artifactNewNotesPart = await relatedPartPath(
    artifactZip,
    artifactNewSlidePart,
    "notesSlide",
  );
  const artifactNewNotesRelsPart = relationshipPartPath(artifactNewNotesPart);
  const [newSlideXml, artifactNewSlideRelsXml, newNotesXml, artifactNewNotesRelsXml] =
    await Promise.all([
      artifactZip.file(artifactNewSlidePart)?.async("string"),
      artifactZip.file(artifactNewSlideRelsPart)?.async("string"),
      artifactZip.file(artifactNewNotesPart)?.async("string"),
      artifactZip.file(artifactNewNotesRelsPart)?.async("string"),
    ]);
  if (!newSlideXml || !artifactNewSlideRelsXml || !newNotesXml || !artifactNewNotesRelsXml) {
    throw new Error("Artifact candidate is missing a new-slide package part");
  }

  const existingSlidePartNumbers = Object.keys(sourceZip.files)
    .map((name) => name.match(/^ppt\/slides\/slide(\d+)\.xml$/)?.[1])
    .filter(Boolean)
    .map(Number);
  const existingNotesPartNumbers = Object.keys(sourceZip.files)
    .map((name) => name.match(/^ppt\/notesSlides\/notesSlide(\d+)\.xml$/)?.[1])
    .filter(Boolean)
    .map(Number);
  const newPartNumber = Math.max(...existingSlidePartNumbers, ...existingNotesPartNumbers) + 1;
  const newSlidePart = `ppt/slides/slide${newPartNumber}.xml`;
  const newSlideRelsPart = relationshipPartPath(newSlidePart);
  const newNotesPart = `ppt/notesSlides/notesSlide${newPartNumber}.xml`;
  const newNotesRelsPart = relationshipPartPath(newNotesPart);

  const newSlideRelsXml = rewriteRelationshipTarget(
    artifactNewSlideRelsXml,
    "notesSlide",
    `../notesSlides/notesSlide${newPartNumber}.xml`,
  );
  const newNotesRelsXml = rewriteRelationshipTarget(
    artifactNewNotesRelsXml,
    "slide",
    `../slides/slide${newPartNumber}.xml`,
  );
  sourceZip.file(newSlidePart, newSlideXml);
  sourceZip.file(newSlideRelsPart, newSlideRelsXml);
  sourceZip.file(newNotesPart, newNotesXml);
  sourceZip.file(newNotesRelsPart, newNotesRelsXml);

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
  const slideIds = slideIdTags
    .map((tag) => Number(tag.match(/\bid="(\d+)"/)?.[1]))
    .filter(Number.isFinite);
  const newSlideId = Math.max(...slideIds) + 1;
  const relationshipIds = relationshipTags(presentationRelsXml)
    .map((tag) => relationshipAttribute(tag, "Id")?.match(/^rId(\d+)$/)?.[1])
    .filter(Boolean)
    .map(Number);
  const newRelationshipId = `rId${Math.max(...relationshipIds) + 1}`;
  const newSlideIdTag = `<p:sldId id="${newSlideId}" r:id="${newRelationshipId}"/>`;
  presentationXml = presentationXml.replace(
    slideIdTags[0],
    `${slideIdTags[0]}${newSlideIdTag}`,
  );
  const newPresentationRelationship =
    `<Relationship Id="${newRelationshipId}" ` +
    `Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" ` +
    `Target="slides/slide${newPartNumber}.xml"/>`;
  presentationRelsXml = presentationRelsXml.replace(
    "</Relationships>",
    `${newPresentationRelationship}</Relationships>`,
  );
  contentTypesXml = addContentTypeOverride(
    contentTypesXml,
    `/${newSlidePart}`,
    "application/vnd.openxmlformats-officedocument.presentationml.slide+xml",
  );
  contentTypesXml = addContentTypeOverride(
    contentTypesXml,
    `/${newNotesPart}`,
    "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml",
  );
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
    requiredNativeChartOwnerSlides: [15],
    requiredEmbeddedWorkbookChartOwnerSlides: [15],
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
      families: [FONT_FAMILY],
      referencePath: SOURCE,
      referenceSha256: sourceHash,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD_DIR, "insert_workflow_part.validation.json"),
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

  const expectedPartLabels = [
    [2, "PART 1"],
    [3, "PART 2"],
    [6, "PART 3"],
    [16, "PART 4"],
    [30, "PART 5"],
    [37, "PART 5"],
    [43, "PART 6"],
  ];
  for (const [slideNumber, label] of expectedPartLabels) {
    const matches = finalRecords.filter(
      (record) =>
        record.kind === "textbox" && record.slide === slideNumber && record.text === label,
    );
    if (matches.length !== 1) {
      throw new Error(`Expected one '${label}' label on final slide ${slideNumber}`);
    }
  }
  const workflowTitle = finalRecords.find(
    (record) => record.kind === "slide" && record.slide === 2,
  )?.title;
  if (workflowTitle !== "Overall workflow") {
    throw new Error(`Final slide 2 title is '${workflowTitle}'`);
  }
  const finalNotesChecks = [
    [1, "Preview the overall workflow"],
    [2, "Mouse validation is a proposed next step"],
    [15, "Part 4"],
    [16, "Part 4"],
    [43, "Part 6"],
  ];
  for (const [slideNumber, phrase] of finalNotesChecks) {
    const text = finalRecords.find(
      (record) => record.kind === "notes" && record.slide === slideNumber,
    )?.text;
    if (!text?.includes(phrase)) {
      throw new Error(`Final slide ${slideNumber} notes lack '${phrase}'`);
    }
  }

  const renderSlideNumbers = [1, 2, 3, 6, 15, 16, 30, 37, 43];
  for (const slideNumber of renderSlideNumbers) {
    const png = await blobBuffer(
      await reopened.export({
        slide: finalSlides[slideNumber - 1],
        format: "png",
        scale: 1.5,
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
        insertedSlide: 2,
        finalSlideCount: FINAL_SLIDE_COUNT,
        partLabels: expectedPartLabels,
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
