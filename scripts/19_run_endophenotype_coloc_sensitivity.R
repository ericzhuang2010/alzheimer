#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(coloc))

args <- commandArgs(trailingOnly = TRUE)
value_after <- function(flag) {
  i <- match(flag, args)
  if (is.na(i) || i == length(args)) stop(paste("Missing", flag))
  args[[i + 1]]
}

manifest_path <- value_after("--manifest")
output_path <- value_after("--output")
manifest <- read.delim(manifest_path, stringsAsFactors = FALSE, check.names = FALSE)
p12_values <- c(1e-6, 5e-6, 1e-5)
output <- list()

for (i in seq_len(nrow(manifest))) {
  item <- manifest[i, ]
  matched <- read.delim(item$matched_file, stringsAsFactors = FALSE, check.names = FALSE)
  matched <- matched[
    is.finite(matched$gwas_beta) & is.finite(matched$gwas_se) & matched$gwas_se > 0 &
    is.finite(matched$qtl_beta) & is.finite(matched$qtl_se) & matched$qtl_se > 0,
  ]
  if (nrow(matched) < 500) next
  dataset1 <- list(
    beta = matched$gwas_beta,
    varbeta = matched$gwas_se^2,
    snp = matched$rsid,
    N = as.numeric(item$gwas_n),
    type = "quant",
    sdY = 1
  )
  dataset2 <- list(
    beta = matched$qtl_beta,
    varbeta = matched$qtl_se^2,
    snp = matched$rsid,
    N = as.numeric(item$qtl_n),
    type = "quant",
    sdY = 1
  )
  for (p12 in p12_values) {
    fit <- suppressWarnings(coloc.abf(
      dataset1 = dataset1,
      dataset2 = dataset2,
      p1 = 1e-4,
      p2 = 1e-4,
      p12 = p12
    ))
    summary <- fit$summary
    output[[length(output) + 1]] <- data.frame(
      trait_id = item$trait_id,
      qtl_source_id = item$qtl_source_id,
      molecular_trait = item$molecular_trait,
      qtl_accession = item$qtl_accession,
      qtl_context = item$qtl_context,
      p12 = p12,
      matched_variants = nrow(matched),
      pp_h0 = unname(summary[["PP.H0.abf"]]),
      pp_h1 = unname(summary[["PP.H1.abf"]]),
      pp_h2 = unname(summary[["PP.H2.abf"]]),
      pp_h3 = unname(summary[["PP.H3.abf"]]),
      pp_h4 = unname(summary[["PP.H4.abf"]]),
      conditional_h4 = unname(summary[["PP.H4.abf"]]) /
        (unname(summary[["PP.H3.abf"]]) + unname(summary[["PP.H4.abf"]])),
      method = "coloc.abf_single_signal_sensitivity_only",
      stringsAsFactors = FALSE
    )
  }
}

if (length(output) == 0) {
  write.table(data.frame(), output_path, sep = "\t", quote = FALSE, row.names = FALSE)
} else {
  result <- do.call(rbind, output)
  write.table(result, output_path, sep = "\t", quote = FALSE, row.names = FALSE)
}
