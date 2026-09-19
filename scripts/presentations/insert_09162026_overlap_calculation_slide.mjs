#!/usr/bin/env node

/**
 * Insert a slide before the pathway-overlap heatmap explaining its calculation.
 *
 * The source deck remains unchanged. The script writes a validated PPTX to the
 * requested output path and stores previews and validation records under the
 * requested build directory.
 */

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
  "results/presentations/09162026_overlap_insert/formula_build",
);
const DEFAULT_OUTPUT = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_overlap_insert/output/09162026_sex_apoe_kda_fine_broad_overlap_formula.pptx",
);
const EXPECTED_OUTPUT_SLIDES = 160;
const EXPECTED_SLIDE_SIZE_EMU = "12192000,6858000";
const FONT_FAMILY = "Arial";

const COLORS = {
  background: "#F7F9FC",
  navy: "#0F233D",
  dark: "#1F2730",
  gray: "#4E5A68",
  paleBlue: "#EBF7FC",
  blue: "#0072B2",
  paleGreen: "#E4F4EE",
  green: "#00684D",
  paleRed: "#FDEBE4",
  vermilion: "#9E3A00",
  paleGray: "#F1F4F7",
  purple: "#7E4C9A",
  line: "#D8E2EC",
  white: "#FFFFFF",
};

function parseArgs(argv) {
  const result = {
    source: DEFAULT_SOURCE,
    build: DEFAULT_BUILD,
    output: DEFAULT_OUTPUT,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    const value = argv[i + 1];
    if (key === "--source" || key === "--build" || key === "--output") {
      if (!value) throw new Error(`Missing value after ${key}`);
      result[key.slice(2)] = path.resolve(value);
      i += 1;
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

async function saveBlob(blob, outputPath) {
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, Buffer.from(await blob.arrayBuffer()));
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

function addCard(slide, name, position, fill, accent, step, title, body) {
  slide.shapes.add({
    geometry: "roundRect",
    name: `${name}-surface`,
    position,
    fill,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 18,
    shadow: "shadow-sm",
  });
  addText(
    slide,
    `${name}-step`,
    `STEP ${step}`,
    { left: position.left + 28, top: position.top + 24, width: 130, height: 22 },
    { fontSize: 15, bold: true, color: accent },
  );
  addText(
    slide,
    `${name}-title`,
    title,
    { left: position.left + 28, top: position.top + 58, width: position.width - 56, height: 52 },
    { fontSize: 23, bold: true, color: COLORS.navy, verticalAlignment: "middle" },
  );
  addText(
    slide,
    `${name}-body`,
    body,
    { left: position.left + 28, top: position.top + 124, width: position.width - 56, height: position.height - 150 },
    { fontSize: 17, color: COLORS.dark, verticalAlignment: "top" },
  );
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

function buildCalculationSlide(slide) {
  const background = slide.shapes.add({
    geometry: "rect",
    name: "overlap-calculation-background",
    position: { left: 0, top: 0, width: 1280, height: 720 },
    fill: COLORS.background,
    line: { style: "solid", fill: "none", width: 0 },
  });
  background.sendToBack();

  addText(
    slide,
    "overlap-calculation-title",
    "How to calculate pathway and sex/APOE overlap",
    { left: 56, top: 43, width: 1120, height: 46 },
    { fontSize: 33, bold: true, color: COLORS.navy, verticalAlignment: "middle" },
  );

  addText(
    slide,
    "formula-label",
    "Overlap (%) =",
    { left: 76, top: 228, width: 235, height: 65 },
    { fontSize: 35, bold: true, color: COLORS.navy, alignment: "right", verticalAlignment: "middle" },
  );
  addText(
    slide,
    "formula-numerator",
    "Unique pathway genes that are DEGs in at least one fine cell type\nwithin one sex/APOE group",
    { left: 346, top: 146, width: 690, height: 89 },
    { fontSize: 25, bold: true, color: COLORS.navy, alignment: "center", verticalAlignment: "bottom" },
  );
  slide.shapes.add({
    geometry: "line",
    name: "formula-fraction-line",
    position: { left: 346, top: 254, width: 690, height: 0 },
    fill: "none",
    line: { style: "solid", fill: COLORS.navy, width: 2.5 },
  });
  addText(
    slide,
    "formula-denominator",
    "All genes in the pathway",
    { left: 346, top: 276, width: 690, height: 54 },
    { fontSize: 25, bold: true, color: COLORS.navy, alignment: "center", verticalAlignment: "top" },
  );
  addText(
    slide,
    "formula-multiplier",
    "× 100",
    { left: 1058, top: 228, width: 145, height: 65 },
    { fontSize: 35, bold: true, color: COLORS.navy, alignment: "left", verticalAlignment: "middle" },
  );

  slide.shapes.add({
    geometry: "roundRect",
    name: "overlap-example-band",
    position: { left: 145, top: 410, width: 990, height: 185 },
    fill: COLORS.paleGreen,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 16,
    shadow: "shadow-sm",
  });
  addText(
    slide,
    "worked-example-label",
    "Example: male ε2 mitochondrial translation",
    { left: 195, top: 443, width: 890, height: 34 },
    { fontSize: 20, bold: true, color: COLORS.green, alignment: "center" },
  );
  addText(
    slide,
    "worked-example-text",
    "130 unique DEG genes  ÷  155 pathway genes  ×  100  =  84%",
    { left: 195, top: 497, width: 890, height: 55 },
    { fontSize: 31, bold: true, color: COLORS.navy, alignment: "center", verticalAlignment: "middle" },
  );

  slide.speakerNotes.textFrame.setText(
    structuredNotes({
      goal: "Explain the overlap formula and its worked example.",
      walkthrough:
        "This percentage summarizes one pathway within one sex/APOE group. The numerator is the number of unique pathway genes that were significant DEGs in at least one fine-cell comparison in that group. The denominator is the total number of genes in the pathway. Multiplying by 100 converts the ratio to a percentage. In the male epsilon-2 mitochondrial-translation example, 130 of the 155 pathway genes appeared as DEGs. Therefore, 130 divided by 155 times 100 equals 84 percent.",
      boundary:
        "Each gene counts once, regardless of how many fine cell types contain it. The percentage does not show the percentage of fine cell types, the direction of change, recurrence across cell types, or pathway enrichment.",
      transition: "Now inspect the calculated pathway-gene coverage across the six sex/APOE groups.",
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
  const outputStat = await fs.stat(args.output).catch(() => undefined);
  if (outputStat) throw new Error(`Output already exists: ${args.output}`);

  await fs.mkdir(args.build, { recursive: true });
  await fs.mkdir(path.dirname(args.output), { recursive: true });

  const { importRuntimeModule } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href
  );
  const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");
  const presentation = await PresentationFile.importPptx(await FileBlob.load(args.source));
  const sourceSlides = slidesFromPresentation(presentation);
  if (![159, 160].includes(sourceSlides.length)) {
    throw new Error(`Expected 159 or 160 source slides, found ${sourceSlides.length}`);
  }

  const before = await presentation.inspect({
    kind: "slide,textbox,shape,notes,layout",
    search: "Four mitochondrial pathways highlighted|Which pathway genes appeared among the DEGs",
    maxChars: 12000,
  });
  await fs.writeFile(path.join(args.build, "before.ndjson"), before.ndjson || "", "utf8");
  await saveBlob(
    await presentation.export({ slide: sourceSlides[6], format: "png", scale: 1 }),
    path.join(args.build, "before-slide-07.png"),
  );
  await saveBlob(
    await presentation.export({ slide: sourceSlides[7], format: "png", scale: 1 }),
    path.join(args.build, "before-slide-08.png"),
  );

  sourceSlides[6].speakerNotes.textFrame.setText(
    structuredNotes({
      goal: "Introduce the four mitochondrial pathways highlighted in the focused results.",
      walkthrough:
        "The focused analysis highlights four fixed pathway definitions, using the same gene membership in every contrast. The first contains the 13 OXPHOS subunits encoded by mitochondrial DNA. The second contains 86 structural OXPHOS subunits encoded by nuclear DNA. The third contains 155 genes involved in translating proteins inside mitochondria. The fourth contains 19 MIB/MICOS genes that organize the inner mitochondrial membrane and its folds, called cristae.",
      boundary:
        "These are focused benchmark pathways, not the full pathway search. Phase 11 also tested 46 Level 1 and Level 2 MitoCarta pathway categories and all 149 MitoCarta pathways. Listing a pathway, or observing some of its genes among the DEGs, does not establish enrichment or altered function.",
      transition: "Next, explain how fine-cell DEG results are pooled into each overlap value.",
    }),
  );

  let calculationSlide;
  if (sourceSlides.length === 159) {
    presentation.slides.insert({
      after: sourceSlides[6],
      layoutId: "/ppt/slideLayouts/slideLayout7.xml",
    });
    calculationSlide = presentation.slides.getItem(7);
  } else {
    calculationSlide = sourceSlides[7];
    calculationSlide.shapes.deleteAll();
  }
  buildCalculationSlide(calculationSlide);

  const finalSlides = slidesFromPresentation(presentation);
  if (finalSlides.length !== EXPECTED_OUTPUT_SLIDES) {
    throw new Error(
      `Expected ${EXPECTED_OUTPUT_SLIDES} output slides, found ${finalSlides.length}`,
    );
  }

  const after = await presentation.inspect({
    kind: "slide,textbox,shape,notes,layout",
    search: "How pathway-gene overlap was calculated|130 unique DEG genes",
    maxChars: 16000,
  });
  await fs.writeFile(path.join(args.build, "after.ndjson"), after.ndjson || "", "utf8");
  await saveBlob(
    await presentation.export({ slide: finalSlides[6], format: "png", scale: 1 }),
    path.join(args.build, "after-slide-07.png"),
  );
  await saveBlob(
    await presentation.export({ slide: finalSlides[7], format: "png", scale: 1 }),
    path.join(args.build, "after-slide-08.png"),
  );
  await saveBlob(
    await presentation.export({ slide: finalSlides[8], format: "png", scale: 1 }),
    path.join(args.build, "after-slide-09.png"),
  );
  await saveBlob(
    await presentation.export({ format: "webp", montage: true, scale: 0.35 }),
    path.join(args.build, "after-montage.webp"),
  );
  await saveBlob(
    await finalSlides[7].export({ format: "layout" }),
    path.join(args.build, "after-slide-08.layout.json"),
  );

  const sourceBytes = await fs.readFile(args.source);
  const sourceSha256 = crypto.createHash("sha256").update(sourceBytes).digest("hex");
  const candidatePath = path.join(args.build, "candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const result = await finalizePresentation({
    explicitTotalSlideCount: EXPECTED_OUTPUT_SLIDES,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [],
    workspaceDir: WORKSPACE_DIR,
    candidatePath,
    finalPath: args.output,
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
    receiptPath: path.join(args.build, `${path.basename(args.output)}.validation.json`),
  });

  console.log(
    JSON.stringify(
      {
        source: args.source,
        output: args.output,
        slideCount: EXPECTED_OUTPUT_SLIDES,
        insertedSlide: 8,
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
