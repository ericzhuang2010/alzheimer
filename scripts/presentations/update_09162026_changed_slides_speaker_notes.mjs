#!/usr/bin/env node

/** Refresh speaker notes for the manually revised sensitivity and section slides. */

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
  "results/presentations/09162026_changed_script_refresh/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_changed_script_refresh/output/09162026_sex_apoe_kda_fine_broad_slides35_37_38_40_notes_refreshed_20260919_v2.pptx",
);
const EXPECTED_SLIDES = 160;

function notes({ goal, walkthrough, boundary, transition }) {
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

const NOTES_BY_SLIDE = new Map([
  [
    35,
    notes({
      goal:
        "Define an arm and show the numerical impact of raising the minimum donor requirement from three to five in both cohorts.",
      walkthrough:
        "An arm is one disease-status group within a comparison. In ROSMAP, the two arms are AD and NCI. In SEA-AD, they are dementia and no dementia. A contrast is eligible only when each arm meets the stated donor minimum. Raising that minimum from three to five reduces ROSMAP from 42 to 40 eligible contrasts and from three to two KDA runs. Its returned driver rows fall from 39 to 13, and its unique non-mitochondrial drivers fall from 33 to 13. SEA-AD falls from 28 to 20 eligible contrasts, but its five KDA runs, 24 returned rows, and 18 unique non-mitochondrial drivers remain unchanged.",
      boundary:
        "The threshold test changes only the donor eligibility gate. It does not change the retained contrast models, DEG queries, networks, or KDA settings. A contrast with fewer than five donors in either arm becomes unavailable under the stricter threshold; that exclusion is not a negative KDA result. Source: Phase 22 and VH14 run manifests and returns; donor-per-arm 3-versus-5 sensitivity assessment dated 2026-09-11.",
      transition:
        "Interpret why the two cohorts respond differently to the donor threshold.",
    }),
  ],
  [
    37,
    notes({
      goal:
        "Define the query-size threshold and show how increasing it changes KDA availability and returned drivers.",
      walkthrough:
        "The threshold is the minimum number of effective mitochondrial query genes remaining after network mapping. The donor minimum stays fixed at three in each disease-status group, so the source-estimable contrast counts remain 42 for ROSMAP and 28 for SEA-AD. One query is used for each contrast, which is why the query-passing contrast count equals the KDA-run count. In ROSMAP, increasing the threshold from three to ten genes reduces the analysis from three runs and 39 significant rows to one run and 26 rows. Thresholds of 20 and 30 make no further change. SEA-AD remains unchanged at five genes, falls to three runs and eight rows at ten or twenty genes, and retains two runs and seven rows at thirty genes.",
      boundary:
        "This sensitivity analysis filters existing calls by mapped query size. It does not refit DEG models or rerun KDA for retained calls. Significant rows are raw KDA returns, while the final column excludes MT-* genes and deduplicates drivers within each cohort. Source: validated Phase 22 and VH14 run manifests and significant-return tables dated 2026-09-11.",
      transition: "Identify the calls responsible for the query-size step changes.",
    }),
  ],
  [
    38,
    notes({
      goal: "Identify the seven KDA calls that create the query-threshold pattern.",
      walkthrough:
        "Read the ROSMAP panel first. Its three executed queries contain 3, 8, and 78 mapped genes. A minimum of five removes the OPC female epsilon-4 call. A minimum of ten also removes the astrocyte female epsilon-4 call, leaving only the 78-gene vasculature male epsilon-2 call. That remaining call has low donor support, so raising the query floor makes the ROSMAP result more dependent on it. In SEA-AD, the five query sizes are 5, 9, 21, 43, and 45 genes. A minimum of five changes nothing. A minimum of ten removes the microglia male epsilon-3 homozygous and astrocyte female epsilon-4 calls, reducing the output from 24 to 8 rows and from 18 to 3 unique non-MT drivers. A minimum of thirty also removes the 21-gene oligodendrocyte call, but its only returned gene is MT-*, so the non-MT driver count remains three.",
      boundary:
        "Query size means the number of effective mitochondrial genes after network mapping, not the number of donors, cells, or genes in a pathway. This test filters existing calls and does not rerun KDA. Returned MT-* genes explain changes in raw row counts but are not eligible non-mitochondrial key drivers. Source: validated Phase 22 and VH14 run manifests and significant-return tables dated 2026-09-11.",
      transition: "Finish with the implications for matched-stratum validation.",
    }),
  ],
  [
    40,
    notes({
      goal: "Introduce Part 5, the biological findings and discussion.",
      walkthrough:
        "Part 5 translates the DEG, pathway, KDA, and sensitivity results into 17 testable biological findings. It begins with two cross-cohort OXPHOS patterns, then examines additional sex/APOE-associated patterns, candidate key drivers, cross-cell recurrence, and the limits of validation and interpretation.",
      boundary:
        "These findings synthesize transcriptomic and network evidence. They do not establish causality or mitochondrial function. SEA-AD support is graded according to matched coverage and may support a broader pathway pattern without reproducing the exact driver gene.",
      transition: "Begin with Finding 1, the female epsilon-3 homozygous mtDNA-OXPHOS increase.",
    }),
  ],
]);

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

  const beforePngs = new Map();
  for (const [slideNumber, updatedNotes] of NOTES_BY_SLIDE) {
    const slide = slides[slideNumber - 1];
    const beforePng = await blobBuffer(
      await presentation.export({ slide, format: "png", scale: 2 }),
    );
    beforePngs.set(slideNumber, beforePng);
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-before.png`), beforePng);
    slide.speakerNotes.textFrame.setText(updatedNotes);
    slide.speakerNotes.setVisible(true);
    const afterPng = await blobBuffer(
      await presentation.export({ slide, format: "png", scale: 2 }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-after.png`), afterPng);
    if (sha256(beforePng) !== sha256(afterPng)) {
      throw new Error(`Visible slide ${slideNumber} changed while updating notes`);
    }
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const changedNotesParts = [];
  for (const slideNumber of NOTES_BY_SLIDE.keys()) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const updatedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!updatedNotesXml) throw new Error(`Updated notes are missing for slide ${slideNumber}`);
    sourceZip.file(sourceNotesPart, updatedNotesXml);
    changedNotesParts.push(sourceNotesPart);
  }

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
    nativeChartTargetApplication: "powerpoint",
    workspaceDir: WORKSPACE_DIR,
    candidatePath,
    finalPath: FINAL_PPTX,
    pythonExecutable:
      "/Users/rzhuang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
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
      "09162026_sex_apoe_kda_fine_broad_slides35_37_38_40_notes_refreshed_v2.validation.json",
    ),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const notesSnapshot = await reopened.inspect({ kind: "notes", maxChars: 2000000 });
  const finalNotesBySlide = new Map(
    notesSnapshot.ndjson
      .split("\n")
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text]),
  );
  for (const [slideNumber, expectedNotes] of NOTES_BY_SLIDE) {
    const finalPng = await blobBuffer(
      await reopened.export({
        slide: reopenedSlides[slideNumber - 1],
        format: "png",
        scale: 2,
      }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-final.png`), finalPng);
    if (sha256(beforePngs.get(slideNumber)) !== sha256(finalPng)) {
      throw new Error(`Finalized deck changed visible slide ${slideNumber}`);
    }
    const actualNotes = finalNotesBySlide.get(slideNumber);
    if (typeof actualNotes !== "string") {
      throw new Error(`Finalized notes are missing on slide ${slideNumber}`);
    }
    if (actualNotes.trim() !== expectedNotes.trim()) {
      throw new Error(`Finalized notes do not match on slide ${slideNumber}`);
    }
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const sourceFiles = Object.keys(originalZip.files)
    .filter((name) => !originalZip.files[name].dir)
    .sort();
  const changedParts = [];
  for (const name of sourceFiles) {
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [sourceData, finalData] = await Promise.all([
      originalZip.file(name).async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(sourceData) !== sha256(finalData)) changedParts.push(name);
  }
  const expectedParts = [...changedNotesParts].sort();
  if (
    changedParts.length !== expectedParts.length ||
    changedParts.some((part, index) => part !== expectedParts[index])
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
        updatedSlides: [...NOTES_BY_SLIDE.keys()],
        visibleSlidesPreserved: true,
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
