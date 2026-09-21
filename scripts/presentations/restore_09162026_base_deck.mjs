#!/usr/bin/env node

/** Restore the base deck after an edit was accidentally applied to the wrong target. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const SKILL_DIR =
  "/Users/rzhuang/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations";
const WORKSPACE_DIR = "/Users/rzhuang/Documents/VscodeProjects/alzheimer";
const SOURCE = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_slide58_notes_refresh_20260920_v2/output/09162026_sex_apoe_kda_fine_broad_slide58_notes_refreshed_20260920_v2.pptx",
);
const BUILD_DIR = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_restore_base_after_wrong_target/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_restore_base_after_wrong_target/output/09162026_sex_apoe_kda_fine_broad_restored.pptx",
);
const INSTALL_PATH = path.join(
  WORKSPACE_DIR,
  "docs/presentations/09162026/09162026_sex_apoe_kda_fine_broad.pptx",
);
const SOURCE_SHA256 =
  "95f7568e504cea66174399dd44142e005aa6e1c4817e819c462d9180c1a4a3bd";
const SLIDE_COUNT = 159;

const ORIGINAL_NOTES = [
  "Teaching goal: Quantify the ROSMAP evidence for Finding 3.",
  "",
  "Walk through: The core MT gene set contributes 128 DEG occurrences: 127 AD-up and one AD-down, or 99 percent upregulated. Nuclear-encoded OXPHOS genes contribute 243 occurrences: 239 AD-up and four AD-down, or 98 percent upregulated. The analysis also identified 29 significant pathway-enrichment results across KDA calls, comprising 20 for core MT genes and nine for nuclear-encoded OXPHOS genes. Within fine excitatory neurons, nine of 12 fine cell types support core MT upregulation and eight of 12 support nuclear-encoded OXPHOS upregulation.",
  "",
  "Scientific boundary: Occurrence counts can repeat genes across fine-cell KDA queries and do not represent independent donors or expression effect sizes. The number of enriched KDA calls can also depend on query size and the genes available in each network background.",
  "",
  "Transition: Compare the primary fine-cell result with direct broad-cell and SEA-AD evidence.",
  "",
  "Sources: docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 3. Literature: https://doi.org/10.1016/j.neuron.2019.03.075; https://doi.org/10.1016/j.celrep.2023.113183; https://doi.org/10.1186/s13024-023-00624-5",
].join("\n");

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
  if (!relsXml) throw new Error(`Missing ${relsPath}`);
  const relation = [...relsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)]
    .map((match) => relationshipAttributes(match[0]))
    .find((item) => item.Type?.endsWith("/notesSlide"));
  if (!relation?.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return relation.Target.startsWith("/")
    ? relation.Target.slice(1)
    : path.posix.normalize(path.posix.join(path.posix.dirname(slidePart), relation.Target));
}

async function main() {
  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
  const sourceBuffer = await fs.readFile(SOURCE);
  if (sha256(sourceBuffer) !== SOURCE_SHA256) {
    throw new Error("The known pre-edit source changed");
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
  slides[57].speakerNotes.textFrame.setText(ORIGINAL_NOTES);
  slides[57].speakerNotes.setVisible(true);

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const sourceSlidePart = await visibleSlidePart(sourceZip, 58);
  const artifactSlidePart = await visibleSlidePart(artifactZip, 58);
  const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
  const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
  const revisedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
  if (!revisedNotesXml?.includes("29 significant pathway-enrichment results")) {
    throw new Error("Could not verify the original slide 58 notes");
  }
  sourceZip.file(sourceNotesPart, revisedNotesXml);

  const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    candidatePath,
    await sourceZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );

  const { finalizePresentation } = await import(
    pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
  );
  await finalizePresentation({
    explicitTotalSlideCount: SLIDE_COUNT,
    requiredNativeTableOwnerSlides: [],
    requiredNativeChartOwnerSlides: [14],
    requiredEmbeddedWorkbookChartOwnerSlides: [14],
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
      referenceSha256: SOURCE_SHA256,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD_DIR, "restore-base.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalNotes = await reopened.inspect({ kind: "notes", maxChars: 3000000 });
  const slide58Notes = finalNotes.ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .find((record) => record.kind === "notes" && record.slide === 58)?.text;
  if (slide58Notes?.trim() !== ORIGINAL_NOTES.trim()) {
    throw new Error("Restored slide 58 notes do not match the pre-edit notes");
  }
  await fs.copyFile(FINAL_PPTX, INSTALL_PATH);
  console.log(
    JSON.stringify(
      {
        restored: INSTALL_PATH,
        slideCount: SLIDE_COUNT,
        sha256: sha256(await fs.readFile(INSTALL_PATH)),
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
