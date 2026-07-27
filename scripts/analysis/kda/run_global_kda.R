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
  "  Rscript scripts/analysis/kda/run_global_kda.R \\",
  "    --network-id ID --network PATH --output-dir DIR [options]",
  "",
  "Options:",
  "  --driver-search-layers N       Default: 6",
  "  --enrichment-layers N          Default: 3",
  "  --include-driver               Include the driver in its neighborhood",
  "  --no-boost-hubs                Disable Wang's hub boost",
  "  --force                        Replace incompatible/partial known outputs",
  "  --help, -h                     Show this help",
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
    "network-id", "network", "output-dir",
    "driver-search-layers", "enrichment-layers"
  ),
  flag_options = c("include-driver", "no-boost-hubs", "force"),
  required = c("network-id", "network", "output-dir"),
  defaults = list(
    "driver-search-layers" = "6",
    "enrichment-layers" = "3",
    "include-driver" = FALSE,
    "no-boost-hubs" = FALSE,
    force = FALSE
  ),
  usage = usage
)
project_root <- find_project_root(kda_dir)
result <- run_global_kda_files(
  network_id = cli[["network-id"]],
  network_path = cli$network,
  output_root = cli[["output-dir"]],
  driver_search_layers = as_integer_option(
    cli[["driver-search-layers"]], "driver-search-layers", 1L
  ),
  enrichment_layers = as_integer_option(
    cli[["enrichment-layers"]], "enrichment-layers", 1L
  ),
  include_driver_in_neighborhood = isTRUE(cli[["include-driver"]]),
  boost_hubs = !isTRUE(cli[["no-boost-hubs"]]),
  force = isTRUE(cli$force),
  project_root = project_root
)
cat(
  if (isTRUE(result$reused)) "Reused" else "Completed",
  "global KDA with", nrow(result$global_drivers), "candidate drivers.\n"
)
