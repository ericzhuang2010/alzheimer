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
  "  Rscript scripts/analysis/kda/run_kda_pipeline.R \\",
  "    --manifest PATH --output-dir DIR [--run-id ID] [options]",
  "",
  "Without --run-id, all eligible manifest rows run serially and combined tables",
  "are published. Per-run jobs do not write shared combined tables; after they",
  "finish, invoke this command with --combine-only.",
  "",
  "Options:",
  "  --run-id ID                    Run one manifest row",
  "  --driver-search-layers N       Default: 6",
  "  --enrichment-layers N          Default: 3",
  "  --include-driver               Include driver in downstream neighborhood",
  "  --no-boost-hubs                Disable Wang's hub boost",
  "  --p-adjust-method NAME         Default: BH",
  "  --alpha NUMBER                 Default: 0.05",
  "  --combine-only                 Only combine completed enrichment outputs",
  "  --force                        Replace incompatible/partial known outputs",
  "  --help, -h                     Show this help",
  sep = "\n"
)

combine_completed_enrichment <- function(enrichment_root, combined_root) {
  require_kda_packages()
  directories <- list.dirs(enrichment_root, recursive = FALSE, full.names = TRUE)
  tables <- list()
  for (directory in sort(directories, method = "radix")) {
    files <- enrichment_output_files(directory)
    run_manifest <- read_json_manifest(files$manifest)
    if (is.null(run_manifest) ||
        !identical(as.character(run_manifest$status %||% ""), "complete")) {
      next
    }
    if (!file.exists(files$enrichment)) {
      kda_abort("Completed enrichment directory lacks driver_enrichment.tsv: %s", directory)
    }
    tables[[basename(directory)]] <- read_tsv(files$enrichment)
  }
  if (!length(tables)) {
    kda_abort("No completed enrichment outputs were found below: %s", enrichment_root)
  }
  combined <- data.table::rbindlist(tables, use.names = TRUE, fill = FALSE)
  data.table::setorder(combined, run_id, q_value, p_value, driver, na.last = TRUE)
  significant <- combined[significant == TRUE]
  atomic_write_tsv(
    combined,
    file.path(combined_root, "all_driver_enrichment.tsv.gz")
  )
  atomic_write_tsv(
    significant,
    file.path(combined_root, "significant_drivers.tsv")
  )
  cat(
    "Combined", length(tables), "completed runs into", nrow(combined),
    "driver rows and", nrow(significant), "significant rows.\n"
  )
  invisible(list(all = combined, significant = significant))
}

arguments <- commandArgs(trailingOnly = TRUE)
if ("-h" %in% arguments) {
  cat(usage, "\n")
  quit(save = "no", status = 0L)
}
cli <- parse_kda_cli(
  arguments,
  value_options = c(
    "manifest", "output-dir", "run-id", "driver-search-layers",
    "enrichment-layers", "p-adjust-method", "alpha"
  ),
  flag_options = c(
    "include-driver", "no-boost-hubs", "combine-only", "force"
  ),
  required = c("manifest", "output-dir"),
  defaults = list(
    "driver-search-layers" = "6",
    "enrichment-layers" = "3",
    "p-adjust-method" = "BH",
    alpha = "0.05",
    "include-driver" = FALSE,
    "no-boost-hubs" = FALSE,
    "combine-only" = FALSE,
    force = FALSE
  ),
  usage = usage
)

project_root <- find_project_root(kda_dir)
output_root <- resolve_project_path(cli[["output-dir"]], project_root)
global_root <- file.path(output_root, "global")
enrichment_root <- file.path(output_root, "enrichment")
combined_root <- file.path(output_root, "combined")

if (isTRUE(cli[["combine-only"]])) {
  combine_completed_enrichment(enrichment_root, combined_root)
  quit(save = "no", status = 0L)
}

manifest_path <- resolve_project_path(cli$manifest, project_root)
manifest <- read_run_manifest(manifest_path)
single_run <- !is.null(cli[["run-id"]])
if (single_run) {
  manifest <- manifest[run_id == cli[["run-id"]]]
  if (nrow(manifest) != 1L) {
    kda_abort("run_id '%s' was not found exactly once.", cli[["run-id"]])
  }
  if ("eligible" %in% names(manifest) && !isTRUE(as.logical(manifest$eligible[[1L]]))) {
    kda_abort(
      "run_id '%s' is ineligible: %s",
      cli[["run-id"]],
      manifest_row_value(manifest, "skip_reason", "ineligible")
    )
  }
} else if ("eligible" %in% names(manifest)) {
  ineligible_count <- sum(!as.logical(manifest$eligible))
  if (ineligible_count) {
    kda_message("Skipping %d ineligible manifest rows.", ineligible_count)
  }
  manifest <- manifest[as.logical(eligible)]
}
if (!nrow(manifest)) kda_abort("No eligible KDA runs were selected.")

driver_search_layers <- as_integer_option(
  cli[["driver-search-layers"]], "driver-search-layers", 1L
)
enrichment_layers <- as_integer_option(
  cli[["enrichment-layers"]], "enrichment-layers", 1L
)
alpha <- as_numeric_option(cli$alpha, "alpha", 0, 1)

network_rows <- manifest[!duplicated(network_id)]
for (row_index in seq_len(nrow(network_rows))) {
  row <- network_rows[row_index]
  kda_message("Global KDA: %s", row$network_id[[1L]])
  run_global_kda_files(
    network_id = row$network_id[[1L]],
    network_path = row$network_path[[1L]],
    output_root = global_root,
    driver_search_layers = driver_search_layers,
    enrichment_layers = enrichment_layers,
    include_driver_in_neighborhood = isTRUE(cli[["include-driver"]]),
    boost_hubs = !isTRUE(cli[["no-boost-hubs"]]),
    force = isTRUE(cli$force),
    project_root = project_root
  )
}

for (row_index in seq_len(nrow(manifest))) {
  run_id <- manifest$run_id[[row_index]]
  kda_message("Signature enrichment: %s", run_id)
  run_signature_enrichment_files(
    manifest_path = manifest_path,
    run_id = run_id,
    global_root = global_root,
    output_root = enrichment_root,
    p_adjust_method = cli[["p-adjust-method"]],
    alpha = alpha,
    force = isTRUE(cli$force),
    project_root = project_root
  )
}

if (single_run) {
  cat(
    "Completed one run. Shared combined tables were not changed; after all",
    "per-run jobs finish, run this command again with --combine-only.\n"
  )
} else {
  combine_completed_enrichment(enrichment_root, combined_root)
}
