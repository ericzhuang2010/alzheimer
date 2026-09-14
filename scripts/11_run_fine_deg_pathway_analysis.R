#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    config = NULL, execution_config = NULL, task_mode = NULL,
    force = FALSE
  )
  value_options <- c("--config", "--execution-config", "--task-mode")
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/11_run_fine_deg_pathway_analysis.R ",
        "--config FILE --execution-config FILE ",
        "--task-mode pathway_deg_fine [--force]\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (key == "--force") {
      out$force <- TRUE
      i <- i + 1L
      next
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    name <- gsub("-", "_", sub("^--", "", key))
    out[[name]] <- args[[i + 1L]]
    i <- i + 2L
  }
  required <- c("config", "execution_config", "task_mode")
  missing <- required[vapply(out[required], is.null, logical(1))]
  if (length(missing)) {
    stop("Missing required options: ", paste(missing, collapse = ", "), call. = FALSE)
  }
  if (!identical(out$task_mode, "pathway_deg_fine")) {
    stop("--task-mode must be pathway_deg_fine", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

relative_path <- function(path, root) {
  normalized <- normalizePath(path, mustWork = FALSE)
  root <- normalizePath(root, mustWork = TRUE)
  prefix <- paste0(root, .Platform$file.sep)
  if (startsWith(normalized, prefix)) {
    substring(normalized, nchar(prefix) + 1L)
  } else {
    normalized
  }
}

must <- function(condition, message) {
  if (length(condition) != 1L || is.na(condition) || !condition) {
    stop(message, call. = FALSE)
  }
}

nonempty <- function(x) {
  !is.na(x) & nzchar(trimws(as.character(x)))
}

is_true <- function(x) {
  !is.na(x) & as.logical(x)
}

collapse_values <- function(x, separator = ",") {
  values <- unique(as.character(x[nonempty(x)]))
  if (length(values)) paste(values, collapse = separator) else ""
}

split_gene_string <- function(x) {
  values <- unlist(strsplit(x[nonempty(x)], ",", fixed = TRUE), use.names = FALSE)
  unique(values[nonempty(values)])
}

sha256_file <- function(path) {
  if (!file.exists(path)) return(NA_character_)
  digest::digest(file = path, algo = "sha256", serialize = FALSE)
}

git_revision <- function(root) {
  result <- suppressWarnings(system2(
    "git", c("-C", root, "rev-parse", "HEAD"),
    stdout = TRUE, stderr = TRUE
  ))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) return(NA_character_)
  result[[1L]]
}

peak_ram_gib <- function() {
  path <- "/proc/self/status"
  if (!file.exists(path)) return(NA_real_)
  lines <- readLines(path, warn = FALSE)
  value <- sub(
    "^VmHWM:[[:space:]]+([0-9]+)[[:space:]]+kB.*$", "\\1",
    grep("^VmHWM:", lines, value = TRUE)
  )
  if (!length(value)) return(NA_real_)
  as.numeric(value[[1L]]) / 1024^2
}

atomic_fwrite <- function(x, path) {
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
    stop("Could not atomically write ", path, call. = FALSE)
  }
}

atomic_write_lines <- function(lines, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- file.path(dirname(path), paste0(".", basename(path), ".tmp.", Sys.getpid()))
  writeLines(lines, tmp, useBytes = TRUE)
  if (!file.rename(tmp, path)) {
    stop("Could not atomically write ", path, call. = FALSE)
  }
}

schema_ok <- function(x, schema) {
  nrow(x) > 0L && "schema_version" %in% names(x) &&
    all(x$schema_version == schema)
}

ora_probability <- function(k, M, N, n) {
  stats::phyper(
    q = k - 1L, m = M, n = N - M, k = n, lower.tail = FALSE
  )
}

program_testability <- function(
    collection, query_available, n, N, M, reference_coverage,
    minimum_query_size = 3L, minimum_members = 5L,
    minimum_reference_coverage = 0.30) {
  if (!query_available) return("contrast_not_estimable")
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

apply_bh_families <- function(
    ora, global_columns, method = "BH", threshold = 0.05) {
  ora[, `:=`(
    local_fdr_bh = NA_real_,
    local_fdr_family_size = NA_integer_,
    local_fdr_significant = FALSE,
    global_fdr_bh = NA_real_,
    global_fdr_family_size = NA_integer_,
    global_fdr_significant = FALSE
  )]
  ora[test_status == "tested", `:=`(
    local_fdr_bh = stats::p.adjust(p_value, method = method),
    local_fdr_family_size = .N
  ), by = .(query_id, pathway_collection)]
  ora[test_status == "tested", `:=`(
    global_fdr_bh = stats::p.adjust(p_value, method = method),
    global_fdr_family_size = .N
  ), by = global_columns]
  ora[test_status == "tested", `:=`(
    local_fdr_significant = local_fdr_bh < threshold,
    global_fdr_significant = global_fdr_bh < threshold
  )]
  ora
}

parse_mitocarta_source <- function(path) {
  raw <- data.table::as.data.table(readxl::read_excel(
    path, sheet = "C MitoPathways", col_types = "text"
  ))
  required <- c("MitoPathway", "MitoPathways Hierarchy", "Genes")
  must(all(required %in% names(raw)), "MitoCarta pathway sheet columns changed")
  raw <- raw[nonempty(MitoPathway)]
  must(nrow(raw) > 0L, "MitoCarta pathway source has no pathways")
  must(!anyDuplicated(raw$MitoPathway), "MitoCarta pathway IDs are duplicated")
  metadata <- vector("list", nrow(raw))
  memberships <- vector("list", nrow(raw))
  for (i in seq_len(nrow(raw))) {
    pathway <- trimws(raw$MitoPathway[[i]])
    hierarchy <- trimws(raw[["MitoPathways Hierarchy"]][[i]])
    parts <- trimws(strsplit(hierarchy, ">", fixed = TRUE)[[1L]])
    parts <- parts[nonempty(parts)]
    genes <- trimws(strsplit(raw$Genes[[i]], ",", fixed = TRUE)[[1L]])
    genes <- unique(genes[nonempty(genes)])
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

build_program_collections <- function(legacy, mitocarta, config) {
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
  data.table::setorder(
    metadata, collection_order, source_pathway_order
  )
  data.table::setorder(
    membership, pathway_collection, pathway_id, symbol_hgnc_current
  )
  list(metadata = metadata, membership = membership)
}

run_ora <- function(
    query_manifest, query_genes, background_genes,
    program_manifest, program_membership, config,
    schema, profile, global_columns) {
  query_lists <- split(
    query_genes$symbol_hgnc_current, query_genes$query_id
  )
  background_lists <- split(
    background_genes$symbol_hgnc_current, background_genes$background_id
  )
  query_gene_tables <- split(query_genes, query_genes$query_id)
  keys <- paste(
    program_membership$pathway_collection,
    program_membership$pathway_id,
    sep = "\r"
  )
  membership_lists <- split(program_membership$symbol_hgnc_current, keys)
  collection_ids <- unique(program_manifest$pathway_collection)
  rows <- vector("list", nrow(query_manifest) * length(collection_ids))
  row_index <- 0L
  analysis_cfg <- config$analysis

  for (i in seq_len(nrow(query_manifest))) {
    query <- query_manifest[i]
    query_id <- as.character(query$query_id)
    background_id <- as.character(query$background_id)
    query_symbols <- unique(query_lists[[query_id]] %||% character())
    background_symbols <- unique(background_lists[[background_id]] %||% character())
    query_table <- query_gene_tables[[query_id]]
    N <- length(background_symbols)
    n <- length(query_symbols)
    query_available <- isTRUE(query$structurally_available)
    for (collection in collection_ids) {
      row_index <- row_index + 1L
      meta <- program_manifest[pathway_collection == collection]
      member_keys <- paste(collection, meta$pathway_id, sep = "\r")
      members <- membership_lists[member_keys]
      background_members <- lapply(
        members, function(x) x[x %chin% background_symbols]
      )
      overlaps <- lapply(
        members, function(x) x[x %chin% query_symbols]
      )
      M <- lengths(background_members)
      k <- lengths(overlaps)
      coverage <- M / meta$source_pathway_size
      reasons <- vapply(seq_len(nrow(meta)), function(j) {
        program_testability(
          collection = collection,
          query_available = query_available,
          n = n, N = N, M = M[[j]],
          reference_coverage = coverage[[j]],
          minimum_query_size = as.integer(analysis_cfg$minimum_query_size),
          minimum_members = as.integer(
            analysis_cfg$minimum_background_pathway_members
          ),
          minimum_reference_coverage = as.numeric(
            analysis_cfg$minimum_reference_coverage
          )
        )
      }, character(1))
      tested <- reasons == "tested"
      p_value <- rep(NA_real_, nrow(meta))
      p_value[tested] <- ora_probability(
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
        up_symbols <- query_table[is_true(in_upregulated_query), symbol_hgnc_current]
        down_symbols <- query_table[is_true(in_downregulated_query), symbol_hgnc_current]
        overlap_up <- lengths(lapply(overlaps, intersect, y = up_symbols))
        overlap_down <- lengths(lapply(overlaps, intersect, y = down_symbols))
      }
      strict_reason <- ifelse(
        n < as.integer(analysis_cfg$minimum_query_size),
        ifelse(n == 0L, "empty_query", "query_below_minimum"),
        ifelse(
          M < as.integer(analysis_cfg$minimum_background_pathway_members),
          "below_minimum_background_members",
          ifelse(
            M >= N, "pathway_spans_entire_background",
            ifelse(
              coverage < as.numeric(analysis_cfg$minimum_reference_coverage),
              "below_minimum_reference_coverage", "tested"
            )
          )
        )
      )
      rows[[row_index]] <- data.table::data.table(
        schema_version = schema,
        analysis_profile = profile,
        query_order = as.integer(query$query_order),
        query_id = query_id,
        background_id = background_id,
        contrast_id = as.character(query$contrast_id),
        kda_run_id = as.character(query$kda_run_id),
        rds_id = as.character(query$rds_id),
        fine_cell_type = as.character(query$fine_cell_type),
        broad_cell_type = as.character(query$broad_cell_type),
        signature_group = as.character(query$signature_group),
        sex = as.character(query$sex),
        apoe_group = as.character(query$apoe_group),
        query_mode = as.character(query$query_mode),
        structural_status = as.character(query$structural_status),
        structurally_available = query_available,
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
        fold_enrichment = if (n > 0L && N > 0L && any(M > 0L)) {
          ifelse(M > 0L, (k / n) / (M / N), NA_real_)
        } else {
          rep(NA_real_, length(M))
        },
        pathway_hit_rate = ifelse(M > 0L, k / M, NA_real_),
        test_status = ifelse(tested, "tested", "not_testable"),
        testability_reason = reasons,
        strict_testability_reason = strict_reason,
        small_pathway_status = ifelse(
          tested &
            M <= as.integer(analysis_cfg$small_pathway_upper_bound),
          "small_pathway_lower_confidence",
          ifelse(tested, "standard_pathway_size", "not_testable")
        ),
        p_value = p_value,
        overlap_genes = overlap_genes
      )
    }
  }
  ora <- data.table::rbindlist(rows[seq_len(row_index)], fill = TRUE)
  ora <- apply_bh_families(
    ora, global_columns = global_columns,
    method = as.character(config$fdr$method),
    threshold = as.numeric(config$fdr$threshold)
  )
  ora[, query_significant_pathways := sum(local_fdr_significant), by = .(
    query_id, pathway_collection
  )]
  ora[, status_order := fifelse(test_status == "tested", 0L, 1L)]
  data.table::setorderv(
    ora,
    c(
      "query_order", "collection_order", "status_order",
      "local_fdr_bh", "p_value", "overlap_count",
      "source_pathway_order"
    ),
    c(1L, 1L, 1L, 1L, 1L, -1L, 1L),
    na.last = TRUE
  )
  ora[, statistical_order := seq_len(.N), by = .(
    query_id, pathway_collection
  )]
  ora[, status_order := NULL]
  ora
}

recurrence_fields <- function(overlap_strings, significant) {
  strings <- overlap_strings[significant %in% TRUE & nonempty(overlap_strings)]
  if (!length(strings)) {
    return(list(
      overlap_gene_union = "",
      overlap_gene_union_count = 0L,
      recurrent_overlap_genes = "",
      recurrent_overlap_gene_count = 0L
    ))
  }
  per_row <- lapply(strings, split_gene_string)
  all_genes <- unlist(per_row, use.names = FALSE)
  counts <- table(all_genes)
  union <- sort(names(counts))
  recurrent <- sort(names(counts)[counts >= 2L])
  list(
    overlap_gene_union = paste(union, collapse = ","),
    overlap_gene_union_count = length(union),
    recurrent_overlap_genes = paste(recurrent, collapse = ","),
    recurrent_overlap_gene_count = length(recurrent)
  )
}

build_recurrence_summary <- function(ora, by_columns, schema) {
  ora[, {
    sig <- local_fdr_significant %in% TRUE
    fold <- fold_enrichment[sig & is.finite(fold_enrichment)]
    recurrence <- recurrence_fields(overlap_genes, sig)
    c(list(
      structurally_available_contrasts =
        data.table::uniqueN(contrast_id[structurally_available %in% TRUE]),
      total_contrasts = data.table::uniqueN(contrast_id),
      testable_queries = sum(test_status == "tested"),
      locally_significant_queries = sum(sig),
      globally_significant_queries = sum(global_fdr_significant %in% TRUE),
      significant_ad_any_queries =
        sum(sig & query_mode == "AD_any_mito"),
      significant_ad_up_queries =
        sum(sig & query_mode == "AD_up_mito"),
      significant_ad_down_queries =
        sum(sig & query_mode == "AD_down_mito"),
      significant_fine_cell_types =
        data.table::uniqueN(fine_cell_type[sig]),
      signal_depends_on_one_fine_cell =
        data.table::uniqueN(fine_cell_type[sig]) == 1L,
      median_significant_fold_enrichment =
        if (length(fold)) stats::median(fold) else NA_real_,
      minimum_significant_fold_enrichment =
        if (length(fold)) min(fold) else NA_real_,
      maximum_significant_fold_enrichment =
        if (length(fold)) max(fold) else NA_real_
    ), recurrence)
  }, by = by_columns][, schema_version := schema][]
}

compute_redundancy_map <- function(
    program_manifest, program_membership, schema, threshold = 0.25) {
  meta <- program_manifest[pathway_collection == "mitocarta_complete_149"]
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
    a_ancestor <- nonempty(a$hierarchy) && nonempty(b$hierarchy) &&
      startsWith(b$hierarchy, paste0(a$hierarchy, " > "))
    b_ancestor <- nonempty(a$hierarchy) && nonempty(b$hierarchy) &&
      startsWith(a$hierarchy, paste0(b$hierarchy, " > "))
    direct_parent <- identical(as.character(b$parent_pathway), as.character(a$pathway_id)) ||
      identical(as.character(a$parent_pathway), as.character(b$pathway_id))
    relationship <- if (direct_parent) {
      "direct_parent_child"
    } else if (a_ancestor || b_ancestor) {
      "ancestor_descendant"
    } else if (identical(as.character(a$level_1), as.character(b$level_1))) {
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
      same_top_level_system =
        identical(as.character(a$level_1), as.character(b$level_1)),
      redundancy_candidate =
        jaccard >= threshold || relationship %in% c(
          "direct_parent_child", "ancestor_descendant"
        ),
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

artifact_valid <- function(row, root) {
  path <- absolute_path(as.character(row$path), root)
  file.exists(path) &&
    identical(sha256_file(path), as.character(row$sha256)) &&
    as.numeric(file.info(path)$size) == as.numeric(row$bytes)
}

valid_existing_bundle <- function(
    final_root, project_root, status_schema, artifacts_schema,
    script_hash, config_hash) {
  status_path <- file.path(final_root, "fine_deg_pathway_status.tsv")
  artifacts_path <- file.path(final_root, "fine_deg_pathway_artifacts.tsv")
  if (!file.exists(status_path) || !file.exists(artifacts_path)) return(FALSE)
  status <- tryCatch(data.table::fread(status_path), error = function(e) NULL)
  artifacts <- tryCatch(data.table::fread(artifacts_path), error = function(e) NULL)
  if (is.null(status) || is.null(artifacts) || nrow(status) != 1L) return(FALSE)
  if (!schema_ok(status, status_schema) || !schema_ok(artifacts, artifacts_schema)) {
    return(FALSE)
  }
  if (!identical(status$validation_status[[1L]], "validated_complete") ||
      !identical(status$scientific_script_sha256[[1L]], script_hash) ||
      !identical(status$scientific_config_sha256[[1L]], config_hash)) {
    return(FALSE)
  }
  all(vapply(
    seq_len(nrow(artifacts)),
    function(i) artifact_valid(artifacts[i], project_root),
    logical(1)
  ))
}

run_analysis <- function(cli = parse_cli(commandArgs(trailingOnly = TRUE))) {
  required_packages <- c("data.table", "yaml", "digest", "readxl")
  for (package in required_packages) {
    if (!requireNamespace(package, quietly = TRUE)) {
      stop("Package '", package, "' is required", call. = FALSE)
    }
  }
  library(data.table)

  start_time <- Sys.time()
  project_root <- normalizePath(getwd(), mustWork = TRUE)
  pipeline_config_path <- absolute_path(cli$config, project_root)
  execution_config_path <- absolute_path(cli$execution_config, project_root)
  must(file.exists(pipeline_config_path), "Pipeline config does not exist")
  must(file.exists(execution_config_path), "Execution config does not exist")
  pipeline_config <- yaml::read_yaml(pipeline_config_path)
  execution_config <- yaml::read_yaml(execution_config_path)
  phase_config_path <- absolute_path(
    pipeline_config$project$phase11_pathway_deg_fine_config %||% "",
    project_root
  )
  must(file.exists(phase_config_path), "Fine-DEG pathway config does not exist")
  config <- yaml::read_yaml(phase_config_path)
  must(
    identical(config$schema_version, "phase11_pathway_deg_fine_config_v1"),
    "Unexpected fine-DEG pathway config schema"
  )

  execution <- execution_config$execution
  execution_stage <- as.character(execution$execution_stage)
  must(
    execution_stage %in% c(
      "local_pilot", "local_production_equivalent",
      "minerva_production", "lsf_fallback"
    ),
    "Unsupported execution stage"
  )
  output_root <- absolute_path(pipeline_config$outputs$root, project_root)
  final_root <- file.path(output_root, as.character(config$output$directory))
  staging_root <- file.path(
    output_root,
    paste0(".", as.character(config$output$directory), ".staging.", Sys.getpid())
  )
  script_path <- file.path(
    project_root, "scripts/11_run_fine_deg_pathway_analysis.R"
  )
  script_hash <- sha256_file(script_path)
  config_hash <- sha256_file(phase_config_path)
  if (dir.exists(final_root)) {
    if (valid_existing_bundle(
      final_root, project_root,
      config$schemas$status, config$schemas$artifacts,
      script_hash, config_hash
    )) {
      cat(
        "Fine-DEG pathway output is complete and hash-valid: ",
        final_root, "\n", sep = ""
      )
      return(invisible(final_root))
    }
    stop(
      "Output directory exists but is not a complete hash-valid bundle: ",
      final_root,
      if (isTRUE(cli$force)) {
        " (--force never deletes or overwrites an invalid production bundle)"
      } else {
        ""
      },
      call. = FALSE
    )
  }
  must(!dir.exists(staging_root), "Process-specific staging directory exists")
  dir.create(staging_root, recursive = TRUE, showWarnings = FALSE)
  on.exit({
    if (dir.exists(staging_root)) unlink(staging_root, recursive = TRUE)
  }, add = TRUE)

  input_path <- function(section, name = NULL) {
    value <- if (is.null(name)) config$inputs[[section]] else {
      file.path(config$inputs[[section]], name)
    }
    absolute_path(value, project_root)
  }
  phase08_root <- input_path("phase08_root")
  phase09_root <- input_path("phase09_root")
  phase11_root <- input_path("phase11_similarity_root")
  phase12_root <- input_path("phase12_root")
  phase20_root <- input_path("phase20_combo_root")

  paths <- list(
    phase09_status = file.path(phase09_root, "annotation_status.tsv"),
    phase09_checks = file.path(phase09_root, "annotation_checks.tsv"),
    phase09_artifacts = file.path(phase09_root, "annotation_artifacts.tsv"),
    phase09_core = file.path(phase09_root, "deg_mito_core.tsv.gz"),
    phase09_master = file.path(phase09_root, "gene_annotation_master.tsv.gz"),
    phase11_status = file.path(phase11_root, "pathway_status.tsv"),
    phase11_artifacts = file.path(phase11_root, "pathway_artifacts.tsv"),
    phase11_reference = file.path(phase11_root, "pathway_reference_manifest.tsv"),
    phase11_membership = file.path(phase11_root, "pathway_membership_long.tsv.gz"),
    phase12_status = file.path(phase12_root, "kda_status.tsv"),
    phase12_artifacts = file.path(phase12_root, "kda_artifacts.tsv"),
    phase12_background = file.path(phase12_root, "kda_background_members.tsv.gz"),
    phase20_manifest = file.path(phase20_root, "combo_run_manifest.tsv"),
    phase20_query = file.path(phase20_root, "combo_query_members.tsv.gz"),
    legacy = input_path("legacy_module_membership"),
    mitocarta = input_path("mitocarta_source")
  )
  missing_paths <- names(paths)[!vapply(paths, file.exists, logical(1))]
  must(
    !length(missing_paths),
    paste("Required inputs are missing:", paste(missing_paths, collapse = ", "))
  )

  phase08_artifact_files <- Sys.glob(
    file.path(phase08_root, "*.yu_mast_de_artifacts.tsv")
  )
  phase08_manifest_files <- Sys.glob(
    file.path(phase08_root, "*.yu_mast_contrast_manifest.tsv")
  )
  phase08_status_files <- Sys.glob(
    file.path(phase08_root, "*.yu_mast_contrast_status.tsv")
  )
  must(
    length(phase08_artifact_files) == as.integer(config$expected$rds_sets),
    "Unexpected number of Phase 08 artifact manifests"
  )
  must(
    length(phase08_manifest_files) == as.integer(config$expected$rds_sets) &&
      length(phase08_status_files) == as.integer(config$expected$rds_sets),
    "Unexpected number of Phase 08 contrast contracts"
  )

  phase08_artifacts <- rbindlist(lapply(phase08_artifact_files, fread), fill = TRUE)
  must(
    all(phase08_artifacts$validation_status == "validated_complete"),
    "A Phase 08 artifact is not validated_complete"
  )
  required_phase08_artifacts <- phase08_artifacts[
    grepl(
      "yu_mast_(contrast_manifest|contrast_status|de)[.]tsv",
      artifact
    )
  ]
  phase08_artifact_valid <- vapply(
    seq_len(nrow(required_phase08_artifacts)),
    function(i) artifact_valid(required_phase08_artifacts[i], project_root),
    logical(1)
  )
  must(all(phase08_artifact_valid), "A required Phase 08 artifact failed validation")

  phase08_manifests <- rbindlist(lapply(
    phase08_manifest_files, fread, showProgress = FALSE
  ), fill = TRUE)
  phase08_statuses <- rbindlist(lapply(
    phase08_status_files, fread, showProgress = FALSE
  ), fill = TRUE)
  must(
    schema_ok(phase08_manifests, config$expected_schemas$phase08_manifest),
    "Unexpected Phase 08 contrast-manifest schema"
  )
  must(
    schema_ok(phase08_statuses, config$expected_schemas$phase08_status),
    "Unexpected Phase 08 contrast-status schema"
  )

  phase09_status <- fread(paths$phase09_status)
  phase09_checks <- fread(paths$phase09_checks)
  phase09_artifacts <- fread(paths$phase09_artifacts)
  must(
    schema_ok(phase09_status, config$expected_schemas$phase09_status) &&
      phase09_status$validation_status[[1L]] == "validated_complete",
    "Phase 09 status is not validated_complete"
  )
  must(
    schema_ok(phase09_checks, config$expected_schemas$phase09_checks) &&
      all(is_true(phase09_checks$passed)),
    "Phase 09 checks are not complete"
  )
  must(
    schema_ok(phase09_artifacts, config$expected_schemas$phase09_artifacts),
    "Unexpected Phase 09 artifact schema"
  )
  required_phase09 <- phase09_artifacts[
    artifact %in% c("deg_mito_core.tsv.gz", "gene_annotation_master.tsv.gz")
  ]
  must(nrow(required_phase09) == 2L, "Required Phase 09 artifacts are unregistered")
  must(
    all(vapply(
      seq_len(nrow(required_phase09)),
      function(i) artifact_valid(required_phase09[i], project_root),
      logical(1)
    )),
    "A required Phase 09 artifact failed validation"
  )

  phase11_status <- fread(paths$phase11_status)
  phase11_artifacts <- fread(paths$phase11_artifacts)
  phase11_reference <- fread(paths$phase11_reference)
  phase11_membership <- fread(paths$phase11_membership)
  must(
    phase11_status$validation_status[[1L]] == "validated_complete",
    "Phase 11 similarity status is not validated_complete"
  )
  required_phase11 <- phase11_artifacts[
    artifact %in% c(
      "pathway_reference_manifest.tsv", "pathway_membership_long.tsv.gz"
    )
  ]
  must(
    all(vapply(
      seq_len(nrow(required_phase11)),
      function(i) artifact_valid(required_phase11[i], project_root),
      logical(1)
    )),
    "A required Phase 11 reference artifact failed validation"
  )
  must(
    schema_ok(
      phase11_reference,
      config$expected_schemas$phase11_reference_manifest
    ) &&
      schema_ok(
        phase11_membership,
        config$expected_schemas$phase11_membership
      ),
    "Unexpected Phase 11 reference schema"
  )

  phase12_status <- fread(paths$phase12_status)
  phase12_artifacts <- fread(paths$phase12_artifacts)
  must(
    phase12_status$validation_status[[1L]] == "validated_complete",
    "Phase 12 status is not validated_complete"
  )
  phase12_background_artifact <- phase12_artifacts[
    basename(path) == "kda_background_members.tsv.gz"
  ]
  must(
    nrow(phase12_background_artifact) == 1L &&
      artifact_valid(phase12_background_artifact, project_root),
    "Phase 12 KDA background failed artifact validation"
  )

  must(
    identical(
      sha256_file(paths$mitocarta),
      as.character(config$references$mitocarta$source_sha256)
    ),
    "MitoCarta source checksum differs from the frozen config"
  )

  deg <- fread(paths$phase09_core, showProgress = FALSE)
  gene_annotation <- fread(
    paths$phase09_master,
    select = c(
      "rds_id", "symbol_hgnc_current", "is_mitocarta3",
      "mito_tier", "reference_only"
    ),
    showProgress = FALSE
  )
  combo_manifest <- fread(paths$phase20_manifest)
  combo_query <- fread(paths$phase20_query, showProgress = FALSE)
  kda_background <- fread(paths$phase12_background, showProgress = FALSE)
  legacy <- fread(paths$legacy)

  must(
    schema_ok(deg, config$expected_schemas$phase09_core),
    "Unexpected Phase 09 core-DEG schema"
  )
  must(
    schema_ok(combo_manifest, config$expected_schemas$phase20_combo_manifest),
    "Unexpected Phase 20 combo-manifest schema"
  )
  must(
    schema_ok(combo_query, config$expected_schemas$phase20_combo_members),
    "Unexpected Phase 20 combo-query schema"
  )
  must(
    schema_ok(kda_background, config$expected_schemas$phase12_background),
    "Unexpected Phase 12 KDA-background schema"
  )

  parsed_mitocarta <- parse_mitocarta_source(paths$mitocarta)
  normalized_mitocarta <- phase11_membership[
    pathway_collection == config$references$mitocarta$normalized_collection,
    .(
      source_pathway_order, source_gene_order, pathway_id,
      symbol_hgnc_current, hierarchy, hierarchy_depth, level_1,
      level_2, level_3_or_deeper, parent_pathway, pathway_name,
      description, pathway_scope
    )
  ]
  parsed_keys <- parsed_mitocarta$membership[
    , paste(pathway_id, symbol_hgnc_current, sep = "\r")
  ]
  normalized_keys <- normalized_mitocarta[
    , paste(pathway_id, symbol_hgnc_current, sep = "\r")
  ]
  mitocarta_exact_reconciliation <- setequal(parsed_keys, normalized_keys)
  programs <- build_program_collections(legacy, parsed_mitocarta, config)
  program_manifest <- programs$metadata
  program_membership <- programs$membership

  phase08_manifest_unique <- unique(
    phase08_manifests, by = "contrast_id"
  )
  phase08_status_unique <- unique(
    phase08_statuses, by = "contrast_id"
  )
  contrast_manifest <- merge(
    phase08_manifest_unique,
    phase08_status_unique[, .(
      contrast_id,
      terminal_status,
      genes_returned_phase08 = genes_returned,
      paper_degs_phase08 = paper_degs,
      phase08_status_message = message
    )],
    by = "contrast_id", all.x = TRUE, sort = FALSE
  )
  combo_map <- unique(combo_manifest[, .(
    source_contrast_id, broad_cell_type, signature_group
  )], by = "source_contrast_id")
  contrast_manifest <- merge(
    contrast_manifest, combo_map,
    by.x = "contrast_id", by.y = "source_contrast_id",
    all.x = TRUE, sort = FALSE
  )
  contrast_manifest[, `:=`(
    fine_cell_type = cell_type_high_resolution,
    structural_status = fifelse(
      terminal_status == "validated_complete",
      "estimable_validated", "not_estimable"
    ),
    structurally_available = terminal_status == "validated_complete"
  )]
  data.table::setorder(
    contrast_manifest, rds_id, manifest_row
  )
  contrast_manifest[, contrast_order := seq_len(.N)]

  tested_statuses <- unlist(
    config$analysis$tested_statuses, use.names = FALSE
  )
  deg[, stored_paper_deg := is_true(paper_deg)]
  deg[, reproduced_paper_deg :=
    is.finite(fdr_bh_within_contrast) &
      fdr_bh_within_contrast < as.numeric(config$analysis$significance_threshold) &
      is.finite(logFC) &
      abs(logFC) > paper_effect_threshold_log2
  ]
  paper_deg_reproduced <- identical(
    deg$stored_paper_deg, deg$reproduced_paper_deg
  )

  background_candidates <- deg[
    !is_true(reference_only) &
      tested_status %in% tested_statuses &
      nonempty(symbol_hgnc_current)
  ]
  background_genes <- background_candidates[, .(
    source_feature_ids = collapse_values(feature_id_original),
    source_feature_count = data.table::uniqueN(feature_id_original),
    tested_statuses = collapse_values(tested_status),
    genome_origins = collapse_values(genome_origin),
    mapping_statuses = collapse_values(mapping_status)
  ), by = .(
    contrast_id, rds_id, fine_cell_type = cell_type_high_resolution,
    sex, apoe_group, symbol_hgnc_current
  )]
  background_genes[, background_id := contrast_id]
  background_genes[, schema_version := config$schemas$background_genes]
  data.table::setcolorder(background_genes, c(
    "schema_version", "background_id", "contrast_id", "rds_id",
    "fine_cell_type", "sex", "apoe_group", "symbol_hgnc_current",
    "source_feature_ids", "source_feature_count", "tested_statuses",
    "genome_origins", "mapping_statuses"
  ))
  data.table::setorder(background_genes, contrast_id, symbol_hgnc_current)

  background_stats <- background_candidates[, .(
    admitted_feature_rows = .N,
    mapped_unique_background_genes = data.table::uniqueN(symbol_hgnc_current),
    duplicate_symbol_collapses =
      .N - data.table::uniqueN(symbol_hgnc_current)
  ), by = contrast_id]
  all_core_stats <- deg[, .(
    core_feature_rows = .N,
    mapped_core_feature_rows = sum(nonempty(symbol_hgnc_current)),
    unmapped_core_feature_rows = sum(!nonempty(symbol_hgnc_current)),
    reference_only_rows = sum(is_true(reference_only))
  ), by = contrast_id]
  background_manifest <- merge(
    contrast_manifest[, .(
      contrast_order, contrast_id, rds_id,
      fine_cell_type, broad_cell_type, signature_group,
      sex, apoe_group, structural_status, structurally_available
    )],
    all_core_stats, by = "contrast_id", all.x = TRUE, sort = FALSE
  )
  background_manifest <- merge(
    background_manifest, background_stats,
    by = "contrast_id", all.x = TRUE, sort = FALSE
  )
  for (column in c(
    "admitted_feature_rows", "mapped_unique_background_genes",
    "duplicate_symbol_collapses"
  )) {
    data.table::set(
      background_manifest,
      which(is.na(background_manifest[[column]])),
      column, 0L
    )
  }
  background_manifest[, `:=`(
    background_id = contrast_id,
    background_size = mapped_unique_background_genes,
    background_status = fifelse(
      !structurally_available, "contrast_not_estimable",
      fifelse(
        mapped_unique_background_genes > 0L,
        "available", "empty_background"
      )
    ),
    schema_version = config$schemas$background_manifest
  )]
  data.table::setorder(background_manifest, contrast_order)

  deg_significant <- deg[
    stored_paper_deg &
      tested_status %in% c("significant_up", "significant_down") &
      nonempty(symbol_hgnc_current)
  ]
  collapsed_degs <- deg_significant[, .(
    source_feature_ids = collapse_values(feature_id_original),
    source_feature_count = data.table::uniqueN(feature_id_original),
    logFC_min = min(logFC),
    logFC_max = max(logFC),
    logFC_representative = logFC[which.max(abs(logFC))],
    minimum_fdr_bh = min(fdr_bh_within_contrast),
    in_upregulated_query = any(logFC > 0),
    in_downregulated_query = any(logFC < 0),
    source_tested_statuses = collapse_values(tested_status),
    genome_origins = collapse_values(genome_origin)
  ), by = .(
    contrast_id, rds_id,
    fine_cell_type = cell_type_high_resolution,
    sex, apoe_group, symbol_hgnc_current
  )]
  direction_conflicts <- collapsed_degs[
    in_upregulated_query & in_downregulated_query, .N
  ]

  query_modes <- names(config$analysis$query_modes)
  query_manifest_rows <- vector(
    "list", nrow(contrast_manifest) * length(query_modes)
  )
  query_gene_rows <- list()
  query_index <- 0L
  for (i in seq_len(nrow(contrast_manifest))) {
    contrast <- contrast_manifest[i]
    contrast_degs <- collapsed_degs[contrast_id == contrast$contrast_id]
    for (mode in query_modes) {
      query_index <- query_index + 1L
      mode_cfg <- config$analysis$query_modes[[mode]]
      selected <- switch(
        as.character(mode_cfg$direction),
        any = contrast_degs,
        up = contrast_degs[in_upregulated_query %in% TRUE],
        down = contrast_degs[in_downregulated_query %in% TRUE],
        stop("Unsupported query direction", call. = FALSE)
      )
      query_id <- paste(contrast$contrast_id, mode, sep = "::")
      if (nrow(selected)) {
        genes <- data.table::copy(selected)
        genes[, `:=`(
          schema_version = config$schemas$query_genes,
          query_id = query_id,
          background_id = as.character(contrast$contrast_id),
          query_mode = mode,
          signature_group = as.character(contrast$signature_group),
          broad_cell_type = as.character(contrast$broad_cell_type)
        )]
        query_gene_rows[[length(query_gene_rows) + 1L]] <- genes
      }
      query_manifest_rows[[query_index]] <- data.table::data.table(
        query_order = query_index,
        query_id = query_id,
        background_id = as.character(contrast$contrast_id),
        contrast_order = as.integer(contrast$contrast_order),
        contrast_id = as.character(contrast$contrast_id),
        kda_run_id = NA_character_,
        rds_id = as.character(contrast$rds_id),
        fine_cell_type = as.character(contrast$fine_cell_type),
        broad_cell_type = as.character(contrast$broad_cell_type),
        signature_group = as.character(contrast$signature_group),
        sex = as.character(contrast$sex),
        apoe_group = as.character(contrast$apoe_group),
        query_mode = mode,
        query_direction = as.character(mode_cfg$direction),
        structural_status = as.character(contrast$structural_status),
        structurally_available = isTRUE(contrast$structurally_available),
        source_significant_feature_rows = nrow(selected),
        mapped_unique_query_genes = data.table::uniqueN(
          selected$symbol_hgnc_current
        ),
        duplicate_symbol_collapses =
          nrow(selected) - data.table::uniqueN(selected$symbol_hgnc_current),
        query_size = data.table::uniqueN(selected$symbol_hgnc_current),
        background_size = background_manifest[
          contrast_id == contrast$contrast_id, background_size
        ],
        query_status = if (!isTRUE(contrast$structurally_available)) {
          "contrast_not_estimable"
        } else if (!nrow(selected)) {
          "empty_query"
        } else if (data.table::uniqueN(selected$symbol_hgnc_current) <
                   as.integer(config$analysis$minimum_query_size)) {
          "query_below_minimum"
        } else {
          "testable_query"
        },
        schema_version = config$schemas$query_manifest
      )
    }
  }
  query_manifest <- rbindlist(query_manifest_rows)
  query_genes <- if (length(query_gene_rows)) {
    rbindlist(query_gene_rows, fill = TRUE)
  } else {
    data.table()
  }
  data.table::setorder(query_manifest, query_order)
  data.table::setorder(query_genes, query_id, symbol_hgnc_current)

  query_counts_wide <- data.table::dcast(
    query_manifest,
    contrast_id ~ query_mode,
    value.var = "query_size"
  )
  data.table::setnames(
    query_counts_wide,
    c("AD_any_mito", "AD_up_mito", "AD_down_mito"),
    c("mito_deg_any_count", "mito_deg_up_count", "mito_deg_down_count")
  )
  contrast_manifest <- merge(
    contrast_manifest,
    background_manifest[, .(contrast_id, background_size, background_status)],
    by = "contrast_id", all.x = TRUE, sort = FALSE
  )
  contrast_manifest <- merge(
    contrast_manifest, query_counts_wide,
    by = "contrast_id", all.x = TRUE, sort = FALSE
  )
  phase09_contrast_counts <- unique(deg[, .(
    contrast_id,
    phase09_contrast_paper_degs = contrast_paper_degs
  )], by = "contrast_id")
  contrast_manifest <- merge(
    contrast_manifest, phase09_contrast_counts,
    by = "contrast_id", all.x = TRUE, sort = FALSE
  )
  contrast_manifest[
    , schema_version := config$schemas$contrast_manifest
  ]
  data.table::setorder(contrast_manifest, contrast_order)

  phase08_phase09_counts_match <- all(
    contrast_manifest$paper_degs_phase08 ==
      contrast_manifest$phase09_contrast_paper_degs
  )

  primary_ora <- run_ora(
    query_manifest = query_manifest,
    query_genes = query_genes,
    background_genes = background_genes,
    program_manifest = program_manifest,
    program_membership = program_membership,
    config = config,
    schema = config$schemas$ora,
    profile = "primary_pre_network_fine_deg",
    global_columns = c("pathway_collection", "query_mode")
  )

  significant_results <- data.table::copy(
    primary_ora[local_fdr_significant %in% TRUE]
  )
  significant_results[, schema_version := config$schemas$significant_results]

  fine_cell_summary <- primary_ora[, .(
    structural_status = first(structural_status),
    structurally_available = first(structurally_available),
    background_size = max(background_size),
    query_size = max(query_size),
    pathway_count = .N,
    testable_pathways = sum(test_status == "tested"),
    locally_significant_pathways = sum(local_fdr_significant %in% TRUE),
    globally_significant_pathways = sum(global_fdr_significant %in% TRUE),
    minimum_local_fdr_bh = if (any(is.finite(local_fdr_bh))) {
      min(local_fdr_bh, na.rm = TRUE)
    } else {
      NA_real_
    },
    top_pathway = if (any(is.finite(local_fdr_bh))) {
      pathway_name[which.min(local_fdr_bh)]
    } else {
      NA_character_
    }
  ), by = .(
    contrast_id, rds_id, fine_cell_type, broad_cell_type,
    signature_group, sex, apoe_group, query_mode,
    pathway_collection, collection_role
  )]
  fine_cell_summary[, schema_version := config$schemas$fine_cell_summary]

  broad_cell_summary <- build_recurrence_summary(
    primary_ora,
    c(
      "signature_group", "sex", "apoe_group", "broad_cell_type",
      "query_mode", "pathway_collection", "collection_role",
      "pathway_id", "pathway_name", "hierarchy_depth", "level_1", "level_2"
    ),
    config$schemas$broad_cell_summary
  )
  sex_apoe_summary <- build_recurrence_summary(
    primary_ora,
    c(
      "signature_group", "sex", "apoe_group", "query_mode",
      "pathway_collection", "collection_role", "pathway_id",
      "pathway_name", "hierarchy_depth", "level_1", "level_2"
    ),
    config$schemas$sex_apoe_summary
  )
  redundancy_map <- compute_redundancy_map(
    program_manifest, program_membership,
    config$schemas$redundancy_map,
    as.numeric(config$redundancy$representative_jaccard_threshold)
  )

  included_manifest <- combo_manifest[is_true(included_at_thresholds)]
  included_query <- combo_query[
    is_true(included_at_thresholds) & is_true(effective_member)
  ]
  annotation_sets <- split(
    unique(gene_annotation[
      is_true(is_mitocarta3) &
        !is_true(reference_only) &
        nonempty(symbol_hgnc_current),
      .(rds_id, symbol_hgnc_current)
    ])$symbol_hgnc_current,
    unique(gene_annotation[
      is_true(is_mitocarta3) &
        !is_true(reference_only) &
        nonempty(symbol_hgnc_current),
      .(rds_id, symbol_hgnc_current)
    ])$rds_id
  )
  kda_background_sets <- split(kda_background$gene, kda_background$kda_run_id)
  kda_query_sets <- split(included_query$gene, included_query$kda_run_id)
  kda_background_rows <- list()
  kda_query_rows <- list()
  kda_query_manifest_rows <- vector("list", nrow(included_manifest))
  for (i in seq_len(nrow(included_manifest))) {
    run <- included_manifest[i]
    source_rds <- strsplit(
      as.character(run$source_contrast_id), "::", fixed = TRUE
    )[[1L]][[1L]]
    exact_background <- sort(intersect(
      unique(kda_background_sets[[run$kda_run_id]] %||% character()),
      unique(annotation_sets[[source_rds]] %||% character())
    ))
    source_query <- included_query[kda_run_id == run$kda_run_id]
    exact_query <- sort(unique(kda_query_sets[[run$kda_run_id]] %||% character()))
    kda_background_rows[[i]] <- data.table::data.table(
      background_id = as.character(run$kda_run_id),
      symbol_hgnc_current = exact_background
    )
    if (length(exact_query)) {
      source_query <- source_query[!duplicated(gene)]
      kda_query_rows[[i]] <- source_query[, .(
        query_id = as.character(run$kda_run_id),
        background_id = as.character(run$kda_run_id),
        symbol_hgnc_current = gene,
        in_upregulated_query,
        in_downregulated_query,
        source_directions
      )]
    }
    kda_query_manifest_rows[[i]] <- data.table::data.table(
      query_order = i,
      query_id = as.character(run$kda_run_id),
      background_id = as.character(run$kda_run_id),
      contrast_id = as.character(run$source_contrast_id),
      kda_run_id = as.character(run$kda_run_id),
      rds_id = source_rds,
      fine_cell_type = as.character(run$fine_cell_type),
      broad_cell_type = as.character(run$broad_cell_type),
      signature_group = as.character(run$signature_group),
      sex = as.character(run$sex),
      apoe_group = as.character(run$apoe_group),
      query_mode = as.character(run$query_mode),
      structural_status = "kda_eligible_effective_query",
      structurally_available = TRUE,
      query_size = length(exact_query),
      background_size = length(exact_background)
    )
  }
  kda_query_manifest <- rbindlist(kda_query_manifest_rows)
  kda_query_genes <- rbindlist(kda_query_rows, fill = TRUE)
  kda_background_genes <- rbindlist(kda_background_rows, fill = TRUE)
  kda_queries_subset <- all(vapply(
    seq_len(nrow(kda_query_manifest)),
    function(i) {
      run <- kda_query_manifest[i]
      all(
        kda_query_genes[query_id == run$query_id, symbol_hgnc_current] %chin%
          kda_background_genes[
            background_id == run$background_id, symbol_hgnc_current
          ]
      )
    },
    logical(1)
  ))

  kda_ora <- run_ora(
    query_manifest = kda_query_manifest,
    query_genes = kda_query_genes,
    background_genes = kda_background_genes,
    program_manifest = program_manifest,
    program_membership = program_membership,
    config = config,
    schema = config$schemas$kda_ora,
    profile = "kda_effective_query_compatibility",
    global_columns = "pathway_collection"
  )

  reconciliation_rows <- list()
  add_reconciliation <- function(
      checkpoint_group, metric, observed, expected, details = "") {
    reconciliation_rows[[length(reconciliation_rows) + 1L]] <<-
      data.table::data.table(
        schema_version = config$schemas$reconciliation,
        checkpoint_group = checkpoint_group,
        metric = metric,
        observed = as.character(observed),
        expected = as.character(expected),
        passed = identical(as.numeric(observed), as.numeric(expected)),
        details = details
      )
  }
  f_cfg <- config$legacy_reconciliation$female_e33
  m_cfg <- config$legacy_reconciliation$male_e33
  mt_genes <- program_membership[
    pathway_collection == "legacy_four" &
      pathway_id == f_cfg$mitochondrial_module,
    symbol_hgnc_current
  ]
  nuclear_genes <- program_membership[
    pathway_collection == "legacy_four" &
      pathway_id == m_cfg$nuclear_module,
    symbol_hgnc_current
  ]
  for (module_id in names(
    config$legacy_reconciliation$global_four_modules
  )) {
    module_cfg <- config$legacy_reconciliation$global_four_modules[[module_id]]
    module_genes <- program_membership[
      pathway_collection == "legacy_four" &
        pathway_id == module_id,
      symbol_hgnc_current
    ]
    module_rows <- kda_query_genes[
      symbol_hgnc_current %chin% module_genes
    ]
    module_significant <- kda_ora[
      pathway_collection == "legacy_four" &
        pathway_id == module_id &
        local_fdr_significant %in% TRUE,
      .N
    ]
    add_reconciliation(
      "global_four_modules", paste0(module_id, "_occurrences"),
      nrow(module_rows), module_cfg$expected_occurrences
    )
    add_reconciliation(
      "global_four_modules", paste0(module_id, "_up"),
      sum(is_true(module_rows$in_upregulated_query)), module_cfg$expected_up
    )
    add_reconciliation(
      "global_four_modules", paste0(module_id, "_down"),
      sum(is_true(module_rows$in_downregulated_query)), module_cfg$expected_down
    )
    add_reconciliation(
      "global_four_modules", paste0(module_id, "_significant_calls"),
      module_significant, module_cfg$expected_significant_calls
    )
  }
  for (signature in names(
    config$legacy_reconciliation$mtdna_by_stratum
  )) {
    stratum_cfg <- config$legacy_reconciliation$mtdna_by_stratum[[signature]]
    stratum_ids <- kda_query_manifest[
      signature_group == signature, query_id
    ]
    stratum_rows <- kda_query_genes[
      query_id %in% stratum_ids &
        symbol_hgnc_current %chin% mt_genes
    ]
    stratum_significant <- kda_ora[
      query_id %in% stratum_ids &
        pathway_collection == "legacy_four" &
        pathway_id == f_cfg$mitochondrial_module &
        local_fdr_significant %in% TRUE,
      .N
    ]
    checkpoint <- paste0("mtdna_by_stratum_", signature)
    add_reconciliation(
      checkpoint, "occurrences", nrow(stratum_rows),
      stratum_cfg$expected_occurrences
    )
    add_reconciliation(
      checkpoint, "up",
      sum(is_true(stratum_rows$in_upregulated_query)),
      stratum_cfg$expected_up
    )
    add_reconciliation(
      checkpoint, "down",
      sum(is_true(stratum_rows$in_downregulated_query)),
      stratum_cfg$expected_down
    )
    add_reconciliation(
      checkpoint, "significant_calls", stratum_significant,
      stratum_cfg$expected_significant_calls
    )
  }
  female_rows <- kda_query_genes[
    query_id %in% kda_query_manifest[
      signature_group == f_cfg$signature_group, query_id
    ] & symbol_hgnc_current %chin% mt_genes
  ]
  female_sig <- kda_ora[
    signature_group == f_cfg$signature_group &
      pathway_collection == "legacy_four" &
      pathway_id == f_cfg$mitochondrial_module &
      local_fdr_significant %in% TRUE
  ]
  add_reconciliation(
    "female_e33", "group_mtdna_occurrences", nrow(female_rows),
    f_cfg$expected_group_mtdna_occurrences
  )
  add_reconciliation(
    "female_e33", "group_mtdna_up",
    sum(is_true(female_rows$in_upregulated_query)),
    f_cfg$expected_group_mtdna_up
  )
  add_reconciliation(
    "female_e33", "group_mtdna_down",
    sum(is_true(female_rows$in_downregulated_query)),
    f_cfg$expected_group_mtdna_down
  )
  add_reconciliation(
    "female_e33", "group_significant_calls", nrow(female_sig),
    f_cfg$expected_group_significant_calls
  )
  female_broad_ids <- kda_query_manifest[
    signature_group == f_cfg$signature_group &
      broad_cell_type == f_cfg$broad_cell_type,
    query_id
  ]
  female_broad_rows <- kda_query_genes[
    query_id %in% female_broad_ids &
      symbol_hgnc_current %chin% mt_genes
  ]
  female_broad_sig <- kda_ora[
    query_id %in% female_broad_ids &
      pathway_collection == "legacy_four" &
      pathway_id == f_cfg$mitochondrial_module &
      local_fdr_significant %in% TRUE
  ]
  add_reconciliation(
    "female_e33_broad", "eligible_calls", length(female_broad_ids),
    f_cfg$expected_broad_eligible_calls
  )
  add_reconciliation(
    "female_e33_broad", "mtdna_occurrences", nrow(female_broad_rows),
    f_cfg$expected_broad_mtdna_occurrences
  )
  add_reconciliation(
    "female_e33_broad", "mtdna_up",
    sum(is_true(female_broad_rows$in_upregulated_query)),
    f_cfg$expected_broad_mtdna_up
  )
  add_reconciliation(
    "female_e33_broad", "mtdna_down",
    sum(is_true(female_broad_rows$in_downregulated_query)),
    f_cfg$expected_broad_mtdna_down
  )
  add_reconciliation(
    "female_e33_broad", "significant_calls", nrow(female_broad_sig),
    f_cfg$expected_broad_significant_calls
  )
  male_ids <- kda_query_manifest[
    signature_group == m_cfg$signature_group, query_id
  ]
  male_rows <- kda_query_genes[query_id %in% male_ids]
  male_mt <- male_rows[symbol_hgnc_current %chin% mt_genes]
  male_nuclear <- male_rows[symbol_hgnc_current %chin% nuclear_genes]
  add_reconciliation(
    "male_e33", "eligible_calls", length(male_ids),
    m_cfg$expected_eligible_calls
  )
  add_reconciliation(
    "male_e33", "mtdna_occurrences", nrow(male_mt),
    m_cfg$expected_mtdna_occurrences
  )
  add_reconciliation(
    "male_e33", "mtdna_up", sum(is_true(male_mt$in_upregulated_query)),
    m_cfg$expected_mtdna_up
  )
  add_reconciliation(
    "male_e33", "mtdna_down", sum(is_true(male_mt$in_downregulated_query)),
    m_cfg$expected_mtdna_down
  )
  add_reconciliation(
    "male_e33", "mtdna_significant_calls",
    kda_ora[
      query_id %in% male_ids &
        pathway_collection == "legacy_four" &
        pathway_id == m_cfg$mitochondrial_module &
        local_fdr_significant %in% TRUE,
      .N
    ],
    m_cfg$expected_mtdna_significant_calls
  )
  add_reconciliation(
    "male_e33", "nuclear_occurrences", nrow(male_nuclear),
    m_cfg$expected_nuclear_occurrences
  )
  add_reconciliation(
    "male_e33", "nuclear_up",
    sum(is_true(male_nuclear$in_upregulated_query)),
    m_cfg$expected_nuclear_up
  )
  add_reconciliation(
    "male_e33", "nuclear_down",
    sum(is_true(male_nuclear$in_downregulated_query)),
    m_cfg$expected_nuclear_down
  )
  add_reconciliation(
    "male_e33", "nuclear_significant_calls",
    kda_ora[
      query_id %in% male_ids &
        pathway_collection == "legacy_four" &
        pathway_id == m_cfg$nuclear_module &
        local_fdr_significant %in% TRUE,
      .N
    ],
    m_cfg$expected_nuclear_significant_calls
  )
  reconciliation <- rbindlist(reconciliation_rows)

  input_rows <- list()
  add_input <- function(role, path, records = NA_integer_, schema = NA_character_) {
    input_rows[[length(input_rows) + 1L]] <<- data.table::data.table(
      schema_version = config$schemas$reference_manifest,
      input_role = role,
      path = relative_path(path, project_root),
      sha256 = sha256_file(path),
      bytes = as.numeric(file.info(path)$size),
      records = as.integer(records),
      source_schema = schema,
      validation_status = "validated_complete"
    )
  }
  for (i in seq_len(nrow(required_phase08_artifacts))) {
    row <- required_phase08_artifacts[i]
    add_input(
      paste0("phase08_", row$artifact),
      absolute_path(row$path, project_root),
      row$records, row$schema_version
    )
  }
  add_input("phase09_status", paths$phase09_status, nrow(phase09_status),
            unique(phase09_status$schema_version))
  add_input("phase09_checks", paths$phase09_checks, nrow(phase09_checks),
            unique(phase09_checks$schema_version))
  add_input("phase09_artifacts", paths$phase09_artifacts, nrow(phase09_artifacts),
            unique(phase09_artifacts$schema_version))
  add_input("phase09_core_deg", paths$phase09_core, nrow(deg),
            unique(deg$schema_version))
  add_input("phase09_gene_annotation", paths$phase09_master, nrow(gene_annotation),
            "gene_annotation_master_v1")
  add_input("phase11_status", paths$phase11_status, nrow(phase11_status),
            unique(phase11_status$schema_version))
  add_input("phase11_artifacts", paths$phase11_artifacts, nrow(phase11_artifacts),
            unique(phase11_artifacts$schema_version))
  add_input("phase11_reference", paths$phase11_reference, nrow(phase11_reference),
            unique(phase11_reference$schema_version))
  add_input("phase11_membership", paths$phase11_membership,
            nrow(phase11_membership), unique(phase11_membership$schema_version))
  add_input("phase12_status", paths$phase12_status, nrow(phase12_status),
            unique(phase12_status$schema_version))
  add_input("phase12_artifacts", paths$phase12_artifacts, nrow(phase12_artifacts),
            unique(phase12_artifacts$schema_version))
  add_input("phase12_background", paths$phase12_background,
            nrow(kda_background), unique(kda_background$schema_version))
  add_input("phase20_combo_manifest", paths$phase20_manifest,
            nrow(combo_manifest), unique(combo_manifest$schema_version))
  add_input("phase20_combo_query", paths$phase20_query,
            nrow(combo_query), unique(combo_query$schema_version))
  add_input("legacy_module_membership", paths$legacy, nrow(legacy),
            unique(legacy$schema_version))
  add_input("mitocarta_source", paths$mitocarta, 149L, "MitoCarta3.0")
  reference_manifest <- rbindlist(input_rows)

  checks <- list()
  add_check <- function(name, passed, observed, expected, details = "") {
    checks[[length(checks) + 1L]] <<- data.table::data.table(
      schema_version = config$schemas$checks,
      check_name = name,
      passed = isTRUE(passed),
      observed = as.character(observed),
      expected = as.character(expected),
      details = details
    )
  }
  add_check(
    "phase08_artifact_hashes", all(phase08_artifact_valid),
    sum(phase08_artifact_valid), nrow(required_phase08_artifacts)
  )
  add_check("phase09_paper_deg_reproduced", paper_deg_reproduced,
            sum(deg$stored_paper_deg != deg$reproduced_paper_deg), 0)
  add_check("phase08_phase09_deg_counts_match", phase08_phase09_counts_match,
            sum(
              contrast_manifest$paper_degs_phase08 !=
                contrast_manifest$phase09_contrast_paper_degs
            ), 0)
  add_check("mitocarta_source_reconciles", mitocarta_exact_reconciliation,
            length(setdiff(parsed_keys, normalized_keys)) +
              length(setdiff(normalized_keys, parsed_keys)), 0)
  add_check(
    "planned_contrasts",
    nrow(contrast_manifest) == as.integer(config$expected$planned_contrasts),
    nrow(contrast_manifest), config$expected$planned_contrasts
  )
  add_check(
    "fine_cell_types",
    uniqueN(contrast_manifest$fine_cell_type) ==
      as.integer(config$expected$fine_cell_types),
    uniqueN(contrast_manifest$fine_cell_type), config$expected$fine_cell_types
  )
  add_check(
    "sex_apoe_strata",
    uniqueN(contrast_manifest[, .(sex, apoe_group)]) ==
      as.integer(config$expected$sex_apoe_strata),
    uniqueN(contrast_manifest[, .(sex, apoe_group)]),
    config$expected$sex_apoe_strata
  )
  add_check(
    "estimable_contrasts",
    sum(contrast_manifest$structurally_available) ==
      as.integer(config$expected$estimable_contrasts),
    sum(contrast_manifest$structurally_available),
    config$expected$estimable_contrasts
  )
  add_check(
    "nonestimable_contrasts",
    sum(!contrast_manifest$structurally_available) ==
      as.integer(config$expected$nonestimable_contrasts),
    sum(!contrast_manifest$structurally_available),
    config$expected$nonestimable_contrasts
  )
  add_check(
    "phase09_core_rows",
    nrow(deg) == as.integer(config$expected$phase09_core_rows),
    nrow(deg), config$expected$phase09_core_rows
  )
  add_check(
    "query_manifest_rows",
    nrow(query_manifest) ==
      as.integer(config$expected$planned_contrasts) * length(query_modes),
    nrow(query_manifest),
    as.integer(config$expected$planned_contrasts) * length(query_modes)
  )
  collection_counts <- program_manifest[, .N, by = pathway_collection]
  for (collection in names(config$collections)) {
    expected_count <- as.integer(config$collections[[collection]]$expected_programs)
    observed_count <- collection_counts[
      pathway_collection == collection, N
    ]
    add_check(
      paste0("program_count_", collection),
      identical(observed_count, expected_count),
      observed_count, expected_count
    )
  }
  add_check(
    "primary_ora_rows",
    nrow(primary_ora) == nrow(query_manifest) * nrow(program_manifest),
    nrow(primary_ora), nrow(query_manifest) * nrow(program_manifest)
  )
  add_check(
    "primary_ora_keys_unique",
    !anyDuplicated(primary_ora[, .(
      query_id, pathway_collection, pathway_id
    )]),
    anyDuplicated(primary_ora[, .(
      query_id, pathway_collection, pathway_id
    )]), 0
  )
  add_check(
    "background_keys_unique",
    !anyDuplicated(background_genes[, .(
      background_id, symbol_hgnc_current
    )]),
    anyDuplicated(background_genes[, .(
      background_id, symbol_hgnc_current
    )]), 0
  )
  add_check(
    "query_keys_unique",
    !anyDuplicated(query_genes[, .(query_id, symbol_hgnc_current)]),
    anyDuplicated(query_genes[, .(query_id, symbol_hgnc_current)]), 0
  )
  primary_queries_subset <- all(vapply(
    seq_len(nrow(query_manifest)),
    function(i) {
      query <- query_manifest[i]
      all(
        query_genes[query_id == query$query_id, symbol_hgnc_current] %chin%
          background_genes[
            background_id == query$background_id, symbol_hgnc_current
          ]
      )
    },
    logical(1)
  ))
  add_check("primary_query_subset_background", primary_queries_subset,
            primary_queries_subset, TRUE)
  add_check(
    "up_query_direction",
    all(query_genes[
      query_mode == "AD_up_mito", logFC_representative
    ] > 0),
    sum(query_genes[
      query_mode == "AD_up_mito", logFC_representative <= 0
    ]), 0
  )
  add_check(
    "down_query_direction",
    all(query_genes[
      query_mode == "AD_down_mito", logFC_representative
    ] < 0),
    sum(query_genes[
      query_mode == "AD_down_mito", logFC_representative >= 0
    ]), 0
  )
  add_check("collapsed_direction_conflicts", direction_conflicts == 0L,
            direction_conflicts, 0)
  tested_primary <- primary_ora[test_status == "tested"]
  cells_nonnegative <- all(
    tested_primary$query_in_pathway >= 0L &
      tested_primary$query_not_in_pathway >= 0L &
      tested_primary$background_outside_query_in_pathway >= 0L &
      tested_primary$background_outside_query_not_in_pathway >= 0L
  )
  cells_sum <- all(
    tested_primary$query_in_pathway +
      tested_primary$query_not_in_pathway +
      tested_primary$background_outside_query_in_pathway +
      tested_primary$background_outside_query_not_in_pathway ==
      tested_primary$background_size
  )
  add_check("contingency_cells_nonnegative", cells_nonnegative,
            cells_nonnegative, TRUE)
  add_check("contingency_cells_sum_to_background", cells_sum,
            cells_sum, TRUE)
  recalculated_p <- ora_probability(
    tested_primary$overlap_count,
    tested_primary$background_pathway_size,
    tested_primary$background_size,
    tested_primary$query_size
  )
  p_error <- max(abs(tested_primary$p_value - recalculated_p), na.rm = TRUE)
  add_check("hypergeometric_p_recalculation", p_error < 1e-12,
            format(p_error, scientific = TRUE), "<1e-12")
  zero_overlap_ok <- all(
    tested_primary[overlap_count == 0L, p_value] == 1
  )
  add_check("zero_overlap_p_equals_one", zero_overlap_ok,
            zero_overlap_ok, TRUE)
  fisher_sample <- head(tested_primary[overlap_count > 0L], 30L)
  fisher_values <- vapply(seq_len(nrow(fisher_sample)), function(i) {
    row <- fisher_sample[i]
    stats::fisher.test(
      matrix(c(
        row$query_in_pathway,
        row$query_not_in_pathway,
        row$background_outside_query_in_pathway,
        row$background_outside_query_not_in_pathway
      ), nrow = 2L, byrow = TRUE),
      alternative = "greater"
    )$p.value
  }, numeric(1))
  fisher_error <- max(abs(fisher_sample$p_value - fisher_values))
  add_check("fisher_audit", fisher_error < 1e-12,
            format(fisher_error, scientific = TRUE), "<1e-12")
  local_audit <- tested_primary[, .(
    maximum_error = max(abs(
      local_fdr_bh - stats::p.adjust(p_value, method = config$fdr$method)
    ))
  ), by = .(query_id, pathway_collection)]
  global_audit <- tested_primary[, .(
    maximum_error = max(abs(
      global_fdr_bh - stats::p.adjust(p_value, method = config$fdr$method)
    ))
  ), by = .(pathway_collection, query_mode)]
  add_check("local_bh_audit", max(local_audit$maximum_error) < 1e-12,
            max(local_audit$maximum_error), "<1e-12")
  add_check("global_bh_audit", max(global_audit$maximum_error) < 1e-12,
            max(global_audit$maximum_error), "<1e-12")
  toy <- data.table(
    N = c(20L, 10L, 10L, 10L),
    n = c(5L, 2L, 2L, 2L),
    M = c(4L, 3L, 3L, 3L),
    k = c(2L, 0L, 1L, 2L),
    expected = c(3856 / 15504, 1, 24 / 45, 3 / 45)
  )
  toy[, observed := ora_probability(k, M, N, n)]
  toy_error <- max(abs(toy$observed - toy$expected))
  add_check("toy_ora_cases", toy_error < 1e-12,
            format(toy_error, scientific = TRUE), "<1e-12")
  add_check(
    "kda_effective_calls",
    nrow(kda_query_manifest) == as.integer(config$expected$kda_effective_calls),
    nrow(kda_query_manifest), config$expected$kda_effective_calls
  )
  add_check("kda_query_subset_background", kda_queries_subset,
            kda_queries_subset, TRUE)
  add_check(
    "kda_source_query_mode",
    identical(unique(kda_query_manifest$query_mode), "AD_both_mito"),
    collapse_values(unique(kda_query_manifest$query_mode)), "AD_both_mito"
  )
  add_check(
    "kda_ora_rows",
    nrow(kda_ora) == nrow(kda_query_manifest) * nrow(program_manifest),
    nrow(kda_ora), nrow(kda_query_manifest) * nrow(program_manifest)
  )
  add_check(
    "legacy_reconciliation",
    all(reconciliation$passed),
    sum(reconciliation$passed), nrow(reconciliation)
  )
  add_check(
    "redundancy_pairs",
    nrow(redundancy_map) == choose(as.integer(config$expected$mitocarta_pathways), 2),
    nrow(redundancy_map),
    choose(as.integer(config$expected$mitocarta_pathways), 2)
  )
  checks_table <- rbindlist(checks)
  must(
    all(checks_table$passed),
    paste(
      "Fine-DEG pathway checks failed:",
      paste(checks_table[passed == FALSE, check_name], collapse = ", ")
    )
  )

  output_objects <- list(
    fine_deg_pathway_checks.tsv = checks_table,
    fine_deg_pathway_reference_manifest.tsv = reference_manifest,
    fine_deg_pathway_program_manifest.tsv = program_manifest,
    fine_deg_pathway_contrast_manifest.tsv = contrast_manifest,
    fine_deg_pathway_background_manifest.tsv = background_manifest,
    fine_deg_pathway_background_genes.tsv.gz = background_genes,
    fine_deg_pathway_query_manifest.tsv = query_manifest,
    fine_deg_pathway_query_genes.tsv.gz = query_genes,
    fine_deg_pathway_ora.tsv.gz = primary_ora,
    fine_deg_pathway_significant_results.tsv.gz = significant_results,
    fine_deg_pathway_fine_cell_summary.tsv = fine_cell_summary,
    fine_deg_pathway_broad_cell_summary.tsv = broad_cell_summary,
    fine_deg_pathway_sex_apoe_summary.tsv = sex_apoe_summary,
    fine_deg_pathway_redundancy_map.tsv.gz = redundancy_map,
    kda_effective_query_program_ora.tsv.gz = kda_ora,
    legacy_four_module_reconciliation.tsv = reconciliation
  )
  for (name in names(output_objects)) {
    atomic_fwrite(output_objects[[name]], file.path(staging_root, name))
  }

  readme_lines <- c(
    "# Fine-cell DEG mitochondrial pathway analysis",
    "",
    "This validated production bundle tests mitochondrial pathway over-representation",
    "directly in ROSMAP fine-cell AD-versus-NCI DEG lists.",
    "",
    sprintf("- Planned contrasts: %d", nrow(contrast_manifest)),
    sprintf("- Estimable contrasts: %d", sum(contrast_manifest$structurally_available)),
    sprintf("- Query definitions: %d (combined, AD-up, and AD-down)", nrow(query_manifest)),
    sprintf("- Legacy programs: %d", program_manifest[pathway_collection == "legacy_four", .N]),
    sprintf("- Broad MitoCarta programs: %d", program_manifest[pathway_collection == "mitocarta_broad_46", .N]),
    sprintf("- Complete MitoCarta pathways: %d", program_manifest[pathway_collection == "mitocarta_complete_149", .N]),
    sprintf("- Primary ORA rows: %d", nrow(primary_ora)),
    sprintf("- KDA-aligned effective queries: %d", nrow(kda_query_manifest)),
    "",
    "The authoritative result is `fine_deg_pathway_ora.tsv.gz`; it includes",
    "significant, nonsignificant, not-testable, empty-query, and non-estimable",
    "records. Local BH FDR is primary. Global BH FDR is a study-wide sensitivity.",
    "",
    "The KDA-aligned table is a downstream compatibility profile and must not be",
    "confused with the pre-network primary DEG analysis. Enrichment is not proof",
    "of pathway activity, driver control, or a disease-by-sex/APOE interaction.",
    ""
  )
  atomic_write_lines(readme_lines, file.path(staging_root, "README.md"))

  artifact_rows <- list()
  for (name in names(output_objects)) {
    path <- file.path(staging_root, name)
    artifact_rows[[length(artifact_rows) + 1L]] <- data.table(
      schema_version = config$schemas$artifacts,
      artifact = name,
      path = relative_path(file.path(final_root, name), project_root),
      bytes = as.numeric(file.info(path)$size),
      sha256 = sha256_file(path),
      records = nrow(output_objects[[name]]),
      output_schema = if ("schema_version" %in% names(output_objects[[name]])) {
        unique(output_objects[[name]]$schema_version)[[1L]]
      } else {
        NA_character_
      },
      validation_status = "validated_complete"
    )
  }
  readme_path <- file.path(staging_root, "README.md")
  artifact_rows[[length(artifact_rows) + 1L]] <- data.table(
    schema_version = config$schemas$artifacts,
    artifact = "README.md",
    path = relative_path(file.path(final_root, "README.md"), project_root),
    bytes = as.numeric(file.info(readme_path)$size),
    sha256 = sha256_file(readme_path),
    records = length(readme_lines),
    output_schema = "markdown_v1",
    validation_status = "validated_complete"
  )
  artifacts <- rbindlist(artifact_rows)
  atomic_fwrite(
    artifacts,
    file.path(staging_root, "fine_deg_pathway_artifacts.tsv")
  )

  elapsed <- as.numeric(difftime(Sys.time(), start_time, units = "secs"))
  status <- data.table(
    schema_version = config$schemas$status,
    execution_stage = execution_stage,
    execution_phase = as.character(execution$execution_phase),
    backend = as.character(execution$backend),
    run_id = as.character(execution$run_id),
    stable_task_id = "global:pathway_deg_fine",
    task_mode = "pathway_deg_fine",
    scientific_script = relative_path(script_path, project_root),
    scientific_script_sha256 = script_hash,
    scientific_config_sha256 = config_hash,
    pipeline_config_sha256 = sha256_file(pipeline_config_path),
    execution_config_sha256 = sha256_file(execution_config_path),
    phase09_core_sha256 = sha256_file(paths$phase09_core),
    phase11_membership_sha256 = sha256_file(paths$phase11_membership),
    phase12_background_sha256 = sha256_file(paths$phase12_background),
    phase20_manifest_sha256 = sha256_file(paths$phase20_manifest),
    phase20_query_sha256 = sha256_file(paths$phase20_query),
    mitocarta_source_sha256 = sha256_file(paths$mitocarta),
    planned_contrasts = nrow(contrast_manifest),
    estimable_contrasts = sum(contrast_manifest$structurally_available),
    nonestimable_contrasts = sum(!contrast_manifest$structurally_available),
    query_definitions = nrow(query_manifest),
    pathway_collections = uniqueN(program_manifest$pathway_collection),
    pathway_definitions = nrow(program_manifest),
    primary_ora_rows = nrow(primary_ora),
    tested_primary_ora_rows = primary_ora[test_status == "tested", .N],
    significant_primary_ora_rows =
      primary_ora[local_fdr_significant %in% TRUE, .N],
    kda_effective_queries = nrow(kda_query_manifest),
    kda_ora_rows = nrow(kda_ora),
    failed_checks = checks_table[passed == FALSE, .N],
    peak_ram_gib = peak_ram_gib(),
    elapsed_seconds = elapsed,
    validation_status = "validated_complete",
    git_revision = git_revision(project_root),
    timestamp_utc = format(
      as.POSIXct(Sys.time(), tz = "UTC"),
      "%Y-%m-%d %H:%M:%S UTC", tz = "UTC"
    )
  )
  atomic_fwrite(
    status,
    file.path(staging_root, "fine_deg_pathway_status.tsv")
  )

  staged_artifacts <- fread(
    file.path(staging_root, "fine_deg_pathway_artifacts.tsv")
  )
  staged_valid <- all(vapply(seq_len(nrow(staged_artifacts)), function(i) {
    staged_path <- file.path(
      staging_root, basename(staged_artifacts$path[[i]])
    )
    file.exists(staged_path) &&
      identical(sha256_file(staged_path), staged_artifacts$sha256[[i]]) &&
      as.numeric(file.info(staged_path)$size) ==
        as.numeric(staged_artifacts$bytes[[i]])
  }, logical(1)))
  must(staged_valid, "A staged output artifact failed final hash validation")
  must(!dir.exists(final_root), "Final output appeared during staging")
  if (!file.rename(staging_root, final_root)) {
    stop("Could not atomically publish output bundle", call. = FALSE)
  }
  on.exit(NULL, add = FALSE)
  cat(
    "Fine-DEG pathway analysis validated and published: ",
    final_root, "\n", sep = ""
  )
  invisible(final_root)
}

if (sys.nframe() == 0L) {
  run_analysis()
}
