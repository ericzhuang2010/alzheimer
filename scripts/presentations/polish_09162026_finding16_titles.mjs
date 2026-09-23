#!/usr/bin/env node

/** Remove a duplicated Finding 16 label and keep APOE explicit in the evidence-limit title. */

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
  "results/presentations/09162026_clarify_finding16_20260922_v2",
);
const BUILD_DIR = path.join(RUN_DIR, "build");
const FINAL_PPTX = path.join(
  RUN_DIR,
  "output/09162026_sex_apoe_kda_fine_broad_finding16_clarified_20260922_v2.pptx",
);
const EXPECTED_SOURCE_SHA256 =
  "8416bdea39b3462571f505ffb1870785470fa606720a114e346bcd58dcc4240a";
const SLIDE_COUNT = 154;
const REPLACEMENTS = [
  {
    slide: 149,
    before: "Finding 16: vascular stress-response genes in the female APOE ε4 group",
    after: "Vascular stress-response genes in the female APOE ε4 group",
  },
  {
    slide: 152,
    before: "Two KDA calls make the female ε4 subgroup result preliminary",
    after: "Two KDA calls make the female APOE ε4 subgroup result preliminary",
  },
];

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function parseNdjson(ndjson) {
  return (ndjson || "")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
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
  const snapshot = parseNdjson(
    (await presentation.inspect({ kind: "textbox", maxChars: 6000000 })).ndjson,
  );
  for (const replacement of REPLACEMENTS) {
    const matches = snapshot.filter(
      (record) =>
        record.kind === "textbox" &&
        record.slide === replacement.slide &&
        record.text === replacement.before,
    );
    if (matches.length !== 1) {
      throw new Error(`Expected one match on slide ${replacement.slide}, found ${matches.length}`);
    }
    presentation.resolve(matches[0].id).text.replace(replacement.before, replacement.after);
  }

  const artifactCandidate = path.join(BUILD_DIR, "artifact-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(artifactCandidate);
  const sourceZip = await JSZip.loadAsync(sourceBuffer);
  const artifactZip = await JSZip.loadAsync(await fs.readFile(artifactCandidate));
  const changedParts = REPLACEMENTS.map(({ slide }) => `ppt/slides/slide${slide}.xml`);
  for (const part of changedParts) {
    const xml = await artifactZip.file(part)?.async("string");
    if (!xml) throw new Error(`Updated slide part missing: ${part}`);
    sourceZip.file(part, xml);
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

  const finalZip = await JSZip.loadAsync(await fs.readFile(FINAL_PPTX));
  const originalZip = await JSZip.loadAsync(sourceBuffer);
  const actualChanged = [];
  for (const [name, entry] of Object.entries(originalZip.files)) {
    if (entry.dir) continue;
    const finalEntry = finalZip.file(name);
    if (!finalEntry) throw new Error(`Package part deleted unexpectedly: ${name}`);
    const [before, after] = await Promise.all([
      entry.async("nodebuffer"),
      finalEntry.async("nodebuffer"),
    ]);
    if (sha256(before) !== sha256(after)) actualChanged.push(name);
  }
  actualChanged.sort();
  changedParts.sort();
  if (
    actualChanged.length !== changedParts.length ||
    actualChanged.some((name, index) => name !== changedParts[index])
  ) {
    throw new Error(`Unexpected changed package parts: ${actualChanged.join(", ")}`);
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
        finalSlideCount: SLIDE_COUNT,
        updatedSlides: REPLACEMENTS.map(({ slide }) => slide),
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
