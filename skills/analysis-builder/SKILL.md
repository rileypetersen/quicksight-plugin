---
name: analysis-builder
description: Build and modify AWS QuickSight analysis definitions programmatically. Use when asked to build a QuickSight analysis, add visuals or sheets, create KPIs/charts/tables, modify field wells, add filters or parameters, create calculated fields, add conditional formatting, debug CREATION_FAILED errors, or construct analysis definition JSON. Also use when encountering errors like FIELD_NOT_FOUND, INVALID_VISUAL_CONFIGURATION, or visuals rendering blank.
---

## Setup

Set AWS context for every command. All QuickSight API calls require account ID and region.

```bash
export QS_ACCOUNT=$ACCOUNT_ID
export QS_PROFILE=$PROFILE
export QS_REGION=$REGION
```

Two commands drive the workflow:

```bash
# Export current state — always do this before modifying
aws quicksight describe-analysis-definition \
  --aws-account-id $QS_ACCOUNT --profile $QS_PROFILE \
  --analysis-id $ANALYSIS_ID \
  --query 'Definition' > /tmp/qs-current.json

# Push updated definition
aws quicksight update-analysis \
  --aws-account-id $QS_ACCOUNT --profile $QS_PROFILE \
  --analysis-id $ANALYSIS_ID \
  --name "Analysis Name" \
  --definition file:///tmp/qs-analysis.json
```

The definition JSON is the complete analysis specification — typically 2,000 to 10,000+ lines for real dashboards. Never hand-edit it. Use a Python builder.

---

## Python Builder Pattern

Raw JSON is 5,000+ lines, repetitive, and one typo breaks the entire push. Use Python helpers to generate the definition. This eliminates copy-paste errors and makes layouts composable.

Start from `templates/build_analysis.py` in this plugin. The key helpers:

### Grid positioning

```python
def grid_element(visual_id, col, row, width, height):
    """Place a visual on the 36-column grid."""
    return {
        "ElementId": visual_id,
        "ElementType": "VISUAL",
        "ColumnIndex": col,
        "RowIndex": row,
        "ColumnSpan": width,
        "RowSpan": height,
    }
```

### Field ID generation

Field IDs must be unique across ALL visuals in the entire analysis. Use deterministic IDs derived from the dataset alias, column name, and visual context.

```python
def field_id(dataset_alias, column_name, suffix=""):
    """Generate a deterministic, unique field ID."""
    base = f"{dataset_alias}-{column_name}"
    return f"{base}-{suffix}" if suffix else base
```

### Field builders

```python
def measure_field(ds, col, agg="SUM", suffix="", prefix="", decimals=0):
    """NumericalMeasureField with optional format."""
    fid = field_id(ds, col, agg.lower())
    field = {"FieldId": fid, "Column": {"DataSetIdentifier": ds, "ColumnName": col},
             "AggregationFunction": {"SimpleNumericalAggregation": agg}}
    fmt = number_format(suffix=suffix, prefix=prefix, decimals=decimals)
    if fmt:
        field["FormatConfiguration"] = {"FormatConfiguration": {"NumberFormatConfiguration": {"FormatConfiguration": fmt}}}
    return {"NumericalMeasureField": field}

def dim_field_date(ds, col, granularity="DAY"):
    """DateDimensionField with hierarchy."""
    return {"DateDimensionField": {"FieldId": field_id(ds, col, "date"),
        "Column": {"DataSetIdentifier": ds, "ColumnName": col},
        "DateGranularity": granularity, "HierarchyId": field_id(ds, col, "hierarchy")}}

def dim_field_cat(ds, col):
    """CategoricalDimensionField."""
    return {"CategoricalDimensionField": {"FieldId": field_id(ds, col, "cat"),
        "Column": {"DataSetIdentifier": ds, "ColumnName": col}}}

def number_format(suffix="", prefix="", decimals=0):
    """Inner NumericFormatConfiguration. Prevents triple-nesting errors."""
    cfg = {"SeparatorConfiguration": {"DecimalSeparator": "DOT",
           "ThousandsSeparator": {"Symbol": "COMMA", "Visibility": "VISIBLE"}},
           "DecimalPlacesConfiguration": {"DecimalPlaces": decimals}}
    if suffix: cfg["Suffix"] = suffix
    if prefix: cfg["Prefix"] = prefix
    return {"NumericFormatConfiguration": cfg}

def unagg_field(ds, col, fmt=None):
    """Flat TableUnaggregatedFieldWells entry. No type wrapper."""
    entry = {"FieldId": field_id(ds, col, "unagg"),
             "Column": {"DataSetIdentifier": ds, "ColumnName": col}}
    if fmt: entry["FormatConfiguration"] = fmt
    return entry
```

### Script structure

```python
def build_definition():
    return {
        "DataSetIdentifierDeclarations": [
            {"Identifier": "my_dataset", "DataSetArn": f"arn:aws:quicksight:{REGION}:{ACCOUNT_ID}:dataset/{DATASET_ID}"}
        ],
        "Sheets": [build_overview_sheet(), build_detail_sheet()],
        "ParameterDeclarations": [...],
        "FilterGroups": [...],
        "CalculatedFields": [...],
        "AnalysisDefaults": {"DefaultNewSheetConfiguration": {
            "InteractiveLayoutConfiguration": {"Grid": {"CanvasSizeOptions": {
                "ScreenCanvasSizeOptions": {"ResizeOption": "FIXED", "OptimizedViewPortWidth": "1600px"}
            }}}
        }},
    }

if __name__ == "__main__":
    defn = build_definition()
    if "--dry-run" in sys.argv:
        with open("/tmp/qs-analysis.json", "w") as f:
            json.dump(defn, f, indent=2)
        print("Wrote /tmp/qs-analysis.json")
    elif "--push" in sys.argv:
        # Call update-analysis via subprocess or boto3
        ...
```

---

## Analysis Definition Structure

Top-level keys in the definition object:

```python
{
    "DataSetIdentifierDeclarations": [...],  # max 50 datasets
    "Sheets": [...],                          # max 20 sheets
    "ParameterDeclarations": [...],           # max 400 parameters
    "FilterGroups": [...],                    # max 2000 filter groups
    "CalculatedFields": [...],               # max 2000 calc fields
    "AnalysisDefaults": {...}                 # default sheet config
}
```

**DataSetIdentifierDeclarations** map an alias (Identifier) to a DataSetArn. The Identifier is referenced everywhere else — field wells, filters, calculated fields. Keep aliases short and descriptive (e.g., `"tickets"`, `"health_scores"`).

```python
{"Identifier": "tickets", "DataSetArn": "arn:aws:quicksight:$REGION:$ACCOUNT_ID:dataset/$DATASET_ID"}
```

**Sheets** contain SheetId, Name, Visuals (max 75 per sheet), Layouts (exactly 1 per sheet), and optional ParameterControls, FilterControls, TextBoxes, SheetControlLayouts.

---

## Grid Layout

QuickSight uses a **36-column grid**. Maximum ColumnSpan is 36; maximum RowSpan is 21.

### Common positioning patterns

| Layout | Width | Columns (0-indexed) |
|--------|-------|---------------------|
| Full width | 36 | col=0 |
| Two columns | 17 each | col=0, col=19 (2-col gap) |
| Three columns | 12 each | col=0, col=12, col=24 |
| Four columns | 9 each | col=0, col=9, col=18, col=27 |

Typical heights: KPI=6-8, chart=12, table=15-21, text header=2-3.

### Complete Layouts block

Every sheet needs exactly one Layouts entry. Multiple entries cause a validation error.

```python
"Layouts": [{
    "Configuration": {"GridLayout": {
        "Elements": [
            grid_element("kpi-tickets",      col=0,  row=0,  width=9,  height=8),
            grid_element("kpi-automation",   col=9,  row=0,  width=9,  height=8),
            grid_element("chart-trend",      col=0,  row=8,  width=36, height=12),
            grid_element("table-detail",     col=0,  row=20, width=36, height=21),
        ],
        "CanvasSizeOptions": {"ScreenCanvasSizeOptions": {
            "ResizeOption": "FIXED", "OptimizedViewPortWidth": "1600px"
        }}
    }}
}]
```

Set `OptimizedViewPortWidth` to `"1600px"` for consistent rendering. Without it, visuals reflow unpredictably.

---

## Visual Types and Field Wells

Field wells follow three structural patterns depending on the visual type. Mixing patterns causes INVALID_VISUAL_CONFIGURATION.

### Pattern A — Flat (KPI, Gauge)

Values placed directly in FieldWells without a wrapper object.

```json
{"KPIVisual": {"VisualId": "kpi-total", "DataSetIdentifier": "tickets",
  "ChartConfiguration": {"FieldWells": {
    "Values": [{"NumericalMeasureField": {"FieldId": "...", "Column": {"DataSetIdentifier": "tickets", "ColumnName": "ticket_count"}, "AggregationFunction": {"SimpleNumericalAggregation": "SUM"}}}],
    "TargetValues": [], "TrendGroups": []
}}}}
```

### Pattern B — Wrapped (most chart visuals)

FieldWells contain a type-specific wrapper: `{VisualType}AggregatedFieldWells`. The wrapper name must exactly match: `LineChartAggregatedFieldWells`, `BarChartAggregatedFieldWells`, `PieChartAggregatedFieldWells`, etc.

```json
{"FieldWells": {"BarChartAggregatedFieldWells": {
    "Category": [{"CategoricalDimensionField": {"FieldId": "...", "Column": {...}}}],
    "Values": [{"NumericalMeasureField": {"FieldId": "...", "Column": {...}, "AggregationFunction": {...}}}],
    "Colors": []
}}}
```

### Pattern C — Dual mode (Table, ScatterPlot)

Tables support both `TableAggregatedFieldWells` and `TableUnaggregatedFieldWells`. Unaggregated fields are **flat** — no type wrapper.

```json
// CORRECT — flat
"Values": [{"FieldId": "ds-name-unagg", "Column": {"DataSetIdentifier": "ds", "ColumnName": "name"}}]

// WRONG — do not wrap
"Values": [{"UnaggregatedField": {"FieldId": "...", "Column": {...}}}]
```

### Visual selection guide

| Data Pattern | Visual Type | Notes |
|---|---|---|
| Single metric | KPIVisual | Optional sparkline via TrendGroups, comparison via TargetValues |
| Trend over time | LineChartVisual | Date dimension on Category, smooth interpolation available |
| Category comparison | BarChartVisual | Set Orientation: HORIZONTAL for long category labels |
| Part of whole | PieChartVisual | Keep to 10 slices max for readability |
| Two related metrics | ComboChartVisual | Bars + lines on dual axes, 2500 data point limit |
| Detail records | TableVisual (unagg) | One row per record, flat field wells |
| Grouped summary | TableVisual (agg) | GroupBy dimensions + aggregated Values |
| Hierarchical grouping | PivotTableVisual | Rows + Columns + Values, max 40 fields each |
| Geographic data | GeoSpatialMapVisual | Requires geospatial column type |
| Progress toward goal | GaugeChartVisual | Pattern A field wells with TargetValues |

For per-visual-type JSON structures, read the relevant file in `references/`: `visuals-kpi.md`, `visuals-charts.md`, `visuals-tables.md`, `visuals-comparison.md`, or `visuals-specialized.md`.

---

## Filters, Parameters, and Controls

This is the most error-prone part of the API. Three objects must be wired together correctly: Parameters declare the variable, FilterGroups bind it to dataset columns, and Controls expose it in the UI.

### Step 1 — Declare parameters

Parameters live at the top level of the definition. Names must be **alphanumeric only** (no hyphens, underscores, or spaces). Types: `DateTimeParameterDeclaration`, `StringParameterDeclaration`, `IntegerParameterDeclaration`, `DecimalParameterDeclaration`.

```json
{"ParameterDeclarations": [
    {"DateTimeParameterDeclaration": {
        "Name": "StartDate",
        "DefaultValues": {"StaticValues": ["2024-01-01T00:00:00"]},
        "TimeGranularity": "DAY"
    }},
    {"StringParameterDeclaration": {
        "Name": "SelectedStatus",
        "DefaultValues": {"StaticValues": ["all"]},
        "ParameterValueType": "SINGLE_VALUED"
    }}
]}
```

### Step 2 — Create filter groups

Each FilterGroup targets one dataset. Use `CrossDataset: "SINGLE_DATASET"` unless you have an identical column across multiple datasets and want one filter to control all of them.

```json
{"FilterGroupId": "time-range-tickets",
 "Filters": [{"TimeRangeFilter": {
     "FilterId": "time-filter-tickets",
     "Column": {"DataSetIdentifier": "tickets", "ColumnName": "date"},
     "RangeMinimumValue": {"Parameter": "StartDate"},
     "NullOption": "NON_NULLS_ONLY"
 }}],
 "ScopeConfiguration": {"SelectedSheets": {"SheetVisualScopingConfigurations": [
     {"SheetId": "overview-sheet", "Scope": "ALL_VISUALS"}
 ]}},
 "Status": "ENABLED",
 "CrossDataset": "SINGLE_DATASET"}
```

To filter only specific visuals, use `"Scope": "SELECTED_VISUALS"` with a `"VisualIds"` array.

### Step 3 — Add controls to the sheet

Controls go inside the Sheet object, not at the definition level. Types: `DateTimePicker`, `Dropdown`, `TextField`, `TextArea`, `Slider`, `List`.

```json
{"SheetId": "overview-sheet", "Name": "Overview",
 "ParameterControls": [{"DateTimePicker": {
    "ParameterControlId": "ctrl-start-date", "Title": "Show Data From",
    "SourceParameterName": "StartDate",
    "DisplayOptions": {"TitleOptions": {"Visibility": "VISIBLE"}, "DateTimeFormat": "YYYY/MM/DD"}
 }}],
 "Visuals": [...]}
```

Filter types: `TimeRangeFilter`, `RelativeDatesFilter`, `CategoryFilter`, `NumericRangeFilter`, `NumericEqualityFilter`.

### Key rules

- One FilterGroup per dataset per filter concept. Do not mix datasets in one FilterGroup.
- Parameter names: alphanumeric only. `Start_Date` fails; use `StartDate`.
- `NullOption` is required on every filter (`"NON_NULLS_ONLY"` or `"ALL_VALUES"`).
- Use `ALL_VISUALS` scope only when every visual on the sheet uses that dataset. Otherwise use `SELECTED_VISUALS` to avoid FIELD_NOT_FOUND.

---

## Calculated Fields

Two scopes: **dataset-level** (in LogicalTableMap, shared across analyses) and **analysis-level** (in `CalculatedFields`, scoped to this analysis).

```json
{"CalculatedFields": [{"DataSetIdentifier": "tickets", "Name": "automation_rate", "Expression": "{ai_responses} / {total_tickets}"}]}
```

Expression syntax: `{column_name}` for references, `ifelse()` for conditionals, `dateDiff()` for date math, `sumOver()` / `rankOver()` for window functions, `isNull()` for null handling.

Read `references/calculated-fields.md` for the full expression syntax and function catalog.

---

## Conditional Formatting

Add a `ConditionalFormatting` block inside any visual. Each condition uses an expression evaluated per row.

```json
{"ConditionalFormatting": {"ConditionalFormattingOptions": [{"PrimaryValue": {
    "TextColor": {"Solid": {"Expression": "ifelse({health_score} >= 70, 0, ifelse({health_score} >= 40, 1, 2))", "Color": "#2ECC71"}}
}}]}}
```

Format types by visual: **KPI** uses PrimaryValue, **Table** uses Cell (per-column color/icon), **Bar/Line/Pie** do not support direct conditional formatting (use calculated fields with color mapping instead). Use `Gradient` instead of `Solid` for continuous ranges.

Read `references/format-patterns.md` for complete conditional formatting patterns including gradient examples and icon set configuration.

---

## Themes

Apply a theme to control colors, fonts, and UI chrome across the entire analysis.

```bash
aws quicksight create-theme \
  --aws-account-id $QS_ACCOUNT --profile $QS_PROFILE \
  --theme-id "my-dark-theme" --name "Dark Theme" --base-theme-id "MIDNIGHT" \
  --configuration '{"DataColorPalette": {"Colors": ["#3498DB","#2ECC71","#E74C3C","#F39C12"]}, "UIColorPalette": {"PrimaryBackground": "#1a1a2e", "PrimaryForeground": "#e0e0e0", "Accent": "#3498DB"}}'

# Apply when pushing
--theme-arn "arn:aws:quicksight:$REGION:$QS_ACCOUNT:theme/my-dark-theme"
```

- ThemeId: `[0-9a-zA-Z-]*` only. Built-in themes: `CLASSIC`, `MIDNIGHT`, `SEASIDE`, `RAINIER`.
- `DataColorPalette.Colors` controls chart series colors in order. Provide at least 8.
- Use `create-theme-alias` for version management (e.g., `LATEST`, `v2`).

---

## Critical Gotchas

These are the most common causes of CREATION_FAILED and blank visuals. Each includes the correct and incorrect pattern.

### 1. Double-nested FormatConfiguration

The API nests format config three levels deep. Missing any level silently shows raw numbers.

```python
# CORRECT path: FormatConfiguration > FormatConfiguration > NumberFormatConfiguration > FormatConfiguration > NumericFormatConfiguration
"FormatConfiguration": {"FormatConfiguration": {"NumberFormatConfiguration": {"FormatConfiguration": {"NumericFormatConfiguration": {"Suffix": "%", "DecimalPlacesConfiguration": {"DecimalPlaces": 1}}}}}}

# WRONG — missing middle layer
"FormatConfiguration": {"NumberFormatConfiguration": {"NumericFormatConfiguration": {"Suffix": "%"}}}
```

### 2. Field IDs must be globally unique

Every FieldId across all visuals in the entire analysis must be unique. Reusing a FieldId from one visual in another causes FIELD_NOT_FOUND errors that point to the wrong visual.

```python
# CORRECT — include visual context in field ID
field_id("tickets", "count", "kpi-overview")   # "tickets-count-kpi-overview"
field_id("tickets", "count", "chart-trend")     # "tickets-count-chart-trend"

# WRONG — same ID in two visuals
field_id("tickets", "count")  # used in both KPI and chart
```

### 3. Layouts array — exactly one per sheet

```python
# CORRECT
"Layouts": [{"Configuration": {"GridLayout": {...}}}]

# WRONG — multiple layouts
"Layouts": [{"Configuration": {...}}, {"Configuration": {...}}]

# WRONG — empty
"Layouts": []
```

### 4. KPI sparkline requires Type even when hidden

If a KPI has a TrendGroups field well, the KPIOptions must include a Sparkline configuration with a Type, even if Visibility is HIDDEN.

```json
// CORRECT
"KPIOptions": {
    "Sparkline": {"Visibility": "HIDDEN", "Type": "LINE"}
}

// WRONG — omitting Type when Visibility is HIDDEN causes validation error
"KPIOptions": {
    "Sparkline": {"Visibility": "HIDDEN"}
}
```

### 5. Table unaggregated fields are flat

Covered in Pattern C above. Do not wrap unaggregated field entries in a type object.

### 6. Table sort uses ColumnSort, not UnaggregatedSort

```json
// CORRECT
"SortConfiguration": {
    "RowSort": [{
        "FieldSort": {
            "FieldId": "ds-score-unagg",
            "Direction": "DESC"
        }
    }]
}

// WRONG — UnaggregatedSort is not a valid sort type
"SortConfiguration": {
    "RowSort": [{
        "UnaggregatedSort": {"FieldId": "...", "Direction": "DESC"}
    }]
}
```

### 7. DataLabels Position values

Valid values: `OUTSIDE`, `INSIDE`, `LEFT`, `BOTTOM`, `TOP`, `RIGHT`.

```json
// WRONG — OUTSIDE_END is not valid
"Position": "OUTSIDE_END"

// CORRECT
"Position": "OUTSIDE"
```

### 8. Use LENIENT validation during development

Strict validation rejects the entire push on any warning. Use LENIENT to iterate, then switch to strict before publishing.

```bash
# Development — allows warnings
--validation-strategy '{"Mode": "LENIENT"}'

# Production — fails on warnings
--validation-strategy '{"Mode": "STRICT"}'
```

### 9. Empty arrays vs omitted keys

Some fields require an empty array if present; others must be omitted entirely. When in doubt, omit optional fields rather than passing empty arrays. The API is inconsistent about this.

### 10. CrossDataset filter scope

Setting `CrossDataset: "ALL_DATASETS"` on a filter that references a column not present in all datasets causes FIELD_NOT_FOUND on the datasets lacking that column. Default to `"SINGLE_DATASET"` unless you are certain.

---

## Pushing to QuickSight

### Development workflow

```bash
# 1. Generate and inspect
python3 build_analysis.py --dry-run  # writes /tmp/qs-analysis.json

# 2. Push with lenient validation
aws quicksight update-analysis --aws-account-id $QS_ACCOUNT --profile $QS_PROFILE \
  --analysis-id $ANALYSIS_ID --name "My Analysis" \
  --definition file:///tmp/qs-analysis.json --validation-strategy '{"Mode": "LENIENT"}'

# 3. Check status and errors
aws quicksight describe-analysis --aws-account-id $QS_ACCOUNT --profile $QS_PROFILE \
  --analysis-id $ANALYSIS_ID --query 'Analysis.Status'
aws quicksight describe-analysis --aws-account-id $QS_ACCOUNT --profile $QS_PROFILE \
  --analysis-id $ANALYSIS_ID --query 'Analysis.Errors'
```

### Common error resolution

| Error | Cause | Fix |
|---|---|---|
| FIELD_NOT_FOUND | FieldId mismatch or wrong DataSetIdentifier | Verify field IDs are unique and dataset aliases match declarations |
| INVALID_VISUAL_CONFIGURATION | Wrong field well pattern for visual type | Check Pattern A/B/C above |
| CREATION_FAILED (no detail) | Structural JSON error | Use `--dry-run`, validate with `python3 -m json.tool`, diff against known-good |
| Visual renders blank | FormatConfiguration nesting wrong, or NullOption missing | Check triple nesting; add NullOption to filters |

---

## Reference Files

These companion files contain detailed structures. Read only the file relevant to your current task.

- `references/visuals-kpi.md` — KPI visual JSON with sparklines, comparisons, conditional formatting
- `references/visuals-charts.md` — Line, bar, combo, pie chart field wells and options
- `references/visuals-tables.md` — Table and pivot table configuration, aggregated and unaggregated
- `references/visuals-comparison.md` — Gauge, funnel, waterfall, tree map visuals
- `references/visuals-specialized.md` — Geospatial, word cloud, sankey, box plot
- `references/format-patterns.md` — Number/date/currency format configuration, conditional formatting, icon sets
- `references/calculated-fields.md` — Expression syntax, function catalog, window functions, LAC-W
- `references/api-gotchas.md` — Full list of API pitfalls, edge cases, and debugging procedures
