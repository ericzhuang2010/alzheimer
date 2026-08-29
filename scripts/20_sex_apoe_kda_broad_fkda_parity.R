#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 6L) {
  stop(
    paste(
      "Usage: Rscript --vanilla scripts/20_sex_apoe_kda_broad_fkda_parity.R",
      "FKDA_SOURCE NETWORK_TSV SIGNATURE_TSV BACKGROUND_SIZE NLAYERS OUTPUT_TSV"
    ),
    call. = FALSE
  )
}

fkda_source <- args[[1L]]
network_path <- args[[2L]]
signature_path <- args[[3L]]
background_size <- as.integer(args[[4L]])
n_layers <- as.integer(args[[5L]])
output_path <- args[[6L]]

stopifnot(
  file.exists(fkda_source),
  file.exists(network_path),
  file.exists(signature_path),
  is.finite(background_size), background_size > 0L,
  is.finite(n_layers), n_layers >= 1L
)

source(fkda_source, local = TRUE)

network <- read.delim(
  network_path, header = TRUE, sep = "\t", quote = "", comment.char = "",
  colClasses = "character", check.names = FALSE
)
signature <- read.delim(
  signature_path, header = TRUE, sep = "\t", quote = "", comment.char = "",
  colClasses = "character", check.names = FALSE
)
stopifnot(
  ncol(network) >= 2L, nrow(network) > 0L,
  all(c("Var", "Group") %in% names(signature)), nrow(signature) > 0L
)

result <- NULL
invisible(capture.output({
  result <- call_key_drivers(
    net = network[, 1:2, drop = FALSE],
    signature.df = signature[, c("Var", "Group"), drop = FALSE],
    nLayerToTest = n_layers,
    nLayersToExpand = 0L,
    bg.size = background_size,
    directed = TRUE,
    reduce.within.nlayer = 2L,
    fdr = 0.05,
    p.correction.method = "BH",
    return.overlap = TRUE
  )
}))

fields <- c(
  "Signature", "Keydriver", "BestLayer", "q", "m", "n", "k", "FE",
  "log.P.Value", "adj.P.Value", "is.signature", "is.root.node",
  "global.Keydriver", "Overlap.Items"
)

if (is.null(result) || !nrow(result)) {
  normalized <- as.data.frame(setNames(replicate(length(fields), character(), simplify = FALSE), fields))
} else {
  normalized <- as.data.frame(result, stringsAsFactors = FALSE, check.names = FALSE)
  for (field in setdiff(fields, names(normalized))) {
    normalized[[field]] <- if (field %in% c("is.signature", "is.root.node", "global.Keydriver")) {
      NA
    } else if (field %in% c("Signature", "Keydriver", "Overlap.Items")) {
      ""
    } else {
      NA_real_
    }
  }
  normalized <- normalized[, fields, drop = FALSE]
}

write.table(
  normalized, output_path, sep = "\t", quote = FALSE, row.names = FALSE,
  col.names = TRUE, na = "NA"
)
