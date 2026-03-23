# QuickSight API Gotchas

Hard-won lessons from the QuickSight API. Each gotcha explains what goes wrong, why, and how to fix it.

---

## Core Gotchas

### 1. Dataset Permissions Are NOT Auto-Granted

> **WARNING: This is the #1 cause of "where did my dataset go?" confusion.**

When you create a dataset via `create-data-set`, the creator principal gets **zero** permissions. The dataset exists but is invisible in the console and unusable in analyses until you explicitly call `update-data-set-permissions`.

**Correct — grant permissions immediately after creation:**
```bash
aws quicksight update-data-set-permissions \
  --aws-account-id $ACCOUNT_ID \
  --data-set-id $DATASET_ID \
  --grant-permissions '[
    {
      "Principal": "arn:aws:quicksight:$REGION:$ACCOUNT_ID:user/default/$USERNAME",
      "Actions": [
        "quicksight:DescribeDataSet",
        "quicksight:DescribeDataSetPermissions",
        "quicksight:PassDataSet",
        "quicksight:DescribeIngestion",
        "quicksight:ListIngestions",
        "quicksight:UpdateDataSet",
        "quicksight:DeleteDataSet",
        "quicksight:CreateIngestion",
        "quicksight:CancelIngestion",
        "quicksight:UpdateDataSetPermissions"
      ]
    }
  ]'
```

**Viewer action set** (read-only):
```json
[
  "quicksight:DescribeDataSet",
  "quicksight:DescribeDataSetPermissions",
  "quicksight:PassDataSet",
  "quicksight:DescribeIngestion",
  "quicksight:ListIngestions"
]
```

**Owner action set** (full control):
```json
[
  "quicksight:DescribeDataSet",
  "quicksight:DescribeDataSetPermissions",
  "quicksight:PassDataSet",
  "quicksight:DescribeIngestion",
  "quicksight:ListIngestions",
  "quicksight:UpdateDataSet",
  "quicksight:DeleteDataSet",
  "quicksight:CreateIngestion",
  "quicksight:CancelIngestion",
  "quicksight:UpdateDataSetPermissions"
]
```

**Incorrect — assuming create-data-set is enough:**
```bash
# Dataset created but invisible to everyone, including creator
aws quicksight create-data-set --aws-account-id $ACCOUNT_ID ...
# "I can't find my dataset!" — because no permissions were granted
```

---

### 2. Physical/Logical Table Map Keys Must Match `[0-9a-zA-Z-]*`

**Why:** QuickSight validates map keys against the regex `^[0-9a-zA-Z-]*$`. Underscores, dots, and spaces are all rejected with a cryptic validation error.

**Correct:**
```json
{
  "PhysicalTableMap": {
    "my-table-source": { ... }
  },
  "LogicalTableMap": {
    "my-table-logical": { ... }
  }
}
```

**Incorrect:**
```json
{
  "PhysicalTableMap": {
    "my_table_source": { ... }
  }
}
```

**Python replacement pattern:**
```python
def sanitize_map_key(name: str) -> str:
    """Replace non-alphanumeric/hyphen chars with hyphens."""
    import re
    return re.sub(r'[^0-9a-zA-Z-]', '-', name)
```

---

### 3. Double-Nested FormatConfiguration

**Why:** The API has two different types both named `FormatConfiguration`. A `NumericalMeasureField` has a `FormatConfiguration` (of type `NumberFormatConfiguration`) which itself contains a `FormatConfiguration` (of type `NumericFormatConfiguration`). Yes, the key name appears twice.

**Correct:**
```json
{
  "NumericalMeasureField": {
    "FieldId": "$FIELD_ID",
    "Column": {"DataSetIdentifier": "$DS_ID", "ColumnName": "$COLUMN"},
    "AggregationFunction": {"SimpleNumericalAggregation": "SUM"},
    "FormatConfiguration": {
      "FormatConfiguration": {
        "NumberDisplayFormatConfiguration": {
          "Prefix": "$",
          "SeparatorConfiguration": {
            "ThousandsSeparator": {"Visibility": "VISIBLE", "Symbol": "COMMA"}
          },
          "DecimalPlacesConfiguration": {"DecimalPlaces": 0}
        }
      }
    }
  }
}
```

**Incorrect — only one level of FormatConfiguration:**
```json
{
  "NumericalMeasureField": {
    "FormatConfiguration": {
      "NumberDisplayFormatConfiguration": { ... }
    }
  }
}
```

See `references/format-patterns.md` for the full hierarchy diagram.

---

### 4. Parameter Names Must Be Alphanumeric Only

**Why:** Parameter names are validated against `^[a-zA-Z0-9]+$`. No hyphens, underscores, or spaces.

**Correct:** `"Name": "StartDate"`, `"Name": "AccountFilter"`

**Incorrect:** `"Name": "start-date"`, `"Name": "account_filter"`, `"Name": "Start Date"`

---

### 5. Layouts Array Must Be Exactly 1 Item Per Sheet

**Why:** Each sheet must have exactly one layout. The API types it as an array, but providing 0 or 2+ items causes a validation error.

**Correct:**
```json
{
  "SheetId": "$SHEET_ID",
  "Layouts": [
    {
      "Configuration": {
        "GridLayout": {
          "Elements": [ ... ]
        }
      }
    }
  ]
}
```

**Incorrect — multiple layouts:**
```json
{
  "Layouts": [
    {"Configuration": {"GridLayout": {"Elements": [...]}}},
    {"Configuration": {"FreeFormLayout": {"Elements": [...]}}}
  ]
}
```

---

### 6. KPI Sparkline Requires Type Even When Hidden

**Why:** The `Type` field on `KPISparklineOptions` is required regardless of `Visibility`. Omitting it causes a validation error even if `Visibility` is `"HIDDEN"`.

**Correct:**
```json
{
  "Sparkline": {
    "Visibility": "HIDDEN",
    "Type": "LINE"
  }
}
```

**Incorrect:**
```json
{
  "Sparkline": {
    "Visibility": "HIDDEN"
  }
}
```

Valid Types: `LINE`, `AREA`

---

### 7. TableUnaggregatedFieldWells Has a Flat Structure

**Why:** Unlike aggregated field wells which wrap fields in `CategoricalDimensionField`, `NumericalMeasureField`, etc., unaggregated fields use `UnaggregatedField` directly without a type-specific wrapper key.

**Correct:**
```json
{
  "TableUnaggregatedFieldWells": {
    "Values": [
      {
        "FieldId": "$FIELD_ID",
        "Column": {"DataSetIdentifier": "$DS_ID", "ColumnName": "$COLUMN"},
        "FormatConfiguration": { ... }
      }
    ]
  }
}
```

**Incorrect — wrapping in a type key:**
```json
{
  "TableUnaggregatedFieldWells": {
    "Values": [
      {
        "CategoricalDimensionField": {
          "FieldId": "$FIELD_ID",
          "Column": { ... }
        }
      }
    ]
  }
}
```

---

### 8. Table Sort Uses ColumnSort, Not UnaggregatedSort

**Why:** There is no `UnaggregatedSort` type. Even for unaggregated tables, use `ColumnSort` inside `RowSort`.

**Correct:**
```json
{
  "SortConfiguration": {
    "RowSort": [
      {
        "ColumnSort": {
          "SortBy": {"DataSetIdentifier": "$DS_ID", "ColumnName": "$COLUMN"},
          "Direction": "DESC"
        }
      }
    ]
  }
}
```

**Incorrect:**
```json
{
  "SortConfiguration": {
    "RowSort": [
      {
        "UnaggregatedSort": { ... }
      }
    ]
  }
}
```

---

## Extended Gotchas

### 9. CLI file:// for JSON, fileb:// for Binary

Use `file://` to load JSON parameters from a file. Use `fileb://` for binary data. Mixing them up causes parse errors.

```bash
# JSON definition
aws quicksight update-analysis --cli-input-json file://analysis.json

# Binary content (e.g., image)
--content fileb://logo.png
```

---

### 10. Ingestion ID Reuse Fails While Running

If an ingestion with the same ID is still running, creating a new one with that ID fails. Always append a timestamp.

**Correct:**
```bash
aws quicksight create-ingestion \
  --aws-account-id $ACCOUNT_ID \
  --data-set-id $DATASET_ID \
  --ingestion-id "refresh-$(date +%s)-$DATASET_ID"
```

---

### 11. UpdateAnalysis Requires Name Even If Unchanged

The `Name` parameter is required on `update-analysis` even if you are only changing the definition. Omitting it causes a validation error.

---

### 12. SmallMultiples Max = 1 Dimension Field

SmallMultiples wells on bar, line, and pie charts accept at most 1 DimensionField. Adding more causes a validation error.

---

### 13. PivotTable Max = 40 Items Per Well

PivotTable Rows, Columns, and Values each max at 40 items, not 200 like most other visuals.

---

### 14. Max Limits per Analysis

| Resource | Limit |
|----------|-------|
| Visuals per sheet | 75 |
| Sheets per analysis | 20 |
| Datasets per analysis | 50 |
| Calculated fields per analysis | 2000 |
| Parameters per analysis | 200 |

---

### 15. DataLabels Position Valid Values

Valid: `OUTSIDE`, `LEFT`, `BOTTOM`, `TOP`, `RIGHT`, `INSIDE`

**Incorrect:** `OUTSIDE_END`, `CENTER`, `NONE` (these do not exist)

---

## Debugging CREATION_FAILED

When `create-analysis` or `update-analysis` returns status `CREATION_FAILED`:

### Step 1: Get the actual error message
```bash
aws quicksight describe-analysis \
  --aws-account-id $ACCOUNT_ID \
  --analysis-id $ANALYSIS_ID \
  --query 'Analysis.Errors'
```

The `Errors` array contains specific messages that are far more useful than the generic failure status.

### Step 2: Use LENIENT validation during development
```json
{
  "Definition": { ... },
  "ValidationStrategy": {
    "Mode": "LENIENT"
  }
}
```

LENIENT mode allows the analysis to be created even with warnings, so you can iterate on fixes in the console.

### Step 3: Debug incrementally
Start with the absolute minimum:
1. One sheet, one visual, no filters, no parameters
2. Verify it succeeds
3. Add visuals one at a time
4. Add filters and parameters last

### Common Causes of CREATION_FAILED

| Symptom | Cause |
|---------|-------|
| "Column not found" | ColumnIdentifier DataSetIdentifier or ColumnName mismatch |
| "DataSet not found" | DataSetIdentifier in visual not declared in DataSetIdentifierDeclarations |
| "Duplicate identifier" | Two visuals or fields share the same FieldId |
| "Sheet not found" | SheetId in FilterScopeConfiguration references nonexistent sheet |
| Generic failure | SheetId or VisualId not globally unique within the analysis |

### FieldId Uniqueness

FieldIds must be unique **across the entire analysis**, not just within a visual. Use a naming convention:
```
{visual_short_name}_{field_purpose}
```
Example: `kpi_revenue_value`, `bar_monthly_category`

---

## Boto3 Translation Note

When translating AWS CLI commands to Python boto3:

| CLI | Boto3 |
|-----|-------|
| `--aws-account-id $ACCOUNT_ID` | `AwsAccountId='$ACCOUNT_ID'` |
| `--data-set-id $DATASET_ID` | `DataSetId='$DATASET_ID'` |
| `--cli-input-json file://def.json` | Pass dict directly to method |
| Kebab-case params | PascalCase params |
| JSON string for `--permissions` | Python list of dicts |

```python
import boto3

qs = boto3.client('quicksight', region_name='$REGION')

# CLI: aws quicksight describe-analysis --aws-account-id 123 --analysis-id abc
# Boto3:
response = qs.describe_analysis(
    AwsAccountId='$ACCOUNT_ID',
    AnalysisId='$ANALYSIS_ID'
)
```
