#!/usr/bin/env node

/** Refresh speaker notes after the user's latest manual slide edits. */

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
  "results/presentations/09162026_manual_edits_notes_refresh_20260922_v1",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_notes_refreshed_20260922_v1.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "e313330c0d9d352fe4c9c6f97a42e640be58492aa5d49e930bc241da2c51b5e0";
const EXPECTED_SLIDES = 160;

function notes({ goal, walkthrough, boundary, transition, sources }) {
  return [
    `Teaching goal: ${goal}`,
    "",
    `Walk through: ${walkthrough}`,
    "",
    `Scientific boundary: ${boundary}`,
    "",
    `Transition: ${transition}`,
    "",
    `Sources: ${sources}`,
  ].join("\n");
}

const NOTES_BY_SLIDE = new Map([
  [
    102,
    notes({
      goal:
        "Explain the proposed connection between lysosomal nutrient sensing and nuclear-encoded OXPHOS genes.",
      walkthrough:
        "Begin with the lysosome, which breaks down cellular material and also helps the cell sense nutrient availability. LAMTOR5 belongs to a protein complex on the lysosome that helps amino-acid availability regulate mTORC1. In the ROSMAP KDA results, LAMTOR5 was returned from 17 neuronal KDA calls across six categories. The mitochondrial genes connected to LAMTOR5 were mainly nuclear-encoded OXPHOS genes with lower expression in AD. Together, these observations suggest a possible relationship between lysosomal nutrient sensing and the amount of mitochondrial respiration the cell carries out.",
      boundary:
        "KDA identifies a network relationship. It does not show whether LAMTOR5 changes OXPHOS genes, whether mitochondrial changes affect LAMTOR5, or whether another process affects both.",
      transition: "Show the ROSMAP evidence supporting the repeated LAMTOR5 result.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 8; https://doi.org/10.1016/j.cell.2012.07.032; https://doi.org/10.1016/j.cmet.2013.10.001; https://doi.org/10.15252/embj.2018100241",
    }),
  ],
  [
    104,
    notes({
      goal:
        "Explain why GABARAPL2, ATG101, and ATP6AP2 provide additional support for the lysosome-to-mitochondria interpretation.",
      walkthrough:
        "These genes were identified independently of LAMTOR5. GABARAPL2 participates in autophagy, including delivery of cellular material to lysosomes, and appeared in 13 KDA calls across five categories. ATG101 helps begin autophagosome formation and appeared in six calls across three categories. ATP6AP2 supports the V-ATPase system that acidifies lysosomes and also appeared in six calls across three categories. Each gene was connected to mitochondrial genes in the ROSMAP networks. The repeated pattern therefore supports a broader relationship among lysosome function, autophagy, and mitochondria rather than relying on LAMTOR5 alone. SEA-AD had no KDA call in the matching sex/APOE and cell categories, so it could not test these results directly.",
      boundary:
        "The three genes are functionally related to the same biological process. The analysis does not show that they directly interact with LAMTOR5 or that any of them causally regulates the connected mitochondrial genes.",
      transition: "Explain why established nutrient-sensing biology makes LAMTOR5 testable.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 8; https://www.ncbi.nlm.nih.gov/gene/11345; https://www.ncbi.nlm.nih.gov/gene/60673; https://doi.org/10.1073/pnas.1507263112; https://doi.org/10.1161/CIRCRESAHA.110.224667",
    }),
  ],
  [
    105,
    notes({
      goal:
        "Explain why previous biology supports a LAMTOR5 experiment without treating the KDA connections as proven regulation.",
      walkthrough:
        "Amino acids activate mTORC1 at the lysosome. The Ragulator complex, which contains LAMTOR5, helps place this nutrient-sensing machinery at the lysosomal surface. mTORC1 can then change cellular protein production, including production of nuclear-encoded mitochondrial proteins, and can affect respiratory capacity. Alzheimer’s-related experimental work also shows that amyloid-beta can disrupt communication between lysosomes and mitochondria in neurons. These findings make a direct LAMTOR5 experiment reasonable. For example, one could reduce or increase LAMTOR5 and then measure lysosomal acidity, mTORC1 activity, OXPHOS gene expression, OXPHOS proteins, and respiration.",
      boundary:
        "Previous experiments have not shown that LAMTOR5 directly regulates the mitochondrial genes connected to it in the ROSMAP KDA results. The KDA connections are inferred from a gene network and do not establish causal direction.",
      transition: "Compare this interpretation with the specific support and limitations of prior studies.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 8; https://doi.org/10.1016/j.cell.2012.07.032; https://doi.org/10.1016/j.cmet.2013.10.001; https://doi.org/10.15252/embj.2018100241",
    }),
  ],
  [
    118,
    notes({
      goal: "Explain how prior studies support and limit the interpretation of SELENOM.",
      walkthrough:
        "Ferguson and colleagues identify SELENOM as an endoplasmic-reticulum protein involved in reversible oxidation reactions. Yim and colleagues show that SELENOM affects oxidation and calcium regulation in neurons. Experimental amyloid-beta studies connect SELENOM with amyloid-related and mitochondrial outcomes in cells or animals. These studies make the proposed biology plausible, but none reproduces the ROSMAP network connections in human AD neurons. The slide therefore assigns high novelty to the specific network finding.",
      boundary:
        "High novelty means that the focused literature review did not identify a direct prior report of the same relationship. It does not mean that the current evidence is strong or causal.",
      transition: "Proceed to Finding 11 and the SELENOW result.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 10; https://doi.org/10.1074/jbc.M511386200; https://doi.org/10.3892/ijmm_00000211; https://doi.org/10.3390/ijms14034385",
    }),
  ],
  [
    124,
    notes({
      goal: "Explain how prior studies support and limit the interpretation of SELENOW.",
      walkthrough:
        "Misra and colleagues show that loss of SELENOW changes oxidative stress and mitochondrial respiration, although their experiments used macrophages rather than neurons. Ren and colleagues report improved tau clearance and other outcomes after increasing SELENOW in a mouse model of AD. The current ROSMAP analysis adds human neuronal connections to respiration and removal of damaged mitochondrial proteins. Together, these results support biological plausibility without proving the direction of regulation. The slide assigns moderate novelty to the human neuronal network finding.",
      boundary:
        "Moderate novelty describes what this analysis adds beyond prior work. It does not convert evidence from macrophages, mice, or KDA into proof of a causal neuronal mechanism.",
      transition: "Proceed to Finding 12 and the PGK1-centered astrocyte result.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 11; https://doi.org/10.1016/j.redox.2022.102571; https://doi.org/10.1038/s42003-024-06572-0",
    }),
  ],
  [
    130,
    notes({
      goal: "Explain how prior studies support and limit the interpretation of PGK1 in astrocytes.",
      walkthrough:
        "Mathys and colleagues report groups of glial genes that include PGK1 and BNIP3L and change together in human AD, although that study also uses ROSMAP and may share donors with this analysis. Schmukler and colleagues connect APOE4 astrocytes with altered mitochondrial shape and removal of damaged mitochondria. Lee and colleagues connect lysosomal cholesterol with reduced removal of damaged mitochondria and impaired respiration. These studies support the proposed biological setting but do not show that PGK1 controls BNIP3-family genes. The slide assigns moderate novelty to the specific KDA connection.",
      boundary:
        "The literature supports related astrocyte biology, not the direction or causality of the PGK1 network result. Shared ROSMAP donors also prevent the Mathys study from serving as independent replication.",
      transition: "Proceed to Finding 13 and the OPC iron-stress result.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 12; https://doi.org/10.1038/s41586-024-07606-7; https://doi.org/10.1038/s41419-020-02776-4; https://doi.org/10.1016/j.celrep.2023.113183",
    }),
  ],
  [
    136,
    notes({
      goal: "Explain how prior studies support and limit the OPC iron-stress interpretation.",
      walkthrough:
        "Experimental work shows that reduced GPX4 protection can make OPCs vulnerable to iron-dependent lipid damage. Transcriptomic studies also report oxytosis- and ferroptosis-related expression patterns in AD datasets. The current ROSMAP analysis adds focused connections among FTL, ANKRD11, GPX4, and genes involved in recycling damaged cellular material. This combination motivates an OPC iron-stress hypothesis, and the slide assigns high novelty to the specific human network relationship.",
      boundary:
        "Expression patterns do not demonstrate that ferroptotic cell death occurred. Only one OPC fine cell type contributes to the KDA result, so the finding remains narrow.",
      transition: "Proceed to Finding 14 and the PLCG2 result.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 13; https://pmc.ncbi.nlm.nih.gov/articles/PMC8941078/; https://doi.org/10.1186/s12915-025-02235-6",
    }),
  ],
  [
    142,
    notes({
      goal: "Explain why PLCG2 has strong genetic relevance but weak support for the specific MT-CO1 connection.",
      walkthrough:
        "The Phase 19b genetic screen provides strong Alzheimer’s gene-level support for PLCG2. Prior work on the protective P522R variant shows a small increase in one PLCG2 function, and a 2026 study reports neuron-intrinsic PLCG2 effects on synapses, amyloid-beta, and tau. These findings establish PLCG2 as an important AD gene to investigate. None of them demonstrates that PLCG2 regulates MT-CO1 or confirms the cell-specific network connections in this analysis. The slide assigns high novelty to that specific proposed relationship.",
      boundary:
        "High novelty does not imply high confidence. The PLCG2-to-MT-CO1 result is narrow, and gene-level genetic support cannot validate a particular cell context or KDA connection.",
      transition: "Proceed to Finding 15 and the astrocyte APOE result.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 14; https://doi.org/10.1186/s13195-019-0469-0; https://doi.org/10.1038/s41588-026-02709-5",
    }),
  ],
  [
    148,
    notes({
      goal: "Explain how established APOE biology supports but does not resolve the astrocyte network result.",
      walkthrough:
        "Human genetics establishes APOE as the strongest common risk locus for late-onset AD. Experimental studies show that APOE-related changes in astrocytes can alter mitochondrial function, mitochondrial shape, and removal of damaged mitochondria. This literature makes an astrocyte APOE-to-mitochondria relationship plausible. It does not explain why APOE changes in opposite directions across the sex/APOE groups shown here, and it does not confirm the three different sets of KDA connections. The slide assigns moderate novelty to this context-specific result.",
      boundary:
        "The current result includes epsilon-2 groups as well as epsilon-4. Established APOE4 biology therefore cannot be applied automatically to every group on the slide.",
      transition: "Proceed to Finding 16 and the female epsilon-4 vascular stress-response result.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 15; https://doi.org/10.1016/j.neuron.2019.03.075; https://doi.org/10.1016/j.celrep.2023.113183; https://doi.org/10.1038/s41419-020-02776-4",
    }),
  ],
  [
    154,
    notes({
      goal: "Explain the evidence supporting the female epsilon-4 vascular stress-response result.",
      walkthrough:
        "The current pathway test shows that female epsilon-4 vascular KDA calls returned several genes controlled by HSF1, a regulator of the cellular response to damaged or misfolded proteins. Guo and colleagues support analyzing AD networks separately by cell type and sex. Mathys and colleagues also show that AD-related gene expression differs among brain cell populations. Those studies support the analysis strategy, but they do not independently report this particular group of vascular stress-response genes. The slide assigns moderate novelty to the result.",
      boundary:
        "The result depends on only three related genes from two KDA calls. It should therefore be treated as a focused hypothesis rather than a broadly established vascular response.",
      transition: "Proceed to Finding 17 and the cross-cohort comparison.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7",
    }),
  ],
  [
    160,
    notes({
      goal: "Summarize what the cross-cohort comparisons support and where the evidence remains limited.",
      walkthrough:
        "For female epsilon-3 homozygous excitatory neurons, nine core MT genes are upregulated in AD in both cohorts, and the adjusted overlap P value is 0.00505. Only one matched SEA-AD KDA call was available, so the coverage is narrow. For male epsilon-3 homozygous inhibitory neurons, 19 of 22 shared DEG genes change in the same direction across the contributing fine cell types, although the direct broad-cell ROSMAP result depends on cell composition. At the level of genes returned from KDA calls, three genes occur in both cohorts. That overlap is greater than the average expected by chance, but P equals 0.0812 and does not meet the significance threshold. The slide assigns moderate novelty to this combined cross-cohort assessment.",
      boundary:
        "The strongest agreement occurs at the level of mitochondrial DEG patterns. The analysis does not show that the same gene controls those patterns in both cohorts, and the three-gene KDA overlap is not statistically significant.",
      transition: "Close with the strongest mitochondrial results and the experiments needed to test causality.",
      sources:
        "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md, Finding 17",
    }),
  ],
]);

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
  if (slides.length !== EXPECTED_SLIDES) {
    throw new Error(`Expected ${EXPECTED_SLIDES} slides, found ${slides.length}`);
  }

  for (const [slideNumber, updatedNotes] of NOTES_BY_SLIDE) {
    slides[slideNumber - 1].speakerNotes.textFrame.setText(updatedNotes);
    slides[slideNumber - 1].speakerNotes.setVisible(true);
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("Source changed during speaker-note editing");
  }

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
    explicitTotalSlideCount: EXPECTED_SLIDES,
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
  const notesSnapshot = await reopened.inspect({ kind: "notes", maxChars: 5000000 });
  const finalNotesBySlide = new Map(
    notesSnapshot.ndjson
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text || ""]),
  );
  for (const [slideNumber, expectedNotes] of NOTES_BY_SLIDE) {
    if (finalNotesBySlide.get(slideNumber) !== expectedNotes) {
      throw new Error(`Final speaker notes do not match for slide ${slideNumber}`);
    }
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const actualParts = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) actualParts.push(name);
  }
  actualParts.sort();
  changedNotesParts.sort();
  if (
    actualParts.length !== changedNotesParts.length ||
    actualParts.some((name, index) => name !== changedNotesParts[index])
  ) {
    throw new Error(`Unexpected package changes: ${actualParts.join(", ")}`);
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
        updatedNotesSlides: [...NOTES_BY_SLIDE.keys()],
        changedParts: actualParts,
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
