# Chart Visuals: Bar, Line, Combo, Pie, Funnel

All chart visuals use **wrapped** field wells — fields are nested inside a type-specific aggregated wrapper key.

---

## BarChartVisual

### Field Wells

Wrapper key: `BarChartAggregatedFieldWells`

```json
{
  "BarChartVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "BarChartAggregatedFieldWells": {
          "Category": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_CAT",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$CATEGORY_COLUMN"}
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
          ],
          "Colors": [],
          "SmallMultiples": []
        }
      },
      "Orientation": "VERTICAL",
      "BarsArrangement": "CLUSTERED",
      "Legend": {"Visibility": "VISIBLE", "Position": "RIGHT"},
      "DataLabels": {"Visibility": "VISIBLE", "Position": "OUTSIDE"},
      "Tooltip": {
        "TooltipVisibility": "VISIBLE",
        "FieldBasedTooltip": {
          "AggregationVisibility": "VISIBLE",
          "TooltipTitleType": "PRIMARY_VALUE",
          "TooltipFields": [
            {
              "FieldTooltipItem": {
                "FieldId": "$FIELD_ID_VAL",
                "Visibility": "VISIBLE"
              }
            }
          ]
        }
      },
      "SortConfiguration": {
        "CategorySort": [
          {
            "FieldSort": {
              "FieldId": "$FIELD_ID_VAL",
              "Direction": "DESC"
            }
          }
        ]
      }
    },
    "ColumnHierarchies": [],
    "Actions": []
  }
}
```

### Key Points

- **Well limits**: Category (max 200), Values (max 200), Colors (max 200), SmallMultiples (max 1)
- **Orientation**: `HORIZONTAL` (bars go left-right), `VERTICAL` (bars go up-down, i.e., column chart)
- **BarsArrangement**: `CLUSTERED`, `STACKED`, `STACKED_PERCENT`
- **SmallMultiples**: Max 1 DimensionField. Creates a grid of mini-charts.
- **SortConfiguration**: Use `CategorySort` with `FieldSort` (by FieldId) or `ColumnSort` (by Column)

### Common Pitfall

Using `DateDimensionField` in Category without setting `DateGranularity` results in the finest grain (individual timestamps). Always set granularity:
```json
{
  "DateDimensionField": {
    "FieldId": "$FIELD_ID",
    "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$DATE_COLUMN"},
    "DateGranularity": "MONTH"
  }
}
```

---

## LineChartVisual

### Field Wells

Wrapper key: `LineChartAggregatedFieldWells`

```json
{
  "LineChartVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "LineChartAggregatedFieldWells": {
          "Category": [
            {
              "DateDimensionField": {
                "FieldId": "$FIELD_ID_DATE",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$DATE_COLUMN"},
                "DateGranularity": "WEEK"
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
          ],
          "Colors": [],
          "SmallMultiples": []
        }
      },
      "Type": "LINE",
      "Legend": {"Visibility": "VISIBLE"},
      "DataLabels": {"Visibility": "HIDDEN"},
      "PrimaryYAxisDisplayOptions": {
        "AxisOptions": {"AxisLineVisibility": "VISIBLE"}
      },
      "SortConfiguration": {
        "CategorySort": [
          {
            "FieldSort": {
              "FieldId": "$FIELD_ID_DATE",
              "Direction": "ASC"
            }
          }
        ]
      }
    },
    "ColumnHierarchies": [
      {
        "DateTimeHierarchy": {
          "HierarchyId": "$HIERARCHY_ID",
          "DrillDownFilters": []
        }
      }
    ],
    "Actions": []
  }
}
```

### Key Points

- **Well limits**: Category (max 200), Values (max 200), Colors (max 200), SmallMultiples (max 1)
- **Type**: `LINE`, `STACKED_AREA`, `AREA`
- **ColumnHierarchies**: Required for date drill-down (year > quarter > month > week > day). Use `DateTimeHierarchy`.
- **ScrollbarOptions**: `{"VisibleRange": {"PercentRange": {"From": 70, "To": 100}}}` to show only the most recent portion
- **ReferenceLines**: Add horizontal/vertical reference lines via `ChartConfiguration.ReferenceLines`

### Common Pitfall

Forgetting `ColumnHierarchies` with `DateTimeHierarchy` means users cannot drill up/down on dates in the console.

---

## ComboChartVisual

### Field Wells

Wrapper key: `ComboChartAggregatedFieldWells`

```json
{
  "ComboChartVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "ComboChartAggregatedFieldWells": {
          "Category": [
            {
              "DateDimensionField": {
                "FieldId": "$FIELD_ID_DATE",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$DATE_COLUMN"},
                "DateGranularity": "MONTH"
              }
            }
          ],
          "BarValues": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_BAR",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$BAR_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "SUM"}
              }
            }
          ],
          "LineValues": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_LINE",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$LINE_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "AVERAGE"}
              }
            }
          ],
          "Colors": []
        }
      },
      "BarsArrangement": "CLUSTERED",
      "Legend": {"Visibility": "VISIBLE"},
      "BarDataLabels": {"Visibility": "HIDDEN"},
      "LineDataLabels": {"Visibility": "HIDDEN"},
      "SortConfiguration": {
        "CategorySort": [
          {
            "FieldSort": {
              "FieldId": "$FIELD_ID_DATE",
              "Direction": "ASC"
            }
          }
        ]
      }
    },
    "ColumnHierarchies": [],
    "Actions": []
  }
}
```

### Key Points

- **Well limits**: Category (max 200), BarValues (max 200), LineValues (max 200), Colors (max 200)
- **BarsArrangement**: `CLUSTERED`, `STACKED` — does NOT support `STACKED_PERCENT`
- **2500 data point limit**: Combo charts cap at 2500 data points before truncating
- **Separate DataLabels**: `BarDataLabels` and `LineDataLabels` are configured independently
- Bars render on primary Y axis, lines on secondary Y axis by default

---

## PieChartVisual

### Field Wells

Wrapper key: `PieChartAggregatedFieldWells`

```json
{
  "PieChartVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "PieChartAggregatedFieldWells": {
          "Category": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_CAT",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$CATEGORY_COLUMN"}
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
          ],
          "SmallMultiples": []
        }
      },
      "DonutOptions": {
        "ArcOptions": {"ArcThickness": "WHOLE"},
        "DonutCenterOptions": {"LabelVisibility": "VISIBLE"}
      },
      "Legend": {"Visibility": "VISIBLE", "Position": "RIGHT"},
      "DataLabels": {"Visibility": "VISIBLE", "LabelContent": "PERCENT"},
      "SortConfiguration": {
        "CategorySort": [
          {
            "FieldSort": {
              "FieldId": "$FIELD_ID_VAL",
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

### Key Points

- **Well limits**: Category (max 200), Values (max 200), SmallMultiples (max 1)
- **DonutOptions.ArcOptions.ArcThickness**: `WHOLE` (pie), `SMALL`/`MEDIUM`/`LARGE` (donut)
- **Default slice limit**: 20 slices. Excess categories grouped into "Other".
- **LabelContent**: `VALUE`, `PERCENT`, `VALUE_AND_PERCENT`

---

## FunnelChartVisual

### Field Wells

Wrapper key: `FunnelChartAggregatedFieldWells`

```json
{
  "FunnelChartVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "FunnelChartAggregatedFieldWells": {
          "Category": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_CAT",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$STAGE_COLUMN"}
              }
            }
          ],
          "Values": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_VAL",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$COUNT_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "SUM"}
              }
            }
          ]
        }
      },
      "DataLabels": {"Visibility": "VISIBLE", "LabelContent": "VALUE_AND_PERCENT"},
      "SortConfiguration": {
        "CategorySort": [
          {
            "FieldSort": {
              "FieldId": "$FIELD_ID_VAL",
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

### Key Points

- **Well limits**: Category (max 1), Values (max 1) — the most restrictive chart type
- **Sort matters**: Controls the order of funnel stages. Sort descending for a traditional narrowing funnel.
- Categories render top-to-bottom in the order determined by sort
