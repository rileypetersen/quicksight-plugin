# Comparison Visuals: ScatterPlot, Waterfall, BoxPlot, Histogram

---

## ScatterPlotVisual

ScatterPlot supports **two mutually exclusive modes**: categorically aggregated and unaggregated.

### Mode 1: Categorically Aggregated

Wrapper key: `ScatterPlotCategoricallyAggregatedFieldWells`

```json
{
  "ScatterPlotVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "ScatterPlotCategoricallyAggregatedFieldWells": {
          "XAxis": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_X",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$X_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "SUM"}
              }
            }
          ],
          "YAxis": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_Y",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$Y_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "AVERAGE"}
              }
            }
          ],
          "Category": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_CAT",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$CATEGORY_COLUMN"}
              }
            }
          ],
          "Label": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_LABEL",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$LABEL_COLUMN"}
              }
            }
          ],
          "Size": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_SIZE",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$SIZE_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "SUM"}
              }
            }
          ]
        }
      },
      "Legend": {"Visibility": "VISIBLE"},
      "DataLabels": {"Visibility": "HIDDEN"},
      "XAxisDisplayOptions": {
        "AxisLineVisibility": "VISIBLE"
      },
      "YAxisDisplayOptions": {
        "AxisLineVisibility": "VISIBLE"
      },
      "SortConfiguration": {}
    },
    "ColumnHierarchies": [],
    "Actions": []
  }
}
```

### Mode 2: Unaggregated

Wrapper key: `ScatterPlotUnaggregatedFieldWells`

> **IMPORTANT**: In unaggregated mode, XAxis and YAxis take **DimensionField** (not MeasureField).

```json
{
  "ScatterPlotVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "ScatterPlotUnaggregatedFieldWells": {
          "XAxis": [
            {
              "NumericalDimensionField": {
                "FieldId": "$FIELD_ID_X",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$X_COLUMN"}
              }
            }
          ],
          "YAxis": [
            {
              "NumericalDimensionField": {
                "FieldId": "$FIELD_ID_Y",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$Y_COLUMN"}
              }
            }
          ],
          "Category": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_CAT",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$CATEGORY_COLUMN"}
              }
            }
          ],
          "Label": [],
          "Size": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_SIZE",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$SIZE_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "SUM"}
              }
            }
          ]
        }
      }
    },
    "Actions": []
  }
}
```

### Key Differences Between Modes

| Aspect | Aggregated | Unaggregated |
|--------|-----------|--------------|
| Wrapper | `ScatterPlotCategoricallyAggregatedFieldWells` | `ScatterPlotUnaggregatedFieldWells` |
| XAxis/YAxis type | `NumericalMeasureField` (MeasureField) | `NumericalDimensionField` (DimensionField) |
| Data points | One per Category value (aggregated) | One per row (raw) |
| Size field | MeasureField in both modes | MeasureField in both modes |

### Common Pitfall

Using `NumericalMeasureField` for XAxis/YAxis in unaggregated mode causes a validation error. The field type must be `NumericalDimensionField`.

---

## WaterfallVisual

### Field Wells

Wrapper key: `WaterfallChartAggregatedFieldWells`

> **NOTE**: The category well is named `Categories` (plural), not `Category` like most other visuals.

```json
{
  "WaterfallVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "WaterfallChartAggregatedFieldWells": {
          "Categories": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_CAT",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$CATEGORY_COLUMN"}
              }
            }
          ],
          "Breakdowns": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_BREAKDOWN",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$BREAKDOWN_COLUMN"}
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
      "WaterfallChartOptions": {
        "TotalBarLabel": "Total"
      },
      "Legend": {"Visibility": "VISIBLE"},
      "DataLabels": {"Visibility": "VISIBLE"},
      "SortConfiguration": {
        "CategorySort": [
          {
            "FieldSort": {
              "FieldId": "$FIELD_ID_CAT",
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

- **Well limits**: Categories (max 200), Breakdowns (max 200), Values (max 200)
- **Categories vs Category**: This is the ONLY chart type that uses `Categories` (plural). Using `Category` fails silently or errors.
- **Breakdowns**: Optional sub-category within each waterfall step
- **TotalBarLabel**: Customize the label on the total bar

---

## BoxPlotVisual

### Field Wells

Wrapper key: `BoxPlotAggregatedFieldWells`

```json
{
  "BoxPlotVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "BoxPlotAggregatedFieldWells": {
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
                "FieldId": "$FIELD_ID_VAL",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$VALUE_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "SUM"}
              }
            }
          ]
        }
      },
      "BoxPlotOptions": {
        "OutlierVisibility": "VISIBLE",
        "AllDataPointsVisibility": "HIDDEN",
        "StyleOptions": {
          "FillStyle": "SOLID"
        }
      },
      "Legend": {"Visibility": "VISIBLE"},
      "SortConfiguration": {
        "CategorySort": [
          {
            "FieldSort": {
              "FieldId": "$FIELD_ID_GROUP",
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

- **Well limits**: GroupBy (max 1), Values (max 5)
- **OutlierVisibility**: `VISIBLE` or `HIDDEN`
- **AllDataPointsVisibility**: `VISIBLE` shows individual data points overlaid on the box
- **FillStyle**: `SOLID` or `TRANSPARENT`

---

## HistogramVisual

### Field Wells

Wrapper key: `HistogramAggregatedFieldWells`

The simplest visual type — just a single Values field.

```json
{
  "HistogramVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "HistogramAggregatedFieldWells": {
          "Values": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_VAL",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$VALUE_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "COUNT"}
              }
            }
          ]
        }
      },
      "HistogramBinOptions": {
        "SelectedBinType": "BIN_COUNT",
        "BinCount": {
          "Value": 20
        }
      },
      "XAxisDisplayOptions": {
        "AxisLineVisibility": "VISIBLE"
      },
      "YAxisDisplayOptions": {
        "AxisLineVisibility": "VISIBLE"
      },
      "DataLabels": {"Visibility": "HIDDEN"}
    },
    "Actions": []
  }
}
```

### Key Points

- **Well limits**: Values (max 1)
- **SelectedBinType**: `BIN_COUNT` (specify number of bins) or `BIN_WIDTH` (specify width of each bin)
- **BinCount.Value**: Number of histogram bins
- **BinWidth.Value**: Width of each bin in the unit of the measure
- No Category well — the histogram bins are auto-generated from the Values distribution
