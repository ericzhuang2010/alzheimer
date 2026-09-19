#!/usr/bin/env node

/**
 * Insert an OXPHOS dominant-direction formula slide before the direction chart.
 * Also synchronize the previously revised slide 7 narration.
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
  "results/presentations/09162026_oxphos_direction_formula/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_oxphos_direction_formula/output/09162026_sex_apoe_kda_fine_broad_direction_formula.pptx",
);
const EXPECTED_SOURCE_SLIDES = 161;
const EXPECTED_OUTPUT_SLIDES = 162;
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
  paleGray: "#F1F4F7",
  purple: "#7E4C9A",
};

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

function revisedSlide7Notes() {
  return structuredNotes({
    goal: "Explain the two-stage pathway analysis and define a significant result.",
    walkthrough:
      "Each estimable fine-cell sex/APOE contrast was analyzed separately. For each contrast, the analysis created three mitochondrial DEG lists: all significant DEGs, genes up-regulated in AD, and genes down-regulated in AD. It then tested each pathway to ask whether the DEG list contained more pathway genes than expected among genes detectable in the same contrast. A significant result means that the greater-than-expected overlap remained significant after Benjamini-Hochberg correction across the pathways in the same collection for that DEG list, with a false-discovery rate below 5 percent. Twelve of the 46 Level 1 and Level 2 pathways and 18 of the 149 complete pathways had at least one significant result. Most significant results involved overlapping OXPHOS pathways. Non-OXPHOS signals were fewer and more localized.",
    boundary:
      "The complete 149-pathway collection contains the 46 Level 1 and Level 2 pathways, so the two reported scopes overlap. At least one significant result means enrichment in at least one fine-cell, sex/APOE, and DEG direction list. It does not mean significance in every group or prove altered pathway activity.",
    transition: "Focus next on four mitochondrial pathways used repeatedly in the later findings.",
  });
}

function buildFormulaSlide(slide) {
  const background = slide.shapes.add({
    geometry: "rect",
    name: "direction-formula-background",
    position: { left: 0, top: 0, width: 1280, height: 720 },
    fill: COLORS.background,
    line: { style: "solid", fill: "none", width: 0 },
  });
  background.sendToBack();

  addText(
    slide,
    "direction-formula-title",
    "How the OXPHOS direction percentage is calculated",
    { left: 56, top: 43, width: 1120, height: 50 },
    { fontSize: 33, bold: true, color: COLORS.navy, verticalAlignment: "middle" },
  );
  addText(
    slide,
    "direction-formula-subtitle",
    "Calculated separately for each sex/APOE group and each OXPHOS gene set.",
    { left: 58, top: 97, width: 1110, height: 34 },
    { fontSize: 20, color: COLORS.gray, verticalAlignment: "middle" },
  );

  slide.shapes.add({
    geometry: "roundRect",
    name: "direction-formula-surface",
    position: { left: 105, top: 158, width: 1070, height: 198 },
    fill: COLORS.paleBlue,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 16,
    shadow: "shadow-sm",
  });
  addText(
    slide,
    "direction-formula-label",
    "Dominant direction % =",
    { left: 138, top: 224, width: 290, height: 54 },
    {
      fontSize: 28,
      bold: true,
      color: COLORS.navy,
      alignment: "right",
      verticalAlignment: "middle",
    },
  );
  addText(
    slide,
    "direction-formula-numerator",
    "max(upregulated occurrences, downregulated occurrences)",
    { left: 462, top: 183, width: 590, height: 55 },
    {
      fontSize: 22,
      bold: true,
      color: COLORS.navy,
      alignment: "center",
      verticalAlignment: "bottom",
    },
  );
  slide.shapes.add({
    geometry: "line",
    name: "direction-formula-fraction-line",
    position: { left: 470, top: 252, width: 575, height: 0 },
    fill: "none",
    line: { style: "solid", fill: COLORS.navy, width: 2.5 },
  });
  addText(
    slide,
    "direction-formula-denominator",
    "upregulated occurrences + downregulated occurrences",
    { left: 462, top: 267, width: 590, height: 50 },
    {
      fontSize: 22,
      bold: true,
      color: COLORS.navy,
      alignment: "center",
      verticalAlignment: "top",
    },
  );
  addText(
    slide,
    "direction-formula-times-100",
    "× 100",
    { left: 1064, top: 224, width: 96, height: 54 },
    {
      fontSize: 28,
      bold: true,
      color: COLORS.navy,
      alignment: "left",
      verticalAlignment: "middle",
    },
  );

  addText(
    slide,
    "direction-occurrence-definition",
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
    name: "direction-example-surface",
    position: { left: 160, top: 444, width: 960, height: 130 },
    fill: COLORS.paleGreen,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 16,
    shadow: "shadow-sm",
  });
  addText(
    slide,
    "direction-example-label",
    "Example: male ε3/ε3, mtDNA-encoded OXPHOS",
    { left: 205, top: 465, width: 870, height: 30 },
    { fontSize: 18, bold: true, color: COLORS.green, alignment: "center" },
  );
  addText(
    slide,
    "direction-example-calculation",
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
    name: "direction-reading-surface",
    position: { left: 105, top: 608, width: 1070, height: 62 },
    fill: COLORS.paleGray,
    line: { style: "solid", fill: COLORS.line, width: 1 },
    borderRadius: 12,
  });
  addText(
    slide,
    "direction-reading-label",
    "Reading the chart",
    { left: 134, top: 625, width: 175, height: 27 },
    { fontSize: 16, bold: true, color: COLORS.purple, verticalAlignment: "middle" },
  );
  addText(
    slide,
    "direction-reading-text",
    "Positive bars mean upregulated is dominant. Negative bars mean downregulated is dominant. Color identifies the gene set.",
    { left: 315, top: 621, width: 830, height: 35 },
    { fontSize: 17, color: COLORS.dark, verticalAlignment: "middle" },
  );

  slide.speakerNotes.textFrame.setText(
    structuredNotes({
      goal: "Define the OXPHOS dominant-direction percentage before showing the bars.",
      walkthrough:
        "The calculation is performed separately for each sex/APOE group and each OXPHOS gene set. One occurrence means that one pathway gene is a significant DEG in one fine-cell comparison. A gene can therefore contribute again when it is significant in another fine cell type. Count the upregulated and downregulated occurrences, then identify the larger count. The dominant direction percentage equals that larger count divided by the total number of upregulated plus downregulated occurrences, multiplied by 100. For male epsilon-3 homozygous mtDNA-encoded OXPHOS, 70 occurrences increased and 11 decreased. Seventy divided by 81 equals 86 percent, so upregulation is the dominant direction. On the chart, the bar sign shows direction and the color identifies the OXPHOS gene set.",
      boundary:
        "This percentage is not a fold change, the percentage of unique genes, cells, donors, or fine cell types, an enrichment result, or a measure of OXPHOS activity. Repeated occurrences across fine cell types are not independent biological replications.",
      transition: "Apply this percentage across the six sex/APOE groups.",
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
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const sourceSlides = slidesFromPresentation(presentation);
  if (sourceSlides.length !== EXPECTED_SOURCE_SLIDES) {
    throw new Error(
      `Expected ${EXPECTED_SOURCE_SLIDES} source slides, found ${sourceSlides.length}`,
    );
  }

  const before = await presentation.inspect({
    kind: "slide,textbox,shape,notes,layout",
    search: "Which pathway genes appeared among the DEGs|OXPHOS gene directions vary across sex/APOE groups|Female ε3/ε3 neurons repeatedly increase",
    maxChars: 22000,
  });
  await fs.writeFile(path.join(BUILD_DIR, "before.ndjson"), before.ndjson || "", "utf8");
  for (const slideNumber of [10, 11, 12]) {
    await saveBlob(
      await presentation.export({
        slide: sourceSlides[slideNumber - 1],
        format: "png",
        scale: 1,
      }),
      path.join(BUILD_DIR, `before-slide-${String(slideNumber).padStart(2, "0")}.png`),
    );
  }

  sourceSlides[6].speakerNotes.textFrame.setText(revisedSlide7Notes());
  sourceSlides[6].speakerNotes.setVisible(true);

  sourceSlides[9].speakerNotes.textFrame.setText(
    structuredNotes({
      goal: "Show the breadth of pathway-gene overlap with the fine-cell DEG results.",
      walkthrough:
        "For each sex/APOE group, a pathway gene is counted once if it was a significant DEG in at least one fine-cell comparison. The denominator is the full frozen pathway size shown on the previous slide. Twelve of the 13 mitochondrial-DNA OXPHOS genes appeared in every group. Male epsilon-2 had the broadest overlap in the other three pathways: 67 of 86 nuclear structural OXPHOS genes, 130 of 155 mitochondrial-translation genes, and 17 of 19 inner-membrane genes. Female epsilon-3 homozygous had narrower overlap in mitochondrial translation and inner-membrane organization.",
      boundary:
        "This heatmap collapses across fine cell types and records presence, not direction, recurrence, effect size, or statistical enrichment. Groups with more overall DEGs will tend to overlap more pathway genes. Formal over-representation analysis instead uses the detectable-gene background within each comparison and controls the false-discovery rate.",
      transition: "Define how the OXPHOS direction percentage is calculated.",
    }),
  );

  const captionInspect = await presentation.inspect({
    kind: "textbox",
    search: "% = share of gene-by-fine-cell DEG occurrences in the dominant direction",
    maxChars: 5000,
  });
  const captionRecord = (captionInspect.ndjson || "")
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .find((record) => record.kind === "textbox" && record.slide === 11);
  if (!captionRecord?.id || !captionRecord?.text) {
    throw new Error("Could not locate the slide 11 direction-percentage caption");
  }
  presentation.resolve(captionRecord.id).text.replace(
    captionRecord.text,
    "Bar label = percentage of DEG occurrences in the more common direction. Positive means upregulated. Negative means downregulated.",
  );

  presentation.slides.insert({
    after: sourceSlides[9],
    layoutId: "/ppt/slideLayouts/slideLayout7.xml",
  });
  const formulaSlide = presentation.slides.getItem(10);
  buildFormulaSlide(formulaSlide);

  const finalSlides = slidesFromPresentation(presentation);
  if (finalSlides.length !== EXPECTED_OUTPUT_SLIDES) {
    throw new Error(
      `Expected ${EXPECTED_OUTPUT_SLIDES} output slides, found ${finalSlides.length}`,
    );
  }

  const after = await presentation.inspect({
    kind: "slide,textbox,shape,notes,layout",
    search: "How the OXPHOS direction percentage is calculated|Bar label = percentage of DEG occurrences|Non-OXPHOS signals were fewer",
    maxChars: 24000,
  });
  await fs.writeFile(path.join(BUILD_DIR, "after.ndjson"), after.ndjson || "", "utf8");
  if (!after.ndjson?.includes('"slide":11')) {
    throw new Error("Inserted slide 11 was not found after editing");
  }
  if (!after.ndjson?.includes('"slide":12')) {
    throw new Error("Updated OXPHOS direction chart was not found at slide 12");
  }

  for (const slideNumber of [10, 11, 12, 13]) {
    await saveBlob(
      await presentation.export({
        slide: finalSlides[slideNumber - 1],
        format: "png",
        scale: 1,
      }),
      path.join(BUILD_DIR, `after-slide-${String(slideNumber).padStart(2, "0")}.png`),
    );
  }
  await saveBlob(
    await formulaSlide.export({ format: "layout" }),
    path.join(BUILD_DIR, "after-slide-11.layout.json"),
  );
  await saveBlob(
    await presentation.export({ format: "webp", montage: true, scale: 0.28 }),
    path.join(BUILD_DIR, "after-montage.webp"),
  );

  const sourceBuffer = await fs.readFile(SOURCE);
  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
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
      "09162026_sex_apoe_kda_fine_broad_direction_formula.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const finalInspect = await reopened.inspect({
    kind: "slide,textbox,notes",
    search: "How the OXPHOS direction percentage is calculated|Bar label = percentage of DEG occurrences|Explain the two-stage pathway analysis",
    maxChars: 18000,
  });
  await fs.writeFile(
    path.join(BUILD_DIR, "final.ndjson"),
    finalInspect.ndjson || "",
    "utf8",
  );
  if (reopenedSlides.length !== EXPECTED_OUTPUT_SLIDES) {
    throw new Error("Finalized deck has the wrong slide count");
  }
  await saveBlob(
    await reopened.export({ slide: reopenedSlides[10], format: "png", scale: 1 }),
    path.join(BUILD_DIR, "final-slide-11.png"),
  );
  await saveBlob(
    await reopened.export({ slide: reopenedSlides[11], format: "png", scale: 1 }),
    path.join(BUILD_DIR, "final-slide-12.png"),
  );

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        output: FINAL_PPTX,
        slideCount: EXPECTED_OUTPUT_SLIDES,
        insertedSlide: 11,
        updatedChartSlide: 12,
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
