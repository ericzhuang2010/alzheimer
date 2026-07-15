#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

`%||%` <- function(x, y) if (is.null(x)) y else x

parse_cli <- function(args) {
  out <- list(
    manifest = "config/minerva_rds_manifest.tsv",
    input_root = NULL,
    output = "results/rds_structure_summaries.json",
    project_root = ".",
    rds_id = NULL,
    donor_field = "projid",
    cell_type_field = "cell_type_high_resolution",
    max_tool_depth = 3L,
    force = FALSE,
    hash = FALSE
  )
  value_options <- c(
    "--manifest", "--input-root", "--output", "--project-root", "--rds-id",
    "--donor-field", "--cell-type-field", "--max-tool-depth"
  )
  flag_options <- c("--force", "--hash")

  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (key %in% c("--help", "-h")) {
      cat(
        "Usage: Rscript scripts/16_export_rds_structure_summaries.R [options]\n\n",
        "Options:\n",
        "  --manifest FILE          Nine-RDS manifest (default: config/minerva_rds_manifest.tsv)\n",
        "  --input-root DIR         Override the manifest directory; basenames are retained\n",
        "  --output FILE            Combined JSON output file\n",
        "  --project-root DIR       Repository root (default: current directory)\n",
        "  --rds-id ID[,ID...]      Inspect only selected manifest IDs\n",
        "  --donor-field NAME       Donor metadata field (default: projid)\n",
        "  --cell-type-field NAME   Fine-cell-type field\n",
        "  --max-tool-depth N       Recursive depth for Seurat tools/misc summaries\n",
        "  --force                   Discard an existing output instead of resuming\n",
        "  --hash                    Calculate SHA-256 for each large RDS (slow)\n",
        sep = ""
      )
      quit(status = 0L)
    }
    if (key %in% flag_options) {
      out[[gsub("-", "_", sub("^--", "", key))]] <- TRUE
      i <- i + 1L
      next
    }
    if (!key %in% value_options || i == length(args)) {
      stop("Unknown option or missing value: ", key, call. = FALSE)
    }
    out[[gsub("-", "_", sub("^--", "", key))]] <- args[[i + 1L]]
    i <- i + 2L
  }

  out$max_tool_depth <- suppressWarnings(as.integer(out$max_tool_depth))
  if (is.na(out$max_tool_depth) || out$max_tool_depth < 0L || out$max_tool_depth > 8L) {
    stop("--max-tool-depth must be an integer from 0 through 8", call. = FALSE)
  }
  out
}

absolute_path <- function(path, root) {
  if (grepl("^/", path)) path else file.path(root, path)
}

atomic_write_json <- function(x, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  tmp <- paste0(path, ".tmp.", Sys.getpid())
  jsonlite::write_json(
    x, tmp, pretty = TRUE, auto_unbox = TRUE, null = "null", na = "null",
    digits = NA
  )
  if (!file.rename(tmp, path)) {
    unlink(tmp)
    stop("Could not atomically write ", path, call. = FALSE)
  }
}

sha256_file <- function(path) {
  result <- suppressWarnings(system2("sha256sum", path, stdout = TRUE, stderr = TRUE))
  status <- attr(result, "status")
  if (!length(result) || (!is.null(status) && status != 0L)) return(NA_character_)
  strsplit(result[[1L]], "[[:space:]]+")[[1L]][[1L]]
}

peak_ram_gib <- function() {
  path <- "/proc/self/status"
  if (!file.exists(path)) return(NA_real_)
  line <- grep("^VmHWM:", readLines(path, warn = FALSE), value = TRUE)
  if (!length(line)) return(NA_real_)
  kib <- suppressWarnings(as.numeric(gsub("[^0-9.]", "", line[[1L]])))
  kib / (1024^2)
}

package_version_or_missing <- function(package) {
  if (!requireNamespace(package, quietly = TRUE)) return("MISSING")
  as.character(utils::packageVersion(package))
}

safe_slot <- function(x, name, default = NULL) {
  if (!isS4(x) || !name %in% methods::slotNames(x)) return(default)
  tryCatch(methods::slot(x, name), error = function(e) default)
}

dimensions <- function(x) {
  value <- dim(x)
  if (is.null(value)) return(NULL)
  labels <- if (length(value) == 2L) c("rows", "columns") else paste0("dim", seq_along(value))
  stats::setNames(as.list(as.numeric(value)), labels)
}

head_tail_names <- function(x, n = 5L) {
  x <- as.character(x %||% character())
  list(
    count = length(x),
    first = unname(utils::head(x, n)),
    last = unname(utils::tail(x, n))
  )
}

matrix_summary <- function(x) {
  sparse <- inherits(x, "sparseMatrix")
  nonzero <- if (sparse && "x" %in% methods::slotNames(x)) {
    length(methods::slot(x, "x"))
  } else if (!is.null(dim(x)) && length(x) == 0L) {
    0
  } else {
    NA_real_
  }
  list(
    class = unname(class(x)),
    dimensions = dimensions(x),
    sparse = sparse,
    nonzero_entries = as.numeric(nonzero),
    object_size_bytes = as.numeric(utils::object.size(x)),
    row_names = head_tail_names(rownames(x)),
    column_names = head_tail_names(colnames(x))
  )
}

compact_atomic <- function(x, max_values = 20L) {
  if (is.null(x)) return(NULL)
  if (inherits(x, c("POSIXct", "POSIXlt", "Date"))) return(as.character(x))
  if (is.factor(x)) x <- as.character(x)
  if (is.atomic(x) && length(x) <= max_values) return(unname(x))
  list(class = unname(class(x)), length = as.numeric(length(x)))
}

structure_summary <- function(x, depth = 0L, max_depth = 3L) {
  out <- list(
    class = unname(class(x)),
    type = typeof(x),
    length = as.numeric(length(x)),
    dimensions = dimensions(x),
    object_size_bytes = as.numeric(utils::object.size(x))
  )

  if (is.null(x)) return(out)
  if (inherits(x, "sparseMatrix")) {
    out$nonzero_entries <- if ("x" %in% methods::slotNames(x)) {
      as.numeric(length(methods::slot(x, "x")))
    } else {
      NA_real_
    }
    out$row_names <- head_tail_names(rownames(x))
    out$column_names <- head_tail_names(colnames(x))
    return(out)
  }
  if (is.data.frame(x)) {
    out$fields <- unname(names(x))
    out$field_classes <- lapply(x, function(value) unname(class(value)))
    return(out)
  }
  if (is.matrix(x) || is.array(x)) {
    out$row_names <- head_tail_names(rownames(x))
    out$column_names <- head_tail_names(colnames(x))
    return(out)
  }
  if (depth >= max_depth) {
    out$children_truncated <- TRUE
    return(out)
  }
  if (isS4(x)) {
    slots <- methods::slotNames(x)
    out$slots <- stats::setNames(lapply(slots, function(name) {
      structure_summary(safe_slot(x, name), depth + 1L, max_depth)
    }), slots)
    return(out)
  }
  if (is.list(x)) {
    if (!length(x)) {
      out$items <- list()
      return(out)
    }
    child_names <- names(x)
    if (is.null(child_names)) child_names <- paste0("item_", seq_along(x))
    child_names[!nzchar(child_names)] <- paste0("item_", which(!nzchar(child_names)))
    out$items <- stats::setNames(lapply(x, function(value) {
      structure_summary(value, depth + 1L, max_depth)
    }), make.unique(child_names))
    return(out)
  }
  if (is.atomic(x)) out$values <- compact_atomic(x)
  out
}

table_records <- function(x, name_field, count_field = "nuclei") {
  value <- table(x, useNA = "ifany")
  lapply(seq_along(value), function(i) {
    stats::setNames(
      list(as.character(names(value)[[i]]), as.numeric(value[[i]])),
      c(name_field, count_field)
    )
  })
}

cell_coverage <- function(cell_names, metadata, donor_field, cell_type_field) {
  if (is.null(cell_names) || !length(cell_names)) {
    return(list(cells = 0, metadata_rows_matched = 0, donors = 0, fine_cell_types = 0))
  }
  index <- match(cell_names, rownames(metadata))
  matched <- !is.na(index)
  donor_values <- if (donor_field %in% names(metadata)) {
    trimws(as.character(metadata[[donor_field]][index[matched]]))
  } else {
    character()
  }
  type_values <- if (cell_type_field %in% names(metadata)) {
    trimws(as.character(metadata[[cell_type_field]][index[matched]]))
  } else {
    character()
  }
  donor_values <- donor_values[!is.na(donor_values) & nzchar(donor_values)]
  type_values <- type_values[!is.na(type_values) & nzchar(type_values)]
  list(
    cells = length(cell_names),
    metadata_rows_matched = sum(matched),
    metadata_rows_missing = sum(!matched),
    donors = length(unique(donor_values)),
    fine_cell_types = length(unique(type_values))
  )
}

get_assay_layer_names <- function(assay) {
  value <- tryCatch(SeuratObject::Layers(assay), error = function(e) character())
  if (length(value)) return(as.character(value))
  intersect(c("counts", "data", "scale.data"), methods::slotNames(assay))
}

get_assay_layer <- function(assay, layer) {
  if (isS4(assay) && layer %in% methods::slotNames(assay)) {
    return(safe_slot(assay, layer))
  }
  tryCatch(
    SeuratObject::LayerData(assay, layer = layer),
    error = function(e) NULL
  )
}

summarize_assay <- function(assay, metadata, donor_field, cell_type_field) {
  layer_names <- get_assay_layer_names(assay)
  layers <- stats::setNames(lapply(layer_names, function(layer_name) {
    value <- get_assay_layer(assay, layer_name)
    if (is.null(value)) return(list(error = "Layer could not be read"))
    result <- matrix_summary(value)
    result$role <- if (grepl("^counts($|[.])", layer_name)) {
      "raw_counts"
    } else if (grepl("^data($|[.])", layer_name)) {
      "normalized_expression"
    } else if (grepl("^scale[.]data($|[.])", layer_name)) {
      "scaled_expression"
    } else {
      "other"
    }
    result$biological_coverage <- cell_coverage(
      colnames(value), metadata, donor_field, cell_type_field
    )
    if (identical(result$role, "raw_counts") && inherits(value, "sparseMatrix") &&
      "x" %in% methods::slotNames(value)) {
      result$total_raw_counts <- as.numeric(sum(methods::slot(value, "x")))
    }
    result
  }), layer_names)

  variable_features <- safe_slot(assay, "var.features")
  if (is.null(variable_features)) {
    variable_features <- tryCatch(SeuratObject::VariableFeatures(assay), error = function(e) character())
  }
  feature_metadata <- safe_slot(assay, "meta.features")
  assay_misc <- safe_slot(assay, "misc")
  key <- tryCatch(SeuratObject::Key(assay), error = function(e) safe_slot(assay, "key", ""))

  list(
    class = unname(class(assay)),
    slots = unname(methods::slotNames(assay)),
    key = as.character(key %||% ""),
    original_assay = compact_atomic(safe_slot(assay, "assay.orig")),
    layers = layers,
    variable_features = list(
      count = length(variable_features %||% character()),
      names = head_tail_names(variable_features %||% character())
    ),
    feature_metadata = if (is.null(feature_metadata)) NULL else list(
      dimensions = dimensions(feature_metadata),
      fields = unname(names(feature_metadata))
    ),
    misc = structure_summary(assay_misc, max_depth = 1L)
  )
}

summarize_metadata <- function(metadata, donor_field, cell_type_field) {
  fields <- unname(names(metadata))
  field_classes <- stats::setNames(lapply(metadata, function(x) unname(class(x))), fields)
  result <- list(
    dimensions = dimensions(metadata),
    fields = fields,
    field_classes = field_classes,
    row_names = head_tail_names(rownames(metadata)),
    donor_field = donor_field,
    fine_cell_type_field = cell_type_field,
    donor_field_present = donor_field %in% fields,
    fine_cell_type_field_present = cell_type_field %in% fields
  )
  if (!donor_field %in% fields || !cell_type_field %in% fields) return(result)

  donor <- trimws(as.character(metadata[[donor_field]]))
  fine_type <- trimws(as.character(metadata[[cell_type_field]]))
  donor_ok <- !is.na(donor) & nzchar(donor)
  type_ok <- !is.na(fine_type) & nzchar(fine_type)
  donors <- sort(unique(donor[donor_ok]))
  fine_types <- sort(unique(fine_type[type_ok]))

  donors_by_type <- lapply(fine_types, function(label) {
    sort(unique(donor[fine_type == label & donor_ok]))
  })
  names(donors_by_type) <- fine_types
  cell_type_summary <- lapply(fine_types, function(label) {
    index <- !is.na(fine_type) & fine_type == label
    list(
      fine_cell_type = label,
      nuclei = sum(index),
      donors = length(unique(donor[index & donor_ok])),
      missing_donor_ids = sum(index & !donor_ok)
    )
  })

  donor_type_counts <- table(unlist(donors_by_type, use.names = FALSE))
  coverage_distribution <- table(as.numeric(donor_type_counts))
  nuclei_per_donor <- table(donor[donor_ok])
  quantiles <- stats::quantile(
    as.numeric(nuclei_per_donor), c(0, 0.25, 0.5, 0.75, 1),
    names = FALSE, type = 7
  )
  observed_pairs <- sum(vapply(donors_by_type, length, integer(1)))
  possible_pairs <- length(donors) * length(fine_types)

  result$missing_donor_ids <- sum(!donor_ok)
  result$missing_fine_cell_types <- sum(!type_ok)
  result$donors <- length(donors)
  result$fine_cell_types <- length(fine_types)
  result$fine_cell_type_summary <- cell_type_summary
  result$donor_cell_type_coverage <- list(
    observed_pairs = observed_pairs,
    possible_pairs = possible_pairs,
    coverage_fraction = if (possible_pairs > 0L) observed_pairs / possible_pairs else NA_real_,
    donors_by_number_of_fine_cell_types = lapply(seq_along(coverage_distribution), function(i) {
      list(
        fine_cell_types_per_donor = as.numeric(names(coverage_distribution)[[i]]),
        donors = as.numeric(coverage_distribution[[i]])
      )
    })
  )
  result$nuclei_per_donor <- list(
    minimum = unname(quantiles[[1L]]),
    first_quartile = unname(quantiles[[2L]]),
    median = unname(quantiles[[3L]]),
    mean = mean(as.numeric(nuclei_per_donor)),
    third_quartile = unname(quantiles[[4L]]),
    maximum = unname(quantiles[[5L]])
  )
  result
}

summarize_reduction <- function(reduction, metadata, donor_field, cell_type_field, assays) {
  embeddings <- safe_slot(reduction, "cell.embeddings", matrix(numeric(), 0, 0))
  assay_used <- as.character(safe_slot(reduction, "assay.used", ""))
  list(
    class = unname(class(reduction)),
    slots = unname(methods::slotNames(reduction)),
    key = as.character(safe_slot(reduction, "key", "")),
    assay_used = assay_used,
    assay_used_is_present = !nzchar(assay_used) || assay_used %in% assays,
    global = isTRUE(safe_slot(reduction, "global", FALSE)),
    cell_embeddings = matrix_summary(embeddings),
    biological_coverage = cell_coverage(
      rownames(embeddings), metadata, donor_field, cell_type_field
    ),
    feature_loadings = matrix_summary(
      safe_slot(reduction, "feature.loadings", matrix(numeric(), 0, 0))
    ),
    projected_feature_loadings = matrix_summary(
      safe_slot(reduction, "feature.loadings.projected", matrix(numeric(), 0, 0))
    ),
    standard_deviations = compact_atomic(safe_slot(reduction, "stdev", numeric())),
    misc = structure_summary(safe_slot(reduction, "misc"), max_depth = 1L)
  )
}

summarize_command <- function(command) {
  params <- safe_slot(command, "params", list())
  list(
    class = unname(class(command)),
    command = as.character(safe_slot(command, "name", "")),
    timestamp = as.character(safe_slot(command, "time.stamp", "")),
    assay_used = as.character(safe_slot(command, "assay.used", "")),
    call_string = as.character(safe_slot(command, "call.string", "")),
    parameters = if (is.list(params)) lapply(params, compact_atomic) else compact_atomic(params)
  )
}

summarize_named_components <- function(x, max_depth = 1L) {
  if (is.null(x) || !length(x)) return(list())
  component_names <- names(x)
  if (is.null(component_names)) component_names <- paste0("item_", seq_along(x))
  stats::setNames(lapply(x, structure_summary, max_depth = max_depth), component_names)
}

primary_layer_matrix <- function(object, assay_name) {
  if (!nzchar(assay_name) || !assay_name %in% names(object@assays)) return(NULL)
  assay <- object@assays[[assay_name]]
  layers <- get_assay_layer_names(assay)
  preferred <- c("counts", grep("^counts[.]", layers, value = TRUE), layers)
  preferred <- unique(preferred[preferred %in% layers])
  if (!length(preferred)) return(NULL)
  get_assay_layer(assay, preferred[[1L]])
}

summarize_rds <- function(path, manifest_row, args) {
  started <- Sys.time()
  info <- file.info(path)
  message("Reading ", path)
  object <- readRDS(path)
  if (!inherits(object, "Seurat")) {
    stop("Object is not a Seurat object; observed class: ", paste(class(object), collapse = ";"))
  }

  metadata <- object@meta.data
  assay_names <- names(object@assays)
  default_assay <- as.character(object@active.assay %||% "")
  assay_summaries <- stats::setNames(lapply(assay_names, function(name) {
    message("  assay: ", name)
    summarize_assay(
      object@assays[[name]], metadata, args$donor_field, args$cell_type_field
    )
  }), assay_names)
  metadata_summary <- summarize_metadata(
    metadata, args$donor_field, args$cell_type_field
  )

  identities <- object@active.ident
  identity_values <- as.character(identities)
  identity_summary <- list(
    length = length(identities),
    levels = unname(levels(identities) %||% sort(unique(identity_values))),
    counts = table_records(identity_values, "identity"),
    matches_fine_cell_type = if (args$cell_type_field %in% names(metadata)) {
      identical(identity_values, as.character(metadata[[args$cell_type_field]]))
    } else {
      NA
    }
  )

  reduction_names <- names(object@reductions)
  reductions <- stats::setNames(lapply(reduction_names, function(name) {
    summarize_reduction(
      object@reductions[[name]], metadata, args$donor_field,
      args$cell_type_field, assay_names
    )
  }), reduction_names)

  command_names <- names(object@commands)
  commands <- stats::setNames(lapply(object@commands, summarize_command), command_names)
  tools <- summarize_named_components(object@tools, args$max_tool_depth)
  misc <- structure_summary(object@misc, max_depth = args$max_tool_depth)

  primary <- primary_layer_matrix(object, default_assay)
  primary_features <- if (is.null(primary)) character() else rownames(primary)
  canonical_mtdna <- c(
    "MT-ND1", "MT-ND2", "MT-CO1", "MT-CO2", "MT-ATP8", "MT-ATP6",
    "MT-CO3", "MT-ND3", "MT-ND4L", "MT-ND4", "MT-ND5", "MT-ND6", "MT-CYB"
  )

  clinical_fields <- c(
    "sex", "msex", "diagnosis", "apoe_genotype", "apoe_group",
    "age_death", "age_death_numeric", "pmi", "pmi_numeric", "individualID"
  )
  finished <- Sys.time()
  result <- list(
    status = "complete",
    rds_id = as.character(manifest_row$rds_id[[1L]]),
    source_file = normalizePath(path, mustWork = TRUE),
    source_file_name = basename(path),
    source_file_bytes = as.numeric(info$size[[1L]]),
    source_file_modified_utc = format(info$mtime[[1L]], tz = "UTC", usetz = TRUE),
    source_file_sha256 = if (isTRUE(args$hash)) sha256_file(path) else NULL,
    manifest = lapply(manifest_row, function(x) compact_atomic(x[[1L]])),
    object = list(
      class = unname(class(object)),
      version = as.character(object@version),
      project_name = as.character(object@project.name),
      top_level_slots = unname(methods::slotNames(object)),
      object_size_bytes = as.numeric(utils::object.size(object)),
      active_assay = default_assay,
      assays = assay_names
    ),
    overview = list(
      features = if (is.null(primary)) NA_real_ else nrow(primary),
      nuclei = nrow(metadata),
      donors = metadata_summary$donors %||% NA_real_,
      fine_cell_types = metadata_summary$fine_cell_types %||% NA_real_,
      mitochondrial_protein_genes_present = intersect(canonical_mtdna, primary_features),
      mitochondrial_protein_genes_missing = setdiff(canonical_mtdna, primary_features)
    ),
    assays = assay_summaries,
    metadata = metadata_summary,
    active_identity = identity_summary,
    reductions = reductions,
    graphs = summarize_named_components(object@graphs, max_depth = 1L),
    neighbors = summarize_named_components(object@neighbors, max_depth = 2L),
    images = summarize_named_components(object@images, max_depth = 2L),
    commands = commands,
    tools = tools,
    misc = misc,
    clinical_fields_present = intersect(clinical_fields, names(metadata)),
    clinical_fields_absent = setdiff(clinical_fields, names(metadata)),
    inspection = list(
      started_utc = format(started, tz = "UTC", usetz = TRUE),
      finished_utc = format(finished, tz = "UTC", usetz = TRUE),
      elapsed_seconds = as.numeric(difftime(finished, started, units = "secs")),
      process_peak_ram_gib = peak_ram_gib()
    )
  )
  rm(primary, object)
  result
}

args <- parse_cli(commandArgs(trailingOnly = TRUE))

required_packages <- c("jsonlite", "Matrix", "SeuratObject", "Seurat")
missing_packages <- required_packages[
  !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_packages)) {
  stop("Missing required R packages: ", paste(missing_packages, collapse = ", "), call. = FALSE)
}

invocation_root <- normalizePath(getwd(), mustWork = TRUE)
project_root <- normalizePath(absolute_path(args$project_root, invocation_root), mustWork = TRUE)
manifest_path <- absolute_path(args$manifest, project_root)
output_path <- absolute_path(args$output, project_root)
if (!file.exists(manifest_path)) stop("Manifest does not exist: ", manifest_path, call. = FALSE)

manifest <- read.delim(manifest_path, check.names = FALSE, stringsAsFactors = FALSE)
required_manifest_fields <- c("rds_id", "input_rds", "enabled")
missing_manifest_fields <- setdiff(required_manifest_fields, names(manifest))
if (length(missing_manifest_fields)) {
  stop("Manifest is missing fields: ", paste(missing_manifest_fields, collapse = ", "), call. = FALSE)
}
enabled <- toupper(trimws(as.character(manifest$enabled))) %in% c("TRUE", "T", "1", "YES")
manifest <- manifest[enabled, , drop = FALSE]
if (!is.null(args$rds_id)) {
  requested <- trimws(strsplit(args$rds_id, ",", fixed = TRUE)[[1L]])
  unknown <- setdiff(requested, manifest$rds_id)
  if (length(unknown)) stop("Unknown or disabled --rds-id values: ", paste(unknown, collapse = ", "))
  manifest <- manifest[match(requested, manifest$rds_id), , drop = FALSE]
}
if (!nrow(manifest)) stop("No enabled manifest rows were selected", call. = FALSE)

input_root <- if (is.null(args$input_root)) NULL else {
  normalizePath(absolute_path(args$input_root, project_root), mustWork = TRUE)
}
resolve_input <- function(manifest_value) {
  if (!is.null(input_root)) return(file.path(input_root, basename(manifest_value)))
  absolute_path(manifest_value, project_root)
}
input_paths <- vapply(manifest$input_rds, resolve_input, character(1))
missing_inputs <- input_paths[!file.exists(input_paths)]
if (length(missing_inputs)) {
  stop("Input RDS files do not exist:\n", paste("  ", missing_inputs, collapse = "\n"), call. = FALSE)
}

new_bundle <- function() {
  list(
    schema_version = "rds_structure_summary_bundle_v1",
    generated_by = "scripts/16_export_rds_structure_summaries.R",
    project_root = project_root,
    manifest_file = normalizePath(manifest_path, mustWork = TRUE),
    input_root_override = input_root,
    output_file = output_path,
    donor_field = args$donor_field,
    fine_cell_type_field = args$cell_type_field,
    requested_rds_ids = unname(as.character(manifest$rds_id)),
    environment = list(
      host = Sys.info()[["nodename"]],
      R_version = R.version.string,
      platform = R.version$platform,
      packages = stats::setNames(
        lapply(required_packages, package_version_or_missing), required_packages
      )
    ),
    run = list(status = "running", started_utc = format(Sys.time(), tz = "UTC", usetz = TRUE)),
    objects = list()
  )
}

bundle <- if (file.exists(output_path) && !isTRUE(args$force)) {
  message("Resuming from ", output_path)
  value <- jsonlite::fromJSON(output_path, simplifyVector = FALSE)
  if (!identical(value$schema_version, "rds_structure_summary_bundle_v1")) {
    stop("Existing output has an incompatible schema; use --force to replace it", call. = FALSE)
  }
  value$requested_rds_ids <- unname(as.character(manifest$rds_id))
  value$run$status <- "running"
  value$run$resumed_utc <- format(Sys.time(), tz = "UTC", usetz = TRUE)
  value
} else {
  new_bundle()
}

for (i in seq_len(nrow(manifest))) {
  row <- manifest[i, , drop = FALSE]
  rds_id <- as.character(row$rds_id[[1L]])
  path <- input_paths[[i]]
  info <- file.info(path)
  previous <- bundle$objects[[rds_id]]
  unchanged_complete <- !is.null(previous) && identical(previous$status, "complete") &&
    isTRUE(as.numeric(previous$source_file_bytes) == as.numeric(info$size[[1L]])) &&
    identical(previous$source_file_modified_utc, format(info$mtime[[1L]], tz = "UTC", usetz = TRUE))
  if (unchanged_complete && !isTRUE(args$force)) {
    message("Skipping completed unchanged object: ", rds_id)
    next
  }

  message("[", i, "/", nrow(manifest), "] Inspecting ", rds_id)
  entry <- tryCatch(
    summarize_rds(path, row, args),
    error = function(e) list(
      status = "error",
      rds_id = rds_id,
      source_file = path,
      source_file_bytes = as.numeric(info$size[[1L]]),
      source_file_modified_utc = format(info$mtime[[1L]], tz = "UTC", usetz = TRUE),
      error = conditionMessage(e),
      error_call = paste(deparse(conditionCall(e)), collapse = " "),
      failed_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
      process_peak_ram_gib = peak_ram_gib()
    )
  )
  bundle$objects[[rds_id]] <- entry
  bundle$run$last_checkpoint_utc <- format(Sys.time(), tz = "UTC", usetz = TRUE)
  atomic_write_json(bundle, output_path)
  gc(verbose = FALSE, full = TRUE)
}

selected_status <- vapply(as.character(manifest$rds_id), function(id) {
  bundle$objects[[id]]$status %||% "missing"
}, character(1))
bundle$run$status <- if (all(selected_status == "complete")) "complete" else "incomplete"
bundle$run$completed_rds <- sum(selected_status == "complete")
bundle$run$failed_rds <- sum(selected_status == "error")
bundle$run$missing_rds <- sum(selected_status == "missing")
bundle$run$finished_utc <- format(Sys.time(), tz = "UTC", usetz = TRUE)
atomic_write_json(bundle, output_path)

message("Wrote ", output_path)
message(
  "Status: ", bundle$run$status,
  "; complete=", bundle$run$completed_rds,
  "; failed=", bundle$run$failed_rds,
  "; missing=", bundle$run$missing_rds
)
if (!identical(bundle$run$status, "complete")) quit(status = 1L)
