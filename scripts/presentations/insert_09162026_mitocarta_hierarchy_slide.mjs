#!/usr/bin/env node

/**
 * Insert a MitoCarta hierarchy explainer before the pathway-method slide.
 *
 * The source deck remains unchanged. The script writes a validated revision to
 * a separate PPTX so an open PowerPoint file cannot lose unsaved edits.
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
  "results/presentations/09162026_mitocarta_hierarchy/build",
);
const DEFAULT_OUTPUT = path.join(
  WORKSPACE_DIR,
  "docs/presentations/09162026/09162026_sex_apoe_kda_fine_broad_mitocarta_levels.pptx",
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
  paleBlue: "#EBF7FC",
  blue: "#0072B2",
  paleGreen: "#E4F4EE",
  green: "#00684D",
  paleGold: "#FFF3D6",
  gold: "#9A6200",
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

function addHierarchyBand(
  slide,
  { name, top, left, width, fill, accent, level, label, example, count },
) {
  slide.shapes.add({
    geometry: "roundRect",
    name: `${name}-band`,
    position: { left, top, width, height: 104 },
    fill,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 14,
    shadow: "shadow-sm",
  });
  addText(
    slide,
    `${name}-level`,
    `LEVEL ${level}`,
    { left: left + 28, top: top + 19, width: 126, height: 24 },
    { fontSize: 15, bold: true, color: accent, verticalAlignment: "middle" },
  );
  addText(
    slide,
    `${name}-label`,
    label,
    { left: left + 28, top: top + 51, width: width * 0.43, height: 32 },
    { fontSize: 23, bold: true, color: COLORS.navy, verticalAlignment: "middle" },
  );
  addText(
    slide,
    `${name}-example`,
    example,
    { left: left + width * 0.48, top: top + 36, width: width * 0.27, height: 49 },
    { fontSize: 18, color: COLORS.dark, verticalAlignment: "middle" },
  );
  addText(
    slide,
    `${name}-count`,
    count,
    { left: left + width - 180, top: top + 29, width: 150, height: 48 },
    {
      fontSize: 23,
      bold: true,
      color: accent,
      alignment: "right",
      verticalAlignment: "middle",
    },
  );
}

function buildHierarchySlide(slide) {
  const background = slide.shapes.add({
    geometry: "rect",
    name: "mitocarta-hierarchy-background",
    position: { left: 0, top: 0, width: 1280, height: 720 },
    fill: COLORS.background,
    line: { style: "solid", fill: "none", width: 0 },
  });
  background.sendToBack();

  addText(
    slide,
    "mitocarta-hierarchy-title",
    "Three levels of MitoCarta pathways",
    { left: 56, top: 43, width: 1120, height: 50 },
    { fontSize: 33, bold: true, color: COLORS.navy, verticalAlignment: "middle" },
  );
  addText(
    slide,
    "mitocarta-hierarchy-subtitle",
    "MitoCarta groups mitochondrial genes into nested pathways, from broad systems to detailed subpathways.",
    { left: 58, top: 96, width: 1110, height: 38 },
    { fontSize: 20, color: COLORS.gray, verticalAlignment: "middle" },
  );

  addHierarchyBand(slide, {
    name: "mitocarta-level-1",
    top: 162,
    left: 90,
    width: 1100,
    fill: COLORS.paleBlue,
    accent: COLORS.blue,
    level: 1,
    label: "Broad mitochondrial system",
    example: "Example: Oxidative phosphorylation (OXPHOS)",
    count: "7 pathways",
  });
  addHierarchyBand(slide, {
    name: "mitocarta-level-2",
    top: 284,
    left: 170,
    width: 940,
    fill: COLORS.paleGreen,
    accent: COLORS.green,
    level: 2,
    label: "Pathway within a system",
    example: "Example: Complex I",
    count: "39 pathways",
  });
  addHierarchyBand(slide, {
    name: "mitocarta-level-3",
    top: 406,
    left: 250,
    width: 780,
    fill: COLORS.paleGold,
    accent: COLORS.gold,
    level: 3,
    label: "Detailed subpathway",
    example: "Example: Complex I subunits",
    count: "103 pathways",
  });

  addText(
    slide,
    "mitocarta-hierarchy-summary",
    "Levels 1 and 2 contain 46 pathways. Including Level 3 gives 149 pathways in total.",
    { left: 130, top: 563, width: 1020, height: 46 },
    {
      fontSize: 23,
      bold: true,
      color: COLORS.navy,
      alignment: "center",
      verticalAlignment: "middle",
    },
  );
  addText(
    slide,
    "mitocarta-hierarchy-note",
    "The same gene may belong to a broad pathway and one or more nested pathways.",
    { left: 180, top: 621, width: 920, height: 32 },
    {
      fontSize: 17,
      color: COLORS.gray,
      alignment: "center",
      verticalAlignment: "middle",
    },
  );

  slide.speakerNotes.textFrame.setText(
    structuredNotes({
      goal: "Define the three MitoCarta pathway levels used in the analysis.",
      walkthrough:
        "MitoCarta organizes mitochondrial genes into a nested hierarchy. Level 1 contains seven broad mitochondrial systems. Level 2 contains 39 pathways within those systems. Level 3 adds 103 more detailed subpathways. For example, oxidative phosphorylation is a Level 1 system, Complex I is a Level 2 pathway within it, and Complex I subunits form a Level 3 pathway. Levels 1 and 2 therefore contain 46 pathways, while the complete hierarchy contains 149.",
      boundary:
        "The levels describe biological specificity, not statistical strength. Because the hierarchy is nested, broad and detailed pathways can share genes and can produce related enrichment results. Counts come from the Phase 11 MitoCarta pathway manifest in results/minerva_production/11_pathway_deg_fine.",
      transition: "Next, explain how each fine-cell DEG list was tested against these pathway definitions.",
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
  const presentation = await PresentationFile.importPptx(await FileBlob.load(args.source));
  const sourceSlides = slidesFromPresentation(presentation);
  if (sourceSlides.length !== EXPECTED_SOURCE_SLIDES) {
    throw new Error(
      `Expected ${EXPECTED_SOURCE_SLIDES} source slides, found ${sourceSlides.length}`,
    );
  }

  const before = await presentation.inspect({
    kind: "slide,textbox,shape,notes,layout",
    search: "Pathway analysis|How the pathway analysis was done|Four mitochondrial pathways highlighted",
    maxChars: 18000,
  });
  await fs.writeFile(path.join(args.build, "before.ndjson"), before.ndjson || "", "utf8");
  for (const slideNumber of [5, 6, 7]) {
    await saveBlob(
      await presentation.export({
        slide: sourceSlides[slideNumber - 1],
        format: "png",
        scale: 1,
      }),
      path.join(args.build, `before-slide-${String(slideNumber).padStart(2, "0")}.png`),
    );
  }

  sourceSlides[4].speakerNotes.textFrame.setText(
    structuredNotes({
      goal: "Position pathway analysis between DEG testing and network analysis.",
      walkthrough:
        "Pathway analysis asks whether mitochondrial DEG results are concentrated in predefined pathways, including mitochondrial and nuclear OXPHOS, mitochondrial translation, and MICOS or inner-membrane organization. It therefore describes pathway-level signal before network-based driver nomination.",
      boundary:
        "Pathway enrichment describes the composition or ranking of gene-level results. It does not identify an upstream driver or prove that a pathway is more or less functional.",
      transition: "Introduce the three-level MitoCarta hierarchy used to define the pathway sets.",
    }),
  );

  const subtitleInspect = await presentation.inspect({
    kind: "textbox",
    search: "MitoCarta is a curated catalog of mitochondrial genes and pathways",
    maxChars: 5000,
  });
  const subtitleRecord = (subtitleInspect.ndjson || "")
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .find((record) => record.kind === "textbox" && record.slide === 6);
  if (!subtitleRecord?.id || !subtitleRecord?.text) {
    throw new Error("Could not locate the existing slide 6 subtitle");
  }
  const subtitleShape = presentation.resolve(subtitleRecord.id);
  subtitleShape.text =
    "Each fine-cell sex/APOE contrast was tested separately against these pathway definitions.";
  subtitleShape.text.style = {
    typeface: FONT_FAMILY,
    fontSize: 21.33,
    color: COLORS.gray,
    alignment: "left",
    verticalAlignment: "top",
    autoFit: "shrinkText",
    wrap: "square",
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
  };

  presentation.slides.insert({
    after: sourceSlides[4],
    layoutId: "/ppt/slideLayouts/slideLayout7.xml",
  });
  const hierarchySlide = presentation.slides.getItem(5);
  buildHierarchySlide(hierarchySlide);

  const finalSlides = slidesFromPresentation(presentation);
  if (finalSlides.length !== EXPECTED_OUTPUT_SLIDES) {
    throw new Error(
      `Expected ${EXPECTED_OUTPUT_SLIDES} output slides, found ${finalSlides.length}`,
    );
  }

  const after = await presentation.inspect({
    kind: "slide,textbox,shape,notes,layout",
    search: "Three levels of MitoCarta pathways|Each fine-cell sex/APOE contrast|Four mitochondrial pathways highlighted",
    maxChars: 22000,
  });
  await fs.writeFile(path.join(args.build, "after.ndjson"), after.ndjson || "", "utf8");
  for (const slideNumber of [5, 6, 7, 8]) {
    await saveBlob(
      await presentation.export({
        slide: finalSlides[slideNumber - 1],
        format: "png",
        scale: 1,
      }),
      path.join(args.build, `after-slide-${String(slideNumber).padStart(2, "0")}.png`),
    );
  }
  await saveBlob(
    await hierarchySlide.export({ format: "layout" }),
    path.join(args.build, "after-slide-06.layout.json"),
  );
  await saveBlob(
    await presentation.export({ format: "webp", montage: true, scale: 0.28 }),
    path.join(args.build, "after-montage.webp"),
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
        insertedSlide: 6,
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
