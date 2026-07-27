#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

kda_dir <- dirname(normalizePath(
  sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1L]),
  winslash = "/", mustWork = TRUE
))
source(file.path(kda_dir, "lib", "cli.R"))
source(file.path(kda_dir, "lib", "kda_validation.R"))
source(file.path(kda_dir, "lib", "kda_io.R"))

usage <- paste(
  "Usage:",
  "  Rscript scripts/analysis/kda/install_kda.R [options]",
  "",
  "Options:",
  "  --archive PATH  KDA 0.2 source archive",
  "  --force         Reinstall even if the correct version is available",
  "  --help, -h      Show this help",
  sep = "\n"
)
arguments <- commandArgs(trailingOnly = TRUE)
if ("-h" %in% arguments) {
  cat(usage, "\n")
  quit(save = "no", status = 0L)
}
options_cli <- parse_kda_cli(
  arguments,
  value_options = "archive",
  flag_options = "force",
  defaults = list(
    archive = "archive/wang_kda_code/KDA_analysis/KDA-0.2.tar.gz",
    force = FALSE
  ),
  usage = usage
)

project_root <- find_project_root(kda_dir)
archive_path <- resolve_project_path(options_cli$archive, project_root)
if (!file.exists(archive_path)) {
  kda_abort(
    "KDA archive is absent: %s\nDownload the pinned archive described in docs/analysis/mt_pathway/kda/wang_kda_package_installation.md.",
    archive_path
  )
}
archive_checksum <- sha256_file(archive_path)
if (!identical(archive_checksum, KDA_EXPECTED_ARCHIVE_SHA256)) {
  kda_abort(
    "KDA archive checksum mismatch.\nExpected: %s\nObserved: %s\nFile: %s",
    KDA_EXPECTED_ARCHIVE_SHA256,
    archive_checksum,
    archive_path
  )
}
if (!requireNamespace("renv", quietly = TRUE)) {
  kda_abort("The renv package is unavailable; bootstrap this project's renv environment first.")
}

lockfile <- jsonlite::read_json(file.path(project_root, "renv.lock"), simplifyVector = TRUE)
locked_r <- as.character(lockfile$R$Version %||% "")
if (nzchar(locked_r) && !identical(as.character(getRversion()), locked_r)) {
  kda_abort(
    "Active R is %s, but renv.lock records R %s. Load the recorded R version first.",
    as.character(getRversion()),
    locked_r
  )
}
renv::load(project_root)
correct_version <- requireNamespace("KDA", quietly = TRUE) &&
  identical(as.character(utils::packageVersion("KDA")), KDA_EXPECTED_VERSION)
if (correct_version && !isTRUE(options_cli$force)) {
  kda_message("KDA %s is already installed; no changes made.", KDA_EXPECTED_VERSION)
} else {
  renv::install(
    archive_path,
    rebuild = isTRUE(options_cli$force),
    prompt = FALSE,
    project = project_root
  )
}
assert_kda_available()
cat("KDA version:", as.character(utils::packageVersion("KDA")), "\n")
cat("KDA library:", find.package("KDA"), "\n")
cat("Archive SHA-256:", archive_checksum, "\n")
cat("No analysis outputs were created and renv.lock was not snapshotted.\n")
