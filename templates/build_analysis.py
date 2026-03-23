#!/usr/bin/env python3
"""
Build and push a QuickSight analysis definition.

Generates the full analysis JSON with visuals arranged in a 36-column grid,
then optionally pushes via the AWS CLI. This makes dashboards reproducible
and version-controlled.

Usage:
    python3 build_analysis.py --dry-run          # Write JSON to /tmp
    python3 build_analysis.py --push             # Push to QuickSight
    python3 build_analysis.py --push --lenient   # Push with relaxed validation
"""

import argparse
import json
import subprocess
import sys
import uuid

# ─── Configuration ────────────────────────────────────────────────────────────
# Replace these with your actual values.

AWS_ACCOUNT_ID = "YOUR_ACCOUNT_ID"       # e.g., "123456789012"
AWS_PROFILE = "YOUR_PROFILE"             # e.g., "production"
AWS_REGION = "us-west-2"
ANALYSIS_ID = "YOUR_ANALYSIS_ID"         # UUID of your analysis
ANALYSIS_NAME = "My Analysis"

# Dataset IDs — map logical names to UUIDs assigned during create-data-set.
KNOWN_DATASET_IDS = {
    # "my_dataset": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def dataset_arn(dataset_id: str) -> str:
    return f"arn:aws:quicksight:{AWS_REGION}:{AWS_ACCOUNT_ID}:dataset/{dataset_id}"


def dataset_placeholder(name: str) -> dict:
    """DataSetIdentifierDeclaration for a dataset."""
    ds_id = KNOWN_DATASET_IDS.get(name)
    if not ds_id:
        raise ValueError(f"Unknown dataset: {name}. Add it to KNOWN_DATASET_IDS.")
    return {"Identifier": name, "DataSetArn": dataset_arn(ds_id)}


def grid_element(element_id: str, col: int, row: int, width: int, height: int) -> dict:
    """Place a visual on the 36-column grid.

    Common layouts:
        Full width:  width=36
        Half width:  width=17, col=0 and col=19 (2-col gap)
        Third width: width=12, col=0, col=12, col=24
    Typical heights: KPI=8, chart=12, table=21
    """
    return {
        "ElementId": element_id,
        "ElementType": "VISUAL",
        "ColumnIndex": col,
        "ColumnSpan": width,
        "RowIndex": row,
        "RowSpan": height,
    }


def field_id(dataset_name: str, column: str) -> str:
    """Deterministic field ID — avoids UUID sprawl."""
    return f"{dataset_name}.{column}"


def measure_field(ds: str, col: str, agg: str = "SUM",
                  suffix: str = None, prefix: str = None,
                  decimals: int = None) -> dict:
    """NumericalMeasureField with optional formatting."""
    field = {
        "NumericalMeasureField": {
            "FieldId": field_id(ds, col),
            "Column": {"DataSetIdentifier": ds, "ColumnName": col},
            "AggregationFunction": {"SimpleNumericalAggregation": agg},
        }
    }
    fmt = number_format(suffix=suffix, prefix=prefix, decimals=decimals)
    if fmt:
        field["NumericalMeasureField"]["FormatConfiguration"] = fmt
    return field


def dim_field_date(ds: str, col: str, granularity: str = "WEEK") -> dict:
    """DateDimensionField with hierarchy for drill-down."""
    hid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{ds}.{col}"))
    return {
        "DateDimensionField": {
            "FieldId": field_id(ds, col),
            "Column": {"DataSetIdentifier": ds, "ColumnName": col},
            "DateGranularity": granularity,
            "HierarchyId": hid,
            "FormatConfiguration": {"DateTimeFormat": "MMM DD"},
        }
    }


def dim_field_cat(ds: str, col: str) -> dict:
    """CategoricalDimensionField for group-by dimensions."""
    return {
        "CategoricalDimensionField": {
            "FieldId": field_id(ds, col),
            "Column": {"DataSetIdentifier": ds, "ColumnName": col},
        }
    }


def date_hierarchy(ds: str, col: str) -> dict:
    """DateTimeHierarchy matching dim_field_date's HierarchyId."""
    hid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{ds}.{col}"))
    return {"DateTimeHierarchy": {"HierarchyId": hid, "DrillDownFilters": []}}


def number_format(suffix: str = None, prefix: str = None,
                  decimals: int = None) -> dict | None:
    """Build the double-nested FormatConfiguration for numerical fields.

    The nesting is: FormatConfiguration.FormatConfiguration.NumberDisplayFormatConfiguration
    Yes, the key "FormatConfiguration" appears twice. This is not a bug.
    """
    if not any([suffix, prefix, decimals is not None]):
        return None
    num_cfg = {}
    if suffix:
        num_cfg["Suffix"] = suffix
    if prefix:
        num_cfg["Prefix"] = prefix
    if decimals is not None:
        num_cfg["DecimalPlacesConfiguration"] = {"DecimalPlaces": decimals}
    return {
        "FormatConfiguration": {
            "FormatConfiguration": {
                "NumberDisplayFormatConfiguration": num_cfg,
            }
        }
    }


def currency_fmt() -> dict:
    """Format configuration for currency columns (e.g., in unaggregated table fields)."""
    return {
        "NumberFormatConfiguration": {
            "FormatConfiguration": {
                "NumberDisplayFormatConfiguration": {
                    "Prefix": "$",
                    "DecimalPlacesConfiguration": {"DecimalPlaces": 0},
                    "SeparatorConfiguration": {
                        "ThousandsSeparator": {"Visibility": "VISIBLE", "Symbol": "COMMA"},
                    },
                }
            }
        }
    }


def unagg_field(ds: str, col: str, fmt: dict = None) -> dict:
    """Field for TableUnaggregatedFieldWells.Values — flat structure, no type wrapper."""
    f = {
        "FieldId": field_id(ds, col),
        "Column": {"DataSetIdentifier": ds, "ColumnName": col},
    }
    if fmt:
        f["FormatConfiguration"] = fmt
    return f


# ─── Sheet Builders ───────────────────────────────────────────────────────────
# Add your sheet builder functions here. Example:

def build_example_sheet() -> dict:
    """Example sheet — replace with your own visuals."""
    ds = "my_dataset"  # must match a key in KNOWN_DATASET_IDS

    # Example: KPI visual
    kpi = {
        "KPIVisual": {
            "VisualId": "kpi-example",
            "Title": {"Visibility": "VISIBLE", "FormatText": {
                "RichText": "<visual-title>Example KPI</visual-title>",
            }},
            "Subtitle": {"Visibility": "HIDDEN"},
            "ChartConfiguration": {
                "FieldWells": {
                    "Values": [measure_field(ds, "value_column", "SUM")],
                    "TargetValues": [],
                    "TrendGroups": [],
                },
                "SortConfiguration": {},
                "KPIOptions": {
                    "PrimaryValueDisplayType": "ACTUAL",
                    "Sparkline": {"Visibility": "HIDDEN", "Type": "LINE"},
                },
            },
            "Actions": [],
            "ColumnHierarchies": [],
        }
    }

    return {
        "SheetId": "example-sheet",
        "Name": "Example Sheet",
        "ParameterControls": [],
        "Visuals": [kpi],
        "Layouts": [{
            "Configuration": {
                "GridLayout": {
                    "Elements": [
                        grid_element("kpi-example", 0, 0, 12, 8),
                    ],
                    "CanvasSizeOptions": {
                        "ScreenCanvasSizeOptions": {
                            "ResizeOption": "FIXED",
                            "OptimizedViewPortWidth": "1600px",
                        }
                    },
                }
            }
        }],
    }


# ─── Main Definition ──────────────────────────────────────────────────────────

def build_definition() -> dict:
    dataset_declarations = [
        dataset_placeholder(name)
        for name in KNOWN_DATASET_IDS
        if KNOWN_DATASET_IDS[name]
    ]

    return {
        "DataSetIdentifierDeclarations": dataset_declarations,
        "Sheets": [
            build_example_sheet(),
        ],
        "AnalysisDefaults": {
            "DefaultNewSheetConfiguration": {
                "InteractiveLayoutConfiguration": {
                    "Grid": {
                        "CanvasSizeOptions": {
                            "ScreenCanvasSizeOptions": {
                                "ResizeOption": "FIXED",
                                "OptimizedViewPortWidth": "1600px",
                            }
                        }
                    }
                }
            }
        },
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build and push QuickSight analysis")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Write JSON to /tmp only")
    group.add_argument("--push", action="store_true", help="Push to QuickSight")
    parser.add_argument("--lenient", action="store_true",
                        help="Use LENIENT validation (accepts partial errors)")
    args = parser.parse_args()

    definition = build_definition()
    output_path = "/tmp/qs-analysis.json"

    with open(output_path, "w") as f:
        json.dump(definition, f, indent=2)
    print(f"Definition written to {output_path}")
    print(f"  Datasets: {len(definition['DataSetIdentifierDeclarations'])}")
    for sheet in definition["Sheets"]:
        print(f"  Sheet '{sheet['Name']}': {len(sheet['Visuals'])} visuals")

    if args.push:
        print("\nPushing to QuickSight...")
        cmd = [
            "aws", "quicksight", "update-analysis",
            "--aws-account-id", AWS_ACCOUNT_ID,
            "--profile", AWS_PROFILE,
            "--region", AWS_REGION,
            "--analysis-id", ANALYSIS_ID,
            "--name", ANALYSIS_NAME,
            "--definition", f"file://{output_path}",
        ]
        if args.lenient:
            cmd += ["--validation-strategy", '{"Mode": "LENIENT"}']
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Success!")
            print(result.stdout)
        else:
            print("Failed!")
            print(result.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
