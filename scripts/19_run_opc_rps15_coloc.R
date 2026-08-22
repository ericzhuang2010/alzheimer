#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(coloc)
  library(data.table)
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
  stopifnot(requireNamespace("coloc", quietly = TRUE))
  stopifnot(all(c("p1", "p2", "p12") %in% names(formals(coloc::coloc.abf))))
  cat("coloc_self_test_pass\n")
  quit(status = 0L)
}

required <- c("gwas-rds", "qtl-rds", "output-tsv")
missing <- setdiff(required, names(args))
if (length(missing)) stop("Missing arguments: ", paste(missing, collapse = ", "))

gwas <- readRDS(args[["gwas-rds"]])
qtl <- readRDS(args[["qtl-rds"]])
stopifnot(is.list(gwas), is.list(qtl))
result <- coloc::coloc.susie(gwas, qtl)
summary <- as.data.table(result$summary, keep.rownames = "signal_pair")
fwrite(summary, args[["output-tsv"]], sep = "\t")
