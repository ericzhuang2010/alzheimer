#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 2)

source("scripts/12_run_kda.R")
source("scripts/NetWeaver/fKDA.R")

assert <- function(condition, message) {
  if (!isTRUE(condition)) stop(message, call. = FALSE)
}

expected_mapping <- c(
  "Ast GFAP" = "Astrocytes",
  "Exc L2-3 LINC00507" = "Excitatory_neurons",
  "Inh PVALB" = "Inhibitory_neurons",
  "OPC" = "OPCs",
  "Oli OPALIN" = "Oligodendrocytes",
  "End" = "Vasculature_cells",
  "Fib COL15A1" = "Vasculature_cells",
  "Per" = "Vasculature_cells",
  "SMC" = "Vasculature_cells",
  "CAMs" = "CAMs",
  "Mic P2RY12" = "Microglia",
  "T cells" = "T_cells"
)
observed_mapping <- vapply(names(expected_mapping), fine_to_network, character(1))
assert(identical(unname(observed_mapping), unname(expected_mapping)), "Fine-to-broad mapping failed")

assert(group_id_from("Female", "e2") == "F_e2", "Female e2 group ID failed")
assert(group_id_from("Male", "e33") == "M_e33", "Male e33 group ID failed")

member_up <- list(c("A", "B"), c("B", "C"))
member_down <- list(c("D", "X"), c("A", "E"))
pool_up <- sort(unique(unlist(member_up)))
pool_down <- sort(unique(unlist(member_down)))
pool_both <- sort(unique(c(pool_up, pool_down)))
assert(identical(pool_up, c("A", "B", "C")), "Pooled up union failed")
assert(identical(pool_down, c("A", "D", "E", "X")), "Pooled down union failed")
assert("A" %in% pool_up && "A" %in% pool_down, "Direction-discordant pooled gene was lost")
assert(identical(pool_both, c("A", "B", "C", "D", "E", "X")), "Pooled both union failed")

tested <- Reduce(intersect, list(c("A", "B", "C", "D"), c("B", "C", "D", "E")))
assert(identical(tested, c("B", "C", "D")), "Pooled tested-set intersection failed")
toy_net <- data.frame(from = c("A", "B", "C", "X"), to = c("B", "C", "D", "Y"))
induced <- toy_net[toy_net$from %in% tested & toy_net$to %in% tested, , drop = FALSE]
background <- sort(unique(c(induced$from, induced$to)))
assert(nrow(induced) == 2L && identical(background, c("B", "C", "D")), "Induced network failed")
assert(length(intersect(c("A", "B", "D"), background)) == 2L, "Effective query calculation failed")
assert(is_dag(toy_net), "DAG validation rejected a DAG")
assert(!is_dag(data.frame(from = c("A", "B"), to = c("B", "A"))), "DAG validation accepted a cycle")

fine <- c("End", "Fib FLRT2", "Fib COL15A1", "Per", "SMC")
primary <- c("F_e2", "F_e33", "F_e4", "M_e2", "M_e33", "M_e4")
pools <- c("female_pool", "male_pool", "e2_pool", "e33_pool", "e4_pool")
directions <- c("AD_up_mito", "AD_down_mito", "AD_both_mito")
ids <- c(
  unlist(lapply(fine, function(cell) unlist(lapply(primary, function(group) {
    vapply(directions, function(direction) safe_id("primary", cell, group, direction), character(1))
  })))),
  unlist(lapply(fine, function(cell) unlist(lapply(pools, function(group) {
    vapply(directions, function(direction) safe_id("secondary", cell, group, direction), character(1))
  }))))
)
assert(length(ids) == 165L && length(unique(ids)) == 165L, "Pilot run IDs are not complete and unique")

signature <- paste0("S", 1:10)
forward <- rbind(
  data.frame(from = "D", to = signature),
  data.frame(from = paste0("U", 1:99), to = paste0("U", 2:100))
)
reverse <- rbind(
  data.frame(from = signature, to = "D"),
  data.frame(from = paste0("U", 1:99), to = paste0("U", 2:100))
)
signature_df <- data.frame(Var = signature, Group = "toy", stringsAsFactors = FALSE)
forward_result <- suppressWarnings(capture.output({
  forward_kda <- call_key_drivers(
    forward, signature_df, nLayerToTest = 1, bg.size = 111,
    directed = TRUE, fdr = 0.05, return.overlap = TRUE
  )
}))
reverse_result <- suppressWarnings(capture.output({
  reverse_kda <- call_key_drivers(
    reverse, signature_df, nLayerToTest = 1, bg.size = 111,
    directed = TRUE, fdr = 0.05, return.overlap = TRUE
  )
}))
assert(!is.null(forward_kda) && "D" %in% forward_kda$Keydriver, "Directed positive-control KDA failed")
assert(is.null(reverse_kda) || !"D" %in% reverse_kda$Keydriver, "Direction reversal did not remove driver D")

empty <- empty_results()
assert(nrow(empty) == 0L && all(c("kda_run_id", "key_driver", "adjusted_p_value") %in% names(empty)),
       "Empty-result schema failed")

cat("Phase 12 deterministic tests passed\n")
