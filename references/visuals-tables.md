# Table, PivotTable, and HeatMap Visuals

These are the most complex visuals in QuickSight. Tables have dual aggregation modes, pivot tables have unique sort semantics, and all three have extensive formatting options.

---

## TableVisual

TableVisual supports **two mutually exclusive modes**: aggregated and unaggregated.

### Mode 1: Aggregated (GroupBy + Measures)

Wrapper key: `TableAggregatedFieldWells`

```json
{
  "TableVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "TableAggregatedFieldWells": {
          "GroupBy": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_GROUP",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$GROUP_COLUMN"}
              }
            }
          ],
          "Values": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_MEASURE",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$MEASURE_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "SUM"},
                "FormatConfiguration": {
                  "FormatConfiguration": {
                    "NumberDisplayFormatConfiguration": {
                      "DecimalPlacesConfiguration": {"DecimalPlaces": 0},
                      "SeparatorConfiguration": {
                        "ThousandsSeparator": {"Visibility": "VISIBLE", "Symbol": "COMMA"}
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "SortConfiguration": {
        "RowSort": [
          {
            "FieldSort": {
              "FieldId": "$FIELD_ID_MEASURE",
              "Direction": "DESC"
            }
          }
        ]
      },
      "TableOptions": {
        "HeaderStyle": {
          "BackgroundColor": "#232F3E",
          "FontConfiguration": {"FontColor": "#FFFFFF", "FontWeight": {"Name": "BOLD"}}
        },
        "CellStyle": {
          "FontConfiguration": {"FontSize": {"Relative": "MEDIUM"}}
        },
        "RowAlternateColorOptions": {
          "Status": "ENABLED",
          "RowAlternateColors": ["#F7F7F7"]
        }
      },
      "TotalOptions": {
        "TotalsVisibility": "VISIBLE",
        "Placement": "END",
        "TotalCellStyle": {
          "FontConfiguration": {"FontWeight": {"Name": "BOLD"}}
        }
      },
      "PaginatedReportOptions": {
        "VerticalOverflowVisibility": "VISIBLE",
        "OverflowColumnHeaderVisibility": "VISIBLE"
      }
    },
    "Actions": []
  }
}
```

### Mode 2: Unaggregated (Raw Rows)

Wrapper key: `TableUnaggregatedFieldWells`

> **IMPORTANT**: UnaggregatedField is a FLAT structure. Fields are NOT wrapped in a type-specific key.

```json
{
  "TableVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "TableUnaggregatedFieldWells": {
          "Values": [
            {
              "FieldId": "$FIELD_ID_NAME",
              "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$NAME_COLUMN"}
            },
            {
              "FieldId": "$FIELD_ID_DATE",
              "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$DATE_COLUMN"},
              "FormatConfiguration": {
                "DateTimeFormatConfiguration": {
                  "DateTimeFormat": "yyyy-MM-dd"
                }
              }
            },
            {
              "FieldId": "$FIELD_ID_AMOUNT",
              "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$AMOUNT_COLUMN"},
              "FormatConfiguration": {
                "NumberFormatConfiguration": {
                  "FormatConfiguration": {
                    "CurrencyDisplayFormatConfiguration": {
                      "Symbol": "$",
                      "DecimalPlacesConfiguration": {"DecimalPlaces": 2},
                      "SeparatorConfiguration": {
                        "ThousandsSeparator": {"Visibility": "VISIBLE", "Symbol": "COMMA"}
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "SortConfiguration": {
        "RowSort": [
          {
            "ColumnSort": {
              "SortBy": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$AMOUNT_COLUMN"},
              "Direction": "DESC"
            }
          }
        ]
      }
    },
    "Actions": []
  }
}
```

### Key Differences Between Modes

| Aspect | Aggregated | Unaggregated |
|--------|-----------|--------------|
| Wrapper | `TableAggregatedFieldWells` | `TableUnaggregatedFieldWells` |
| Field structure | Wrapped in `CategoricalDimensionField`, `NumericalMeasureField`, etc. | Flat `UnaggregatedField` — no type wrapper |
| Sorting | `FieldSort` (by FieldId) | `ColumnSort` (by Column reference) |
| Max fields | GroupBy: 200, Values: 200 | Values: 201 |
| Totals row | Supported | Not applicable |
| Format nesting | Double-nested `FormatConfiguration` on measures | `NumberFormatConfiguration` wrapper (different path) |

### Sorting Pitfall

Unaggregated tables use `ColumnSort`, NOT `FieldSort` or `UnaggregatedSort` (which does not exist):

**Correct:**
```json
{"ColumnSort": {"SortBy": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$COLUMN"}, "Direction": "DESC"}}
```

**Incorrect:**
```json
{"UnaggregatedSort": { ... }}
{"FieldSort": {"FieldId": "$FIELD_ID", "Direction": "DESC"}}
```

### Table Conditional Formatting

```json
{
  "ConditionalFormatting": {
    "ConditionalFormattingOptions": [
      {
        "Cell": {
          "FieldId": "$FIELD_ID_MEASURE",
          "TextFormat": {
            "BackgroundColor": {
              "Gradient": {
                "Expression": "{$MEASURE_COLUMN}",
                "Color": {
                  "Stops": [
                    {"GradientOffset": 0, "Color": "#DE3B00"},
                    {"GradientOffset": 50, "Color": "#FFCC00"},
                    {"GradientOffset": 100, "Color": "#2CAD00"}
                  ]
                }
              }
            }
          }
        }
      }
    ]
  }
}
```

---

## PivotTableVisual

### Field Wells

Wrapper key: `PivotTableAggregatedFieldWells`

> **NOTE**: Max 40 items per well (Rows, Columns, Values) — not 200 like most visuals.

```json
{
  "PivotTableVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "PivotTableAggregatedFieldWells": {
          "Rows": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_ROW1",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$ROW_COLUMN"}
              }
            }
          ],
          "Columns": [
            {
              "DateDimensionField": {
                "FieldId": "$FIELD_ID_COL1",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$DATE_COLUMN"},
                "DateGranularity": "MONTH"
              }
            }
          ],
          "Values": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_VAL1",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$VALUE_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "SUM"},
                "FormatConfiguration": {
                  "FormatConfiguration": {
                    "NumberDisplayFormatConfiguration": {
                      "DecimalPlacesConfiguration": {"DecimalPlaces": 0},
                      "SeparatorConfiguration": {
                        "ThousandsSeparator": {"Visibility": "VISIBLE", "Symbol": "COMMA"}
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      },
      "SortConfiguration": {
        "FieldSortOptions": [
          {
            "FieldId": "$FIELD_ID_ROW1",
            "SortBy": {
              "Field": {
                "FieldId": "$FIELD_ID_VAL1",
                "Direction": "DESC"
              }
            }
          }
        ]
      },
      "TableOptions": {
        "MetricPlacement": "ROW",
        "CollapsedRowDimensionsVisibility": "VISIBLE",
        "RowAlternateColorOptions": {
          "Status": "ENABLED",
          "RowAlternateColors": ["#F7F7F7"]
        },
        "CellStyle": {
          "FontConfiguration": {"FontSize": {"Relative": "MEDIUM"}}
        },
        "ColumnHeaderStyle": {
          "FontConfiguration": {"FontWeight": {"Name": "BOLD"}}
        },
        "RowHeaderStyle": {
          "FontConfiguration": {"FontWeight": {"Name": "BOLD"}}
        }
      },
      "TotalOptions": {
        "RowTotalOptions": {
          "TotalsVisibility": "VISIBLE",
          "Placement": "END"
        },
        "ColumnTotalOptions": {
          "TotalsVisibility": "VISIBLE",
          "Placement": "END"
        },
        "RowSubtotalOptions": {
          "TotalsVisibility": "VISIBLE"
        }
      }
    },
    "Actions": []
  }
}
```

### Key Points

- **Well limits**: Rows (max 40), Columns (max 40), Values (max 40)
- **SortConfiguration**: Uses `FieldSortOptions` (unique to PivotTable) — specify which row/column to sort and by which value field
- **MetricPlacement**: `ROW` (measures as rows) or `COLUMN` (measures as columns, default)
- **CollapsedRowDimensionsVisibility**: `VISIBLE` shows expand/collapse toggles for row hierarchies
- **CalculatedMeasureField** is valid in the Values well for inline pivot calculations
- **TotalOptions**: Separate control for row totals, column totals, and subtotals

### Pivot Sort Pitfall

PivotTable does NOT use `CategorySort` or `RowSort`. It uses `FieldSortOptions`, which is structurally different:
```json
{
  "FieldSortOptions": [
    {
      "FieldId": "$ROW_FIELD_ID",
      "SortBy": {
        "Field": {
          "FieldId": "$VALUE_FIELD_ID",
          "Direction": "DESC"
        }
      }
    }
  ]
}
```

---

## HeatMapVisual

### Field Wells

Wrapper key: `HeatMapAggregatedFieldWells`

```json
{
  "HeatMapVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "HeatMapAggregatedFieldWells": {
          "Rows": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_ROW",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$ROW_COLUMN"}
              }
            }
          ],
          "Columns": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_COL",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$COL_COLUMN"}
              }
            }
          ],
          "Values": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_VAL",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$VALUE_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "SUM"}
              }
            }
          ]
        }
      },
      "ColorScale": {
        "ColorFillType": "GRADIENT",
        "Colors": [
          {"Color": "#DE3B00"},
          {"Color": "#FFCC00"},
          {"Color": "#2CAD00"}
        ]
      },
      "Legend": {"Visibility": "VISIBLE"},
      "DataLabels": {"Visibility": "VISIBLE"},
      "SortConfiguration": {
        "HeatMapRowSort": [
          {
            "FieldSort": {
              "FieldId": "$FIELD_ID_ROW",
              "Direction": "ASC"
            }
          }
        ],
        "HeatMapColumnSort": [
          {
            "FieldSort": {
              "FieldId": "$FIELD_ID_COL",
              "Direction": "ASC"
            }
          }
        ]
      }
    },
    "Actions": []
  }
}
```

### Key Points

- **Well limits**: Rows (max 1), Columns (max 1), Values (max 1) — the most restrictive tabular visual
- **Max cells**: 100 rows x 100 columns
- **ColorScale.ColorFillType**: `GRADIENT` (smooth transition) or `DISCRETE` (distinct buckets)
- **SortConfiguration**: Uses `HeatMapRowSort` and `HeatMapColumnSort` (unique sort keys)
- ColorScale accepts 2 or 3 colors (min, [mid], max)
