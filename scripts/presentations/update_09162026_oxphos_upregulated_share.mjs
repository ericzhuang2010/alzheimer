#!/usr/bin/env node

/**
 * Reframe slides 11 and 12 around the percentage of OXPHOS DEG occurrences
 * that are upregulated. The chart uses 50% as the equal up/down reference.
 */

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
  "results/presentations/09162026_oxphos_upregulated_share/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_oxphos_upregulated_share/output/09162026_sex_apoe_kda_fine_broad_upregulated_share_v2.pptx",
);
const EXPECTED_SLIDES = 162;
const EXPECTED_SLIDE_SIZE_EMU = "12192000,6858000";
const FONT_FAMILY = "Arial";

const COLORS = {
  background: "#F7F9FC",
  white: "#FFFFFF",
  navy: "#0F233D",
  dark: "#1F2730",
  gray: "#4E5A68",
  line: "#D8E2EC",
  paleBlue: "#EBF7FC",
  blue: "#0072B2",
  paleGreen: "#E4F4EE",
  green: "#00684D",
  paleGray: "#F1F4F7",
  purple: "#7E4C9A",
  orange: "#D55E00",
};

const GROUPS = [
  "Female ε2",
  "Female ε3/ε3",
  "Female ε4",
  "Male ε2",
  "Male ε3/ε3",
  "Male ε4",
];

const COUNTS = {
  mitochondrial: [
    [127, 1],
    [217, 0],
    [26, 38],
    [13, 119],
    [70, 11],
    [87, 23],
  ],
  nuclear: [
    [239, 4],
    [76, 13],
    [10, 206],
    [63, 404],
    [8, 60],
    [34, 55],
  ],
};

function upPercentages(countPairs) {
  return countPairs.map(([up, down]) => Math.round((100 * up) / (up + down)));
}

const MITO_UP_PERCENTAGES = upPercentages(COUNTS.mitochondrial);
const NUCLEAR_UP_PERCENTAGES = upPercentages(COUNTS.nuclear);

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

async function saveBlob(blob, outputPath) {
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, await blobBuffer(blob));
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

function addCoveringBackground(slide, name) {
  return slide.shapes.add({
    geometry: "rect",
    name,
    position: { left: 0, top: 0, width: 1280, height: 720 },
    fill: COLORS.background,
    line: { style: "solid", fill: "none", width: 0 },
  });
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

function buildSlide11(slide) {
  addCoveringBackground(slide, "up-share-formula-background");

  addText(
    slide,
    "up-share-formula-title",
    "How the upregulated occurrence percentage is calculated",
    { left: 56, top: 43, width: 1120, height: 50 },
    { fontSize: 33, bold: true, color: COLORS.navy, verticalAlignment: "middle" },
  );
  addText(
    slide,
    "up-share-formula-subtitle",
    "Calculated separately for each sex/APOE group and each OXPHOS gene set.",
    { left: 58, top: 97, width: 1110, height: 34 },
    { fontSize: 20, color: COLORS.gray, verticalAlignment: "middle" },
  );

  slide.shapes.add({
    geometry: "roundRect",
    name: "up-share-formula-surface",
    position: { left: 105, top: 158, width: 1070, height: 198 },
    fill: COLORS.paleBlue,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 16,
    shadow: "shadow-sm",
  });
  addText(
    slide,
    "up-share-formula-label",
    "Upregulated occurrence % =",
    { left: 120, top: 224, width: 350, height: 54 },
    {
      fontSize: 25,
      bold: true,
      color: COLORS.navy,
      alignment: "right",
      verticalAlignment: "middle",
    },
  );
  addText(
    slide,
    "up-share-formula-numerator",
    "upregulated occurrences",
    { left: 500, top: 188, width: 500, height: 50 },
    {
      fontSize: 23,
      bold: true,
      color: COLORS.navy,
      alignment: "center",
      verticalAlignment: "bottom",
    },
  );
  slide.shapes.add({
    geometry: "line",
    name: "up-share-formula-fraction-line",
    position: { left: 485, top: 252, width: 530, height: 0 },
    fill: "none",
    line: { style: "solid", fill: COLORS.navy, width: 2.5 },
  });
  addText(
    slide,
    "up-share-formula-denominator",
    "upregulated occurrences + downregulated occurrences",
    { left: 475, top: 267, width: 550, height: 50 },
    {
      fontSize: 21,
      bold: true,
      color: COLORS.navy,
      alignment: "center",
      verticalAlignment: "top",
    },
  );
  addText(
    slide,
    "up-share-formula-times-100",
    "× 100",
    { left: 1040, top: 224, width: 100, height: 54 },
    {
      fontSize: 28,
      bold: true,
      color: COLORS.navy,
      verticalAlignment: "middle",
    },
  );

  addText(
    slide,
    "up-share-occurrence-definition",
    "1 occurrence = 1 significant pathway gene in 1 fine-cell comparison. The same gene may count again in another fine cell type.",
    { left: 120, top: 378, width: 1040, height: 44 },
    {
      fontSize: 18,
      color: COLORS.gray,
      alignment: "center",
      verticalAlignment: "middle",
    },
  );

  slide.shapes.add({
    geometry: "roundRect",
    name: "up-share-example-surface",
    position: { left: 160, top: 444, width: 960, height: 130 },
    fill: COLORS.paleGreen,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 16,
    shadow: "shadow-sm",
  });
  addText(
    slide,
    "up-share-example-label",
    "Example: male ε3/ε3, mtDNA-encoded OXPHOS",
    { left: 205, top: 465, width: 870, height: 30 },
    { fontSize: 18, bold: true, color: COLORS.green, alignment: "center" },
  );
  addText(
    slide,
    "up-share-example-calculation",
    "70 up ÷ (70 up + 11 down) × 100 = 86% upregulated",
    { left: 205, top: 508, width: 870, height: 40 },
    {
      fontSize: 26,
      bold: true,
      color: COLORS.navy,
      alignment: "center",
      verticalAlignment: "middle",
    },
  );

  slide.shapes.add({
    geometry: "roundRect",
    name: "up-share-reading-surface",
    position: { left: 105, top: 608, width: 1070, height: 62 },
    fill: COLORS.paleGray,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 12,
  });
  addText(
    slide,
    "up-share-reading-label",
    "Reading the chart",
    { left: 134, top: 625, width: 175, height: 27 },
    { fontSize: 16, bold: true, color: COLORS.purple, verticalAlignment: "middle" },
  );
  addText(
    slide,
    "up-share-reading-text",
    "50% means equal upregulated and downregulated occurrences. Above 50% favors upregulation; below 50% favors downregulation.",
    { left: 315, top: 617, width: 830, height: 43 },
    { fontSize: 16, color: COLORS.dark, verticalAlignment: "middle" },
  );

  slide.speakerNotes.textFrame.setText(
    structuredNotes({
      goal:
        "Define an occurrence and show how the upregulated OXPHOS occurrence percentage is calculated.",
      walkthrough:
        "Begin with the counting unit highlighted on the slide. One occurrence means that one pathway gene is a significant DEG in one fine-cell comparison. If the same gene is significant in another fine cell type, it contributes another occurrence. The calculation is performed separately for each sex/APOE group and each OXPHOS gene set. Divide the upregulated occurrences by all upregulated plus downregulated occurrences, then multiply by 100. In the male epsilon-3 homozygous mtDNA-encoded OXPHOS example, 70 occurrences were upregulated and 11 were downregulated. Seventy divided by 81 equals 86 percent upregulated. A value of 50 percent means the two directions occur equally often. Values above 50 percent favor upregulation, while values below 50 percent favor downregulation.",
      boundary:
        "This occurrence-based summary gives more weight to genes that recur across fine-cell comparisons. It is not a fold change, the percentage of unique genes, cells, donors, or fine cell types, an enrichment result, or a measure of OXPHOS activity. Repeated occurrences are not independent biological replications.",
      transition: "Compare the upregulated occurrence percentage across the six sex/APOE groups.",
    }),
  );
  slide.speakerNotes.setVisible(true);
}

function percentageLabelOverrides(values, color) {
  return values.map((value, idx) => ({
      idx,
      text: `${value}%`,
      position: value < 20 ? "outEnd" : "inEnd",
      showValue: false,
      textStyle: {
        typeface: FONT_FAMILY,
        fontSize: 15,
        bold: true,
        fill: value < 20 ? color : COLORS.white,
      },
    }));
}

function buildSlide12(slide, applyPresentationChartFont) {
  addCoveringBackground(slide, "up-share-chart-background");

  addText(
    slide,
    "up-share-chart-title",
    "Share of OXPHOS DEG occurrences that are upregulated",
    { left: 58, top: 45, width: 1130, height: 46 },
    { fontSize: 30, bold: true, color: COLORS.navy, verticalAlignment: "middle" },
  );
  addText(
    slide,
    "up-share-chart-subtitle",
    "OXPHOS (oxidative phosphorylation) is the mitochondrial process that makes most cellular ATP.",
    { left: 122, top: 120, width: 1040, height: 38 },
    { fontSize: 24, color: COLORS.gray, alignment: "center", verticalAlignment: "middle" },
  );
  addText(
    slide,
    "up-share-chart-reference",
    "50% = equal numbers of upregulated and downregulated occurrences",
    { left: 75, top: 166, width: 1130, height: 24 },
    { fontSize: 15, bold: true, color: COLORS.purple, alignment: "center" },
  );

  const chart = slide.charts.add("bar", {
    position: { left: 75, top: 188, width: 1130, height: 355 },
    categories: GROUPS,
    series: [
      {
        name: "13 OXPHOS genes encoded by mitochondrial DNA",
        values: MITO_UP_PERCENTAGES,
        valuesFormatCode: '0"%"',
        fill: COLORS.blue,
        line: { style: "solid", fill: COLORS.blue, width: 1 },
        dataLabelOverrides: percentageLabelOverrides(MITO_UP_PERCENTAGES, COLORS.blue),
      },
      {
        name: "86 structural OXPHOS genes encoded by nuclear DNA",
        values: NUCLEAR_UP_PERCENTAGES,
        valuesFormatCode: '0"%"',
        fill: COLORS.orange,
        line: { style: "solid", fill: COLORS.orange, width: 1 },
        dataLabelOverrides: percentageLabelOverrides(NUCLEAR_UP_PERCENTAGES, COLORS.orange),
      },
    ],
    barOptions: {
      direction: "column",
      grouping: "clustered",
      gapWidth: 55,
      overlap: 0,
    },
    hasLegend: true,
    legend: {
      position: "top",
      overlay: false,
      textStyle: { typeface: FONT_FAMILY, fontSize: 14, fill: COLORS.dark },
    },
    xAxis: {
      visible: true,
      textStyle: { typeface: FONT_FAMILY, fontSize: 15, bold: true, fill: COLORS.dark },
      line: { style: "solid", fill: "#667788", width: 1 },
      majorGridlines: null,
    },
    yAxis: {
      visible: true,
      title: {
        text: "Upregulated occurrences among all OXPHOS DEG occurrences",
        textStyle: { typeface: FONT_FAMILY, fontSize: 14, fill: COLORS.dark },
      },
      min: 0,
      max: 100,
      majorUnit: 25,
      numberFormatCode: '0"%"',
      textStyle: { typeface: FONT_FAMILY, fontSize: 13, fill: COLORS.dark },
      line: { style: "solid", fill: "#667788", width: 1 },
      majorGridlines: { style: "solid", fill: "#D5DDE6", width: 1 },
    },
    dataLabels: {
      showValue: true,
      position: "inEnd",
      textStyle: {
        typeface: FONT_FAMILY,
        fontSize: 15,
        bold: true,
        fill: COLORS.white,
      },
    },
    chartFill: COLORS.white,
    chartLine: { style: "solid", fill: "none", width: 0 },
    plotAreaFill: COLORS.white,
    plotAreaLine: { style: "solid", fill: "none", width: 0 },
  });
  applyPresentationChartFont(chart, { fontFamily: FONT_FAMILY });

  slide.shapes.add({
    geometry: "roundRect",
    name: "up-share-key-contrast-surface",
    position: { left: 68, top: 592, width: 1144, height: 69 },
    fill: COLORS.paleGray,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 12,
    shadow: "shadow-sm",
  });
  addText(
    slide,
    "up-share-key-contrast-label",
    "Key contrast",
    { left: 100, top: 616, width: 120, height: 25 },
    { fontSize: 16, bold: true, color: COLORS.purple, verticalAlignment: "middle" },
  );
  addText(
    slide,
    "up-share-key-contrast-text",
    "Female ε3/ε3: both OXPHOS sets mostly rise. Male ε3/ε3: mitochondrial-encoded genes rise while nuclear-encoded genes fall.",
    { left: 228, top: 605, width: 940, height: 47 },
    { fontSize: 18, color: COLORS.dark, verticalAlignment: "middle" },
  );

  slide.speakerNotes.textFrame.setText(
    structuredNotes({
      goal:
        "Compare the share of upregulated OXPHOS DEG occurrences with 50 percent as the equal-direction baseline.",
      walkthrough:
        "OXPHOS, or oxidative phosphorylation, is the mitochondrial process that produces most cellular ATP. Blue bars summarize the 13 OXPHOS genes encoded by mitochondrial DNA, and orange bars summarize 86 structural OXPHOS genes encoded by nuclear DNA. Every bar starts at the 50 percent line, where upregulated and downregulated occurrences are equally common. Bars extend upward when more than half of the occurrences are upregulated and downward when fewer than half are upregulated. The label at the end of each bar gives the actual upregulated percentage, while bar length shows its percentage-point distance from 50 percent. Female epsilon-2 is 99 percent mitochondrial and 98 percent nuclear upregulated. Female epsilon-3 homozygous is 100 percent mitochondrial and 85 percent nuclear upregulated. Female epsilon-4 is 41 percent mitochondrial and 5 percent nuclear upregulated. Male epsilon-2 is 10 percent mitochondrial and 13 percent nuclear upregulated. Male epsilon-3 homozygous shows the clearest split, at 86 percent mitochondrial and 12 percent nuclear upregulated. Male epsilon-4 shows the same split more weakly, at 79 percent mitochondrial and 38 percent nuclear upregulated.",
      boundary:
        "The bars show the share of repeated gene-by-fine-cell DEG occurrences that are upregulated. The vertical displacement from 50 percent is a descriptive percentage-point difference, not an effect size. The chart does not show percent expression change, percent of cells or donors, percent of unique genes, pathway enrichment, OXPHOS activity, or a direct statistical interaction between disease, sex, and APOE.",
      transition: "Focus first on the female epsilon-3 homozygous mitochondrial increase.",
    }),
  );
  slide.speakerNotes.setVisible(true);
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
  const { applyPresentationChartFont, finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );

  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const slides = slidesFromPresentation(presentation);
  if (slides.length !== EXPECTED_SLIDES) {
    throw new Error(`Expected ${EXPECTED_SLIDES} slides, found ${slides.length}`);
  }

  const titleCheck = await presentation.inspect({
    kind: "slide,textbox,notes,chart,layout",
    search:
      "How the OXPHOS direction percentage is calculated|OXPHOS gene directions vary across sex/APOE groups",
    maxChars: 20000,
  });
  if (!titleCheck.ndjson?.includes('"slide":11')) {
    throw new Error("Could not verify the source slide 11 title");
  }
  if (!titleCheck.ndjson?.includes('"slide":12')) {
    throw new Error("Could not verify the source slide 12 title");
  }
  await fs.writeFile(path.join(BUILD_DIR, "before.ndjson"), titleCheck.ndjson || "", "utf8");
  await saveBlob(
    await presentation.export({ slide: slides[10], format: "png", scale: 1 }),
    path.join(BUILD_DIR, "slide-11-before.png"),
  );
  await saveBlob(
    await presentation.export({ slide: slides[11], format: "png", scale: 1 }),
    path.join(BUILD_DIR, "slide-12-before.png"),
  );

  buildSlide11(slides[10]);
  buildSlide12(slides[11], applyPresentationChartFont);

  await saveBlob(
    await presentation.export({ slide: slides[10], format: "png", scale: 1 }),
    path.join(BUILD_DIR, "slide-11-after.png"),
  );
  await saveBlob(
    await presentation.export({ slide: slides[11], format: "png", scale: 1 }),
    path.join(BUILD_DIR, "slide-12-after.png"),
  );
  await saveBlob(
    await presentation.export({ format: "webp", montage: true, scale: 0.22 }),
    path.join(BUILD_DIR, "after-montage.webp"),
  );

  const after = await presentation.inspect({
    kind: "slide,textbox,notes,chart,layout",
    search:
      "How the upregulated occurrence percentage is calculated|Share of OXPHOS DEG occurrences that are upregulated|50% means equal",
    maxChars: 26000,
  });
  await fs.writeFile(path.join(BUILD_DIR, "after.ndjson"), after.ndjson || "", "utf8");

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await (await PresentationFile.exportPptx(presentation, {
    materializeLiteralChartWorkbooks: true,
  })).save(candidatePath);
  const sourceBuffer = await fs.readFile(SOURCE);

  const result = await finalizePresentation({
    explicitTotalSlideCount: EXPECTED_SLIDES,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [12],
    materializeLiteralChartWorkbooks: true,
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
      EXPECTED_SLIDE_SIZE_EMU,
      "--validate-bullet-geometry",
      "--validate-heading-fit",
    ],
    fontPolicy: {
      basis: "reference",
      families: [FONT_FAMILY],
      referencePath: SOURCE,
      referenceSha256: sha256(sourceBuffer),
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(
      BUILD_DIR,
      "09162026_sex_apoe_kda_fine_broad_upregulated_share_v2.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  if (reopenedSlides.length !== EXPECTED_SLIDES) {
    throw new Error("Finalized deck has the wrong slide count");
  }
  const finalCheck = await reopened.inspect({
    kind: "slide,textbox,notes,chart",
    search:
      "How the upregulated occurrence percentage is calculated|Share of OXPHOS DEG occurrences that are upregulated|Fifty percent means",
    maxChars: 26000,
  });
  await fs.writeFile(path.join(BUILD_DIR, "final.ndjson"), finalCheck.ndjson || "", "utf8");
  await saveBlob(
    await reopened.export({ slide: reopenedSlides[10], format: "png", scale: 1 }),
    path.join(BUILD_DIR, "slide-11-final.png"),
  );
  await saveBlob(
    await reopened.export({ slide: reopenedSlides[11], format: "png", scale: 1 }),
    path.join(BUILD_DIR, "slide-12-final.png"),
  );

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        output: FINAL_PPTX,
        slideCount: EXPECTED_SLIDES,
        updatedSlides: [11, 12],
        chartValues: {
          mitochondrial: MITO_UP_PERCENTAGES,
          nuclear: NUCLEAR_UP_PERCENTAGES,
        },
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
