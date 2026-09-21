#!/usr/bin/env node

/** Clarify the three mitochondrial gene sets on slide 6 and refresh its notes. */

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
  "results/presentations/09162026_slide6_gene_sets_v5/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slide6_gene_sets_v5/output/09162026_sex_apoe_kda_fine_broad_slide6_mitocarta_mt_label_20260919.pptx",
);
const EXPECTED_SLIDES = 161;
const TARGET_SLIDE = 6;

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

const UPDATED_NOTES = structuredNotes({
  goal:
    "Distinguish the three mitochondrial gene sets by where the genes are encoded and how each set is used.",
  walkthrough:
    "Mitochondrial DNA, abbreviated mtDNA, is the small DNA molecule inside mitochondria. It encodes 37 genes: 13 protein genes, 22 transfer-RNA genes, and two ribosomal-RNA genes. The MitoCarta MT gene inventory is broader, where MT means mitochondrial. It contains 1,136 genes whose protein products are associated with mitochondria: 13 are encoded by mtDNA and 1,123 are encoded by nuclear DNA. The third set focuses on the 13 protein-coding genes in mtDNA. All 13 contribute to oxidative phosphorylation, abbreviated OXPHOS. Finding 1 measures RNA from this 13-gene set.",
  boundary:
    "The label mtDNA refers to the DNA molecule. The labels on the slide refer to gene sets. MitoCarta MT genes refers specifically to the 1,136-gene protein inventory. The shorthand core MT genes is avoided because it does not clearly distinguish the 37 genes encoded by mtDNA from the 1,136-gene MitoCarta inventory. RNA abundance from the 13 OXPHOS genes does not measure mtDNA copy number, OXPHOS protein abundance, or mitochondrial function.",
  transition:
    "With the gene sets distinguished, introduce the three-level MitoCarta pathway hierarchy.",
});

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
  const slideIds = [...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g)]
    .map((match) => match[1]);
  const relationshipId = slideIds[ordinal - 1];
  if (!relationshipId) throw new Error(`Visible slide ${ordinal} was not found`);
  const relationships = [...presentationRels.matchAll(/<Relationship\b[^>]*\/?\s*>/g)]
    .map((match) => relationshipAttributes(match[0]));
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
  const relationships = [...relsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)]
    .map((match) => relationshipAttributes(match[0]));
  const relation = relationships.find((item) => item.Type?.endsWith("/notesSlide"));
  if (!relation?.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return relation.Target.startsWith("/")
    ? relation.Target.slice(1)
    : path.posix.normalize(path.posix.join(path.posix.dirname(slidePart), relation.Target));
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
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
  const slides = slidesFromPresentation(presentation);
  if (slides.length !== EXPECTED_SLIDES) {
    throw new Error(`Expected ${EXPECTED_SLIDES} slides, found ${slides.length}`);
  }

  const targetSlide = slides[TARGET_SLIDE - 1];
  const beforePng = await blobBuffer(
    await presentation.export({ slide: targetSlide, format: "png", scale: 2 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-6-before.png"), beforePng);

  const slideHit = await presentation.inspect({
    kind: "slide",
    search: "Three mitochondrial gene sets used in this study",
    maxChars: 3000,
  });
  const slideAnchor = slideHit.ndjson?.match(/"id":"(sl\/[^"]+)"/)?.[1];
  if (!slideAnchor) throw new Error("Could not locate slide 6 by its current title");
  const shapeSnapshot = await presentation.inspect({
    target: { id: slideAnchor, beforeLines: 0, afterLines: 30 },
    kind: "slide,textbox,shape",
    include: "id,slide,name,text,textPreview,bbox",
    maxChars: 30000,
  });
  const textboxesByName = new Map(
    shapeSnapshot.ndjson
      .split("\n")
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .filter(
        (record) =>
          record.kind === "textbox" &&
          record.slide === TARGET_SLIDE &&
          typeof record.name === "string",
      )
      .map((record) => [record.name, record]),
  );
  function replaceNamedText(name, oldText, newText) {
    const record = textboxesByName.get(name);
    if (!record?.id) throw new Error(`Could not locate ${name} on slide 6`);
    if (record.text !== oldText) {
      throw new Error(`Unexpected source text in ${name}: ${JSON.stringify(record.text)}`);
    }
    presentation.resolve(record.id).text = newText;
  }

  replaceNamedText(
    "definition-2-term",
    "MitoCarta\nmitochondrial genes",
    "MitoCarta MT genes",
  );
  replaceNamedText(
    "definition-2-meaning",
    "1,136 genes whose protein products are associated with mitochondria.",
    "1,136 mitochondrial (MT) protein genes listed in MitoCarta.",
  );

  targetSlide.speakerNotes.textFrame.setText(UPDATED_NOTES);
  targetSlide.speakerNotes.setVisible(true);

  const afterPng = await blobBuffer(
    await presentation.export({ slide: targetSlide, format: "png", scale: 2 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-6-after.png"), afterPng);
  if (sha256(beforePng) === sha256(afterPng)) {
    throw new Error("Slide 6 did not change after the terminology revision");
  }

  const afterInspect = await presentation.inspect({
    kind: "slide,textbox,notes,layout",
    search:
      "MitoCarta MT genes|The MitoCarta MT gene inventory is broader",
    include: "id,slide,title,text,textPreview,bbox",
    maxChars: 16000,
  });
  await fs.writeFile(
    path.join(BUILD_DIR, "after.ndjson"),
    afterInspect.ndjson || "",
    "utf8",
  );
  if (!afterInspect.ndjson?.includes('"slide":6')) {
    throw new Error("Could not verify the updated slide 6 notes in Artifact Tool");
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const sourceSlidePart = await visibleSlidePart(sourceZip, TARGET_SLIDE);
  const artifactSlidePart = await visibleSlidePart(artifactZip, TARGET_SLIDE);
  const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
  const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
  const updatedSlideXml = await artifactZip.file(artifactSlidePart)?.async("string");
  if (!updatedSlideXml?.includes("MitoCarta MT genes")) {
    throw new Error("Artifact candidate does not contain the MitoCarta MT genes label");
  }
  const updatedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
  if (!updatedNotesXml?.includes("Mitochondrial DNA, abbreviated mtDNA")) {
    throw new Error("Artifact candidate does not contain the updated slide 6 notes");
  }
  sourceZip.file(sourceSlidePart, updatedSlideXml);
  sourceZip.file(sourceNotesPart, updatedNotesXml);
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
      referenceSha256: sha256(sourceBuffer),
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(
      BUILD_DIR,
      "09162026_sex_apoe_kda_fine_broad_slide6_mitocarta_mt_label.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const finalPng = await blobBuffer(
    await reopened.export({ slide: reopenedSlides[TARGET_SLIDE - 1], format: "png", scale: 2 }),
  );
  await fs.writeFile(path.join(BUILD_DIR, "slide-6-final.png"), finalPng);
  if (sha256(afterPng) !== sha256(finalPng)) {
    throw new Error("Finalized slide 6 does not match the revised slide preview");
  }

  const notesSnapshot = await reopened.inspect({ kind: "notes", maxChars: 2000000 });
  const slide6Notes = notesSnapshot.ndjson
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .find((record) => record.kind === "notes" && record.slide === TARGET_SLIDE)?.text;
  if (slide6Notes?.trim() !== UPDATED_NOTES.trim()) {
    throw new Error("Finalized slide 6 notes do not match the requested script");
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const sourceFiles = Object.keys(originalZip.files)
    .filter((name) => !originalZip.files[name].dir)
    .sort();
  const finalFiles = Object.keys(finalZip.files)
    .filter((name) => !finalZip.files[name].dir)
    .sort();
  if (sourceFiles.join("\n") !== finalFiles.join("\n")) {
    throw new Error("Final deck package parts differ from the source package");
  }
  const changedParts = [];
  for (const name of sourceFiles) {
    const [sourceData, finalData] = await Promise.all([
      originalZip.file(name).async("nodebuffer"),
      finalZip.file(name).async("nodebuffer"),
    ]);
    if (sha256(sourceData) !== sha256(finalData)) changedParts.push(name);
  }
  const expectedChangedParts = [sourceNotesPart, sourceSlidePart].sort();
  if (
    changedParts.length !== expectedChangedParts.length ||
    changedParts.some((name, index) => name !== expectedChangedParts[index])
  ) {
    throw new Error(`Unexpected package changes: ${changedParts.join(", ")}`);
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sha256(sourceBuffer),
        output: FINAL_PPTX,
        slideCount: EXPECTED_SLIDES,
        updatedSlide: TARGET_SLIDE,
        visibleSlideUpdated: true,
        changedParts,
        validation: result,
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
