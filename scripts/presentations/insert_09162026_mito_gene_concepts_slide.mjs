#!/usr/bin/env node

/** Insert a slide after slide 5 that distinguishes three mitochondrial gene sets. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const SKILL_DIR =
  "/Users/rzhuang/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations";
const WORKSPACE_DIR = "/Users/rzhuang/Documents/VscodeProjects/alzheimer";
const DEFAULT_SOURCE = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slides41_47_script_refresh/output/09162026_sex_apoe_kda_fine_broad_slides41_47_notes_refreshed_20260919.pptx",
);
const DEFAULT_BUILD = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_mito_gene_concepts_slide/build",
);
const DEFAULT_OUTPUT = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_mito_gene_concepts_slide/output/09162026_sex_apoe_kda_fine_broad_with_mito_gene_concepts_20260919.pptx",
);
const EXPECTED_SOURCE_SLIDES = 160;
const EXPECTED_OUTPUT_SLIDES = 161;
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
  palePurple: "#F2EAF8",
  purple: "#7A4298",
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
    position: { left: 64, top, width: 1152, height: 120 },
    fill,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 12,
    shadow: "shadow-sm",
  });
  slide.shapes.add({
    geometry: "rect",
    name: `definition-${number}-accent`,
    position: { left: 64, top: top + 18, width: 8, height: 84 },
    fill: accent,
    line: { style: "solid", fill: "none", width: 0 },
  });
  addText(
    slide,
    `definition-${number}-number`,
    String(number),
    { left: 91, top: top + 29, width: 42, height: 54 },
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
    { left: 151, top: top + 22, width: 310, height: 76 },
    { fontSize: 22, bold: true, color: COLORS.navy, verticalAlignment: "middle" },
  );
  addText(
    slide,
    `definition-${number}-meaning`,
    definition,
    { left: 480, top: top + 19, width: 375, height: 82 },
    { fontSize: 18, color: COLORS.dark, verticalAlignment: "middle" },
  );
  addText(
    slide,
    `definition-${number}-role`,
    role,
    { left: 880, top: top + 19, width: 300, height: 82 },
    { fontSize: 18, color: COLORS.dark, verticalAlignment: "middle" },
  );
}

function buildGeneConceptsSlide(slide) {
  const background = slide.shapes.add({
    geometry: "rect",
    name: "gene-concepts-background",
    position: { left: 0, top: 0, width: 1280, height: 720 },
    fill: COLORS.background,
    line: { style: "solid", fill: "none", width: 0 },
  });
  background.sendToBack();

  addText(
    slide,
    "gene-concepts-title",
    "Three mitochondrial gene sets used in this study",
    { left: 56, top: 39, width: 1160, height: 54 },
    { fontSize: 33, bold: true, color: COLORS.navy, verticalAlignment: "middle" },
  );
  addText(
    slide,
    "gene-concepts-header-term",
    "GENE SET",
    { left: 151, top: 135, width: 310, height: 22 },
    { fontSize: 13, bold: true, color: COLORS.gray },
  );
  addText(
    slide,
    "gene-concepts-header-meaning",
    "WHAT IT INCLUDES",
    { left: 480, top: 135, width: 375, height: 22 },
    { fontSize: 13, bold: true, color: COLORS.gray },
  );
  addText(
    slide,
    "gene-concepts-header-role",
    "ROLE IN THIS STUDY",
    { left: 880, top: 135, width: 300, height: 22 },
    { fontSize: 13, bold: true, color: COLORS.gray },
  );

  addDefinitionRow(slide, {
    top: 165,
    number: 1,
    term: "Genes in\nmitochondrial DNA",
    definition:
      "37 genes encoded by mitochondrial DNA (mtDNA), the small DNA molecule inside mitochondria.",
    role: "13 protein genes\n22 tRNA genes\n2 rRNA genes",
    fill: COLORS.paleBlue,
    accent: COLORS.blue,
  });
  addDefinitionRow(slide, {
    top: 300,
    number: 2,
    term: "MitoCarta MT genes",
    definition:
      "1,136 mitochondrial (MT) protein genes listed in MitoCarta.",
    role: "13 encoded by mtDNA\n1,123 encoded by nuclear DNA",
    fill: COLORS.paleGreen,
    accent: COLORS.green,
  });
  addDefinitionRow(slide, {
    top: 435,
    number: 3,
    term: "OXPHOS genes in\nmitochondrial DNA",
    definition:
      "The 13 protein genes in mtDNA that contribute to oxidative phosphorylation (OXPHOS).",
    role: "Finding 1 measures RNA\nfrom this 13-gene set",
    fill: COLORS.paleGold,
    accent: COLORS.gold,
  });

  slide.speakerNotes.textFrame.setText(
    structuredNotes({
      goal:
        "Distinguish the three mitochondrial gene sets by where the genes are encoded and how each set is used.",
      walkthrough:
        "Mitochondrial DNA, abbreviated mtDNA, is the small DNA molecule inside mitochondria. It encodes 37 genes: 13 protein genes, 22 transfer-RNA genes, and two ribosomal-RNA genes. The MitoCarta MT gene inventory is broader, where MT means mitochondrial. It contains 1,136 genes whose protein products are associated with mitochondria: 13 are encoded by mtDNA and 1,123 are encoded by nuclear DNA. The third set focuses on the 13 protein-coding genes in mtDNA. All 13 contribute to oxidative phosphorylation, abbreviated OXPHOS. Finding 1 measures RNA from this 13-gene set.",
      boundary:
        "The label mtDNA refers to the DNA molecule. The labels on the slide refer to gene sets. MitoCarta MT genes refers specifically to the 1,136-gene protein inventory. The shorthand core MT genes is avoided because it does not clearly distinguish the 37 genes encoded by mtDNA from the 1,136-gene MitoCarta inventory. RNA abundance from the 13 OXPHOS genes does not measure mtDNA copy number, OXPHOS protein abundance, or mitochondrial function.",
      transition:
        "With the gene sets distinguished, introduce the three-level MitoCarta pathway hierarchy.",
    }),
  );
  slide.speakerNotes.setVisible(true);
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

  const beforeHashes = new Map();
  for (let index = 0; index < sourceSlides.length; index += 1) {
    const rendered = await blobBuffer(
      await presentation.export({ slide: sourceSlides[index], format: "png", scale: 1 }),
    );
    beforeHashes.set(index + 1, sha256(rendered));
    if ([5, 6, 7].includes(index + 1)) {
      await fs.writeFile(
        path.join(args.build, `before-slide-${String(index + 1).padStart(3, "0")}.png`),
        rendered,
      );
    }
  }

  sourceSlides[4].speakerNotes.textFrame.setText(
    structuredNotes({
      goal: "Position pathway analysis between DEG testing and network analysis.",
      walkthrough:
        "Pathway analysis asks whether mitochondrial DEG results are concentrated in predefined pathways, including mtDNA-encoded OXPHOS, nuclear OXPHOS, mitochondrial translation, and MICOS or inner-membrane organization. It therefore describes pathway-level signal before network-based driver nomination.",
      boundary:
        "Pathway enrichment describes the composition or ranking of gene-level results. It does not identify an upstream driver or prove that a pathway is more or less functional.",
      transition:
        "First distinguish mitochondrial DNA, mtDNA-encoded OXPHOS genes, and the broader MitoCarta inventory.",
    }),
  );
  sourceSlides[4].speakerNotes.setVisible(true);

  presentation.slides.insert({
    after: sourceSlides[4],
    layoutId: "/ppt/slideLayouts/slideLayout7.xml",
  });
  const insertedSlide = presentation.slides.getItem(5);
  buildGeneConceptsSlide(insertedSlide);

  const outputSlides = slidesFromPresentation(presentation);
  if (outputSlides.length !== EXPECTED_OUTPUT_SLIDES) {
    throw new Error(
      `Expected ${EXPECTED_OUTPUT_SLIDES} output slides, found ${outputSlides.length}`,
    );
  }

  const insertedPreview = await blobBuffer(
    await presentation.export({ slide: insertedSlide, format: "png", scale: 2 }),
  );
  await fs.writeFile(path.join(args.build, "inserted-slide-006.png"), insertedPreview);
  await fs.writeFile(
    path.join(args.build, "inserted-slide-006.layout.json"),
    await (await insertedSlide.export({ format: "layout" })).text(),
  );

  const sourceBytes = await fs.readFile(args.source);
  const sourceSha256 = sha256(sourceBytes);
  const candidatePath = path.join(args.build, "candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

  // Artifact Tool preserves the native chart object but currently relocates it
  // without its embedded workbook during an insertion. Restore the source chart
  // package and point the shifted owner slide to the standard chart location.
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
  const chartOwnerRelsPath = "ppt/slides/_rels/slide13.xml.rels";
  const chartOwnerRels = await candidateZip.file(chartOwnerRelsPath)?.async("string");
  if (!chartOwnerRels?.includes("/ppt/slides/charts/chart1.xml")) {
    throw new Error("Could not locate the shifted chart relationship");
  }
  candidateZip.file(
    chartOwnerRelsPath,
    chartOwnerRels.replace(
      "/ppt/slides/charts/chart1.xml",
      "../charts/chart1.xml",
    ),
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

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const result = await finalizePresentation({
    explicitTotalSlideCount: EXPECTED_OUTPUT_SLIDES,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [13],
    requiredEmbeddedWorkbookChartOwnerSlides: [13],
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
    receiptPath: path.join(
      args.build,
      "09162026_sex_apoe_kda_fine_broad_with_mito_gene_concepts.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(args.output));
  const finalSlides = slidesFromPresentation(reopened);
  if (finalSlides.length !== EXPECTED_OUTPUT_SLIDES) {
    throw new Error(`Final deck contains ${finalSlides.length} slides`);
  }
  const finalRenderDir = path.join(args.build, "final-slides");
  await fs.mkdir(finalRenderDir, { recursive: true });
  for (let index = 0; index < finalSlides.length; index += 1) {
    const rendered = await blobBuffer(
      await reopened.export({ slide: finalSlides[index], format: "png", scale: 1 }),
    );
    await fs.writeFile(
      path.join(finalRenderDir, `slide-${String(index + 1).padStart(3, "0")}.png`),
      rendered,
    );
    if (index !== 5) {
      const sourceNumber = index < 5 ? index + 1 : index;
      const beforeHash = beforeHashes.get(sourceNumber);
      if (beforeHash !== sha256(rendered)) {
        throw new Error(
          `Visible source slide ${sourceNumber} changed at output position ${index + 1}`,
        );
      }
    }
  }

  const notesSnapshot = await reopened.inspect({ kind: "notes", maxChars: 2000000 });
  const insertedNotes = notesSnapshot.ndjson
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .find((record) => record.kind === "notes" && record.slide === 6)?.text;
  if (!insertedNotes?.includes("1,136 genes")) {
    throw new Error("Inserted slide notes did not survive export");
  }

  console.log(
    JSON.stringify(
      {
        source: args.source,
        sourceSha256,
        output: args.output,
        outputSha256: sha256(await fs.readFile(args.output)),
        slideCount: finalSlides.length,
        insertedSlide: 6,
        allExistingSlideVisualsPreserved: true,
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
