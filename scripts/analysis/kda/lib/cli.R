`%||%` <- function(x, y) {
  if (is.null(x) || length(x) == 0L || (length(x) == 1L && is.na(x))) y else x
}

kda_abort <- function(..., call. = FALSE) {
  stop(sprintf(...), call. = call.)
}

kda_warn <- function(...) {
  warning(sprintf(...), call. = FALSE, immediate. = TRUE)
}

kda_message <- function(...) {
  message(sprintf(...))
}

find_project_root <- function(start = getwd()) {
  current <- normalizePath(start, winslash = "/", mustWork = TRUE)
  repeat {
    if (file.exists(file.path(current, "renv.lock")) &&
        file.exists(file.path(current, ".Rprofile"))) {
      return(current)
    }
    parent <- dirname(current)
    if (identical(parent, current)) {
      kda_abort("Could not locate the project root above: %s", start)
    }
    current <- parent
  }
}

script_directory <- function() {
  file_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
  if (length(file_arg) != 1L) {
    kda_abort("Could not determine the executing R script path.")
  }
  dirname(normalizePath(sub("^--file=", "", file_arg), winslash = "/", mustWork = TRUE))
}

source_kda_libraries <- function(kda_script_dir,
                                 libraries = c(
                                   "kda_validation.R",
                                   "kda_io.R",
                                   "kda_core.R",
                                   "kda_enrichment.R"
                                 )) {
  for (library_file in libraries) {
    source(file.path(kda_script_dir, "lib", library_file), local = FALSE)
  }
  invisible(TRUE)
}

parse_kda_cli <- function(args,
                          value_options = character(),
                          flag_options = character(),
                          required = character(),
                          defaults = list(),
                          usage = NULL) {
  values <- defaults
  value_options <- unique(gsub("^--", "", value_options))
  flag_options <- unique(gsub("^--", "", flag_options))
  known <- c(value_options, flag_options, "help")

  index <- 1L
  while (index <= length(args)) {
    token <- args[[index]]
    if (!startsWith(token, "--")) {
      kda_abort("Unexpected positional argument: %s%s",
                token,
                if (!is.null(usage)) paste0("\n\n", usage) else "")
    }
    key_value <- sub("^--", "", token)
    if (grepl("=", key_value, fixed = TRUE)) {
      pieces <- strsplit(key_value, "=", fixed = TRUE)[[1L]]
      key <- pieces[[1L]]
      value <- paste(pieces[-1L], collapse = "=")
      if (!(key %in% value_options)) {
        kda_abort("Option --%s does not accept a value or is unknown.", key)
      }
      values[[key]] <- value
      index <- index + 1L
      next
    }

    key <- key_value
    if (!(key %in% known)) {
      kda_abort("Unknown option: --%s%s",
                key,
                if (!is.null(usage)) paste0("\n\n", usage) else "")
    }
    if (identical(key, "help")) {
      cat(usage %||% "No usage text is available.", "\n")
      quit(save = "no", status = 0L)
    }
    if (key %in% flag_options) {
      values[[key]] <- TRUE
      index <- index + 1L
      next
    }
    if (index == length(args) || startsWith(args[[index + 1L]], "--")) {
      kda_abort("Option --%s requires a value.", key)
    }
    values[[key]] <- args[[index + 1L]]
    index <- index + 2L
  }

  missing_options <- required[
    !vapply(required, function(key) {
      value <- values[[key]]
      !is.null(value) && length(value) == 1L && !is.na(value) && nzchar(value)
    }, logical(1L))
  ]
  if (length(missing_options)) {
    kda_abort("Missing required option(s): %s%s",
              paste0("--", missing_options, collapse = ", "),
              if (!is.null(usage)) paste0("\n\n", usage) else "")
  }
  values
}

as_integer_option <- function(value, option, minimum = NULL) {
  numeric_value <- suppressWarnings(as.numeric(value))
  valid <- length(numeric_value) == 1L && !is.na(numeric_value) &&
    is.finite(numeric_value) && numeric_value == as.integer(numeric_value)
  parsed <- if (valid) as.integer(numeric_value) else NA_integer_
  if (!valid || (!is.null(minimum) && parsed < minimum)) {
    qualifier <- if (is.null(minimum)) "an integer" else
      sprintf("an integer >= %d", minimum)
    kda_abort("--%s must be %s; received: %s", option, qualifier, value)
  }
  parsed
}

as_numeric_option <- function(value, option, minimum = NULL, maximum = NULL) {
  parsed <- suppressWarnings(as.numeric(value))
  if (length(parsed) != 1L || is.na(parsed) || !is.finite(parsed) ||
      (!is.null(minimum) && parsed < minimum) ||
      (!is.null(maximum) && parsed > maximum)) {
    kda_abort("--%s must be numeric%s; received: %s",
              option,
              if (!is.null(minimum) || !is.null(maximum)) {
                sprintf(" in [%s, %s]", minimum %||% "-Inf", maximum %||% "Inf")
              } else "",
              value)
  }
  parsed
}

resolve_project_path <- function(path, project_root = find_project_root()) {
  if (grepl("^/", path)) {
    return(normalizePath(path, winslash = "/", mustWork = FALSE))
  }
  normalizePath(file.path(project_root, path), winslash = "/", mustWork = FALSE)
}

project_relative_path <- function(path, project_root = find_project_root()) {
  normalized <- normalizePath(path, winslash = "/", mustWork = FALSE)
  root <- paste0(normalizePath(project_root, winslash = "/", mustWork = TRUE), "/")
  if (startsWith(normalized, root)) substring(normalized, nchar(root) + 1L) else normalized
}

safe_path_component <- function(value) {
  value <- trimws(as.character(value))
  value <- gsub("[^A-Za-z0-9_.-]+", "_", value)
  value <- gsub("_+", "_", value)
  value <- gsub("^[_ .-]+|[_ .-]+$", "", value)
  if (!nzchar(value) || value %in% c(".", "..")) {
    kda_abort("Value cannot be converted to a safe path component.")
  }
  value
}
