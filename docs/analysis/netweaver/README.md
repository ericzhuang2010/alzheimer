# NetWeaver plotting code and generated figures

Yes—I generated three figures directly from the local R files.

## Plotting code inventory

| Category | R files |
|---|---|
| Canvas/tracks | `rc.plot.area.R`, `rc.plot.track.R`, `rc.plot.track.bg.R` |
| Genome structure | `rc.plot.ideogram.R` |
| Data tracks | `rc.plot.histogram.R`, `rc.plot.mHistogram.R`, `rc.plot.barchart.R`, `rc.plot.heatmap.R` |
| Markers/labels | `rc.plot.point.R`, `rc.plot.line.R`, `rc.plot.text.R`, `rc.plot.track.id.R` |
| Relationships | `rc.plot.link.R`, `rc.plot.ribbon.R` |
| Legends | `rc.plot.grColLegend.R` |
| Hierarchies | `rc.plot.sunburst.R`, `rc.plot.sunburst2.R` |

The supporting setup and geometry are primarily in `rc.initialize.R`, `rc.get.coordinates.R`, `rc.track.pos.R`, and `rc.get.params.R`.

Common input formats are:

- Intervals: `Chr`, `Start`, `End`
- Points/lines/text: `Chr`, `Pos`
- Links: `Chr1`, `Pos1`, `Chr2`, `Pos2`
- Ribbons: two chromosome intervals
- Sunburst: `child`, `parent`

## Generated figures

- [Plotting primitives demo](./netweaver_plotting_primitives.png) — ideogram, histograms, heatmap, stacked bars, points, lines, links, and ribbons
- [Coexpression module features](./netweaver_module_features.png) — bundled Alzheimer's/coexpression-module data
- [Donut chart](./netweaver_donut.png)

The reproducible driver is [generate_local_figures.R](./generate_local_figures.R). Run the original driver with:

```bash
Rscript untracked/NetWeaver/examples/generate_local_figures.R
```

All three PNGs rendered successfully and were visually checked. I left the core package code unchanged. One likely issue worth fixing later is [`rc.plot.ribbon.R`](../../../untracked/NetWeaver/R/rc.plot.ribbon.R), where the second interval appears to use `Start1` instead of `Start2`.
