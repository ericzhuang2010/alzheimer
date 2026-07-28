#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(config = NULL, execution_config = NULL, task_mode = NULL)
  value_options <- c("--config", "--execution-config", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/12_run_kda.R --config FILE ",
        "--execution-config FILE --task-mode kda\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    name <- gsub("-", "_", sub("^--", "", key))
    out[[name]] <- args[[i + 1L]]
    i <- i + 2L
  }
  missing <- names(out)[vapply(out, is.null, logical(1))]
  if (length(missing)) {
    stop("Missing required options: ", paste(missing, collapse = ", "), call. = FALSE)
  }
  if (!identical(out$task_mode, "kda")) stop("--task-mode must be kda", call. = FALSE)
  out
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

must <- function(condition, message) {
  if (length(condition) != 1L || is.na(condition) || !condition) {
    stop(message, call. = FALSE)
  }
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  value <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(value, "status")
  if (!is.null(status) && status != 0L) return(NA_character_)
  strsplit(value[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

git_revision <- function(root) {
  value <- suppressWarnings(system2(
    "git", c("-C", root, "rev-parse", "HEAD"), stdout = TRUE, stderr = TRUE
  ))
  status <- attr(value, "status")
  if (!is.null(status) && status != 0L) NA_character_ else value[[1L]]
}

peak_ram_gib <- function() {
  path <- "/proc/self/status"
  if (!file.exists(path)) return(NA_real_)
  line <- grep("^VmHWM:", readLines(path, warn = FALSE), value = TRUE)
  if (!length(line)) return(NA_real_)
  as.numeric(sub("^VmHWM:[[:space:]]+([0-9]+).*$", "\\1", line[[1L]])) / 1024^2
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

is_dag <- function(net) {
  if (!nrow(net)) return(FALSE)
  nodes <- unique(c(net[[1L]], net[[2L]]))
  indegree <- setNames(integer(length(nodes)), nodes)
  children <- split(net[[2L]], net[[1L]])
  counts <- table(net[[2L]])
  indegree[names(counts)] <- as.integer(counts)
  queue <- names(indegree)[indegree == 0L]
  visited <- 0L
  while (length(queue)) {
    node <- queue[[1L]]
    queue <- queue[-1L]
    visited <- visited + 1L
    for (child in children[[node]] %||% character()) {
      indegree[[child]] <- indegree[[child]] - 1L
      if (indegree[[child]] == 0L) queue <- c(queue, child)
    }
  }
  visited == length(nodes)
}

fine_to_network <- function(fine) {
  if (grepl("^Ast", fine)) return("Astrocytes")
  if (grepl("^Exc", fine)) return("Excitatory_neurons")
  if (grepl("^Inh", fine)) return("Inhibitory_neurons")
  if (identical(fine, "OPC")) return("OPCs")
  if (grepl("^Oli", fine)) return("Oligodendrocytes")
  if (fine %in% c("End", "Per", "SMC") || grepl("^Fib", fine)) return("Vasculature_cells")
  if (identical(fine, "CAMs")) return("CAMs")
  if (grepl("^Mic", fine)) return("Microglia")
  if (identical(fine, "T cells")) return("T_cells")
  NA_character_
}

group_id_from <- function(sex, apoe) {
  prefix <- ifelse(sex == "Female", "F", ifelse(sex == "Male", "M", NA_character_))
  paste0(prefix, "_", apoe)
}

safe_id <- function(...) {
  gsub("[^A-Za-z0-9]+", "_", paste(..., sep = "__"))
}

read_network <- function(path) {
  net <- data.table::fread(path, header = FALSE, select = 1:2, col.names = c("from", "to"))
  net <- unique(net[!is.na(from) & !is.na(to) & nzchar(from) & nzchar(to) & from != to])
  as.data.frame(net)
}

empty_results <- function() {
  data.table::data.table(
    schema_version = character(), kda_run_id = character(), analysis_tier = character(),
    fine_cell_type = character(), broad_network = character(), signature_group = character(),
    signature_direction = character(), key_driver = character(), best_layer = integer(),
    overlap_count = integer(), neighborhood_size = integer(), non_neighborhood_size = integer(),
    signature_size = integer(), fold_enrichment = numeric(), log_p_value = numeric(),
    adjusted_p_value = numeric(), is_signature = logical(), is_root_node = logical(),
    global_key_driver = logical(), overlap_items = character()
  )
}

normalize_kda_result <- function(x, meta, schema) {
  if (is.null(x) || !nrow(x)) return(empty_results())
  get_column <- function(name, default) {
    if (name %in% names(x)) x[[name]] else rep(default, nrow(x))
  }
  data.table::data.table(
    schema_version = schema,
    kda_run_id = meta$kda_run_id,
    analysis_tier = meta$analysis_tier,
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

phase12_main <- function(cli_args = commandArgs(trailingOnly = TRUE)) {
  args <- parse_cli(cli_args)
  for (package in c("data.table", "yaml")) {
    if (!requireNamespace(package, quietly = TRUE)) {
      stop("Package '", package, "' is required", call. = FALSE)
    }
  }
  start_time <- Sys.time()
  project_root <- normalizePath(getwd(), mustWork = TRUE)
  config_path <- absolute_path(args$config, project_root)
  execution_path <- absolute_path(args$execution_config, project_root)
  must(file.exists(config_path), paste("Project config does not exist:", config_path))
  must(file.exists(execution_path), paste("Execution config does not exist:", execution_path))
  config <- yaml::read_yaml(config_path)
  execution_config <- yaml::read_yaml(execution_path)
  phase12_path <- absolute_path(config$project$phase12_kda_config %||% "", project_root)
  must(file.exists(phase12_path), paste("Phase 12 config does not exist:", phase12_path))
  phase12 <- yaml::read_yaml(phase12_path)
  must(identical(phase12$schema_version, "phase12_kda_config_v1"), "Unexpected Phase 12 config schema")

  execution <- execution_config$execution
  stage_name <- as.character(execution$execution_stage)
  must(stage_name %in% c("local_pilot", "minerva_production"), "KDA requires local_pilot or minerva_production")
  expected <- phase12$expected[[stage_name]]
  output_root <- absolute_path(config$outputs$root, project_root)
  phase08_root <- file.path(output_root, "08_mast")
  phase09_root <- file.path(output_root, "09_annotate_genes")
  final_root <- file.path(output_root, phase12$outputs$directory)
  temp_parent <- absolute_path(execution$temp_dir %||% file.path(output_root, "tmp"), project_root)
  staging_root <- file.path(temp_parent, paste0("phase12_kda_", Sys.getpid()))
  dir.create(staging_root, recursive = TRUE, showWarnings = FALSE)
  on.exit(unlink(staging_root, recursive = TRUE, force = TRUE), add = TRUE)

  output_names <- unlist(phase12$outputs$files, use.names = FALSE)
  must(length(output_names) == 9L, "Phase 12 output contract must contain exactly nine files")
  must(!dir.exists(final_root) || !length(list.files(final_root, all.files = FALSE)),
       paste("Phase 12 output directory already contains files; refusing to overwrite:", final_root))

  fKDA_path <- absolute_path(phase12$kda$source, project_root)
  must(file.exists(fKDA_path), paste("fKDA source does not exist:", fKDA_path))
  must(identical(sha256_file(fKDA_path), as.character(phase12$kda$source_sha256)),
       "fKDA source checksum differs from the reviewed configuration")
  source(fKDA_path, local = environment())

  status_paths <- list.files(phase08_root, pattern = "[.]yu_mast_contrast_status[.]tsv$", full.names = TRUE)
  result_paths <- list.files(phase08_root, pattern = "[.]yu_mast_de[.]tsv[.]gz$", full.names = TRUE)
  must(length(status_paths) > 0L, "No Phase 08 contrast-status inputs found")
  must(length(result_paths) > 0L, "No Phase 08 DEG inputs found")
  contrast_status <- data.table::rbindlist(lapply(status_paths, data.table::fread), use.names = TRUE, fill = TRUE)
  de <- data.table::rbindlist(lapply(result_paths, data.table::fread), use.names = TRUE, fill = TRUE)
  must(all(contrast_status$contrast_family == "AD_vs_NCI"), "Phase 08 status includes a non-AD-vs-NCI contrast")
  must(all(de$contrast_family == "AD_vs_NCI"), "Phase 08 results include a non-AD-vs-NCI contrast")
  must(all(c("paper_deg", "logFC", "gene") %in% names(de)), "Phase 08 DEG schema is incomplete")

  annotation_path <- file.path(phase09_root, "gene_annotation_master.tsv.gz")
  annotation_status_path <- file.path(phase09_root, "annotation_status.tsv")
  must(file.exists(annotation_path), "Phase 09 gene annotation master is missing")
  must(file.exists(annotation_status_path), "Phase 09 annotation status is missing")
  annotation_status <- data.table::fread(annotation_status_path)
  must(nrow(annotation_status) == 1L && annotation_status$validation_status == "validated_complete",
       "Phase 09 annotation is not validated_complete")
  annotation <- data.table::fread(annotation_path)
  annotation <- annotation[reference_only == FALSE]
  annotation[, mapped_gene := ifelse(
    !is.na(symbol_hgnc_current) & nzchar(symbol_hgnc_current),
    symbol_hgnc_current, feature_id_original
  )]
  annotation <- unique(annotation[, .(rds_id, gene = feature_id_original, mapped_gene, mito_tier)])
  de <- merge(de, annotation, by = c("rds_id", "gene"), all.x = TRUE)
  de[is.na(mapped_gene) | !nzchar(mapped_gene), mapped_gene := gene]
  contrast_status[, group_id := group_id_from(sex, apoe_group)]
  de[, group_id := group_id_from(sex, apoe_group)]

  configured_groups <- vapply(phase12$primary_groups, function(x) as.character(x$group_id), character(1))
  fine_types <- sort(unique(contrast_status$cell_type_high_resolution))
  fine_networks <- vapply(fine_types, fine_to_network, character(1))
  must(!anyNA(fine_networks), paste(
    "No broad-network mapping for:", paste(fine_types[is.na(fine_networks)], collapse = ", ")
  ))
  must(setequal(unique(contrast_status$group_id), configured_groups), "Phase 08 strata differ from Phase 12 primary groups")
  must(!anyDuplicated(contrast_status[, .(cell_type_high_resolution, group_id)]),
       "Phase 08 has duplicate fine-cell-type/stratum statuses")

  network_names <- unique(fine_networks)
  networks <- list()
  network_checks <- list()
  for (network_name in network_names) {
    cfg <- phase12$networks[[network_name]]
    must(!is.null(cfg), paste("Network is not configured:", network_name))
    path <- absolute_path(cfg$path, project_root)
    must(file.exists(path), paste("Network file is missing:", path))
    observed_sha <- sha256_file(path)
    must(identical(observed_sha, as.character(cfg$sha256)), paste("Network checksum mismatch:", network_name))
    net <- read_network(path)
    must(nrow(net) > 0L, paste("Network has no usable edges:", network_name))
    dag <- is_dag(net)
    must(dag, paste("Network is not a DAG:", network_name))
    networks[[network_name]] <- net
    network_checks[[network_name]] <- data.table::data.table(
      network = network_name, path = relative_path(path, project_root), sha256 = observed_sha,
      edges = nrow(net), nodes = length(unique(c(net[[1L]], net[[2L]]))), is_dag = dag
    )
  }
  network_inventory <- data.table::rbindlist(network_checks)

  directions <- unlist(phase12$signature_directions, use.names = FALSE)
  tiers <- unlist(phase12$query_universe$mito_tiers, use.names = FALSE)
  minimum_query <- as.integer(phase12$eligibility$minimum_effective_query_genes)
  source_cache <- list()
  for (fine in fine_types) {
    for (group in configured_groups) {
      key <- paste(fine, group, sep = "||")
      status_row <- contrast_status[cell_type_high_resolution == fine & group_id == group]
      source_rows <- de[cell_type_high_resolution == fine & group_id == group]
      source_complete <- nrow(status_row) == 1L && status_row$terminal_status == "validated_complete"
      tested <- if (source_complete) sort(unique(source_rows$mapped_gene)) else character()
      deg <- source_rows[paper_deg == TRUE & mito_tier %in% tiers]
      source_cache[[key]] <- list(
        complete = source_complete,
        terminal_status = if (nrow(status_row)) as.character(status_row$terminal_status) else "missing",
        contrast_id = if (nrow(status_row)) as.character(status_row$contrast_id) else "",
        tested = tested,
        up = sort(unique(deg[logFC > 0, mapped_gene])),
        down = sort(unique(deg[logFC < 0, mapped_gene]))
      )
    }
  }

  manifest_parts <- list()
  signature_parts <- list()
  background_parts <- list()
  result_parts <- list()
  part_index <- 0L
  pool_defs <- lapply(phase12$secondary_pools, unlist, use.names = FALSE)
  analysis_defs <- c(
    setNames(lapply(configured_groups, function(x) x), configured_groups),
    pool_defs
  )
  analysis_tiers <- c(
    setNames(rep("primary", length(configured_groups)), configured_groups),
    setNames(rep("secondary", length(pool_defs)), names(pool_defs))
  )

  for (fine in fine_types) {
    network_name <- fine_to_network(fine)
    full_net <- networks[[network_name]]
    for (signature_group in names(analysis_defs)) {
      members <- as.character(analysis_defs[[signature_group]])
      sources <- lapply(members, function(group) source_cache[[paste(fine, group, sep = "||")]])
      sources_complete <- all(vapply(sources, `[[`, logical(1), "complete"))
      source_statuses <- paste(vapply(sources, `[[`, character(1), "terminal_status"), collapse = ";")
      source_contrasts <- paste(vapply(sources, `[[`, character(1), "contrast_id"), collapse = ";")
      tested <- if (sources_complete) Reduce(intersect, lapply(sources, `[[`, "tested")) else character()
      up <- if (sources_complete) sort(unique(unlist(lapply(sources, `[[`, "up")))) else character()
      down <- if (sources_complete) sort(unique(unlist(lapply(sources, `[[`, "down")))) else character()
      candidate_sets <- list(AD_up_mito = up, AD_down_mito = down, AD_both_mito = sort(unique(c(up, down))))
      induced <- full_net[full_net[[1L]] %in% tested & full_net[[2L]] %in% tested, , drop = FALSE]
      background <- sort(unique(c(induced[[1L]], induced[[2L]])))
      for (direction in directions) {
        part_index <- part_index + 1L
        candidate <- candidate_sets[[direction]]
        effective <- intersect(candidate, background)
        reason <- if (!sources_complete) {
          "source_contrast_not_validated"
        } else if (!nrow(induced)) {
          "no_induced_network_edges"
        } else if (length(effective) < minimum_query) {
          "effective_query_below_minimum"
        } else {
          "eligible"
        }
        run_id <- safe_id(analysis_tiers[[signature_group]], fine, signature_group, direction)
        meta <- list(
          kda_run_id = run_id,
          analysis_tier = analysis_tiers[[signature_group]],
          fine_cell_type = fine,
          broad_network = network_name,
          signature_group = signature_group,
          signature_direction = direction
        )
        kda_result <- NULL
        kda_error <- ""
        elapsed <- 0
        if (identical(reason, "eligible")) {
          sig <- data.frame(Var = effective, Group = run_id, stringsAsFactors = FALSE)
          call_start <- proc.time()[[3L]]
          tryCatch(
            capture.output({
              kda_result <- call_key_drivers(
                net = induced,
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
            error = function(e) kda_error <<- conditionMessage(e)
          )
          elapsed <- proc.time()[[3L]] - call_start
          if (nzchar(kda_error)) reason <- "kda_error"
        }
        normalized <- normalize_kda_result(kda_result, meta, phase12$schemas$results)
        if (nrow(normalized) && any(normalized$overlap_count < 1L)) {
          kda_error <- "fKDA returned a significant key driver with zero signature overlap"
          reason <- "kda_error"
          normalized <- empty_results()
        }
        terminal <- if (reason == "eligible") {
          if (nrow(normalized)) "completed_significant" else "completed_no_significant"
        } else if (reason == "kda_error") {
          "failed"
        } else {
          paste0("skipped_", reason)
        }
        manifest_parts[[part_index]] <- data.table::data.table(
          schema_version = phase12$schemas$run_manifest,
          kda_run_id = run_id,
          analysis_tier = meta$analysis_tier,
          fine_cell_type = fine,
          broad_network = network_name,
          signature_group = signature_group,
          source_groups = paste(members, collapse = ";"),
          source_contrast_ids = source_contrasts,
          source_terminal_statuses = source_statuses,
          signature_direction = direction,
          candidate_query_genes = length(candidate),
          effective_query_genes = length(effective),
          exact_tested_genes = length(tested),
          induced_network_edges = nrow(induced),
          effective_background_genes = length(background),
          eligibility_status = reason,
          terminal_status = terminal,
          significant_key_drivers = nrow(normalized),
          elapsed_seconds = elapsed,
          message = kda_error
        )
        if (length(candidate)) {
          signature_parts[[part_index]] <- data.table::data.table(
            schema_version = phase12$schemas$signature_members,
            kda_run_id = run_id,
            gene = candidate,
            effective_member = candidate %in% effective,
            exclusion_reason = ifelse(candidate %in% effective, "", "not_in_effective_background")
          )
        }
        if (length(background)) {
          background_parts[[part_index]] <- data.table::data.table(
            schema_version = phase12$schemas$background_members,
            kda_run_id = run_id,
            gene = background
          )
        }
        if (nrow(normalized)) result_parts[[part_index]] <- normalized
        cat(sprintf("[%d] %s: %s (%d effective genes, %d KDs, %.2fs)\n",
                    part_index, run_id, terminal, length(effective), nrow(normalized), elapsed))
      }
    }
  }

  run_manifest <- data.table::rbindlist(manifest_parts, use.names = TRUE, fill = TRUE)
  signature_members <- data.table::rbindlist(signature_parts, use.names = TRUE, fill = TRUE)
  if (!nrow(signature_members)) signature_members <- data.table::data.table(
    schema_version = character(), kda_run_id = character(), gene = character(),
    effective_member = logical(), exclusion_reason = character()
  )
  background_members <- data.table::rbindlist(background_parts, use.names = TRUE, fill = TRUE)
  if (!nrow(background_members)) background_members <- data.table::data.table(
    schema_version = character(), kda_run_id = character(), gene = character()
  )
  results <- data.table::rbindlist(result_parts, use.names = TRUE, fill = TRUE)
  if (!nrow(results)) results <- empty_results()

  if (nrow(results)) {
    key_driver_summary <- results[, .(
      significant_runs = data.table::uniqueN(kda_run_id),
      fine_cell_types = data.table::uniqueN(fine_cell_type),
      primary_runs = data.table::uniqueN(kda_run_id[analysis_tier == "primary"]),
      secondary_runs = data.table::uniqueN(kda_run_id[analysis_tier == "secondary"]),
      global_calls = sum(global_key_driver %in% TRUE, na.rm = TRUE),
      minimum_adjusted_p_value = min(adjusted_p_value, na.rm = TRUE),
      maximum_fold_enrichment = max(fold_enrichment, na.rm = TRUE)
    ), by = .(broad_network, key_driver)]
    key_driver_summary[, schema_version := phase12$schemas$summary]
    data.table::setcolorder(key_driver_summary, "schema_version")
  } else {
    key_driver_summary <- data.table::data.table(
      schema_version = character(), broad_network = character(), key_driver = character(),
      significant_runs = integer(), fine_cell_types = integer(), primary_runs = integer(),
      secondary_runs = integer(), global_calls = integer(), minimum_adjusted_p_value = numeric(),
      maximum_fold_enrichment = numeric()
    )
  }

  qc_summary <- run_manifest[, .(
    planned_runs = .N,
    eligible_runs = sum(eligibility_status == "eligible"),
    skipped_runs = sum(grepl("^skipped_", terminal_status)),
    failed_runs = sum(terminal_status == "failed"),
    significant_runs = sum(terminal_status == "completed_significant"),
    no_significant_runs = sum(terminal_status == "completed_no_significant"),
    candidate_query_genes = sum(candidate_query_genes),
    effective_query_genes = sum(effective_query_genes),
    significant_key_drivers = sum(significant_key_drivers),
    elapsed_seconds = sum(elapsed_seconds)
  ), by = .(analysis_tier, broad_network, fine_cell_type)]
  qc_summary[, schema_version := phase12$schemas$qc]
  data.table::setcolorder(qc_summary, "schema_version")

  checks <- data.table::data.table(
    check_id = c(
      "fine_cell_type_count", "network_count", "primary_run_count", "secondary_run_count",
      "planned_run_count", "unique_run_ids", "all_sources_represented", "no_kda_failures",
      "signatures_are_core_mito", "effective_queries_in_background", "networks_are_dags"
    ),
    severity = c(rep("error", 8L), rep("error", 3L)),
    observed = c(
      length(fine_types), length(network_names),
      sum(run_manifest$analysis_tier == "primary"), sum(run_manifest$analysis_tier == "secondary"),
      nrow(run_manifest), data.table::uniqueN(run_manifest$kda_run_id),
      nrow(contrast_status), sum(run_manifest$terminal_status == "failed"),
      sum(!signature_members$gene %in% unique(de[mito_tier %in% tiers, mapped_gene])),
      sum(signature_members$effective_member & !paste(signature_members$kda_run_id, signature_members$gene) %in%
            paste(background_members$kda_run_id, background_members$gene)),
      sum(network_inventory$is_dag)
    ),
    expected = c(
      expected$fine_cell_types, expected$networks, expected$primary_runs, expected$secondary_runs,
      expected$planned_runs, expected$planned_runs,
      length(fine_types) * length(configured_groups), 0L, 0L, 0L, length(network_names)
    )
  )
  checks[, passed := as.character(observed) == as.character(expected)]
  checks[, schema_version := phase12$schemas$checks]
  data.table::setcolorder(checks, "schema_version")
  must(all(checks[severity == "error", passed]), paste(
    "Phase 12 validation failed:", paste(checks[passed == FALSE, check_id], collapse = ", ")
  ))

  staged_paths <- setNames(file.path(staging_root, output_names), output_names)
  atomic_fwrite(run_manifest, staged_paths[["kda_run_manifest.tsv"]])
  atomic_fwrite(signature_members, staged_paths[["kda_signature_members.tsv.gz"]])
  atomic_fwrite(background_members, staged_paths[["kda_background_members.tsv.gz"]])
  atomic_fwrite(results, staged_paths[["kda_results.tsv.gz"]])
  atomic_fwrite(key_driver_summary, staged_paths[["kda_key_driver_summary.tsv"]])
  atomic_fwrite(qc_summary, staged_paths[["kda_qc_summary.tsv"]])
  atomic_fwrite(checks, staged_paths[["kda_checks.tsv"]])

  artifact_inputs <- data.table::rbindlist(list(
    data.table::data.table(
      artifact_role = c("phase12_config", "fKDA_source", "phase09_annotation", "phase09_status"),
      path = c(phase12_path, fKDA_path, annotation_path, annotation_status_path)
    ),
    data.table::data.table(artifact_role = "phase08_status", path = status_paths),
    data.table::data.table(artifact_role = "phase08_results", path = result_paths),
    data.table::data.table(
      artifact_role = paste0("network_", network_inventory$network),
      path = vapply(network_inventory$path, absolute_path, character(1), root = project_root)
    )
  ))
  output_artifact_names <- setdiff(output_names, c("kda_artifacts.tsv", "kda_status.tsv"))
  artifact_outputs <- data.table::data.table(
    artifact_role = "phase12_output",
    path = file.path(final_root, output_artifact_names),
    hash_source = unname(staged_paths[output_artifact_names])
  )
  artifact_inputs[, hash_source := path]
  artifacts <- data.table::rbindlist(list(artifact_inputs, artifact_outputs), use.names = TRUE, fill = TRUE)
  artifacts[, `:=`(
    schema_version = phase12$schemas$artifacts,
    sha256 = vapply(hash_source, sha256_file, character(1)),
    bytes = vapply(hash_source, function(p) file.info(p)$size, numeric(1)),
    path = vapply(path, relative_path, character(1), root = project_root)
  )]
  artifacts[, hash_source := NULL]
  data.table::setcolorder(artifacts, "schema_version")
  atomic_fwrite(artifacts, staged_paths[["kda_artifacts.tsv"]])

  elapsed_total <- as.numeric(difftime(Sys.time(), start_time, units = "secs"))
  status <- data.table::data.table(
    schema_version = phase12$schemas$status,
    execution_stage = stage_name,
    execution_phase = as.integer(execution$execution_phase),
    backend = as.character(execution$backend),
    execution_run_id = as.character(execution$run_id),
    stable_task_id = "global:kda",
    task_mode = "kda",
    scientific_script = "scripts/12_run_kda.R",
    scientific_script_sha256 = sha256_file(file.path(project_root, "scripts/12_run_kda.R")),
    scientific_config_sha256 = sha256_file(phase12_path),
    pipeline_config_sha256 = sha256_file(config_path),
    execution_config_sha256 = sha256_file(execution_path),
    phase08_status_sha256 = paste(vapply(status_paths, sha256_file, character(1)), collapse = ";"),
    phase08_results_sha256 = paste(vapply(result_paths, sha256_file, character(1)), collapse = ";"),
    phase09_annotation_sha256 = sha256_file(annotation_path),
    fKDA_source_sha256 = sha256_file(fKDA_path),
    network_sha256 = paste(paste(network_inventory$network, network_inventory$sha256, sep = "="), collapse = ";"),
    fine_cell_types = length(fine_types),
    broad_networks = length(network_names),
    planned_runs = nrow(run_manifest),
    eligible_runs = sum(run_manifest$eligibility_status == "eligible"),
    skipped_runs = sum(grepl("^skipped_", run_manifest$terminal_status)),
    failed_runs = sum(run_manifest$terminal_status == "failed"),
    significant_runs = sum(run_manifest$terminal_status == "completed_significant"),
    significant_key_drivers = nrow(results),
    failed_checks = sum(!checks$passed),
    peak_ram_gib = peak_ram_gib(),
    elapsed_seconds = elapsed_total,
    validation_status = as.character(expected$validation_status),
    git_revision = git_revision(project_root),
    timestamp_utc = format(Sys.time(), tz = "UTC", usetz = TRUE)
  )
  atomic_fwrite(status, staged_paths[["kda_status.tsv"]])

  dir.create(final_root, recursive = TRUE, showWarnings = FALSE)
  for (name in output_names) {
    must(file.rename(staged_paths[[name]], file.path(final_root, name)), paste("Could not publish", name))
  }
  cat(sprintf(
    "Phase 12 KDA complete: %d planned, %d eligible, %d significant runs, %d key-driver rows in %.1f seconds\n",
    nrow(run_manifest), sum(run_manifest$eligibility_status == "eligible"),
    sum(run_manifest$terminal_status == "completed_significant"), nrow(results), elapsed_total
  ))
  invisible(list(status = status, checks = checks, manifest = run_manifest))
}

direct_file <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
if (length(direct_file) && grepl("(^|/)12_run_kda[.]R$", direct_file[[1L]])) {
  phase12_main()
}
