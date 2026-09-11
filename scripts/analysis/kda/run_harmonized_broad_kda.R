#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

parse_cli <- function(args) {
  out <- list(config = "config/harmonized_broad_kda.yml", cohort = NULL)
  i <- 1L
  while (i <= length(args)) {
    if (args[[i]] == "--config" && i < length(args)) {
      out$config <- args[[i + 1L]]
      i <- i + 2L
    } else if (args[[i]] == "--cohort" && i < length(args)) {
      out$cohort <- args[[i + 1L]]
      i <- i + 2L
    } else {
      stop("Unknown or incomplete option: ", args[[i]], call. = FALSE)
    }
  }
  if (!out$cohort %in% c("rosmap", "seaad")) {
    stop("--cohort must be rosmap or seaad", call. = FALSE)
  }
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
  value <- suppressWarnings(system2("shasum", c("-a", "256", path), stdout = TRUE, stderr = TRUE))
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

get_col <- function(x, name, default) {
  if (name %in% names(x)) x[[name]] else rep(default, nrow(x))
}

empty_returns <- function() {
  data.table::data.table(
    schema_version = character(), cohort = character(), kda_run_id = character(),
    contrast_id = character(), broad_cell_type = character(), group_id = character(),
    sex = character(), apoe_group = character(), case_phenotype = character(),
    reference_phenotype = character(), coefficient_direction = character(),
    native_query_mode = character(), query_mode = character(),
    network_release_mode = character(), exploratory_network = logical(),
    key_driver = character(), best_layer = integer(), overlap_count = integer(),
    neighborhood_size = integer(), non_neighborhood_size = integer(),
    signature_size = integer(), fold_enrichment = numeric(), log_p_value = numeric(),
    raw_p_value = numeric(), adjusted_p_value = numeric(), is_signature = logical(),
    is_root_node = logical(), global_key_driver = logical(), overlap_items = character()
  )
}

empty_candidates <- function() {
  data.table::data.table(
    schema_version = character(), cohort = character(), kda_run_id = character(),
    contrast_id = character(), broad_cell_type = character(), group_id = character(),
    sex = character(), apoe_group = character(), case_phenotype = character(),
    reference_phenotype = character(), coefficient_direction = character(),
    native_query_mode = character(), query_mode = character(),
    network_release_mode = character(), exploratory_network = logical(),
    key_driver = character(), best_layer = integer(), overlap_count = integer(),
    neighborhood_size = integer(), non_neighborhood_size = integer(),
    signature_size = integer(), fold_enrichment = numeric(), log_p_value = numeric(),
    raw_p_value = numeric(), adjusted_p_value = numeric(), is_bh_significant = logical(),
    is_signature = logical(), is_root_node = logical(), stock_fkda_return = logical(),
    overlap_items = character()
  )
}

metadata_table <- function(meta, n) {
  data.table::data.table(
    schema_version = rep("harmonized_broad_kda_call_returns_v1", n),
    cohort = rep(meta$cohort, n), kda_run_id = rep(meta$kda_run_id, n),
    contrast_id = rep(meta$contrast_id, n), broad_cell_type = rep(meta$broad_cell_type, n),
    group_id = rep(meta$group_id, n), sex = rep(meta$sex, n),
    apoe_group = rep(meta$apoe_group, n), case_phenotype = rep(meta$case_phenotype, n),
    reference_phenotype = rep(meta$reference_phenotype, n),
    coefficient_direction = rep(meta$coefficient_direction, n),
    native_query_mode = rep(meta$native_query_mode, n),
    query_mode = rep(meta$query_mode, n),
    network_release_mode = rep(meta$network_release_mode, n),
    exploratory_network = rep(as.logical(meta$exploratory_network), n)
  )
}

normalize_stock <- function(result, meta) {
  if (is.null(result) || !nrow(result)) return(empty_returns())
  prefix <- metadata_table(meta, nrow(result))
  data.table::data.table(
    prefix,
    key_driver = as.character(get_col(result, "Keydriver", NA_character_)),
    best_layer = as.integer(get_col(result, "BestLayer", NA_integer_)),
    overlap_count = as.integer(get_col(result, "q", NA_integer_)),
    neighborhood_size = as.integer(get_col(result, "m", NA_integer_)),
    non_neighborhood_size = as.integer(get_col(result, "n", NA_integer_)),
    signature_size = as.integer(get_col(result, "k", NA_integer_)),
    fold_enrichment = as.numeric(get_col(result, "FE", NA_real_)),
    log_p_value = as.numeric(get_col(result, "log.P.Value", NA_real_)),
    raw_p_value = exp(as.numeric(get_col(result, "log.P.Value", NA_real_))),
    adjusted_p_value = as.numeric(get_col(result, "adj.P.Value", NA_real_)),
    is_signature = as.logical(get_col(result, "is.signature", NA)),
    is_root_node = as.logical(get_col(result, "is.root.node", NA)),
    global_key_driver = as.logical(get_col(result, "global.Keydriver", NA)),
    overlap_items = as.character(get_col(result, "Overlap.Items", ""))
  )
}

reconstruct_candidates <- function(net, signature, background_size, n_layers, correction, fdr) {
  layers <- expandToNeighbors(
    seed = signature, net = net, nLayersToExpand = n_layers,
    return.individual.layer = TRUE, directed = FALSE
  )
  if (is.null(layers) || !length(layers)) return(data.table::data.table())
  targets <- layers[[length(layers)]]
  parts <- lapply(targets, function(driver) {
    neighbors <- getNeigobhors(
      node = driver, net = net, nLayer = n_layers,
      collapse = FALSE, directed = TRUE
    )
    if (is.null(neighbors)) return(NULL)
    data.table::rbindlist(lapply(seq_along(neighbors), function(layer) {
      overlap <- neighbors[[layer]][neighbors[[layer]] %in% signature]
      q <- length(overlap)
      m <- length(neighbors[[layer]])
      n <- background_size - m
      k <- length(signature)
      log_p <- phyper(q - 1L, m, n, k, lower.tail = FALSE, log.p = TRUE)
      data.table::data.table(
        key_driver = as.character(driver), best_layer = as.integer(layer),
        overlap_count = as.integer(q), neighborhood_size = as.integer(m),
        non_neighborhood_size = as.integer(n), signature_size = as.integer(k),
        fold_enrichment = round(q * background_size / m / k, 2),
        log_p_value = as.numeric(log_p),
        overlap_items = paste(overlap, collapse = ";")
      )
    }))
  })
  candidate <- data.table::rbindlist(parts, use.names = TRUE, fill = TRUE)
  if (!nrow(candidate)) return(candidate)
  candidate <- candidate[order(candidate$log_p_value), ]
  candidate <- candidate[!duplicated(candidate$key_driver), ]
  candidate[, raw_p_value := exp(log_p_value)]
  candidate[, adjusted_p_value := p.adjust(raw_p_value, method = correction)]
  candidate[, is_bh_significant := adjusted_p_value <= fdr]
  candidate[, is_signature := key_driver %in% signature]
  candidate[, is_root_node := !key_driver %in% net[, 2]]
  candidate
}

decorate_candidates <- function(candidate, stock, meta) {
  if (!nrow(candidate)) return(empty_candidates())
  prefix <- metadata_table(meta, nrow(candidate))
  prefix[, schema_version := "harmonized_broad_kda_candidate_tests_v1"]
  data.table::data.table(
    prefix, candidate,
    stock_fkda_return = candidate$key_driver %in% stock$key_driver
  )
}

max_delta <- function(x, y) {
  if (!length(x)) return(0)
  max(abs(as.numeric(x) - as.numeric(y)), na.rm = TRUE)
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
  config_path <- normalizePath(absolute_path(args$config, root), mustWork = TRUE)
  config <- yaml::read_yaml(config_path)
  cfg <- config$cohorts[[args$cohort]]
  must(!is.null(cfg), paste("Missing cohort configuration:", args$cohort))
  input_dir <- absolute_path(cfg$input_directory, root)
  output_dir <- absolute_path(cfg$output_directory, root)
  must(dir.exists(input_dir), paste("Input release does not exist:", input_dir))
  if (dir.exists(output_dir)) {
    must(length(list.files(output_dir, all.files = TRUE, no.. = TRUE)) == 0L,
         paste("Refusing to overwrite nonempty KDA release:", output_dir))
    unlink(output_dir, recursive = FALSE)
  }

  input_status <- data.table::fread(file.path(input_dir, "status.tsv"))
  must(nrow(input_status) == 1L && input_status$validation_status[[1L]] == "validated_complete",
       paste(cfg$input_phase, "is not validated_complete"))
  artifacts <- data.table::fread(file.path(input_dir, "artifacts.tsv"))
  for (i in seq_len(nrow(artifacts))) {
    path <- absolute_path(artifacts$path[[i]], root)
    must(file.exists(path), paste("Missing frozen input artifact:", path))
    must(file.info(path)$size == artifacts$bytes[[i]] && sha256_file(path) == artifacts$sha256[[i]],
         paste("Frozen input artifact mismatch:", path))
  }
  authority <- data.table::fread(file.path(input_dir, "input_authority.tsv"))
  for (i in seq_len(nrow(authority))) {
    path <- absolute_path(authority$path[[i]], root)
    must(file.exists(path), paste("Missing input authority:", path))
    must(file.info(path)$size == authority$bytes[[i]] && sha256_file(path) == authority$sha256[[i]],
         paste("Input authority mismatch:", path))
  }

  fkda_path <- absolute_path(config$kda$source, root)
  must(sha256_file(fkda_path) == config$kda$source_sha256, "fKDA source checksum mismatch")
  source(fkda_path, local = .GlobalEnv)
  manifest <- data.table::fread(file.path(input_dir, "query_manifest.tsv"))
  queries <- data.table::fread(file.path(input_dir, "query_members.tsv.gz"))
  backgrounds <- data.table::fread(file.path(input_dir, "background_members.tsv.gz"))
  runs <- manifest[execute_kda == TRUE]
  must(nrow(manifest) == 42L, "Query manifest must contain 42 structural slots")
  must(nrow(runs) == as.integer(input_status$eligible_kda_calls[[1L]]),
       "Eligible-call count differs from input status")
  must(!anyDuplicated(manifest$kda_run_id), "KDA run IDs are not unique")

  networks <- list()
  for (cell in unique(runs$broad_cell_type)) {
    row <- runs[broad_cell_type == cell][1L]
    path <- absolute_path(row$network_path[[1L]], root)
    must(sha256_file(path) == row$network_sha256[[1L]], paste("Network checksum mismatch:", cell))
    networks[[cell]] <- read_network(path)
  }

  return_parts <- vector("list", nrow(runs))
  candidate_parts <- vector("list", nrow(runs))
  qc_parts <- vector("list", nrow(runs))
  reconstruction_parts <- vector("list", nrow(runs))
  for (i in seq_len(nrow(runs))) {
    run <- runs[i]
    run_id <- run$kda_run_id[[1L]]
    query <- sort(unique(queries[kda_run_id == run_id & effective_member == TRUE, gene]))
    background <- sort(unique(backgrounds[kda_run_id == run_id, gene]))
    must(length(query) == run$effective_query_genes[[1L]], paste("Query-size mismatch:", run_id))
    must(length(background) == run$effective_background_genes[[1L]], paste("Background-size mismatch:", run_id))
    must(all(query %in% background), paste("Query outside background:", run_id))
    full <- networks[[run$broad_cell_type[[1L]]]]
    induced <- full[from %in% background & to %in% background]
    must(nrow(induced) == run$induced_network_edges[[1L]], paste("Induced-edge mismatch:", run_id))

    meta <- as.list(run[1L])
    meta$cohort <- args$cohort
    signature <- data.frame(Var = query, Group = run_id, stringsAsFactors = FALSE)
    answer <- NULL
    error_message <- ""
    call_start <- proc.time()[[3L]]
    tryCatch(
      capture.output({
        answer <- call_key_drivers(
          net = as.data.frame(induced), signature.df = signature,
          nLayerToTest = as.integer(config$kda$nLayerToTest),
          nLayersToExpand = as.integer(config$kda$nLayersToExpand),
          bg.size = length(background), directed = isTRUE(config$kda$directed),
          reduce.within.nlayer = as.integer(config$kda$reduce_within_nlayer),
          fdr = as.numeric(config$kda$fdr),
          p.correction.method = as.character(config$kda$p_correction_method),
          return.overlap = isTRUE(config$kda$return_overlap)
        )
      }),
      error = function(e) error_message <<- conditionMessage(e)
    )
    elapsed <- proc.time()[[3L]] - call_start
    must(!nzchar(error_message), paste("Stock fKDA failed for", run_id, error_message))
    stock <- normalize_stock(answer, meta)
    reconstructed <- reconstruct_candidates(
      as.data.frame(induced), query, length(background),
      as.integer(config$kda$nLayerToTest), as.character(config$kda$p_correction_method),
      as.numeric(config$kda$fdr)
    )
    candidate <- decorate_candidates(reconstructed, stock, meta)
    reconstructed_significant <- candidate[is_bh_significant == TRUE]
    stock_keys <- sort(stock$key_driver)
    reconstructed_keys <- sort(reconstructed_significant$key_driver)
    keys_match <- identical(stock_keys, reconstructed_keys)
    joined <- merge(
      stock[, .(key_driver, stock_q = adjusted_p_value, stock_log_p = log_p_value,
                 stock_layer = best_layer, stock_overlap = overlap_count,
                 stock_size = neighborhood_size, stock_fe = fold_enrichment)],
      reconstructed_significant[, .(key_driver, reconstructed_q = adjusted_p_value,
                                     reconstructed_log_p = log_p_value,
                                     reconstructed_layer = best_layer,
                                     reconstructed_overlap = overlap_count,
                                     reconstructed_size = neighborhood_size,
                                     reconstructed_fe = fold_enrichment)],
      by = "key_driver", all = TRUE
    )
    q_delta <- if (nrow(joined)) max_delta(joined$stock_q, joined$reconstructed_q) else 0
    logp_delta <- if (nrow(joined)) max_delta(joined$stock_log_p, joined$reconstructed_log_p) else 0
    integer_fields_match <- if (nrow(joined)) all(
      joined$stock_layer == joined$reconstructed_layer &
      joined$stock_overlap == joined$reconstructed_overlap &
      joined$stock_size == joined$reconstructed_size &
      joined$stock_fe == joined$reconstructed_fe
    ) else TRUE
    reconstruction_pass <- keys_match && integer_fields_match && q_delta <= 1e-12 && logp_delta <= 1e-12
    terminal <- if (nrow(stock)) "completed_significant" else "completed_no_significant"
    return_parts[[i]] <- stock
    candidate_parts[[i]] <- candidate
    qc_parts[[i]] <- data.table::data.table(
      schema_version = "harmonized_broad_kda_run_qc_v1", cohort = args$cohort,
      kda_run_id = run_id, contrast_id = run$contrast_id[[1L]],
      broad_cell_type = run$broad_cell_type[[1L]], group_id = run$group_id[[1L]],
      query_mode = run$query_mode[[1L]],
      network_release_mode = run$network_release_mode[[1L]],
      exploratory_network = as.logical(run$exploratory_network[[1L]]),
      effective_query_genes = length(query), effective_background_genes = length(background),
      induced_network_edges = nrow(induced), candidate_tests = nrow(candidate),
      significant_key_drivers = nrow(stock), elapsed_seconds = elapsed,
      terminal_status = terminal, message = ""
    )
    reconstruction_parts[[i]] <- data.table::data.table(
      schema_version = "harmonized_broad_kda_reconstruction_checks_v1",
      cohort = args$cohort, kda_run_id = run_id,
      stock_return_rows = nrow(stock), reconstructed_significant_rows = nrow(reconstructed_significant),
      driver_keys_match = keys_match, integer_statistics_match = integer_fields_match,
      maximum_adjusted_p_delta = q_delta, maximum_log_p_delta = logp_delta,
      passed = reconstruction_pass
    )
    cat(sprintf(
      "%s call %d/%d %s: %s, candidates=%d, significant=%d, %.2fs\n",
      cfg$run_phase, i, nrow(runs), run_id, terminal, nrow(candidate), nrow(stock), elapsed
    ))
  }

  returns <- if (length(return_parts)) data.table::rbindlist(return_parts, use.names = TRUE, fill = TRUE) else empty_returns()
  candidates <- if (length(candidate_parts)) data.table::rbindlist(candidate_parts, use.names = TRUE, fill = TRUE) else empty_candidates()
  qc <- if (length(qc_parts)) data.table::rbindlist(qc_parts, use.names = TRUE, fill = TRUE) else data.table::data.table()
  reconstruction <- if (length(reconstruction_parts)) data.table::rbindlist(reconstruction_parts, use.names = TRUE, fill = TRUE) else data.table::data.table()
  significant <- data.table::copy(returns[adjusted_p_value <= as.numeric(config$kda$fdr)])
  driver_units <- significant[, .(
    schema_version = "harmonized_broad_kda_driver_units_v1", cohort, key_driver,
    group_id, sex, apoe_group, broad_cell_type, case_phenotype, reference_phenotype,
    coefficient_direction, native_query_mode, query_mode, kda_run_id,
    effective_query_genes = signature_size, best_layer, overlap_count,
    neighborhood_size, fold_enrichment, raw_p_value, adjusted_p_value,
    global_key_driver, network_release_mode, exploratory_network, overlap_items
  )]

  run_manifest <- data.table::copy(manifest)
  data.table::setnames(run_manifest, "terminal_status", "input_terminal_status")
  run_manifest[, `:=`(kda_terminal_status = input_terminal_status, significant_driver_count = 0L)]
  if (nrow(qc)) {
    qc_status <- setNames(qc$terminal_status, qc$kda_run_id)
    qc_counts <- setNames(qc$significant_key_drivers, qc$kda_run_id)
    active <- run_manifest$execute_kda == TRUE
    run_manifest[active, kda_terminal_status := unname(qc_status[kda_run_id])]
    run_manifest[active, significant_driver_count := as.integer(unname(qc_counts[kda_run_id]))]
  }

  checks <- data.table::data.table(
    schema_version = "harmonized_broad_kda_run_checks_v1", cohort = args$cohort,
    check = c(
      "input_release_validated", "structural_slot_count", "eligible_call_count",
      "all_calls_completed", "all_returned_q_values_reconstructed",
      "return_keys_unique", "significant_return_identity", "terminal_state_complete",
      "seaad_vasculature_exploratory"
    ),
    passed = c(
      TRUE, nrow(run_manifest) == 42L, nrow(qc) == nrow(runs),
      nrow(qc) == 0L || all(grepl("^completed_", qc$terminal_status)),
      nrow(reconstruction) == nrow(runs) && (nrow(reconstruction) == 0L || all(reconstruction$passed)),
      !anyDuplicated(returns[, .(kda_run_id, key_driver)]),
      nrow(significant) == nrow(returns),
      !any(is.na(run_manifest$kda_terminal_status) | !nzchar(run_manifest$kda_terminal_status)),
      args$cohort != "seaad" || all(run_manifest[broad_cell_type == "Vasculature_cells"]$exploratory_network)
    ),
    observed = c(
      input_status$validation_status[[1L]], nrow(run_manifest), nrow(qc),
      sum(grepl("^completed_", qc$terminal_status)), sum(reconstruction$passed),
      nrow(returns) - data.table::uniqueN(returns[, .(kda_run_id, key_driver)]), nrow(significant),
      sum(!is.na(run_manifest$kda_terminal_status) & nzchar(run_manifest$kda_terminal_status)),
      sum(run_manifest[broad_cell_type == "Vasculature_cells"]$exploratory_network)
    ),
    expected = c(
      "validated_complete", 42L, nrow(runs), nrow(runs), nrow(runs), 0L,
      nrow(returns), 42L, if (args$cohort == "seaad") 6L else 0L
    )
  )
  must(all(checks$passed), paste("Blocking KDA checks failed:", paste(checks[passed == FALSE]$check, collapse = ", ")))

  stage <- paste0(output_dir, ".tmp.", Sys.getpid())
  if (dir.exists(stage)) unlink(stage, recursive = TRUE)
  dir.create(stage, recursive = TRUE, showWarnings = FALSE)
  driver_name <- paste0(args$cohort, "_broad_driver_units.tsv")
  products <- list(
    "run_manifest.tsv" = run_manifest,
    "call_returns.tsv.gz" = returns,
    "candidate_tests.tsv.gz" = candidates,
    "significant_returns.tsv" = significant,
    "run_reconstruction_checks.tsv" = reconstruction,
    "run_qc.tsv" = qc,
    "checks.tsv" = checks
  )
  products[[driver_name]] <- driver_units
  for (name in names(products)) atomic_fwrite(products[[name]], file.path(stage, name))
  artifact_rows <- vector("list", length(products))
  for (i in seq_along(products)) {
    name <- names(products)[[i]]
    path <- file.path(stage, name)
    artifact_rows[[i]] <- data.table::data.table(
      schema_version = "harmonized_broad_kda_run_artifacts_v1", artifact_order = i,
      path = relative_path(file.path(output_dir, name), root), rows = nrow(products[[name]]),
      bytes = file.info(path)$size, sha256 = sha256_file(path)
    )
  }
  atomic_fwrite(data.table::rbindlist(artifact_rows), file.path(stage, "artifacts.tsv"))
  status <- data.table::data.table(
    schema_version = "harmonized_broad_kda_run_status_v1", phase = cfg$run_phase,
    cohort = args$cohort, validation_status = "validated_complete", failed_checks = 0L,
    structural_query_slots = nrow(run_manifest), eligible_kda_calls = nrow(runs),
    completed_significant_calls = sum(qc$terminal_status == "completed_significant"),
    completed_no_significant_calls = sum(qc$terminal_status == "completed_no_significant"),
    candidate_test_rows = nrow(candidates), significant_return_rows = nrow(significant),
    unique_key_drivers = data.table::uniqueN(significant$key_driver),
    exploratory_executed_calls = sum(qc$exploratory_network),
    config_sha256 = sha256_file(config_path), fkda_source_sha256 = sha256_file(fkda_path),
    R_version = R.version.string, data_table_version = as.character(utils::packageVersion("data.table")),
    started_at_utc = started, completed_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE)
  )
  atomic_fwrite(status, file.path(stage, "status.tsv"))
  must(file.rename(stage, output_dir), paste("Could not publish KDA release:", output_dir))
  cat(sprintf(
    "%s validated_complete: %s; calls=%d; significant_calls=%d; driver_rows=%d\n",
    cfg$run_phase, relative_path(output_dir, root), nrow(runs),
    status$completed_significant_calls[[1L]], nrow(significant)
  ))
}

main()
