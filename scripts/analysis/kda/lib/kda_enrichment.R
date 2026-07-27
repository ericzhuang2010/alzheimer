KDA_ENRICHMENT_COLUMNS <- c(
  "run_id", "network_id", "driver", "query_size_original",
  "query_size_effective", "background_size", "neighborhood_size",
  "overlap_size", "overlap_genes", "fold_enrichment", "p_value",
  "q_value", "significant", "driver_in_query", "driver_in_background",
  "wang_global_keydriver_flag", "driver_search_layers", "enrichment_layers"
)

empty_enrichment_table <- function() {
  data.table::data.table(
    run_id = character(),
    network_id = character(),
    driver = character(),
    query_size_original = integer(),
    query_size_effective = integer(),
    background_size = integer(),
    neighborhood_size = integer(),
    overlap_size = integer(),
    overlap_genes = character(),
    fold_enrichment = numeric(),
    p_value = numeric(),
    q_value = numeric(),
    significant = logical(),
    driver_in_query = logical(),
    driver_in_background = logical(),
    wang_global_keydriver_flag = integer(),
    driver_search_layers = integer(),
    enrichment_layers = integer()
  )
}

hypergeometric_enrichment <- function(background_size,
                                      query_size,
                                      neighborhood_size,
                                      overlap_size) {
  values <- c(background_size, query_size, neighborhood_size, overlap_size)
  if (any(!is.finite(values)) || any(values < 0) ||
      any(values != as.integer(values))) {
    kda_abort("Hypergeometric sizes must be finite nonnegative integers.")
  }
  if (query_size > background_size ||
      neighborhood_size > background_size ||
      overlap_size > min(query_size, neighborhood_size)) {
    kda_abort("Inconsistent hypergeometric sizes: N=%d, K=%d, n=%d, k=%d.",
              background_size, query_size, neighborhood_size, overlap_size)
  }
  if (neighborhood_size == 0L) {
    return(list(p_value = 1, fold_enrichment = NA_real_))
  }
  p_value <- stats::phyper(
    q = overlap_size - 1L,
    m = query_size,
    n = background_size - query_size,
    k = neighborhood_size,
    lower.tail = FALSE
  )
  fold_enrichment <- (overlap_size / neighborhood_size) /
    (query_size / background_size)
  list(p_value = unname(p_value), fold_enrichment = unname(fold_enrichment))
}

compute_driver_enrichment <- function(global_drivers,
                                      neighborhoods,
                                      query,
                                      background,
                                      network_nodes_all,
                                      run_id,
                                      network_id,
                                      driver_search_layers = 6L,
                                      enrichment_layers = 3L,
                                      p_adjust_method = "BH",
                                      alpha = 0.05,
                                      query_size_original = NULL) {
  require_kda_packages("data.table")
  driver_search_layers <- validate_positive_integer(driver_search_layers, "driver_search_layers")
  enrichment_layers <- validate_positive_integer(enrichment_layers, "enrichment_layers")
  if (!p_adjust_method %in% stats::p.adjust.methods) {
    kda_abort("Unknown P-value adjustment method: %s", p_adjust_method)
  }
  if (length(alpha) != 1L || !is.finite(alpha) || alpha <= 0 || alpha > 1) {
    kda_abort("alpha must be in (0, 1].")
  }
  validated <- validate_query_background(
    query, background, network_nodes_all,
    minimum_effective_query_size = 3L,
    query_label = run_id
  )
  query <- validated$query
  effective_query <- validated$effective_query
  background <- validated$background
  query_size_original <- as.integer(query_size_original %||% length(query))
  if (query_size_original < length(query)) {
    kda_abort("query_size_original cannot be smaller than the supplied query membership.")
  }

  required_driver_columns <- c("driver", "wang_global_keydriver_flag")
  missing_driver_columns <- setdiff(required_driver_columns, names(global_drivers))
  if (length(missing_driver_columns)) {
    kda_abort("Global driver table is missing column(s): %s",
              paste(missing_driver_columns, collapse = ", "))
  }
  if (!all(c("driver", "gene") %in% names(neighborhoods))) {
    kda_abort("Neighborhood table must contain 'driver' and 'gene'.")
  }
  drivers <- sort(unique(as.character(global_drivers$driver)), method = "radix")
  if (!length(drivers)) {
    return(list(
      enrichment = empty_enrichment_table(),
      overlap_members = data.table::data.table(
        run_id = character(), network_id = character(),
        driver = character(), gene = character()
      ),
      coverage = data.table::data.table(
        run_id = run_id,
        network_id = network_id,
        query_size_original = query_size_original,
        query_size_supplied = length(query),
        query_size_effective = length(effective_query),
        background_size = length(background),
        network_size = length(network_nodes_all),
        query_coverage_fraction = length(effective_query) / query_size_original,
        missing_query_genes = paste(validated$query_missing_from_background, collapse = ";")
      )
    ))
  }
  unknown_neighborhood_drivers <- setdiff(unique(neighborhoods$driver), drivers)
  if (length(unknown_neighborhood_drivers)) {
    kda_abort("Neighborhood table contains driver(s) absent from global_drivers.")
  }
  unknown_neighborhood_genes <- setdiff(unique(neighborhoods$gene), network_nodes_all)
  if (length(unknown_neighborhood_genes)) {
    kda_abort("Neighborhood table contains gene(s) absent from the network.")
  }

  result_rows <- vector("list", length(drivers))
  overlap_rows <- vector("list", length(drivers))
  for (index in seq_along(drivers)) {
    driver <- drivers[[index]]
    current_driver <- driver
    neighborhood <- sort(
      unique(as.character(neighborhoods[driver == current_driver, gene])),
      method = "radix"
    )
    background_neighborhood <- intersect(neighborhood, background)
    overlap <- intersect(background_neighborhood, effective_query)
    statistic <- hypergeometric_enrichment(
      length(background),
      length(effective_query),
      length(background_neighborhood),
      length(overlap)
    )
    driver_row <- global_drivers[driver == current_driver][1L]
    result_rows[[index]] <- data.table::data.table(
      run_id = run_id,
      network_id = network_id,
      driver = driver,
      query_size_original = query_size_original,
      query_size_effective = length(effective_query),
      background_size = length(background),
      neighborhood_size = length(background_neighborhood),
      overlap_size = length(overlap),
      overlap_genes = paste(overlap, collapse = ";"),
      fold_enrichment = statistic$fold_enrichment,
      p_value = statistic$p_value,
      q_value = NA_real_,
      significant = FALSE,
      driver_in_query = driver %in% query,
      driver_in_background = driver %in% background,
      wang_global_keydriver_flag = as.integer(driver_row$wang_global_keydriver_flag),
      driver_search_layers = driver_search_layers,
      enrichment_layers = enrichment_layers
    )
    overlap_rows[[index]] <- data.table::data.table(
      run_id = run_id,
      network_id = network_id,
      driver = driver,
      gene = overlap
    )
  }
  enrichment <- data.table::rbindlist(result_rows, use.names = TRUE)
  enrichment[, q_value := stats::p.adjust(p_value, method = p_adjust_method)]
  enrichment[, significant := !is.na(q_value) & q_value <= alpha]
  data.table::setorder(enrichment, q_value, p_value, driver, na.last = TRUE)
  overlaps <- data.table::rbindlist(overlap_rows, use.names = TRUE)
  if (nrow(overlaps)) data.table::setorder(overlaps, driver, gene)
  absent_drivers <- sum(!enrichment$driver_in_background)
  if (absent_drivers) {
    kda_warn("%d/%d candidate drivers are absent from the contrast background.",
             absent_drivers, nrow(enrichment))
  }
  if (!any(enrichment$significant)) {
    kda_warn("No candidate driver passes adjusted P <= %.4g for run %s.", alpha, run_id)
  }
  coverage <- data.table::data.table(
    run_id = run_id,
    network_id = network_id,
    query_size_original = query_size_original,
    query_size_supplied = length(query),
    query_size_effective = length(effective_query),
    background_size = length(background),
    network_size = length(network_nodes_all),
    query_coverage_fraction = length(effective_query) / query_size_original,
    missing_query_genes = paste(validated$query_missing_from_background, collapse = ";")
  )
  list(enrichment = enrichment, overlap_members = overlaps, coverage = coverage)
}

enrichment_output_files <- function(output_directory) {
  list(
    coverage = file.path(output_directory, "query_coverage.tsv"),
    enrichment = file.path(output_directory, "driver_enrichment.tsv"),
    overlaps = file.path(output_directory, "overlap_members.tsv.gz"),
    manifest = file.path(output_directory, "run_manifest.json")
  )
}

read_completed_enrichment_output <- function(output_directory) {
  files <- enrichment_output_files(output_directory)
  required <- unlist(files[c("coverage", "enrichment", "overlaps")])
  missing <- required[!file.exists(required)]
  if (length(missing)) {
    kda_abort("Completed enrichment manifest is missing output file(s): %s",
              paste(missing, collapse = ", "))
  }
  list(
    query_coverage = read_tsv(files$coverage),
    enrichment = read_tsv(files$enrichment),
    overlap_members = read_tsv(files$overlaps),
    manifest = read_json_manifest(files$manifest),
    reused = TRUE
  )
}

run_signature_enrichment_files <- function(manifest_path,
                                           run_id,
                                           global_root,
                                           output_root,
                                           p_adjust_method = "BH",
                                           alpha = 0.05,
                                           force = FALSE,
                                           project_root = find_project_root()) {
  require_kda_packages()
  assert_kda_available()
  manifest_path <- resolve_project_path(manifest_path, project_root)
  global_root <- resolve_project_path(global_root, project_root)
  output_root <- resolve_project_path(output_root, project_root)
  manifest <- read_run_manifest(manifest_path)
  selected_run_id <- run_id
  selected <- manifest[run_id == selected_run_id]
  if (nrow(selected) != 1L) {
    kda_abort("run_id '%s' occurs %d times in the manifest.", run_id, nrow(selected))
  }
  if ("eligible" %in% names(selected) && !isTRUE(as.logical(selected$eligible[[1L]]))) {
    reason <- manifest_row_value(selected, "skip_reason", "ineligible")
    kda_abort("run_id '%s' is ineligible: %s", run_id, reason)
  }
  network_id <- selected$network_id[[1L]]
  network_path <- resolve_project_path(selected$network_path[[1L]], project_root)
  signature_path <- resolve_project_path(selected$signature_path[[1L]], project_root)
  background_path <- resolve_project_path(selected$background_path[[1L]], project_root)
  query <- read_membership_genes(signature_path, run_id, "signature")
  background <- read_membership_genes(background_path, run_id, "background")
  network <- read_network_file(network_path)

  global_directory <- file.path(global_root, network_id)
  global_files <- global_output_files(global_directory)
  global_manifest <- read_json_manifest(global_files$manifest)
  if (is.null(global_manifest) ||
      !identical(as.character(global_manifest$status %||% ""), "complete")) {
    kda_abort("Compatible completed global KDA output is absent: %s", global_directory)
  }
  network_checksum <- sha256_file(network_path)
  if (!identical(as.character(global_manifest$network_sha256), network_checksum)) {
    kda_abort("Global KDA network checksum does not match manifest run %s.", run_id)
  }
  global <- read_completed_global_output(global_directory)
  driver_search_layers <- as.integer(global_manifest$driver_search_layers)
  enrichment_layers <- as.integer(global_manifest$enrichment_layers)
  query_checksum <- sha256_character_vector(query)
  background_checksum <- sha256_character_vector(background)
  output_directory <- file.path(output_root, safe_path_component(run_id))
  files <- enrichment_output_files(output_directory)
  expected <- list(
    analysis_type = "signature_enrichment",
    run_id = run_id,
    network_id = network_id,
    network_sha256 = network_checksum,
    effective_signature_sha256 = query_checksum,
    background_sha256 = background_checksum,
    global_manifest_sha256 = sha256_file(global_files$manifest),
    p_adjust_method = p_adjust_method,
    alpha = alpha,
    driver_search_layers = driver_search_layers,
    enrichment_layers = enrichment_layers
  )
  if (assert_compatible_completed_run(files$manifest, expected, force, "signature enrichment")) {
    kda_message("Reusing compatible signature-enrichment output: %s", output_directory)
    return(read_completed_enrichment_output(output_directory))
  }
  if (!isTRUE(force) && dir.exists(output_directory) &&
      length(list.files(output_directory, all.files = TRUE, no.. = TRUE))) {
    kda_abort("Enrichment output directory is nonempty without a compatible manifest; use --force or a new directory: %s", output_directory)
  }

  started <- Sys.time()
  query_size_original <- suppressWarnings(as.integer(
    manifest_row_value(selected, "query_size_original", length(query))
  ))
  if (is.na(query_size_original)) query_size_original <- length(query)
  result <- compute_driver_enrichment(
    global$global_drivers,
    global$neighborhoods,
    query,
    background,
    network_nodes(network),
    run_id,
    network_id,
    driver_search_layers,
    enrichment_layers,
    p_adjust_method,
    alpha,
    query_size_original
  )
  if ("query_genes_unmapped" %in% names(selected)) {
    result$coverage[, missing_query_genes := as.character(selected$query_genes_unmapped[[1L]])]
  }
  atomic_write_tsv(result$coverage, files$coverage)
  atomic_write_tsv(result$enrichment, files$enrichment)
  atomic_write_tsv(result$overlap_members, files$overlaps)
  finished <- Sys.time()
  run_manifest <- c(
    common_run_provenance(project_root),
    expected,
    list(
      status = "complete",
      archive_sha256 = checksum_or_na(file.path(
        project_root, "archive", "wang_kda_code", "KDA_analysis", "KDA-0.2.tar.gz"
      )),
      source_manifest_path = project_relative_path(manifest_path, project_root),
      signature_path = project_relative_path(signature_path, project_root),
      signature_file_sha256 = sha256_file(signature_path),
      background_path = project_relative_path(background_path, project_root),
      background_file_sha256 = sha256_file(background_path),
      query_size_original = result$coverage$query_size_original[[1L]],
      query_size_effective = result$coverage$query_size_effective[[1L]],
      background_size = result$coverage$background_size[[1L]],
      candidate_drivers = nrow(result$enrichment),
      significant_drivers = sum(result$enrichment$significant),
      started_at = utc_timestamp(started),
      completed_at = utc_timestamp(finished),
      elapsed_seconds = unname(as.numeric(difftime(finished, started, units = "secs")))
    )
  )
  atomic_write_json(run_manifest, files$manifest)
  list(
    query_coverage = result$coverage,
    enrichment = result$enrichment,
    overlap_members = result$overlap_members,
    manifest = run_manifest,
    reused = FALSE
  )
}

run_celltype_kda <- function(network,
                             signatures,
                             backgrounds,
                             driver_search_layers = 6L,
                             enrichment_layers = 3L,
                             include_driver_in_neighborhood = FALSE,
                             boost_hubs = TRUE,
                             p_adjust_method = "BH",
                             alpha = 0.05) {
  require_kda_packages()
  network <- validate_network(network)
  if (!is.list(signatures) || is.null(names(signatures)) ||
      any(!nzchar(names(signatures))) || anyDuplicated(names(signatures))) {
    kda_abort("signatures must be a uniquely named list of gene vectors.")
  }
  if (!is.list(backgrounds) || !setequal(names(backgrounds), names(signatures))) {
    kda_abort("backgrounds must be a named list matching signatures exactly.")
  }
  global <- run_global_driver_search(network, driver_search_layers, boost_hubs)
  global_drivers <- format_global_drivers(global$parsed$drivers, "in_memory")
  neighborhoods <- extract_driver_neighborhoods(
    network,
    global_drivers$driver,
    enrichment_layers,
    include_driver_in_neighborhood,
    "in_memory"
  )
  per_signature <- lapply(names(signatures), function(run_id) {
    compute_driver_enrichment(
      global_drivers,
      neighborhoods,
      signatures[[run_id]],
      backgrounds[[run_id]],
      network_nodes(network),
      run_id,
      "in_memory",
      driver_search_layers,
      enrichment_layers,
      p_adjust_method,
      alpha
    )
  })
  names(per_signature) <- names(signatures)
  query_coverage <- data.table::rbindlist(lapply(per_signature, `[[`, "coverage"))
  enrichment <- data.table::rbindlist(lapply(per_signature, `[[`, "enrichment"))
  significant <- enrichment[significant == TRUE]
  list(
    run_manifest = list(
      status = "complete",
      kda_version = assert_kda_available(),
      driver_search_layers = driver_search_layers,
      enrichment_layers = enrichment_layers,
      include_driver_in_neighborhood = include_driver_in_neighborhood,
      boost_hubs = boost_hubs,
      p_adjust_method = p_adjust_method,
      alpha = alpha
    ),
    query_coverage = query_coverage,
    global_drivers = global_drivers,
    neighborhoods = neighborhoods,
    enrichment = enrichment,
    significant_drivers = significant,
    raw_kda = global$raw
  )
}
