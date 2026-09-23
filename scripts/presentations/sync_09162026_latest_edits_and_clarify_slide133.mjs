#!/usr/bin/env node

/** Synchronize notes with the latest manual edits, then clarify ANKRD11 on slide 133. */

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
  "results/presentations/09162026_sync_latest_manual_edits_then_clarify_slide133_20260922_v2",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_notes_synced_slide133_clarified_20260922_v2.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "6a7d85e76110775ab4a383c3448d8d19ba7d7fa411733c791b58c47770f9b74d";
const SLIDE_COUNT = 154;
const CHANGED_SLIDES = [133];

const ANALYSIS_SOURCE =
  "docs/analysis/kda_w_human_validation/rosmap_sex_apoe_broad_kda_analysis.md";

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

const FINDING9_SOURCES =
  `${ANALYSIS_SOURCE}, Finding 9; ` +
  "https://doi.org/10.1128/MCB.01356-07; " +
  "https://doi.org/10.1016/j.cell.2011.06.051; " +
  "https://doi.org/10.3892/mmr.2015.4271";
const FINDING10_SOURCES =
  `${ANALYSIS_SOURCE}, Finding 10; ` +
  "https://doi.org/10.1074/jbc.M511386200; " +
  "https://doi.org/10.3892/ijmm_00000211; " +
  "https://doi.org/10.3390/ijms14034385";
const FINDING11_SOURCES =
  `${ANALYSIS_SOURCE}, Finding 11; ` +
  "https://doi.org/10.1016/j.redox.2022.102571; " +
  "https://doi.org/10.1038/s42003-024-06572-0";
const FINDING12_SOURCES =
  `${ANALYSIS_SOURCE}, Finding 12; ` +
  "https://doi.org/10.1038/s41586-024-07606-7; " +
  "https://doi.org/10.1038/s41419-020-02776-4; " +
  "https://doi.org/10.1016/j.celrep.2023.113183";
const FINDING13_SOURCES =
  `${ANALYSIS_SOURCE}, Finding 13; ` +
  "https://pmc.ncbi.nlm.nih.gov/articles/PMC8941078/; " +
  "https://doi.org/10.1186/s12915-025-02235-6";

const NOTES_BY_SLIDE = new Map([
  [
    108,
    notes({
      goal:
        "Explain the focused WDR82 result and why the four connected core MT genes do not provide four independent observations.",
      walkthrough:
        "The result occurs only in excitatory neurons and is supported by 18 KDA calls. WDR82 helps regulate which nuclear genes are active and is not part of the mitochondrial ribosome. Nearly every direct mitochondrial connection involves MT-ND1, MT-ND3, MT-ND4L, or MT-ND5. The mitochondrial heavy strand produces these four genes from one long RNA that is later processed into separate gene products. Their shared starting transcript can make their expression correlated.",
      boundary:
        "The shared transcript does not make the four mature RNAs identical, because their processing and stability can differ. KDA does not show that WDR82 regulates these genes.",
      transition:
        "Show the number and direction of core MT gene occurrences in the supporting KDA calls.",
      sources: FINDING9_SOURCES,
    }),
  ],
  [
    109,
    notes({
      goal: "Present the primary ROSMAP evidence supporting the WDR82 result.",
      walkthrough:
        "All 18 supporting excitatory KDA input DEG sets show significant enrichment of upregulated core MT genes. The inputs contain 172 core MT gene occurrences, all upregulated in AD. Of the 70 direct gene connections to WDR82, 68 involve MT-ND1, MT-ND3, MT-ND4L, or MT-ND5, while the remaining two involve PIM1. WDR82 itself did not meet the DEG definition in any of the 18 calls. Thirteen calls had an FDR below 0.05, but their WDR82 expression changes remained below the effect-size cutoff.",
      boundary:
        "Gene occurrences can repeat across KDA calls and do not represent independent donors. KDA can return a gene because of its network position even when the gene itself is not a DEG.",
      transition:
        "Show which sex and APOE groups contribute the WDR82 KDA calls.",
      sources: FINDING9_SOURCES,
    }),
  ],
  [
    110,
    notes({
      goal: "Describe the sex and APOE distribution of the WDR82 KDA calls.",
      walkthrough:
        "Female APOE epsilon-2 contributes two excitatory KDA calls. Female APOE epsilon-3 homozygous contributes 11 calls and provides most of the evidence. Male groups contribute five calls, including two male epsilon-3 homozygous and three male epsilon-4 calls. SEA-AD contained 11 matching excitatory-neuron networks in which WDR82 could have been returned, but it was not. SEA-AD still supports the female epsilon-3 homozygous core MT gene pattern.",
      boundary:
        "The concentration of calls in one group does not establish a formal sex-by-APOE interaction. Different cohort networks and sample sizes limit interpretation of a gene that was testable but not returned in SEA-AD.",
      transition: "Explain the possible biological and technical interpretations.",
      sources: FINDING9_SOURCES,
    }),
  ],
  [
    111,
    notes({
      goal:
        "Explain the three interpretations of the WDR82 and core MT gene relationship.",
      walkthrough:
        "One biological explanation is that nuclear gene regulation indirectly affects mitochondrial RNA production. A second explanation is that the repeated core MT genes mainly reflect overall mitochondrial RNA abundance or sample quality. A network-based explanation is that four connected gene names arise from one shared long mitochondrial RNA rather than four separate mechanisms.",
      boundary:
        "The current analysis cannot distinguish these explanations or establish that WDR82 changes mitochondrial RNA abundance.",
      transition: "Compare the interpretation with prior research.",
      sources: FINDING9_SOURCES,
    }),
  ],
  [
    112,
    notes({
      goal:
        "Explain which part of the WDR82 interpretation each prior source supports.",
      walkthrough:
        "Lee and Skalnik show that WDR82 helps regulate nuclear genes through SETD1A and SETD1B protein complexes, but they provide no direct mitochondrial mechanism. Mercer and colleagues show that core MT genes are produced from long mitochondrial RNAs that are later processed, but they do not connect WDR82 with mitochondrial transcription. Zhu and colleagues report increased WDR82 expression and many network connections in mixed-cell hippocampal tissue, but that analysis does not identify the responsible cell type and lacks independent confirmation. The focused WDR82 network result therefore has high provisional novelty.",
      boundary:
        "The novelty assessment comes from a focused literature review and does not establish causal or replication strength.",
      transition: "Proceed to Finding 10 and the SELENOM result.",
      sources: FINDING9_SOURCES,
    }),
  ],
  [
    113,
    notes({
      goal:
        "Introduce the SELENOM finding and clarify its scope across sex and APOE groups.",
      walkthrough:
        "SELENOM connects oxidation control in the endoplasmic reticulum with genes used for protein production inside mitochondria. Most connected mitochondrial protein-production genes have lower expression in AD. KDA returned SELENOM across all six sex and APOE groups, so this is a broadly recurrent finding rather than a subgroup-specific finding.",
      boundary:
        "Recurrence across groups does not prove an identical biological effect in every group or establish that SELENOM controls mitochondrial protein production.",
      transition:
        "Define the endoplasmic-reticulum function of SELENOM and the connected mitochondrial process.",
      sources: FINDING10_SOURCES,
    }),
  ],
  [
    114,
    notes({
      goal:
        "Explain how SELENOM connects an endoplasmic-reticulum process with mitochondrial protein production.",
      walkthrough:
        "Twelve neuronal KDA calls across all six sex and APOE groups support this result. SELENOM helps control reversible oxidation reactions in the endoplasmic reticulum. The connected mitochondrial genes include mitochondrial ribosome genes and related factors that make proteins encoded by core MT genes. These connected genes mostly have lower expression in AD. SELENOM itself is not part of the mitochondrial ribosome. KDA links the two systems because their genes are close in the network.",
      boundary:
        "Network proximity does not show that SELENOM regulates mitochondrial protein production or identify the direction of an effect.",
      transition: "Show the ROSMAP counts supporting the SELENOM result.",
      sources: FINDING10_SOURCES,
    }),
  ],
  [
    120,
    notes({
      goal:
        "Explain the mitochondrial functions connected to SELENOW and distinguish SELENOW from SELENOM.",
      walkthrough:
        "Sixteen neuronal KDA calls across six categories support the result. NDUFB11, COA3, and CYC1 support mitochondrial respiration. MRPS34 and MRPL34 help mitochondria produce proteins encoded by core MT genes. CLPP removes damaged mitochondrial proteins, while other connected genes transport molecules across the inner mitochondrial membrane. The connections therefore span respiration, mitochondrial protein production, and removal of damaged proteins. SELENOW and SELENOM are different genes and should remain separate hypotheses.",
      boundary:
        "The network does not show that SELENOW controls every connected function or that all connected genes change through one mechanism.",
      transition: "Show the ROSMAP counts supporting the SELENOW result.",
      sources: FINDING11_SOURCES,
    }),
  ],
  [
    121,
    notes({
      goal: "Present the primary ROSMAP evidence supporting the SELENOW result.",
      walkthrough:
        "Sixteen neuronal KDA calls across six categories and four sex and APOE groups support the result. SELENOW has 123 connections to MitoCarta MT genes that represent several mitochondrial functions. Thirteen of the 16 input DEG sets show significant enrichment of nuclear-encoded OXPHOS genes. Frequently connected respiration genes include NDUFB11, COA3, and CYC1. MRPS34, MRPL34, and CLPP connect the result with mitochondrial protein production and removal of damaged proteins. SELENOW itself is a DEG in 10 of the 16 calls.",
      boundary:
        "Connections and DEG occurrences can repeat across KDA calls and do not represent independent donors.",
      transition: "Compare the SELENOW result with SEA-AD.",
      sources: FINDING11_SOURCES,
    }),
  ],
  [
    122,
    notes({
      goal:
        "Explain why SEA-AD provides little gene-level support for the SELENOW result.",
      walkthrough:
        "SELENOW was present in 10 matching SEA-AD excitatory networks and eight matching inhibitory networks, but no KDA call returned it. SEA-AD returned SECISBP2 from one KDA call. SECISBP2 is also related to selenium biology, but it is a different gene with a different function. A different related gene provides weaker evidence than recurrence of SELENOW itself.",
      boundary:
        "A gene that was testable but not returned provides limited counterevidence because ROSMAP and SEA-AD use different samples and cohort-specific networks. SECISBP2 does not validate the SELENOW mechanism.",
      transition: "Explain why the SELENOW result may still matter biologically.",
      sources: FINDING11_SOURCES,
    }),
  ],
  [
    123,
    notes({
      goal:
        "Explain the possible relationship among oxidative stress, damaged-protein removal, and mitochondrial function.",
      walkthrough:
        "Mitochondria depend on oxidation reactions and can also generate oxidative stress. Oxidative imbalance can damage proteins and respiratory machinery. CLPP removes damaged mitochondrial proteins, while prior mouse work links SELENOW with tau removal. The network therefore suggests a possible connection between removal of damaged mitochondrial proteins and broader removal of damaged proteins. Prior experiments used macrophages or mice rather than human neurons. SELENOW and SELENOM also connect to different genes and should remain separate hypotheses.",
      boundary:
        "Evidence from macrophages and mouse models cannot establish a human neuronal mechanism or causal direction.",
      transition: "Compare the current result with the supporting studies.",
      sources: FINDING11_SOURCES,
    }),
  ],
  [
    124,
    notes({
      goal:
        "Explain what prior research supports and where the SELENOW interpretation remains uncertain.",
      walkthrough:
        "Misra and colleagues show that loss of SELENOW changes oxidative stress and mitochondrial respiration, although their experiments used macrophages. Ren and colleagues report improved tau clearance and other outcomes after increasing SELENOW in a 3×Tg-AD mouse model. The current ROSMAP analysis adds connections in human neurons to respiration and removal of damaged mitochondrial proteins. The slide therefore assigns moderate novelty to the human neuronal network finding.",
      boundary:
        "The three sources support different parts of the interpretation. Together they do not prove a causal SELENOW mechanism in human neurons.",
      transition: "Proceed to Finding 12 and the PGK1-centered astrocyte result.",
      sources: FINDING11_SOURCES,
    }),
  ],
  [
    126,
    notes({
      goal:
        "Explain the proposed astrocyte connection between glycolysis and recycling of damaged mitochondria.",
      walkthrough:
        "Three astrocyte KDA calls support this result. PGK1 participates in glycolysis, which breaks down glucose outside mitochondria. FAM162A and BNIP3 respond to low oxygen or mitochondrial damage. BNIP3L can help mark damaged mitochondria for recycling. This small set of connected genes suggests a relationship between glucose breakdown and removal of damaged mitochondria.",
      boundary:
        "The result does not show that PGK1 broadly controls OXPHOS or directly regulates the three connected stress-response genes.",
      transition: "Show the ROSMAP counts and PGK1 expression changes.",
      sources: FINDING12_SOURCES,
    }),
  ],
  [
    127,
    notes({
      goal: "Present the primary ROSMAP evidence supporting the PGK1 result.",
      walkthrough:
        "Three astrocyte KDA calls in female epsilon-3 homozygous, female epsilon-4, and male epsilon-4 groups support the result. The calls contain eight direct connections involving FAM162A, BNIP3, or BNIP3L. PGK1 is upregulated in AD and meets the DEG threshold in female epsilon-3 homozygous and male epsilon-4 astrocytes, with log fold changes of plus 1.06 and plus 0.95. In female epsilon-4 astrocytes, its log fold change is plus 0.03 and it does not meet the DEG definition.",
      boundary:
        "The three groups do not establish a formal sex-by-APOE interaction. The directly connected genes recur across calls and are not independent observations.",
      transition: "Evaluate support outside the primary ROSMAP analysis.",
      sources: FINDING12_SOURCES,
    }),
  ],
  [
    128,
    notes({
      goal:
        "Explain why the PGK1 result is focused but has limited support outside ROSMAP.",
      walkthrough:
        "All eight direct connections involve only three genes. FAM162A appears in all three KDA calls, BNIP3 appears in all three, and BNIP3L appears in two. Each gene is related to low-oxygen responses or removal of damaged mitochondria. PGK1 was present but not returned in the only female epsilon-4 SEA-AD astrocyte network available for testing, whose KDA input contained only five DEGs. The supporting Mathys analysis also uses ROSMAP, so it may include some of the same donors and does not provide independent validation.",
      boundary:
        "The small number of connected genes makes the result sensitive to those genes. A single small SEA-AD input provides limited counterevidence.",
      transition: "Explain why the focused astrocyte hypothesis may still matter.",
      sources: FINDING12_SOURCES,
    }),
  ],
  [
    129,
    notes({
      goal:
        "Explain how astrocyte glucose use and removal of damaged mitochondria may be related.",
      walkthrough:
        "Astrocytes help regulate energy supply for neurons and respond strongly to Alzheimer’s pathology. Cells can shift ATP production toward glucose breakdown outside mitochondria, potentially reducing mitochondrial demand. BNIP3 and BNIP3L respond to low oxygen or damage and can help remove damaged mitochondria. These changes could protect cells or indicate severe stress. An experiment that changes PGK1 and then rescues the response can test whether PGK1 acts before BNIP3 and BNIP3L.",
      boundary:
        "The direction of the expression changes does not reveal whether the response is protective or harmful, and KDA does not establish causal order.",
      transition: "Compare the hypothesis with prior experimental research.",
      sources: FINDING12_SOURCES,
    }),
  ],
  [
    132,
    notes({
      goal:
        "Explain the proposed OPC connection among iron storage, protection from lipid damage, and removal of damaged cell components.",
      walkthrough:
        "OPCs are oligodendrocyte precursor cells that become myelin-producing cells. FTL and FTH1 form ferritin, which stores iron in a safer form and limits damaging free iron. GPX4 helps prevent oxidation of membrane fats. FIS1, PARK7, and PHB2 connect FTL and ANKRD11 with mitochondrial stress and recycling of damaged cell components. Together, the network suggests a relationship between iron handling and cellular cleanup.",
      boundary:
        "The result does not demonstrate ferroptosis. That conclusion would require direct measurement of iron-dependent lipid damage and rescue with a ferroptosis inhibitor.",
      transition: "Show the two supporting OPC KDA calls and their gene-expression directions.",
      sources: FINDING13_SOURCES,
    }),
  ],
  [
    133,
    notes({
      goal:
        "Present the two OPC KDA calls and distinguish an ANKRD11 KDA return from ANKRD11 differential expression.",
      walkthrough:
        "Female epsilon-3 homozygous and male epsilon-2 OPC KDA calls connect FTL and ANKRD11 to nearly the same genes. The calls share FTH1, GPX4, COX5B, and UQCR10, and both input DEG sets show significant enrichment of core MT and nuclear-encoded OXPHOS genes. FTL is a DEG in both calls but increases in the female epsilon-3 homozygous group and decreases in the male epsilon-2 group. KDA returned ANKRD11 in both groups because of its network connections. The DEG definition also requires FDR below 0.05 and an absolute log2 fold change above log2 of 1.3, or 0.379. ANKRD11 passes this expression threshold only in male epsilon-2 OPCs, where log2FC is plus 0.417. In female epsilon-3 homozygous OPCs, log2FC is minus 0.086, which is statistically significant but too small to qualify as a DEG.",
      boundary:
        "ROSMAP contains one OPC fine type, so the two group-specific calls do not provide broad subtype replication. KDA cannot determine whether ANKRD11, FTL, or another connected gene acts first.",
      transition:
        "Show the pathway results for genes returned from the OPC KDA calls.",
      sources: FINDING13_SOURCES,
    }),
  ],
]);

const TEXT_REPLACEMENTS = [
  {
    slide: 133,
    before: "Effect threshold only in M_e2",
    after: "Returned from both KDA calls",
  },
  {
    slide: 133,
    before: "The network cannot show whether ANKRD11 or FTL acts first",
    after: "DEG only in male ε2: +0.42 log2FC versus −0.09 in female ε3/ε3",
  },
];

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function parseNdjson(ndjson) {
  return ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
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

function relationships(xml) {
  return [...xml.matchAll(/<Relationship\b[^>]*\/?\s*>/g)].map((match) => ({
    attrs: relationshipAttributes(match[0]),
  }));
}

function normalizePart(basePart, target) {
  if (target.startsWith("/")) return target.slice(1);
  return path.posix.normalize(path.posix.join(path.posix.dirname(basePart), target));
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
  const relation = relationships(presentationRels).find(
    (item) => item.attrs.Id === relationshipId && item.attrs.Type?.endsWith("/slide"),
  );
  if (!relation?.attrs.Target) throw new Error(`Visible slide ${ordinal} was not found`);
  return normalizePart("ppt/presentation.xml", relation.attrs.Target);
}

async function notesPartForSlide(zip, slidePart) {
  const relsPath = path.posix.join(
    path.posix.dirname(slidePart),
    "_rels",
    `${path.posix.basename(slidePart)}.rels`,
  );
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing slide relationships: ${relsPath}`);
  const relation = relationships(relsXml).find((item) =>
    item.attrs.Type?.endsWith("/notesSlide"),
  );
  if (!relation?.attrs.Target) throw new Error(`No notes relationship for ${slidePart}`);
  return normalizePart(slidePart, relation.attrs.Target);
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
  if (slides.length !== SLIDE_COUNT) {
    throw new Error(`Expected ${SLIDE_COUNT} slides, found ${slides.length}`);
  }

  const snapshot = parseNdjson(
    (await presentation.inspect({ kind: "textbox,notes", maxChars: 8000000 })).ndjson,
  );
  for (const replacement of TEXT_REPLACEMENTS) {
    const matches = snapshot.filter(
      (record) =>
        record.kind === "textbox" &&
        record.slide === replacement.slide &&
        record.text === replacement.before,
    );
    if (matches.length !== 1) {
      throw new Error(
        `Expected one text match on slide ${replacement.slide}, found ${matches.length}: ${replacement.before}`,
      );
    }
    presentation.resolve(matches[0].id).text.replace(replacement.before, replacement.after);
  }

  for (const [slideNumber, noteText] of NOTES_BY_SLIDE) {
    slides[slideNumber - 1].speakerNotes.textFrame.setText(noteText);
    slides[slideNumber - 1].speakerNotes.setVisible(true);
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("Source changed while the updated deck was being authored");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));

  for (const slideNumber of CHANGED_SLIDES) {
    const sourcePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactPart = await visibleSlidePart(artifactZip, slideNumber);
    const updatedXml = await artifactZip.file(artifactPart)?.async("string");
    if (!updatedXml) throw new Error(`Updated slide XML is missing for slide ${slideNumber}`);
    sourceZip.file(sourcePart, updatedXml);
  }

  for (const slideNumber of NOTES_BY_SLIDE.keys()) {
    const sourceSlidePart = await visibleSlidePart(sourceZip, slideNumber);
    const artifactSlidePart = await visibleSlidePart(artifactZip, slideNumber);
    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const updatedNotesXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!updatedNotesXml) throw new Error(`Updated notes are missing for slide ${slideNumber}`);
    sourceZip.file(sourceNotesPart, updatedNotesXml);
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
  const finalSnapshot = parseNdjson(
    (await reopened.inspect({ kind: "textbox,notes", maxChars: 8000000 })).ndjson,
  );
  const slide133Text = finalSnapshot
    .filter((record) => record.kind === "textbox" && record.slide === 133)
    .map((record) => record.text)
    .join("\n");
  for (const phrase of [
    "Returned from both KDA calls",
    "DEG only in male ε2: +0.42 log2FC versus −0.09 in female ε3/ε3",
  ]) {
    if (!slide133Text.includes(phrase)) {
      throw new Error(`Required phrase missing from slide 133: ${phrase}`);
    }
  }
  const notes133 = finalSnapshot
    .filter((record) => record.kind === "notes" && record.slide === 133)
    .map((record) => record.text)
    .join("\n");
  if (!notes133.includes("absolute log2 fold change above log2 of 1.3")) {
    throw new Error("Slide 133 speaker notes do not explain the DEG effect threshold");
  }

  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const actualChanged = [];
  const actualDeleted = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) {
      actualDeleted.push(name);
      continue;
    }
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) actualChanged.push(name);
  }
  actualChanged.sort();
  actualDeleted.sort();
  const expectedChanged = [];
  for (const slideNumber of CHANGED_SLIDES) {
    expectedChanged.push(await visibleSlidePart(originalZip, slideNumber));
  }
  for (const slideNumber of NOTES_BY_SLIDE.keys()) {
    const slidePart = await visibleSlidePart(originalZip, slideNumber);
    expectedChanged.push(await notesPartForSlide(originalZip, slidePart));
  }
  expectedChanged.sort();
  if (
    actualChanged.length !== expectedChanged.length ||
    actualChanged.some((name, index) => name !== expectedChanged[index])
  ) {
    throw new Error(`Unexpected changed package parts: ${actualChanged.join(", ")}`);
  }
  if (actualDeleted.length) {
    throw new Error(`Unexpected deleted package parts: ${actualDeleted.join(", ")}`);
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
        slideCount: SLIDE_COUNT,
        updatedSlide: 133,
        updatedNotesSlides: [...NOTES_BY_SLIDE.keys()],
        changedParts: actualChanged,
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
