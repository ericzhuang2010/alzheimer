# Shared, side-effect-free helpers for Phase 11 DEG pathway analyses.

`%||%` <- function(x, y) if (is.null(x)) y else x

phase11_must <- function(condition, message) {
  if (length(condition) != 1L || is.na(condition) || !condition) {
    stop(message, call. = FALSE)
  }
}

phase11_nonempty <- function(x) {
  !is.na(x) & nzchar(trimws(as.character(x)))
}

phase11_is_true <- function(x) {
  !is.na(x) & as.logical(x)
}

phase11_absolute_path <- function(path, root) {
  path <- as.character(path)
  ifelse(grepl("^/", path), path, file.path(root, path))
}

phase11_relative_path <- function(path, root) {
  vapply(as.character(path), function(one_path) {
    normalized <- normalizePath(one_path, mustWork = FALSE)
    project <- normalizePath(root, mustWork = TRUE)
    prefix <- paste0(project, .Platform$file.sep)
    if (startsWith(normalized, prefix)) {
      substring(normalized, nchar(prefix) + 1L)
    } else {
      normalized
    }
  }, character(1), USE.NAMES = FALSE)
}

phase11_sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  digest::digest(file = path, algo = "sha256", serialize = FALSE)
}

phase11_git_revision <- function(root) {
  result <- suppressWarnings(system2(
    "git", c("-C", root, "rev-parse", "HEAD"),
    stdout = TRUE, stderr = TRUE
  ))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) {
    return(NA_character_)
  }
  result[[1L]]
}

phase11_atomic_fwrite <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  gzip <- grepl("\\.gz$", path)
  tmp <- file.path(
    dirname(path),
    paste0(".", basename(path), ".tmp.", Sys.getpid(), if (gzip) ".plain" else "")
  )
  data.table::fwrite(
    x, tmp, sep = "\t", quote = FALSE, na = "NA", logical01 = FALSE
  )
  if (gzip) {
    status <- system2("gzip", c("-n", "-f", tmp))
    compressed <- paste0(tmp, ".gz")
    if (status != 0L || !file.exists(compressed)) {
      unlink(c(tmp, compressed))
      stop("Could not gzip temporary output for ", path, call. = FALSE)
    }
    tmp <- compressed
  }
  if (!file.rename(tmp, path)) {
    unlink(tmp)
    stop("Could not atomically write ", path, call. = FALSE)
  }
}

phase11_atomic_write_lines <- function(lines, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- file.path(
    dirname(path), paste0(".", basename(path), ".tmp.", Sys.getpid())
  )
  writeLines(lines, tmp, useBytes = TRUE)
  if (!file.rename(tmp, path)) {
    unlink(tmp)
    stop("Could not atomically write ", path, call. = FALSE)
  }
}

phase11_schema_ok <- function(x, schema) {
  nrow(x) > 0L && "schema_version" %in% names(x) &&
    all(x$schema_version == schema)
}

phase11_artifact_valid <- function(row, root) {
  path <- phase11_absolute_path(as.character(row$path), root)
  file.exists(path) &&
    identical(phase11_sha256_file(path), as.character(row$sha256)) &&
    as.numeric(file.info(path)$size) == as.numeric(row$bytes)
}

phase11_parse_mitocarta_source <- function(path) {
  raw <- data.table::as.data.table(readxl::read_excel(
    path, sheet = "C MitoPathways", col_types = "text"
  ))
  required <- c("MitoPathway", "MitoPathways Hierarchy", "Genes")
  phase11_must(
    all(required %in% names(raw)),
    "MitoCarta pathway sheet columns changed"
  )
  raw <- raw[phase11_nonempty(MitoPathway)]
  phase11_must(nrow(raw) > 0L, "MitoCarta pathway source has no pathways")
  phase11_must(!anyDuplicated(raw$MitoPathway), "MitoCarta pathway IDs are duplicated")

  metadata <- vector("list", nrow(raw))
  memberships <- vector("list", nrow(raw))
  for (i in seq_len(nrow(raw))) {
    pathway <- trimws(raw$MitoPathway[[i]])
    hierarchy <- trimws(raw[["MitoPathways Hierarchy"]][[i]])
    parts <- trimws(strsplit(hierarchy, ">", fixed = TRUE)[[1L]])
    parts <- parts[phase11_nonempty(parts)]
    genes <- trimws(strsplit(raw$Genes[[i]], ",", fixed = TRUE)[[1L]])
    genes <- unique(genes[phase11_nonempty(genes)])
    depth <- length(parts)
    metadata[[i]] <- data.table::data.table(
      source_pathway_order = as.integer(i),
      pathway_id = pathway,
      pathway_name = pathway,
      description = hierarchy,
      hierarchy = hierarchy,
      hierarchy_depth = as.integer(depth),
      level_1 = if (depth >= 1L) parts[[1L]] else NA_character_,
      level_2 = if (depth >= 2L) parts[[2L]] else NA_character_,
      level_3_or_deeper = if (depth >= 3L) {
        paste(parts[3:depth], collapse = " > ")
      } else {
        NA_character_
      },
      parent_pathway = if (depth >= 2L) parts[[depth - 1L]] else NA_character_,
      pathway_scope = if (depth <= 2L) "broad_program" else "detailed_program",
      source_pathway_size = length(genes)
    )
    memberships[[i]] <- data.table::data.table(
      source_pathway_order = as.integer(i),
      source_gene_order = seq_along(genes),
      pathway_id = pathway,
      symbol_hgnc_current = genes
    )
  }
  list(
    metadata = data.table::rbindlist(metadata),
    membership = data.table::rbindlist(memberships)
  )
}

phase11_build_program_collections <- function(legacy, mitocarta, config) {
  module_labels <- c(
    mtdna_oxphos_13 = "mtDNA-encoded OXPHOS",
    nuclear_oxphos_structural_86 = "Nuclear structural OXPHOS",
    mitochondrial_translation_155 = "Mitochondrial translation",
    mib_micos_inner_membrane_19 = "MIB/MICOS inner membrane"
  )
  legacy_meta <- unique(legacy[, .(module_order, module_id)])
  legacy_meta[, `:=`(
    pathway_collection = "legacy_four",
    collection_order = 1L,
    collection_role = "compatibility_benchmark",
    pathway_id = module_id,
    pathway_name = unname(module_labels[module_id]),
    description = "Frozen respiratory/mitochondrial program benchmark",
    hierarchy = NA_character_,
    hierarchy_depth = NA_integer_,
    level_1 = NA_character_,
    level_2 = NA_character_,
    level_3_or_deeper = NA_character_,
    parent_pathway = NA_character_,
    pathway_scope = "legacy_module",
    source_pathway_order = as.integer(module_order)
  )]
  legacy_sizes <- legacy[
    , .(source_pathway_size = data.table::uniqueN(current_approved_symbol)),
    by = module_id
  ]
  legacy_meta <- merge(
    legacy_meta, legacy_sizes, by = "module_id", all.x = TRUE, sort = FALSE
  )
  legacy_meta[, module_id := NULL]
  legacy_members <- unique(legacy[, .(
    pathway_collection = "legacy_four",
    pathway_id = module_id,
    symbol_hgnc_current = current_approved_symbol
  )])

  make_mitocarta_collection <- function(id, role, order, depths) {
    meta <- data.table::copy(mitocarta$metadata[hierarchy_depth %in% depths])
    meta[, `:=`(
      pathway_collection = id,
      collection_order = as.integer(order),
      collection_role = role
    )]
    members <- merge(
      mitocarta$membership,
      meta[, .(pathway_id)],
      by = "pathway_id", all = FALSE
    )
    members[, pathway_collection := id]
    members <- members[, .(
      pathway_collection, pathway_id, symbol_hgnc_current
    )]
    list(metadata = meta, membership = members)
  }

  broad <- make_mitocarta_collection(
    "mitocarta_broad_46", "primary_expanded", 2L, c(1L, 2L)
  )
  complete <- make_mitocarta_collection(
    "mitocarta_complete_149", "supplemental_complete", 3L, c(1L, 2L, 3L)
  )
  metadata <- data.table::rbindlist(
    list(legacy_meta, broad$metadata, complete$metadata),
    use.names = TRUE, fill = TRUE
  )
  membership <- data.table::rbindlist(
    list(legacy_members, broad$membership, complete$membership),
    use.names = TRUE
  )
  metadata[, schema_version := config$schemas$program_manifest]
  data.table::setcolorder(metadata, c(
    "schema_version", "pathway_collection", "collection_order",
    "collection_role", "pathway_id", "pathway_name", "description",
    "source_pathway_order", "source_pathway_size", "hierarchy",
    "hierarchy_depth", "level_1", "level_2", "level_3_or_deeper",
    "parent_pathway", "pathway_scope"
  ))
  data.table::setorder(metadata, collection_order, source_pathway_order)
  data.table::setorder(
    membership, pathway_collection, pathway_id, symbol_hgnc_current
  )
  list(metadata = metadata, membership = membership)
}

phase11_ora_probability <- function(k, M, N, n) {
  stats::phyper(
    q = k - 1L, m = M, n = N - M, k = n, lower.tail = FALSE
  )
}

phase11_program_testability <- function(
    collection, available, n, N, M, reference_coverage,
    minimum_query_size = 3L, minimum_members = 5L,
    minimum_reference_coverage = 0.30) {
  if (!available) return("contrast_not_estimable")
  if (N <= 0L) return("empty_background")
  if (n == 0L) return("empty_query")
  if (n < minimum_query_size) return("query_below_minimum")
  if (identical(collection, "legacy_four")) return("tested")
  if (M < minimum_members) return("below_minimum_background_members")
  if (M >= N) return("pathway_spans_entire_background")
  if (reference_coverage < minimum_reference_coverage) {
    return("below_minimum_reference_coverage")
  }
  "tested"
}

phase11_apply_fdr <- function(
    results, local_columns, global_columns,
    method = "BH", threshold = 0.05) {
  results[, `:=`(
    local_fdr_bh = NA_real_,
    local_fdr_family_size = NA_integer_,
    local_fdr_significant = FALSE,
    global_fdr_bh = NA_real_,
    global_fdr_family_size = NA_integer_,
    global_fdr_significant = FALSE
  )]
  results[test_status == "tested", `:=`(
    local_fdr_bh = stats::p.adjust(p_value, method = method),
    local_fdr_family_size = .N
  ), by = local_columns]
  results[test_status == "tested", `:=`(
    global_fdr_bh = stats::p.adjust(p_value, method = method),
    global_fdr_family_size = .N
  ), by = global_columns]
  results[test_status == "tested", `:=`(
    local_fdr_significant = local_fdr_bh < threshold,
    global_fdr_significant = global_fdr_bh < threshold
  )]
  results
}

phase11_run_ora <- function(
    query_manifest, query_genes, background_genes,
    program_manifest, program_membership, config, schema) {
  query_lists <- split(
    query_genes$symbol_hgnc_current, query_genes$query_id
  )
  background_lists <- split(
    background_genes$symbol_hgnc_current, background_genes$background_id
  )
  query_gene_tables <- split(query_genes, query_genes$query_id)
  membership_keys <- paste(
    program_membership$pathway_collection,
    program_membership$pathway_id,
    sep = "\r"
  )
  membership_lists <- split(
    program_membership$symbol_hgnc_current, membership_keys
  )
  collection_ids <- unique(program_manifest$pathway_collection)
  rows <- vector("list", nrow(query_manifest) * length(collection_ids))
  row_index <- 0L

  for (i in seq_len(nrow(query_manifest))) {
    query <- query_manifest[i]
    query_id <- as.character(query$query_id)
    background_id <- as.character(query$background_id)
    query_symbols <- unique(query_lists[[query_id]] %||% character())
    background_symbols <- unique(
      background_lists[[background_id]] %||% character()
    )
    query_table <- query_gene_tables[[query_id]]
    N <- length(background_symbols)
    n <- length(query_symbols)
    available <- isTRUE(query$structurally_available)

    for (collection in collection_ids) {
      row_index <- row_index + 1L
      meta <- program_manifest[pathway_collection == collection]
      keys <- paste(collection, meta$pathway_id, sep = "\r")
      members <- membership_lists[keys]
      background_members <- lapply(
        members, function(x) x[x %chin% background_symbols]
      )
      overlaps <- lapply(
        members, function(x) sort(x[x %chin% query_symbols])
      )
      M <- lengths(background_members)
      k <- lengths(overlaps)
      coverage <- M / meta$source_pathway_size
      reasons <- vapply(seq_len(nrow(meta)), function(j) {
        phase11_program_testability(
          collection = collection,
          available = available,
          n = n, N = N, M = M[[j]],
          reference_coverage = coverage[[j]],
          minimum_query_size = as.integer(config$analysis$minimum_query_size),
          minimum_members = as.integer(
            config$analysis$minimum_background_pathway_members
          ),
          minimum_reference_coverage = as.numeric(
            config$analysis$minimum_reference_coverage
          )
        )
      }, character(1))
      tested <- reasons == "tested"
      p_value <- rep(NA_real_, nrow(meta))
      p_value[tested] <- phase11_ora_probability(
        k[tested], M[tested], N, n
      )
      overlap_genes <- vapply(
        overlaps,
        function(x) if (length(x)) paste(x, collapse = ",") else "",
        character(1)
      )
      overlap_up <- integer(length(overlaps))
      overlap_down <- integer(length(overlaps))
      if (!is.null(query_table) && nrow(query_table)) {
        up <- query_table[
          phase11_is_true(in_upregulated_query), symbol_hgnc_current
        ]
        down <- query_table[
          phase11_is_true(in_downregulated_query), symbol_hgnc_current
        ]
        overlap_up <- lengths(lapply(overlaps, intersect, y = up))
        overlap_down <- lengths(lapply(overlaps, intersect, y = down))
      }

      strict_reason <- ifelse(
        n < as.integer(config$analysis$minimum_query_size),
        ifelse(n == 0L, "empty_query", "query_below_minimum"),
        ifelse(
          M < as.integer(config$analysis$minimum_background_pathway_members),
          "below_minimum_background_members",
          ifelse(
            M >= N, "pathway_spans_entire_background",
            ifelse(
              coverage < as.numeric(config$analysis$minimum_reference_coverage),
              "below_minimum_reference_coverage", "tested"
            )
          )
        )
      )
      rows[[row_index]] <- data.table::data.table(
        schema_version = schema,
        analysis_profile = "thresholded_ora",
        query_order = as.integer(query$query_order),
        query_id = query_id,
        background_id = background_id,
        contrast_id = as.character(query$contrast_id),
        broad_cell_type = as.character(query$broad_cell_type),
        sex = as.character(query$sex),
        apoe_group = as.character(query$apoe_group),
        deg_tier = as.character(query$deg_tier),
        query_mode = as.character(query$query_mode),
        structural_status = as.character(query$structural_status),
        structurally_available = available,
        pathway_collection = collection,
        collection_order = as.integer(meta$collection_order),
        collection_role = as.character(meta$collection_role),
        pathway_id = as.character(meta$pathway_id),
        pathway_name = as.character(meta$pathway_name),
        description = as.character(meta$description),
        source_pathway_order = as.integer(meta$source_pathway_order),
        hierarchy = as.character(meta$hierarchy),
        hierarchy_depth = as.integer(meta$hierarchy_depth),
        level_1 = as.character(meta$level_1),
        level_2 = as.character(meta$level_2),
        level_3_or_deeper = as.character(meta$level_3_or_deeper),
        parent_pathway = as.character(meta$parent_pathway),
        pathway_scope = as.character(meta$pathway_scope),
        source_pathway_size = as.integer(meta$source_pathway_size),
        background_pathway_size = as.integer(M),
        background_size = as.integer(N),
        query_size = as.integer(n),
        overlap_count = as.integer(k),
        overlap_up_count = as.integer(overlap_up),
        overlap_down_count = as.integer(overlap_down),
        query_in_pathway = as.integer(k),
        query_not_in_pathway = as.integer(n - k),
        background_outside_query_in_pathway = as.integer(M - k),
        background_outside_query_not_in_pathway =
          as.integer(N - M - n + k),
        reference_coverage = as.numeric(coverage),
        gene_ratio = if (n > 0L) k / n else NA_real_,
        background_ratio = if (N > 0L) M / N else NA_real_,
        fold_enrichment = ifelse(
          n > 0L & M > 0L, (k / n) / (M / N), NA_real_
        ),
        pathway_hit_rate = ifelse(M > 0L, k / M, NA_real_),
        test_status = ifelse(tested, "tested", "not_testable"),
        testability_reason = reasons,
        strict_testability_reason = strict_reason,
        small_pathway_status = ifelse(
          tested &
            M <= as.integer(config$analysis$small_pathway_upper_bound),
          "small_pathway_lower_confidence",
          ifelse(tested, "standard_pathway_size", "not_testable")
        ),
        p_value = p_value,
        overlap_genes = overlap_genes
      )
    }
  }

  result <- data.table::rbindlist(rows[seq_len(row_index)], fill = TRUE)
  result <- phase11_apply_fdr(
    result,
    local_columns = c(
      "contrast_id", "deg_tier", "query_mode", "pathway_collection"
    ),
    global_columns = c("deg_tier", "query_mode", "pathway_collection"),
    method = as.character(config$fdr$method),
    threshold = as.numeric(config$fdr$threshold)
  )
  result[, query_significant_pathways := sum(local_fdr_significant), by = .(
    query_id, pathway_collection
  )]
  result[, status_order := data.table::fifelse(
    test_status == "tested", 0L, 1L
  )]
  data.table::setorderv(
    result,
    c(
      "query_order", "collection_order", "status_order",
      "local_fdr_bh", "p_value", "overlap_count", "source_pathway_order"
    ),
    c(1L, 1L, 1L, 1L, 1L, -1L, 1L),
    na.last = TRUE
  )
  result[, statistical_order := seq_len(.N), by = .(
    query_id, pathway_collection
  )]
  result[, status_order := NULL]
  result
}

phase11_seed_from_id <- function(id, base_seed) {
  value <- digest::digest(
    as.character(id), algo = "xxhash32", serialize = FALSE
  )
  hash_part <- strtoi(substr(value, 1L, 7L), base = 16L)
  as.integer((as.double(hash_part) + as.double(base_seed)) %% 2147483646 + 1)
}

phase11_gsea_reason <- function(
    collection, available, rank_size, pathway_size, source_size,
    minimum_members, minimum_coverage) {
  if (!available) return("contrast_not_estimable")
  if (rank_size <= 0L) return("empty_rank")
  if (pathway_size < minimum_members) {
    return("below_minimum_rank_members")
  }
  if (pathway_size >= rank_size) return("pathway_spans_entire_rank")
  coverage <- pathway_size / source_size
  if (!identical(collection, "legacy_four") &&
      coverage < minimum_coverage) {
    return("below_minimum_reference_coverage")
  }
  "tested"
}

phase11_run_gsea_collection <- function(
    rank_manifest, ranked_genes, program_manifest, program_membership,
    collection, config, schema, profile) {
  meta <- program_manifest[pathway_collection == collection]
  members <- program_membership[pathway_collection == collection]
  membership_lists <- split(
    members$symbol_hgnc_current, members$pathway_id
  )
  rank_tables <- split(ranked_genes, ranked_genes$rank_id)
  rows <- vector("list", nrow(rank_manifest))

  for (i in seq_len(nrow(rank_manifest))) {
    rank <- rank_manifest[i]
    rank_id <- as.character(rank$rank_id)
    table <- rank_tables[[rank_id]]
    available <- isTRUE(rank$structurally_available)
    if (is.null(table)) {
      table <- data.table::data.table(
        symbol_hgnc_current = character(), rank_score = numeric()
      )
    }
    stats <- table$rank_score
    names(stats) <- table$symbol_hgnc_current
    stats <- stats[is.finite(stats) & phase11_nonempty(names(stats))]
    rank_size <- length(stats)
    intersections <- lapply(
      membership_lists[meta$pathway_id],
      function(x) sort(intersect(x, names(stats)))
    )
    pathway_sizes <- lengths(intersections)
    coverage <- pathway_sizes / meta$source_pathway_size
    reasons <- vapply(seq_len(nrow(meta)), function(j) {
      phase11_gsea_reason(
        collection = collection,
        available = available,
        rank_size = rank_size,
        pathway_size = pathway_sizes[[j]],
        source_size = meta$source_pathway_size[[j]],
        minimum_members = as.integer(config$gsea$minimum_pathway_size),
        minimum_coverage = as.numeric(config$gsea$minimum_reference_coverage)
      )
    }, character(1))
    if (!available) {
      reasons[] <- as.character(rank$structural_status)
    }
    tested <- reasons == "tested"

    raw_result <- data.table::data.table()
    if (any(tested)) {
      eligible <- membership_lists[meta$pathway_id[tested]]
      eligible <- lapply(eligible, intersect, y = names(stats))
      stats <- sort(stats, decreasing = TRUE)
      set.seed(phase11_seed_from_id(
        paste(profile, rank$contrast_id, sep = "::"),
        as.integer(config$gsea$seed_base)
      ))
      raw_result <- suppressWarnings(data.table::as.data.table(
        fgsea::fgseaMultilevel(
          pathways = eligible,
          stats = stats,
          minSize = as.integer(config$gsea$minimum_pathway_size),
          maxSize = max(1L, rank_size - 1L),
          eps = as.numeric(config$gsea$eps),
          scoreType = "std",
          nproc = as.integer(config$gsea$workers),
          sampleSize = as.integer(config$gsea$sample_size),
          gseaParam = as.numeric(config$gsea$exponent)
        )
      ))
    }

    raw_by_pathway <- split(raw_result, raw_result$pathway)
    values <- lapply(seq_len(nrow(meta)), function(j) {
      hit <- raw_by_pathway[[meta$pathway_id[[j]]]]
      if (!tested[[j]] || is.null(hit) || !nrow(hit)) {
        return(list(
          enrichment_score = NA_real_,
          normalized_enrichment_score = NA_real_,
          p_value = NA_real_,
          log2_error = NA_real_,
          leading_edge_genes = "",
          leading_edge_count = 0L,
          fgsea_reported_size = NA_integer_
        ))
      }
      leading <- sort(unique(as.character(hit$leadingEdge[[1L]])))
      list(
        enrichment_score = as.numeric(hit$ES[[1L]]),
        normalized_enrichment_score = as.numeric(hit$NES[[1L]]),
        p_value = as.numeric(hit$pval[[1L]]),
        log2_error = as.numeric(hit$log2err[[1L]]),
        leading_edge_genes = paste(leading, collapse = ","),
        leading_edge_count = length(leading),
        fgsea_reported_size = as.integer(hit$size[[1L]])
      )
    })
    value_table <- data.table::rbindlist(values)
    rows[[i]] <- cbind(
      data.table::data.table(
        schema_version = schema,
        analysis_profile = profile,
        rank_order = as.integer(rank$rank_order),
        rank_id = rank_id,
        contrast_id = as.character(rank$contrast_id),
        broad_cell_type = as.character(rank$broad_cell_type),
        sex = as.character(rank$sex),
        apoe_group = as.character(rank$apoe_group),
        structural_status = as.character(rank$structural_status),
        structurally_available = available,
        rank_size = as.integer(rank_size),
        pathway_collection = collection,
        collection_order = as.integer(meta$collection_order),
        collection_role = as.character(meta$collection_role),
        pathway_id = as.character(meta$pathway_id),
        pathway_name = as.character(meta$pathway_name),
        description = as.character(meta$description),
        source_pathway_order = as.integer(meta$source_pathway_order),
        hierarchy = as.character(meta$hierarchy),
        hierarchy_depth = as.integer(meta$hierarchy_depth),
        level_1 = as.character(meta$level_1),
        level_2 = as.character(meta$level_2),
        level_3_or_deeper = as.character(meta$level_3_or_deeper),
        parent_pathway = as.character(meta$parent_pathway),
        pathway_scope = as.character(meta$pathway_scope),
        source_pathway_size = as.integer(meta$source_pathway_size),
        rank_pathway_size = as.integer(pathway_sizes),
        reference_coverage = as.numeric(coverage),
        test_status = ifelse(tested, "tested", "not_testable"),
        testability_reason = reasons
      ),
      value_table
    )
  }
  result <- data.table::rbindlist(rows, fill = TRUE)
  result[, gsea_direction := data.table::fifelse(
    is.na(normalized_enrichment_score), "not_testable",
    data.table::fifelse(
      normalized_enrichment_score > 0, "AD_up",
      data.table::fifelse(
        normalized_enrichment_score < 0, "AD_down", "neutral"
      )
    )
  )]
  result[, leading_edge_confidence := data.table::fifelse(
    test_status != "tested", "not_testable",
    data.table::fifelse(
      leading_edge_count <= 1L,
      as.character(config$gsea$single_leading_edge_label),
      "multiple_leading_edge_genes"
    )
  )]
  result
}

phase11_derive_broad_gsea <- function(
    complete_results, program_manifest, schema) {
  broad_meta <- program_manifest[pathway_collection == "mitocarta_broad_46"]
  result <- merge(
    complete_results[pathway_id %in% broad_meta$pathway_id],
    broad_meta[, .(
      pathway_id,
      broad_collection_order = collection_order,
      broad_collection_role = collection_role
    )],
    by = "pathway_id", all.x = TRUE, sort = FALSE
  )
  result[, `:=`(
    schema_version = schema,
    pathway_collection = "mitocarta_broad_46",
    collection_order = as.integer(broad_collection_order),
    collection_role = broad_collection_role
  )]
  result[, c("broad_collection_order", "broad_collection_role") := NULL]
  result
}

phase11_finalize_gsea <- function(results, config) {
  results <- phase11_apply_fdr(
    results,
    local_columns = c("contrast_id", "pathway_collection"),
    global_columns = c("pathway_collection"),
    method = as.character(config$fdr$method),
    threshold = as.numeric(config$fdr$threshold)
  )
  results[, rank_significant_pathways := sum(local_fdr_significant), by = .(
    rank_id, pathway_collection
  )]
  results[, status_order := data.table::fifelse(
    test_status == "tested", 0L, 1L
  )]
  data.table::setorderv(
    results,
    c(
      "rank_order", "collection_order", "status_order",
      "local_fdr_bh", "p_value", "source_pathway_order"
    ),
    c(1L, 1L, 1L, 1L, 1L, 1L),
    na.last = TRUE
  )
  results[, statistical_order := seq_len(.N), by = .(
    rank_id, pathway_collection
  )]
  results[, status_order := NULL]
  results
}

phase11_split_genes <- function(x) {
  values <- unlist(
    strsplit(x[phase11_nonempty(x)], ",", fixed = TRUE),
    use.names = FALSE
  )
  unique(values[phase11_nonempty(values)])
}

phase11_recurrence_fields <- function(strings, selected) {
  values <- strings[selected %in% TRUE & phase11_nonempty(strings)]
  if (!length(values)) {
    return(list(
      gene_union = "",
      gene_union_count = 0L,
      recurrent_genes = "",
      recurrent_gene_count = 0L
    ))
  }
  all_genes <- unlist(lapply(values, phase11_split_genes), use.names = FALSE)
  counts <- table(all_genes)
  union <- sort(names(counts))
  recurrent <- sort(names(counts)[counts >= 2L])
  list(
    gene_union = paste(union, collapse = ","),
    gene_union_count = length(union),
    recurrent_genes = paste(recurrent, collapse = ","),
    recurrent_gene_count = length(recurrent)
  )
}

phase11_compute_redundancy_map <- function(
    program_manifest, program_membership, schema, threshold = 0.25) {
  meta <- program_manifest[
    pathway_collection == "mitocarta_complete_149"
  ]
  members <- program_membership[
    pathway_collection == "mitocarta_complete_149"
  ]
  member_lists <- split(members$symbol_hgnc_current, members$pathway_id)
  pairs <- utils::combn(seq_len(nrow(meta)), 2L)
  rows <- lapply(seq_len(ncol(pairs)), function(i) {
    a <- meta[pairs[1L, i]]
    b <- meta[pairs[2L, i]]
    a_genes <- member_lists[[a$pathway_id]]
    b_genes <- member_lists[[b$pathway_id]]
    shared <- sort(intersect(a_genes, b_genes))
    union_size <- length(union(a_genes, b_genes))
    a_ancestor <- phase11_nonempty(a$hierarchy) &&
      phase11_nonempty(b$hierarchy) &&
      startsWith(b$hierarchy, paste0(a$hierarchy, " > "))
    b_ancestor <- phase11_nonempty(a$hierarchy) &&
      phase11_nonempty(b$hierarchy) &&
      startsWith(a$hierarchy, paste0(b$hierarchy, " > "))
    direct_parent <- identical(
      as.character(b$parent_pathway), as.character(a$pathway_id)
    ) || identical(
      as.character(a$parent_pathway), as.character(b$pathway_id)
    )
    relationship <- if (direct_parent) {
      "direct_parent_child"
    } else if (a_ancestor || b_ancestor) {
      "ancestor_descendant"
    } else if (identical(
      as.character(a$level_1), as.character(b$level_1)
    )) {
      "same_top_level_system"
    } else {
      "different_top_level_system"
    }
    jaccard <- if (union_size > 0L) length(shared) / union_size else 0
    data.table::data.table(
      schema_version = schema,
      pathway_a = as.character(a$pathway_id),
      pathway_b = as.character(b$pathway_id),
      pathway_a_depth = as.integer(a$hierarchy_depth),
      pathway_b_depth = as.integer(b$hierarchy_depth),
      pathway_a_size = length(a_genes),
      pathway_b_size = length(b_genes),
      intersection_size = length(shared),
      union_size = union_size,
      jaccard_similarity = jaccard,
      shared_genes = paste(shared, collapse = ","),
      hierarchy_relationship = relationship,
      same_top_level_system = identical(
        as.character(a$level_1), as.character(b$level_1)
      ),
      redundancy_candidate = jaccard >= threshold ||
        relationship %in% c("direct_parent_child", "ancestor_descendant"),
      representative_jaccard_threshold = threshold
    )
  })
  result <- data.table::rbindlist(rows)
  data.table::setorder(
    result, -redundancy_candidate, -jaccard_similarity,
    pathway_a, pathway_b
  )
  result
}
