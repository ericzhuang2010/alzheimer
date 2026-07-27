#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

kda_dir <- dirname(normalizePath(
  sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1L]),
  winslash = "/", mustWork = TRUE
))
source(file.path(kda_dir, "lib", "cli.R"))
source_kda_libraries(kda_dir)

usage <- paste(
  "Usage:",
  "  Rscript scripts/analysis/kda/run_signature_enrichment.R \\",
  "    --manifest PATH --run-id ID --global-dir DIR --output-dir DIR [options]",
  "",
  "Options:",
  "  --p-adjust-method NAME  Default: BH",
  "  --alpha NUMBER          Default: 0.05",
  "  --force                 Replace incompatible/partial known outputs",
  "  --help, -h              Show this help",
  sep = "\n"
)
arguments <- commandArgs(trailingOnly = TRUE)
if ("-h" %in% arguments) {
  cat(usage, "\n")
  quit(save = "no", status = 0L)
}
cli <- parse_kda_cli(
  arguments,
  value_options = c(
    "manifest", "run-id", "global-dir", "output-dir",
    "p-adjust-method", "alpha"
  ),
  flag_options = "force",
  required = c("manifest", "run-id", "global-dir", "output-dir"),
  defaults = list("p-adjust-method" = "BH", alpha = "0.05", force = FALSE),
  usage = usage
)
project_root <- find_project_root(kda_dir)
result <- run_signature_enrichment_files(
  manifest_path = cli$manifest,
  run_id = cli[["run-id"]],
  global_root = cli[["global-dir"]],
  output_root = cli[["output-dir"]],
  p_adjust_method = cli[["p-adjust-method"]],
  alpha = as_numeric_option(cli$alpha, "alpha", minimum = 0, maximum = 1),
  force = isTRUE(cli$force),
  project_root = project_root
)
cat(
  if (isTRUE(result$reused)) "Reused" else "Completed",
  "enrichment with", nrow(result$enrichment), "candidate drivers and",
  sum(result$enrichment$significant), "significant drivers.\n"
)
