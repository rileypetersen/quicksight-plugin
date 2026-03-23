# Calculated Fields

---

## Dataset vs Analysis Calculated Fields

### Dataset Calculated Fields

Created via `CreateColumnsOperation` in the `LogicalTableMap` transforms. These are evaluated at data ingestion time and stored as physical columns.

```json
{
  "LogicalTableMap": {
    "$LOGICAL_TABLE_ID": {
      "Alias": "$TABLE_ALIAS",
      "Source": {
        "PhysicalTableId": "$PHYSICAL_TABLE_ID"
      },
      "DataTransforms": [
        {
          "CreateColumnsOperation": {
            "Columns": [
              {
                "ColumnName": "$NEW_COLUMN",
                "ColumnId": "$COLUMN_ID",
                "Expression": "ifelse({status} = 'active', 1, 0)"
              }
            ]
          }
        }
      ]
    }
  }
}
```

**Limitations:**
- Cannot use LAC (Level-Aware Calculations) like `sumOver`, `rankOver`
- Cannot reference fields from other datasets
- Evaluated row-by-row only

### Analysis Calculated Fields

Defined in the `CalculatedFields` array at the top level of `AnalysisDefinition`. These are evaluated at query time and support the full expression language.

```json
{
  "AnalysisDefinition": {
    "CalculatedFields": [
      {
        "DataSetIdentifier": "$DS_IDENTIFIER",
        "Name": "$CALC_FIELD_NAME",
        "Expression": "sumOver({revenue}, [{region}], PRE_AGG)"
      }
    ],
    "DataSetIdentifierDeclarations": [ ... ],
    "Sheets": [ ... ]
  }
}
```

**Max**: 2000 calculated fields per analysis.

**Advantages over dataset fields:**
- Support LAC functions (window functions)
- Can reference other calculated fields
- Changes don't require data re-ingestion
- Available across all visuals using the same dataset

---

## Expression Syntax

### Field References

```
{column_name}                      -- simple column reference
{DatasetIdentifier.column_name}    -- qualified reference (for multi-dataset)
```

### String Functions

| Function | Example | Result |
|----------|---------|--------|
| `concat` | `concat({first}, " ", {last})` | "John Smith" |
| `substring` | `substring({name}, 1, 3)` | "Joh" |
| `strlen` | `strlen({name})` | 10 |
| `trim` | `trim({name})` | removes whitespace |
| `toLower` | `toLower({name})` | "john" |
| `toUpper` | `toUpper({name})` | "JOHN" |
| `replace` | `replace({text}, "old", "new")` | substitution |
| `split` | `split({csv}, ",", 1)` | first element |
| `contains` | `contains({name}, "test")` | true/false |
| `startsWith` | `startsWith({url}, "https")` | true/false |
| `endsWith` | `endsWith({email}, ".com")` | true/false |

### Numeric Functions

| Function | Example |
|----------|---------|
| `ceil` | `ceil({score})` |
| `floor` | `floor({score})` |
| `round` | `round({score}, 2)` |
| `abs` | `abs({delta})` |
| `log` | `log({value})` |
| `sqrt` | `sqrt({variance})` |
| `mod` | `mod({value}, 10)` |
| `exp` | `exp({growth_rate})` |

### Date Functions

| Function | Example | Notes |
|----------|---------|-------|
| `dateDiff` | `dateDiff({start}, {end}, "DAY")` | Units: YEAR, QUARTER, MONTH, WEEK, DAY, HOUR, MINUTE, SECOND |
| `addDateTime` | `addDateTime(30, "DAY", {date})` | Add/subtract from date |
| `extract` | `extract("MONTH", {date})` | Extract component |
| `parseDate` | `parseDate({str}, "yyyy-MM-dd")` | String to date |
| `formatDate` | `formatDate({date}, "MMM yyyy")` | Date to string |
| `now` | `now()` | Current timestamp |
| `truncDate` | `truncDate("MONTH", {date})` | Truncate to unit |

### Conditional Functions

```
ifelse({score} >= 80, "Healthy",
       {score} >= 50, "At Risk",
       "Critical")
```

`ifelse` supports multiple condition-value pairs. The last argument (without a condition) is the else value.

### Null Handling

| Function | Example | Notes |
|----------|---------|-------|
| `isNull` | `isNull({field})` | Returns true if null |
| `isNotNull` | `isNotNull({field})` | Returns true if not null |
| `nullIf` | `nullIf({field}, 0)` | Returns null if value equals arg |
| `coalesce` | `coalesce({a}, {b}, 0)` | First non-null value |

### Type Conversion

| Function | Example |
|----------|---------|
| `toString` | `toString({number})` |
| `parseInt` | `parseInt({string})` |
| `parseDecimal` | `parseDecimal({string})` |
| `parseDate` | `parseDate({string}, "yyyy-MM-dd")` |

---

## Window Functions (Analysis Calculated Fields Only)

These are LAC (Level-Aware Calculations) — they compute values across groups of rows. Not available in dataset calculated fields.

### Aggregation Over Partitions

```
sumOver({revenue}, [{region}], PRE_AGG)
avgOver({score}, [{department}, {quarter}], PRE_AGG)
countOver({id}, [{category}], PRE_AGG)
minOver({price}, [{product_type}], PRE_AGG)
maxOver({score}, [{team}], PRE_AGG)
```

**Syntax**: `functionOver({measure}, [{partition_field1}, {partition_field2}], LEVEL)`

**Levels:**
| Level | Meaning |
|-------|---------|
| `PRE_AGG` | Calculate before visual aggregation (most common) |
| `PRE_FILTER` | Calculate before filters are applied |
| `POST_AGG_FILTER` | Calculate after aggregation and filtering |

### Ranking Functions

```
rankOver({score}, [{category}], DESC, PRE_AGG)
denseRankOver({score}, [{category}], DESC, PRE_AGG)
percentileOver({score}, 90, [{category}], PRE_AGG)
```

**Syntax**: `rankOver({measure}, [{partition}], SORT_DIRECTION, LEVEL)`

**Sort direction**: `ASC` or `DESC`

### Offset Functions

```
lag({revenue}, 1, [{date}], ASC, PRE_AGG)
lead({revenue}, 1, [{date}], ASC, PRE_AGG)
```

**Syntax**: `lag({field}, offset, [{sort_field}], SORT_DIRECTION, LEVEL)`

### Running Calculations

```
runningSum({amount}, [{date}], ASC, PRE_AGG)
runningAvg({score}, [{date}], ASC, PRE_AGG)
runningCount({id}, [{date}], ASC, PRE_AGG)
runningMin({price}, [{date}], ASC, PRE_AGG)
runningMax({price}, [{date}], ASC, PRE_AGG)
```

### Percent of Total

```
percentOfTotal({revenue}, [{region}], PRE_AGG)
```

Returns a decimal (0.0 to 1.0), not a percentage. Multiply by 100 or use percentage formatting.

---

## Common Recipes

### Year-over-Year Growth

```
ifelse(
  lag({revenue}, 12, [{month}], ASC, PRE_AGG) = 0,
  NULL,
  ({revenue} - lag({revenue}, 12, [{month}], ASC, PRE_AGG))
    / lag({revenue}, 12, [{month}], ASC, PRE_AGG)
)
```

### Running Total

```
runningSum({amount}, [{date}], ASC, PRE_AGG)
```

### Null-Safe Division

```
ifelse({denominator} = 0, NULL, {numerator} / {denominator})
```

Or more concisely:
```
{numerator} / nullIf({denominator}, 0)
```

### Cohort Bucket

```
ifelse(
  {score} >= 80, "Healthy",
  {score} >= 50, "At Risk",
  "Critical"
)
```

### Percent of Category Total

```
{revenue} / sumOver({revenue}, [{category}], PRE_AGG)
```

### Moving Average (3-period)

```
(
  {value}
  + coalesce(lag({value}, 1, [{date}], ASC, PRE_AGG), {value})
  + coalesce(lag({value}, 2, [{date}], ASC, PRE_AGG), {value})
) / 3
```

### Days Since Last Activity

```
dateDiff({last_activity_date}, now(), "DAY")
```

### Fiscal Quarter (April start)

```
concat(
  "FY",
  toString(
    ifelse(extract("MONTH", {date}) >= 4,
           extract("YEAR", {date}),
           extract("YEAR", {date}) - 1)
  ),
  " Q",
  toString(
    ifelse(extract("MONTH", {date}) >= 4,
           ceil((extract("MONTH", {date}) - 3) / 3),
           ceil((extract("MONTH", {date}) + 9) / 3))
  )
)
```

### Top N Flag

```
ifelse(rankOver({revenue}, [{category}], DESC, PRE_AGG) <= 10, "Top 10", "Other")
```

### Cumulative Percent

```
runningSum({count}, [{bucket}], ASC, PRE_AGG)
  / sumOver({count}, [], PRE_AGG)
```

Empty partition `[]` means "across all rows."
