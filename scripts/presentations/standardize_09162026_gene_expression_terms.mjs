#!/usr/bin/env node

/** Replace RNA shorthand with gene-expression terminology where the deck reports DEG direction. */

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
  "results/presentations/09162026_gene_expression_terminology_20260919/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_gene_expression_terminology_20260919/output/09162026_sex_apoe_kda_fine_broad_gene_expression_terms_20260919.pptx",
);
const EXPECTED_SLIDES = 160;

const TEXT_UPDATES = [
  {
    slide: 43,
    name: "TextBox 1",
    oldText:
      "Female ε3/ε3 cells (especially excitatory neurons) raise mtDNA OXPHOS-gene RNA in AD",
    newText:
      "Female ε3/ε3 cells show higher mtDNA-encoded OXPHOS gene expression in AD",
  },
  {
    slide: 43,
    name: "TextBox 17",
    oldText: "more mtDNA-OXPHOS RNA\nin AD than in the comparison group",
    newText:
      "higher expression of mtDNA-encoded OXPHOS genes\nin AD than in the comparison group",
  },
  {
    slide: 43,
    name: "TextBox 19",
    oldText:
      "Nuclear OXPHOS RNA also mostly rises in ROSMAP, but cross-cohort support is strongest for mtDNA OXPHOS.",
    newText:
      "Nuclear-encoded OXPHOS gene expression also rises in ROSMAP, but cross-cohort support is strongest for mtDNA-encoded genes.",
  },
  {
    slide: 46,
    name: "TextBox 17",
    oldText:
      "mtDNA OXPHOS rises in ROSMAP and SEA-AD. Nuclear OXPHOS also mostly rises in ROSMAP.",
    newText:
      "mtDNA-encoded OXPHOS genes are mostly upregulated in both cohorts. Nuclear-encoded genes are also mostly upregulated in ROSMAP.",
  },
  {
    slide: 46,
    name: "TextBox 20",
    oldText:
      "The increase may be compensation or a stress response. It is not an evidence that mitochondria make more ATP.",
    newText:
      "The increase may be compensation or a stress response. It is not evidence that mitochondria make more ATP.",
  },
  {
    slide: 49,
    name: "TextBox 1",
    oldText:
      "Male ε3/ε3 cells raise mtDNA energy-gene RNA while lowering nuclear energy-gene RNA",
    newText:
      "Male ε3/ε3 cells show opposite directions in OXPHOS gene expression",
  },
  {
    slide: 49,
    name: "TextBox 14",
    oldText: "mtDNA-OXPHOS RNA\nmostly increases in AD",
    newText: "mtDNA-encoded OXPHOS gene expression\nmostly increases in AD",
  },
  {
    slide: 49,
    name: "TextBox 18",
    oldText: "nuclear OXPHOS RNA\nmostly decreases in AD",
    newText: "nuclear-encoded OXPHOS gene expression\nmostly decreases in AD",
  },
  {
    slide: 49,
    name: "TextBox 20",
    oldText:
      "Plain meaning: RNA instructions for two matching sets of respiratory parts move in opposite directions.",
    newText:
      "Plain meaning: the two sets of respiratory genes show opposite expression directions.",
  },
  {
    slide: 50,
    name: "TextBox 1",
    oldText: "ROSMAP: male ε3/ε3 cells show opposite OXPHOS RNA directions",
    newText:
      "ROSMAP: male ε3/ε3 cells show opposite directions in OXPHOS gene expression",
  },
  {
    slide: 50,
    name: "TextBox 28",
    oldText:
      "Enriched = more program genes than expected in a KDA input query (BH < 0.05), not the number of genes returned from KDA calls.",
    newText:
      "Enriched = more pathway genes than expected in a KDA input query (BH < 0.05), not the number of genes returned from KDA calls.",
  },
  {
    slide: 53,
    name: "TextBox 2",
    oldText:
      "Opposite RNA directions could challenge coordination, but the functional outcome remains unknown.",
    newText:
      "Opposite directions in OXPHOS gene expression could challenge coordination, but the functional outcome remains unknown.",
  },
  {
    slide: 53,
    name: "TextBox 20",
    oldText:
      "This is an RNA-level mitonuclear mismatch—not proof that respiratory proteins or ATP production are unbalanced.",
    newText:
      "This is an RNA-level difference between the two OXPHOS gene sets, not proof that respiratory proteins or ATP production are unbalanced.",
  },
  {
    slide: 56,
    name: "TextBox 20",
    oldText:
      "Both mitochondrial and nuclear OXPHOS RNA mostly increased in female ε2 cells.",
    newText:
      "Both mtDNA-encoded and nuclear-encoded OXPHOS genes were mostly upregulated in female ε2 cells.",
  },
  {
    slide: 57,
    name: "TextBox 1",
    oldText: "Female ε2 cells raise both mitochondrial and nuclear OXPHOS RNA in AD",
    newText:
      "Female ε2 cells show higher expression of both OXPHOS gene sets in AD",
  },
  {
    slide: 57,
    name: "TextBox 21",
    oldText: "Coordinated RNA",
    newText: "Coordinated gene expression",
  },
  {
    slide: 57,
    name: "TextBox 22",
    oldText:
      "Both instruction sets rise together. Protein assembly and ATP remain unmeasured.",
    newText:
      "Both gene sets are upregulated together. Protein assembly and ATP remain unmeasured.",
  },
  {
    slide: 57,
    name: "TextBox 24",
    oldText:
      "This is a coordinated transcriptional response, not evidence that mitochondria produce more energy.",
    newText:
      "This coordinated expression pattern does not show that mitochondria produce more energy.",
  },
  {
    slide: 60,
    name: "TextBox 14",
    oldText:
      "Population-level ε2 protection does not make this RNA pattern protective by itself.",
    newText:
      "Population-level ε2 protection does not make this gene-expression pattern protective by itself.",
  },
  {
    slide: 62,
    name: "TextBox 9",
    oldText: "Does not explain the observed female ε2 RNA response.",
    newText: "Does not explain the observed expression pattern in female ε2 cells.",
  },
  {
    slide: 63,
    name: "TextBox 20",
    oldText:
      "The strongest signal is a fine-cell decrease in nuclear-encoded OXPHOS RNA.",
    newText:
      "The strongest signal is lower expression of nuclear-encoded OXPHOS genes in fine-cell results.",
  },
  {
    slide: 64,
    name: "TextBox 1",
    oldText:
      "Female ε4 fine-cell results lower nuclear-encoded OXPHOS RNA in AD",
    newText:
      "Female ε4 fine-cell results show lower nuclear-encoded OXPHOS gene expression in AD",
  },
  {
    slide: 67,
    name: "TextBox 6",
    oldText:
      "A broad RNA decrease could affect the supply of respiratory-complex parts.",
    newText:
      "Lower expression across many nuclear-encoded OXPHOS genes could reduce the supply of respiratory-complex parts.",
  },
  {
    slide: 70,
    name: "TextBox 20",
    oldText:
      "Both mtDNA and nuclear OXPHOS RNA are broadly lower, but query size strongly affects KDA yield.",
    newText:
      "Both OXPHOS gene sets show lower expression, but query size strongly affects KDA yield.",
  },
  {
    slide: 71,
    name: "TextBox 1",
    oldText: "Male ε2 cells lower both mitochondrial and nuclear OXPHOS RNA in AD",
    newText:
      "Male ε2 cells show lower expression of both OXPHOS gene sets in AD",
  },
  {
    slide: 71,
    name: "TextBox 24",
    oldText:
      "An ε2 allele can be protective at the population level while diseased tissue still shows an unfavorable-looking RNA pattern.",
    newText:
      "An ε2 allele can be protective at the population level while diseased tissue still shows lower OXPHOS gene expression.",
  },
  {
    slide: 78,
    name: "TextBox 1",
    oldText:
      "Male ε4 cells may separate mitochondrial and nuclear OXPHOS RNA directions",
    newText:
      "Male ε4 cells may show opposite directions in OXPHOS gene expression",
  },
  {
    slide: 78,
    name: "TextBox 14",
    oldText: "mtDNA-encoded OXPHOS RNA mostly increases in AD.",
    newText: "mtDNA-encoded OXPHOS gene expression mostly increases in AD.",
  },
  {
    slide: 78,
    name: "TextBox 18",
    oldText:
      "Nuclear structural OXPHOS RNA leans downward, but less strongly.",
    newText:
      "Nuclear-encoded structural OXPHOS gene expression tends to decrease, but less consistently.",
  },
  {
    slide: 83,
    name: "TextBox 9",
    oldText: "Risk association does not validate the RNA mismatch.",
    newText: "Risk association does not validate the gene-expression mismatch.",
  },
  {
    slide: 93,
    name: "TextBox 18",
    oldText: "Most structural OXPHOS overlaps point toward lower RNA in AD",
    newText: "Most structural OXPHOS overlaps show lower gene expression in AD",
  },
  {
    slide: 106,
    name: "TextBox 22",
    oldText:
      "The exact network neighborhood connects the ER candidate with lower mitochondrial protein-production RNA.",
    newText:
      "The exact network neighborhood connects the ER candidate with lower expression of mitochondrial translation genes.",
  },
  {
    slide: 107,
    name: "TextBox 18",
    oldText: "Most mitochondrial-translation overlaps have lower RNA in AD",
    newText: "Most mitochondrial-translation overlaps show lower gene expression in AD",
  },
  {
    slide: 143,
    name: "TextBox 6",
    oldText: "The female ε2 astrocyte KDA call shows higher APOE RNA in AD.",
    newText: "The female ε2 astrocyte KDA call shows higher APOE expression in AD.",
  },
  {
    slide: 143,
    name: "TextBox 10",
    oldText:
      "The male ε2 and male ε4 astrocyte KDA calls show lower APOE RNA in AD.",
    newText:
      "The male ε2 and male ε4 astrocyte KDA calls show lower APOE expression in AD.",
  },
  {
    slide: 144,
    name: "TextBox 10",
    oldText: "APOE RNA may reflect different astrocyte states or responses to pathology.",
    newText: "APOE expression may reflect different astrocyte states or responses to pathology.",
  },
];

function normalizeNotes(text) {
  let revised = text;
  const replacements = [
    [
      "Both mitochondrial and nuclear OXPHOS RNA mostly increased",
      "Expression of both mtDNA-encoded and nuclear-encoded OXPHOS genes mostly increased",
    ],
    [
      "Both mtDNA and nuclear OXPHOS RNA are broadly lower",
      "Expression of both mtDNA-encoded and nuclear-encoded OXPHOS genes is broadly lower",
    ],
    [
      "mitochondrial-DNA-encoded OXPHOS RNA",
      "expression of mitochondrial-DNA-encoded OXPHOS genes",
    ],
    [
      "mitochondrial-DNA OXPHOS RNA",
      "expression of mitochondrial-DNA-encoded OXPHOS genes",
    ],
    ["Nuclear-encoded OXPHOS RNA", "Expression of nuclear-encoded OXPHOS genes"],
    ["nuclear-encoded OXPHOS RNA", "expression of nuclear-encoded OXPHOS genes"],
    ["Nuclear OXPHOS RNA", "Expression of nuclear-encoded OXPHOS genes"],
    ["nuclear OXPHOS RNA", "expression of nuclear-encoded OXPHOS genes"],
    ["mtDNA OXPHOS RNA", "expression of mtDNA-encoded OXPHOS genes"],
    ["Opposite RNA directions", "Opposite directions in gene expression"],
    ["opposite RNA directions", "opposite directions in gene expression"],
    ["RNA mismatch", "gene-expression mismatch"],
    ["unfavorable-looking RNA pattern", "downward OXPHOS gene-expression pattern"],
    ["female ε2 RNA response", "expression pattern in female ε2 cells"],
    ["coordinated transcriptional response", "coordinated gene-expression pattern"],
  ];
  for (const [before, after] of replacements) revised = revised.replaceAll(before, after);
  return revised;
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

function parseNdjson(ndjson) {
  return (ndjson || "")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function relationshipAttributes(tag) {
  return Object.fromEntries(
    [...tag.matchAll(/([A-Za-z:]+)="([^"]*)"/g)].map((match) => [match[1], match[2]]),
  );
}

function relationshipPartPath(ownerPartPath) {
  return path.posix.join(
    path.posix.dirname(ownerPartPath),
    "_rels",
    `${path.posix.basename(ownerPartPath)}.rels`,
  );
}

function targetPartPath(ownerPartPath, target) {
  if (target.startsWith("/")) return target.slice(1);
  return path.posix.normalize(path.posix.join(path.posix.dirname(ownerPartPath), target));
}

async function orderedSlidePartPaths(zip) {
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
  const relationships = [
    ...presentationRels.matchAll(/<Relationship\b[^>]*\/?\s*>/g),
  ].map((match) => relationshipAttributes(match[0]));
  return slideIds.map((relationshipId) => {
    const relation = relationships.find(
      (item) => item.Id === relationshipId && item.Type?.endsWith("/slide"),
    );
    if (!relation?.Target) throw new Error(`Slide relationship ${relationshipId} was not found`);
    return relation.Target.startsWith("/")
      ? relation.Target.slice(1)
      : path.posix.normalize(path.posix.join("ppt", relation.Target));
  });
}

async function notesPartForSlide(zip, slidePart) {
  const relsXml = await zip.file(relationshipPartPath(slidePart))?.async("string");
  if (!relsXml) throw new Error(`Missing slide relationships: ${slidePart}`);
  const relationships = [...relsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map(
    (match) => relationshipAttributes(match[0]),
  );
  const relation = relationships.find((item) => item.Type?.endsWith("/notesSlide"));
  if (!relation?.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return targetPartPath(slidePart, relation.Target);
}

async function remapSlideRelationshipIds({
  sourceZip,
  artifactZip,
  sourceSlidePart,
  artifactSlidePart,
  artifactSlideXml,
}) {
  const sourceRelsXml = await sourceZip
    .file(relationshipPartPath(sourceSlidePart))
    ?.async("string");
  const artifactRelsXml = await artifactZip
    .file(relationshipPartPath(artifactSlidePart))
    ?.async("string");
  if (!sourceRelsXml || !artifactRelsXml) {
    throw new Error(`Missing relationships for ${sourceSlidePart}`);
  }
  const sourceRelationships = [
    ...sourceRelsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g),
  ].map((match) => relationshipAttributes(match[0]));
  const artifactRelationships = [
    ...artifactRelsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g),
  ].map((match) => relationshipAttributes(match[0]));
  let remapped = artifactSlideXml;
  for (const artifactRelation of artifactRelationships) {
    if (!artifactRelation.Id || !artifactRelation.Type || !artifactRelation.Target) continue;
    const artifactTarget = targetPartPath(artifactSlidePart, artifactRelation.Target);
    const sourceRelation = sourceRelationships.find(
      (item) =>
        item.Type === artifactRelation.Type &&
        item.Target &&
        targetPartPath(sourceSlidePart, item.Target) === artifactTarget,
    );
    if (!sourceRelation?.Id) {
      throw new Error(
        `Could not map ${artifactRelation.Id} (${artifactRelation.Type}) on ${sourceSlidePart}`,
      );
    }
    remapped = remapped.replaceAll(artifactRelation.Id, sourceRelation.Id);
  }
  return remapped;
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

  const updatedSlideNumbers = [...new Set(TEXT_UPDATES.map((update) => update.slide))].sort(
    (a, b) => a - b,
  );
  const beforePngs = new Map();
  for (const slideNumber of updatedSlideNumbers) {
    const png = await blobBuffer(
      await presentation.export({ slide: slides[slideNumber - 1], format: "png", scale: 2 }),
    );
    beforePngs.set(slideNumber, png);
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-before.png`), png);
  }

  const snapshot = await presentation.inspect({
    kind: "textbox",
    include: "id,slide,name,text,bbox",
    maxChars: 4000000,
  });
  const textboxes = parseNdjson(snapshot.ndjson).filter(
    (record) => record.kind === "textbox" && typeof record.text === "string",
  );
  for (const update of TEXT_UPDATES) {
    const matches = textboxes.filter(
      (record) => record.slide === update.slide && record.name === update.name,
    );
    if (matches.length !== 1) {
      throw new Error(
        `Expected one ${update.name} on slide ${update.slide}, found ${matches.length}`,
      );
    }
    if (matches[0].text !== update.oldText) {
      throw new Error(
        `Unexpected source text on slide ${update.slide} ${update.name}: ${JSON.stringify(matches[0].text)}`,
      );
    }
    presentation.resolve(matches[0].id).text.replace(update.oldText, update.newText);
  }

  const expectedNotesBySlide = new Map();
  for (let index = 0; index < slides.length; index += 1) {
    const slide = slides[index];
    const currentNotes = slide.speakerNotes.textFrame.paragraphs.toPlainText();
    const revisedNotes = normalizeNotes(currentNotes);
    if (revisedNotes !== currentNotes) {
      slide.speakerNotes.textFrame.setText(revisedNotes);
      slide.speakerNotes.setVisible(true);
      expectedNotesBySlide.set(index + 1, revisedNotes);
    }
  }

  for (const slideNumber of updatedSlideNumbers) {
    const png = await blobBuffer(
      await presentation.export({ slide: slides[slideNumber - 1], format: "png", scale: 2 }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-after.png`), png);
    if (sha256(beforePngs.get(slideNumber)) === sha256(png)) {
      throw new Error(`Visible slide ${slideNumber} did not change`);
    }
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  const currentSourceBuffer = await fs.readFile(SOURCE);
  if (sha256(currentSourceBuffer) !== sourceHash) {
    throw new Error("The source presentation changed during the edit");
  }

  const sourceZip = await JSZip.loadAsync(currentSourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const sourceSlideParts = await orderedSlidePartPaths(sourceZip);
  const artifactSlideParts = await orderedSlidePartPaths(artifactZip);
  const changedPartsExpected = new Set();

  for (const slideNumber of updatedSlideNumbers) {
    const sourceSlidePart = sourceSlideParts[slideNumber - 1];
    const artifactSlidePart = artifactSlideParts[slideNumber - 1];
    const artifactSlideXml = await artifactZip.file(artifactSlidePart)?.async("string");
    if (!artifactSlideXml) throw new Error(`Missing revised slide XML: ${artifactSlidePart}`);
    const revisedSlideXml = await remapSlideRelationshipIds({
      sourceZip,
      artifactZip,
      sourceSlidePart,
      artifactSlidePart,
      artifactSlideXml,
    });
    sourceZip.file(sourceSlidePart, revisedSlideXml);
    changedPartsExpected.add(sourceSlidePart);
  }

  for (const slideNumber of expectedNotesBySlide.keys()) {
    const sourceSlidePart = sourceSlideParts[slideNumber - 1];
    const artifactSlidePart = artifactSlideParts[slideNumber - 1];
    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const revisedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!revisedNotesXml) throw new Error(`Missing revised notes XML: ${artifactNotesPart}`);
    sourceZip.file(sourceNotesPart, revisedNotesXml);
    changedPartsExpected.add(sourceNotesPart);
  }

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
    await sourceZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const validation = await finalizePresentation({
    explicitTotalSlideCount: EXPECTED_SLIDES,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [13],
    requiredEmbeddedWorkbookChartOwnerSlides: [13],
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
    ],
    fontPolicy: {
      basis: "reference",
      families: ["Arial"],
      referencePath: SOURCE,
      referenceSha256: sourceHash,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD_DIR, "gene-expression-terminology.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const finalSnapshot = await reopened.inspect({
    kind: "textbox,notes",
    include: "id,slide,name,text,bbox",
    maxChars: 5000000,
  });
  const finalRecords = parseNdjson(finalSnapshot.ndjson);
  for (const update of TEXT_UPDATES) {
    const matches = finalRecords.filter(
      (record) =>
        record.kind === "textbox" &&
        record.slide === update.slide &&
        record.name === update.name,
    );
    if (matches.length !== 1 || matches[0].text !== update.newText) {
      throw new Error(`Final text mismatch on slide ${update.slide} ${update.name}`);
    }
  }

  const finalNotesBySlide = new Map(
    finalRecords
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text]),
  );
  for (const [slideNumber, expectedNotes] of expectedNotesBySlide) {
    if (finalNotesBySlide.get(slideNumber)?.trim() !== expectedNotes.trim()) {
      throw new Error(`Final notes mismatch on slide ${slideNumber}`);
    }
  }

  for (const slideNumber of updatedSlideNumbers) {
    const finalPng = await blobBuffer(
      await reopened.export({
        slide: reopenedSlides[slideNumber - 1],
        format: "png",
        scale: 2,
      }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-final.png`), finalPng);
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const changedParts = [];
  for (const name of Object.keys(originalZip.files).filter((item) => !originalZip.files[item].dir)) {
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [sourceData, finalData] = await Promise.all([
      originalZip.file(name).async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(sourceData) !== sha256(finalData)) changedParts.push(name);
  }
  changedParts.sort();
  const expectedChangedParts = [...changedPartsExpected].sort();
  if (
    changedParts.length !== expectedChangedParts.length ||
    changedParts.some((part, index) => part !== expectedChangedParts[index])
  ) {
    throw new Error(`Unexpected package changes: ${changedParts.join(", ")}`);
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        slideCount: EXPECTED_SLIDES,
        updatedSlides: updatedSlideNumbers,
        updatedNotesSlides: [...expectedNotesBySlide.keys()],
        changedParts,
        validation,
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
