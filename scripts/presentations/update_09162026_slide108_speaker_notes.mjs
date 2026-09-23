#!/usr/bin/env node

/** Update only slide 108 speaker notes after the user's visual revision. */

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
  "results/presentations/09162026_slide108_notes_refresh_20260922_v1",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_slide108_notes_refreshed_20260922_v1.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "1b4746438abc243e64f44bf4ad49dad4eebae78cc6df1265ce1afa4df53e2df5";
const SLIDE_NUMBER = 108;
const SLIDE_COUNT = 160;

const NOTES = [
  "Teaching goal: Explain the focused WDR82 result and why four connected core MT genes should not be treated as four independent regulatory observations.",
  "",
  "Walk through: Start with the four labels across the top. The result occurs only in excitatory neurons and is supported by 18 KDA calls. WDR82 is directly connected to four recurring core MT genes, but a gene returned from KDA calls does not have to be a strong DEG. Then read the three main panels from left to right. WDR82 helps regulate which nuclear genes are active and is not part of the mitochondrial ribosome. Nearly every direct mitochondrial connection to WDR82 involves MT-ND1, MT-ND3, MT-ND4L, or MT-ND5. These four core MT genes are produced from one long RNA transcribed from the mitochondrial heavy strand and then processed into separate gene products. Their shared starting transcript means that four gene names do not provide four fully independent regulatory observations.",
  "",
  "Scientific boundary: Shared transcription can make the four gene measurements correlated, but processing and stability can still differ among the mature RNAs. The KDA result does not show that WDR82 regulates these genes or explain why their expression increases in AD.",
  "",
  "Transition: The next slide shows that every WDR82 KDA input has significant enrichment of upregulated core MT genes.",
  "",
  "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 9; https://doi.org/10.1128/MCB.01356-07; https://doi.org/10.1016/j.cell.2011.06.051; https://doi.org/10.3892/mmr.2015.4271",
].join("\n");

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
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
  const relationships = [
    ...presentationRels.matchAll(/<Relationship\b[^>]*\/?\s*>/g),
  ].map((match) => relationshipAttributes(match[0]));
  const relation = relationships.find(
    (item) => item.Id === relationshipId && item.Type?.endsWith("/slide"),
  );
  if (!relation?.Target) throw new Error(`Slide relationship ${relationshipId} was not found`);
  return relation.Target.startsWith("/")
    ? relation.Target.slice(1)
    : path.posix.normalize(path.posix.join("ppt", relation.Target));
}

async function notesPartForSlide(zip, slidePart) {
  const relsPath = path.posix.join(
    path.posix.dirname(slidePart),
    "_rels",
    `${path.posix.basename(slidePart)}.rels`,
  );
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing slide relationships: ${relsPath}`);
  const relationships = [...relsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map(
    (match) => relationshipAttributes(match[0]),
  );
  const relation = relationships.find((item) => item.Type?.endsWith("/notesSlide"));
  if (!relation?.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return relation.Target.startsWith("/")
    ? relation.Target.slice(1)
    : path.posix.normalize(path.posix.join(path.posix.dirname(slidePart), relation.Target));
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
    throw new Error(`Source deck changed before the notes edit: ${sourceHash}`);
  }

  const { importRuntimeModule } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/runtime_helpers.mjs")).href
  );
  const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");
  const JSZipModule = await importRuntimeModule("jszip");
  const JSZip = JSZipModule.default ?? JSZipModule;
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const slides = slidesFromPresentation(presentation);
  if (slides.length !== SLIDE_COUNT) {
    throw new Error(`Expected ${SLIDE_COUNT} slides, found ${slides.length}`);
  }

  slides[SLIDE_NUMBER - 1].speakerNotes.textFrame.setText(NOTES);
  slides[SLIDE_NUMBER - 1].speakerNotes.setVisible(true);

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("Source changed during the notes edit");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const sourceSlidePart = await visibleSlidePart(sourceZip, SLIDE_NUMBER);
  const artifactSlidePart = await visibleSlidePart(artifactZip, SLIDE_NUMBER);
  const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
  const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
  const notesXml = await artifactZip.file(artifactNotesPart)?.async("string");
  if (!notesXml) throw new Error(`Artifact candidate is missing ${artifactNotesPart}`);
  sourceZip.file(sourceNotesPart, notesXml);

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
    explicitTotalSlideCount: SLIDE_COUNT,
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
  const finalNotes = (await reopened.inspect({ kind: "notes", maxChars: 5000000 })).ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .find((record) => record.kind === "notes" && record.slide === SLIDE_NUMBER)?.text;
  if (finalNotes !== NOTES) {
    throw new Error("Final speaker notes do not match the slide 108 revision");
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const changedParts = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) changedParts.push(name);
  }
  changedParts.sort();
  if (changedParts.length !== 1 || changedParts[0] !== sourceNotesPart) {
    throw new Error(`Unexpected package changes: ${changedParts.join(", ")}`);
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
        updatedSlides: [SLIDE_NUMBER],
        changedParts,
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
