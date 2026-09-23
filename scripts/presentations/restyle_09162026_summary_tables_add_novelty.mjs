#!/usr/bin/env node

/** Restyle slides 53–57 summary tables and add novelty to slides 54–57. */

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
  "results/presentations/09162026_summary_tables_novelty_20260922_v1",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_summary_tables_novelty_20260922_v1.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "98dfdc2d0340e842869dfc19365824c2f259197764647bce2a6bbc246b21e49a";
const EXPECTED_SLIDES = 160;

const COLORS = {
  navy: "#11263F",
  navy2: "#244767",
  text: "#1F2D3D",
  muted: "#536273",
  border: "#D5DFE9",
  white: "#FFFFFF",
  stripe: "#F7FAFD",
  blue: "#0077B6",
  teal: "#00856F",
  orange: "#B86100",
  purple: "#7D4FA1",
  highFill: "#FFF1CE",
  highText: "#8A4A00",
  moderateFill: "#E5F2FA",
  moderateText: "#005E82",
};

const TABLE_SPECS = new Map([
  [
    53,
    {
      name: "Summary 1 Table",
      accent: COLORS.blue,
      widths: [220, 160, 470, 290],
      values: [
        ["Category", "Findings", "Main question", "Role in the story"],
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
          "Candidate genes that may drive or explain mitochondrial changes",
        ],
        [
          "Human validation",
          "17",
          "Which ROSMAP patterns recur in SEA-AD?",
          "Supporting evidence",
        ],
      ],
      firstColumnFills: [COLORS.blue, COLORS.teal, COLORS.purple],
      centeredColumns: [1],
    },
  ],
  [
    54,
    {
      name: "Summary 2 Table",
      accent: COLORS.blue,
      widths: [90, 220, 690, 140],
      values: [
        ["Finding", "Sex/APOE group", "Main result", "Novelty"],
        ["1", "Female ε3/ε3", "Core MT genes rise; nuclear-encoded OXPHOS genes also mostly rise in ROSMAP.", "Moderate"],
        ["2", "Male ε3/ε3", "Core MT genes rise while nuclear-encoded OXPHOS genes fall.", "High"],
        ["3", "Female ε2", "Core MT and nuclear-encoded OXPHOS genes both rise.", "High"],
        ["4", "Female ε4", "Nuclear-encoded OXPHOS genes show a strong decrease.", "Moderate"],
        ["5", "Male ε2", "Both core MT and nuclear-encoded OXPHOS gene sets show broad decreases.", "High"],
        ["6", "Male ε4", "Core MT genes rise while nuclear-encoded OXPHOS genes decrease more modestly.", "Moderate"],
      ],
      centeredColumns: [0, 3],
    },
  ],
  [
    55,
    {
      name: "Summary 3 Table",
      accent: COLORS.teal,
      widths: [85, 270, 625, 160],
      values: [
        ["Finding", "Observed groups", "Gene and mitochondrial connection", "Novelty"],
        ["8", "F ε2, F ε3/ε3, F ε4, M ε2", "LAMTOR5 connects genes that sense nutrients at lysosomes, the cell’s recycling compartments, with OXPHOS genes.", "High"],
        ["9", "F ε2, F ε3/ε3, M ε3/ε3, M ε4", "WDR82 is connected in the network to a small set of core MT genes that are upregulated in AD in excitatory neurons.", "High"],
        ["11", "F ε2, F ε4, M ε2, M ε3/ε3", "SELENOW, a gene involved in controlling oxidative stress, was connected to genes involved in mitochondrial respiration, protein production, and removal of damaged mitochondrial proteins.", "Moderate"],
        ["12", "F ε3/ε3, F ε4, M ε4", "PGK1 connects astrocyte glycolysis and low-oxygen signaling with genes involved in removing damaged mitochondria.", "Moderate"],
        ["13", "F ε3/ε3, M ε2", "FTL and ANKRD11 connect iron handling in oligodendrocyte precursor cells with genes that protect against oxidative damage and recycle damaged cell components.", "High"],
      ],
      centeredColumns: [0, 3],
    },
  ],
  [
    56,
    {
      name: "Summary 4 Table",
      accent: COLORS.orange,
      widths: [85, 245, 650, 160],
      values: [
        ["Finding", "Observed groups", "Gene and main qualification", "Novelty"],
        ["14", "Female ε2, ε3/ε3, and ε4", "PLCG2 has strong AD genetic evidence, but only one MitoCarta MT gene, MT-CO1, was connected to it in the KDA result.", "High"],
        ["15", "F ε2, M ε2, M ε4", "Astrocyte APOE expression changes in opposite directions across groups, so the result is not specific to ε4.", "Moderate"],
        ["16", "Female ε4", "A small group of genes that respond to protein damage and cellular stress appears in only two female ε4 vascular-cell KDA calls.", "Moderate"],
        ["18", "Male ε2", "INTS8 was returned from one inhibitory-neuron KDA call. Human genetics supports follow-up, but it was not returned from additional KDA calls.", "Moderate"],
      ],
      centeredColumns: [0, 3],
    },
  ],
  [
    57,
    {
      name: "Summary 5 Table",
      accent: COLORS.purple,
      widths: [80, 190, 470, 260, 140],
      values: [
        ["Finding", "Scope", "Summary", "Role", "Novelty"],
        ["7", "All six groups", "RPL11, RPS15, and related genes that help ribosomes outside mitochondria make proteins are connected to nuclear-encoded OXPHOS genes.", "Found across all six sex/APOE groups", "Moderate"],
        ["10", "All six groups", "SELENOM, which helps control oxidative stress and calcium inside the endoplasmic reticulum, is connected to genes used for mitochondrial protein production.", "Found across all six sex/APOE groups", "High"],
        ["17", "Cross-cohort comparison", "ROSMAP and SEA-AD agree more on mitochondrial gene sets than on exact genes returned from KDA calls.", "Supporting validation", "Moderate"],
      ],
      centeredColumns: [0, 4],
    },
  ],
]);

const NOVELTY_NOTE =
  "Novelty is provisional. It describes how much the specific result adds beyond prior research and is separate from evidence strength.";

const NOVELTY_SUMMARIES = new Map([
  [54, "Ratings: Findings 1, 4, and 6 are Moderate; Findings 2, 3, and 5 are High."],
  [55, "Ratings: Findings 8, 9, and 13 are High; Findings 11 and 12 are Moderate."],
  [56, "Ratings: Finding 14 is High; Findings 15, 16, and 18 are Moderate. Finding 14 remains a low-confidence network result despite its high novelty."],
  [57, "Ratings: Findings 7 and 17 are Moderate; Finding 10 is High."],
]);

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function parseNdjson(ndjson) {
  return (ndjson || "")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
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

function styleTable(table, spec) {
  const rowCount = spec.values.length;
  const columnCount = spec.values[0].length;
  table.styleOptions = {
    headerRow: true,
    totalRow: false,
    firstColumn: false,
    lastColumn: false,
    bandedRows: false,
    bandedColumns: false,
  };
  table.borders.assign({ style: "solid", fill: COLORS.border, width: 1 });
  table.cells.block({ row: 0, column: 0, rowCount, columnCount }).assign({
    textStyle: {
      typeface: "Arial",
      fontSize: 15,
      color: COLORS.text,
      alignment: "left",
    },
    margins: { left: 10, right: 10, top: 7, bottom: 7 },
    anchor: "middle",
    horizontalOverflow: "clip",
  });
  table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount }).assign({
    fill: COLORS.navy,
    textStyle: {
      typeface: "Arial",
      fontSize: 15,
      bold: true,
      color: COLORS.white,
      alignment: "left",
    },
  });

  for (let row = 1; row < rowCount; row += 1) {
    const fill = row % 2 === 1 ? COLORS.white : COLORS.stripe;
    table.cells.block({ row, column: 0, rowCount: 1, columnCount }).assign({ fill });
    table.cells.block({ row, column: 0, rowCount: 1, columnCount: 1 }).assign({
      fill: spec.firstColumnFills?.[row - 1] ?? spec.accent,
      textStyle: {
        typeface: "Arial",
        fontSize: 15,
        bold: true,
        color: COLORS.white,
        alignment: spec.firstColumnFills ? "left" : "center",
      },
    });
  }

  for (const column of spec.centeredColumns ?? []) {
    table.cells.block({ row: 0, column, rowCount, columnCount: 1 }).assign({
      textStyle: {
        typeface: "Arial",
        fontSize: 15,
        bold: true,
        color: COLORS.white,
        alignment: "center",
      },
    });
    if (column !== 0) {
      table.cells.block({ row: 1, column, rowCount: rowCount - 1, columnCount: 1 }).assign({
        textStyle: {
          typeface: "Arial",
          fontSize: 15,
          bold: column === columnCount - 1,
          color: COLORS.text,
          alignment: "center",
        },
      });
    }
  }

  if (spec.values[0][columnCount - 1] === "Novelty") {
    for (let row = 1; row < rowCount; row += 1) {
      const rating = spec.values[row][columnCount - 1];
      const isHigh = rating === "High";
      table.cells.block({ row, column: columnCount - 1, rowCount: 1, columnCount: 1 }).assign({
        fill: isHigh ? COLORS.highFill : COLORS.moderateFill,
        textStyle: {
          typeface: "Arial",
          fontSize: 15,
          bold: true,
          color: isHigh ? COLORS.highText : COLORS.moderateText,
          alignment: "center",
        },
      });
    }
  }
}

function addStyledTable(slide, spec) {
  const existing = slide.tables.items.find((table) => table.name === spec.name);
  if (!existing) throw new Error(`Could not find ${spec.name}`);
  slide.tables.deleteById(existing.id);
  const table = slide.tables.add({
    rows: spec.values.length,
    columns: spec.values[0].length,
    left: 70,
    top: 160,
    width: 1140,
    height: 461,
    columnWidths: spec.widths,
    values: spec.values,
  });
  table.name = spec.name;
  styleTable(table, spec);
  table.rows[0].height = 52;
  const bodyHeight = (461 - 52) / (spec.values.length - 1);
  for (let row = 1; row < spec.values.length; row += 1) {
    table.rows[row].height = bodyHeight;
  }
  return table;
}

function addNoveltyToNotes(existing, slideNumber) {
  const summary = NOVELTY_SUMMARIES.get(slideNumber);
  if (!summary) return existing;
  const noveltyParagraph = `${NOVELTY_NOTE} ${summary}`;
  const sourceMarker = "\n\nSource:";
  if (existing.includes(sourceMarker)) {
    return existing.replace(sourceMarker, `\n\n${noveltyParagraph}${sourceMarker}`);
  }
  return `${existing.trim()}\n\n${noveltyParagraph}`;
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
    throw new Error(`Source deck changed before edit: ${sourceHash}`);
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
  if (slides.length !== EXPECTED_SLIDES) {
    throw new Error(`Expected ${EXPECTED_SLIDES} slides, found ${slides.length}`);
  }

  const notesSnapshot = parseNdjson(
    (await presentation.inspect({ kind: "notes", maxChars: 5000000 })).ndjson,
  );
  const notesBySlide = new Map(
    notesSnapshot
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text || ""]),
  );

  const beforeImages = new Map();
  for (const slideNumber of TABLE_SPECS.keys()) {
    const slide = slides[slideNumber - 1];
    const before = Buffer.from(
      await (await presentation.export({ slide, format: "png", scale: 1.5 })).arrayBuffer(),
    );
    beforeImages.set(slideNumber, before);
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-before.png`), before);
    addStyledTable(slide, TABLE_SPECS.get(slideNumber));
    if (slideNumber >= 54) {
      const updatedNotes = addNoveltyToNotes(notesBySlide.get(slideNumber) || "", slideNumber);
      slide.speakerNotes.textFrame.setText(updatedNotes);
      slide.speakerNotes.setVisible(true);
    }
    const after = Buffer.from(
      await (await presentation.export({ slide, format: "png", scale: 1.5 })).arrayBuffer(),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-after.png`), after);
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("Source changed during table editing");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const expectedChangedParts = [];
  for (const slideNumber of TABLE_SPECS.keys()) {
    const slidePart = `ppt/slides/slide${slideNumber}.xml`;
    const updatedSlideXml = await artifactZip.file(slidePart)?.async("string");
    if (!updatedSlideXml) throw new Error(`Missing ${slidePart} in artifact candidate`);
    sourceZip.file(slidePart, updatedSlideXml);
    expectedChangedParts.push(slidePart);
    if (slideNumber >= 54) {
      const notesPart = `ppt/notesSlides/notesSlide${slideNumber}.xml`;
      const updatedNotesXml = await artifactZip.file(notesPart)?.async("string");
      if (!updatedNotesXml) throw new Error(`Missing ${notesPart} in artifact candidate`);
      sourceZip.file(notesPart, updatedNotesXml);
      expectedChangedParts.push(notesPart);
    }
  }

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
    explicitTotalSlideCount: EXPECTED_SLIDES,
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

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalSlides = slidesFromPresentation(reopened);
  const tableSnapshot = parseNdjson(
    (await reopened.inspect({
      kind: "table",
      include: "id,slide,name,rows,cols,preview,bbox,bboxUnit",
      maxChars: 500000,
    })).ndjson,
  );
  for (const [slideNumber, spec] of TABLE_SPECS) {
    const record = tableSnapshot.find(
      (item) => item.kind === "table" && item.slide === slideNumber && item.name === spec.name,
    );
    if (!record) throw new Error(`Final table missing from slide ${slideNumber}`);
    if (record.rows !== spec.values.length || record.cols !== spec.values[0].length) {
      throw new Error(`Unexpected table dimensions on slide ${slideNumber}`);
    }
    const table = reopened.resolve(record.id);
    for (let row = 0; row < spec.values.length; row += 1) {
      for (let column = 0; column < spec.values[row].length; column += 1) {
        if (table.getCell(row, column).value !== spec.values[row][column]) {
          throw new Error(`Cell mismatch on slide ${slideNumber}, row ${row}, column ${column}`);
        }
      }
    }
    const finalImage = Buffer.from(
      await (
        await reopened.export({ slide: finalSlides[slideNumber - 1], format: "png", scale: 1.5 })
      ).arrayBuffer(),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-final.png`), finalImage);
    if (sha256(beforeImages.get(slideNumber)) === sha256(finalImage)) {
      throw new Error(`Slide ${slideNumber} did not change visually`);
    }
  }

  const finalNotes = parseNdjson(
    (await reopened.inspect({ kind: "notes", maxChars: 5000000 })).ndjson,
  );
  for (let slideNumber = 54; slideNumber <= 57; slideNumber += 1) {
    const text = finalNotes.find(
      (record) => record.kind === "notes" && record.slide === slideNumber,
    )?.text;
    if (!text?.includes(NOVELTY_NOTE) || !text.includes(NOVELTY_SUMMARIES.get(slideNumber))) {
      throw new Error(`Novelty explanation missing from slide ${slideNumber} notes`);
    }
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const actualChangedParts = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) actualChangedParts.push(name);
  }
  actualChangedParts.sort();
  expectedChangedParts.sort();
  if (
    actualChangedParts.length !== expectedChangedParts.length ||
    actualChangedParts.some((name, index) => name !== expectedChangedParts[index])
  ) {
    throw new Error(`Unexpected package changes: ${actualChangedParts.join(", ")}`);
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
        updatedSlides: [...TABLE_SPECS.keys()],
        noveltySlides: [...NOVELTY_SUMMARIES.keys()],
        changedParts: actualChangedParts,
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
