#!/usr/bin/env node

/** Insert five summary slides before the detailed Finding 1 slide. */

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
  "results/presentations/09162026_findings_summary_20260922_v5/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_findings_summary_20260922_v5/output/09162026_sex_apoe_kda_fine_broad_findings_summary_20260922_v5.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "67c260d2c97cce04ce8108ef70f05cc2aa9f39968af80af9c71decf6ea4a2a9e";
const SOURCE_SLIDES = 155;
const FINAL_SLIDES = 160;

const COLORS = {
  navy: "#11263F",
  navy2: "#244767",
  blue: "#0077B6",
  teal: "#00856F",
  gold: "#F2A900",
  orange: "#D75B00",
  purple: "#7D4FA1",
  text: "#1F2D3D",
  muted: "#536273",
  border: "#D5DFE9",
  bg: "#F4F7FB",
  white: "#FFFFFF",
  paleBlue: "#E9F4FB",
  paleTeal: "#E8F5F1",
  paleGold: "#FFF5DA",
  paleOrange: "#FCEDE5",
  palePurple: "#F3ECF8",
};

const SUMMARY_SLIDES = [
  {
    title: "How the 18 findings are organized",
    subtitle:
      "The findings separate into pre-network expression and pathway results, results from KDA calls, and cross-cohort validation.",
    columns: ["Category", "Findings", "Main question", "Role in the story"],
    widths: [220, 160, 470, 290],
    rows: [
      [
        "DEG and pathway",
        "1–6",
        "How do mitochondrial genes and pathways change within each sex/APOE group?",
        "Primary biological results",
      ],
      [
        "Results from KDA calls",
        "7–16 and 18",
        "Which network genes are returned from KDA calls made with MitoCarta MT DEGs?",
        "Mechanistic hypotheses, with priority on group-linked results",
      ],
      [
        "Human validation",
        "17",
        "Which ROSMAP patterns recur in SEA-AD?",
        "Supporting evidence",
      ],
    ],
    rowFills: [COLORS.paleBlue, COLORS.paleTeal, COLORS.palePurple],
    footer:
      "15 findings are tied to one or more sex/APOE groups. Findings 7, 10, and 17 are not sex/APOE-specific and receive lower priority in the sex/APOE narrative.",
    notes: [
      "Teaching goal: Give the audience a map of all 18 findings before presenting them one by one.",
      "",
      "Walk through: Findings 1–6 come from differential-expression and pathway analyses before making KDA calls. Findings 7–16 and 18 summarize genes returned from KDA calls. Finding 17 evaluates cross-cohort support using SEA-AD.",
      "",
      "Priority: Fifteen findings are linked to one or more analyzed sex/APOE groups. Findings 7, 10, and 17 do not distinguish a sex/APOE group, so they receive lower priority in a presentation centered on sex and APOE.",
      "",
      "Boundary: A result observed in a subset of separately analyzed groups is not proof of a statistical sex or APOE interaction.",
      "",
      "Transition: Summarize the six pre-network DEG and pathway findings first.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 1–18.",
    ].join("\n"),
  },
  {
    title: "Findings 1–6 are DEG and pathway results",
    subtitle:
      "These findings describe mitochondrial gene-expression and pathway patterns before making KDA calls.",
    columns: ["Finding", "Sex/APOE group", "Main result"],
    widths: [120, 250, 770],
    rows: [
      ["1", "Female ε3/ε3", "Core MT genes rise; nuclear-encoded OXPHOS genes also mostly rise in ROSMAP."],
      ["2", "Male ε3/ε3", "Core MT genes rise while nuclear-encoded OXPHOS genes fall."],
      ["3", "Female ε2", "Core MT and nuclear-encoded OXPHOS genes both rise."],
      ["4", "Female ε4", "Nuclear-encoded OXPHOS genes show a strong decrease."],
      ["5", "Male ε2", "Both OXPHOS gene sets show broad decreases."],
      ["6", "Male ε4", "Core MT genes rise while nuclear-encoded OXPHOS genes decrease more modestly."],
    ],
    rowFills: [COLORS.paleBlue],
    footer: "KDA calls are not involved in Findings 1–6.",
    notes: [
      "Teaching goal: Separate the direct DEG and pathway results from the later results of KDA calls.",
      "",
      "Walk through: Finding 1 is the female ε3/ε3 coordinated OXPHOS increase. Finding 2 is the male ε3/ε3 mitonuclear mismatch. Findings 3–6 complete the six sex/APOE group-level pathway patterns.",
      "",
      "Interpretation: These results summarize DEG occurrences and pathway direction across fine cell types. They do not depend on genes returned from KDA calls.",
      "",
      "Boundary: Directional patterns do not establish mitochondrial function, ATP production, or a formal interaction between groups.",
      "",
      "Transition: Move from expression patterns to recurring, sex/APOE-linked genes returned from KDA calls.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 1–6.",
    ].join("\n"),
  },
  {
    title: "Recurring sex/APOE-linked genes from KDA calls",
    subtitle:
      "These genes recur among KDA calls from multiple sex/APOE groups or connect a repeated mitochondrial theme to network genes.",
    columns: ["Finding", "Observed groups", "Gene and mitochondrial connection"],
    widths: [120, 350, 670],
    rows: [
      ["8", "F ε2, F ε3/ε3, F ε4, M ε2", "LAMTOR5 links lysosomal nutrient sensing to OXPHOS."],
      ["9", "F ε2, F ε3/ε3, M ε3/ε3, M ε4", "WDR82 links to a narrow excitatory-neuron core MT-up module."],
      ["11", "F ε2, F ε4, M ε2, M ε3/ε3", "SELENOW connects redox and protein-quality control to respiration."],
      ["12", "F ε3/ε3, F ε4, M ε4", "PGK1 links astrocyte glycolysis and hypoxia signaling to mitochondrial quality control."],
      ["13", "F ε3/ε3, M ε2", "FTL and ANKRD11 link OPC iron handling, GPX4, and autophagy."],
    ],
    rowFills: [COLORS.paleTeal],
    footer:
      "Genes returned from KDA calls are hypotheses: network proximity does not establish causal regulation.",
    notes: [
      "Teaching goal: Summarize recurring sex/APOE-linked genes returned from KDA calls without mixing them with DEG-only results.",
      "",
      "Walk through: LAMTOR5, WDR82, SELENOW, PGK1, and the FTL/ANKRD11 pair each connect a non-MitoCarta candidate to a mitochondrial neighborhood in selected sex/APOE groups.",
      "",
      "Priority: These findings support mechanistic follow-up because they retain subgroup context and connect to coherent biological themes.",
      "",
      "Boundary: A KDA call identifies a network neighborhood, not direct regulation or causality. Recurrence across separately analyzed groups is descriptive rather than independent replication.",
      "",
      "Transition: Review the more qualified or secondary genes returned from sex/APOE-linked KDA calls.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 8, 9, and 11–13.",
    ].join("\n"),
  },
  {
    title: "Qualified sex/APOE-linked genes from KDA calls",
    subtitle:
      "These findings remain useful, but their network evidence is narrow, context-dependent, or sparse.",
    columns: ["Finding", "Observed groups", "Gene and main qualification"],
    widths: [120, 310, 710],
    rows: [
      ["14", "Female ε2, ε3/ε3, and ε4", "PLCG2 has strong AD genetics, but the network neighborhood underlying its KDA calls contains MT-CO1 alone."],
      ["15", "F ε2, M ε2, M ε4", "Astrocyte APOE changes direction across groups and is not an ε4-only result."],
      ["16", "Female ε4", "A small vascular heat-shock module comes from only two eligible KDA calls."],
      ["18", "Male ε2", "INTS8 was returned from one inhibitory-neuron KDA call; human genetics supports follow-up, but network recurrence is absent."],
    ],
    rowFills: [COLORS.paleGold],
    footer:
      "Finding 18 is a secondary gene returned from a KDA call and supported by the completed Phase 19b genetic-support analysis.",
    notes: [
      "Teaching goal: Keep promising but qualified genes returned from KDA calls visible without giving them the same weight as broader recurring results.",
      "",
      "Walk through: PLCG2 has strong gene-level genetics but a fragile one-gene mitochondrial neighborhood. APOE is biologically important but context-dependent. The female ε4 vascular module is small. INTS8 is returned from one male ε2 inhibitory-neuron KDA call and is strengthened by gene-level human genetics.",
      "",
      "Priority: These are targeted follow-up candidates rather than the first results to emphasize in the main narrative.",
      "",
      "Boundary: Gene-level genetics does not validate the inferred cell type, sex/APOE context, or network neighborhood underlying a KDA call.",
      "",
      "Transition: Separate the three findings that do not support a sex/APOE-specific conclusion.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 14–16 and 18.",
    ].join("\n"),
  },
  {
    title: "Lower-priority findings for the sex/APOE story",
    subtitle:
      "These findings remain informative, but they do not distinguish one sex/APOE group from the others.",
    columns: ["Finding", "Scope", "Summary", "Role"],
    widths: [110, 240, 500, 290],
    rows: [
      ["7", "All six groups", "RPL11, RPS15, and related cytosolic-ribosome genes connect to nuclear-encoded OXPHOS genes.", "Shared result from KDA calls"],
      ["10", "All six groups", "SELENOM links ER redox biology to mitochondrial protein production.", "Shared result from KDA calls"],
      ["17", "Cross-cohort comparison", "ROSMAP and SEA-AD agree more on mitochondrial gene sets than on exact genes returned from KDA calls.", "Supporting validation"],
    ],
    rowFills: [COLORS.paleOrange],
    footer:
      "Presentation priority: Findings 1–6 first, sex/APOE-linked results from KDA calls second, and Findings 7, 10, and 17 last.",
    notes: [
      "Teaching goal: Explain why Findings 7, 10, and 17 receive lower priority in a sex/APOE-focused presentation.",
      "",
      "Walk through: Findings 7 and 10 recur across all six groups, so they may describe shared mitochondrial-network biology. Finding 17 evaluates cross-cohort support and is analytical rather than a subgroup-specific mechanism.",
      "",
      "Interpretation: Lower priority refers only to the sex/APOE narrative. These findings can still be biologically important or useful as supporting evidence.",
      "",
      "Boundary: A broad finding may conceal quantitative group differences that require direct interaction models to test.",
      "",
      "Transition: Begin the detailed finding sequence with the female ε3/ε3 DEG and pathway result.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 7, 10, and 17.",
    ].join("\n"),
  },
];

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

async function blobBuffer(blob) {
  return Buffer.from(await blob.arrayBuffer());
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

function insertBeforeClosingTag(xml, closingTag, insertion) {
  const position = xml.lastIndexOf(closingTag);
  if (position < 0) throw new Error(`Could not find closing tag ${closingTag}`);
  return `${xml.slice(0, position)}${insertion}${xml.slice(position)}`;
}

function insertSlideIdsAfter(xml, afterPosition, slideIdTags) {
  const listMatch = xml.match(/<p:sldIdLst>([\s\S]*?)<\/p:sldIdLst>/);
  if (!listMatch) throw new Error("Could not find p:sldIdLst");
  const inner = listMatch[1];
  const tags = [...inner.matchAll(/<p:sldId\b[^>]*\/?\s*>/g)];
  if (tags.length !== SOURCE_SLIDES) {
    throw new Error(`Expected ${SOURCE_SLIDES} slide IDs, found ${tags.length}`);
  }
  const anchor = tags[afterPosition - 1];
  const insertionPoint = anchor.index + anchor[0].length;
  const revisedInner = `${inner.slice(0, insertionPoint)}${slideIdTags}${inner.slice(insertionPoint)}`;
  return xml.replace(inner, revisedInner);
}

async function buildHybridCandidate(JSZip, sourceBuffer, artifactPath, candidatePath) {
  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactPath));
  const addedParts = [];

  for (let index = 0; index < SUMMARY_SLIDES.length; index += 1) {
    const artifactNumber = 53 + index;
    const newNumber = 156 + index;
    const mappings = [
      [`ppt/slides/slide${artifactNumber}.xml`, `ppt/slides/slide${newNumber}.xml`],
      [
        `ppt/slides/_rels/slide${artifactNumber}.xml.rels`,
        `ppt/slides/_rels/slide${newNumber}.xml.rels`,
      ],
      [
        `ppt/notesSlides/notesSlide${artifactNumber}.xml`,
        `ppt/notesSlides/notesSlide${newNumber}.xml`,
      ],
      [
        `ppt/notesSlides/_rels/notesSlide${artifactNumber}.xml.rels`,
        `ppt/notesSlides/_rels/notesSlide${newNumber}.xml.rels`,
      ],
    ];
    for (const [artifactPart, newPart] of mappings) {
      let content = await artifactZip.file(artifactPart)?.async("string");
      if (!content) throw new Error(`Missing artifact part: ${artifactPart}`);
      if (artifactPart.endsWith(".rels")) {
        content = content
          .replaceAll(
            `/ppt/notesSlides/notesSlide${artifactNumber}.xml`,
            `/ppt/notesSlides/notesSlide${newNumber}.xml`,
          )
          .replaceAll(
            `/ppt/slides/slide${artifactNumber}.xml`,
            `/ppt/slides/slide${newNumber}.xml`,
          );
      }
      sourceZip.file(newPart, content);
      addedParts.push(newPart);
    }
  }

  let presentationRels = await sourceZip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  let presentationXml = await sourceZip.file("ppt/presentation.xml")?.async("string");
  let contentTypes = await sourceZip.file("[Content_Types].xml")?.async("string");
  let appXml = await sourceZip.file("docProps/app.xml")?.async("string");
  if (!presentationRels || !presentationXml || !contentTypes || !appXml) {
    throw new Error("Source package metadata is incomplete");
  }

  const relationshipNumbers = [...presentationRels.matchAll(/Id="rId(\d+)"/g)].map(
    (match) => Number(match[1]),
  );
  let nextRelationshipNumber = Math.max(...relationshipNumbers) + 1;
  const slideIds = [...presentationXml.matchAll(/<p:sldId\b[^>]*\bid="(\d+)"[^>]*\/?\s*>/g)].map(
    (match) => Number(match[1]),
  );
  let nextSlideId = Math.max(...slideIds) + 1;
  const newSlideIdTags = [];
  const newRelationshipTags = [];
  const newContentTypeTags = [];
  for (let index = 0; index < SUMMARY_SLIDES.length; index += 1) {
    const newNumber = 156 + index;
    const relationshipId = `rId${nextRelationshipNumber}`;
    nextRelationshipNumber += 1;
    newRelationshipTags.push(
      `<Relationship Id="${relationshipId}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide${newNumber}.xml"/>`,
    );
    newSlideIdTags.push(`<p:sldId id="${nextSlideId}" r:id="${relationshipId}"/>`);
    nextSlideId += 1;
    newContentTypeTags.push(
      `<Override PartName="/ppt/slides/slide${newNumber}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>`,
      `<Override PartName="/ppt/notesSlides/notesSlide${newNumber}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>`,
    );
  }

  presentationRels = insertBeforeClosingTag(
    presentationRels,
    "</Relationships>",
    newRelationshipTags.join(""),
  );
  presentationXml = insertSlideIdsAfter(presentationXml, 52, newSlideIdTags.join(""));
  contentTypes = insertBeforeClosingTag(contentTypes, "</Types>", newContentTypeTags.join(""));
  if (!appXml.includes(`<Slides>${SOURCE_SLIDES}</Slides>`)) {
    throw new Error("Unexpected slide count in docProps/app.xml");
  }
  appXml = appXml.replace(`<Slides>${SOURCE_SLIDES}</Slides>`, `<Slides>${FINAL_SLIDES}</Slides>`);

  sourceZip.file("ppt/_rels/presentation.xml.rels", presentationRels);
  sourceZip.file("ppt/presentation.xml", presentationXml);
  sourceZip.file("[Content_Types].xml", contentTypes);
  sourceZip.file("docProps/app.xml", appXml);
  await fs.writeFile(
    candidatePath,
    await sourceZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );
  return addedParts;
}

function addTextBox(slide, name, text, position, style) {
  const box = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  box.text = text;
  box.text.style = {
    typeface: "Arial",
    autoFit: "shrinkText",
    wrap: "square",
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
    ...style,
  };
  return box;
}

function styleTable(table, rowFills) {
  const rowCount = table.rows.length;
  const columnCount = table.columns.length;
  table.borders.assign({ style: "solid", fill: COLORS.border, width: 1 });
  table.cells.block({ row: 0, column: 0, rowCount, columnCount }).assign({
    textStyle: {
      typeface: "Arial",
      fontSize: 16,
      color: COLORS.text,
      alignment: "left",
    },
    margins: { left: 12, right: 12, top: 8, bottom: 8 },
    anchor: "middle",
    horizontalOverflow: "clip",
  });
  table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount }).assign({
    fill: COLORS.paleBlue,
    textStyle: {
      typeface: "Arial",
      fontSize: 16,
      bold: true,
      color: COLORS.navy,
      alignment: "left",
    },
  });
  for (let row = 1; row < rowCount; row += 1) {
    const fill = rowFills[(row - 1) % rowFills.length];
    table.cells.block({ row, column: 0, rowCount: 1, columnCount }).assign({ fill });
    table.cells.block({ row, column: 0, rowCount: 1, columnCount: 1 }).assign({
      textStyle: {
        typeface: "Arial",
        fontSize: 17,
        bold: true,
        color: COLORS.navy,
        alignment: "left",
      },
    });
  }
  for (let row = 0; row < rowCount; row += 1) {
    for (let column = 0; column < columnCount; column += 1) {
      const cell = table.getCell(row, column);
      cell.fill = row === 0 ? COLORS.paleBlue : rowFills[(row - 1) % rowFills.length];
      table.cells.block({ row, column, rowCount: 1, columnCount: 1 }).assign({
        textStyle: {
          typeface: "Arial",
          fontSize: row === 0 ? 16 : column === 0 ? 17 : 16,
          bold: row === 0 || column === 0,
          color: row === 0 ? COLORS.navy : COLORS.text,
          alignment: "left",
        },
      });
    }
  }
}

function richTableValues(columns, rows) {
  return [columns, ...rows].map((row, rowIndex) =>
    row.map((value, columnIndex) => [
      {
        run: String(value),
        textStyle: {
          typeface: "Arial",
          fontSize: rowIndex === 0 ? "12pt" : columnIndex === 0 ? "12.75pt" : "12pt",
          bold: rowIndex === 0 || columnIndex === 0,
          color: rowIndex === 0 ? COLORS.navy : COLORS.text,
        },
      },
    ]),
  );
}

function addSummarySlide(presentation, spec, index) {
  const slide = presentation.slides.add();
  slide.moveTo(51 + index);
  slide.background.fill = COLORS.bg;
  addTextBox(
    slide,
    `Summary ${index} Title`,
    spec.title,
    { left: 64, top: 38, width: 1152, height: 58 },
    { fontSize: 30, bold: true, color: COLORS.navy, alignment: "left" },
  );
  addTextBox(
    slide,
    `Summary ${index} Subtitle`,
    spec.subtitle,
    { left: 66, top: 105, width: 1148, height: 44 },
    { fontSize: 17, color: COLORS.muted, alignment: "left" },
  );

  const tableTop = 160;
  const tableBottom = 621;
  const values = richTableValues(spec.columns, spec.rows);
  const table = slide.tables.add({
    rows: values.length,
    columns: spec.columns.length,
    left: 70,
    top: tableTop,
    width: 1140,
    height: tableBottom - tableTop,
    columnWidths: spec.widths,
    values,
  });
  table.name = `Summary ${index} Table`;
  styleTable(table, spec.rowFills);
  table.rows[0].height = 56;
  const bodyRowHeight = (tableBottom - tableTop - 56) / (values.length - 1);
  for (let row = 1; row < values.length; row += 1) table.rows[row].height = bodyRowHeight;

  addTextBox(
    slide,
    `Summary ${index} Footer`,
    spec.footer,
    { left: 72, top: 642, width: 1136, height: 42 },
    { fontSize: 16, bold: true, color: COLORS.purple, alignment: "left" },
  );
  slide.speakerNotes.textFrame.setText(spec.notes);
  slide.speakerNotes.setVisible(true);
  return slide;
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
    throw new Error(`Source deck changed before the summary-slide edit: ${sourceHash}`);
  }

  const { importRuntimeModule } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href
  );
  const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");
  const JSZipModule = await importRuntimeModule("jszip");
  const JSZip = JSZipModule.default ?? JSZipModule;
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const originalSlides = slidesFromPresentation(presentation);
  if (originalSlides.length !== SOURCE_SLIDES) {
    throw new Error(`Expected ${SOURCE_SLIDES} source slides, found ${originalSlides.length}`);
  }

  const beforeImages = new Map();
  for (const slideNumber of [1, 19, 52, 53, 155]) {
    beforeImages.set(
      slideNumber,
      await blobBuffer(
        await presentation.export({
          slide: originalSlides[slideNumber - 1],
          format: "png",
          scale: 1.25,
        }),
      ),
    );
  }

  const insertedSlides = [];
  for (let index = 0; index < SUMMARY_SLIDES.length; index += 1) {
    const inserted = addSummarySlide(presentation, SUMMARY_SLIDES[index], index + 1);
    insertedSlides.push(inserted);
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed during the summary-slide edit");
  }

  const hybridCandidatePath = path.join(BUILD_DIR, "candidate.pptx");
  const addedParts = await buildHybridCandidate(
    JSZip,
    sourceBuffer,
    artifactCandidatePath,
    hybridCandidatePath,
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const validation = await finalizePresentation({
    explicitTotalSlideCount: FINAL_SLIDES,
    requiredNativeTableOwnerSlides: [53, 54, 55, 56, 57],
    requiredNativeChartOwnerSlides: [19],
    requiredEmbeddedWorkbookChartOwnerSlides: [19],
    nativeChartTargetApplication: "powerpoint",
    workspaceDir: WORKSPACE_DIR,
    candidatePath: hybridCandidatePath,
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
    receiptPath: path.join(BUILD_DIR, "findings_summary.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalSlides = slidesFromPresentation(reopened);
  if (finalSlides.length !== FINAL_SLIDES) {
    throw new Error(`Expected ${FINAL_SLIDES} final slides, found ${finalSlides.length}`);
  }

  const slideSnapshot = await reopened.inspect({ kind: "slides", maxChars: 1000000 });
  const slideTitles = new Map(
    parseNdjson(slideSnapshot.ndjson)
      .filter((record) => record.kind === "slide" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.title]),
  );
  for (let index = 0; index < SUMMARY_SLIDES.length; index += 1) {
    const slideNumber = 53 + index;
    if (slideTitles.get(slideNumber) !== SUMMARY_SLIDES[index].title) {
      throw new Error(`Unexpected title on inserted slide ${slideNumber}`);
    }
  }
  if (slideTitles.get(58) !== "FINDING 1") {
    throw new Error(`Detailed finding sequence did not shift correctly: ${slideTitles.get(58)}`);
  }

  const notesSnapshot = await reopened.inspect({ kind: "notes", maxChars: 4000000 });
  const notesBySlide = new Map(
    parseNdjson(notesSnapshot.ndjson)
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text]),
  );
  for (let index = 0; index < SUMMARY_SLIDES.length; index += 1) {
    const slideNumber = 53 + index;
    if (notesBySlide.get(slideNumber)?.trim() !== SUMMARY_SLIDES[index].notes.trim()) {
      throw new Error(`Speaker notes do not match on inserted slide ${slideNumber}`);
    }
    const png = await blobBuffer(
      await reopened.export({ slide: finalSlides[slideNumber - 1], format: "png", scale: 1.5 }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-final.png`), png);
  }

  const shiftedChecks = new Map([
    [1, 1],
    [19, 19],
    [52, 52],
    [53, 58],
    [155, 160],
  ]);
  for (const [beforeNumber, afterNumber] of shiftedChecks) {
    const afterPng = await blobBuffer(
      await reopened.export({ slide: finalSlides[afterNumber - 1], format: "png", scale: 1.25 }),
    );
    if (sha256(beforeImages.get(beforeNumber)) !== sha256(afterPng)) {
      throw new Error(
        `Existing slide ${beforeNumber} changed visually after insertion at slide ${afterNumber}`,
      );
    }
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const expectedChangedExistingParts = new Set([
    "[Content_Types].xml",
    "docProps/app.xml",
    "ppt/_rels/presentation.xml.rels",
    "ppt/presentation.xml",
  ]);
  const changedExistingParts = [];
  for (const [name, entry] of Object.entries(sourceZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing source part ${name}`);
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) changedExistingParts.push(name);
  }
  changedExistingParts.sort();
  const expectedChanged = [...expectedChangedExistingParts].sort();
  if (
    changedExistingParts.length !== expectedChanged.length ||
    changedExistingParts.some((name, index) => name !== expectedChanged[index])
  ) {
    throw new Error(`Unexpected existing package changes: ${changedExistingParts.join(", ")}`);
  }
  for (const part of addedParts) {
    if (!finalZip.file(part)) throw new Error(`Final deck is missing added part ${part}`);
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
        sourceSlideCount: SOURCE_SLIDES,
        finalSlideCount: FINAL_SLIDES,
        insertedSlides: [53, 54, 55, 56, 57],
        insertedTitles: SUMMARY_SLIDES.map((slide) => slide.title),
        changedExistingParts,
        addedParts,
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
