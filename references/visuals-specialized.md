# Specialized Visuals: TreeMap, Sankey, Radar, Maps, WordCloud, Empty, Custom, Plugin

---

## TreeMapVisual

### Field Wells

Wrapper key: `TreeMapAggregatedFieldWells`

```json
{
  "TreeMapVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "TreeMapAggregatedFieldWells": {
          "Groups": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_GROUP",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$GROUP_COLUMN"}
              }
            }
          ],
          "Sizes": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_SIZE",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$SIZE_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "SUM"}
              }
            }
          ],
          "Colors": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_COLOR",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$COLOR_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "AVERAGE"}
              }
            }
          ]
        }
      },
      "Legend": {"Visibility": "VISIBLE"},
      "DataLabels": {"Visibility": "VISIBLE", "LabelContent": "VALUE"},
      "ColorScale": {
        "ColorFillType": "GRADIENT",
        "Colors": [
          {"Color": "#DE3B00"},
          {"Color": "#2CAD00"}
        ]
      },
      "SortConfiguration": {
        "TreeMapSort": [
          {
            "FieldSort": {
              "FieldId": "$FIELD_ID_SIZE",
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

- **Well limits**: Groups (max 1), Sizes (max 1), Colors (max 1)
- **Groups**: Determines the rectangles (one per category value)
- **Sizes**: Controls rectangle area
- **Colors**: Controls rectangle color intensity (independent of size)
- **SortConfiguration**: Uses `TreeMapSort` (unique key)

---

## SankeyDiagramVisual

### Field Wells

Wrapper key: `SankeyDiagramAggregatedFieldWells`

```json
{
  "SankeyDiagramVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "SankeyDiagramAggregatedFieldWells": {
          "Source": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_SOURCE",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$SOURCE_COLUMN"}
              }
            }
          ],
          "Destination": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_DEST",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$DEST_COLUMN"}
              }
            }
          ],
          "Weight": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_WEIGHT",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$WEIGHT_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "SUM"}
              }
            }
          ]
        }
      },
      "DataLabels": {"Visibility": "VISIBLE"},
      "SortConfiguration": {}
    },
    "Actions": []
  }
}
```

### Key Points

- **Source/Destination**: Define flow from left nodes to right nodes
- **Weight**: Controls the thickness of flow connections
- No configurable color scale — colors are auto-assigned per node

---

## RadarChartVisual

### Field Wells

Wrapper key: `RadarChartAggregatedFieldWells`

```json
{
  "RadarChartVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "RadarChartAggregatedFieldWells": {
          "Category": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_CAT",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$AXIS_COLUMN"}
              }
            }
          ],
          "Color": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_COLOR",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$SERIES_COLUMN"}
              }
            }
          ],
          "Values": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_VAL",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$VALUE_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "AVERAGE"}
              }
            }
          ]
        }
      },
      "Shape": "POLYGON",
      "Legend": {"Visibility": "VISIBLE"},
      "AlternateBandColorsVisibility": "VISIBLE",
      "SortConfiguration": {}
    },
    "Actions": []
  }
}
```

### Key Points

- **Well limits**: Category (max 1), Color (max 1), Values (max 20)
- **Shape**: `POLYGON` (straight lines between axes) or `CIRCLE` (curved)
- **Category**: Defines the radar axes (spokes)
- **Color**: Creates overlapping radar shapes for comparison

---

## FilledMapVisual

### Field Wells

Wrapper key: `FilledMapAggregatedFieldWells`

```json
{
  "FilledMapVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "FilledMapAggregatedFieldWells": {
          "Geospatial": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_GEO",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$STATE_COLUMN"}
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
      "Legend": {"Visibility": "VISIBLE"},
      "MapStyleOptions": {"BaseMapStyle": "LIGHT_GRAY"},
      "WindowOptions": {
        "MapZoomMode": "AUTO"
      },
      "SortConfiguration": {}
    },
    "Actions": []
  }
}
```

### Key Points

- **Well limits**: Geospatial (max 1), Values (max 1)
- **Geospatial column**: Must be recognized as a geographic type (country, state, city, zip)
- **BaseMapStyle**: `LIGHT_GRAY`, `DARK_GRAY`, `STREET`, `IMAGERY`
- **MapZoomMode**: `AUTO` (fit to data) or `MANUAL`

---

## GeospatialMapVisual

> **IMPORTANT**: Uses `Columns` array instead of named field wells — structurally different from all other visuals.

```json
{
  "GeospatialMapVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "GeospatialMapAggregatedFieldWells": {
          "Geospatial": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_GEO",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$LOCATION_COLUMN"}
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
          "Colors": []
        }
      },
      "PointStyleOptions": {
        "SelectedPointStyle": "POINT",
        "ClusterMarkerConfiguration": {
          "ClusterMarker": {
            "SimpleClusterMarker": {
              "Color": "#3366FF"
            }
          }
        }
      },
      "MapStyleOptions": {"BaseMapStyle": "LIGHT_GRAY"},
      "WindowOptions": {"MapZoomMode": "AUTO"}
    },
    "Actions": []
  }
}
```

### Key Points

- **SelectedPointStyle**: `POINT` (individual markers), `CLUSTER` (grouped markers), `HEATMAP`
- Supports latitude/longitude columns or recognized place names

---

## WordCloudVisual

### Field Wells

Wrapper key: `WordCloudAggregatedFieldWells`

```json
{
  "WordCloudVisual": {
    "VisualId": "$VISUAL_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": {
        "WordCloudAggregatedFieldWells": {
          "GroupBy": [
            {
              "CategoricalDimensionField": {
                "FieldId": "$FIELD_ID_GROUP",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$WORD_COLUMN"}
              }
            }
          ],
          "Size": [
            {
              "NumericalMeasureField": {
                "FieldId": "$FIELD_ID_SIZE",
                "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$COUNT_COLUMN"},
                "AggregationFunction": {"SimpleNumericalAggregation": "SUM"}
              }
            }
          ]
        }
      },
      "WordCloudOptions": {
        "WordOrientation": "HORIZONTAL",
        "WordPadding": "MEDIUM",
        "CloudLayout": "FLUID",
        "MaximumStringLength": 64,
        "WordScaling": "EMPHASIZE"
      },
      "SortConfiguration": {
        "CategorySort": [
          {
            "FieldSort": {
              "FieldId": "$FIELD_ID_SIZE",
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

- **Well limits**: GroupBy (max 10), Size (max 1)
- **WordOrientation**: `HORIZONTAL`, `MOSTLY_HORIZONTAL`, `MOSTLY_VERTICAL`, `VERTICAL`
- **CloudLayout**: `FLUID` or `NORMAL`
- **WordScaling**: `EMPHASIZE` (larger range) or `NORMAL`

---

## EmptyVisual

Placeholder visual with no field configuration. Used as a spacer or future placeholder.

```json
{
  "EmptyVisual": {
    "VisualId": "$VISUAL_ID",
    "DataSetIdentifier": "$DS_IDENTIFIER",
    "Actions": []
  }
}
```

---

## CustomContentVisual

Embeds external content (images, URLs) in the analysis.

```json
{
  "CustomContentVisual": {
    "VisualId": "$VISUAL_ID",
    "DataSetIdentifier": "$DS_IDENTIFIER",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ContentUrl": "https://$CONTENT_HOST/$PATH",
    "ContentType": "IMAGE",
    "ImageScaling": "FIT_TO_WIDTH",
    "Actions": []
  }
}
```

### Key Points

- **ContentType**: `IMAGE`, `OTHER_EMBEDDED_CONTENT`
- **ImageScaling**: `FIT_TO_HEIGHT`, `FIT_TO_WIDTH`, `DO_NOT_SCALE`, `SCALE_TO_VISUAL`

---

## PluginVisual

Requires a registered QuickSight plugin.

```json
{
  "PluginVisual": {
    "VisualId": "$VISUAL_ID",
    "PluginArn": "arn:aws:quicksight:$REGION:$ACCOUNT_ID:plugin/$PLUGIN_ID",
    "Title": {"Visibility": "VISIBLE", "FormatText": {"PlainText": "$TITLE"}},
    "ChartConfiguration": {
      "FieldWells": [],
      "VisualOptions": {
        "VisualProperties": [
          {"Name": "$PROPERTY_NAME", "Value": "$PROPERTY_VALUE"}
        ]
      }
    },
    "Actions": []
  }
}
```

### Key Points

- **PluginArn**: Required — references a pre-registered plugin
- **VisualProperties**: Plugin-specific key-value configuration
- Field wells structure depends on the specific plugin
