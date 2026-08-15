#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_phase18_cli <- function(args) {
  out <- list(
    config = NULL,
    execution_config = NULL,
    task_mode = "key_driver_selection",
    phase18_config = "config/phase18_key_driver_selection.yml",
    phase12_dir = NULL,
    output_dir = NULL
  )
  allowed <- c(
    "--config", "--execution-config", "--task-mode", "--phase18-config",
    "--phase12-dir", "--output-dir"
  )
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/18_run_key_driver_selection.R ",
        "[--config PIPELINE_CONFIG] [--execution-config EXECUTION_CONFIG] ",
        "[--task-mode key_driver_selection] ",
        "[--phase18-config FILE] [--phase12-dir DIR] [--output-dir DIR]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% allowed || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    out[[gsub("-", "_", sub("^--", "", key))]] <- args[[i + 1L]]
    i <- i + 2L
  }
  if (!identical(out$task_mode, "key_driver_selection")) {
    stop("--task-mode must be key_driver_selection", call. = FALSE)
  }
  out
}

if (sys.nframe() == 0L) {
  args <- parse_phase18_cli(commandArgs(trailingOnly = TRUE))
  root <- normalizePath(getwd(), mustWork = TRUE)
  python_script <- file.path(root, "scripts", "18_run_key_driver_selection.py")
  if (!file.exists(python_script)) {
    stop("Missing Phase 18 Python core: ", python_script, call. = FALSE)
  }
  command <- c(
    python_script,
    "--config", args$phase18_config
  )
  if (!is.null(args$phase12_dir)) {
    command <- c(command, "--phase12-dir", args$phase12_dir)
  }
  if (!is.null(args$output_dir)) {
    command <- c(command, "--output-dir", args$output_dir)
  }
  status <- system2("python3", command)
  quit(status = status)
}
