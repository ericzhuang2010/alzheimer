#!/usr/bin/env node

/** Replace unclear or jargon-heavy wording on slides 95–160 and synchronize notes. */

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
  "results/presentations/09162026_plain_language_slides95_160_20260922",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_plain_language_slides95_160.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "01d2d74e2ccdbb24ffaae57ad8c987a67ce2451565c8918a69fa02ab03f74420";
const SLIDE_COUNT = 160;

// [slide number, shape name, replacement text]
const EDITS = [
  [95, "TextBox 3", "Cytosolic ribosome genes repeatedly connect with nuclear-encoded OXPHOS genes"],
  [95, "TextBox 20", "RPL11, RPS15, and related cytosolic ribosome genes are repeatedly connected to nuclear-encoded OXPHOS genes in KDA calls."],

  [96, "TextBox 1", "Cytosolic ribosome genes repeatedly connect to nuclear-encoded OXPHOS genes"],
  [96, "TextBox 2", "The cytosolic ribosome builds most cellular proteins. The result is more credible as one recurring group of related genes than as 20 independent genes returned from KDA calls."],
  [96, "TextBox 10", "Group-level interpretation"],
  [96, "TextBox 16", "NETWORK CONNECTIONS"],
  [96, "TextBox 18", "Many ribosome genes returned from KDA calls are connected to nuclear genes that encode parts of the respiratory system."],
  [96, "TextBox 21", "One recurring gene group"],
  [96, "TextBox 22", "Because these genes perform related functions and share network connections, they should not be treated as independent findings."],
  [96, "TextBox 24", "The analysis points to a recurring connection between ribosome genes and OXPHOS genes, not 20 separately proven mitochondrial regulators."],

  [97, "TextBox 2", "The enrichment test compares 228 unique non-MitoCarta genes returned from KDA calls with all 11,478 genes available for selection in the same networks."],
  [97, "TextBox 9", "ribosome genes among available network genes"],
  [97, "TextBox 10", "0.62% of available genes"],
  [97, "TextBox 13", "multiple-testing-adjusted P value"],
  [97, "TextBox 14", "one-sided enrichment test"],
  [97, "TextBox 16", "Categories with ribosome genes"],
  [97, "TextBox 20", "Gene–category pairs"],
  [97, "TextBox 22", "Ribosome genes make up 18.4% of non-MitoCarta gene–category pairs"],
  [97, "TextBox 24", "Gene occurrences within KDA calls"],
  [97, "TextBox 26", "Ribosome genes make up 21.3% of non-MitoCarta returned-gene occurrences"],

  [98, "TextBox 1", "RPL11 and RPS15 are the most recurrent ribosome genes"],
  [98, "TextBox 2", "RPL11 is connected to many nuclear-encoded OXPHOS genes, while RPS15 appears in the largest number of categories."],
  [98, "TextBox 4", "RPL11 ACROSS KDA CALLS"],
  [98, "TextBox 6", "The KDA calls span all six sex/APOE groups and four broad networks."],
  [98, "TextBox 8", "GENES CONNECTED TO RPL11"],
  [98, "TextBox 9", "253 gene connections across 37 genes"],
  [98, "TextBox 10", "Nuclear-encoded OXPHOS genes account for 151 connections; 100 involve lower expression in AD."],
  [98, "TextBox 12", "RPS15 ACROSS KDA CALLS"],
  [98, "TextBox 14", "RPS15 appears across the largest number of categories."],
  [98, "TextBox 16", "Frequently connected RPL11 genes include COX7C, UQCRQ, NDUFS5, NDUFA1, ATP5PF, NDUFB9, and NDUFB3."],

  [99, "TextBox 2", "Ribosome stress and OXPHOS changes may be biologically linked, but the network’s connection pattern could also explain the result."],
  [99, "TextBox 5", "Protein production and respiration are connected"],
  [99, "TextBox 13", "Genes with many connections may rank highly"],
  [99, "TextBox 14", "Highly expressed ribosome genes may be selected more often by network-based methods."],
  [99, "TextBox 17", "Tests that compare genes with similar numbers of network connections are needed before treating recurring ribosome genes as regulators."],

  [100, "TextBox 19", "Recurring ribosome genes"],
  [100, "TextBox 21", "Several ribosome genes appear across categories and connect repeatedly to OXPHOS genes."],
  [100, "TextBox 23", "Some comparisons share donors, and highly connected genes can be selected more often; the observations are therefore not independent."],

  [102, "TextBox 2", "Lysosomes recycle cell material and sense nutrients. LAMTOR5 relays this information to mTORC1, a pathway that regulates cell growth and protein production."],
  [102, "TextBox 13", "Recycling material and sensing nutrients"],
  [102, "TextBox 17", "Part of the lysosomal nutrient-sensing complex"],
  [102, "TextBox 18", "LAMTOR5 helps the cell use amino-acid availability at lysosomes to regulate mTORC1."],
  [102, "TextBox 22", "Genes connected to LAMTOR5 suggest a relationship with how much the cell invests in mitochondrial respiration."],
  [102, "TextBox 24", "The result suggests a possible connection between lysosomal nutrient sensing and mitochondrial respiration, but KDA cannot show which process controls the other."],

  [103, "TextBox 1", "ROSMAP: LAMTOR5 recurs in neuronal KDA calls and connects repeatedly to OXPHOS genes"],
  [103, "TextBox 2", "The largest scores occur in male ε2 neurons, where the DEG input to KDA contained unusually many genes."],
  [103, "TextBox 6", "six categories, four sex/APOE groups"],
  [103, "TextBox 9", "connections to MitoCarta MT genes"],
  [103, "TextBox 13", "input DEG sets with significant OXPHOS enrichment"],
  [103, "TextBox 18", "Most connected nuclear-encoded OXPHOS genes show lower expression in AD"],
  [103, "TextBox 20", "Frequently connected genes"],

  [104, "TextBox 1", "Other genes returned from KDA calls also connect lysosomal recycling with mitochondrial genes"],
  [104, "TextBox 2", "Several related genes support the same biological connection, reducing reliance on LAMTOR5 alone."],
  [104, "TextBox 6", "Genes connected to GABARAPL2 include CHCHD2, ATP5MC3, PARK7, and mitochondrial-ribosome genes."],
  [104, "TextBox 10", "Genes connected to ATG101 include MRPS34, UQCRFS1, CLPP, and PINK1."],
  [104, "TextBox 14", "ATP6AP2 connects lysosomal acidification through the V-ATPase with OXPHOS and mitochondrial protein import."],
  [104, "TextBox 16", "SEA-AD had no KDA call for the same sex/APOE and cell categories, so it could not test this result directly."],

  [105, "TextBox 1", "Why this matters: nutrient sensing can coordinate protein production and mitochondrial respiration"],
  [105, "TextBox 2", "LAMTOR5 is positioned between lysosomes, mTORC1, and mitochondria, making this connection biologically plausible."],
  [105, "TextBox 6", "The Ragulator protein complex helps position nutrient signals at the lysosome."],
  [105, "TextBox 10", "mTORC1 can change the production of nuclear-encoded mitochondrial proteins and the cell’s capacity for respiration."],
  [105, "TextBox 13", "Amyloid-β can disrupt this communication"],
  [105, "TextBox 14", "Experimental work links disrupted communication between lysosomes and mitochondria in neurons with tau-related stress."],
  [105, "TextBox 17", "The known biology supports experiments that alter LAMTOR5, but it does not confirm the network connections found here."],

  [106, "TextBox 5", "LAMTOR5 and mTORC1 nutrient signaling"],
  [106, "TextBox 7", "Shows that LAMTOR5 helps sense amino acids at lysosomes."],
  [106, "TextBox 16", "Does not show that LAMTOR5 causes the relationship observed here."],
  [106, "TextBox 21", "Shows that amyloid-β disrupts communication between lysosomes and mitochondria in neurons."],

  [107, "TextBox 3", "WDR82 is linked to a small group of upregulated core MT genes in excitatory neurons"],
  [107, "TextBox 20", "WDR82 appears only in excitatory neurons and is connected to four upregulated core MT genes."],

  [108, "TextBox 2", "WDR82 is directly connected to only four recurring core MT genes, all produced from one long mitochondrial RNA."],
  [108, "TextBox 13", "Gene involved in nuclear gene regulation"],
  [108, "TextBox 14", "WDR82 helps regulate which nuclear genes are active; it is not part of the mitochondrial ribosome."],
  [108, "TextBox 16", "GENES DIRECTLY CONNECTED TO WDR82"],
  [108, "TextBox 18", "These four core MT genes account for nearly every direct mitochondrial connection to WDR82."],
  [108, "TextBox 20", "WHY THESE ARE NOT FOUR INDEPENDENT SIGNALS"],

  [109, "TextBox 1", "ROSMAP: every WDR82 KDA input shows significant enrichment of upregulated core MT genes"],
  [109, "TextBox 2", "KDA can return a gene because of its network connections even when that gene does not meet the DEG threshold."],
  [109, "TextBox 13", "input DEG sets with significant core MT enrichment"],
  [109, "TextBox 16", "Core MT genes directly connected to WDR82"],
  [109, "TextBox 20", "Other directly connected gene"],
  [109, "TextBox 22", "PIM1 is the only other directly connected gene"],
  [109, "TextBox 26", "Thirteen KDA calls had FDR below 0.05, but WDR82 expression changes were too small to meet the DEG effect-size cutoff"],

  [110, "TextBox 1", "Most WDR82 KDA calls come from female ε3/ε3 excitatory neurons"],
  [110, "TextBox 2", "WDR82 was returned in four sex/APOE groups, but most KDA calls come from female ε3/ε3."],
  [110, "TextBox 10", "This group provides most WDR82 KDA calls and the strongest core MT gene-set support."],
  [110, "TextBox 14", "WDR82 was also returned from two male ε3/ε3 and three male ε4 excitatory KDA calls."],
  [110, "TextBox 16", "SEA-AD had 11 matching excitatory-neuron networks in which WDR82 could have been returned, but it was not. SEA-AD still supports the female ε3/ε3 core MT gene pattern."],

  [111, "TextBox 1", "Why this matters: a nuclear gene regulator may track mitochondrial RNA abundance"],
  [111, "TextBox 2", "The pattern could reflect coordinated RNA production, overall mitochondrial RNA abundance, or how the network was constructed."],
  [111, "TextBox 4", "POSSIBLE BIOLOGICAL EXPLANATION"],
  [111, "TextBox 5", "Nuclear gene regulation may influence mitochondrial RNA"],
  [111, "TextBox 9", "Overall mitochondrial RNA abundance"],
  [111, "TextBox 10", "Repeated core MT genes may reflect the overall amount of mitochondrial RNA or sample quality."],
  [111, "TextBox 12", "NETWORK-BASED EXPLANATION"],
  [111, "TextBox 13", "Four connected genes dominate"],
  [111, "TextBox 14", "The small set of connections may reflect one shared long mitochondrial RNA rather than four separate mechanisms."],
  [111, "TextBox 17", "Repeating KDA after removing core MT genes from the input DEG sets can test whether the result depends on those genes."],

  [112, "TextBox 5", "WDR82 and nuclear gene regulation"],
  [112, "TextBox 7", "Shows that WDR82 helps regulate which nuclear genes are active through SETD1A/B protein complexes."],
  [112, "TextBox 14", "Shows that core MT genes are produced from long mitochondrial RNAs that are later cut into individual gene products."],
  [112, "TextBox 19", "WDR82 in AD gene expression"],
  [112, "TextBox 21", "Reports increased WDR82 expression and many network connections in a reanalysis of mixed-cell hippocampal tissue."],
  [112, "TextBox 23", "The mixed-cell analysis does not show which cell types drive the result and has not been confirmed in another cohort."],

  [113, "TextBox 3", "SELENOM connects oxidation control in the ER with mitochondrial protein production"],
  [113, "TextBox 20", "SELENOM repeatedly connects to genes used for protein production inside mitochondria, and most have lower expression in AD."],

  [114, "TextBox 1", "SELENOM connects oxidation control in the ER with mitochondrial protein production"],
  [114, "TextBox 6", "All six sex/APOE groups"],
  [114, "TextBox 8", "Oxidation and calcium control in the ER"],
  [114, "TextBox 10", "Protein production inside mitochondria"],
  [114, "TextBox 13", "Protein that controls oxidation in the ER"],
  [114, "TextBox 14", "This selenium-containing protein helps control reversible oxidation reactions inside the ER."],
  [114, "TextBox 16", "PROTEIN PRODUCTION INSIDE MITOCHONDRIA"],
  [114, "TextBox 21", "Protein-production genes mostly down"],
  [114, "TextBox 22", "Genes directly connected to SELENOM are mostly mitochondrial protein-production genes with lower expression in AD."],
  [114, "TextBox 24", "SELENOM is not part of the mitochondrial ribosome. KDA links the two systems because their genes are close in the network."],

  [115, "TextBox 1", "ROSMAP: genes for mitochondrial protein production dominate SELENOM’s connections"],
  [115, "TextBox 9", "connections to MitoCarta MT genes"],
  [115, "TextBox 10", "27 genes for protein production"],
  [115, "TextBox 13", "input DEG sets with significant OXPHOS enrichment"],
  [115, "TextBox 16", "Direction of expression change"],
  [115, "TextBox 18", "Most connected mitochondrial protein-production genes have lower expression in AD"],
  [115, "TextBox 20", "Frequently connected genes"],
  [115, "TextBox 22", "CLPP and MRPS26 are also repeatedly connected to SELENOM"],
  [115, "TextBox 26", "SELENOM itself also changes expression in most supporting KDA calls"],

  [116, "TextBox 2", "Repeated ROSMAP KDA calls and repeated connections to mitochondrial protein-production genes are still the main evidence."],
  [116, "TextBox 4", "SEA-AD OPPORTUNITY TO TEST"],
  [116, "TextBox 5", "10 matching networks"],
  [116, "TextBox 8", "RETURNED FROM SEA-AD KDA CALLS"],
  [116, "TextBox 13", "No qualifying gene-level evidence"],
  [116, "TextBox 14", "The local genetic screen did not find qualifying genetic evidence for SELENOM."],
  [116, "TextBox 16", "The lack of support in SEA-AD or human genetics lowers confidence outside ROSMAP, but the repeated ROSMAP result remains."],

  [117, "TextBox 9", "Protein production supplies core MT proteins"],
  [117, "TextBox 10", "Lower expression of this machinery could reduce assembly of mitochondrial respiratory complexes."],
  [117, "TextBox 12", "POSSIBLE BIOLOGICAL EXPLANATION"],
  [117, "TextBox 13", "Stress shared between the ER and mitochondria"],
  [117, "TextBox 14", "SELENOM could affect mitochondria indirectly by changing oxidation or calcium control in the ER."],
  [117, "TextBox 17", "An experiment that changes SELENOM and measures both ER and mitochondrial responses can distinguish a specific connection from general cell stress."],

  [118, "TextBox 5", "What SELENOM does"],
  [118, "TextBox 7", "Shows that SELENOM is a protein inside the ER that helps control reversible oxidation reactions."],
  [118, "TextBox 12", "Oxidation and calcium in neurons"],
  [118, "TextBox 14", "Shows that SELENOM helps regulate oxidation and calcium in neurons."],
  [118, "TextBox 19", "SELENOM and AD-related outcomes"],
  [118, "TextBox 21", "Reports effects on amyloid-β-related and mitochondrial outcomes in cells or animals."],
  [118, "TextBox 23", "Results from cells or animals do not prove the network connections observed in ROSMAP."],

  [119, "TextBox 3", "SELENOW connects oxidative-stress control, mitochondrial respiration, and removal of damaged proteins"],
  [119, "TextBox 20", "SELENOW is connected to genes involved in mitochondrial respiration, protein production, and removal of damaged mitochondrial proteins."],

  [120, "TextBox 1", "SELENOW connects oxidative-stress control with mitochondrial respiration and damaged-protein removal"],
  [120, "TextBox 2", "Cells must control oxidation to prevent damaging oxidative stress. SELENOW should not be treated as the same mechanism as SELENOM."],
  [120, "TextBox 8", "Control of oxidative stress"],
  [120, "TextBox 10", "Genes from several mitochondrial functions"],
  [120, "TextBox 20", "REMOVAL OF DAMAGED PROTEINS"],
  [120, "TextBox 21", "CLPP and inner-membrane genes"],
  [120, "TextBox 22", "Connected genes include CLPP, which removes damaged mitochondrial proteins, and genes that transport molecules across the inner membrane."],
  [120, "TextBox 24", "The connected genes span oxidative-stress control, respiration, protein production, and removal of damaged proteins rather than one narrow OXPHOS connection."],

  [121, "TextBox 1", "ROSMAP: SELENOW recurs in neurons and has 123 connections to MitoCarta MT genes"],
  [121, "TextBox 2", "The supporting KDA calls cover excitatory and inhibitory neurons in four sex/APOE groups."],
  [121, "TextBox 6", "six categories, four sex/APOE groups"],
  [121, "TextBox 9", "connections to MitoCarta MT genes"],
  [121, "TextBox 10", "genes from several mitochondrial functions"],
  [121, "TextBox 13", "input DEG sets with significant OXPHOS enrichment"],
  [121, "TextBox 18", "Frequently connected genes support mitochondrial respiration"],
  [121, "TextBox 20", "Protein production and damaged-protein removal"],
  [121, "TextBox 22", "Connected genes include mitochondrial ribosome genes and CLPP, which removes damaged proteins"],
  [121, "TextBox 26", "SELENOW itself also changes expression in most supporting KDA calls"],

  [122, "TextBox 1", "SEA-AD returns a different selenium-related gene, not SELENOW"],
  [122, "TextBox 2", "Returning the same gene would be stronger evidence than returning a different gene with a related function."],
  [122, "TextBox 6", "SELENOW was present in matching male ε3/ε3 excitatory networks but was not returned from KDA calls."],
  [122, "TextBox 10", "SELENOW was present in matching inhibitory networks but was not returned from KDA calls."],
  [122, "TextBox 13", "SECISBP2 returned from one KDA call"],
  [122, "TextBox 14", "A different selenium-related gene gives only weak support for related biology."],
  [122, "TextBox 16", "The local genetic screen adds weak evidence from a study that links genetically predicted gene expression with disease, but this does not establish causality."],

  [123, "TextBox 1", "Why this matters: oxidative stress, removal of tau, and mitochondrial function may be connected"],
  [123, "TextBox 4", "CONTROL OF OXIDATIVE STRESS"],
  [123, "TextBox 5", "Mitochondria depend on oxidation reactions and can generate oxidative stress"],
  [123, "TextBox 8", "REMOVAL OF DAMAGED PROTEINS"],
  [123, "TextBox 9", "CLPP removes damaged mitochondrial proteins; prior mouse work links SELENOW to tau removal"],
  [123, "TextBox 10", "SELENOW may connect removal of damaged mitochondrial proteins with broader removal of damaged proteins in the cell."],
  [123, "TextBox 12", "LIMIT OF PRIOR EXPERIMENTS"],
  [123, "TextBox 17", "SELENOW and SELENOM are both selenium-related, but they connect to different genes and should remain separate hypotheses."],

  [124, "TextBox 7", "Shows that loss of SELENOW changes oxidative stress and mitochondrial respiration."],
  [124, "TextBox 19", "Connections observed in human neurons"],
  [124, "TextBox 21", "Adds cell-type-specific connections to respiration and removal of damaged mitochondrial proteins."],

  [125, "TextBox 3", "PGK1 connects astrocyte glucose breakdown and low-oxygen signaling with removal of damaged mitochondria"],
  [125, "TextBox 20", "PGK1 connects astrocyte glucose breakdown with BNIP3, BNIP3L, and FAM162A, three genes that respond to low oxygen or mitochondrial damage."],

  [126, "TextBox 10", "Low oxygen and removal of damaged mitochondria"],
  [126, "TextBox 16", "GENES RESPONDING TO LOW OXYGEN OR DAMAGE"],
  [126, "TextBox 24", "This small set of connected genes suggests a link between glucose breakdown and recycling of damaged mitochondria, not broad control of all OXPHOS genes."],

  [127, "TextBox 1", "ROSMAP: PGK1 appears in three astrocyte groups and connects to three stress-response genes"],
  [127, "TextBox 2", "The summary scores rank candidates for follow-up but are exploratory and are not multiple-testing-adjusted q values."],
  [127, "TextBox 9", "directly connected gene occurrences"],
  [127, "TextBox 13", "directly connected genes"],

  [128, "TextBox 1", "The same three genes recur, but support outside ROSMAP remains limited"],
  [128, "TextBox 2", "A result based on only three connected genes gives a focused hypothesis but depends heavily on those genes."],
  [128, "TextBox 4", "DIRECTLY CONNECTED GENES"],
  [128, "TextBox 5", "FAM162A in 3 KDA calls, BNIP3 in 3, BNIP3L in 2"],
  [128, "TextBox 6", "All eight gene connections involve response to low oxygen or removal of damaged mitochondria."],
  [128, "TextBox 8", "SEA-AD TEST"],
  [128, "TextBox 9", "PGK1 present but not returned"],
  [128, "TextBox 10", "PGK1 was present in the only female ε4 astrocyte network available for testing, but the KDA input contained only five DEGs."],
  [128, "TextBox 12", "INDEPENDENCE OF PRIOR STUDY"],
  [128, "TextBox 13", "Mathys et al. also uses ROSMAP"],
  [128, "TextBox 14", "Related evidence about glucose breakdown in glial cells may include some of the same donors, so it is not independent validation."],

  [129, "TextBox 1", "Why this matters: astrocytes can shift glucose use and remove damaged mitochondria"],
  [129, "TextBox 5", "More glucose breakdown outside mitochondria may reduce mitochondrial demand"],
  [129, "TextBox 8", "RESPONSE TO MITOCHONDRIAL DAMAGE"],
  [129, "TextBox 9", "BNIP3 and BNIP3L respond to low oxygen and damage"],
  [129, "TextBox 10", "These genes can help remove damaged mitochondria."],
  [129, "TextBox 13", "Could be protective or harmful"],
  [129, "TextBox 14", "Increased glucose breakdown and removal of damaged mitochondria can protect cells or indicate severe stress."],
  [129, "TextBox 17", "An experiment that changes PGK1 and then rescues the response can test whether PGK1 acts before BNIP3 and BNIP3L."],

  [130, "TextBox 5", "Changes in glucose breakdown in glial cells"],
  [130, "TextBox 7", "Reports groups of glial genes that include PGK1 and BNIP3L and change together in human AD."],
  [130, "TextBox 12", "APOE4 astrocytes and removal of damaged mitochondria"],
  [130, "TextBox 14", "Connects APOE4 astrocytes with changes in mitochondrial shape and removal of damaged mitochondria."],
  [130, "TextBox 19", "Removal of damaged mitochondria by astrocytes"],
  [130, "TextBox 21", "Connects lysosomal cholesterol with reduced removal of damaged mitochondria and impaired respiration."],

  [131, "TextBox 3", "FTL and ANKRD11 connect iron storage, protection from lipid damage, and cellular recycling in OPCs"],
  [131, "TextBox 20", "FTL and ANKRD11 connect iron storage in OPCs with GPX4 protection from lipid damage and genes that recycle damaged cell components."],

  [132, "TextBox 1", "FTL and ANKRD11 connect iron storage with protection from lipid damage and mitochondrial cleanup in OPCs"],
  [132, "TextBox 8", "Protection from iron-related lipid damage"],
  [132, "TextBox 10", "Ferroptosis requires direct testing"],
  [132, "TextBox 20", "REMOVAL OF DAMAGED CELL COMPONENTS"],
  [132, "TextBox 21", "Genes that recycle damaged cell components"],
  [132, "TextBox 22", "FIS1, PARK7, and PHB2 connect FTL and ANKRD11 with genes involved in mitochondrial stress and recycling damaged cell components."],
  [132, "TextBox 24", "The data suggest a link between iron storage and recycling of damaged cell components. Ferroptosis would require direct measurement of lipid damage and rescue by a ferroptosis inhibitor."],

  [133, "TextBox 1", "ROSMAP: FTL and ANKRD11 connect to almost the same genes in OPCs"],
  [133, "TextBox 9", "shared directly connected genes"],
  [133, "TextBox 13", "input DEG sets with significant enrichment"],
  [133, "TextBox 26", "The network cannot show whether ANKRD11 or FTL acts first"],

  [134, "TextBox 1", "Genes returned from OPC KDA calls emphasize recycling of damaged cell components and iron handling"],
  [134, "TextBox 2", "Several pathway terms contain many of the same genes, including widely used ubiquitin and tubulin genes."],
  [134, "TextBox 4", "RECYCLING SPECIFIC CELL COMPONENTS"],
  [134, "TextBox 6", "This is the strongest exploratory pathway result among genes returned from OPC KDA calls."],
  [134, "TextBox 8", "REMOVAL OF DAMAGED MITOCHONDRIA"],
  [134, "TextBox 10", "Genes returned from OPC KDA calls include genes associated with removing damaged mitochondria."],
  [134, "TextBox 14", "FTL, UBB, and UBC are the genes behind this pathway result."],
  [134, "TextBox 16", "SEA-AD had no OPC category for KDA, so this result could not be tested in that cohort."],

  [135, "TextBox 2", "Iron storage, GPX4 protection from lipid damage, and removal of damaged mitochondria combine into a testable model."],
  [135, "TextBox 12", "WHAT WOULD PROVE FERROPTOSIS"],
  [135, "TextBox 13", "Rescue by a ferroptosis inhibitor"],

  [136, "TextBox 19", "Connections in human OPCs"],
  [136, "TextBox 21", "Adds focused connections among FTL, ANKRD11, GPX4, and genes that recycle damaged cell components."],

  [137, "TextBox 3", "PLCG2 has strong genetic evidence, but its mitochondrial KDA result depends on one gene"],
  [137, "TextBox 20", "PLCG2 has strong Alzheimer’s genetic evidence, but MT-CO1 is the only MitoCarta MT gene directly connected to it in these KDA calls."],

  [138, "TextBox 1", "PLCG2 has strong genetic support, but only one connected mitochondrial gene"],
  [138, "TextBox 2", "PLCG2 encodes a signaling enzyme. KDA can return a gene because of its network connections even when it is not a DEG."],
  [138, "TextBox 20", "WHY THE NETWORK RESULT IS UNCERTAIN"],
  [138, "TextBox 21", "One repeatedly connected gene"],
  [138, "TextBox 22", "MT-CO1 is the only MitoCarta MT gene directly connected to PLCG2 across these KDA calls."],
  [138, "TextBox 24", "Strong genetics supports PLCG2 as an AD gene, but does not confirm this PLCG2–MT-CO1 connection in inhibitory neurons."],

  [139, "TextBox 1", "ROSMAP: PLCG2 recurs across six KDA calls, but only MT-CO1 is directly connected"],
  [139, "TextBox 9", "unique directly connected MitoCarta MT gene"],
  [139, "TextBox 14", "PLCG2 returned by KDA only; not a DEG"],
  [139, "TextBox 18", "MT-CO1 is the directly connected mitochondrial gene"],
  [139, "TextBox 22", "All four KDA calls directly connect PLCG2 with MT-CO1"],
  [139, "TextBox 26", "Five PLCG2–MT-CO1 connections involve MT-CO1 upregulation in AD and one involves downregulation"],

  [140, "TextBox 1", "The KDA input DEG sets contain many core MT genes, but this does not explain the PLCG2–MT-CO1 connection"],
  [140, "TextBox 2", "Enrichment in the full DEG input and direct connections to PLCG2 answer different questions."],
  [140, "TextBox 4", "FULL KDA INPUT DEG SETS"],
  [140, "TextBox 5", "41 core MT DEG occurrences"],
  [140, "TextBox 6", "Across the six KDA input DEG sets, core MT genes are upregulated in 36 occurrences and downregulated in five."],
  [140, "TextBox 8", "SIGNIFICANT CORE MT ENRICHMENT"],
  [140, "TextBox 10", "All six KDA input DEG sets contain more core MT genes than expected by chance."],
  [140, "TextBox 13", "SEA-AD could not test this result"],
  [140, "TextBox 14", "SEA-AD had no female inhibitory KDA category, so it could not test the same sex/APOE and cell context."],
  [140, "TextBox 16", "Phase 19b provides gene-level genetic support for PLCG2, but the network result still depends on the single PLCG2–MT-CO1 connection."],

  [141, "TextBox 1", "Genetic evidence for a gene and evidence for a specific network connection must be considered separately"],
  [141, "TextBox 2", "A well-established AD gene can still have uncertain activity in a particular cell type or uncertain network connections."],
  [141, "TextBox 5", "PLCG2 variants affect AD risk"],
  [141, "TextBox 6", "The protective P522R variant produces a small increase in PLCG2 activity."],
  [141, "TextBox 8", "CELL-TYPE QUESTION"],
  [141, "TextBox 9", "Unexpected result in inhibitory neurons"],
  [141, "TextBox 12", "NETWORK CONNECTION QUESTION"],
  [141, "TextBox 13", "The PLCG2–MT-CO1 connection may be unstable"],
  [141, "TextBox 14", "RNA from nearby cells, droplets containing more than one cell, cell-label errors, or network structure could create the repeated connection."],
  [141, "TextBox 17", "PLCG2 remains worth testing, but first we should verify that inhibitory neurons express PLCG2 and that the PLCG2–MT-CO1 connection is reproducible."],

  [142, "TextBox 12", "Protective variant with a small activity increase"],
  [142, "TextBox 23", "Does not confirm that PLCG2 regulates MT-CO1."],

  [143, "TextBox 3", "Astrocyte APOE results differ by sex/APOE group and are not specific to ε4"],

  [145, "TextBox 2", "Each sex/APOE group contributes only one KDA call, so there is not enough evidence for one shared biological pattern."],
  [145, "TextBox 13", "named directly connected mitochondrial genes"],
  [145, "TextBox 16", "Mitochondrial protein production"],
  [145, "TextBox 18", "TUFM, a gene needed for mitochondrial protein production, is connected to APOE"],
  [145, "TextBox 20", "Energy production and mitochondrial structure"],
  [145, "TextBox 22", "LDHB and CHCHD10 are involved in metabolism, mitochondrial structure, or stress responses"],

  [146, "TextBox 1", "The genes connected to APOE differ across groups rather than forming one repeated pathway"],
  [146, "TextBox 2", "Opposite expression directions and different connected genes could reflect real group differences, different astrocyte states, or sampling."],
  [146, "TextBox 13", "SEA-AD could not test these results"],
  [146, "TextBox 14", "SEA-AD had no KDA calls for the same sex/APOE and cell categories."],
  [146, "TextBox 16", "APOE is a well-established AD risk gene, but that does not confirm these expression directions or specific mitochondrial connections."],

  [147, "TextBox 13", "Separate group analyses do not prove that the groups differ"],
  [147, "TextBox 14", "A formal interaction model must directly compare disease effects across sex and APOE groups."],
  [147, "TextBox 17", "The result supports testing separate APOE models by sex and genotype rather than assuming an ε4-only effect."],

  [148, "TextBox 14", "Shows that APOE-related changes in astrocytes can alter normal mitochondrial function."],
  [148, "TextBox 19", "APOE4 and removal of damaged mitochondria"],
  [148, "TextBox 21", "Connects APOE4 astrocytes with changes in mitochondrial shape and removal of damaged mitochondria."],

  [149, "TextBox 3", "Female APOE ε4 vascular cells show a small group of stress-response genes"],
  [149, "TextBox 20", "HSPH1, HSPA1A, and PTGES3 are returned from KDA calls in female ε4 vascular cells, but only two KDA calls contribute."],

  [150, "TextBox 1", "Female ε4 vascular KDA calls return a small group of protein-stress genes"],
  [150, "TextBox 13", "Protein-folding helper during stress"],
  [150, "TextBox 17", "Helps damaged proteins refold"],
  [150, "TextBox 21", "Protein-folding protein"],
  [150, "TextBox 24", "These three related genes give a focused clue, not evidence of a broad stress response in vascular cells."],

  [151, "TextBox 2", "The pathway test compares the five returned genes with all genes available in the vascular network; the result is exploratory."],
  [151, "TextBox 5", "unique non-MitoCarta genes returned from vascular KDA calls"],
  [151, "TextBox 9", "stress-response genes returned from KDA calls"],
  [151, "TextBox 14", "only two KDA calls contribute"],
  [151, "TextBox 16", "Genes controlled by HSF1"],
  [151, "TextBox 18", "HSF1 controls many genes that protect proteins during cell stress"],
  [151, "TextBox 20", "Cellular response to protein stress"],
  [151, "TextBox 22", "This pathway name reflects shared stress-response genes; it does not mean the cells were exposed to high temperature"],
  [151, "TextBox 24", "WHY THE PATHWAY RESULTS ARE NOT INDEPENDENT"],
  [151, "TextBox 25", "The same three genes contribute"],
  [151, "TextBox 26", "The same three genes contribute to several related pathway results"],

  [152, "TextBox 1", "Only two KDA calls and no SEA-AD vascular analysis make this result preliminary"],
  [152, "TextBox 2", "The low confidence comes from very limited ROSMAP evidence, not from a failed comparison with SEA-AD."],
  [152, "TextBox 4", "ROSMAP EVIDENCE"],
  [152, "TextBox 8", "OVERLAPPING PATHWAY RESULTS"],
  [152, "TextBox 10", "The HSF1 and protein-stress pathway results share genes and should not be counted as independent findings."],
  [152, "TextBox 13", "No SEA-AD vascular KDA analysis"],
  [152, "TextBox 14", "SEA-AD cannot test this result because no vascular category was available for KDA."],
  [152, "TextBox 16", "This remains a low-confidence ROSMAP clue because only two KDA calls support it."],

  [153, "TextBox 10", "These genes may indicate protein damage or a general protective response."],

  [154, "TextBox 4", "Current pathway test"],
  [154, "TextBox 5", "Genes controlled by HSF1"],
  [154, "TextBox 7", "Shows that female ε4 vascular KDA calls return several genes controlled by HSF1."],
  [154, "TextBox 9", "Only three related genes from two KDA calls produce this result."],
  [154, "TextBox 12", "Cell- and sex-specific AD networks"],
  [154, "TextBox 16", "Does not report this group of stress-response genes in vascular cells."],
  [154, "TextBox 19", "AD differences among cell populations"],
  [154, "TextBox 21", "Shows that AD-related gene expression differs among brain cell populations."],
  [154, "TextBox 23", "Uses ROSMAP and does not independently confirm this group of genes."],

  [155, "TextBox 3", "SEA-AD supports similar mitochondrial gene sets, but not the same genes returned from KDA calls"],
  [155, "TextBox 20", "Mitochondrial gene-set patterns agree more strongly than the exact genes returned from KDA calls across the two cohort-specific network analyses."],

  [156, "TextBox 1", "ROSMAP and SEA-AD agree more on mitochondrial gene sets than on the exact genes returned from KDA calls"],
  [156, "TextBox 8", "No exact non-MitoCarta gene matches"],
  [156, "TextBox 13", "Same gene, sex/APOE group, and cell class"],
  [156, "TextBox 14", "No testable non-MitoCarta gene returned from a ROSMAP KDA call was also returned in the same SEA-AD context."],
  [156, "TextBox 16", "BROADER COMPARISON"],
  [156, "TextBox 17", "Same gene in a different context"],
  [156, "TextBox 18", "LAGE3, MIPOL1, and PAPOLA are returned in both cohorts, but in different sex/APOE or cell settings."],
  [156, "TextBox 21", "Similar mitochondrial gene sets"],
  [156, "TextBox 24", "The cohort-specific networks can return different genes even when they point to similar mitochondrial biology."],

  [157, "TextBox 1", "Few exact comparisons were possible, and none returned the same non-MitoCarta gene"],
  [157, "TextBox 2", "A ROSMAP gene could be compared only if it was also present in the matching SEA-AD network."],
  [157, "TextBox 5", "ROSMAP gene–category pairs in categories SEA-AD could test"],
  [157, "TextBox 6", "categories available in both cohorts"],
  [157, "TextBox 9", "pairs with the gene present in SEA-AD"],
  [157, "TextBox 10", "gene could have been returned"],
  [157, "TextBox 13", "same gene returned in the same context"],
  [157, "TextBox 14", "non-MitoCarta genes"],
  [157, "TextBox 16", "Matched gene–category opportunities"],
  [157, "TextBox 18", "Non-MitoCarta gene–category pairs present in both matching networks"],
  [157, "TextBox 20", "Expected same-gene matches by chance"],
  [157, "TextBox 22", "Even by chance, far fewer than one exact match was expected"],
  [157, "TextBox 24", "Test for more matches than expected"],
  [157, "TextBox 26", "Zero same-context matches does not show that the cohorts disagree"],

  [158, "TextBox 1", "Three genes were returned in both cohorts, but in different sex/APOE or cell settings"],
  [158, "TextBox 2", "These genes may be relevant across cohorts, but they do not confirm the original sex/APOE and cell setting."],
  [158, "TextBox 6", "LAGE3 recurs in ROSMAP excitatory neurons and SEA-AD male ε3/ε3 inhibitory neurons. In SEA-AD, it is connected to mitochondrial genes."],
  [158, "TextBox 9", "Same male ε3/ε3 group"],
  [158, "TextBox 10", "MIPOL1 appears in the same sex/APOE group but in a different neuronal class, making it the closest partial match."],
  [158, "TextBox 13", "Related glial cell types"],
  [158, "TextBox 14", "PAPOLA appears in ROSMAP OPCs and SEA-AD oligodendrocytes, which are related cell types, but the sex/APOE groups differ."],
  [158, "TextBox 16", "Across all genes, 3 of 43 genes returned in SEA-AD were also among 228 genes returned in ROSMAP. The odds ratio was 3.15, but P = 0.0812 did not meet the significance threshold."],

  [159, "TextBox 1", "Why this matters: pathway agreement can remain even when KDA returns different genes"],
  [159, "TextBox 2", "The cohorts use different networks, disease labels, available cell types, and DEG thresholds for KDA input."],
  [159, "TextBox 5", "Different gene connections change the rankings"],
  [159, "TextBox 6", "Different cohort-specific networks can return different genes from the same DEG input gene set."],
  [159, "TextBox 9", "Only 22 SEA-AD KDA calls were available"],
  [159, "TextBox 10", "Twenty of 22 are male ε3/ε3, so most sex/APOE groups have little or no coverage."],
  [159, "TextBox 13", "Two recurring mitochondrial gene-set patterns"],
  [159, "TextBox 14", "Female ε3/ε3 excitatory and male ε3/ε3 inhibitory mitochondrial patterns recur, although the exact genes returned from KDA calls differ."],
  [159, "TextBox 17", "Support for the same gene set can strengthen a ROSMAP result without confirming the same gene as the upstream regulator."],

  [160, "TextBox 5", "Support from one comparison"],
  [160, "TextBox 7", "Nine core MT genes are upregulated in AD in both cohorts; the multiple-testing-adjusted overlap P value is 0.00505."],
  [160, "TextBox 9", "Only one matched SEA-AD excitatory KDA call was available for comparison."],
  [160, "TextBox 12", "Support from several comparisons"],
  [160, "TextBox 14", "Nineteen of 22 genes shared between inhibitory-neuron DEG sets change in the same direction in every contributing fine-cell type."],
  [160, "TextBox 16", "The direct broad-cell ROSMAP result changes depending on which cell types contribute."],
  [160, "TextBox 18", "Overall overlap of genes returned from KDA calls"],
  [160, "TextBox 19", "Suggestive but not significant"],
  [160, "TextBox 21", "Three genes were returned in both cohorts, more than the average expected by chance."],
  [160, "TextBox 23", "The cross-cohort overlap of returned genes has P = 0.0812 and does not meet the significance threshold."],
];

const NOTE_REPLACEMENTS = [
  ["ribosome module", "group of ribosome genes"],
  ["all six sex/APOE strata", "all six sex/APOE groups"],
  ["neuronal KDA queries", "neuronal KDA input DEG sets"],
  ["coherent neighborhood", "repeated connections to mitochondrial genes"],
  ["network topology", "the network’s connection pattern"],
  ["Degree-matched network tests", "Tests comparing genes with similar numbers of network connections"],
  ["OXPHOS neighborhoods", "connections to OXPHOS genes"],
  ["exact-context support is unavailable", "SEA-AD could not test the same sex/APOE and cell category"],
  ["transcriptional coupling", "coordinated RNA production"],
  ["global mitochondrial RNA", "overall mitochondrial RNA abundance"],
  ["polycistronic RNAs", "long mitochondrial RNAs that are later cut into individual gene products"],
  ["hub status", "many network connections"],
  ["Bulk reanalysis", "Reanalysis of mixed-cell tissue"],
  ["cell-resolved external validation", "validation in individual cell types and another cohort"],
  ["ER redox", "oxidation control in the ER"],
  ["neuronal redox", "oxidation control in neurons"],
  ["mitochondrial translation", "protein production inside mitochondria"],
  ["mitochondrial-translation", "mitochondrial protein-production"],
  ["network proximity", "genes being close together in the network"],
  ["redox balance", "control of oxidative stress"],
  ["protein quality control", "removal of damaged proteins"],
  ["mitochondrial quality control", "removal of damaged mitochondrial proteins"],
  ["proteostasis", "removal of damaged proteins"],
  ["hypoxia", "low oxygen"],
  ["mitophagy", "removal of damaged mitochondria"],
  ["driver matches", "matches among genes returned from KDA calls"],
  ["exact driver identities", "the exact genes returned from KDA calls"],
  ["network edges", "network connections"],
  ["network edge", "network connection"],
  ["drivers", "genes returned from KDA calls"],
  ["strata", "sex/APOE groups"],
  ["contexts", "settings"],
];

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

function parseNdjson(ndjson) {
  return (ndjson || "")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function replaceEvery(text, replacements) {
  let revised = text;
  for (const [before, after] of replacements) revised = revised.split(before).join(after);
  return revised;
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
    throw new Error(`Source deck changed before the edit: ${sourceHash}`);
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
    (
      await presentation.inspect({
        kind: "textbox",
        include: "id,slide,name,text,textPreview,bbox",
        maxChars: 5000000,
      })
    ).ndjson,
  );
  const recordByKey = new Map(
    snapshot
      .filter((record) => record.kind === "textbox")
      .map((record) => [`${record.slide}\t${record.name}`, record]),
  );

  const visibleChanges = [];
  for (const [slideNumber, shapeName, after] of EDITS) {
    const record = recordByKey.get(`${slideNumber}\t${shapeName}`);
    if (!record?.id || typeof record.text !== "string") {
      throw new Error(`Could not resolve slide ${slideNumber}, ${shapeName}`);
    }
    if (record.text === after) continue;
    const shape = presentation.resolve(record.id);
    shape.text.replace(record.text, after);
    visibleChanges.push({
      slide: slideNumber,
      name: shapeName,
      before: record.text,
      after,
    });
  }
  if (!visibleChanges.length) throw new Error("No visible text changes were applied");

  const visibleReplacementsBySlide = new Map();
  for (const change of visibleChanges) {
    if (!visibleReplacementsBySlide.has(change.slide)) {
      visibleReplacementsBySlide.set(change.slide, []);
    }
    visibleReplacementsBySlide.get(change.slide).push([change.before, change.after]);
  }

  const notesSnapshot = parseNdjson(
    (await presentation.inspect({ kind: "notes", maxChars: 5000000 })).ndjson,
  );
  const noteTextBySlide = new Map(
    notesSnapshot
      .filter((record) => record.kind === "notes" && Number.isInteger(record.slide))
      .map((record) => [record.slide, record.text || ""]),
  );
  const noteChanges = [];
  for (const slideNumber of [...visibleReplacementsBySlide.keys()].sort((a, b) => a - b)) {
    const before = noteTextBySlide.get(slideNumber) || "";
    let after = replaceEvery(before, visibleReplacementsBySlide.get(slideNumber));
    after = replaceEvery(after, NOTE_REPLACEMENTS);
    if (after !== before) {
      slides[slideNumber - 1].speakerNotes.textFrame.setText(after);
      slides[slideNumber - 1].speakerNotes.setVisible(true);
      noteChanges.push({ slide: slideNumber, before, after });
    }
  }

  const changeLog = {
    source: SOURCE,
    sourceSha256: sourceHash,
    visibleChanges,
    noteChanges,
  };
  await fs.writeFile(
    path.join(BUILD_DIR, "plain-language-changes.json"),
    JSON.stringify(changeLog, null, 2) + "\n",
    "utf8",
  );

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source presentation changed during the edit");
  }

  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const changedVisibleSlides = [...new Set(visibleChanges.map((change) => change.slide))].sort(
    (a, b) => a - b,
  );
  const changedNotesSlides = [...new Set(noteChanges.map((change) => change.slide))].sort(
    (a, b) => a - b,
  );
  const expectedChangedParts = [];
  for (const slideNumber of changedVisibleSlides) {
    const partName = `ppt/slides/slide${slideNumber}.xml`;
    const content = await artifactZip.file(partName)?.async("string");
    if (!content) throw new Error(`Artifact candidate is missing ${partName}`);
    sourceZip.file(partName, content);
    expectedChangedParts.push(partName);
  }
  for (const slideNumber of changedNotesSlides) {
    const partName = `ppt/notesSlides/notesSlide${slideNumber}.xml`;
    const content = await artifactZip.file(partName)?.async("string");
    if (!content) throw new Error(`Artifact candidate is missing ${partName}`);
    sourceZip.file(partName, content);
    expectedChangedParts.push(partName);
  }

  const hybridCandidatePath = path.join(BUILD_DIR, "candidate.pptx");
  await fs.writeFile(
    hybridCandidatePath,
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
    candidatePath: hybridCandidatePath,
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
    receiptPath: path.join(BUILD_DIR, "slides95_160.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalSnapshot = parseNdjson(
    (
      await reopened.inspect({
        kind: "textbox",
        include: "id,slide,name,text,textPreview,bbox",
        maxChars: 5000000,
      })
    ).ndjson,
  );
  const finalByKey = new Map(
    finalSnapshot
      .filter((record) => record.kind === "textbox")
      .map((record) => [`${record.slide}\t${record.name}`, record.text]),
  );
  for (const [slideNumber, shapeName, expectedText] of EDITS) {
    if (finalByKey.get(`${slideNumber}\t${shapeName}`) !== expectedText) {
      throw new Error(`Final text mismatch on slide ${slideNumber}, ${shapeName}`);
    }
  }

  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const actualChangedParts = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Final deck is missing ${name}`);
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) actualChangedParts.push(name);
  }
  actualChangedParts.sort();
  expectedChangedParts.sort();
  if (
    actualChangedParts.length !== expectedChangedParts.length ||
    actualChangedParts.some((name, index) => name !== expectedChangedParts[index])
  ) {
    throw new Error(`Unexpected package changes: ${actualChangedParts.join(", ")}`);
  }

  if (sha256(await fs.readFile(SOURCE)) !== sourceHash) {
    throw new Error("The source presentation changed before final installation");
  }
  await fs.copyFile(FINAL_PPTX, SOURCE);

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        originalSha256: sourceHash,
        output: FINAL_PPTX,
        outputSha256: sha256(await fs.readFile(FINAL_PPTX)),
        updatedSlides: changedVisibleSlides,
        updatedNotesSlides: changedNotesSlides,
        visibleChangeCount: visibleChanges.length,
        noteChangeCount: noteChanges.length,
        changedParts: actualChangedParts,
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
