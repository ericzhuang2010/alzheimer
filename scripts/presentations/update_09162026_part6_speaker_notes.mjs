#!/usr/bin/env node

/** Refresh only the Part 6 speaker notes in the 2026-09-16 presentation. */

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
  "results/presentations/09162026_part6_notes_refresh_20260921/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_part6_notes_refresh_20260921/output/09162026_sex_apoe_kda_fine_broad_part6_notes_refreshed_20260921.pptx",
);
const EXPECTED_SLIDES = 155;
const EXPECTED_SOURCE_SHA256 =
  "23057c7fc8c7ebeeb2d4412e55db892ac6cf706f87521dbcf84a63543409787b";

function notes({ goal, walkthrough, boundary, transition, sources, method }) {
  return [
    `Teaching goal: ${goal}`,
    "",
    `Walk through: ${walkthrough}`,
    "",
    `Scientific boundary: ${boundary}`,
    ...(method ? ["", `Method: ${method}`] : []),
    ...(sources ? ["", `Sources: ${sources}`] : []),
    "",
    `Transition: ${transition}`,
  ].join("\n");
}

const NOTES_BY_SLIDE = new Map([
  [
    40,
    notes({
      goal: "Introduce the purpose and methods of direct broad-cell validation.",
      walkthrough:
        "Part 6 checks selected pathway findings at direct broad-cell resolution. It first distinguishes this analysis from the primary fine-cell workflow. It then explains how donor-level broad-cell expression profiles are compared, how genes are ranked, and how weighted gene set enrichment analysis produces the enrichment score and the normalized enrichment score. These definitions prepare the audience to interpret direct broad-cell results in later findings.",
      boundary:
        "Direct broad-cell analysis provides supporting evidence. Combining fine cell types can hide a result confined to one fine cell type or can make the result sensitive to differences in fine-cell composition.",
      transition: "Compare the fine-cell and direct broad-cell workflows side by side.",
    }),
  ],
  [
    41,
    notes({
      goal:
        "Distinguish the two workflows without implying that donor-level aggregation is unique to direct broad-cell analysis.",
      walkthrough:
        "Fine-cell analysis produces one donor-level expression profile for each fine cell type. It tests each fine cell type separately and summarizes the resulting evidence by broad cell class afterward. Direct broad-cell analysis instead combines the contributing fine cell types within each donor to create one profile for the entire broad cell class before differential-expression testing. Both workflows compare donors. They differ in the cell-type resolution retained before the comparison.",
      boundary:
        "Agreement supports a result across two resolutions. Disagreement can reflect fine-cell composition or opposing effects among fine cell types and does not by itself invalidate the fine-cell result.",
      transition:
        "Follow the direct broad-cell pathway workflow from donor-level expression profiles to pathway testing.",
    }),
  ],
  [
    42,
    notes({
      goal: "Explain the four stages of direct broad-cell pathway validation.",
      walkthrough:
        "First, the analysis combines cells from one broad cell class within each donor. Second, it compares AD with NCI separately within each sex/APOE group and broad cell class. Third, it orders all tested MitoCarta MT genes from stronger AD-up evidence to stronger AD-down evidence. Fourth, ranked-gene pathway analysis calculates an enrichment score and then a normalized enrichment score, or NES, to summarize whether pathway genes concentrate toward the AD-up or AD-down end of the ranking.",
      boundary:
        "This workflow ranks every tested MitoCarta MT gene rather than filtering to DEGs first. The fine-cell pathway analysis uses a different method based on overlap between a thresholded DEG list and a pathway.",
      transition:
        "The next slide defines the signed score used to rank the tested MitoCarta MT genes.",
    }),
  ],
  [
    43,
    notes({
      goal:
        "Define the rank score used to order all tested MitoCarta MT genes for direct broad-cell GSEA.",
      walkthrough:
        "The analysis calculates the sign of the log fold change multiplied by the square root of the edgeR quasi-likelihood F statistic for every tested MitoCarta MT gene. The log fold change compares AD with NCI. Its sign gives direction: a positive score is AD-up and a negative score is AD-down. The F statistic supplies the score magnitude and reflects the strength of evidence for an AD-versus-NCI difference after accounting for variability. For this one-degree-of-freedom contrast, the square root of F gives a t-like scale and preserves the ordering based on F. The analysis ranks genes from the largest positive score to the most negative score. Log fold change alone is less suitable because it describes the estimated effect size without incorporating its uncertainty. A low-expression gene or a gene with high donor-to-donor variability can therefore have a large but unstable log fold change. In the illustrative example, Gene A has logFC plus 2.0 and F 0.25, so its rank score is plus 0.5. Gene B has logFC plus 0.5 and F 16, so its rank score is plus 4.0. Gene B ranks higher because the evidence for its change is stronger.",
      boundary:
        "This is the study's ranking rule for targeted MitoCarta preranked GSEA. It ranks every tested MitoCarta MT gene and does not first filter to DEGs. GSEA does not require one universal ranking statistic. The two example genes are illustrative and are not observed study results.",
      sources:
        "scripts/11_run_broad_deg_pathway_analysis.R computes rank_score = sign(logFC) multiplied by the square root of F; scripts/08_run_broad_pseudobulk_de.R produces logFC and F with edgeR glmQLFTest.",
      transition:
        "The next slide explains what the standard weighted GSEA enrichment score means.",
    }),
  ],
  [
    44,
    notes({
      goal:
        "Explain what the standard weighted GSEA enrichment score means for one pathway.",
      walkthrough:
        "GSEA starts at the AD-up end of the ranked MitoCarta MT gene list and moves toward the AD-down end. When it encounters a gene from the pathway, the running score increases. Pathway genes with stronger absolute rank scores have more influence because this analysis uses standard weighted GSEA. Other tested genes decrease the running score evenly. The enrichment score, abbreviated ES, is the most extreme point reached by that running score. A large positive ES means pathway genes cluster near the AD-up end. An ES near zero means the pathway genes are dispersed through the ranked list. A large negative ES means pathway genes cluster near the AD-down end.",
      boundary:
        "The ES sign gives direction, and distance from zero describes concentration within that ranked list. The raw ES is not a fold change and does not by itself establish statistical significance. Its magnitude also depends on pathway size and the rank-score distribution, so the normalized enrichment score supports comparisons among pathways.",
      method:
        "The analysis uses fgseaMultilevel with scoreType set to std and gseaParam set to 1, the standard weighted GSEA enrichment score.",
      sources:
        "Subramanian et al., PNAS 2005, doi:10.1073/pnas.0506580102; Bioconductor fgsea documentation; scripts/lib/phase11_deg_pathway_common.R; config/phase11_pathway_deg_broad.yml.",
      transition: "The next slide explains how NES rescales the raw ES.",
    }),
  ],
  [
    45,
    notes({
      goal:
        "Distinguish the raw enrichment score from the normalized enrichment score.",
      walkthrough:
        "ES describes where one pathway's genes concentrate in the ranked list. Its sign gives the AD-up or AD-down direction, but its raw magnitude depends partly on pathway size and the distribution of rank scores. To calculate NES, the analysis compares the observed ES with ES values from random gene sets containing the same number of genes. Positive observed ES values are normalized against positive random ES values, and negative observed ES values are normalized against negative random ES values. NES therefore preserves the ES direction while making enrichment strength more comparable across pathways.",
      boundary:
        "NES is a normalized pathway-ranking score. It is not a fold change, DEG count, or percentage. NES alone does not establish statistical significance. The adjusted P value determines whether the pathway result is significant after multiple-testing correction. Comparisons across separate cohorts or ranking procedures still require caution.",
      sources:
        "Bioconductor fgsea documentation; scripts/lib/phase11_deg_pathway_common.R.",
      transition:
        "Part 7 examines how selected analysis thresholds affect the KDA results.",
    }),
  ],
]);

const EXPECTED_SLIDE_TEXT = new Map([
  [40, "PART 6"],
  [41, "Fine-cell summaries and direct broad-cell analysis answer different questions"],
  [42, "How direct broad-cell pathway validation was done"],
  [43, "direct broad-cell GSEA"],
  [44, "Standard weighted GSEA enrichment score for pathway"],
  [45, "How NES differs from ES"],
  [46, "PART 7"],
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

async function visibleSlideParts(zip) {
  const presentationXml = await zip.file("ppt/presentation.xml")?.async("string");
  const presentationRels = await zip
    .file("ppt/_rels/presentation.xml.rels")
    ?.async("string");
  if (!presentationXml || !presentationRels) {
    throw new Error("Presentation ordering metadata is missing");
  }
  const slideIds = [...presentationXml.matchAll(/<p:sldId\b[^>]*r:id="([^"]+)"[^>]*\/?\s*>/g)].map(
    (match) => match[1],
  );
  const relationships = [...presentationRels.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map(
    (match) => relationshipAttributes(match[0]),
  );
  return slideIds.map((relationshipId) => {
    const relation = relationships.find(
      (item) => item.Id === relationshipId && item.Type?.endsWith("/slide"),
    );
    if (!relation?.Target) {
      throw new Error(`Slide relationship ${relationshipId} was not found`);
    }
    return relation.Target.startsWith("/")
      ? relation.Target.slice(1)
      : path.posix.normalize(path.posix.join("ppt", relation.Target));
  });
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

function plainText(xml) {
  return [...xml.matchAll(/<a:t>([\s\S]*?)<\/a:t>/g)]
    .map((match) =>
      match[1]
        .replace(/&amp;/g, "&")
        .replace(/&lt;/g, "<")
        .replace(/&gt;/g, ">")
        .replace(/&quot;/g, '"')
        .replace(/&apos;/g, "'"),
    )
    .join(" ");
}

async function assertSlideSequence(zip, slideParts) {
  for (const [slideNumber, expected] of EXPECTED_SLIDE_TEXT) {
    const xml = await zip.file(slideParts[slideNumber - 1])?.async("string");
    if (!xml || !plainText(xml).includes(expected)) {
      throw new Error(`Slide ${slideNumber} does not contain ${JSON.stringify(expected)}`);
    }
  }
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
    throw new Error(`Source deck changed before the notes refresh: ${sourceHash}`);
  }

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

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const sourceSlideParts = await visibleSlideParts(sourceZip);
  await assertSlideSequence(sourceZip, sourceSlideParts);

  const beforePngs = new Map();
  for (const [slideNumber, updatedNotes] of NOTES_BY_SLIDE) {
    const slide = slides[slideNumber - 1];
    const beforePng = await blobBuffer(
      await presentation.export({ slide, format: "png", scale: 1.5 }),
    );
    beforePngs.set(slideNumber, beforePng);
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-before.png`), beforePng);
    slide.speakerNotes.textFrame.setText(updatedNotes);
    slide.speakerNotes.setVisible(true);
    const afterPng = await blobBuffer(
      await presentation.export({ slide, format: "png", scale: 1.5 }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-after.png`), afterPng);
    if (sha256(beforePng) !== sha256(afterPng)) {
      throw new Error(`Visible slide ${slideNumber} changed while updating notes`);
    }
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source deck changed during the notes refresh");
  }

  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const artifactSlideParts = await visibleSlideParts(artifactZip);
  const changedNotesParts = [];
  for (const slideNumber of NOTES_BY_SLIDE.keys()) {
    const sourceNotesPart = await notesPartForSlide(
      sourceZip,
      sourceSlideParts[slideNumber - 1],
    );
    const artifactNotesPart = await notesPartForSlide(
      artifactZip,
      artifactSlideParts[slideNumber - 1],
    );
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
  const validation = await finalizePresentation({
    explicitTotalSlideCount: EXPECTED_SLIDES,
    requiredNativeTableOwnerSlides: [],
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
    ],
    fontPolicy: {
      basis: "reference",
      families: ["Arial"],
      referencePath: SOURCE,
      referenceSha256: sourceHash,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD_DIR, "part6_notes_refresh.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const reopenedSlides = slidesFromPresentation(reopened);
  const notesSnapshot = await reopened.inspect({ kind: "notes", maxChars: 3000000 });
  const finalNotesBySlide = new Map(
    notesSnapshot.ndjson
      .split(/\r?\n/)
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
        scale: 1.5,
      }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-final.png`), finalPng);
    if (sha256(beforePngs.get(slideNumber)) !== sha256(finalPng)) {
      throw new Error(`Finalized deck changed visible slide ${slideNumber}`);
    }
    const actualNotes = finalNotesBySlide.get(slideNumber);
    if (typeof actualNotes !== "string" || actualNotes.trim() !== expectedNotes.trim()) {
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
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
        slideCount: EXPECTED_SLIDES,
        updatedSlides: [...NOTES_BY_SLIDE.keys()],
        visibleSlidesPreserved: true,
        changedParts,
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
