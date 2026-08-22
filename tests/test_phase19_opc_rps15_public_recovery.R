#!/usr/bin/env Rscript

root <- normalizePath(file.path(dirname(commandArgs(trailingOnly = FALSE)[1]), ".."), mustWork = FALSE)
if (!file.exists(file.path(root, "scripts", "19_run_opc_rps15_finemapping.R"))) {
  root <- normalizePath(getwd())
}

run_self_test <- function(script) {
  output <- system2(
    "Rscript",
    c(file.path(root, "scripts", script), "--self-test"),
    stdout = TRUE,
    stderr = TRUE
  )
  status <- attr(output, "status")
  if (is.null(status)) status <- 0L
  stopifnot(status == 0L, any(grepl("_self_test_pass", output, fixed = TRUE)))
}

run_self_test("19_run_opc_rps15_finemapping.R")
run_self_test("19_run_opc_rps15_coloc.R")
cat("phase19_opc_rps15_R_tests_pass\n")
