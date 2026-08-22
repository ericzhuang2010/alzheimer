#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(susieR)
})

parse_args <- function(args) {
  out <- list()
  i <- 1L
  while (i <= length(args)) {
    key <- sub("^--", "", args[[i]])
    if (key == "self-test") {
      out[[key]] <- TRUE
      i <- i + 1L
    } else {
      stopifnot(i < length(args))
      out[[key]] <- args[[i + 1L]]
      i <- i + 2L
    }
  }
  out
}

args <- parse_args(commandArgs(trailingOnly = TRUE))
if (isTRUE(args[["self-test"]])) {
  z <- c(5, 0.2, -0.1)
  R <- diag(3)
  fit <- susie_rss(z = z, R = R, n = 1000, L = 1, estimate_residual_variance = FALSE)
  stopifnot(length(fit$pip) == 3L, all(is.finite(fit$pip)))
  cat("finemapping_self_test_pass\n")
  quit(status = 0L)
}

required <- c("input-rds", "output-rds", "summary-tsv")
missing <- setdiff(required, names(args))
if (length(missing)) stop("Missing arguments: ", paste(missing, collapse = ", "))

input <- readRDS(args[["input-rds"]])
stopifnot(is.list(input), all(c("z", "R", "n", "variant_id", "route_id") %in% names(input)))
stopifnot(length(input$z) == nrow(input$R), nrow(input$R) == ncol(input$R))
stopifnot(length(input$variant_id) == length(input$z))
L <- if (is.null(input$L)) 10L else input$L
fit <- susie_rss(
  z = input$z,
  R = input$R,
  n = input$n,
  L = L,
  estimate_residual_variance = FALSE,
  refine = TRUE
)
saveRDS(fit, args[["output-rds"]])
summary <- data.table(
  route_id = input$route_id,
  variant_id = input$variant_id,
  pip = fit$pip,
  converged = isTRUE(fit$converged)
)
fwrite(summary, args[["summary-tsv"]], sep = "\t")
