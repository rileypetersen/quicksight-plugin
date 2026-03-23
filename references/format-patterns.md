# Format Patterns and Conditional Formatting

---

## Double-Nested FormatConfiguration Hierarchy

The most confusing part of the QuickSight API is the format configuration nesting. The key `FormatConfiguration` appears at two levels with different types:

```
NumericalMeasureField
  └─ FormatConfiguration          ← NumberFormatConfiguration (outer)
       └─ FormatConfiguration     ← NumericFormatConfiguration (inner — SAME KEY NAME!)
            ├─ NumberDisplayFormatConfiguration     (plain numbers)
            ├─ CurrencyDisplayFormatConfiguration   (currency values)
            └─ PercentageDisplayFormatConfiguration (percentages)

CategoricalMeasureField
  └─ FormatConfiguration          ← StringFormatConfiguration
       └─ NullValueFormatConfiguration
            └─ NullString

DateMeasureField
  └─ FormatConfiguration          ← DateTimeFormatConfiguration
       └─ DateTimeFormat          ← flat string like "yyyy-MM-dd"

DateDimensionField
  └─ FormatConfiguration          ← DateTimeFormatConfiguration
       └─ DateTimeFormat          ← flat string like "yyyy-MM-dd"
```

---

## Context-Specific Nesting

The path to the display format differs depending on where the field appears:

### In NumericalMeasureField (aggregated tables, charts, KPIs)
```json
{
  "NumericalMeasureField": {
    "FieldId": "$FIELD_ID",
    "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$COLUMN"},
    "AggregationFunction": {"SimpleNumericalAggregation": "SUM"},
    "FormatConfiguration": {
      "FormatConfiguration": {
        "NumberDisplayFormatConfiguration": { ... }
      }
    }
  }
}
```

### In UnaggregatedField (unaggregated tables)
```json
{
  "FieldId": "$FIELD_ID",
  "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$COLUMN"},
  "FormatConfiguration": {
    "NumberFormatConfiguration": {
      "FormatConfiguration": {
        "NumberDisplayFormatConfiguration": { ... }
      }
    }
  }
}
```

Note the extra `NumberFormatConfiguration` wrapper in unaggregated fields.

### In DateDimensionField
```json
{
  "DateDimensionField": {
    "FieldId": "$FIELD_ID",
    "Column": {"DataSetIdentifier": "$DS_IDENTIFIER", "ColumnName": "$DATE_COLUMN"},
    "DateGranularity": "DAY",
    "FormatConfiguration": {
      "DateTimeFormat": "yyyy-MM-dd"
    }
  }
}
```

Flat string — no nesting at all.

---

## Complete JSON Examples

### Number with Thousands Separator and Decimal Places

```json
{
  "FormatConfiguration": {
    "FormatConfiguration": {
      "NumberDisplayFormatConfiguration": {
        "DecimalPlacesConfiguration": {
          "DecimalPlaces": 1
        },
        "SeparatorConfiguration": {
          "DecimalSeparator": "DOT",
          "ThousandsSeparator": {
            "Visibility": "VISIBLE",
            "Symbol": "COMMA"
          }
        },
        "NegativeValueConfiguration": {
          "DisplayMode": "NEGATIVE"
        }
      }
    }
  }
}
```

### Currency ($ with Comma Separator)

```json
{
  "FormatConfiguration": {
    "FormatConfiguration": {
      "CurrencyDisplayFormatConfiguration": {
        "Symbol": "$",
        "DecimalPlacesConfiguration": {
          "DecimalPlaces": 0
        },
        "SeparatorConfiguration": {
          "DecimalSeparator": "DOT",
          "ThousandsSeparator": {
            "Visibility": "VISIBLE",
            "Symbol": "COMMA"
          }
        },
        "NegativeValueConfiguration": {
          "DisplayMode": "NEGATIVE"
        },
        "NullValueFormatConfiguration": {
          "NullString": "-"
        }
      }
    }
  }
}
```

### Percentage

```json
{
  "FormatConfiguration": {
    "FormatConfiguration": {
      "PercentageDisplayFormatConfiguration": {
        "DecimalPlacesConfiguration": {
          "DecimalPlaces": 1
        },
        "SeparatorConfiguration": {
          "DecimalSeparator": "DOT",
          "ThousandsSeparator": {
            "Visibility": "HIDDEN"
          }
        }
      }
    }
  }
}
```

### Date Format

```json
{
  "FormatConfiguration": {
    "DateTimeFormat": "yyyy-MM-dd"
  }
}
```

Common date patterns:
| Pattern | Example |
|---------|---------|
| `yyyy-MM-dd` | 2026-01-15 |
| `MMM dd, yyyy` | Jan 15, 2026 |
| `MM/dd/yyyy` | 01/15/2026 |
| `yyyy-MM-dd HH:mm` | 2026-01-15 14:30 |
| `MMMM yyyy` | January 2026 |
| `yyyy 'Q'Q` | 2026 Q1 |

---

## ThousandsSeparator

> **IMPORTANT**: The key is `ThousandsSeparator`, NOT `ThousandsSeparatorOptions`.

**Correct:**
```json
{
  "SeparatorConfiguration": {
    "DecimalSeparator": "DOT",
    "ThousandsSeparator": {
      "Visibility": "VISIBLE",
      "Symbol": "COMMA"
    }
  }
}
```

**Incorrect:**
```json
{
  "SeparatorConfiguration": {
    "ThousandsSeparatorOptions": {
      "Visibility": "VISIBLE",
      "Symbol": "COMMA"
    }
  }
}
```

**Symbol values:** `COMMA`, `DOT`, `SPACE`

**DecimalSeparator values:** `DOT`, `COMMA`, `SPACE`

---

## Python Helper Functions

### Generic Number Format

```python
def number_format(decimal_places: int = 0, thousands: bool = True) -> dict:
    """Build a NumberDisplayFormatConfiguration."""
    config = {
        "DecimalPlacesConfiguration": {"DecimalPlaces": decimal_places}
    }
    if thousands:
        config["SeparatorConfiguration"] = {
            "DecimalSeparator": "DOT",
            "ThousandsSeparator": {"Visibility": "VISIBLE", "Symbol": "COMMA"}
        }
    return {
        "FormatConfiguration": {
            "FormatConfiguration": {
                "NumberDisplayFormatConfiguration": config
            }
        }
    }
```

### Currency Format

```python
def currency_fmt(symbol: str = "$", decimal_places: int = 0) -> dict:
    """Build a CurrencyDisplayFormatConfiguration."""
    return {
        "FormatConfiguration": {
            "FormatConfiguration": {
                "CurrencyDisplayFormatConfiguration": {
                    "Symbol": symbol,
                    "DecimalPlacesConfiguration": {"DecimalPlaces": decimal_places},
                    "SeparatorConfiguration": {
                        "DecimalSeparator": "DOT",
                        "ThousandsSeparator": {"Visibility": "VISIBLE", "Symbol": "COMMA"}
                    },
                    "NegativeValueConfiguration": {"DisplayMode": "NEGATIVE"}
                }
            }
        }
    }
```

### Percentage Format

```python
def pct_fmt(decimal_places: int = 1) -> dict:
    """Build a PercentageDisplayFormatConfiguration.

    Note: Do NOT add Suffix "%" — PercentageDisplayFormatConfiguration
    already formats values as percentages. Adding a suffix would produce "45%%".
    """
    return {
        "FormatConfiguration": {
            "FormatConfiguration": {
                "PercentageDisplayFormatConfiguration": {
                    "DecimalPlacesConfiguration": {"DecimalPlaces": decimal_places}
                }
            }
        }
    }
```

---

## Conditional Formatting

### Overview

Conditional formatting varies by visual type. The top-level structure is always:

```json
{
  "ConditionalFormatting": {
    "ConditionalFormattingOptions": [ ... ]
  }
}
```

The contents of each option depend on the visual type.

### Expression Syntax

Expressions use curly braces for field references (not SQL column names):
```
{column_name} < 0
{column_name} > 100
{column_name} = "Active"
```

Operators: `<`, `>`, `<=`, `>=`, `=`, `!=`, `AND`, `OR`, `NOT`

### ConditionalFormattingColor Types

**Solid** — single color based on condition:
```json
{
  "Solid": {
    "Expression": "{$COLUMN_NAME} < 50",
    "Color": "#DE3B00"
  }
}
```

**Gradient** — color scale across a range:
```json
{
  "Gradient": {
    "Expression": "{$COLUMN_NAME}",
    "Color": {
      "Stops": [
        {"GradientOffset": 0, "Color": "#DE3B00"},
        {"GradientOffset": 50, "Color": "#FFCC00"},
        {"GradientOffset": 100, "Color": "#2CAD00"}
      ]
    }
  }
}
```

### Table Cell Conditional Formatting

```json
{
  "ConditionalFormatting": {
    "ConditionalFormattingOptions": [
      {
        "Cell": {
          "FieldId": "$FIELD_ID",
          "TextFormat": {
            "TextColor": {
              "Solid": {
                "Expression": "{$COLUMN_NAME} < 0",
                "Color": "#DE3B00"
              }
            },
            "BackgroundColor": {
              "Gradient": {
                "Expression": "{$COLUMN_NAME}",
                "Color": {
                  "Stops": [
                    {"GradientOffset": 0, "Color": "#FFCCCC"},
                    {"GradientOffset": 100, "Color": "#CCFFCC"}
                  ]
                }
              }
            },
            "Icon": {
              "IconSet": {
                "Expression": "{$COLUMN_NAME}",
                "IconSetType": "THREE_COLOR_ARROW"
              }
            }
          }
        }
      }
    ]
  }
}
```

### KPI Conditional Formatting

```json
{
  "ConditionalFormatting": {
    "ConditionalFormattingOptions": [
      {
        "PrimaryValue": {
          "TextColor": {
            "Solid": {
              "Expression": "{$COLUMN_NAME} >= 90",
              "Color": "#2CAD00"
            }
          },
          "Icon": {
            "IconSet": {
              "Expression": "{$COLUMN_NAME}",
              "IconSetType": "THREE_COLOR_ARROW"
            }
          }
        }
      },
      {
        "PrimaryValue": {
          "TextColor": {
            "Solid": {
              "Expression": "{$COLUMN_NAME} < 50",
              "Color": "#DE3B00"
            }
          }
        }
      }
    ]
  }
}
```

Note: Multiple `ConditionalFormattingOptions` entries are evaluated in order; first match wins.

### Icon Set Types

| IconSetType | Icons |
|-------------|-------|
| `THREE_COLOR_ARROW` | Up (green), right (yellow), down (red) arrows |
| `THREE_GRAY_ARROW` | Up, right, down arrows (gray) |
| `THREE_SHAPE` | Circle, triangle, diamond |
| `THREE_CIRCLE` | Green, yellow, red circles |
| `FOUR_COLOR_ARROW` | Up, up-right, down-right, down arrows |
| `FOUR_GRAY_ARROW` | Same as above in gray |
| `CARET_UP_MINUS_DOWN` | Caret up, minus, caret down |
| `THREE_FLAG` | Green, yellow, red flags |
| `BARS` | 1, 2, 3, 4 bars |
| `CHECK_X` | Check mark, X mark |
| `PLUS_MINUS` | Plus, minus |

### Bar Chart Conditional Formatting

```json
{
  "ConditionalFormatting": {
    "ConditionalFormattingOptions": [
      {
        "Bar": {
          "FieldId": "$FIELD_ID",
          "Color": {
            "Solid": {
              "Expression": "{$COLUMN_NAME} > 1000",
              "Color": "#2CAD00"
            }
          }
        }
      }
    ]
  }
}
```

Note: The option key varies by visual type — `Cell` for tables, `PrimaryValue` for KPIs, `Bar` for bar charts, etc.
