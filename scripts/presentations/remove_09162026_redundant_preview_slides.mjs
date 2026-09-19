#!/usr/bin/env node

/** Remove redundant preview slides 13 and 14 while preserving the PPTX package. */

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
  "results/presentations/09162026_remove_redundant_preview_slides/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_remove_redundant_preview_slides/output/09162026_sex_apoe_kda_fine_broad_without_preview_slides.pptx",
);
const SOURCE_SLIDES = 162;
const FINAL_SLIDES = 160;

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

function slide12Notes() {
  return [
    "Teaching goal: Interpret OXPHOS DEG direction across sex/APOE groups and highlight the contrasting epsilon-3 homozygous patterns.",
    "",
    "Walk through: OXPHOS, or oxidative phosphorylation, is the mitochondrial process that produces most cellular ATP. Blue bars summarize the 13 OXPHOS genes encoded by mitochondrial DNA, and orange bars summarize 86 structural OXPHOS genes encoded by nuclear DNA. Every bar starts at the 50 percent line, where upregulated and downregulated occurrences are equally common. Bars extend upward when more than half of the occurrences are upregulated and downward when fewer than half are upregulated. The label at the end of each bar gives the actual upregulated percentage, while bar length shows its percentage-point distance from 50 percent. The key contrast is shown in the callout. In female epsilon-3 homozygous, both gene sets are predominantly upregulated: 100 percent for the mitochondrial-DNA set and 85 percent for the nuclear-DNA set. In male epsilon-3 homozygous, the two sets diverge: 86 percent of mitochondrial-DNA occurrences are upregulated, but only 12 percent of nuclear-DNA occurrences are upregulated, which means 88 percent are downregulated. The broader pattern is that female epsilon-2 is predominantly upregulated in both sets, female epsilon-4 and male epsilon-2 are predominantly downregulated in both, and male epsilon-4 shows a weaker version of the male epsilon-3 homozygous split.",
    "",
    "Scientific boundary: The bars show the share of repeated gene-by-fine-cell DEG occurrences that are upregulated. The vertical displacement from 50 percent is a descriptive percentage-point difference, not an effect size. The chart does not show percent expression change, percent of cells or donors, percent of unique genes, pathway enrichment, OXPHOS activity, or a direct statistical interaction between disease, sex, and APOE.",
    "",
    "Transition: Now move to Part 3, where mitochondrial DEGs become network-analysis queries.",
  ].join("\n");
}

function relationshipTags(xml) {
  return [...xml.matchAll(/<Relationship\b[^>]*\/>/g)].map((match) => match[0]);
}

function relationshipAttribute(tag, name) {
  return tag.match(new RegExp(`\\b${name}="([^"]+)"`))?.[1];
}

function relationshipPartPath(ownerPartPath) {
  return path.posix.join(
    path.posix.dirname(ownerPartPath),
    "_rels",
    `${path.posix.basename(ownerPartPath)}.rels`,
  );
}

async function relatedPartPath(zip, ownerPartPath, relationshipTypeSuffix) {
  const relsPath = relationshipPartPath(ownerPartPath);
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing ${relsPath}`);
  for (const tag of relationshipTags(relsXml)) {
    const type = relationshipAttribute(tag, "Type");
    if (!type?.endsWith(`/relationships/${relationshipTypeSuffix}`)) continue;
    const target = relationshipAttribute(tag, "Target");
    if (!target) continue;
    if (target.startsWith("/")) return target.slice(1);
    return path.posix.normalize(
      path.posix.join(path.posix.dirname(ownerPartPath), target),
    );
  }
  throw new Error(`${ownerPartPath} lacks a ${relationshipTypeSuffix} relationship`);
}

function removeContentTypeOverride(contentTypesXml, partPath) {
  const partName = `/${partPath}`;
  const tags = [...contentTypesXml.matchAll(/<Override\b[^>]*\/>/g)].map(
    (match) => match[0],
  );
  const target = tags.find(
    (tag) => relationshipAttribute(tag, "PartName") === partName,
  );
  if (!target) throw new Error(`Missing content-type override for ${partName}`);
  return contentTypesXml.replace(target, "");
}

function updateAppProperties(appXml) {
  let updated = appXml
    .replace(/<Slides>162<\/Slides>/, "<Slides>160</Slides>")
    .replace(/<Notes>162<\/Notes>/, "<Notes>160</Notes>")
    .replace(
      /(<vt:lpstr>Slide Titles<\/vt:lpstr>\s*<\/vt:variant>\s*<vt:variant>\s*<vt:i4>)162(<\/vt:i4>)/,
      "$1160$2",
    );

  const titlesMatch = updated.match(
    /(<TitlesOfParts>\s*<vt:vector size=")165(" baseType="lpstr">)([\s\S]*?)(<\/vt:vector>\s*<\/TitlesOfParts>)/,
  );
  if (!titlesMatch) throw new Error("Could not locate TitlesOfParts metadata");
  let entriesXml = titlesMatch[3];
  const entries = [...entriesXml.matchAll(/<vt:lpstr>[\s\S]*?<\/vt:lpstr>/g)];
  if (entries.length !== 165) {
    throw new Error(`Expected 165 TitlesOfParts entries, found ${entries.length}`);
  }
  for (const entryIndex of [16, 15]) {
    const entry = entries[entryIndex];
    entriesXml =
      entriesXml.slice(0, entry.index) +
      entriesXml.slice(entry.index + entry[0].length);
  }
  updated = updated.replace(
    titlesMatch[0],
    `${titlesMatch[1]}163${titlesMatch[2]}${entriesXml}${titlesMatch[4]}`,
  );
  return updated;
}

async function main() {
  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceHash = sha256(sourceBuffer);
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
  const sourceSlides = slidesFromPresentation(presentation);
  if (sourceSlides.length !== SOURCE_SLIDES) {
    throw new Error(`Expected ${SOURCE_SLIDES} source slides, found ${sourceSlides.length}`);
  }

  const duplicateCheck = await presentation.inspect({
    kind: "slide,textbox,notes,layout",
    search:
      "Female ε3/ε3 neurons repeatedly increase mtDNA-encoded OXPHOS RNA|Male ε3/ε3 cells show opposite directions in two OXPHOS gene sets",
    maxChars: 20000,
  });
  if (
    !duplicateCheck.ndjson?.includes('"slide":13') ||
    !duplicateCheck.ndjson?.includes('"slide":14')
  ) {
    throw new Error("Could not verify the two redundant preview slides");
  }
  await fs.writeFile(
    path.join(BUILD_DIR, "duplicates-before.ndjson"),
    duplicateCheck.ndjson || "",
    "utf8",
  );

  sourceSlides[11].speakerNotes.textFrame.setText(slide12Notes());
  sourceSlides[11].speakerNotes.setVisible(true);
  sourceSlides[13].delete();
  sourceSlides[12].delete();

  const editedSlides = slidesFromPresentation(presentation);
  if (editedSlides.length !== FINAL_SLIDES) {
    throw new Error(`Expected ${FINAL_SLIDES} slides after deletion, found ${editedSlides.length}`);
  }
  const orderCheck = await presentation.inspect({
    kind: "slide,textbox,notes,layout",
    search:
      "Share of OXPHOS DEG occurrences that are upregulated|PART 3|Female ε3/ε3 neurons repeatedly increase mtDNA-encoded OXPHOS RNA|Male ε3/ε3 cells show opposite directions in two OXPHOS gene sets",
    maxChars: 24000,
  });
  if (!orderCheck.ndjson?.includes('"slide":12')) {
    throw new Error("Slide 12 was not preserved in the Artifact Tool edit");
  }
  if (!orderCheck.ndjson?.includes('"slide":13')) {
    throw new Error("PART 3 did not move to slide 13 in the Artifact Tool edit");
  }
  await fs.writeFile(
    path.join(BUILD_DIR, "order-after.ndjson"),
    orderCheck.ndjson || "",
    "utf8",
  );

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  const currentSourceBuffer = await fs.readFile(SOURCE);
  if (sha256(currentSourceBuffer) !== sourceHash) {
    throw new Error("The source presentation changed during the edit");
  }

  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const artifactNotesPath = await relatedPartPath(
    artifactZip,
    "ppt/slides/slide12.xml",
    "notesSlide",
  );
  const updatedNotesXml = await artifactZip.file(artifactNotesPath)?.async("string");
  if (!updatedNotesXml?.includes("Now move to Part 3")) {
    throw new Error("Artifact candidate does not contain the revised slide 12 transition");
  }

  const zip = await JSZip.loadAsync(currentSourceBuffer);
  const presentationPath = "ppt/presentation.xml";
  const presentationRelsPath = "ppt/_rels/presentation.xml.rels";
  let presentationXml = await zip.file(presentationPath)?.async("string");
  let presentationRelsXml = await zip.file(presentationRelsPath)?.async("string");
  let contentTypesXml = await zip.file("[Content_Types].xml")?.async("string");
  let appXml = await zip.file("docProps/app.xml")?.async("string");
  if (!presentationXml || !presentationRelsXml || !contentTypesXml || !appXml) {
    throw new Error("The source PPTX is missing required package parts");
  }

  const slideIdTags = [...presentationXml.matchAll(/<p:sldId\b[^>]*\/>/g)].map(
    (match) => match[0],
  );
  if (slideIdTags.length !== SOURCE_SLIDES) {
    throw new Error(`Expected ${SOURCE_SLIDES} slide IDs, found ${slideIdTags.length}`);
  }
  const removedSlideIdTags = [slideIdTags[12], slideIdTags[13]];
  const removedRelationshipIds = removedSlideIdTags.map((tag) =>
    relationshipAttribute(tag, "r:id"),
  );
  if (removedRelationshipIds.some((value) => !value)) {
    throw new Error("Could not resolve the deleted slide relationship IDs");
  }

  const presentationRelationships = relationshipTags(presentationRelsXml);
  for (const [index, relationshipId] of removedRelationshipIds.entries()) {
    const relationshipTag = presentationRelationships.find(
      (tag) => relationshipAttribute(tag, "Id") === relationshipId,
    );
    const target = relationshipTag && relationshipAttribute(relationshipTag, "Target");
    if (!relationshipTag || !target) {
      throw new Error(`Could not resolve presentation relationship ${relationshipId}`);
    }
    const slidePartPath = path.posix.normalize(path.posix.join("ppt", target));
    const expectedPartPath = `ppt/slides/slide${index + 13}.xml`;
    if (slidePartPath !== expectedPartPath) {
      throw new Error(`Expected ${expectedPartPath}, found ${slidePartPath}`);
    }
    const slideRelsPath = relationshipPartPath(slidePartPath);
    const notesPartPath = await relatedPartPath(zip, slidePartPath, "notesSlide");
    const notesRelsPath = relationshipPartPath(notesPartPath);

    zip.remove(slidePartPath);
    zip.remove(slideRelsPath);
    zip.remove(notesPartPath);
    zip.remove(notesRelsPath);
    contentTypesXml = removeContentTypeOverride(contentTypesXml, slidePartPath);
    contentTypesXml = removeContentTypeOverride(contentTypesXml, notesPartPath);
    presentationXml = presentationXml.replace(removedSlideIdTags[index], "");
    presentationRelsXml = presentationRelsXml.replace(relationshipTag, "");
  }

  const sourceNotesPath = await relatedPartPath(
    zip,
    "ppt/slides/slide12.xml",
    "notesSlide",
  );
  zip.file(sourceNotesPath, updatedNotesXml);
  zip.file(presentationPath, presentationXml);
  zip.file(presentationRelsPath, presentationRelsXml);
  zip.file("[Content_Types].xml", contentTypesXml);
  zip.file("docProps/app.xml", updateAppProperties(appXml));

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
    await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  const result = await finalizePresentation({
    explicitTotalSlideCount: FINAL_SLIDES,
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
      referenceSha256: sourceHash,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(
      BUILD_DIR,
      "09162026_sex_apoe_kda_fine_broad_without_preview_slides.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalSlides = slidesFromPresentation(reopened);
  if (finalSlides.length !== FINAL_SLIDES) {
    throw new Error(`Final deck has ${finalSlides.length} slides, expected ${FINAL_SLIDES}`);
  }
  const finalInspect = await reopened.inspect({
    kind: "slide,textbox,notes,chart,layout",
    search:
      "Share of OXPHOS DEG occurrences that are upregulated|Now move to Part 3|PART 3|Female ε3/ε3 neurons repeatedly increase mtDNA-encoded OXPHOS RNA|Male ε3/ε3 cells show opposite directions in two OXPHOS gene sets",
    maxChars: 30000,
  });
  await fs.writeFile(
    path.join(BUILD_DIR, "final.ndjson"),
    finalInspect.ndjson || "",
    "utf8",
  );
  if (!finalInspect.ndjson?.includes('"slide":12')) {
    throw new Error("Could not verify final slide 12 and its revised transition");
  }
  if (!finalInspect.ndjson?.includes('"slide":13')) {
    throw new Error("Could not verify PART 3 as final slide 13");
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        removedSourceSlides: [13, 14],
        finalSlideCount: FINAL_SLIDES,
        slide12TransitionUpdated: true,
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
