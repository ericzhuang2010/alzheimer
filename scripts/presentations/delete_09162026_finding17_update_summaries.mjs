#!/usr/bin/env node

/** Delete Finding 17 slides and remove Finding 17 from the summary tables. */

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
  "results/presentations/09162026_delete_finding17_20260922_v1",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_without_finding17_20260922_v1.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "41076865fb7d6ea7a9563318a6feb18ed9dcb77e8db18acf89548a2e91d91e25";
const SOURCE_SLIDE_COUNT = 160;
const FINAL_SLIDE_COUNT = 154;
const DELETE_COUNT = 6;

const COLORS = {
  navy: "#11263F",
  text: "#1F2D3D",
  border: "#D5DFE9",
  white: "#FFFFFF",
  stripe: "#F7FAFD",
  blue: "#0077B6",
  teal: "#00856F",
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
      top: 160,
      height: 430,
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
      ],
      firstColumnFills: [COLORS.blue, COLORS.teal],
      centeredColumns: [1],
    },
  ],
  [
    57,
    {
      name: "Summary 5 Table",
      top: 160,
      height: 430,
      widths: [80, 190, 470, 260, 140],
      values: [
        ["Finding", "Scope", "Summary", "Role", "Novelty"],
        [
          "7",
          "All six groups",
          "RPL11, RPS15, and related genes that help ribosomes outside mitochondria make proteins are connected to nuclear-encoded OXPHOS genes.",
          "Found across all six sex/APOE groups",
          "Moderate",
        ],
        [
          "10",
          "All six groups",
          "SELENOM, which helps control oxidative stress and calcium inside the endoplasmic reticulum, is connected to genes used for mitochondrial protein production.",
          "Found across all six sex/APOE groups",
          "High",
        ],
      ],
      accent: COLORS.purple,
      centeredColumns: [0, 4],
    },
  ],
]);

const TEXT_REPLACEMENTS = [
  {
    slide: 53,
    before: "How the 18 findings are organized",
    after: "How the remaining findings are organized",
  },
  {
    slide: 53,
    before:
      "The findings separate into pre-network expression and pathway results, results from KDA calls, and cross-cohort validation.",
    after: "The findings separate into DEG and pathway results and results from KDA calls.",
  },
  {
    slide: 53,
    before:
      "15 findings are tied to one or more sex/APOE groups. Findings 7, 10, and 17 are not sex/APOE-specific and receive lower priority in the sex/APOE narrative.",
    after:
      "15 findings are tied to one or more sex/APOE groups. Findings 7 and 10 are not sex/APOE-specific and receive lower priority in the sex/APOE narrative.",
  },
];

const NOTES_BY_SLIDE = new Map([
  [
    52,
    [
      "This section presents the remaining findings and explains how much weight to give each type of evidence.",
      "",
      "The next five slides provide a map before the detailed findings begin. Findings 1–6 summarize DEG and pathway results. Findings 7–16 and 18 summarize genes returned from KDA calls.",
      "",
      "Keep the evidence levels separate. DEG and pathway results describe gene-expression patterns, while KDA calls nominate network candidates. Human validation remains supporting evidence within the relevant findings rather than a separate finding. None of these analyses alone establishes causality or mitochondrial function.",
      "",
      "Next, review how the remaining findings are organized.",
    ].join("\n"),
  ],
  [
    53,
    [
      "The remaining findings fall into two categories.",
      "",
      "Findings 1–6 are the primary DEG and pathway results. They ask how mitochondrial genes and pathways change within each analyzed sex/APOE group before making KDA calls.",
      "",
      "Findings 7–16 and 18 come from KDA calls made with MitoCarta MT DEGs. These calls return candidate genes that may help explain the mitochondrial changes. KDA does not show that a candidate gene causes or drives the change. That remains a hypothesis for follow-up.",
      "",
      "Fifteen findings are linked to one or more analyzed sex/APOE groups. Findings 7 and 10 recur across all six groups and therefore do not distinguish a particular group. They receive lower priority in this sex/APOE-focused presentation.",
      "",
      "A result found in selected groups does not by itself prove a statistical sex or APOE interaction.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 1–16 and 18.",
    ].join("\n"),
  ],
  [
    57,
    [
      "Findings 7 and 10 receive lower priority only because this presentation focuses on differences among sex/APOE groups.",
      "",
      "For both findings, found across all six sex/APOE groups means that the related pattern appeared in one or more KDA calls for every group. It does not mean that every individual fine-cell KDA call returned the same genes.",
      "",
      "Finding 7 links RPL11, RPS15, and related genes that help ribosomes outside mitochondria make proteins with nuclear-encoded OXPHOS genes.",
      "",
      "Finding 10 links SELENOM with genes used for mitochondrial protein production. SELENOM helps control oxidative stress and calcium inside the endoplasmic reticulum, the cellular compartment where many proteins are processed.",
      "",
      "These findings may still be biologically important. They simply do not identify a distinct sex/APOE group.",
      "",
      "Novelty is provisional and separate from evidence strength. Finding 7 is rated Moderate, and Finding 10 is rated High.",
      "",
      "Source: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Findings 7 and 10.",
    ].join("\n"),
  ],
  [
    154,
    [
      "Teaching goal: Explain the evidence supporting the female epsilon-4 vascular stress-response result.",
      "",
      "Walk through: The current pathway test shows that female epsilon-4 vascular KDA calls returned several genes controlled by HSF1, a regulator of the cellular response to damaged or misfolded proteins. Guo and colleagues support analyzing AD networks separately by cell type and sex. Mathys and colleagues show that AD-related gene expression differs among brain cell populations. Those studies support the analysis strategy, but they do not independently report this particular group of vascular stress-response genes. The slide assigns moderate novelty to the result.",
      "",
      "Scientific boundary: The result depends on only three related genes from two KDA calls. It should therefore be treated as a focused hypothesis rather than a broadly established vascular response.",
      "",
      "Transition: This concludes the detailed findings.",
      "",
      "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    ].join("\n"),
  ],
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

function relationshipAttributes(tag) {
  return Object.fromEntries(
    [...tag.matchAll(/([A-Za-z:]+)="([^"]*)"/g)].map((match) => [match[1], match[2]]),
  );
}

function relationships(xml) {
  return [...xml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map((match) => ({
    tag: match[0],
    attrs: relationshipAttributes(match[0]),
  }));
}

function normalizePart(basePart, target) {
  if (target.startsWith("/")) return target.slice(1);
  return path.posix.normalize(path.posix.join(path.posix.dirname(basePart), target));
}

async function visibleSlidePart(zip, ordinal) {
  const presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  const presentationRels = await zip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  if (!presentationXml || !presentationRels) {
    throw new Error("Presentation ordering metadata is missing");
  }
  const slideIds = [
    ...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g),
  ].map((match) => match[1]);
  const relationshipId = slideIds[ordinal - 1];
  if (!relationshipId) throw new Error(`Visible slide ${ordinal} was not found`);
  const relation = relationships(presentationRels).find(
    (item) => item.attrs.Id === relationshipId && item.attrs.Type?.endsWith("/slide"),
  );
  if (!relation?.attrs.Target) {
    throw new Error(`Slide relationship ${relationshipId} was not found`);
  }
  return normalizePart("ppt/presentation.xml", relation.attrs.Target);
}

async function notesPartForSlide(zip, slidePart) {
  const relsPath = path.posix.join(
    path.posix.dirname(slidePart),
    "_rels",
    `${path.posix.basename(slidePart)}.rels`,
  );
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing slide relationships: ${relsPath}`);
  const relation = relationships(relsXml).find((item) =>
    item.attrs.Type?.endsWith("/notesSlide"),
  );
  if (!relation?.attrs.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return normalizePart(slidePart, relation.attrs.Target);
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
    table.cells.block({ row, column: 0, rowCount: 1, columnCount }).assign({
      fill: row % 2 === 1 ? COLORS.white : COLORS.stripe,
    });
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
    table.cells.block({ row: 0, column, rowCount: 1, columnCount: 1 }).assign({
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
      const isHigh = spec.values[row][columnCount - 1] === "High";
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

function replaceTable(slide, spec) {
  const existing = slide.tables.items.find((table) => table.name === spec.name);
  if (!existing) throw new Error(`Could not find ${spec.name}`);
  slide.tables.deleteById(existing.id);
  const table = slide.tables.add({
    rows: spec.values.length,
    columns: spec.values[0].length,
    left: 70,
    top: spec.top,
    width: 1140,
    height: spec.height,
    columnWidths: spec.widths,
    values: spec.values,
  });
  table.name = spec.name;
  styleTable(table, spec);
  table.rows[0].height = 52;
  const bodyHeight = (spec.height - 52) / (spec.values.length - 1);
  for (let row = 1; row < spec.values.length; row += 1) {
    table.rows[row].height = bodyHeight;
  }
}

function updateAppProperties(xml) {
  let updated = xml
    .replace(`<Slides>${SOURCE_SLIDE_COUNT}</Slides>`, `<Slides>${FINAL_SLIDE_COUNT}</Slides>`)
    .replace(`<Notes>${SOURCE_SLIDE_COUNT}</Notes>`, `<Notes>${FINAL_SLIDE_COUNT}</Notes>`)
    .replace(
      `<vt:lpstr>Slide Titles</vt:lpstr></vt:variant><vt:variant><vt:i4>${SOURCE_SLIDE_COUNT}</vt:i4>`,
      `<vt:lpstr>Slide Titles</vt:lpstr></vt:variant><vt:variant><vt:i4>${FINAL_SLIDE_COUNT}</vt:i4>`,
    )
    .replace(
      `<TitlesOfParts><vt:vector size="${SOURCE_SLIDE_COUNT + 3}"`,
      `<TitlesOfParts><vt:vector size="${FINAL_SLIDE_COUNT + 3}"`,
    );
  const title = "<vt:lpstr>PowerPoint Presentation</vt:lpstr>";
  for (let index = 0; index < DELETE_COUNT; index += 1) {
    const position = updated.lastIndexOf(title);
    if (position < 0) throw new Error("Could not trim TitlesOfParts in app.xml");
    updated = `${updated.slice(0, position)}${updated.slice(position + title.length)}`;
  }
  return updated;
}

async function deleteTrailingFindingSlides(zip) {
  let presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  let presentationRels = await zip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  let contentTypes = await zip.file("[Content_Types].xml")?.async("string");
  let appXml = await zip.file("docProps/app.xml")?.async("string");
  if (!presentationXml || !presentationRels || !contentTypes || !appXml) {
    throw new Error("Required package metadata is missing");
  }

  const slideTags = [
    ...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g),
  ].map((match) => ({ tag: match[0], relationshipId: match[1] }));
  if (slideTags.length !== SOURCE_SLIDE_COUNT) {
    throw new Error(`Expected ${SOURCE_SLIDE_COUNT} slide ids, found ${slideTags.length}`);
  }
  const deleteTags = slideTags.slice(-DELETE_COUNT);
  const presentationRelationships = relationships(presentationRels);
  const deletedParts = [];
  const deletedSlideParts = [];

  for (const item of deleteTags) {
    const relation = presentationRelationships.find(
      (candidate) =>
        candidate.attrs.Id === item.relationshipId &&
        candidate.attrs.Type?.endsWith("/slide"),
    );
    if (!relation?.attrs.Target) {
      throw new Error(`Missing presentation relationship ${item.relationshipId}`);
    }
    const slidePart = normalizePart("ppt/presentation.xml", relation.attrs.Target);
    const slideXml = await zip.file(slidePart)?.async("string");
    if (!slideXml) throw new Error(`Missing slide part ${slidePart}`);
    const slideNumber = Number(path.posix.basename(slidePart).match(/slide(\d+)\.xml/)?.[1]);
    if (!Number.isInteger(slideNumber) || slideNumber < 155 || slideNumber > 160) {
      throw new Error(`Unexpected trailing slide selected for deletion: ${slidePart}`);
    }
    deletedSlideParts.push(slidePart);

    const slideRelsPart = path.posix.join(
      path.posix.dirname(slidePart),
      "_rels",
      `${path.posix.basename(slidePart)}.rels`,
    );
    const notesPart = await notesPartForSlide(zip, slidePart);
    const notesRelsPart = path.posix.join(
      path.posix.dirname(notesPart),
      "_rels",
      `${path.posix.basename(notesPart)}.rels`,
    );

    presentationXml = presentationXml.replace(item.tag, "");
    presentationRels = presentationRels.replace(relation.tag, "");
    for (const part of [slidePart, slideRelsPart, notesPart, notesRelsPart]) {
      if (!zip.file(part)) throw new Error(`Expected package part is missing: ${part}`);
      zip.remove(part);
      deletedParts.push(part);
    }

    for (const part of [slidePart, notesPart]) {
      const partName = `/${part}`;
      const override = [...contentTypes.matchAll(/<Override\b[^>]*\/?\s*>/g)]
        .map((match) => match[0])
        .find((tag) => relationshipAttributes(tag).PartName === partName);
      if (!override) throw new Error(`Missing content-type override for ${partName}`);
      contentTypes = contentTypes.replace(override, "");
    }
  }

  appXml = updateAppProperties(appXml);
  zip.file("ppt/presentation.xml", presentationXml);
  zip.file("ppt/_rels/presentation.xml.rels", presentationRels);
  zip.file("[Content_Types].xml", contentTypes);
  zip.file("docProps/app.xml", appXml);

  return {
    deletedParts,
    deletedSlideParts,
    changedMetadataParts: [
      "[Content_Types].xml",
      "docProps/app.xml",
      "ppt/_rels/presentation.xml.rels",
      "ppt/presentation.xml",
    ],
  };
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
  if (slides.length !== SOURCE_SLIDE_COUNT) {
    throw new Error(`Expected ${SOURCE_SLIDE_COUNT} slides, found ${slides.length}`);
  }

  const snapshot = parseNdjson(
    (await presentation.inspect({ kind: "textbox,notes", maxChars: 6000000 })).ndjson,
  );
  for (const replacement of TEXT_REPLACEMENTS) {
    const matches = snapshot.filter(
      (record) =>
        record.kind === "textbox" &&
        record.slide === replacement.slide &&
        record.text === replacement.before,
    );
    if (matches.length !== 1) {
      throw new Error(
        `Expected one text match on slide ${replacement.slide}, found ${matches.length}`,
      );
    }
    presentation.resolve(matches[0].id).text.replace(replacement.before, replacement.after);
  }

  for (const [slideNumber, spec] of TABLE_SPECS) {
    replaceTable(slides[slideNumber - 1], spec);
  }
  for (const [slideNumber, revisedNotes] of NOTES_BY_SLIDE) {
    slides[slideNumber - 1].speakerNotes.textFrame.setText(revisedNotes);
    slides[slideNumber - 1].speakerNotes.setVisible(true);
  }

  for (const slideNumber of [53, 57]) {
    const image = Buffer.from(
      await (
        await presentation.export({ slide: slides[slideNumber - 1], format: "png", scale: 1.5 })
      ).arrayBuffer(),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-edited.png`), image);
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("Source changed during summary editing");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const changedParts = [];

  for (const slideNumber of [53, 57]) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const updatedSlideXml = await artifactZip.file(artifactSlidePart)?.async("string");
    if (!updatedSlideXml) throw new Error(`Updated slide XML is missing for slide ${slideNumber}`);
    sourceZip.file(sourceSlidePart, updatedSlideXml);
    changedParts.push(sourceSlidePart);
  }

  for (const slideNumber of NOTES_BY_SLIDE.keys()) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const updatedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!updatedNotesXml) throw new Error(`Updated notes are missing for slide ${slideNumber}`);
    sourceZip.file(sourceNotesPart, updatedNotesXml);
    changedParts.push(sourceNotesPart);
  }

  const deletion = await deleteTrailingFindingSlides(sourceZip);
  changedParts.push(...deletion.changedMetadataParts);

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
    explicitTotalSlideCount: FINAL_SLIDE_COUNT,
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
  if (finalSlides.length !== FINAL_SLIDE_COUNT) {
    throw new Error(`Final deck has ${finalSlides.length} slides`);
  }

  const finalSnapshot = parseNdjson(
    (await reopened.inspect({ kind: "slide,textbox,table,notes", maxChars: 8000000 })).ndjson,
  );
  const remainingFinding17 = finalSnapshot.filter(
    (record) =>
      typeof record.text === "string" &&
      /Finding\s*17|finding\s*17/.test(record.text),
  );
  if (remainingFinding17.length) {
    throw new Error(
      `Finding 17 remains in final deck on slides: ${[
        ...new Set(remainingFinding17.map((record) => record.slide)),
      ].join(", ")}`,
    );
  }

  for (const [slideNumber, spec] of TABLE_SPECS) {
    const tableRecord = finalSnapshot.find(
      (record) =>
        record.kind === "table" &&
        record.slide === slideNumber &&
        record.name === spec.name,
    );
    if (!tableRecord) throw new Error(`Final table is missing from slide ${slideNumber}`);
    if (tableRecord.rows !== spec.values.length || tableRecord.cols !== spec.values[0].length) {
      throw new Error(`Unexpected table dimensions on slide ${slideNumber}`);
    }
    const table = reopened.resolve(tableRecord.id);
    for (let row = 0; row < spec.values.length; row += 1) {
      for (let column = 0; column < spec.values[row].length; column += 1) {
        if (table.getCell(row, column).value !== spec.values[row][column]) {
          throw new Error(`Cell mismatch on slide ${slideNumber}, row ${row}, column ${column}`);
        }
      }
    }
  }

  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  for (const part of deletion.deletedParts) {
    if (finalZip.file(part)) throw new Error(`Deleted part remains in final deck: ${part}`);
  }
  const finalPresentationXml = await finalZip.file("ppt/presentation.xml")?.async("string");
  const finalSlideIdCount = [
    ...(finalPresentationXml || "").matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g),
  ].length;
  if (finalSlideIdCount !== FINAL_SLIDE_COUNT) {
    throw new Error(`Final presentation XML contains ${finalSlideIdCount} slide ids`);
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const actualChanged = [];
  const actualDeleted = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) {
      actualDeleted.push(name);
      continue;
    }
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) actualChanged.push(name);
  }
  actualChanged.sort();
  actualDeleted.sort();
  const expectedChanged = [...new Set(changedParts)].sort();
  const expectedDeleted = [...deletion.deletedParts].sort();
  if (
    actualChanged.length !== expectedChanged.length ||
    actualChanged.some((name, index) => name !== expectedChanged[index])
  ) {
    throw new Error(`Unexpected changed package parts: ${actualChanged.join(", ")}`);
  }
  if (
    actualDeleted.length !== expectedDeleted.length ||
    actualDeleted.some((name, index) => name !== expectedDeleted[index])
  ) {
    throw new Error(`Unexpected deleted package parts: ${actualDeleted.join(", ")}`);
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
        removedSlides: [155, 156, 157, 158, 159, 160],
        finalSlideCount: FINAL_SLIDE_COUNT,
        updatedSummarySlides: [53, 57],
        updatedNotesSlides: [...NOTES_BY_SLIDE.keys()],
        changedParts: actualChanged,
        deletedParts: actualDeleted,
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
