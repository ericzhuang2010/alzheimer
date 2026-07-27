#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE, warn = 1)

kda_dir <- dirname(normalizePath(
  sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1L]),
  winslash = "/", mustWork = TRUE
))
source(file.path(kda_dir, "lib", "cli.R"))
source_kda_libraries(kda_dir)

assert_true <- function(value, label) {
  if (!isTRUE(value)) kda_abort("Smoke test failed: %s", label)
  cat("ok -", label, "\n")
}

version <- assert_kda_available()
assert_true(identical(version, "0.2"), "KDA package version is exactly 0.2")
assert_true(
  all(KDA_REQUIRED_EXPORTS %in% getNamespaceExports("KDA")),
  "required KDA exports are present"
)

star <- data.frame(
  from = rep("DRIVER1", 10L),
  to = paste0("Q", seq_len(10L)),
  stringsAsFactors = FALSE
)
star_result <- run_global_driver_search(star, driver_search_layers = 6L, boost_hubs = TRUE)
assert_true(
  "DRIVER1" %in% star_result$parsed$drivers$keydrivers,
  "directed star recovers DRIVER1"
)
driver_row <- star_result$parsed$drivers[keydrivers == "DRIVER1"]
assert_true(
  nrow(driver_row) == 1L && driver_row$downstream[[1L]] == 10,
  "DRIVER1 has ten downstream genes"
)

reversed <- data.frame(from = star$to, to = star$from, stringsAsFactors = FALSE)
reversed_result <- run_global_driver_search(
  reversed, driver_search_layers = 6L, boost_hubs = TRUE
)
assert_true(
  is.null(reversed_result$raw) && nrow(reversed_result$parsed$drivers) == 0L,
  "reversing the star removes the original upstream-driver result"
)

chain <- data.frame(
  from = c("A", "B", "C", "A"),
  to = c("B", "C", "D", "E"),
  stringsAsFactors = FALSE
)
one_layer <- extract_driver_neighborhood(chain, "A", 1L, FALSE)
two_layers <- extract_driver_neighborhood(chain, "A", 2L, FALSE)
three_layers <- extract_driver_neighborhood(chain, "A", 3L, FALSE)
with_driver <- extract_driver_neighborhood(chain, "A", 3L, TRUE)
assert_true(setequal(one_layer, c("B", "E")), "one-layer direction is column 1 to column 2")
assert_true(setequal(two_layers, c("B", "C", "E")), "two-layer directed reachability")
assert_true(setequal(three_layers, c("B", "C", "D", "E")), "three-layer directed reachability")
assert_true(!"A" %in% three_layers, "driver is excluded from its neighborhood by default")
assert_true("A" %in% with_driver, "driver inclusion compatibility option works")
assert_true(
  length(extract_driver_neighborhood(chain, "D", 3L, FALSE)) == 0L,
  "leaf NULL neighborhood is normalized to empty"
)

reference <- hypergeometric_enrichment(100L, 10L, 20L, 5L)
assert_true(
  isTRUE(all.equal(reference$p_value, 0.025464546427043128, tolerance = 1e-14)),
  "one-sided hypergeometric P value matches reference"
)
assert_true(
  isTRUE(all.equal(reference$fold_enrichment, 2.5, tolerance = 1e-14)),
  "fold enrichment matches reference"
)
zero_neighborhood <- hypergeometric_enrichment(100L, 10L, 0L, 0L)
assert_true(
  identical(zero_neighborhood$p_value, 1) &&
    is.na(zero_neighborhood$fold_enrichment),
  "empty background neighborhood returns P=1 and undefined fold enrichment"
)
adjusted <- stats::p.adjust(c(0.01, 0.04, 0.20), method = "BH")
assert_true(
  isTRUE(all.equal(adjusted, c(0.03, 0.06, 0.20), tolerance = 1e-14)),
  "BH adjustment is applied within one signature"
)

expect_kda_error(
  validate_network(data.frame(from = "A", to = "A")),
  "self-edge"
)
expect_kda_error(
  validate_network(data.frame(from = c("A", "B"), to = c("B", "A"))),
  "cycle"
)
expect_kda_error(validate_positive_integer(1.5, "layers"), "positive integer")
expect_kda_error(validate_positive_integer(0, "layers"), "positive integer")
expect_kda_error(
  validate_query_background(
    query = c("A", "B"),
    background = c("A", "B", "C"),
    nodes = c("A", "B", "C")
  ),
  "at least 3"
)
expect_kda_error(
  validate_query_background(
    query = c("A", "B", "C"),
    background = c("A", "B", "C", "OUTSIDE"),
    nodes = c("A", "B", "C")
  ),
  "absent from the network"
)
malformed <- list(
  matrix("A", nrow = 1L, dimnames = list(NULL, "wrong")),
  matrix("x", nrow = 1L, dimnames = list(NULL, "setting")),
  matrix(c("A", "1"), nrow = 1L, dimnames = list(NULL, c("node", "downstream")))
)
expect_kda_error(
  parse_kda_global_result(malformed, c("A")),
  "missing"
)
cat("All KDA smoke tests passed.\n")
