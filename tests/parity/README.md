# R/Python parity tests

These assert that this package returns the same values as the R
[`nmr.parser`](https://github.com/phenological/nmr-parser) for the same input.

That comparison is only meaningful because the two repositories ship the same
fixture files. At the time of writing, 277 files under `tests/data` here and
`inst/` there are byte-identical, with none differing.

## How it works

`generate_golden.R` runs the R package over the shared fixtures and writes
`golden_r.json`. The tests assert against that recorded file, so **running the
tests does not need R installed**.

## Regenerating

After a change on either side:

```bash
Rscript tests/parity/generate_golden.R ~/git/phenological/nmr-parser
```

and commit `golden_r.json` alongside whatever prompted it. The `_meta` block
records which R version produced it.

## What is covered

| Reader | Asserted |
| --- | --- |
| `read_lipo` | version, parameter order, `value`, `refMax`, `refMin`, on both report versions |
| `extend_lipo` | all 316 derived values, on both report versions |
| `read_pacs` | version, parameter order, `conc_v`, `refMax`, `refMin` |
| `read_quant` | both document shapes, five value columns |
| `read_param` | eleven acquisition parameters |
| `read_spectrum` | point count, both axis ends, intensity range and total |

## Report versions

The lipoprotein fixtures cover two: `lipo_results.xml` is `PL-5009-01/001`,
the older name the fixtures grew up with, and `plasma_lipo_report_1_1_0.xml`
is `/002`, which is what the instruments write now. They carry the same 112
parameters, units and reference ranges, so both are asserted to keep parity
tied to the version actually in use rather than only to the historical one.

## Known divergences

Two, both recorded rather than hidden.

**Row order in `extend_lipo`.** Python and R return the same 316 parameters
with the same values, in a different order: pandas `pivot` alphabetises the
raw block while R keeps Bruker's document order. Held as a strict `xfail` in
`test_parity_lipo.py`, so it will announce itself if it ever changes.

**Spline interpolation in `read_spectrum`.** R calls
`signal::interp1(method = "spline")`, Python calls
`scipy.interpolate.interp1d(kind = "cubic")`. The boundary conditions differ,
so intensities disagree by up to 3.2e-9 relative, largest at the ends. The ppm
axis is arithmetic on both sides and agrees to machine precision. Tolerances
are set accordingly and the reasoning is in the module docstring.
