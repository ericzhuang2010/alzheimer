sha256_file <- function(path) {
  require_kda_packages("digest")
  if (!file.exists(path) || dir.exists(path)) {
    kda_abort("Cannot calculate SHA-256; file does not exist: %s", path)
  }
  unname(digest::digest(file = path, algo = "sha256", serialize = FALSE))
}

sha256_character_vector <- function(value) {
  require_kda_packages("digest")
  value <- sort(unique(as.character(value)), method = "radix")
  digest::digest(paste(value, collapse = "\n"), algo = "sha256", serialize = FALSE)
}

git_revision <- function(project_root = find_project_root(), short = FALSE) {
  arguments <- c("-C", project_root, "rev-parse")
  if (isTRUE(short)) arguments <- c(arguments, "--short")
  arguments <- c(arguments, "HEAD")
  output <- tryCatch(
    system2("git", arguments, stdout = TRUE, stderr = FALSE),
    error = function(...) character()
  )
  if (length(output) == 1L && nzchar(output)) output else NA_character_
}

utc_timestamp <- function(time = Sys.time()) {
  format(time, tz = "UTC", usetz = TRUE, format = "%Y-%m-%dT%H:%M:%SZ")
}

ensure_parent_directory <- function(path) {
  parent <- dirname(path)
  if (!dir.exists(parent) && !dir.create(parent, recursive = TRUE, showWarnings = FALSE)) {
    kda_abort("Could not create output directory: %s", parent)
  }
  invisible(parent)
}

temporary_output_path <- function(path) {
  suffix <- if (endsWith(path, ".gz")) ".tmp.tsv.gz" else ".tmp"
  file.path(
    dirname(path),
    sprintf(".%s.%d.%s%s", basename(path), Sys.getpid(), as.integer(Sys.time()), suffix)
  )
}

publish_file <- function(temporary_path, final_path) {
  if (!file.exists(temporary_path)) {
    kda_abort("Temporary output was not created: %s", temporary_path)
  }
  if (file.exists(final_path) && !unlink(final_path)) {
    kda_abort("Could not replace existing output: %s", final_path)
  }
  if (!file.rename(temporary_path, final_path)) {
    kda_abort("Could not atomically publish output: %s", final_path)
  }
  invisible(final_path)
}

atomic_write_tsv <- function(table, path) {
  require_kda_packages("data.table")
  ensure_parent_directory(path)
  temporary_path <- temporary_output_path(path)
  on.exit(if (file.exists(temporary_path)) unlink(temporary_path), add = TRUE)
  data.table::fwrite(
    data.table::as.data.table(table),
    file = temporary_path,
    sep = "\t",
    quote = FALSE,
    na = "NA",
    compress = if (endsWith(path, ".gz")) "gzip" else "none"
  )
  publish_file(temporary_path, path)
}

atomic_write_json <- function(value, path) {
  require_kda_packages("jsonlite")
  ensure_parent_directory(path)
  temporary_path <- temporary_output_path(path)
  on.exit(if (file.exists(temporary_path)) unlink(temporary_path), add = TRUE)
  jsonlite::write_json(
    value,
    path = temporary_path,
    auto_unbox = TRUE,
    pretty = TRUE,
    null = "null",
    na = "null",
    digits = NA
  )
  write("\n", file = temporary_path, append = TRUE)
  publish_file(temporary_path, path)
}

atomic_save_rds <- function(value, path) {
  ensure_parent_directory(path)
  temporary_path <- temporary_output_path(path)
  on.exit(if (file.exists(temporary_path)) unlink(temporary_path), add = TRUE)
  saveRDS(value, file = temporary_path, version = 3L)
  publish_file(temporary_path, path)
}

read_tsv <- function(path, ...) {
  require_kda_packages("data.table")
  if (!file.exists(path)) {
    kda_abort("Input file does not exist: %s", path)
  }
  tryCatch(
    data.table::fread(path, sep = "\t", header = TRUE, data.table = TRUE, ...),
    error = function(condition) {
      kda_abort("Could not read TSV %s: %s", path, conditionMessage(condition))
    }
  )
}

read_network_file <- function(path, require_dag = TRUE) {
  require_kda_packages("data.table")
  if (!file.exists(path)) {
    kda_abort("Network file does not exist: %s", path)
  }
  field_counts <- utils::count.fields(
    path, sep = "\t", quote = "", blank.lines.skip = FALSE, comment.char = ""
  )
  if (!length(field_counts) || any(field_counts != 2L)) {
    bad_line <- if (length(field_counts)) which(field_counts != 2L)[1L] else 1L
    observed <- if (length(field_counts)) field_counts[[bad_line]] else 0L
    kda_abort("Network must have exactly two tab-delimited fields on every line; line %d has %d: %s",
              bad_line, observed, path)
  }
  network <- tryCatch(
    data.table::fread(
      path,
      sep = "\t",
      header = FALSE,
      col.names = c("from", "to"),
      colClasses = "character",
      data.table = FALSE,
      fill = FALSE,
      blank.lines.skip = TRUE
    ),
    error = function(condition) {
      kda_abort("Could not read network %s: %s", path, conditionMessage(condition))
    }
  )
  if (ncol(network) != 2L) {
    kda_abort(
      "Network file must have exactly two tab-delimited columns; found %d in %s.",
      ncol(network),
      path
    )
  }
  validate_network(network, require_dag = require_dag)
}

read_run_manifest <- function(path) {
  validate_manifest(read_tsv(path))
}

read_membership_genes <- function(path, run_id, kind = "membership") {
  membership <- read_tsv(path, colClasses = c(run_id = "character", gene = "character"))
  missing_columns <- setdiff(c("run_id", "gene"), names(membership))
  if (length(missing_columns)) {
    kda_abort(
      "%s file %s is missing column(s): %s",
      kind,
      path,
      paste(missing_columns, collapse = ", ")
    )
  }
  selected_run_id <- run_id
  rows <- membership[run_id == selected_run_id]
  if (!nrow(rows)) {
    kda_abort("%s file contains no genes for run_id '%s': %s", kind, run_id, path)
  }
  normalize_gene_vector(rows$gene, sprintf("%s for %s", kind, run_id))
}

read_json_manifest <- function(path) {
  require_kda_packages("jsonlite")
  if (!file.exists(path)) return(NULL)
  tryCatch(
    jsonlite::read_json(path, simplifyVector = TRUE),
    error = function(condition) {
      kda_abort("Could not parse existing run manifest %s: %s", path, conditionMessage(condition))
    }
  )
}

values_match <- function(observed, expected) {
  if (is.null(observed) || is.null(expected)) return(is.null(observed) && is.null(expected))
  identical(as.character(observed), as.character(expected))
}

assert_compatible_completed_run <- function(manifest_path,
                                            expected,
                                            force = FALSE,
                                            label = "run") {
  existing <- read_json_manifest(manifest_path)
  if (is.null(existing)) return(FALSE)
  if (!identical(as.character(existing$status %||% ""), "complete")) {
    if (!isTRUE(force)) {
      kda_abort(
        "Output directory contains an incomplete %s manifest. Use --force after inspecting it: %s",
        label,
        manifest_path
      )
    }
    return(FALSE)
  }
  mismatches <- names(expected)[
    !vapply(names(expected), function(key) {
      values_match(existing[[key]], expected[[key]])
    }, logical(1L))
  ]
  if (length(mismatches)) {
    if (!isTRUE(force)) {
      kda_abort(
        "Completed %s output is incompatible in field(s) %s. Use --force or a new output directory.",
        label,
        paste(mismatches, collapse = ", ")
      )
    }
    return(FALSE)
  }
  TRUE
}

common_run_provenance <- function(project_root = find_project_root()) {
  list(
    git_commit = git_revision(project_root),
    r_version = as.character(getRversion()),
    kda_version = if (requireNamespace("KDA", quietly = TRUE)) {
      as.character(utils::packageVersion("KDA"))
    } else {
      NA_character_
    },
    wang_paper_version_label = "0.02",
    package_archive_version = KDA_EXPECTED_VERSION
  )
}

checksum_or_na <- function(path) {
  if (!is.null(path) && length(path) == 1L && file.exists(path) && !dir.exists(path)) {
    sha256_file(path)
  } else {
    NA_character_
  }
}

manifest_row_value <- function(row, name, default = NA_character_) {
  if (name %in% names(row)) as.character(row[[name]][[1L]]) else default
}
