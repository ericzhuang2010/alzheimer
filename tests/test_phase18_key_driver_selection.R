#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
root <- normalizePath(getwd(), mustWork = TRUE)
script <- file.path(root, "tests", "test_phase18_key_driver_selection.py")
status <- system2("python3", c(script, args))
quit(status = status)
