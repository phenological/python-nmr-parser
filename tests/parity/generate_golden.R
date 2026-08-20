#!/usr/bin/env Rscript
# Generate golden values from the R nmr.parser for the parity tests.
#
# The two packages ship byte-identical fixtures, so R can be run over the same
# files Python reads and its answers recorded. Regenerate with:
#
#   Rscript tests/parity/generate_golden.R /path/to/r/nmr-parser
#
# and commit the result. The Python suite asserts against the recorded values,
# so running the tests does not need R.

args <- commandArgs(trailingOnly = TRUE)
rRepo <- if (length(args) > 0) args[1] else "~/git/phenological/nmr-parser"

suppressMessages(devtools::load_all(rRepo, quiet = TRUE))

here <- dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)))
data <- normalizePath(file.path(here, "..", "data"))
out <- list()

fixture <- function(...) file.path(data, ...)

# ---- lipoproteins ---------------------------------------------------------
lipoFile <- fixture("HB-COVID0001", "10", "pdata", "1", "lipo_results.xml")
lipo <- readLipo(lipoFile)
out$read_lipo <- list(
  version = lipo$version,
  n = nrow(lipo$data),
  id = as.character(lipo$data$id),
  value = as.numeric(lipo$data$value),
  unit = as.character(lipo$data$unit),
  refMax = as.numeric(lipo$data$refMax),
  refMin = as.numeric(lipo$data$refMin)
)

ext <- extend_lipo(lipo)
out$extend_lipo <- list(
  n = nrow(ext$data),
  id = as.character(ext$data$id),
  value = as.numeric(ext$data$value)
)

# ---- pacs -----------------------------------------------------------------
pacsFile <- fixture("plasma_pacs_report.xml")
pacs <- readPacs(pacsFile)
out$read_pacs <- list(
  version = pacs$version,
  n = nrow(pacs$data),
  name = as.character(pacs$data$name),
  conc_v = as.character(pacs$data$conc_v),
  refMax = as.character(pacs$data$refMax),
  refMin = as.character(pacs$data$refMin)
)

# ---- quantification, both document shapes ---------------------------------
quantFiles <- c(
  plasma_standard = fixture("HB-COVID0001", "10", "pdata", "1", "plasma_quant_report.xml"),
  plasma_extended = fixture("HB-COVID0001", "10", "pdata", "1", "plasma_quant_report_ver_1_0.xml"),
  urine_e = fixture("urine_quant_report_e.xml")
)
out$read_quant <- list()
for (nm in names(quantFiles)) {
  f <- quantFiles[[nm]]
  if (!file.exists(f)) next
  q <- readQuant(f)
  if (is.null(q)) next
  out$read_quant[[nm]] <- list(
    version = q$version,
    n = nrow(q$data),
    name = as.character(q$data$name),
    conc_v = as.character(q$data$conc_v),
    rawConc = as.character(q$data$rawConc),
    conc_vr = as.character(q$data$conc_vr),
    refMax = as.character(q$data$refMax),
    refMin = as.character(q$data$refMin)
  )
}

# ---- acquisition parameters ------------------------------------------------
acqus <- fixture("HB-COVID0001", "10", "acqus")
params <- c("BF1", "SW", "TE", "RG", "NS", "DE", "PULPROG", "SFO1", "O1", "TD", "SI")
out$read_param <- setNames(
  lapply(params, function(p) {
    v <- suppressWarnings(readParam(acqus, p))
    if (is.null(v)) NULL else if (is.character(v)) v else as.numeric(v)
  }),
  params
)

# ---- processed spectrum ----------------------------------------------------
spec <- readSpectrum(fixture("HB-COVID0001", "10"),
                     options = list(fromTo = c(-0.1, 10), length.out = 44079))
out$read_spectrum <- list(
  n = nrow(spec$spec),
  x_head = head(spec$spec$x, 5), x_tail = tail(spec$spec$x, 5),
  y_head = head(spec$spec$y, 5), y_tail = tail(spec$spec$y, 5),
  y_min = min(spec$spec$y), y_max = max(spec$spec$y), y_sum = sum(spec$spec$y),
  info = as.list(spec$info)
)

meta <- list(
  r_version = as.character(utils::packageVersion("nmr.parser")),
  generated_from = "tests/parity/generate_golden.R"
)

json <- jsonlite::toJSON(c(list(`_meta` = meta), out),
                         auto_unbox = TRUE, digits = NA, null = "null", pretty = TRUE)
writeLines(json, file.path(here, "golden_r.json"))
cat("wrote", file.path(here, "golden_r.json"), "\n")
