#!/usr/bin/env node

/** Revise slide 6 gene-set definitions and insert an editable set diagram as slide 7. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const SKILL_DIR =
  "/Users/rzhuang/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations";
const WORKSPACE_DIR = "/Users/rzhuang/Documents/VscodeProjects/alzheimer";
const DEFAULT_SOURCE = path.join(
  WORKSPACE_DIR,
  "docs/presentations/09162026/09162026_sex_apoe_kda_fine_broad.pptx",
);
const DEFAULT_BUILD = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slide6_gene_sets_slide7_venn_20260920/build",
);
const DEFAULT_OUTPUT = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slide6_gene_sets_slide7_venn_20260920/output/09162026_sex_apoe_kda_fine_broad_slide6_gene_sets_slide7_venn_20260920.pptx",
);
const EXPECTED_SOURCE_SLIDES = 159;
const EXPECTED_OUTPUT_SLIDES = 160;
const EXPECTED_SLIDE_SIZE_EMU = "12192000,6858000";
const FONT_FAMILY = "Arial";

const COLORS = {
  background: "#F7F9FC",
  navy: "#0F233D",
  dark: "#1F2730",
  gray: "#4E5A68",
  line: "#D8E2EC",
  paleBlue: "#E8F5FB",
  blue: "#0072B2",
  paleGreen: "#E4F4EE",
  green: "#008A68",
  paleGold: "#FFF3D6",
  gold: "#A56600",
  white: "#FFFFFF",
};

function parseArgs(argv) {
  const result = {
    source: DEFAULT_SOURCE,
    build: DEFAULT_BUILD,
    output: DEFAULT_OUTPUT,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    const value = argv[index + 1];
    if (["--source", "--build", "--output"].includes(key)) {
      if (!value) throw new Error(`Missing value after ${key}`);
      result[key.slice(2)] = path.resolve(value);
      index += 1;
    } else {
      throw new Error(`Unknown argument: ${key}`);
    }
  }
  return result;
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

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

async function blobBuffer(blob) {
  return Buffer.from(await blob.arrayBuffer());
}

function addText(
  slide,
  name,
  text,
  position,
  {
    fontSize = 18,
    bold = false,
    color = COLORS.dark,
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

function addDefinitionRow(
  slide,
  { top, number, term, definition, role, fill, accent },
) {
  slide.shapes.add({
    geometry: "roundRect",
    name: `definition-${number}-background`,
    position: { left: 64, top, width: 1152, height: 166 },
    fill,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 12,
    shadow: "shadow-sm",
  });
  slide.shapes.add({
    geometry: "rect",
    name: `definition-${number}-accent`,
    position: { left: 64, top: top + 22, width: 8, height: 122 },
    fill: accent,
    line: { style: "solid", fill: "none", width: 0 },
  });
  addText(
    slide,
    `definition-${number}-number`,
    String(number),
    { left: 91, top: top + 52, width: 42, height: 58 },
    {
      fontSize: 28,
      bold: true,
      color: accent,
      alignment: "center",
      verticalAlignment: "middle",
    },
  );
  addText(
    slide,
    `definition-${number}-term`,
    term,
    { left: 151, top: top + 28, width: 294, height: 110 },
    { fontSize: 24, bold: true, color: COLORS.navy, verticalAlignment: "middle" },
  );
  addText(
    slide,
    `definition-${number}-meaning`,
    definition,
    { left: 470, top: top + 25, width: 390, height: 116 },
    { fontSize: 19, color: COLORS.dark, verticalAlignment: "middle" },
  );
  addText(
    slide,
    `definition-${number}-role`,
    role,
    { left: 885, top: top + 25, width: 294, height: 116 },
    { fontSize: 19, color: COLORS.dark, verticalAlignment: "middle" },
  );
}

function buildGeneSetsSlide(slide) {
  slide.shapes.deleteAll();
  const background = slide.shapes.add({
    geometry: "rect",
    name: "gene-sets-background",
    position: { left: 0, top: 0, width: 1280, height: 720 },
    fill: COLORS.background,
    line: { style: "solid", fill: "none", width: 0 },
  });
  background.sendToBack();

  addText(
    slide,
    "gene-sets-title",
    "Two mitochondrial gene sets used in this study",
    { left: 56, top: 39, width: 1160, height: 54 },
    { fontSize: 33, bold: true, color: COLORS.navy, verticalAlignment: "middle" },
  );
  addText(
    slide,
    "gene-sets-header-term",
    "GENE SET",
    { left: 151, top: 133, width: 294, height: 22 },
    { fontSize: 13, bold: true, color: COLORS.gray },
  );
  addText(
    slide,
    "gene-sets-header-meaning",
    "WHAT IT INCLUDES",
    { left: 470, top: 133, width: 390, height: 22 },
    { fontSize: 13, bold: true, color: COLORS.gray },
  );
  addText(
    slide,
    "gene-sets-header-role",
    "ROLE IN THIS STUDY",
    { left: 885, top: 133, width: 294, height: 22 },
    { fontSize: 13, bold: true, color: COLORS.gray },
  );

  addDefinitionRow(slide, {
    top: 163,
    number: 1,
    term: "Core MT genes",
    definition:
      "13 protein-coding genes in mitochondrial DNA (mtDNA). All encode structural oxidative-phosphorylation (OXPHOS) subunits.",
    role: "mtDNA-encoded OXPHOS results",
    fill: COLORS.paleBlue,
    accent: COLORS.blue,
  });
  addDefinitionRow(slide, {
    top: 350,
    number: 2,
    term: "MitoCarta MT genes",
    definition:
      "1,136 protein-coding genes assigned to mitochondria by MitoCarta: 13 core MT genes plus 1,123 genes encoded by nuclear DNA.",
    role: "Mitochondrial pathway definitions and KDA input queries",
    fill: COLORS.paleGreen,
    accent: COLORS.green,
  });

  slide.shapes.add({
    geometry: "roundRect",
    name: "gene-sets-boundary-note-background",
    position: { left: 126, top: 570, width: 1028, height: 82 },
    fill: COLORS.paleGold,
    line: { style: "solid", fill: "none", width: 0 },
    borderRadius: 10,
  });
  addText(
    slide,
    "gene-sets-boundary-note",
    "The other 24 genes in mtDNA encode 22 tRNAs and 2 rRNAs; they are outside the protein-gene sets analyzed here.",
    { left: 160, top: 586, width: 960, height: 50 },
    { fontSize: 18, color: COLORS.dark, alignment: "center", verticalAlignment: "middle" },
  );

  slide.speakerNotes.textFrame.setText(
    structuredNotes({
      goal:
        "Define the two distinct mitochondrial protein-gene sets used in this study and remove the redundant core-MT-OXPHOS label.",
      walkthrough:
        "Core MT genes means the 13 protein-coding genes in mitochondrial DNA. All 13 encode structural subunits of oxidative phosphorylation, abbreviated OXPHOS, so core MT genes and core MT OXPHOS genes are the same set in this study. MitoCarta MT genes is the broader 1,136-gene protein inventory: the same 13 core MT genes plus 1,123 genes encoded by nuclear DNA. The MitoCarta inventory defines mitochondrial pathways and KDA input queries.",
      boundary:
        "Mitochondrial DNA contains 37 genes in total, but the 22 transfer-RNA genes and two ribosomal-RNA genes are not part of the protein-gene sets analyzed here. RNA abundance from the 13 core MT genes does not measure mtDNA copy number, OXPHOS protein abundance, or mitochondrial function.",
      transition:
        "Next, visualize how core MT genes and nuclear-encoded OXPHOS genes fit within the MitoCarta inventory.",
    }),
  );
  slide.speakerNotes.setVisible(true);
}

function buildSetDiagramSlide(slide) {
  const background = slide.shapes.add({
    geometry: "rect",
    name: "mitocarta-oxphos-background",
    position: { left: 0, top: 0, width: 1280, height: 720 },
    fill: COLORS.background,
    line: { style: "solid", fill: "none", width: 0 },
  });
  background.sendToBack();

  addText(
    slide,
    "mitocarta-oxphos-title",
    "How the OXPHOS gene sets fit within MitoCarta",
    { left: 56, top: 39, width: 1160, height: 54 },
    { fontSize: 33, bold: true, color: COLORS.navy, verticalAlignment: "middle" },
  );
  addText(
    slide,
    "mitocarta-oxphos-subtitle",
    "All 99 structural OXPHOS genes analyzed here are part of the 1,136-gene MitoCarta inventory.",
    { left: 58, top: 99, width: 1120, height: 35 },
    { fontSize: 18, color: COLORS.gray, verticalAlignment: "middle" },
  );

  slide.shapes.add({
    geometry: "ellipse",
    name: "mitocarta-circle",
    position: { left: 88, top: 145, width: 790, height: 500 },
    fill: COLORS.paleGreen,
    line: { style: "solid", fill: COLORS.green, width: 3 },
  });
  addText(
    slide,
    "mitocarta-circle-label",
    "MitoCarta MT genes\n1,136",
    { left: 145, top: 194, width: 250, height: 76 },
    { fontSize: 24, bold: true, color: COLORS.green, alignment: "center", verticalAlignment: "middle" },
  );

  slide.shapes.add({
    geometry: "ellipse",
    name: "oxphos-circle",
    position: { left: 340, top: 220, width: 475, height: 365 },
    fill: COLORS.paleGold,
    line: { style: "solid", fill: COLORS.gold, width: 3 },
  });
  addText(
    slide,
    "oxphos-circle-label",
    "Structural OXPHOS genes\n99",
    { left: 418, top: 265, width: 320, height: 70 },
    { fontSize: 25, bold: true, color: COLORS.gold, alignment: "center", verticalAlignment: "middle" },
  );
  slide.shapes.add({
    geometry: "line",
    name: "oxphos-split-line",
    position: { left: 578, top: 360, width: 0, height: 145 },
    fill: "none",
    line: { style: "solid", fill: COLORS.gold, width: 2 },
  });
  addText(
    slide,
    "core-mt-region-label",
    "Core MT genes\n13\nencoded by mtDNA",
    { left: 385, top: 366, width: 170, height: 127 },
    { fontSize: 20, bold: true, color: COLORS.blue, alignment: "center", verticalAlignment: "middle" },
  );
  addText(
    slide,
    "nuclear-oxphos-region-label",
    "Nuclear-encoded\nOXPHOS genes\n86",
    { left: 600, top: 366, width: 174, height: 127 },
    { fontSize: 20, bold: true, color: COLORS.navy, alignment: "center", verticalAlignment: "middle" },
  );
  addText(
    slide,
    "other-mitocarta-label",
    "Other MitoCarta MT genes\n1,037",
    { left: 130, top: 502, width: 265, height: 72 },
    { fontSize: 20, bold: true, color: COLORS.green, alignment: "center", verticalAlignment: "middle" },
  );

  slide.shapes.add({
    geometry: "roundRect",
    name: "oxphos-equation-card",
    position: { left: 920, top: 205, width: 292, height: 152 },
    fill: COLORS.white,
    line: { style: "solid", fill: COLORS.line, width: 1.5 },
    borderRadius: 12,
    shadow: "shadow-sm",
  });
  addText(
    slide,
    "oxphos-equation",
    "13 + 86 = 99",
    { left: 946, top: 232, width: 240, height: 48 },
    { fontSize: 31, bold: true, color: COLORS.navy, alignment: "center", verticalAlignment: "middle" },
  );
  addText(
    slide,
    "oxphos-equation-caption",
    "structural OXPHOS genes",
    { left: 946, top: 289, width: 240, height: 35 },
    { fontSize: 18, color: COLORS.gray, alignment: "center", verticalAlignment: "middle" },
  );

  slide.shapes.add({
    geometry: "roundRect",
    name: "nuclear-definition-card",
    position: { left: 920, top: 384, width: 292, height: 168 },
    fill: COLORS.paleBlue,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 12,
  });
  addText(
    slide,
    "nuclear-definition-title",
    "Nuclear-encoded",
    { left: 948, top: 409, width: 236, height: 32 },
    { fontSize: 20, bold: true, color: COLORS.blue, alignment: "center", verticalAlignment: "middle" },
  );
  addText(
    slide,
    "nuclear-definition-text",
    "The gene is located in nuclear DNA; its protein functions in mitochondria.",
    { left: 950, top: 452, width: 232, height: 76 },
    { fontSize: 17, color: COLORS.dark, alignment: "center", verticalAlignment: "middle" },
  );
  addText(
    slide,
    "set-diagram-footnote",
    "Gene-set membership is shown; areas are not proportional to gene counts.",
    { left: 879, top: 605, width: 338, height: 42 },
    { fontSize: 14, color: COLORS.gray, alignment: "center", verticalAlignment: "middle" },
  );

  slide.speakerNotes.textFrame.setText(
    structuredNotes({
      goal:
        "Show the containment and split of the structural OXPHOS gene set within the MitoCarta MT inventory.",
      walkthrough:
        "The large circle is the 1,136-gene MitoCarta MT inventory. The inner circle contains the 99 structural OXPHOS genes used in this study, all of which are in MitoCarta. That OXPHOS set has two parts: 13 core MT genes encoded by mitochondrial DNA and 86 OXPHOS genes encoded by nuclear DNA. The remaining 1,037 MitoCarta genes support other mitochondrial pathways and functions.",
      boundary:
        "This diagram shows gene-set membership, not expression direction, pathway enrichment, protein abundance, or mitochondrial function. Nuclear-encoded describes the DNA location of a gene; the encoded protein can still function in mitochondria. Circle areas are not proportional to gene counts.",
      transition:
        "With the gene-set relationships defined, introduce the three levels of MitoCarta pathways.",
    }),
  );
  slide.speakerNotes.setVisible(true);
}

async function repairNativeChartPackage({ sourceBytes, candidatePath, JSZip }) {
  const sourceZip = await JSZip.loadAsync(sourceBytes);
  const candidateZip = await JSZip.loadAsync(await fs.readFile(candidatePath));
  for (const partName of [
    "ppt/charts/chart1.xml",
    "ppt/charts/_rels/chart1.xml.rels",
    "ppt/embeddings/Microsoft_Excel_Worksheet.xlsx",
  ]) {
    const part = sourceZip.file(partName);
    if (!part) throw new Error(`Source chart package is missing ${partName}`);
    candidateZip.file(partName, await part.async("nodebuffer"));
  }

  let ownerRelsPath;
  let ownerRelsText;
  for (const relPath of Object.keys(candidateZip.files).filter((name) =>
    /^ppt\/slides\/_rels\/slide\d+\.xml\.rels$/.test(name),
  )) {
    const relText = await candidateZip.file(relPath)?.async("string");
    if (relText?.includes("/ppt/slides/charts/chart1.xml")) {
      ownerRelsPath = relPath;
      ownerRelsText = relText;
      break;
    }
  }
  if (!ownerRelsPath || !ownerRelsText) {
    throw new Error("Could not locate the shifted chart relationship");
  }
  candidateZip.file(
    ownerRelsPath,
    ownerRelsText.replace("/ppt/slides/charts/chart1.xml", "../charts/chart1.xml"),
  );
  candidateZip.remove("ppt/slides/charts/chart1.xml");

  let contentTypes = await candidateZip.file("[Content_Types].xml")?.async("string");
  if (!contentTypes) throw new Error("Candidate content types are missing");
  contentTypes = contentTypes.replace(
    "/ppt/slides/charts/chart1.xml",
    "/ppt/charts/chart1.xml",
  );
  if (!contentTypes.includes('Extension="xlsx"')) {
    contentTypes = contentTypes.replace(
      "</Types>",
      '<Default Extension="xlsx" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"/></Types>',
    );
  }
  candidateZip.file("[Content_Types].xml", contentTypes);
  await fs.writeFile(
    candidatePath,
    await candidateZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );
  return ownerRelsPath;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  for (const target of [args.source, args.build, args.output]) {
    if (!path.isAbsolute(target)) throw new Error(`Path must be absolute: ${target}`);
  }
  const sourceStat = await fs.stat(args.source).catch(() => undefined);
  if (!sourceStat?.isFile()) throw new Error(`Missing source deck: ${args.source}`);
  if (await fs.stat(args.output).catch(() => undefined)) {
    throw new Error(`Output already exists: ${args.output}`);
  }
  await fs.mkdir(args.build, { recursive: true });
  await fs.mkdir(path.dirname(args.output), { recursive: true });

  const { importRuntimeModule } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href
  );
  const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");
  const JSZipModule = await importRuntimeModule("jszip");
  const JSZip = JSZipModule.default ?? JSZipModule;
  const presentation = await PresentationFile.importPptx(await FileBlob.load(args.source));
  const sourceSlides = slidesFromPresentation(presentation);
  if (sourceSlides.length !== EXPECTED_SOURCE_SLIDES) {
    throw new Error(
      `Expected ${EXPECTED_SOURCE_SLIDES} source slides, found ${sourceSlides.length}`,
    );
  }

  sourceSlides[4].speakerNotes.textFrame.setText(
    structuredNotes({
      goal: "Position pathway analysis between DEG testing and network analysis.",
      walkthrough:
        "Pathway analysis asks whether mitochondrial DEG results are concentrated in predefined pathways, including mtDNA-encoded OXPHOS, nuclear OXPHOS, mitochondrial translation, and MICOS or inner-membrane organization. It therefore describes pathway-level signal before network-based driver nomination.",
      boundary:
        "Pathway enrichment describes the composition or ranking of gene-level results. It does not identify an upstream driver or prove that a pathway is more or less functional.",
      transition:
        "First distinguish the 13 core MT genes from the broader MitoCarta MT inventory.",
    }),
  );
  sourceSlides[4].speakerNotes.setVisible(true);

  buildGeneSetsSlide(sourceSlides[5]);
  presentation.slides.insert({
    after: sourceSlides[5],
    layoutId: "/ppt/slideLayouts/slideLayout7.xml",
  });
  const insertedSlide = presentation.slides.getItem(6);
  buildSetDiagramSlide(insertedSlide);

  const outputSlides = slidesFromPresentation(presentation);
  if (outputSlides.length !== EXPECTED_OUTPUT_SLIDES) {
    throw new Error(
      `Expected ${EXPECTED_OUTPUT_SLIDES} output slides, found ${outputSlides.length}`,
    );
  }

  for (const slideNumber of [6, 7, 8]) {
    const preview = await blobBuffer(
      await presentation.export({
        slide: outputSlides[slideNumber - 1],
        format: "png",
        scale: 2,
      }),
    );
    await fs.writeFile(
      path.join(args.build, `preview-slide-${String(slideNumber).padStart(3, "0")}.png`),
      preview,
    );
  }

  const sourceBytes = await fs.readFile(args.source);
  const sourceSha256 = sha256(sourceBytes);
  const candidatePath = path.join(args.build, "candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
  const chartOwnerRelsPath = await repairNativeChartPackage({
    sourceBytes,
    candidatePath,
    JSZip,
  });

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const result = await finalizePresentation({
    explicitTotalSlideCount: EXPECTED_OUTPUT_SLIDES,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [14],
    requiredEmbeddedWorkbookChartOwnerSlides: [14],
    nativeChartTargetApplication: "powerpoint",
    workspaceDir: WORKSPACE_DIR,
    candidatePath,
    finalPath: args.output,
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
      EXPECTED_SLIDE_SIZE_EMU,
      "--validate-bullet-geometry",
      "--validate-heading-fit",
    ],
    fontPolicy: {
      basis: "reference",
      families: [FONT_FAMILY],
      referencePath: args.source,
      referenceSha256: sourceSha256,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(args.build, "slide6_slide7_update.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(args.output));
  const finalSlides = slidesFromPresentation(reopened);
  if (finalSlides.length !== EXPECTED_OUTPUT_SLIDES) {
    throw new Error(`Final deck contains ${finalSlides.length} slides`);
  }
  const notesSnapshot = await reopened.inspect({ kind: "notes", maxChars: 2000000 });
  const notesBySlide = new Map(
    notesSnapshot.ndjson
      .split("\n")
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .filter((record) => record.kind === "notes")
      .map((record) => [record.slide, record.text]),
  );
  if (!notesBySlide.get(6)?.includes("two distinct mitochondrial protein-gene sets")) {
    throw new Error("Revised slide 6 notes did not survive export");
  }
  if (!notesBySlide.get(7)?.includes("13 core MT genes")) {
    throw new Error("Inserted slide 7 notes did not survive export");
  }

  console.log(
    JSON.stringify(
      {
        source: args.source,
        sourceSha256,
        output: args.output,
        outputSha256: sha256(await fs.readFile(args.output)),
        slideCount: finalSlides.length,
        revisedSlide: 6,
        insertedSlide: 7,
        chartOwnerRelsPath,
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
