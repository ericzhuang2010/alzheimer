KDA_EXPECTED_VERSION <- "0.2"
KDA_EXPECTED_ARCHIVE_SHA256 <-
  "7b185e16ef855a4d19061722f3920100777c19acd8357107a31928b73fe9e70f"
KDA_REQUIRED_EXPORTS <- c("keydriverInSubnetwork", "downStreamGenes")
KDA_MANIFEST_REQUIRED_COLUMNS <- c(
  "run_id",
  "network_id",
  "network_path",
  "fine_cell_type",
  "sex",
  "apoe_group",
  "comparison",
  "query_direction",
  "signature_path",
  "background_path"
)

require_kda_packages <- function(packages = c("data.table", "digest", "jsonlite")) {
  missing_packages <- packages[
    !vapply(packages, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1L))
  ]
  if (length(missing_packages)) {
    kda_abort(
      "Missing required R package(s): %s. Run renv::restore(prompt = FALSE).",
      paste(missing_packages, collapse = ", ")
    )
  }
  invisible(TRUE)
}

assert_kda_available <- function() {
  if (!requireNamespace("KDA", quietly = TRUE)) {
    kda_abort(
      "KDA 0.2 is not installed in the active project library. Run scripts/analysis/kda/install_kda.R."
    )
  }
  installed_version <- as.character(utils::packageVersion("KDA"))
  if (!identical(installed_version, KDA_EXPECTED_VERSION)) {
    kda_abort(
      "KDA version %s is installed; this workflow requires exactly %s.",
      installed_version,
      KDA_EXPECTED_VERSION
    )
  }
  exports <- getNamespaceExports("KDA")
  missing_exports <- setdiff(KDA_REQUIRED_EXPORTS, exports)
  if (length(missing_exports)) {
    kda_abort(
      "KDA %s is missing required exported function(s): %s",
      installed_version,
      paste(missing_exports, collapse = ", ")
    )
  }
  invisible(installed_version)
}

normalize_gene_vector <- function(genes, label = "genes", allow_empty = FALSE) {
  genes <- trimws(as.character(genes))
  invalid <- is.na(genes) | !nzchar(genes)
  if (any(invalid)) {
    kda_abort("%s contains %d missing or blank identifier(s).", label, sum(invalid))
  }
  genes <- sort(unique(genes), method = "radix")
  if (!allow_empty && !length(genes)) {
    kda_abort("%s is empty.", label)
  }
  genes
}

network_nodes <- function(network) {
  sort(unique(c(network$from, network$to)), method = "radix")
}

network_is_dag <- function(network) {
  nodes <- network_nodes(network)
  indegree <- stats::setNames(integer(length(nodes)), nodes)
  incoming_counts <- table(network$to)
  indegree[names(incoming_counts)] <- as.integer(incoming_counts)
  outgoing <- split(network$to, network$from)
  queue <- nodes[indegree == 0L]
  visited <- 0L
  queue_index <- 1L
  while (queue_index <= length(queue)) {
    node <- queue[[queue_index]]
    queue_index <- queue_index + 1L
    visited <- visited + 1L
    children <- outgoing[[node]]
    if (!is.null(children)) {
      for (child in children) {
        indegree[[child]] <- indegree[[child]] - 1L
        if (indegree[[child]] == 0L) {
          queue <- c(queue, child)
        }
      }
    }
  }
  identical(visited, length(nodes))
}

validate_network <- function(network, require_dag = TRUE) {
  if (!is.data.frame(network) || ncol(network) != 2L) {
    kda_abort("Network must be a two-column data frame.")
  }
  if (!identical(names(network), c("from", "to"))) {
    kda_abort(
      "Network columns must be named exactly 'from' and 'to' so direction is unambiguous."
    )
  }
  network$from <- trimws(as.character(network$from))
  network$to <- trimws(as.character(network$to))
  if (nrow(network) &&
      tolower(network$from[[1L]]) %in% c("from", "source", "upstream", "regulator") &&
      tolower(network$to[[1L]]) %in% c("to", "target", "downstream", "gene")) {
    kda_abort("Network appears to contain a header row; the contract requires a headerless TSV.")
  }
  invalid <- is.na(network$from) | is.na(network$to) |
    !nzchar(network$from) | !nzchar(network$to)
  if (any(invalid)) {
    kda_abort("Network contains %d edge(s) with missing or blank identifiers.", sum(invalid))
  }
  duplicate_edges <- duplicated(network[c("from", "to")])
  if (any(duplicate_edges)) {
    example <- network[which(duplicate_edges)[1L], , drop = FALSE]
    kda_abort(
      "Network contains %d duplicate edge(s), for example %s -> %s.",
      sum(duplicate_edges),
      example$from,
      example$to
    )
  }
  self_edges <- network$from == network$to
  if (any(self_edges)) {
    kda_abort("Network contains %d self-edge(s).", sum(self_edges))
  }
  if (!nrow(network)) {
    kda_abort("Network contains no edges.")
  }
  if (isTRUE(require_dag) && !network_is_dag(network)) {
    kda_abort("Network contains a directed cycle; final Bayesian-network inputs must be DAGs.")
  }
  rownames(network) <- NULL
  network
}

validate_positive_integer <- function(value, label) {
  if (length(value) != 1L || is.na(value) || !is.finite(value) ||
      value <= 0 || value != as.integer(value)) {
    kda_abort("%s must be one positive integer; received: %s", label, paste(value, collapse = ", "))
  }
  as.integer(value)
}

validate_query_background <- function(query,
                                      background,
                                      nodes,
                                      minimum_effective_query_size = 3L,
                                      query_label = "query") {
  query <- normalize_gene_vector(query, sprintf("%s genes", query_label))
  background <- normalize_gene_vector(background, sprintf("%s background", query_label))
  nodes <- normalize_gene_vector(nodes, "network nodes")
  background_outside <- setdiff(background, nodes)
  if (length(background_outside)) {
    kda_abort(
      "%s background contains %d gene(s) absent from the network, including: %s",
      query_label,
      length(background_outside),
      paste(utils::head(background_outside, 10L), collapse = ", ")
    )
  }
  effective_query <- intersect(query, background)
  if (!all(effective_query %in% background)) {
    kda_abort("%s effective query is not a subset of its background.", query_label)
  }
  if (length(effective_query) < minimum_effective_query_size) {
    kda_abort(
      "%s has only %d effective network-mapped query genes; at least %d are required.",
      query_label,
      length(effective_query),
      minimum_effective_query_size
    )
  }
  coverage <- length(effective_query) / length(query)
  if (coverage < 0.5) {
    kda_warn(
      "%s has low network/background coverage: %d/%d genes (%.1f%%).",
      query_label,
      length(effective_query),
      length(query),
      100 * coverage
    )
  } else if (length(effective_query) < 10L) {
    kda_warn(
      "%s has a small effective query (%d genes); interpret enrichment cautiously.",
      query_label,
      length(effective_query)
    )
  }
  list(
    query = query,
    background = background,
    effective_query = effective_query,
    query_missing_from_background = setdiff(query, background),
    query_coverage = coverage
  )
}

validate_manifest <- function(manifest) {
  if (!is.data.frame(manifest)) {
    kda_abort("Run manifest must be a data frame.")
  }
  missing_columns <- setdiff(KDA_MANIFEST_REQUIRED_COLUMNS, names(manifest))
  if (length(missing_columns)) {
    kda_abort(
      "Run manifest is missing required column(s): %s",
      paste(missing_columns, collapse = ", ")
    )
  }
  if (!nrow(manifest)) {
    kda_abort("Run manifest has no rows.")
  }
  for (column in KDA_MANIFEST_REQUIRED_COLUMNS) {
    value <- trimws(as.character(manifest[[column]]))
    if (any(is.na(value) | !nzchar(value))) {
      kda_abort("Run manifest column '%s' contains missing or blank values.", column)
    }
    manifest[[column]] <- value
  }
  duplicate_ids <- unique(manifest$run_id[duplicated(manifest$run_id)])
  if (length(duplicate_ids)) {
    kda_abort(
      "Run manifest contains duplicate run_id value(s): %s",
      paste(utils::head(duplicate_ids, 10L), collapse = ", ")
    )
  }
  unsafe_ids <- manifest$run_id != vapply(manifest$run_id, safe_path_component, character(1L))
  if (any(unsafe_ids)) {
    kda_abort(
      "run_id values must already be safe path components; invalid example: %s",
      manifest$run_id[which(unsafe_ids)[1L]]
    )
  }
  unsafe_network_ids <- manifest$network_id !=
    vapply(manifest$network_id, safe_path_component, character(1L))
  if (any(unsafe_network_ids)) {
    kda_abort(
      "network_id values must already be safe path components; invalid example: %s",
      manifest$network_id[which(unsafe_network_ids)[1L]]
    )
  }
  manifest
}

validate_kda_raw_result <- function(result, allow_null = TRUE) {
  if (is.null(result)) {
    if (!isTRUE(allow_null)) {
      kda_abort("KDA returned no candidate drivers.")
    }
    return(NULL)
  }
  if (!is.list(result) || length(result) != 3L) {
    kda_abort("KDA returned a malformed object: expected a three-element list.")
  }
  drivers <- as.data.frame(result[[1L]], stringsAsFactors = FALSE)
  parameters <- as.data.frame(result[[2L]], stringsAsFactors = FALSE)
  downstream <- as.data.frame(result[[3L]], stringsAsFactors = FALSE)
  required_driver_columns <- c("keydrivers", "keydriver")
  missing_driver_columns <- setdiff(required_driver_columns, names(drivers))
  if (length(missing_driver_columns)) {
    kda_abort(
      "KDA driver result is missing required column(s): %s",
      paste(missing_driver_columns, collapse = ", ")
    )
  }
  if (!all(c("node", "downstream") %in% names(downstream))) {
    kda_abort("KDA downstream-count result must contain 'node' and 'downstream'.")
  }
  if (!nrow(drivers)) {
    kda_abort("KDA returned no candidate drivers.")
  }
  list(drivers = drivers, parameters = parameters, downstream = downstream)
}

expect_kda_error <- function(expression, pattern = NULL) {
  captured <- NULL
  tryCatch(
    force(expression),
    error = function(condition) {
      captured <<- condition
      invisible(NULL)
    }
  )
  if (is.null(captured)) {
    kda_abort("Expected an error, but the expression succeeded.")
  }
  if (!is.null(pattern) && !grepl(pattern, conditionMessage(captured), perl = TRUE)) {
    kda_abort(
      "Error did not match /%s/: %s",
      pattern,
      conditionMessage(captured)
    )
  }
  invisible(TRUE)
}
