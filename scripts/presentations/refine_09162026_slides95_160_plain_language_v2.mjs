#!/usr/bin/env node

/** Second plain-language pass for residual jargon on slides 95–160. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const SKILL_DIR = "/Users/rzhuang/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations";
const WORKSPACE_DIR = "/Users/rzhuang/Documents/VscodeProjects/alzheimer";
const SOURCE = path.join(WORKSPACE_DIR, "docs/presentations/09162026/09162026_sex_apoe_kda_fine_broad.pptx");
const RUN_DIR = path.join(WORKSPACE_DIR, "results/presentations/09162026_plain_language_slides95_160_20260922_v5");
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(RUN_DIR, "output/09162026_sex_apoe_kda_fine_broad_plain_language_slides95_160_v5.pptx");
const EXPECTED_SOURCE_SHA256 = "89a725a3cc6f5bafa6fde23d3d3681e7d2ff374ac88e2fd4fc937f8998d39d8f";
const SLIDE_COUNT = 160;

const EDITS = [
  [100, "TextBox 1", "How prior research supports and limits Finding 7"],
  [105, "TextBox 2", "LAMTOR5 is positioned between lysosomes, mTORC1, and mitochondria, which is consistent with known biology."],
  [106, "TextBox 1", "How prior research supports and limits Finding 8"],
  [106, "TextBox 9", "Does not test Alzheimer’s neurons or connections to OXPHOS genes."],
  [106, "TextBox 14", "Links mTORC1 with mitochondrial protein production and capacity for respiration."],
  [109, "TextBox 6", "four sex/APOE groups"],
  [109, "TextBox 25", "0 of 18 met DEG criteria"],
  [112, "TextBox 1", "How prior research supports and limits Finding 9"],
  [115, "TextBox 2", "SELENOM recurs across groups, so the result is not sex- or APOE-specific."],
  [118, "TextBox 1", "How prior research supports and limits Finding 10"],
  [122, "TextBox 12", "RELATED GENE IN SEA-AD"],
  [124, "TextBox 1", "How prior research supports and limits Finding 11"],
  [127, "TextBox 22", "PGK1 showed almost no expression change and did not meet the report’s DEG criteria"],
  [128, "TextBox 16", "PGK1 appears across several groups and should not be labeled sex- or APOE-specific."],
  [130, "TextBox 1", "How prior research supports and limits Finding 12"],
  [130, "TextBox 9", "Uses ROSMAP, so some donors may be the same as in the current analysis."],
  [136, "TextBox 1", "How prior research supports and limits Finding 13"],
  [138, "TextBox 14", "Human variants make PLCG2 an important Alzheimer’s gene to study."],
  [138, "TextBox 18", "PLCG2 appears in ε2, ε3/ε3, and ε4 female groups."],
  [139, "TextBox 2", "Repeated MT-CO1 is not equivalent to several distinct mitochondrial genes connected to PLCG2."],
  [139, "TextBox 6", "all in female sex/APOE groups"],
  [139, "TextBox 13", "PLCG2 met DEG criteria"],
  [142, "TextBox 1", "How prior research supports and limits Finding 14"],
  [143, "TextBox 20", "APOE is returned in three astrocyte groups with opposite expression directions and different connected mitochondrial genes."],
  [144, "TextBox 1", "Astrocyte APOE changes direction across sex and APOE groups"],
  [144, "TextBox 2", "Astrocytes produce much of the brain’s APOE. Finding APOE in an analysis separated by APOE group does not make the result specific to ε4."],
  [145, "TextBox 1", "ROSMAP: APOE is a DEG and is returned from KDA calls in three astrocyte groups"],
  [145, "TextBox 9", "APOE met DEG criteria in 3 of 3"],
  [147, "TextBox 1", "Why this matters: APOE biology depends on cell type, sex, and APOE group"],
  [147, "TextBox 6", "Astrocytes are a well-established source of APOE in the brain."],
  [148, "TextBox 1", "How prior research supports and limits Finding 15"],
  [148, "TextBox 9", "Genetics does not confirm the three sets of network connections shown here."],
  [151, "TextBox 1", "ROSMAP: three of five genes returned from female ε4 vascular KDA calls respond to cell stress"],
  [153, "TextBox 9", "Protein-folding helpers protect proteins"],
  [154, "TextBox 1", "How prior research supports and limits Finding 16"],
  [156, "TextBox 4", "ROSMAP RESULTS"],
  [156, "TextBox 10", "Same genes in different settings"],
  [156, "TextBox 20", "COMPARE MITOCHONDRIAL GENE SETS"],
  [158, "TextBox 16", "Across all genes, 3 of 43 genes returned in SEA-AD were also among 228 genes returned in ROSMAP. The odds ratio was 3.15, indicating more overlap than expected, but P = 0.0812 did not meet the significance threshold."],
  [159, "TextBox 17", "Support for the same gene set can strengthen a ROSMAP result without confirming that the same gene controls the process."],
  [160, "TextBox 1", "How prior research supports and limits Finding 17"],
];

const NOTES_REPLACEMENTS = new Map([
  [95, [
    ["nuclear-encoded OXPHOS query genes", "nuclear-encoded OXPHOS genes used as input to KDA"],
  ]],
  [96, [
    ["The signal is more credible as one module than as 20 independent genes returned from KDA calls.", "The signal is best interpreted as one recurring group of biologically related genes, rather than as 20 separate discoveries."],
  ]],
  [97, [
    ["In the exact network background", "Among the genes available for testing in the same network"],
    ["Identify RPL11 and RPS15 as anchors of the recurrent group of ribosome genes.", "Use RPL11 and RPS15 as examples of the recurring group of ribosome genes."],
  ]],
  [106, [
    ["OXPHOS neighbors", "genes connected to OXPHOS genes"],
    ["they do not establish LAMTOR5 as the causal node in this network", "they do not establish that LAMTOR5 causes the network pattern"],
    ["The literature does not establish the inferred LAMTOR5 edges or their direction.", "The literature does not establish the predicted connections between LAMTOR5 and other genes, or which gene influences the other."],
    ["the WDR82-centered core MT gene neighborhood", "the core MT genes connected to WDR82"],
  ]],
  [111, [
    ["Removing core MT genes in the query is an important sensitivity test before mechanistic interpretation.", "Repeating the analysis after removing core MT genes from the KDA input DEG set is an important check before proposing a biological mechanism."],
  ]],
  [155, [
    ["similar mitochondrial gene sets do not prove a shared upstream driver", "similar mitochondrial gene sets do not prove that the same gene controls the process"],
    ["Explain the difference between exact-context driver matching and broader gene-set agreement.", "Explain the difference between finding the same gene in the same sex/APOE and cell context and finding agreement only at the level of a broader mitochondrial gene set."],
  ]],
]);

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function parseNdjson(ndjson) {
  return (ndjson || "").split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
}

function slidesFromPresentation(presentation) {
  if (Array.isArray(presentation.slides?.items)) return presentation.slides.items;
  if (Number.isInteger(presentation.slides?.count) && typeof presentation.slides.getItem === "function") {
    return Array.from({ length: presentation.slides.count }, (_, index) => presentation.slides.getItem(index));
  }
  throw new Error("Could not enumerate presentation slides");
}

async function main() {
  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
  if (await fs.stat(FINAL_PPTX).catch(() => undefined)) throw new Error(`Output already exists: ${FINAL_PPTX}`);

  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceHash = sha256(sourceBuffer);
  if (sourceHash !== EXPECTED_SOURCE_SHA256) throw new Error(`Source deck changed before edit: ${sourceHash}`);
  await fs.writeFile(path.join(BUILD_DIR, "source-original.pptx"), sourceBuffer);

  const { importRuntimeModule } = await import(pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href);
  const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");
  const JSZipModule = await importRuntimeModule("jszip");
  const JSZip = JSZipModule.default ?? JSZipModule;
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const slides = slidesFromPresentation(presentation);
  if (slides.length !== SLIDE_COUNT) throw new Error(`Expected ${SLIDE_COUNT} slides, found ${slides.length}`);

  const snapshot = parseNdjson((await presentation.inspect({ kind: "textbox", include: "id,slide,name,text", maxChars: 5000000 })).ndjson);
  const byKey = new Map(snapshot.filter((record) => record.kind === "textbox").map((record) => [`${record.slide}\t${record.name}`, record]));
  const changes = [];
  for (const [slideNumber, shapeName, after] of EDITS) {
    const record = byKey.get(`${slideNumber}\t${shapeName}`);
    if (!record?.id || typeof record.text !== "string") throw new Error(`Missing slide ${slideNumber}, ${shapeName}`);
    if (record.text === after) continue;
    presentation.resolve(record.id).text.replace(record.text, after);
    changes.push({ slide: slideNumber, name: shapeName, before: record.text, after });
  }

  const replacementsBySlide = new Map();
  for (const change of changes) {
    if (!replacementsBySlide.has(change.slide)) replacementsBySlide.set(change.slide, []);
    replacementsBySlide.get(change.slide).push([change.before, change.after]);
  }
  const notes = parseNdjson((await presentation.inspect({ kind: "notes", maxChars: 5000000 })).ndjson);
  const noteBySlide = new Map(notes.filter((record) => record.kind === "notes").map((record) => [record.slide, record.text || ""]));
  const noteChanges = [];
  for (const [slideNumber, replacements] of replacementsBySlide) {
    const before = noteBySlide.get(slideNumber) || "";
    let after = before;
    for (const [from, to] of replacements) after = after.split(from).join(to);
    if (slideNumber === 139) after = after.split("four sex/APOE strata").join("four sex/APOE groups");
    if (slideNumber === 159) after = after.split("upstream driver").join("gene that controls the process");
    if (after !== before) {
      slides[slideNumber - 1].speakerNotes.textFrame.setText(after);
      slides[slideNumber - 1].speakerNotes.setVisible(true);
      noteChanges.push({ slide: slideNumber, before, after });
    }
  }
  for (const [slideNumber, replacements] of NOTES_REPLACEMENTS) {
    const current = noteChanges.find((change) => change.slide === slideNumber)?.after ?? noteBySlide.get(slideNumber) ?? "";
    let after = current;
    for (const [from, to] of replacements) after = after.split(from).join(to);
    if (after !== current) {
      slides[slideNumber - 1].speakerNotes.textFrame.setText(after);
      slides[slideNumber - 1].speakerNotes.setVisible(true);
      const existing = noteChanges.find((change) => change.slide === slideNumber);
      if (existing) existing.after = after;
      else noteChanges.push({ slide: slideNumber, before: current, after });
    }
  }

  await fs.writeFile(path.join(BUILD_DIR, "changes.json"), JSON.stringify({ sourceHash, changes, noteChanges }, null, 2) + "\n", "utf8");
  const artifactCandidate = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidate);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) throw new Error("Source changed during edit");

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidate));
  const visibleSlides = [...new Set(changes.map((change) => change.slide))].sort((a, b) => a - b);
  const notesSlides = [...new Set(noteChanges.map((change) => change.slide))].sort((a, b) => a - b);
  const expectedParts = [];
  for (const slideNumber of visibleSlides) {
    const part = `ppt/slides/slide${slideNumber}.xml`;
    sourceZip.file(part, await artifactZip.file(part).async("string"));
    expectedParts.push(part);
  }
  for (const slideNumber of notesSlides) {
    const part = `ppt/notesSlides/notesSlide${slideNumber}.xml`;
    sourceZip.file(part, await artifactZip.file(part).async("string"));
    expectedParts.push(part);
  }
  const candidate = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(candidate, await sourceZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 6 } }));

  const { finalizePresentation } = await import(pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href);
  await finalizePresentation({
    explicitTotalSlideCount: SLIDE_COUNT,
    requiredNativeTableOwnerSlides: [53, 54, 55, 56, 57],
    requiredNativeChartOwnerSlides: [19],
    requiredEmbeddedWorkbookChartOwnerSlides: [19],
    nativeChartTargetApplication: "powerpoint",
    workspaceDir: WORKSPACE_DIR,
    candidatePath: candidate,
    finalPath: FINAL_PPTX,
    pythonExecutable: "/Users/rzhuang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12",
    integrityValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_package_integrity.py"),
    layoutValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_layout_geometry.py"),
    layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-bullet-geometry", "--validate-heading-fit", ...[53, 54, 55, 56, 57].flatMap((number) => ["--require-native-table-slide", String(number)])],
    fontPolicy: { basis: "reference", families: ["Arial"], referencePath: SOURCE, referenceSha256: sourceHash },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD_DIR, "validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalSnapshot = parseNdjson((await reopened.inspect({ kind: "textbox", include: "slide,name,text", maxChars: 5000000 })).ndjson);
  const finalByKey = new Map(finalSnapshot.filter((record) => record.kind === "textbox").map((record) => [`${record.slide}\t${record.name}`, record.text]));
  for (const [slideNumber, shapeName, expected] of EDITS) {
    if (finalByKey.get(`${slideNumber}\t${shapeName}`) !== expected) throw new Error(`Final mismatch: slide ${slideNumber}, ${shapeName}`);
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const actualParts = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck missing ${name}`);
    const [before, after] = await Promise.all([entry.async("nodebuffer"), finalEntry.async("nodebuffer")]);
    if (sha256(before) !== sha256(after)) actualParts.push(name);
  }
  actualParts.sort();
  expectedParts.sort();
  if (actualParts.length !== expectedParts.length || actualParts.some((name, i) => name !== expectedParts[i])) {
    throw new Error(`Unexpected package changes: ${actualParts.join(", ")}`);
  }
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) throw new Error("Source changed before installation");
  await fs.copyFile(FINAL_PPTX, SOURCE);
  console.log(JSON.stringify({ source: SOURCE, originalSha256: sourceHash, outputSha256: sha256(await fs.readFile(FINAL_PPTX)), updatedSlides: visibleSlides, updatedNotesSlides: notesSlides, changeCount: changes.length, changedParts: actualParts }, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exitCode = 1;
});
