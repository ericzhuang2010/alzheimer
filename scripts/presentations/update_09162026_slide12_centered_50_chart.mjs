#!/usr/bin/env node

/**
 * Move slide 12's category axis to 50% so bars extend upward or downward from
 * the equal-direction baseline. Preserve the actual upregulated percentages.
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
  "results/presentations/09162026_slide12_centered_50_chart/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slide12_centered_50_chart/output/09162026_sex_apoe_kda_fine_broad_slide12_centered_50_v2.pptx",
);
const EXPECTED_SLIDES = 160;
const MITOCHONDRIAL_DEVIATIONS = [49, 50, -9, -40, 36, 29];
const NUCLEAR_DEVIATIONS = [48, 35, -45, -37, -38, -12];

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

function slide11Notes() {
  return structuredNotes({
    goal:
      "Define an occurrence and show how the upregulated OXPHOS occurrence percentage is calculated.",
    walkthrough:
      "Begin with the counting unit highlighted on the slide. One occurrence means that one pathway gene is a significant DEG in one fine-cell comparison. If the same gene is significant in another fine cell type, it contributes another occurrence. The calculation is performed separately for each sex/APOE group and each OXPHOS gene set. Divide the upregulated occurrences by all upregulated plus downregulated occurrences, then multiply by 100. In the male epsilon-3 homozygous mtDNA-encoded OXPHOS example, 70 occurrences were upregulated and 11 were downregulated. Seventy divided by 81 equals 86 percent upregulated. A value of 50 percent means the two directions occur equally often. Values above 50 percent favor upregulation, while values below 50 percent favor downregulation.",
    boundary:
      "This occurrence-based summary gives more weight to genes that recur across fine-cell comparisons. It is not a fold change, the percentage of unique genes, cells, donors, or fine cell types, an enrichment result, or a measure of OXPHOS activity. Repeated occurrences are not independent biological replications.",
    transition:
      "Compare the upregulated occurrence percentage across the six sex/APOE groups.",
  });
}

function slide12Notes() {
  return structuredNotes({
    goal:
      "Interpret OXPHOS DEG direction across sex/APOE groups and highlight the contrasting epsilon-3 homozygous patterns.",
    walkthrough:
      "OXPHOS, or oxidative phosphorylation, is the mitochondrial process that produces most cellular ATP. Blue bars summarize the 13 OXPHOS genes encoded by mitochondrial DNA, and orange bars summarize 86 structural OXPHOS genes encoded by nuclear DNA. Every bar starts at the 50 percent line, where upregulated and downregulated occurrences are equally common. Bars extend upward when more than half of the occurrences are upregulated and downward when fewer than half are upregulated. The label at the end of each bar gives the actual upregulated percentage, while bar length shows its percentage-point distance from 50 percent. The key contrast is shown in the callout. In female epsilon-3 homozygous, both gene sets are predominantly upregulated: 100 percent for the mitochondrial-DNA set and 85 percent for the nuclear-DNA set. In male epsilon-3 homozygous, the two sets diverge: 86 percent of mitochondrial-DNA occurrences are upregulated, but only 12 percent of nuclear-DNA occurrences are upregulated, which means 88 percent are downregulated. The broader pattern is that female epsilon-2 is predominantly upregulated in both sets, female epsilon-4 and male epsilon-2 are predominantly downregulated in both, and male epsilon-4 shows a weaker version of the male epsilon-3 homozygous split.",
    boundary:
      "The bars show the share of repeated gene-by-fine-cell DEG occurrences that are upregulated. The vertical displacement from 50 percent is a descriptive percentage-point difference, not an effect size. The chart does not show percent expression change, percent of cells or donors, percent of unique genes, pathway enrichment, OXPHOS activity, or a direct statistical interaction between disease, sex, and APOE.",
    transition:
      "Now move to Part 3, where mitochondrial DEGs become network-analysis queries.",
  });
}

function relationshipTarget(relsXml, relationshipTypeSuffix) {
  for (const match of relsXml.matchAll(/<Relationship\b[^>]*>/g)) {
    const tag = match[0];
    if (!tag.includes(`/relationships/${relationshipTypeSuffix}`)) continue;
    const target = tag.match(/\bTarget="([^"]+)"/)?.[1];
    if (target) return target;
  }
  return undefined;
}

async function partPathForSlide(zip, slideNumber, relationshipTypeSuffix) {
  const relsPath = `ppt/slides/_rels/slide${slideNumber}.xml.rels`;
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing ${relsPath}`);
  const target = relationshipTarget(relsXml, relationshipTypeSuffix);
  if (!target) {
    throw new Error(`Slide ${slideNumber} lacks ${relationshipTypeSuffix} relationship`);
  }
  return path.posix.normalize(path.posix.join("ppt/slides", target));
}

function updateDataLabel(seriesXml, pointIndex, color) {
  const labelPattern = new RegExp(
    `<c:dLbl><c:idx val="${pointIndex}"\\/>[\\s\\S]*?<\\/c:dLbl>`,
  );
  const label = seriesXml.match(labelPattern)?.[0];
  if (!label) throw new Error(`Missing data label for point ${pointIndex}`);
  let updated = label.replace(
    /<c:dLblPos val="(?:inEnd|outEnd|center)"\/>/,
    '<c:dLblPos val="outEnd"/>',
  );
  updated = updated.replace(
    /<a:srgbClr val="FFFFFF"\/>/,
    `<a:srgbClr val="${color}"/>`,
  );
  return seriesXml.replace(label, updated);
}

function replaceSeriesValues(seriesXml, values) {
  const valueBlock = seriesXml.match(/<c:val>[\s\S]*?<\/c:val>/)?.[0];
  if (!valueBlock) throw new Error("Chart series lacks a value block");
  let updatedValueBlock = valueBlock.replace(
    /<c:formatCode>[\s\S]*?<\/c:formatCode>/,
    '<c:formatCode>0" pp"</c:formatCode>',
  );
  for (let idx = 0; idx < values.length; idx += 1) {
    const pointPattern = new RegExp(
      `(<c:pt idx="${idx}"><c:v>)[^<]*(<\\/c:v><\\/c:pt>)`,
    );
    if (!pointPattern.test(updatedValueBlock)) {
      throw new Error(`Chart series lacks cached point ${idx}`);
    }
    updatedValueBlock = updatedValueBlock.replace(
      pointPattern,
      `$1${values[idx]}$2`,
    );
  }
  return seriesXml.replace(valueBlock, updatedValueBlock);
}

function makeDivergingChart(chartXml) {
  const categoryAxis = chartXml.match(/<c:catAx>[\s\S]*?<\/c:catAx>/)?.[0];
  if (!categoryAxis) throw new Error("Chart lacks a category axis");
  let updatedAxis = categoryAxis.replace(
    /<c:crosses(?:At)?\b[^>]*\/>/,
    '<c:crosses val="autoZero"/>',
  );
  updatedAxis = updatedAxis.replace(
    /<c:tickLblPos val="[^"]+"\/>/,
    '<c:tickLblPos val="low"/>',
  );
  let updatedChart = chartXml.replace(categoryAxis, updatedAxis);

  const series = [...updatedChart.matchAll(/<c:ser>[\s\S]*?<\/c:ser>/g)].map(
    (match) => match[0],
  );
  if (series.length !== 2) {
    throw new Error(`Expected two chart series, found ${series.length}`);
  }
  let updatedMitochondrial = replaceSeriesValues(
    series[0],
    MITOCHONDRIAL_DEVIATIONS,
  );
  updatedMitochondrial = updateDataLabel(updatedMitochondrial, 2, "0072B2");
  updatedMitochondrial = updatedMitochondrial.replace(
    /<c:invertIfNegative val="1"\/>/,
    '<c:invertIfNegative val="0"/>',
  );
  updatedChart = updatedChart.replace(series[0], updatedMitochondrial);

  const currentSeries = [
    ...updatedChart.matchAll(/<c:ser>[\s\S]*?<\/c:ser>/g),
  ].map((match) => match[0]);
  let updatedNuclear = replaceSeriesValues(
    currentSeries[1],
    NUCLEAR_DEVIATIONS,
  );
  updatedNuclear = updateDataLabel(updatedNuclear, 5, "D55E00");
  updatedNuclear = updatedNuclear.replace(
    /<c:invertIfNegative val="1"\/>/,
    '<c:invertIfNegative val="0"/>',
  );
  updatedChart = updatedChart.replace(currentSeries[1], updatedNuclear);

  const valueAxis = updatedChart.match(/<c:valAx>[\s\S]*?<\/c:valAx>/)?.[0];
  if (!valueAxis) throw new Error("Chart lacks a value axis");
  let updatedValueAxis = valueAxis.replace(
    /<c:scaling>[\s\S]*?<\/c:scaling>/,
    '<c:scaling><c:orientation val="minMax"/><c:max val="50"/><c:min val="-50"/></c:scaling>',
  );
  updatedValueAxis = updatedValueAxis.replace(
    /<a:t>Upregulated occurrences among all OXPHOS DEG occurrences<\/a:t>/,
    '<a:t>Difference from 50% (percentage points)</a:t>',
  );
  updatedValueAxis = updatedValueAxis.replace(
    /<c:numFmt\b[^>]*\/>/,
    '<c:numFmt formatCode="+0&quot; pp&quot;;-0&quot; pp&quot;;&quot;50% equal&quot;" sourceLinked="0"/>',
  );
  updatedChart = updatedChart.replace(valueAxis, updatedValueAxis);

  if (!updatedChart.includes('<c:min val="-50"/>')) {
    throw new Error("The centered value-axis minimum was not written");
  }
  return updatedChart;
}

function updateWorkbookCell(sheetXml, reference, value) {
  const cellPattern = new RegExp(
    `(<c\\b[^>]*\\br="${reference}"[^>]*>[\\s\\S]*?<v>)[^<]*(<\\/v>[\\s\\S]*?<\\/c>)`,
  );
  if (!cellPattern.test(sheetXml)) {
    throw new Error(`Workbook lacks cell ${reference}`);
  }
  return sheetXml.replace(cellPattern, `$1${value}$2`);
}

async function updateEmbeddedWorkbook(sourceZip, chartPath, JSZip) {
  const chartName = path.posix.basename(chartPath);
  const chartRelsPath = path.posix.join(
    path.posix.dirname(chartPath),
    "_rels",
    `${chartName}.rels`,
  );
  const chartRelsXml = await sourceZip.file(chartRelsPath)?.async("string");
  if (!chartRelsXml) throw new Error(`Missing ${chartRelsPath}`);
  const workbookTarget = relationshipTarget(chartRelsXml, "package");
  if (!workbookTarget) throw new Error("Chart lacks an embedded workbook relationship");
  const workbookPath = path.posix.normalize(
    path.posix.join(path.posix.dirname(chartPath), workbookTarget),
  );
  const workbookBuffer = await sourceZip.file(workbookPath)?.async("nodebuffer");
  if (!workbookBuffer) throw new Error(`Missing ${workbookPath}`);
  const workbookZip = await JSZip.loadAsync(workbookBuffer);
  const sheetPath = "xl/worksheets/sheet1.xml";
  let sheetXml = await workbookZip.file(sheetPath)?.async("string");
  if (!sheetXml) throw new Error(`Embedded workbook lacks ${sheetPath}`);
  for (let idx = 0; idx < 6; idx += 1) {
    sheetXml = updateWorkbookCell(
      sheetXml,
      `B${idx + 2}`,
      MITOCHONDRIAL_DEVIATIONS[idx],
    );
    sheetXml = updateWorkbookCell(
      sheetXml,
      `D${idx + 2}`,
      NUCLEAR_DEVIATIONS[idx],
    );
  }
  workbookZip.file(sheetPath, sheetXml);
  sourceZip.file(
    workbookPath,
    await workbookZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );
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
  const JSZipModule = await importRuntimeModule("jszip");
  const JSZip = JSZipModule.default ?? JSZipModule;

  const sourceBuffer = await fs.readFile(SOURCE);
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const slides = slidesFromPresentation(presentation);
  if (slides.length !== EXPECTED_SLIDES) {
    throw new Error(`Expected ${EXPECTED_SLIDES} slides, found ${slides.length}`);
  }

  const beforeInspect = await presentation.inspect({
    kind: "slide,textbox,notes,chart,layout",
    search:
      "How the upregulated occurrence percentage is calculated|Share of OXPHOS DEG occurrences that are upregulated",
    maxChars: 22000,
  });
  if (!beforeInspect.ndjson?.includes('"slide":11')) {
    throw new Error("Could not verify slide 11");
  }
  if (!beforeInspect.ndjson?.includes('"slide":12')) {
    throw new Error("Could not verify slide 12");
  }
  await fs.writeFile(
    path.join(BUILD_DIR, "before.ndjson"),
    beforeInspect.ndjson || "",
    "utf8",
  );
  await fs.writeFile(
    path.join(BUILD_DIR, "slide-12-before.png"),
    await blobBuffer(
      await presentation.export({ slide: slides[11], format: "png", scale: 1 }),
    ),
  );

  slides[10].speakerNotes.textFrame.setText(slide11Notes());
  slides[10].speakerNotes.setVisible(true);
  slides[11].speakerNotes.textFrame.setText(slide12Notes());
  slides[11].speakerNotes.setVisible(true);

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  const artifactCandidateBuffer = await fs.readFile(artifactCandidatePath);

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(artifactCandidateBuffer);
  for (const slideNumber of [11, 12]) {
    const notesPath = await partPathForSlide(sourceZip, slideNumber, "notesSlide");
    const updatedNotesXml = await artifactZip.file(notesPath)?.async("string");
    if (!updatedNotesXml) {
      throw new Error(`Artifact candidate lacks ${notesPath}`);
    }
    sourceZip.file(notesPath, updatedNotesXml);
  }

  const chartPath = await partPathForSlide(sourceZip, 12, "chart");
  const sourceChartXml = await sourceZip.file(chartPath)?.async("string");
  if (!sourceChartXml) throw new Error(`Missing ${chartPath}`);
  sourceZip.file(chartPath, makeDivergingChart(sourceChartXml));
  await updateEmbeddedWorkbook(sourceZip, chartPath, JSZip);

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
    await sourceZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const result = await finalizePresentation({
    explicitTotalSlideCount: EXPECTED_SLIDES,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [12],
    requiredEmbeddedWorkbookChartOwnerSlides: [12],
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
      referenceSha256: sha256(sourceBuffer),
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(
      BUILD_DIR,
      "09162026_sex_apoe_kda_fine_broad_slide12_centered_50_v2.validation.json",
    ),
  });

  const finalBuffer = await fs.readFile(FINAL_PPTX);
  const finalZip = await JSZip.loadAsync(finalBuffer);
  const finalChartXml = await finalZip.file(chartPath)?.async("string");
  if (!finalChartXml?.includes('<c:min val="-50"/>')) {
    throw new Error("Finalized chart is not centered around the 50 percent baseline");
  }

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const finalInspect = await reopened.inspect({
    kind: "slide,textbox,notes,chart",
    search:
      "Share of OXPHOS DEG occurrences that are upregulated|Every bar starts at the 50 percent line",
    maxChars: 22000,
  });
  await fs.writeFile(
    path.join(BUILD_DIR, "final.ndjson"),
    finalInspect.ndjson || "",
    "utf8",
  );
  await fs.writeFile(
    path.join(BUILD_DIR, "slide-12-final.png"),
    await blobBuffer(
      await reopened.export({
        slide: reopenedSlides[11],
        format: "png",
        scale: 1,
      }),
    ),
  );

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sha256(sourceBuffer),
        output: FINAL_PPTX,
        slideCount: EXPECTED_SLIDES,
        updatedSlide: 12,
        categoryAxisCrossing: "0 percentage points, labeled as the 50% baseline",
        barLabels: "actual upregulated percentages",
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
