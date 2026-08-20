#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL)
  i <- 1L
  while (i <= length(args)) {
    if (args[[i]] %in% c("--help", "-h")) {
      cat("Usage: Rscript scripts/validation_human/10_run_seaad_kda.R --config FILE\n")
      quit(status = 0L)
    }
    if (!identical(args[[i]], "--config") || i == length(args)) {
      stop("Unknown option or missing value: ", args[[i]], call. = FALSE)
    }
    out$config <- args[[i + 1L]]
    i <- i + 2L
  }
  if (is.null(out$config)) stop("--config is required", call. = FALSE)
  out
}

must <- function(condition, message) {
  if (length(condition) != 1L || is.na(condition) || !condition) {
    stop(message, call. = FALSE)
  }
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

relative_path <- function(path, root) {
  path <- normalizePath(path, mustWork = FALSE)
  root <- normalizePath(root, mustWork = TRUE)
  prefix <- paste0(root, .Platform$file.sep)
  if (startsWith(path, prefix)) substring(path, nchar(prefix) + 1L) else path
}

sha256_file <- function(path) {
  value <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(value, "status")
  must(is.null(status) || status == 0L, paste("Could not hash", path))
  strsplit(value[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

atomic_fwrite <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  compressed <- grepl("[.]gz$", path)
  tmp <- file.path(dirname(path), paste0(".", basename(path), ".tmp.", Sys.getpid()))
  data.table::fwrite(x, tmp, sep = "\t", quote = FALSE, na = "NA", logical01 = FALSE)
  if (compressed) {
    status <- system2("gzip", c("-n", "-f", tmp))
    must(status == 0L && file.exists(paste0(tmp, ".gz")), paste("Could not gzip", path))
    tmp <- paste0(tmp, ".gz")
  }
  must(file.rename(tmp, path), paste("Could not publish", path))
}

read_network <- function(path) {
  net <- data.table::fread(
    path, header = FALSE, select = 1:2, col.names = c("from", "to")
  )
  unique(net[
    !is.na(from) & !is.na(to) & nzchar(from) & nzchar(to) & from != to
  ])
}

empty_results <- function() {
  data.table::data.table(
    schema_version = character(),
    kda_run_id = character(),
    fine_cell_type = character(),
    broad_network = character(),
    signature_group = character(),
    signature_direction = character(),
    key_driver = character(),
    best_layer = integer(),
    overlap_count = integer(),
    neighborhood_size = integer(),
    non_neighborhood_size = integer(),
    signature_size = integer(),
    fold_enrichment = numeric(),
    log_p_value = numeric(),
    adjusted_p_value = numeric(),
    is_signature = logical(),
    is_root_node = logical(),
    global_key_driver = logical(),
    overlap_items = character()
  )
}

normalize_result <- function(x, meta) {
  if (is.null(x) || !nrow(x)) return(empty_results())
  get_column <- function(name, default) {
    if (name %in% names(x)) x[[name]] else rep(default, nrow(x))
  }
  data.table::data.table(
    schema_version = "seaad_kda_significant_returns_v1",
    kda_run_id = meta$kda_run_id,
    fine_cell_type = meta$fine_cell_type,
    broad_network = meta$broad_network,
    signature_group = meta$signature_group,
    signature_direction = meta$signature_direction,
    key_driver = as.character(get_column("Keydriver", NA_character_)),
    best_layer = as.integer(get_column("BestLayer", NA_integer_)),
    overlap_count = as.integer(get_column("q", NA_integer_)),
    neighborhood_size = as.integer(get_column("m", NA_integer_)),
    non_neighborhood_size = as.integer(get_column("n", NA_integer_)),
    signature_size = as.integer(get_column("k", NA_integer_)),
    fold_enrichment = as.numeric(get_column("FE", NA_real_)),
    log_p_value = as.numeric(get_column("log.P.Value", NA_real_)),
    adjusted_p_value = as.numeric(get_column("adj.P.Value", NA_real_)),
    is_signature = as.logical(get_column("is.signature", NA)),
    is_root_node = as.logical(get_column("is.root.node", NA)),
    global_key_driver = as.logical(get_column("global.Keydriver", NA)),
    overlap_items = as.character(get_column("Overlap.Items", ""))
  )
}

main <- function() {
  for (package in c("data.table", "yaml")) {
    if (!requireNamespace(package, quietly = TRUE)) {
      stop("Package '", package, "' is required", call. = FALSE)
    }
  }
  args <- parse_cli(commandArgs(trailingOnly = TRUE))
  started <- format(Sys.time(), tz = "UTC", usetz = TRUE)
  root <- normalizePath(getwd(), mustWork = TRUE)
  config_path <- absolute_path(args$config, root)
  must(file.exists(config_path), paste("Config does not exist:", config_path))
  config <- yaml::read_yaml(config_path)
  cfg <- config$vh10
  phase12_item <- cfg$input_authority$phase12_config
  phase12_path <- absolute_path(phase12_item$path, root)
  must(
    identical(sha256_file(phase12_path), as.character(phase12_item$sha256)),
    "Phase 12 config checksum mismatch"
  )
  phase12 <- yaml::read_yaml(phase12_path)
  fkda_item <- cfg$input_authority$fkda_source
  fkda_path <- absolute_path(fkda_item$path, root)
  must(
    identical(sha256_file(fkda_path), as.character(fkda_item$sha256)),
    "fKDA source checksum mismatch"
  )
  source(fkda_path, local = environment())

  output_root <- absolute_path(config$output_root, root)
  phase_root <- file.path(output_root, cfg$output_directory)
  input_dir <- file.path(phase_root, "10a_inputs")
  output_dir <- file.path(phase_root, "10b_kda")
  status <- data.table::fread(file.path(input_dir, "status.tsv"))
  must(
    nrow(status) == 1L && status$validation_status[[1L]] == "validated_complete",
    "VH10A is not validated_complete"
  )
  artifacts <- data.table::fread(file.path(input_dir, "artifacts.tsv"))
  for (i in seq_len(nrow(artifacts))) {
    artifact_path <- absolute_path(artifacts$path[[i]], root)
    must(file.exists(artifact_path), paste("Missing VH10A artifact:", artifact_path))
    must(
      file.info(artifact_path)$size == artifacts$bytes[[i]]
      && sha256_file(artifact_path) == artifacts$digest_value[[i]],
      paste("VH10A artifact mismatch:", artifact_path)
    )
  }

  manifest <- data.table::fread(file.path(input_dir, "seaad_kda_run_manifest.tsv"))
  runs <- manifest[
    terminal_status %in% c("eligible_small_query", "eligible_phase18_sized")
  ]
  expected_calls <- as.integer(cfg$analysis$expected$active_kda_calls)
  must(nrow(runs) == expected_calls, paste("Expected", expected_calls, "active calls"))
  must(!anyDuplicated(runs$kda_run_id), "Active KDA run IDs are not unique")
  signatures <- data.table::fread(
    file.path(input_dir, "seaad_kda_signature_members.tsv.gz")
  )
  backgrounds <- data.table::fread(
    file.path(input_dir, "seaad_kda_background_members.tsv.gz")
  )

  networks <- list()
  for (network in unique(runs$broad_network)) {
    item <- phase12$networks[[network]]
    must(!is.null(item), paste("Network is not configured:", network))
    path <- absolute_path(item$path, root)
    must(identical(sha256_file(path), as.character(item$sha256)),
         paste("Network checksum mismatch:", network))
    networks[[network]] <- read_network(path)
  }

  result_parts <- vector("list", nrow(runs))
  qc_parts <- vector("list", nrow(runs))
  for (i in seq_len(nrow(runs))) {
    run <- runs[i]
    run_id <- run$kda_run_id[[1L]]
    query <- sort(unique(signatures[
      kda_run_id == run_id & effective_member == TRUE, gene
    ]))
    background <- sort(unique(backgrounds[kda_run_id == run_id, gene]))
    must(length(query) == run$effective_query_genes[[1L]],
         paste("Query-size mismatch:", run_id))
    must(length(background) == run$effective_background_genes[[1L]],
         paste("Background-size mismatch:", run_id))
    must(all(query %in% background), paste("Query outside background:", run_id))
    full <- networks[[run$broad_network[[1L]]]]
    induced <- full[from %in% background & to %in% background]
    must(nrow(induced) == run$induced_network_edges[[1L]],
         paste("Induced-edge mismatch:", run_id))
    sig <- data.frame(Var = query, Group = run_id, stringsAsFactors = FALSE)
    answer <- NULL
    error_message <- ""
    call_start <- proc.time()[[3L]]
    tryCatch(
      capture.output({
        answer <- call_key_drivers(
          net = as.data.frame(induced),
          signature.df = sig,
          nLayerToTest = as.integer(phase12$kda$nLayerToTest),
          nLayersToExpand = as.integer(phase12$kda$nLayersToExpand),
          bg.size = length(background),
          directed = isTRUE(phase12$kda$directed),
          reduce.within.nlayer = as.integer(phase12$kda$reduce_within_nlayer),
          fdr = as.numeric(phase12$kda$fdr),
          p.correction.method = as.character(phase12$kda$p_correction_method),
          return.overlap = isTRUE(phase12$kda$return_overlap)
        )
      }),
      error = function(e) error_message <<- conditionMessage(e)
    )
    elapsed <- proc.time()[[3L]] - call_start
    normalized <- normalize_result(
      answer,
      list(
        kda_run_id = run_id,
        fine_cell_type = run$fine_cell_type[[1L]],
        broad_network = run$broad_network[[1L]],
        signature_group = run$signature_group[[1L]],
        signature_direction = run$signature_direction[[1L]]
      )
    )
    if (nrow(normalized) && any(normalized$overlap_count < 1L)) {
      error_message <- "fKDA returned a significant result with zero overlap"
    }
    terminal <- if (nzchar(error_message)) {
      "failed"
    } else if (nrow(normalized)) {
      "completed_significant"
    } else {
      "completed_no_significant"
    }
    result_parts[[i]] <- normalized
    qc_parts[[i]] <- data.table::data.table(
      schema_version = "seaad_kda_run_qc_v1",
      kda_run_id = run_id,
      broad_network = run$broad_network[[1L]],
      fine_cell_type = run$fine_cell_type[[1L]],
      signature_group = run$signature_group[[1L]],
      signature_direction = run$signature_direction[[1L]],
      effective_query_genes = length(query),
      effective_background_genes = length(background),
      induced_network_edges = nrow(induced),
      significant_key_drivers = nrow(normalized),
      elapsed_seconds = elapsed,
      terminal_status = terminal,
      message = error_message
    )
    cat(sprintf(
      "VH10B call %d/%d %s status=%s significant=%d elapsed=%.2fs\n",
      i, nrow(runs), run_id, terminal, nrow(normalized), elapsed
    ))
    if (identical(terminal, "failed")) {
      stop("KDA failed for ", run_id, ": ", error_message, call. = FALSE)
    }
  }
  results <- data.table::rbindlist(result_parts, use.names = TRUE, fill = TRUE)
  qc <- data.table::rbindlist(qc_parts, use.names = TRUE, fill = TRUE)
  must(nrow(qc) == expected_calls, "Run QC row count mismatch")
  must(all(grepl("^completed_", qc$terminal_status)), "At least one KDA call failed")
  must(!anyDuplicated(results[, .(kda_run_id, key_driver)]),
       "Significant returns contain duplicate run/gene keys")

  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  significant_path <- file.path(output_dir, "seaad_kda_significant_returns.tsv")
  qc_path <- file.path(output_dir, "r_run_qc.tsv")
  worker_path <- file.path(output_dir, "r_worker_status.tsv")
  atomic_fwrite(results, significant_path)
  atomic_fwrite(qc, qc_path)
  worker <- data.table::data.table(
    schema_version = "seaad_kda_r_worker_status_v1",
    task_status = "worker_complete",
    started_at_utc = started,
    completed_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
    active_kda_calls = nrow(qc),
    completed_significant_calls = sum(qc$terminal_status == "completed_significant"),
    completed_no_significant_calls = sum(qc$terminal_status == "completed_no_significant"),
    significant_return_rows = nrow(results),
    failed_calls = sum(qc$terminal_status == "failed"),
    config_sha256 = sha256_file(config_path),
    fkda_source_sha256 = sha256_file(fkda_path)
  )
  atomic_fwrite(worker, worker_path)
  cat("VH10B R worker_complete:", output_dir, "\n")
}

main()
