KDA_DRIVER_COLUMNS <- c(
  "keydrivers", "is_signature", "hits", "downstream",
  "signature_in_subnetwork", "subnetwork_size", "signature_in_network",
  "network_size", "signature", "optimal_layer", "fold_change_whole",
  "pvalue_whole", "fold_change_subnet", "pvalue_subnet",
  "pvalue_corrected_subnet", "keydriver"
)

KDA_DRIVER_NUMERIC_COLUMNS <- setdiff(KDA_DRIVER_COLUMNS, "keydrivers")

empty_global_drivers <- function() {
  data.table::data.table(
    network_id = character(),
    driver = character(),
    wang_global_keydriver_flag = integer()
  )
}

parse_numeric_column <- function(value, column) {
  value <- as.character(value)
  parsed <- suppressWarnings(as.numeric(value))
  invalid <- is.na(value) | !nzchar(value) | is.na(parsed) | !is.finite(parsed)
  if (any(invalid)) {
    kda_abort("KDA column '%s' contains a nonnumeric value: %s", column, value[which(invalid)[1L]])
  }
  parsed
}

parse_kda_global_result <- function(result, network_nodes_expected) {
  require_kda_packages("data.table")
  parsed <- validate_kda_raw_result(result, allow_null = TRUE)
  if (is.null(parsed)) {
    return(list(
      drivers = data.table::as.data.table(
        stats::setNames(replicate(length(KDA_DRIVER_COLUMNS), character(), simplify = FALSE),
                        KDA_DRIVER_COLUMNS)
      ),
      parameters = data.table::data.table(
        mean_downstream = character(), sd_downstream = character(),
        cut_downstream = character(), mean_degree = character(),
        sd_degree = character(), cut_degree = character()
      ),
      downstream = data.table::data.table(node = character(), downstream = numeric())
    ))
  }
  drivers <- data.table::as.data.table(parsed$drivers)
  missing_columns <- setdiff(KDA_DRIVER_COLUMNS, names(drivers))
  if (length(missing_columns) || length(names(drivers)) != length(KDA_DRIVER_COLUMNS)) {
    kda_abort("KDA driver result must have exactly the expected 16 columns; missing: %s",
              paste(missing_columns, collapse = ", "))
  }
  drivers <- drivers[, ..KDA_DRIVER_COLUMNS]
  for (column in KDA_DRIVER_NUMERIC_COLUMNS) {
    drivers[[column]] <- parse_numeric_column(drivers[[column]], column)
  }
  if (any(!drivers$keydriver %in% c(0, 1))) {
    kda_abort("KDA 'keydriver' flags must be 0 or 1.")
  }
  if (anyDuplicated(drivers$keydrivers)) {
    kda_abort("KDA returned duplicate candidate-driver identifiers.")
  }
  if (any(!drivers$keydrivers %in% network_nodes_expected)) {
    kda_abort("KDA returned a candidate driver absent from the network.")
  }

  downstream <- data.table::as.data.table(parsed$downstream)
  downstream_values <- parse_numeric_column(downstream[["downstream"]], "downstream")
  downstream <- data.table::data.table(
    node = as.character(downstream[["node"]]),
    downstream = downstream_values
  )
  if (!setequal(downstream$node, network_nodes_expected) ||
      nrow(downstream) != length(network_nodes_expected)) {
    kda_abort("KDA downstream-count table does not contain exactly the network node set.")
  }
  if (any(downstream$downstream < 0 | downstream$downstream != as.integer(downstream$downstream))) {
    kda_abort("KDA downstream counts must be nonnegative integers.")
  }
  matched_counts <- downstream$downstream[match(drivers$keydrivers, downstream$node)]
  if (any(drivers$downstream != matched_counts)) {
    kda_abort("KDA candidate downstream counts disagree with the all-node table.")
  }
  data.table::setorder(drivers, keydrivers)
  data.table::setorder(downstream, node)

  list(
    drivers = drivers,
    parameters = data.table::as.data.table(parsed$parameters),
    downstream = downstream
  )
}

run_global_driver_search <- function(network,
                                     driver_search_layers = 6L,
                                     boost_hubs = TRUE) {
  assert_kda_available()
  network <- validate_network(network)
  driver_search_layers <- validate_positive_integer(
    driver_search_layers, "driver_search_layers"
  )
  nodes <- network_nodes(network)
  if (length(nodes) < 5L) {
    kda_abort("Global KDA requires a network with at least five nodes.")
  }
  raw <- KDA::keydriverInSubnetwork(
    as.matrix(network[, c("from", "to"), drop = FALSE]),
    signature = nodes,
    background = NULL,
    directed = TRUE,
    nlayers = driver_search_layers,
    enrichedNodes_percent_cut = -1,
    FET_pvalue_cut = 0.05,
    boost_hubs = isTRUE(boost_hubs),
    dynamic_search = TRUE,
    bonferroni_correction = TRUE,
    expanded_network_as_signature = FALSE
  )
  list(raw = raw, parsed = parse_kda_global_result(raw, nodes))
}

extract_driver_neighborhood <- function(network,
                                        driver,
                                        enrichment_layers = 3L,
                                        include_driver = FALSE) {
  enrichment_layers <- validate_positive_integer(enrichment_layers, "enrichment_layers")
  neighborhood <- KDA::downStreamGenes(
    as.matrix(network[, c("from", "to"), drop = FALSE]),
    seednodes = as.character(driver),
    N = enrichment_layers,
    directed = TRUE
  )
  if (is.null(neighborhood)) neighborhood <- character()
  neighborhood <- normalize_gene_vector(
    neighborhood,
    sprintf("downstream neighborhood for %s", driver),
    allow_empty = TRUE
  )
  if (!isTRUE(include_driver)) neighborhood <- setdiff(neighborhood, driver)
  neighborhood
}

extract_driver_neighborhoods <- function(network,
                                         drivers,
                                         enrichment_layers = 3L,
                                         include_driver = FALSE,
                                         network_id = NA_character_) {
  require_kda_packages("data.table")
  drivers <- normalize_gene_vector(drivers, "candidate drivers", allow_empty = TRUE)
  if (!length(drivers)) {
    return(data.table::data.table(
      network_id = character(),
      driver = character(),
      gene = character(),
      enrichment_layers = integer(),
      include_driver = logical()
    ))
  }
  rows <- lapply(drivers, function(driver) {
    genes <- extract_driver_neighborhood(
      network, driver, enrichment_layers, include_driver
    )
    if (!length(genes)) {
      kda_abort("KDA candidate %s has no directed downstream neighborhood.", driver)
    }
    data.table::data.table(
      network_id = network_id,
      driver = driver,
      gene = genes,
      enrichment_layers = as.integer(enrichment_layers),
      include_driver = isTRUE(include_driver)
    )
  })
  data.table::rbindlist(rows, use.names = TRUE)
}

format_global_drivers <- function(parsed_drivers, network_id) {
  require_kda_packages("data.table")
  if (!nrow(parsed_drivers)) return(empty_global_drivers())
  result <- data.table::copy(parsed_drivers)
  data.table::setnames(result, "keydrivers", "driver")
  result[, `:=`(
    network_id = network_id,
    wang_global_keydriver_flag = as.integer(keydriver)
  )]
  data.table::setcolorder(
    result,
    c("network_id", "driver", "wang_global_keydriver_flag",
      setdiff(names(result), c("network_id", "driver", "wang_global_keydriver_flag")))
  )
  data.table::setorder(result, driver)
  result[]
}

global_output_files <- function(output_directory) {
  list(
    drivers = file.path(output_directory, "global_drivers.tsv"),
    neighborhoods = file.path(output_directory, "driver_neighborhood_members.tsv.gz"),
    raw_drivers = file.path(output_directory, "raw_kda_drivers.tsv"),
    raw_parameters = file.path(output_directory, "raw_kda_parameters.tsv"),
    raw_downstream = file.path(output_directory, "raw_kda_downstream.tsv"),
    raw_rds = file.path(output_directory, "raw_kda.rds"),
    manifest = file.path(output_directory, "run_manifest.json")
  )
}

read_completed_global_output <- function(output_directory) {
  files <- global_output_files(output_directory)
  required <- unlist(files[c("drivers", "neighborhoods", "raw_drivers",
                             "raw_parameters", "raw_downstream", "raw_rds")])
  missing <- required[!file.exists(required)]
  if (length(missing)) {
    kda_abort("Completed global manifest is missing output file(s): %s", paste(missing, collapse = ", "))
  }
  list(
    global_drivers = read_tsv(files$drivers),
    neighborhoods = read_tsv(files$neighborhoods),
    raw_kda = readRDS(files$raw_rds),
    manifest = read_json_manifest(files$manifest),
    reused = TRUE
  )
}

run_global_kda_files <- function(network_id,
                                 network_path,
                                 output_root,
                                 driver_search_layers = 6L,
                                 enrichment_layers = 3L,
                                 include_driver_in_neighborhood = FALSE,
                                 boost_hubs = TRUE,
                                 force = FALSE,
                                 project_root = find_project_root()) {
  require_kda_packages()
  assert_kda_available()
  driver_search_layers <- validate_positive_integer(driver_search_layers, "driver_search_layers")
  enrichment_layers <- validate_positive_integer(enrichment_layers, "enrichment_layers")
  network_id <- safe_path_component(network_id)
  network_path <- resolve_project_path(network_path, project_root)
  output_root <- resolve_project_path(output_root, project_root)
  output_directory <- file.path(output_root, network_id)
  files <- global_output_files(output_directory)
  network_checksum <- sha256_file(network_path)
  expected <- list(
    analysis_type = "global_kda",
    network_id = network_id,
    network_sha256 = network_checksum,
    driver_search_layers = driver_search_layers,
    enrichment_layers = enrichment_layers,
    include_driver_in_neighborhood = isTRUE(include_driver_in_neighborhood),
    boost_hubs = isTRUE(boost_hubs),
    directed = TRUE,
    enriched_nodes_percent_cut = -1,
    fet_pvalue_cut = 0.05,
    dynamic_search = TRUE,
    bonferroni_correction = TRUE,
    expanded_network_as_signature = FALSE
  )
  if (assert_compatible_completed_run(files$manifest, expected, force, "global KDA")) {
    kda_message("Reusing compatible global KDA output: %s", output_directory)
    return(read_completed_global_output(output_directory))
  }
  if (!isTRUE(force) && dir.exists(output_directory) &&
      length(list.files(output_directory, all.files = TRUE, no.. = TRUE))) {
    kda_abort("Global output directory is nonempty without a compatible manifest; use --force or a new directory: %s", output_directory)
  }

  started <- Sys.time()
  network <- read_network_file(network_path, require_dag = TRUE)
  search <- run_global_driver_search(network, driver_search_layers, boost_hubs)
  drivers <- format_global_drivers(search$parsed$drivers, network_id)
  neighborhoods <- extract_driver_neighborhoods(
    network,
    drivers$driver,
    enrichment_layers,
    include_driver_in_neighborhood,
    network_id
  )
  if (!nrow(drivers)) {
    kda_warn("Global KDA returned no candidate drivers for network %s.", network_id)
  }

  raw_drivers <- search$parsed$drivers
  raw_parameters <- search$parsed$parameters
  raw_downstream <- search$parsed$downstream
  atomic_write_tsv(drivers, files$drivers)
  atomic_write_tsv(neighborhoods, files$neighborhoods)
  atomic_write_tsv(raw_drivers, files$raw_drivers)
  atomic_write_tsv(raw_parameters, files$raw_parameters)
  atomic_write_tsv(raw_downstream, files$raw_downstream)
  atomic_save_rds(search$raw, files$raw_rds)

  finished <- Sys.time()
  archive_path <- file.path(
    project_root, "archive", "wang_kda_code", "KDA_analysis", "KDA-0.2.tar.gz"
  )
  manifest <- c(
    common_run_provenance(project_root),
    expected,
    list(
      status = "complete",
      network_path = project_relative_path(network_path, project_root),
      archive_sha256 = checksum_or_na(archive_path),
      global_signature_sha256 = sha256_character_vector(network_nodes(network)),
      network_nodes = length(network_nodes(network)),
      network_edges = nrow(network),
      candidate_drivers = nrow(drivers),
      started_at = utc_timestamp(started),
      completed_at = utc_timestamp(finished),
      elapsed_seconds = unname(as.numeric(difftime(finished, started, units = "secs")))
    )
  )
  atomic_write_json(manifest, files$manifest)
  list(
    global_drivers = drivers,
    neighborhoods = neighborhoods,
    raw_kda = search$raw,
    manifest = manifest,
    reused = FALSE
  )
}
