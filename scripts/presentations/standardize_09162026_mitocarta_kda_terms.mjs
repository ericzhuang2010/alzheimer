#!/usr/bin/env node

/** Standardize MitoCarta query and KDA-driver terminology in the 2026-09-16 deck. */

import crypto from "node:crypto";
import { spawnSync } from "node:child_process";
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
  "results/presentations/09162026_kda_call_wording_v11/build",
);
const FINAL_PPTX = path.join(
  WORKSPACE_DIR,
  "results/presentations/09162026_kda_call_wording_v11/output/09162026_sex_apoe_kda_fine_broad_kda_call_wording_20260919.pptx",
);
const FIGURE_BUILD_DIR = path.join(BUILD_DIR, "figures");
const FIGURE_REGENERATOR = path.join(
  WORKSPACE_DIR,
  "scripts/presentations/regenerate_kda_call_recurrence_figures.py",
);
const PROJECT_PYTHON = path.join(WORKSPACE_DIR, ".venv/bin/python");
const EXPECTED_SLIDES = 161;

const TERM_PATTERN =
  /non-MT|non-mitochondrial|core-MT|core-MitoCarta|core_mito_protein|call_key_drivers?|mitochondrial (?:DEG )?(?:query|queries)|(?<!MitoCarta )MT DEGs|MT-\*|KDA runs?|Run KDA|Run key-driver analysis|returned by KDA|returned by (?:one|at least two) KDA calls?|KDA returns|KDA-run|fine-cell runs|rerun KDA|proceeds to KDA/i;

const REPRESENTATIVE_SLIDES = [16, 20, 21, 24, 29, 31, 34, 36, 38, 39, 87, 157];
const RECURRENCE_FIGURE_SLIDES = [24, 25, 26, 27, 34];

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

function parseNdjson(ndjson) {
  return (ndjson || "")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function relationshipAttributes(tag) {
  return Object.fromEntries(
    [...tag.matchAll(/([A-Za-z:]+)="([^"]*)"/g)].map((match) => [match[1], match[2]]),
  );
}

function relationshipPartPath(ownerPartPath) {
  return path.posix.join(
    path.posix.dirname(ownerPartPath),
    "_rels",
    `${path.posix.basename(ownerPartPath)}.rels`,
  );
}

function targetPartPath(ownerPartPath, target) {
  if (target.startsWith("/")) return target.slice(1);
  return path.posix.normalize(path.posix.join(path.posix.dirname(ownerPartPath), target));
}

async function remapSlideRelationshipIds({
  sourceZip,
  artifactZip,
  sourceSlidePart,
  artifactSlidePart,
  artifactSlideXml,
}) {
  const sourceRelsXml = await sourceZip
    .file(relationshipPartPath(sourceSlidePart))
    ?.async("string");
  const artifactRelsXml = await artifactZip
    .file(relationshipPartPath(artifactSlidePart))
    ?.async("string");
  if (!sourceRelsXml || !artifactRelsXml) {
    throw new Error(`Missing relationships for ${sourceSlidePart}`);
  }
  const sourceRelationships = [
    ...sourceRelsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g),
  ].map((match) => relationshipAttributes(match[0]));
  const artifactRelationships = [
    ...artifactRelsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g),
  ].map((match) => relationshipAttributes(match[0]));
  let remapped = artifactSlideXml;
  for (const artifactRelation of artifactRelationships) {
    if (!artifactRelation.Id || !artifactRelation.Type || !artifactRelation.Target) continue;
    const artifactTarget = targetPartPath(artifactSlidePart, artifactRelation.Target);
    const sourceRelation = sourceRelationships.find(
      (item) =>
        item.Type === artifactRelation.Type &&
        item.Target &&
        targetPartPath(sourceSlidePart, item.Target) === artifactTarget,
    );
    if (!sourceRelation?.Id) {
      throw new Error(
        `Could not map ${artifactRelation.Id} (${artifactRelation.Type}, ${artifactTarget}) on ${sourceSlidePart}`,
      );
    }
    remapped = remapped.replaceAll(artifactRelation.Id, sourceRelation.Id);
  }
  return remapped;
}

async function orderedSlidePartPaths(zip) {
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
  const relationships = [
    ...presentationRels.matchAll(/<Relationship\b[^>]*\/?\s*>/g),
  ].map((match) => relationshipAttributes(match[0]));
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

async function imagePartForSlide(zip, slidePart) {
  const relsPath = relationshipPartPath(slidePart);
  const relsXml = await zip.file(relsPath)?.async("string");
  if (!relsXml) throw new Error(`Missing slide relationships: ${relsPath}`);
  const imageRelationships = [
    ...relsXml.matchAll(/<Relationship\b[^>]*\/?\s*>/g),
  ]
    .map((match) => relationshipAttributes(match[0]))
    .filter((item) => item.Type?.endsWith("/image") && item.Target);
  if (imageRelationships.length !== 1) {
    throw new Error(
      `Expected one image relationship for ${slidePart}, found ${imageRelationships.length}`,
    );
  }
  return targetPartPath(slidePart, imageRelationships[0].Target);
}

function standardizeTerms(text) {
  let revised = text;
  revised = revised.replace(
    "test genes in input query to call_key_drivers().",
    "tested genes are the MitoCarta MT genes in the KDA query.",
  );
  revised = revised.replace("), tested genes are", "). Tested genes are");
  revised = revised.replace("Run call_key_drivers()", "Run key-driver analysis");
  revised = revised.replace(/call_key_drivers calls/g, "KDA calls");
  revised = revised.replace(/call_key_drivers?\(\)/g, "KDA calls");
  revised = revised.replace(/call_key_drivers?/g, "KDA calls");
  revised = revised.replace(/Returned MT-\* genes/g, "Returned MitoCarta MT genes");
  revised = revised.replace(/MT-\* genes/g, "MitoCarta MT genes");
  revised = revised.replace(/is MT-\*/g, "is a MitoCarta MT gene");
  revised = revised.replace(/\bcore-MitoCarta\b/g, "MitoCarta MT");
  revised = revised.replace(/\bcore-MT\b/g, "MitoCarta MT");
  revised = revised.replace(/\bnon-mitochondrial\b/gi, "non-MitoCarta");
  revised = revised.replace(/\bnon-MT\b/g, "non-MitoCarta");
  revised = revised.replace(/\bMitochondrial DEG query\b/g, "MitoCarta MT DEG query");
  revised = revised.replace(/\bmitochondrial DEG query\b/g, "MitoCarta MT DEG query");
  revised = revised.replace(/\bMitochondrial query genes\b/g, "MitoCarta MT query genes");
  revised = revised.replace(/\bmitochondrial query genes\b/g, "MitoCarta MT query genes");
  revised = revised.replace(/\bMitochondrial query\b/g, "MitoCarta MT query");
  revised = revised.replace(/\bmitochondrial query\b/g, "MitoCarta MT query");
  revised = revised.replace(/\bMitochondrial queries\b/g, "MitoCarta MT queries");
  revised = revised.replace(/\bmitochondrial queries\b/g, "MitoCarta MT queries");
  revised = revised.replace(/(?<!MitoCarta )\bMT DEGs\b/g, "MitoCarta MT DEGs");
  revised = revised.replace(
    /\beffective mitochondrial genes\b/gi,
    "effective MitoCarta MT genes",
  );
  revised = revised.replace(/\bRun key-driver analysis\b/g, "Make KDA calls");
  revised = revised.replace(/\bKDA runs\b/g, "KDA calls");
  revised = revised.replace(/\bKDA run\b/g, "KDA call");
  revised = revised.replace(/\bRun KDA\b/g, "Make KDA calls");
  revised = revised.replace(/\brerun KDA\b/g, "make new KDA calls");
  revised = revised.replace(/\bKDA-run\b/g, "KDA call");
  revised = revised.replace(/\bKDA-call\b/g, "KDA call");
  revised = revised.replace(/\bKDA returned key driver\b/g, "gene returned from KDA call");
  revised = revised.replace(/\breturned by KDA\b/g, "returned from KDA call");
  revised = revised.replace(/\bKDA returns\b/g, "rows returned from KDA calls");
  revised = revised.replace(/\bfine-cell runs\b/g, "fine-cell KDA calls");
  revised = revised.replace(/\bproceeds to KDA\b/g, "leads to a KDA call");
  revised = revised.replace(/\bOne completed call\b/g, "One completed KDA call");
  revised = revised.replace(/\ba completed KDA test\b/g, "a completed KDA call");
  revised = revised.replace(/\bCall key\s+driver\b/gi, "Make KDA calls");
  revised = revised.replace(/\bCall key\s+drivers\b/gi, "Make KDA calls");
  revised = revised.replace(
    "Counts are category presence—not independent replication or call counts.",
    "Counts are category presence—not independent replication or counts of KDA calls.",
  );
  revised = revised.replace(
    "program-call enrichments",
    "pathway enrichments across KDA calls",
  );
  revised = revised.replace(
    "the Vasculature × M_e2 4-versus-3-donor call, which alone generated 26 driver rows",
    "the Vasculature × M_e2 KDA call based on 4 versus 3 donors, which returned 26 significant gene rows",
  );
  revised = revised.replace(
    "KDA-returned gene count is confounded",
    "Count of genes returned from KDA calls is confounded",
  );
  revised = revised.replace(
    "Driver abundance is confounded",
    "Count of genes returned from KDA calls is confounded",
  );
  revised = revised.replace(
    "KDA-returned gene is not a strong DEG",
    "Gene returned from KDA calls ≠ strong DEG",
  );
  revised = revised.replace(
    "Driver not a strong DEG",
    "Gene returned from KDA calls ≠ strong DEG",
  );
  revised = revised.replace(
    "The driver frequently changes expression as well as appearing in the network",
    "The gene returned from KDA calls also changes expression frequently",
  );
  revised = revised.replace(
    "A tested but unreturned driver",
    "A tested gene not returned from a KDA call",
  );
  revised = revised.replace(/\breturned drivers\b/gi, "genes returned from KDA calls");
  revised = revised.replace(/\breturned driver\b/gi, "gene returned from a KDA call");
  revised = revised.replace(/\bdriver rows\b/gi, "gene rows returned from KDA calls");
  revised = revised.replace(
    "SEA-AD did not select SELENOM as a key driver in those calls.",
    "SELENOM was not returned from those SEA-AD KDA calls.",
  );
  revised = revised.replace(/\bwithin-call\b/gi, "within each KDA call");
  revised = revised.replace(/\bone-call\b/gi, "one KDA call");
  revised = revised.replace(/\breturned-call\b/gi, "returned KDA call");
  revised = revised.replace(/\bcall-count\b/gi, "KDA call count");
  revised = revised.replace(/\breturned by one KDA call\b/gi, "returned from one KDA call");
  revised = revised.replace(
    /\breturned by at least two KDA calls\b/gi,
    "returned from at least two KDA calls",
  );
  revised = revised.replace(/(?<!KDA )(?<!-)\bcalls\b/gi, "KDA calls");
  revised = revised.replace(/(?<!KDA )(?<!-)\bcall\b/gi, "KDA call");
  return revised;
}

function refineVisibleText(record) {
  const { slide: slideNumber, name, text } = record;
  let revised = standardizeTerms(text);
  if (slideNumber === 3) {
    revised = revised.replace("aggregation happens after KDA.", "aggregation happens after KDA calls.");
    revised = revised.replace(
      "One contrast → run DEG and at most one KDA call",
      "One contrast → run DEG → Make KDA calls (at most one)",
    );
    revised = revised.replace(
      "The call returns a list of significant key-driver genes for that contrast.",
      "Output: significant genes returned from the KDA call for that contrast.",
    );
    revised = revised.replace(
      "The KDA call returns a list of significant key-driver genes for that contrast.",
      "Output: significant genes returned from the KDA call for that contrast.",
    );
  }
  if (slideNumber === 14) {
    revised = revised.replace(/^KDA analysis$/g, "KDA calls");
  }
  if (slideNumber === 16) {
    revised = revised.replace(
      "Four steps: run DEG per contrast, one KDA query per contrast",
      "Four steps: run DEG per contrast, then make KDA calls",
    );
    revised = revised.replace(/^KDA call$/g, "KDA calls");
    revised = revised.replace(
      "Build query per contrast with MitoCarta MT DEGs",
      "Build one query per contrast from MitoCarta MT DEGs",
    );
    revised = revised.replace("Use call_key_drivers", "Make KDA calls");
    revised = revised.replace("Use KDA calls", "Make KDA calls");
    revised = revised.replace(
      "KDA run for valid DEG contrast valid\nnumber of genes in query ≥ 3",
      "Make KDA calls when the mapped query\ncontains ≥3 genes",
    );
    revised = revised.replace(
      "KDA call for valid DEG contrast valid\nnumber of genes in query ≥ 3",
      "Make KDA calls when the mapped query\ncontains ≥3 genes",
    );
  }
  if (slideNumber === 17 || slideNumber === 29) {
    revised = revised.replace(
      "Each contrast contributes at most one MitoCarta MT DEG query; significant non-MitoCarta returns are aggregated by category.",
      "Each contrast contributes at most one MitoCarta MT DEG query. Significant non-MitoCarta key drivers are aggregated by category.",
    );
    revised = revised.replace(
      "Significant non-MitoCarta key drivers are aggregated by category.",
      "Non-MitoCarta genes returned from KDA calls are aggregated by category.",
    );
  }
  if (slideNumber === 17) {
    revised = revised.replace(
      "Aggregate gene returned from KDA call using ACAT for each category",
      "Aggregate genes returned from KDA calls within each category using ACAT",
    );
  }
  if (slideNumber === 15) {
    revised = revised.replace("usable calls", "usable KDA calls");
    revised = revised.replace("and returned drivers", "and genes returned from KDA calls");
    revised = revised.replace(
      "recurring returned values",
      "recurring genes returned from KDA calls",
    );
    revised = revised.replace(
      "Key-driver genes are ranked separately within each category.",
      "Genes returned from KDA calls are ranked separately within each category.",
    );
  }
  if (slideNumber === 18 || slideNumber === 30) {
    revised = revised.replace(/\bKDA called\?/g, "KDA call made?");
    revised = revised.replace(/^TOTAL (\d+) (\d+) calls$/g, "TOTAL $1 $2 KDA calls");
    revised = revised.replace(/^(\d+) calls$/g, "$1 KDA calls");
  }
  if (slideNumber === 19) {
    revised = revised.replace(
      "Source validity and query size decide whether KDA is called",
      "Source validity and query size decide whether a KDA call is made",
    );
    revised = revised.replace(
      "All 194 validated completed calls enter the aggregate.",
      "All 194 completed KDA calls enter the aggregate.",
    );
    revised = revised.replace(
      "The 164 significant calls returned 1,833 rows before mitochondrial filtering.",
      "The 164 significant KDA calls returned 1,833 gene rows before MitoCarta filtering.",
    );
  }
  if (slideNumber === 20) {
    if (name === "TextBox 16") {
      revised = "Query = significant DEGs ∩ MitoCarta MT genes";
    } else if (name === "TextBox 26") {
      revised = "MitoCarta MT DEG occurrences";
    } else if (name === "TextBox 30") {
      revised = "9,262 provisional query occurrences";
    } else if (name === "TextBox 32") {
      revised = "= 7,933 mapped query occurrences";
    }
  }
  if (slideNumber === 21 || slideNumber === 31) {
    revised = revised.replace("gene x category", "gene × category");
    revised = revised.replace("categories with non-MitoCarta returns", "categories represented");
    revised = revised.replace("categories with returns", "categories represented");
    revised = revised.replace(
      "non-MitoCarta gene returned from call_key_driver (before aggregation)",
      "non-MitoCarta gene returned by KDA (before aggregation)",
    );
  }
  if (slideNumber === 21) {
    revised = revised.replace("call counts", "counts of KDA calls");
    revised = revised.replace("KDA-call counts", "counts of KDA calls");
    revised = revised.replace(
      "Where non-MitoCarta driver units occur",
      "Where non-MitoCarta gene × category units occur",
    );
  }
  if ([24, 25, 26, 27, 34].includes(slideNumber)) {
    revised = revised.replace(/^(ROSMAP .+)-neuron drivers recur/, "$1-neuron genes returned from KDA calls recur");
    revised = revised.replace(
      /^ROSMAP (astrocyte|OPC) drivers recur/,
      "ROSMAP $1 genes returned from KDA calls recur",
    );
    revised = revised.replace(
      /^SEA-AD excitatory-neuron drivers occur/,
      "SEA-AD excitatory-neuron genes returned from KDA calls occur",
    );
    const shortTitles = {
      24: "ROSMAP excitatory neurons: genes returned from KDA calls",
      25: "ROSMAP inhibitory neurons: genes returned from KDA calls",
      26: "ROSMAP astrocytes: genes returned from KDA calls",
      27: "ROSMAP OPCs: genes returned from KDA calls",
      34: "SEA-AD excitatory neurons: genes returned from KDA calls",
    };
    if (
      revised.includes("genes returned from KDA calls") &&
      (revised.includes("sex/APOE groups") || slideNumber === 34)
    ) {
      revised = shortTitles[slideNumber];
    }
  }
  if (slideNumber === 29) {
    revised = revised.replace("20 of 22 calls are M_e33.", "20 of 22 KDA calls are M_e33.");
    revised = revised.replace(
      "Do drivers return in an independent human cohort?",
      "Do the same genes returned from KDA calls recur in SEA-AD?",
    );
  }
  if (slideNumber === 30) {
    revised = revised.replace(
      "20 M_e33 calls, one F_e33 call, and one F_e4 call",
      "20 M_e33 KDA calls, one F_e33 KDA call, and one F_e4 KDA call",
    );
  }
  if (slideNumber === 31) {
    revised = revised.replace(
      "20 KDA calls returned results; 2 completed with no significant return.",
      "20 KDA calls returned significant genes; 2 returned no significant genes.",
    );
    revised = revised.replace(
      "20 call_key_driver with returned results; 2 completed empty.",
      "20 KDA calls returned results; 2 completed with no significant return.",
    );
    revised = revised.replace(
      "112 significant return rows before mitochondrial filtering.",
      "112 significant KDA rows before MitoCarta filtering.",
    );
    revised = revised.replace(
      "112 significant KDA rows before MitoCarta filtering.",
      "112 significant gene rows returned from KDA calls before MitoCarta filtering.",
    );
  }
  if (slideNumber === 36) {
    revised = revised.replace("Significant driver rows", "Genes returned from KDA calls");
    revised = revised.replace(
      "Driver rows count significant returned KDA rows. Unique non-MitoCarta drivers exclude MitoCarta MT genes and are deduplicated within each cohort.",
      "Driver rows count significant KDA returns. Unique non-MitoCarta drivers exclude the 1,136 MitoCarta MT genes and are deduplicated within each cohort.",
    );
    revised = revised.replace(
      "Driver rows count significant rows returned from KDA calls.",
      "Driver rows count significant gene rows returned from KDA calls.",
    );
    revised = revised.replace("Unique non-MitoCarta drivers", "Unique non-MitoCarta genes");
    revised = revised.replace(
      "Driver rows count significant gene rows returned from KDA calls.",
      "This column counts significant gene rows returned from KDA calls.",
    );
  }
  if (slideNumber === 37) {
    revised = revised.replace(
      "all five KDA calls and all returned drivers remain unchanged.",
      "all five KDA calls and all genes returned from KDA calls remain unchanged.",
    );
    revised = revised.replace(
      "the Vasculature × M_e2 4-versus-3-donor call, which alone generated 26 driver rows",
      "the Vasculature × M_e2 KDA call based on 4 versus 3 donors, which returned 26 significant gene rows",
    );
    revised = revised.replace(
      "with no shared drivers.",
      "with no shared genes returned from KDA calls.",
    );
  }
  if (slideNumber === 38) {
    revised = revised.replace("Unique non-MitoCarta KDs", "Unique non-MitoCarta genes");
    revised = revised.replace("Unique non-MitoCarta drivers", "Unique non-MitoCarta genes");
    revised = revised.replace("Significant KD rows", "Genes returned from KDA calls");
    revised = revised.replace(
      "Minimum effective genes after network mapping; donor minimum held at 3 per disease arm.",
      "Minimum MitoCarta MT query genes after network mapping; donor minimum held at 3 per disease arm.",
    );
  }
  if (slideNumber === 39) {
    revised = revised.replace("9 driver rows", "9 gene rows returned from KDA calls");
    revised = revised.replace("20 unique non-MitoCarta drivers", "20 unique non-MitoCarta genes");
    revised = revised.replace("18 → 3 unique non-MitoCarta drivers", "18 → 3 unique non-MitoCarta genes");
    revised = revised.replace(
      "whose sole return is a MitoCarta MT gene",
      "whose sole gene returned from its KDA call is a MitoCarta MT gene",
    );
    revised = revised.replace("The non-MitoCarta driver count", "The non-MitoCarta gene count");
  }
  if (slideNumber === 40) {
    revised = revised.replace("preserving every SEA-AD run", "preserving every SEA-AD KDA call");
    revised = revised.replace(
      "cross-cohort driver validation",
      "cross-cohort validation of genes returned from KDA calls",
    );
    revised = revised.replace(
      "Cross-cohort non-MitoCarta driver overlap",
      "Cross-cohort overlap among non-MitoCarta genes returned from KDA calls",
    );
    revised = revised.replace(
      "with no shared drivers.",
      "with no shared genes returned from KDA calls.",
    );
  }
  if (slideNumber === 43) {
    revised = revised.replace("across ROSMAP calls", "across ROSMAP KDA calls");
  }
  if (slideNumber === 46) {
    revised = revised.replace("across ROSMAP calls", "across ROSMAP KDA calls");
  }
  if (slideNumber === 44) {
    revised = revised.replace("For all eligible F_e33 calls", "Across eligible F_e33 KDA calls");
  }
  if (slideNumber === 45) {
    revised = revised.replace("matched female ε3/ε3 excitatory call", "matched female ε3/ε3 excitatory KDA call");
    revised = revised.replace(
      "SEA-AD does not select the same upstream driver.",
      "SEA-AD does not return the same candidate gene from its KDA call.",
    );
  }
  if (slideNumber === 49) {
    revised = revised.replace(
      "without matching the exact ROSMAP drivers",
      "without matching the same genes returned from ROSMAP KDA calls",
    );
  }
  if (slideNumber === 51) {
    revised = revised.replace("occurrences repeat genes across calls", "occurrences repeat genes across queries");
    revised = revised.replace(
      "not the number of key drivers returned",
      "not the number of genes returned from KDA calls",
    );
  }
  if (slideNumber === 52) {
    revised = revised.replace("8 matched calls were evaluable", "8 matched KDA calls were evaluable");
    revised = revised.replace(
      "rather than exact-driver replication",
      "rather than replication of the same gene returned from KDA calls",
    );
  }
  if ([59, 66, 73].includes(slideNumber)) {
    revised = revised.replace(/\beligible calls\b/g, "eligible KDA calls");
    revised = revised.replace(/\bTen calls\b/g, "Ten KDA calls");
  }
  if (slideNumber === 74) {
    revised = revised.replace("ALL ELIGIBLE CALLS", "ALL ELIGIBLE KDA CALLS");
    revised = revised.replace(
      "drivers returned",
      "genes returned from KDA calls",
    );
    revised = revised.replace(
      "KDA driver counts",
      "counts of genes returned from KDA calls",
    );
  }
  if (slideNumber === 75) {
    revised = revised.replace("Driver abundance is confounded", "KDA-returned gene count is confounded");
    revised = revised.replace(
      "opportunities for KDA to return candidates",
      "opportunities for a gene to be returned from a KDA call",
    );
  }
  if (slideNumber === 76) {
    revised = revised.replace("stronger driver biology", "a stronger KDA signal");
    revised = revised.replace("Repeat KDA with", "Make KDA calls with");
  }
  if (slideNumber === 80) {
    revised = revised.replace(/\beligible calls\b/g, "eligible KDA calls");
  }
  if (slideNumber === 86) {
    revised = revised.replace(
      "more credible as one module than as 20 independent drivers",
      "more credible as one module than as 20 independent genes returned from KDA calls",
    );
    revised = revised.replace(
      "Many returned ribosomal genes sit near",
      "Many ribosomal genes returned from KDA calls sit near",
    );
  }
  if (slideNumber === 87) {
    revised = revised.replace("Within-call returns", "Genes returned from KDA calls");
    revised = revised.replace(
      "are strongly over-represented among drivers",
      "are strongly over-represented among genes returned from KDA calls",
    );
    revised = revised.replace(
      "228 unique non-MitoCarta drivers",
      "228 unique non-MitoCarta genes returned from KDA calls",
    );
    revised = revised.replace("driver genes in KEGG ribosome", "returned genes in KEGG ribosome");
    revised = revised.replace("8.8% of drivers", "8.8% of returned genes");
    revised = revised.replace(
      "categories containing non-MitoCarta drivers",
      "categories containing non-MitoCarta genes returned from KDA calls",
    );
    revised = revised.replace(
      "non-MitoCarta returns",
      "non-MitoCarta genes returned from KDA calls",
    );
  }
  if (slideNumber === 88) {
    revised = revised.replace(/\b24 calls\b/g, "24 KDA calls");
    revised = revised.replace(/\b22 calls\b/g, "22 KDA calls");
    revised = revised.replace(/\bThe calls span\b/g, "The KDA calls span");
  }
  if (slideNumber === 90) {
    revised = revised.replace("fine-cell calls", "fine-cell KDA calls");
    revised = revised.replace("Repeat KDA after", "Make KDA calls after");
  }
  if (slideNumber === 92 || slideNumber === 99 || slideNumber === 106) {
    revised = revised.replace(
      "Recurrent ROSMAP driver finding.",
      "Finding based on a recurrent gene returned from ROSMAP KDA calls.",
    );
    revised = revised.replace(
      "Focused ROSMAP driver finding.",
      "Finding based on a gene returned from ROSMAP KDA calls.",
    );
  }
  if ([93, 94].includes(slideNumber)) {
    revised = revised.replace(/\b17 neuronal calls\b/g, "17 neuronal KDA calls");
    revised = revised.replace(/\b17 supporting neuronal calls\b/g, "17 supporting neuronal KDA calls");
    revised = revised.replace(/\b17 enriched supporting queries\b/g, "17 enriched queries supporting KDA calls");
    revised = revised.replace(/\bneuronal calls\b/g, "neuronal KDA calls");
    revised = revised.replace(/\bexcitatory calls\b/g, "excitatory KDA calls");
    revised = revised.replace(/\bmale ε2 calls\b/g, "male ε2 KDA calls");
  }
  if (slideNumber === 95) {
    revised = revised.replace(/\b13 calls\b/g, "13 KDA calls");
    revised = revised.replace(/\bSix calls\b/g, "Six KDA calls");
    revised = revised.replace("no active call", "no active KDA call");
    revised = revised.replace(
      "Other drivers reinforce the lysosome and autophagy axis",
      "Other genes returned from KDA calls reinforce the lysosome and autophagy axis",
    );
  }
  if (slideNumber === 100) {
    revised = revised.replace(/\b18 calls\b/g, "18 KDA calls");
    revised = revised.replace("Driver not a strong DEG", "KDA-returned gene is not a strong DEG");
  }
  if (slideNumber === 101) {
    revised = revised.replace(/\b18 supporting excitatory calls\b/g, "18 supporting excitatory KDA calls");
    revised = revised.replace("supporting excitatory calls", "supporting excitatory KDA calls");
    revised = revised.replace(
      "KDA can nominate a gene by network position",
      "A gene can be returned from a KDA call because of its network position",
    );
    revised = revised.replace(/\bThirteen calls\b/g, "Thirteen KDA calls");
  }
  if (slideNumber === 102) {
    revised = revised.replace(/\b2 calls\b/g, "2 KDA calls");
    revised = revised.replace(/\b11 calls\b/g, "11 KDA calls");
    revised = revised.replace(/\b5 calls\b/g, "5 KDA calls");
    revised = revised.replace(/\bThree male ε4 excitatory calls\b/g, "Three male ε4 excitatory KDA calls");
    revised = revised.replace(/\bTwo male ε3\/ε3 and three male ε4 excitatory calls\b/g, "Two male ε3/ε3 and three male ε4 excitatory KDA calls");
    revised = revised.replace(
      "SEA-AD could return WDR82 in 11 matching excitatory backgrounds but did not",
      "WDR82 could have been returned from a KDA call in 11 matching SEA-AD excitatory backgrounds but was not",
    );
    revised = revised.replace("most supporting calls", "most supporting KDA calls");
    revised = revised.replace(
      "excitatory KDA calls also return WDR82",
      "WDR82 is also returned from these excitatory KDA calls",
    );
  }
  if (slideNumber === 104) {
    revised = revised.replace(
      "Cross-cohort driver replication in SEA-AD",
      "The same gene returned from KDA calls across cohorts",
    );
    revised = revised.replace("Repeat KDA without", "Make KDA calls without");
  }
  return revised;
}

function refineNotes(slideNumber, text) {
  let revised = standardizeTerms(text);
  revised = revised.replace(
    "the ranking score is that KDA call's within each KDA call BH-adjusted KDA P value",
    "the ranking score is the BH-adjusted KDA P value from that KDA call",
  );
  revised = revised.replace(
    /For a gene returned by at least two KDA calls/g,
    "For a gene returned from at least two KDA calls",
  );
  revised = revised.replace(
    "candidate driver can be a non-DEG, non-MitoCarta network gene.",
    "candidate driver can be a non-DEG network gene outside MitoCarta. Here, non-MitoCarta means that the returned gene is not one of the 1,136 MitoCarta MT genes; it may still influence mitochondrial biology.",
  );
  revised = revised.replace(
    "Intersecting those rows with core_mito_protein yields",
    "Intersecting those rows with the 1,136-gene MitoCarta MT inventory yields",
  );
  revised = revised.replace(/call_key_drivers?\(\)?/g, "KDA calls");
  revised = revised.replace("A call in which a gene was not returned", "A KDA call in which a gene was not returned");
  revised = revised.replace(
    /For a gene returned by one KDA call/g,
    "For a gene returned from one KDA call",
  );
  revised = revised.replace(
    /For a gene returned by at least two calls/g,
    "For a gene returned from at least two KDA calls",
  );
  revised = revised.replace(
    /returned non-MitoCarta drivers from eligible fine-cell KDA calls/g,
    "non-MitoCarta genes returned from eligible fine-cell KDA calls",
  );
  revised = revised.replace(
    /Significant rows are raw rows returned from KDA calls/g,
    "Significant rows are gene rows returned from KDA calls",
  );
  revised = revised.replace(
    /Returned MitoCarta MT genes explain/g,
    "MitoCarta MT genes returned from KDA calls explain",
  );
  if (slideNumber === 36) {
    revised = revised.replace(
      "Its returned driver rows fall from 39 to 13",
      "Its gene rows returned from KDA calls fall from 39 to 13",
    );
    revised = revised.replace(
      "its five KDA calls, 24 returned rows",
      "its five KDA calls, 24 gene rows returned from KDA calls",
    );
  }
  if (slideNumber === 38) {
    revised = revised.replace(
      "reduces the analysis from three runs and 39 significant rows to one run and 26 rows",
      "reduces the analysis from three KDA calls and 39 significant rows to one KDA call and 26 rows",
    );
    revised = revised.replace(
      "falls to three runs and eight rows at ten or twenty genes, and retains two runs and seven rows",
      "falls to three KDA calls and eight rows at ten or twenty genes, and retains two KDA calls and seven rows",
    );
    revised = revised.replace("filters existing calls", "filters existing KDA calls");
    revised = revised.replace("for retained calls", "for retained KDA calls");
  }
  if (slideNumber === 39) {
    revised = revised.replace("filters existing calls", "filters existing KDA calls");
  }
  revised = revised.replace(
    "while the final column excludes MitoCarta MT genes and deduplicates drivers within each cohort.",
    "while the final column excludes all 1,136 MitoCarta MT genes and deduplicates drivers within each cohort.",
  );
  revised = revised.replace(
    "Query size means the number of effective MitoCarta MT genes after network mapping",
    "Query size means the number of MitoCarta MT query genes remaining after network mapping",
  );
  revised = revised.replace(
    "Returned MitoCarta MT genes explain changes in raw row counts but are not eligible non-MitoCarta key drivers.",
    "Returned MitoCarta MT genes explain changes in raw row counts but are excluded when the analysis reports non-MitoCarta key drivers.",
  );
  return revised;
}

async function main() {
  const sourceStat = await fs.stat(SOURCE).catch(() => undefined);
  if (!sourceStat?.isFile()) throw new Error(`Missing source deck: ${SOURCE}`);
  if (await fs.stat(FINAL_PPTX).catch(() => undefined)) {
    throw new Error(`Output already exists: ${FINAL_PPTX}`);
  }
  await fs.mkdir(BUILD_DIR, { recursive: true });
  await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
  await fs.mkdir(FIGURE_BUILD_DIR, { recursive: true });

  const figureResult = spawnSync(
    PROJECT_PYTHON,
    [FIGURE_REGENERATOR, "--output-dir", FIGURE_BUILD_DIR],
    { cwd: WORKSPACE_DIR, encoding: "utf8" },
  );
  if (figureResult.status !== 0) {
    throw new Error(
      `Could not regenerate recurrence figures:\n${figureResult.stdout || ""}${figureResult.stderr || ""}`,
    );
  }

  const sourceBuffer = await fs.readFile(SOURCE);
  const sourceHash = sha256(sourceBuffer);
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
  for (const slideNumber of REPRESENTATIVE_SLIDES) {
    const png = await blobBuffer(
      await presentation.export({ slide: slides[slideNumber - 1], format: "png", scale: 1.5 }),
    );
    beforePngs.set(slideNumber, png);
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-before.png`), png);
  }

  const textSnapshot = await presentation.inspect({
    kind: "textbox",
    include: "id,slide,name,text,textPreview,bbox",
    maxChars: 4000000,
  });
  const changedVisibleSlides = new Set();
  const visibleChanges = [];
  for (const record of parseNdjson(textSnapshot.ndjson).filter(
    (item) => item.kind === "textbox" && typeof item.text === "string",
  )) {
    const revised = refineVisibleText(record);
    if (revised === record.text) continue;
    presentation.resolve(record.id).text = revised;
    changedVisibleSlides.add(record.slide);
    visibleChanges.push({ slide: record.slide, id: record.id, before: record.text, after: revised });
  }

  const notesSnapshot = await presentation.inspect({ kind: "notes", maxChars: 4000000 });
  const notesBySlide = new Map(
    parseNdjson(notesSnapshot.ndjson)
      .filter((item) => item.kind === "notes" && typeof item.text === "string")
      .map((item) => [item.slide, item.text]),
  );
  const changedNotesSlides = new Set();
  const noteChanges = [];
  for (const [slideNumber, notesText] of notesBySlide) {
    const revised = refineNotes(slideNumber, notesText);
    if (revised === notesText) continue;
    slides[slideNumber - 1].speakerNotes.textFrame.setText(revised);
    slides[slideNumber - 1].speakerNotes.setVisible(true);
    changedNotesSlides.add(slideNumber);
    noteChanges.push({ slide: slideNumber, before: notesText, after: revised });
  }

  if (!changedVisibleSlides.size || !changedNotesSlides.size) {
    throw new Error("No terminology changes were made");
  }
  await fs.writeFile(
    path.join(BUILD_DIR, "terminology-changes.json"),
    JSON.stringify({ visibleChanges, noteChanges }, null, 2) + "\n",
    "utf8",
  );

  for (const slideNumber of REPRESENTATIVE_SLIDES) {
    const png = await blobBuffer(
      await presentation.export({ slide: slides[slideNumber - 1], format: "png", scale: 1.5 }),
    );
    await fs.writeFile(path.join(BUILD_DIR, `slide-${slideNumber}-after.png`), png);
    if (changedVisibleSlides.has(slideNumber) && sha256(beforePngs.get(slideNumber)) === sha256(png)) {
      throw new Error(`Representative slide ${slideNumber} did not change visually`);
    }
  }

  const artifactCandidatePath = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidatePath);
  const currentSourceBuffer = await fs.readFile(SOURCE);
  if (sha256(currentSourceBuffer) !== sourceHash) {
    throw new Error("The source presentation changed during the terminology edit");
  }

  const sourceZip = await JSZip.loadAsync(currentSourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidatePath));
  const sourceSlideParts = await orderedSlidePartPaths(sourceZip);
  const artifactSlideParts = await orderedSlidePartPaths(artifactZip);
  if (
    sourceSlideParts.length !== EXPECTED_SLIDES ||
    artifactSlideParts.length !== EXPECTED_SLIDES
  ) {
    throw new Error("Slide-order metadata changed unexpectedly");
  }

  const expectedChangedParts = new Set();
  for (const slideNumber of changedVisibleSlides) {
    const sourceSlidePart = sourceSlideParts[slideNumber - 1];
    const artifactSlidePart = artifactSlideParts[slideNumber - 1];
    const revisedXml = await artifactZip.file(artifactSlidePart)?.async("string");
    if (!revisedXml) throw new Error(`Missing revised slide XML for slide ${slideNumber}`);
    const remappedXml = await remapSlideRelationshipIds({
      sourceZip,
      artifactZip,
      sourceSlidePart,
      artifactSlidePart,
      artifactSlideXml: revisedXml,
    });
    sourceZip.file(sourceSlidePart, remappedXml);
    expectedChangedParts.add(sourceSlidePart);
  }
  for (const slideNumber of changedNotesSlides) {
    const sourceSlidePart = sourceSlideParts[slideNumber - 1];
    const artifactSlidePart = artifactSlideParts[slideNumber - 1];
    const sourceNotesPart = await notesPartForSlide(sourceZip, sourceSlidePart);
    const artifactNotesPart = await notesPartForSlide(artifactZip, artifactSlidePart);
    const revisedXml = await artifactZip.file(artifactNotesPart)?.async("string");
    if (!revisedXml) throw new Error(`Missing revised notes XML for slide ${slideNumber}`);
    sourceZip.file(sourceNotesPart, revisedXml);
    expectedChangedParts.add(sourceNotesPart);
  }
  for (const slideNumber of RECURRENCE_FIGURE_SLIDES) {
    const sourceSlidePart = sourceSlideParts[slideNumber - 1];
    const sourceImagePart = await imagePartForSlide(sourceZip, sourceSlidePart);
    const replacementPath = path.join(
      FIGURE_BUILD_DIR,
      `slide-${slideNumber}-recurrence.png`,
    );
    sourceZip.file(sourceImagePart, await fs.readFile(replacementPath));
    expectedChangedParts.add(sourceImagePart);
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
      referenceSha256: sourceHash,
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD_DIR, "mitocarta-kda-terms.validation.json"),
  });

  const reopened = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
  const finalSnapshot = await reopened.inspect({
    kind: "textbox,notes",
    include: "id,slide,name,text,textPreview,bbox",
    maxChars: 4000000,
  });
  const lingering = parseNdjson(finalSnapshot.ndjson).filter(
    (item) => typeof item.text === "string" && TERM_PATTERN.test(item.text),
  );
  if (lingering.length) {
    await fs.writeFile(
      path.join(BUILD_DIR, "lingering-ambiguous-terms.json"),
      JSON.stringify(lingering, null, 2) + "\n",
      "utf8",
    );
    throw new Error(`Final deck still contains ${lingering.length} ambiguous terminology records`);
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
  const expected = [...expectedChangedParts].sort();
  if (
    changedParts.length !== expected.length ||
    changedParts.some((name, index) => name !== expected[index])
  ) {
    throw new Error(`Unexpected package changes: ${changedParts.join(", ")}`);
  }

  console.log(
    JSON.stringify(
      {
        source: SOURCE,
        sourceSha256: sourceHash,
        output: FINAL_PPTX,
        slideCount: EXPECTED_SLIDES,
        visibleSlidesChanged: [...changedVisibleSlides].sort((a, b) => a - b),
        notesSlidesChanged: [...changedNotesSlides].sort((a, b) => a - b),
        changedParts,
        validation,
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
