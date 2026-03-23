# QuickSight Plugin for Claude Code

The first comprehensive AWS QuickSight skill plugin for Claude Code. Build analyses, manage datasets, deploy dashboards, and embed analytics — all programmatically.

## Skills

| Skill | Triggers On | What It Covers |
|-------|------------|----------------|
| **analysis-builder** | "build analysis", "add visual", "create sheet", "CREATION_FAILED" | Python builder pattern, grid layout, visual types, field wells, filters, parameters, themes |
| **dataset-management** | "create dataset", "SPICE refresh", "invisible dataset", "data source" | Data sources, datasets, SPICE ingestion, permissions, refresh schedules, RLS |
| **deployment** | "deploy dashboard", "asset bundle", "migrate", "CI/CD", "template" | Asset bundle export/import, templates, dashboard publishing, CI/CD, rollback |
| **embedding** | "embed dashboard", "session tags", "QuickSight SDK", "CORS error" | Anonymous/registered embedding, JS SDK, React integration, multi-tenant RLS |

## Installation

```bash
claude plugin install rileypetersen/quicksight-plugin
```

## Prerequisites

- **AWS CLI v2** configured with appropriate profile
- **QuickSight Enterprise** subscription (Standard works for basic datasets but lacks embedding, hourly refresh, etc.)
- **IAM permissions** for `quicksight:*` operations on your account

## Reference Files

Shared reference files loaded on-demand by skills when deeper detail is needed:

| File | Content |
|------|---------|
| `references/api-gotchas.md` | Hard-won API pitfalls — invisible datasets, format nesting, key regex, debugging CREATION_FAILED |
| `references/visuals-kpi.md` | KPI, Gauge, Insight — flat field well pattern |
| `references/visuals-charts.md` | Bar, Line, Combo, Pie, Funnel — wrapped field well pattern |
| `references/visuals-tables.md` | Table, PivotTable, HeatMap — dual-mode and aggregated patterns |
| `references/visuals-comparison.md` | Scatter, Waterfall, BoxPlot, Histogram |
| `references/visuals-specialized.md` | TreeMap, Sankey, Radar, Geospatial, WordCloud |
| `references/format-patterns.md` | Number/currency/percentage formats, conditional formatting |
| `references/calculated-fields.md` | Expression syntax, window functions, common recipes |

## Templates

Starter scripts in `templates/` to bootstrap your project:

- **`build_analysis.py`** — Python builder skeleton with helper functions, argparse, `--dry-run` / `--push` modes
- **`refresh_datasets.sh`** — Shell script to bulk-refresh SPICE datasets

Copy these into your project and fill in the placeholder variables.

## Why This Plugin?

The QuickSight API is notoriously painful:
- Analysis definitions are **5,000–50,000 lines of JSON** with deeply nested, inconsistent structures
- Format configuration uses **double-nested** `FormatConfiguration` keys (yes, the same key name appears twice)
- Datasets created via API are **invisible to everyone** until you explicitly grant permissions
- Physical table map keys silently fail if they contain underscores
- `CREATION_FAILED` errors give no indication of which visual is broken

This plugin encodes hard-won knowledge from real production usage into structured skills that prevent hours of trial-and-error debugging.

## License

MIT
