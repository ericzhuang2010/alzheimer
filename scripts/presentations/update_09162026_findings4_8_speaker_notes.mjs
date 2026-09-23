#!/usr/bin/env node

/** Refresh speaker notes for the manually revised Finding 4–8 slides. */

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
  "results/presentations/09162026_findings4_8_notes_refresh_20260921/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_findings4_8_notes_refresh_20260921/output/09162026_sex_apoe_kda_fine_broad_findings4_8_notes_refreshed_20260921.pptx",
);
const EXPECTED_SLIDES = 155;
const EXPECTED_SOURCE_SHA256 =
  "e1c0a1b39c4dbf2b864c31f24bc2e672e4f9344b3a653062c35f71c93e185cb0";

function notes({ goal, walkthrough, boundary, transition, sources }) {
  return [
    `Teaching goal: ${goal}`,
    "",
    `Walk through: ${walkthrough}`,
    "",
    `Scientific boundary: ${boundary}`,
    "",
    `Transition: ${transition}`,
    ...(sources ? ["", `Sources: ${sources}`] : []),
  ].join("\n");
}

const NOTES_BY_SLIDE = new Map([
  [
    77,
    notes({
      goal:
        "Explain how the cited studies support parts of Finding 4 and why the slide rates its novelty as moderate.",
      walkthrough:
        "Schmukler and colleagues link APOE4 models to altered mitochondrial dynamics and removal of damaged mitochondria, but they do not reproduce the nuclear-encoded OXPHOS gene-expression pattern. Lee and colleagues connect APOE4 astrocytes with impaired maintenance of mitochondrial function, but the cell context and experimental design differ. Mathys and colleagues demonstrate strong differences among brain cell states, but that work also uses ROSMAP and is not independent replication. These sources support parts of the interpretation. None establishes the complete female APOE ε4 finding. The slide therefore rates novelty as moderate.",
      boundary:
        "The novelty rating summarizes this focused literature comparison. It does not strengthen the direct evidence, and the finding remains sensitive to analysis resolution and lacks independent confirmation.",
      transition: "Move to the coordinated downward OXPHOS pattern in male APOE ε2 cells.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 4 literature context.",
    }),
  ],
  [
    83,
    notes({
      goal:
        "Explain how the cited studies frame Finding 5 and why the slide rates its novelty as high.",
      walkthrough:
        "Belloy and colleagues establish the population-level protection associated with APOE ε2, but inherited risk does not predict the molecular state of diseased male ε2 cells. Guo and colleagues support sex-aware network analysis but do not report this exact male ε2 decrease. Mathys and colleagues show that Alzheimer’s responses differ among brain cell populations, but the study also uses ROSMAP and cannot independently validate this pattern. None of these sources reproduces the coordinated decrease across both OXPHOS gene sets. The slide therefore rates novelty as high.",
      boundary:
        "The novelty rating comes from a focused literature comparison. The finding still lacks a matched SEA-AD category and functional validation.",
      transition:
        "Move to Finding 6, where male APOE ε4 cells may show opposite directions across the two OXPHOS gene sets.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 5 literature context.",
    }),
  ],
  [
    85,
    notes({
      goal: "Explain why Finding 6 is described as a possible OXPHOS mismatch.",
      walkthrough:
        "In male APOE ε4 cells, 87 of 110 core MT gene occurrences are upregulated in AD, whereas 55 of 89 nuclear-encoded OXPHOS gene occurrences are downregulated. This direction split resembles the male APOE ε3 homozygous pattern, but the nuclear-encoded decrease is less consistent. Direct broad-cell evidence also disagrees across cohorts. The slide therefore describes a possible mismatch that needs replication rather than a definitive mismatch.",
      boundary:
        "This is an RNA-level pattern. It does not demonstrate unbalanced respiratory proteins, impaired mitochondrial function, or a disease-by-APOE interaction.",
      transition: "Show the ROSMAP DEG-occurrence counts behind the direction split.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 6.",
    }),
  ],
  [
    89,
    notes({
      goal:
        "Explain how the cited studies frame Finding 6 and why the slide rates its novelty as moderate.",
      walkthrough:
        "Belloy and colleagues establish APOE ε4 as a major common risk allele for late-onset Alzheimer’s disease, but risk association does not validate the gene-expression direction split. Lee and colleagues show that APOE4 can alter mitochondrial homeostasis in astrocyte models, not in this male cell context. Guo and colleagues support testing Alzheimer’s molecular patterns separately by sex but do not establish this male ε4 pattern. The studies support the rationale for the analysis without reproducing the result. The slide rates novelty as moderate.",
      boundary:
        "The novelty rating comes from a focused literature comparison. The male ε4 direction split remains provisional because its nuclear-encoded component is weaker and cross-cohort broad-cell evidence disagrees.",
      transition: "Proceed to Finding 7 and the recurrent cytosolic-ribosome module.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 6 literature context.",
    }),
  ],
  [
    92,
    notes({
      goal:
        "Explain the three summary levels showing cytosolic-ribosome over-representation among genes returned from KDA calls.",
      walkthrough:
        "At the unique-gene level, 20 of 228 non-MitoCarta genes returned from KDA calls are KEGG ribosome genes, or 8.8 percent. In the exact network background, only 71 of 11,478 genes are ribosome genes, or 0.62 percent. The one-sided hypergeometric test remains significant after multiple-testing correction, with an adjusted P value of 3.56 times 10 to the minus 15. At the category level, ribosome genes occur in 19 of 29 categories that contain non-MitoCarta genes returned from KDA calls. They account for 70 of 381 gene-by-category units, or 18.4 percent. Within individual KDA calls, they account for 133 of 623 returned-gene occurrences, or 21.3 percent. These denominators represent different units and should not be combined.",
      boundary:
        "The enrichment result shows over-representation, not causal regulation of OXPHOS. Category and within-call occurrences can repeat the same genes and share donors, so they are descriptive recurrence summaries rather than independent replication counts.",
      transition: "Identify RPL11 and RPS15 as anchors of the recurrent ribosome module.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 7.",
    }),
  ],
  [
    95,
    notes({
      goal:
        "Explain how prior research and the current analysis frame Finding 7 and its moderate novelty rating.",
      walkthrough:
        "Ding and colleagues report impaired protein synthesis and RNA oxidation in human Alzheimer’s tissue, supporting a relationship between ribosome dysfunction and disease but not the ROSMAP ribosome-to-OXPHOS network. Zhang and colleagues show that RPL11 can signal through the MDM2 and p53 stress pathway, but that experiment does not prove mitochondrial regulation. The current analysis adds recurrence of multiple ribosomal genes across sex and APOE categories and OXPHOS neighborhoods. Shared donors and network connectivity limit the independence of that recurrence. The slide rates novelty as moderate.",
      boundary:
        "The literature establishes biological plausibility rather than the direction or causality of the inferred network relationship. The novelty rating comes from a focused literature comparison.",
      transition: "Proceed to Finding 8 and the LAMTOR5 lysosome-to-mitochondria hypothesis.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 7 literature context; https://doi.org/10.1523/JNEUROSCI.3040-05.2005; https://doi.org/10.1128/MCB.23.23.8902-8912.2003.",
    }),
  ],
  [
    101,
    notes({
      goal:
        "Explain how the cited studies support parts of Finding 8 and why the slide rates its novelty as high.",
      walkthrough:
        "Bar-Peled and colleagues place LAMTOR5 in Ragulator-dependent amino-acid sensing at the lysosome, but they do not test Alzheimer’s neurons or OXPHOS neighbors. Morita and colleagues connect mTORC1 with mitochondrial protein production and oxidative capacity, but they do not establish LAMTOR5 as the causal node in this network. Norambuena and colleagues show that amyloid beta can disrupt a neuronal lysosome-to-mitochondria signaling pathway, but they did not manipulate LAMTOR5. Together, the studies make the proposed bridge plausible without reproducing it. The slide rates novelty as high.",
      boundary:
        "The literature does not establish the inferred LAMTOR5 edges or their direction. The novelty rating comes from a focused literature comparison, and the finding still requires perturbation-based validation.",
      transition: "Proceed to Finding 9 and the WDR82-centered core MT gene neighborhood.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 8 literature context; https://doi.org/10.1016/j.cell.2012.07.032; https://doi.org/10.1016/j.cmet.2013.10.001; https://doi.org/10.15252/embj.2018100241.",
    }),
  ],
]);

const EXPECTED_SLIDE_TEXT = new Map([
  [77, "Prior research and evidence context for Finding 4"],
  [83, "Prior research and evidence context for Finding 5"],
  [85, "Male ε4 cells may show opposite directions in OXPHOS gene expression"],
  [89, "Prior research and evidence context for Finding 6"],
  [92, "cytosolic ribosome genes are strongly over-represented"],
  [95, "Prior research and evidence context for Finding 7"],
  [101, "Prior research and evidence context for Finding 8"],
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
    receiptPath: path.join(BUILD_DIR, "findings4_8_notes_refresh.validation.json"),
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
