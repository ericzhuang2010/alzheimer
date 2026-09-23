#!/usr/bin/env node

/** Refresh speaker notes after the user's latest visual edits to finding slides. */

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
  "results/presentations/09162026_latest_manual_edits_notes_refresh_20260922_v1",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_notes_refreshed_after_manual_edits_20260922_v1.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "5e71cb86c62a1cbbd884462a7eedc25aee34e2da5cc30af535db5ab2e8f9d451";
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

const ANALYSIS_SOURCE =
  "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md";

const NOTES_BY_SLIDE = new Map([
  [
    97,
    notes({
      goal:
        "Explain the ribosome enrichment result and keep the four denominators distinct.",
      walkthrough:
        "Start with the three boxes across the top. Twenty of 228 unique non-MitoCarta genes returned from KDA calls are KEGG ribosome genes, or 8.8 percent. In the same network backgrounds, only 71 of 11,478 genes available for selection are ribosome genes, or 0.62 percent. This difference gives a one-sided, multiple-testing-adjusted P value of 3.56 times 10 to the minus 15. Then move through the three lower rows. Ribosome genes occur in 19 of 29 categories, account for 70 of 381 gene-by-category pairs, and account for 133 of 623 returned-gene occurrences within KDA calls. Each row uses a different unit, so the denominators should not be combined.",
      boundary:
        "The enrichment result shows over-representation, not causal regulation of OXPHOS. Categories, gene-by-category pairs, and within-call occurrences can repeat genes and share donors, so they are descriptive recurrence summaries rather than independent replications.",
      transition:
        "Use RPL11 and RPS15 as examples of the recurring ribosome genes, then consider biological and technical interpretations.",
      sources: `${ANALYSIS_SOURCE}, Finding 7.`,
    }),
  ],
  [
    99,
    notes({
      goal:
        "Present the three interpretations of the recurring ribosome-gene result without choosing one prematurely.",
      walkthrough:
        "Read the three panels from left to right. The biological model notes that cells must produce nuclear-encoded OXPHOS proteins before respiratory complexes can assemble, so protein production and respiration can change together. The stress model notes that experimental systems connect RPL11 with MDM2 and p53 signaling. The technical model notes that genes with many network connections may be returned more often from KDA calls. The footer gives the most cautious interpretation: compare genes with similar numbers of network connections before treating recurring ribosome genes as regulators.",
      boundary:
        "These models are alternatives, and more than one may contribute. The current analysis does not establish causal direction or show that the ribosome genes regulate OXPHOS genes.",
      transition:
        "Compare the current result with prior ribosome and RPL11 research.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 7; https://doi.org/10.1523/JNEUROSCI.3040-05.2005; https://doi.org/10.1128/MCB.23.23.8902-8912.2003`,
    }),
  ],
  [
    100,
    notes({
      goal:
        "Explain which part of Finding 7 each source supports and why the novelty rating is moderate.",
      walkthrough:
        "Read the columns from left to right. Ding and colleagues support ribosome dysfunction in human Alzheimer’s tissue, but they do not establish the ROSMAP ribosome-to-OXPHOS network. Zhang and colleagues show that RPL11 can signal through MDM2 and p53, but that stress pathway does not prove mitochondrial regulation. The current ROSMAP analysis adds recurrence of several ribosome genes across categories and repeated connections to OXPHOS genes. Shared donors and the tendency of highly connected genes to be selected more often limit the independence of that recurrence. Taken together, the focused literature comparison supports a moderate novelty rating.",
      boundary:
        "Moderate novelty describes what the current network result adds beyond prior research. It does not mean that the result is causal or independently replicated.",
      transition:
        "Proceed to Finding 8 and the proposed connection between LAMTOR5 and nuclear-encoded OXPHOS genes.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 7; https://doi.org/10.1523/JNEUROSCI.3040-05.2005; https://doi.org/10.1128/MCB.23.23.8902-8912.2003`,
    }),
  ],
  [
    102,
    notes({
      goal:
        "Explain the proposed connection between lysosomal nutrient sensing and nuclear-encoded OXPHOS genes.",
      walkthrough:
        "The top labels summarize the scope: LAMTOR5 was returned from 17 neuronal KDA calls across six categories. Then follow the three large panels from left to right. Lysosomes recycle cellular material and help cells sense nutrient availability. LAMTOR5 is part of the lysosomal complex that relays amino-acid availability to mTORC1. The mitochondrial side contains mainly nuclear-encoded OXPHOS genes with lower expression in AD. Together, the panels suggest a possible relationship between lysosomal nutrient sensing and mitochondrial respiration.",
      boundary:
        "KDA identifies network relationships. It does not show whether LAMTOR5 changes OXPHOS genes, whether mitochondrial changes affect LAMTOR5, or whether another process affects both.",
      transition:
        "Show the ROSMAP counts and directions that support the repeated LAMTOR5 result.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 8; https://doi.org/10.1016/j.cell.2012.07.032; https://doi.org/10.1016/j.cmet.2013.10.001; https://doi.org/10.15252/embj.2018100241`,
    }),
  ],
  [
    103,
    notes({
      goal: "Present the primary ROSMAP evidence for Finding 8.",
      walkthrough:
        "Start with the three summary boxes. Seventeen neuronal KDA calls across six categories support the result. LAMTOR5 has 87 connections to MitoCarta MT genes, including 39 nuclear-encoded OXPHOS genes. Fourteen of the 17 DEG input sets show significant enrichment of nuclear-encoded OXPHOS genes. Then read the three evidence rows. Thirty of the 39 connected nuclear-encoded OXPHOS genes have lower expression in AD. Frequently connected genes include ATP5IF1, CHCHD10, and ATP5MC2. LAMTOR5 itself is a DEG in 11 of the 17 calls, but its direction differs: it increases in female epsilon-2 excitatory calls and decreases in the strongest male epsilon-2 calls.",
      boundary:
        "The 87 value counts network connections, while 39 counts nuclear-encoded OXPHOS genes. KDA calls can share genes and donors, and the direction of LAMTOR5 itself is not uniform across groups.",
      transition:
        "Separate the repeated network result from evidence about cell context and cross-cohort support.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 8; https://doi.org/10.1016/j.cell.2012.07.032; https://doi.org/10.1016/j.cmet.2013.10.001; https://doi.org/10.15252/embj.2018100241`,
    }),
  ],
  [
    106,
    notes({
      goal:
        "Explain which part of Finding 8 each prior study supports and why the novelty rating is high.",
      walkthrough:
        "Read the three columns from left to right. Bar-Peled and colleagues place LAMTOR5 in amino-acid sensing at lysosomes, but they do not test Alzheimer’s neurons or OXPHOS connections. Morita and colleagues connect mTORC1 with mitochondrial protein production and respiratory capacity, but they do not show that LAMTOR5 causes the relationship observed here. Norambuena and colleagues show that amyloid beta disrupts lysosome-to-mitochondria communication in neurons, but they did not manipulate LAMTOR5. The studies support separate parts of the interpretation without reproducing the full network result, which is why the slide rates novelty as high.",
      boundary:
        "High novelty does not mean high causal confidence. The proposed LAMTOR5-to-OXPHOS relationship still requires direct perturbation and replication.",
      transition:
        "Proceed to Finding 9 and the core MT genes connected to WDR82.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 8; https://doi.org/10.1016/j.cell.2012.07.032; https://doi.org/10.1016/j.cmet.2013.10.001; https://doi.org/10.15252/embj.2018100241`,
    }),
  ],
  [
    114,
    notes({
      goal:
        "Explain how SELENOM connects an endoplasmic-reticulum process with mitochondrial protein production in the KDA results.",
      walkthrough:
        "The top labels show that SELENOM was returned from 12 neuronal KDA calls covering all six sex and APOE groups. Read the three panels from left to right. SELENOM helps control reversible oxidation reactions in the endoplasmic reticulum, or ER. The middle panel defines the connected mitochondrial process: mitochondrial ribosomes and related factors make proteins encoded by core MT genes. The right panel shows the observed network pattern: genes directly connected to SELENOM are mainly mitochondrial protein-production genes with lower expression in AD. SELENOM itself is not part of the mitochondrial ribosome.",
      boundary:
        "The network places these genes close to SELENOM, but it does not show that SELENOM regulates mitochondrial protein production or explain causal direction.",
      transition: "Show the ROSMAP counts behind the SELENOM result.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 10; https://doi.org/10.1074/jbc.M511386200; https://doi.org/10.3892/ijmm_00000211; https://doi.org/10.3390/ijms14034385`,
    }),
  ],
  [
    120,
    notes({
      goal:
        "Explain the several mitochondrial functions connected to SELENOW and distinguish SELENOW from SELENOM.",
      walkthrough:
        "The top labels show 16 neuronal KDA calls across six categories. The three panels organize the connected genes by function. NDUFB11, COA3, and CYC1 support mitochondrial respiration. MRPS34 and MRPL34 help mitochondria produce proteins encoded by core MT genes. CLPP removes damaged mitochondrial proteins, while other connected genes transport molecules across the inner mitochondrial membrane. The connection therefore spans respiration, mitochondrial protein production, and removal of damaged proteins rather than one narrow OXPHOS pathway. SELENOW and SELENOM are different genes and should not be treated as the same mechanism.",
      boundary:
        "These are network connections, not proof that SELENOW controls every connected process or that all connected genes change through one mechanism.",
      transition: "Show the ROSMAP evidence supporting the SELENOW result.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 11; https://doi.org/10.1016/j.redox.2022.102571; https://doi.org/10.1038/s42003-024-06572-0`,
    }),
  ],
  [
    126,
    notes({
      goal:
        "Explain the proposed astrocyte connection between glycolysis and recycling of damaged mitochondria.",
      walkthrough:
        "The top labels identify three astrocyte KDA calls. Read the three panels from left to right. PGK1 participates in glycolysis, which breaks down glucose outside mitochondria. FAM162A and BNIP3 respond to low oxygen or mitochondrial damage. BNIP3L can help mark damaged mitochondria for recycling. This small connected set suggests a relationship between glucose breakdown and removal of damaged mitochondria.",
      boundary:
        "The result involves a small number of genes and does not show that PGK1 broadly controls OXPHOS or directly regulates the mitochondrial-damage genes.",
      transition: "Show the ROSMAP evidence supporting the PGK1-centered result.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 12; https://doi.org/10.1038/s41586-024-07606-7; https://doi.org/10.1038/s41419-020-02776-4; https://doi.org/10.1016/j.celrep.2023.113183`,
    }),
  ],
  [
    132,
    notes({
      goal:
        "Explain the proposed OPC connection among iron storage, protection from lipid damage, and recycling of damaged cell components.",
      walkthrough:
        "OPCs are oligodendrocyte precursor cells that can mature into myelin-producing cells. Read the panels from left to right. FTL and FTH1 form ferritin, which stores iron in a safer form and limits free iron. GPX4 helps protect membrane fats from oxidation. FIS1, PARK7, and PHB2 connect FTL and ANKRD11 with mitochondrial stress and recycling of damaged cell components. Together, the network suggests a relationship between iron handling and cellular cleanup.",
      boundary:
        "The result does not demonstrate ferroptosis. That would require direct measurement of iron-dependent lipid damage and rescue with a ferroptosis inhibitor.",
      transition: "Show the ROSMAP evidence supporting this OPC result.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 13; https://pmc.ncbi.nlm.nih.gov/articles/PMC8941078/; https://doi.org/10.1186/s12915-025-02235-6`,
    }),
  ],
  [
    138,
    notes({
      goal:
        "Separate the strong gene-level support for PLCG2 from the narrow PLCG2-to-MT-CO1 network result.",
      walkthrough:
        "Read the panels from left to right. Human genetic variants make PLCG2 an important Alzheimer’s disease gene to study. In this analysis, PLCG2 was returned from six female inhibitory-neuron KDA calls spanning epsilon-2, epsilon-3 homozygous, and epsilon-4 groups. However, MT-CO1 is the only MitoCarta MT gene directly connected to PLCG2 across those calls. The slide therefore distinguishes established relevance of PLCG2 from uncertainty about this specific network connection.",
      boundary:
        "Gene-level genetic evidence does not validate a particular cell context or prove that PLCG2 regulates MT-CO1. KDA can return a gene because of its network position even when that gene is not a DEG.",
      transition: "Show the ROSMAP evidence and the limits of the PLCG2 result.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 14; https://doi.org/10.1186/s13195-019-0469-0; https://doi.org/10.1038/s41588-026-02709-5`,
    }),
  ],
  [
    144,
    notes({
      goal:
        "Show why the astrocyte APOE result cannot be summarized as an epsilon-4-specific direction.",
      walkthrough:
        "The top labels identify astrocytes, three sex and APOE groups, and opposite directions. Read the three panels from left to right. APOE increases in the supporting female epsilon-2 astrocyte KDA call, with a log fold change of plus 0.79. APOE decreases in male epsilon-2, with a log fold change of minus 0.51, and decreases in male epsilon-4, with a log fold change of minus 1.25. The directions therefore differ across groups and do not support an epsilon-4-only statement.",
      boundary:
        "These within-group directions do not by themselves prove a statistical sex-by-APOE interaction. A direct interaction model is needed.",
      transition: "Show the KDA connections associated with the three astrocyte results.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 15; https://doi.org/10.1016/j.neuron.2019.03.075; https://doi.org/10.1016/j.celrep.2023.113183; https://doi.org/10.1038/s41419-020-02776-4`,
    }),
  ],
  [
    150,
    notes({
      goal:
        "Explain the small protein-stress signal returned from female epsilon-4 vascular KDA calls.",
      walkthrough:
        "The top labels define the context: female epsilon-4 vascular cells and two eligible KDA calls. The three panels name the returned genes. HSPA1A helps proteins fold correctly or recover during stress. HSPH1 works with other heat-shock proteins to help damaged proteins refold. PTGES3 also has protein-folding functions in addition to its other cellular roles. Heat-shock genes respond to many forms of cellular stress, so the result does not imply literal exposure to high temperature.",
      boundary:
        "Only three related genes from two KDA calls support this result. They provide a focused clue, not evidence of a broad vascular stress response.",
      transition: "Show the pathway-test counts and adjusted P values.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7`,
    }),
  ],
  [
    151,
    notes({
      goal:
        "Present the counts and pathway tests supporting the female epsilon-4 vascular stress result.",
      walkthrough:
        "Start with the three boxes. Five unique non-MitoCarta genes were returned from female epsilon-4 vascular KDA calls. Three are stress-response genes: HSPH1, HSPA1A, and PTGES3. Only two eligible vascular KDA calls contribute. Then move to the pathway rows. Genes controlled by HSF1 have a BH-adjusted P value of 4.07 times 10 to the minus 4. Cellular response to protein stress has a BH-adjusted P value of 0.00383. The last row explains that the same three genes contribute to several related pathway results, so those pathway results are not independent observations.",
      boundary:
        "The pathway test compares the five returned genes with genes available in the vascular network and remains exploratory. The result does not show that the cells experienced heat exposure or a broad stress response.",
      transition:
        "Place the result in its limited cell-resolution and cross-cohort context.",
      sources:
        `${ANALYSIS_SOURCE}, Finding 16; https://doi.org/10.1186/s13024-023-00624-5; https://doi.org/10.1038/s41586-024-07606-7`,
    }),
  ],
  [
    156,
    notes({
      goal:
        "Explain why cross-cohort agreement is stronger for mitochondrial gene sets than for exact genes returned from KDA calls.",
      walkthrough:
        "The subtitle defines exact context as the same gene, sex and APOE group, and broad cell class in both cohorts. Read the three panels from left to right. Under the strict comparison, no testable non-MitoCarta gene returned from a ROSMAP KDA call was also returned in the same SEA-AD context. Under the broader comparison, LAGE3, MIPOL1, and PAPOLA are returned in both cohorts, but in different sex and APOE or cell settings. The strongest cross-cohort support is therefore the similar mitochondrial gene-set evidence in female epsilon-3 homozygous and male epsilon-3 homozygous groups.",
      boundary:
        "ROSMAP and SEA-AD use cohort-specific networks, so they can return different genes even when they point to similar mitochondrial biology. A gene found in different contexts does not count as exact replication.",
      transition: "Show the specific DEG and gene-set comparisons across cohorts.",
      sources: `${ANALYSIS_SOURCE}, Finding 17.`,
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
