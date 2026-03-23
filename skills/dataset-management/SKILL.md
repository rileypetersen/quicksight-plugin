---
name: dataset-management
description: Create and manage AWS QuickSight datasets, data sources, and SPICE ingestion. Use when asked to create a QuickSight dataset, connect a database to QuickSight, set up SPICE refresh, configure dataset permissions, create a data source, troubleshoot invisible datasets, fix SPICE ingestion failures, map database columns, create refresh schedules, or manage row-level security. Also use when encountering SQL_SCHEMA_MISMATCH, DATA_SET_SIZE_LIMIT_EXCEEDED, or dataset permission errors.
---

# Dataset Management

## 1. Data Source Creation

Create a DataSource first — the connection object that tells QuickSight how to reach your
database. One data source serves many datasets.

```bash
aws quicksight create-data-source \
  --aws-account-id $ACCOUNT_ID \
  --profile $PROFILE \
  --data-source-id "my-postgres-source" \
  --name "My PostgreSQL" \
  --type POSTGRESQL \
  --data-source-parameters '{
    "PostgreSqlParameters": {
      "Host": "mydb.cluster-xxx.us-east-1.rds.amazonaws.com",
      "Port": 5432,
      "Database": "mydb"
    }
  }' \
  --credentials '{"CredentialPair": {"Username": "app_user", "Password": "..."}}' \
  --ssl-properties '{"DisableSsl": false}'
```

**VPC Connection:** If RDS is in a VPC (it usually is), create a VPC connection first via
`create-vpc-connection`. Security groups on the QuickSight ENIs must allow outbound to RDS.

**Credentials:** `CredentialPair` (inline username/password) or `SecretArn` (Secrets Manager
reference — recommended because credentials rotate without touching QuickSight).

**Permissions:** Call `update-data-source-permissions` immediately after creation — same
invisible-resource trap as datasets.

**Get the data source ARN** (needed for dataset creation):

```bash
aws quicksight describe-data-source \
  --aws-account-id $ACCOUNT_ID \
  --profile $PROFILE \
  --data-source-id "my-postgres-source" \
  --query 'DataSource.Arn' --output text
```

**Supported types:** POSTGRESQL, MYSQL, AURORA, AURORA_POSTGRESQL, SQLSERVER, ORACLE, REDSHIFT,
ATHENA, S3, MARIADB, BIGQUERY, DATABRICKS, and others.

## 2. Dataset Creation Step-by-Step

Follow these steps in order. Skipping permissions causes invisible datasets.

**Step 1: Pre-assign a UUID** (needed for every subsequent operation).

```bash
DATASET_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
echo $DATASET_ID
```

**Step 2: Define the physical table map.** Two approaches:

*RelationalTable* — point at a database view or table directly:

```json
{
  "phys-my-view": {
    "RelationalTable": {
      "DataSourceArn": "$DATA_SOURCE_ARN",
      "Schema": "metrics",
      "Name": "v_my_summary",
      "InputColumns": [
        {"Name": "customer_name", "Type": "STRING"},
        {"Name": "revenue", "Type": "DECIMAL"},
        {"Name": "created_date", "Type": "DATETIME"},
        {"Name": "is_active", "Type": "BOOLEAN"}
      ]
    }
  }
}
```

*CustomSql* — embed a SQL query:

```json
{
  "phys-custom-query": {
    "CustomSql": {
      "DataSourceArn": "$DATA_SOURCE_ARN",
      "Name": "My Custom Query",
      "SqlQuery": "SELECT * FROM metrics.v_my_summary WHERE is_active = true",
      "Columns": [
        {"Name": "customer_name", "Type": "STRING"},
        {"Name": "revenue", "Type": "DECIMAL"}
      ]
    }
  }
}
```

Use RelationalTable for views/tables (simpler, console auto-detects columns). Use CustomSql
when you need filtering or joins the view does not provide.

**CRITICAL: Table map key regex.** Keys must match `[0-9a-zA-Z-]*`. NO underscores — the
API returns a cryptic validation error. Always sanitize:

```python
safe_key = f"phys-{name.replace('_', '-')}"
```

**Step 3: Define the logical table map** (optional — for renames, type casts, calculated
fields). Skip to use physical columns as-is.

```json
{
  "log-my-view": {
    "Alias": "My View",
    "Source": {"PhysicalTableId": "phys-my-view"},
    "DataTransforms": [
      {"RenameColumnOperation": {"ColumnName": "old_name", "NewColumnName": "New Name"}},
      {"CastColumnTypeOperation": {"ColumnName": "date_str", "NewColumnType": "DATETIME", "Format": "yyyy-MM-dd"}}
    ]
  }
}
```

**Step 4: Create the dataset.**

```bash
aws quicksight create-data-set \
  --aws-account-id $ACCOUNT_ID \
  --profile $PROFILE \
  --data-set-id $DATASET_ID \
  --name "My Dataset" \
  --import-mode SPICE \
  --physical-table-map file://physical.json \
  --logical-table-map file://logical.json
```

**Step 5: Grant permissions IMMEDIATELY.** (See Permissions section.) Without this, the
dataset is invisible in the console.

**Step 6: Trigger initial SPICE ingestion.**

```bash
aws quicksight create-ingestion \
  --aws-account-id $ACCOUNT_ID \
  --profile $PROFILE \
  --data-set-id $DATASET_ID \
  --ingestion-id "initial-$(date +%s)"
```

**Step 7: Set up a refresh schedule.** See the Refresh Schedules section below.

## 3. Column Type Mapping

Getting types wrong causes SPICE ingestion failures or silent data truncation.

| PostgreSQL Type     | QuickSight Type | Notes                                         |
|---------------------|-----------------|-----------------------------------------------|
| TEXT, VARCHAR       | STRING          |                                               |
| INT, BIGINT        | INTEGER         |                                               |
| NUMERIC, DECIMAL   | DECIMAL         | Without precision, SPICE may coerce to STRING |
| BOOLEAN            | BOOLEAN         |                                               |
| DATE, TIMESTAMPTZ  | DATETIME        |                                               |
| JSONB              | --              | Extract fields in SQL view first              |
| INTERVAL           | --              | Convert to numeric in SQL                     |
| ARRAY              | --              | Unnest or aggregate in SQL                    |

**Best practice:** Create a database VIEW that handles type conversions, then point QuickSight
at the view. This keeps transformation logic in testable SQL and the QuickSight definition thin.

## 4. Logical Table Transforms

Transforms execute in array order. Available operations:

- **RenameColumnOperation** — Human-readable display names.
- **CastColumnTypeOperation** — Change types. Requires `Format` for STRING-to-DATETIME
  (e.g., `"yyyy-MM-dd"`, `"yyyy-MM-dd'T'HH:mm:ss"`).
- **CreateColumnsOperation** — Calculated fields (QuickSight syntax, not SQL).
- **ProjectOperation** — Select/reorder columns. Omitted columns are dropped.
- **FilterOperation** — Row-level filtering. Applies before SPICE ingestion.
- **TagColumnOperation** — Geographic roles (Country, State, City, Latitude, Longitude).

**Complete example with multiple transforms:**

```json
{
  "log-customer-health": {
    "Alias": "Customer Health",
    "Source": {"PhysicalTableId": "phys-customer-health"},
    "DataTransforms": [
      {"ProjectOperation": {"ProjectedColumns": ["customer_name", "health_score", "arr", "status", "scored_at"]}},
      {"RenameColumnOperation": {"ColumnName": "arr", "NewColumnName": "Annual Recurring Revenue"}},
      {"CastColumnTypeOperation": {"ColumnName": "scored_at", "NewColumnType": "DATETIME", "Format": "yyyy-MM-dd"}},
      {"TagColumnOperation": {"ColumnName": "customer_name", "Tags": [{"ColumnGeographicRole": "STATE"}]}},
      {"CreateColumnsOperation": {"Columns": [{"ColumnName": "ARR Tier", "ColumnId": "arr-tier",
        "Expression": "ifElse({Annual Recurring Revenue} >= 100000, 'Enterprise', ifElse({Annual Recurring Revenue} >= 25000, 'Mid-Market', 'SMB'))"}]}}
    ]
  }
}
```

**Order matters.** Transforms reference column names as they exist after prior transforms.
Referencing a renamed column before its RenameColumnOperation fails.

## 5. Permissions

**THE #1 GOTCHA:** Datasets created via API are invisible to everyone until you explicitly
grant permissions. This is the most common "I can't find my dataset" cause.

**Owner permissions (full control):**

```bash
PRINCIPAL="arn:aws:quicksight:$REGION:$ACCOUNT_ID:user/default/$USER_NAME"

aws quicksight update-data-set-permissions \
  --aws-account-id $ACCOUNT_ID \
  --profile $PROFILE \
  --data-set-id $DATASET_ID \
  --grant-permissions "[{
    \"Principal\": \"$PRINCIPAL\",
    \"Actions\": [
      \"quicksight:DescribeDataSet\",
      \"quicksight:DescribeDataSetPermissions\",
      \"quicksight:PassDataSet\",
      \"quicksight:DescribeIngestion\",
      \"quicksight:ListIngestions\",
      \"quicksight:UpdateDataSet\",
      \"quicksight:DeleteDataSet\",
      \"quicksight:CreateIngestion\",
      \"quicksight:CancelIngestion\",
      \"quicksight:UpdateDataSetPermissions\"
    ]
  }]"
```

**Viewer permissions (read-only):**

```bash
aws quicksight update-data-set-permissions \
  --aws-account-id $ACCOUNT_ID \
  --profile $PROFILE \
  --data-set-id $DATASET_ID \
  --grant-permissions "[{
    \"Principal\": \"$PRINCIPAL\",
    \"Actions\": [
      \"quicksight:DescribeDataSet\",
      \"quicksight:DescribeDataSetPermissions\",
      \"quicksight:PassDataSet\",
      \"quicksight:DescribeIngestion\",
      \"quicksight:ListIngestions\"
    ]
  }]"
```

`PassDataSet` is the critical action — without it, users see the dataset but cannot add it
to analyses. Always include it in both owner and viewer grants.

**Grant to a group** (preferred over individual users for team access):

```bash
PRINCIPAL="arn:aws:quicksight:$REGION:$ACCOUNT_ID:group/default/$GROUP_NAME"
```

## 6. SPICE vs Direct Query

| Factor              | SPICE                       | Direct Query                |
|---------------------|-----------------------------|-----------------------------|
| Performance         | Fast (in-memory)            | Depends on source DB        |
| Cost                | $0.25/GB/month              | No SPICE cost, but DB load  |
| Freshness           | Stale until refresh         | Real-time                   |
| Incremental refresh | Enterprise only             | N/A                         |

**Recommendation:** Use SPICE unless you need real-time data or exceed capacity. SPICE
offloads query load from production databases — important when multiple users view dashboards.
Switch modes via `--import-mode DIRECT_QUERY`; switching Direct-to-SPICE requires an ingestion.

## 7. Refresh Schedules

```bash
aws quicksight create-refresh-schedule \
  --aws-account-id $ACCOUNT_ID \
  --profile $PROFILE \
  --data-set-id $DATASET_ID \
  --schedule '{
    "ScheduleId": "daily-refresh",
    "ScheduleFrequency": {
      "Interval": "DAILY",
      "TimeOfTheDay": "10:00",
      "Timezone": "UTC"
    },
    "StartAfterDateTime": "2024-01-01T10:00:00Z",
    "RefreshType": "FULL_REFRESH"
  }'
```

**Available intervals:** MINUTE15, MINUTE30, HOURLY, DAILY, WEEKLY, MONTHLY.

- MINUTE15, MINUTE30, HOURLY require Enterprise. These are exclusive — cannot combine with
  other schedules on the same dataset.
- WEEKLY needs `RefreshOnDay.DayOfWeek`. MONTHLY needs `DayOfMonth` (`"1"`-`"28"` or
  `"LAST_DAY_OF_MONTH"`).
- Maximum 5 schedules per dataset.

**Schedule refresh AFTER your data pipeline completes.** If pipelines finish at 08:00 UTC,
set SPICE refresh at 10:00 UTC to buffer for late runs.

List existing schedules with `list-refresh-schedules --data-set-id $DATASET_ID`.

## 8. Manual Ingestion

```bash
# Trigger
INGESTION_ID="manual-$(date +%s)-$DATASET_ID"
aws quicksight create-ingestion \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --data-set-id $DATASET_ID --ingestion-id "$INGESTION_ID"

# Poll (status: QUEUED -> RUNNING -> COMPLETED or FAILED/CANCELLED)
aws quicksight describe-ingestion \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --data-set-id $DATASET_ID --ingestion-id "$INGESTION_ID" \
  --query 'Ingestion.{Status:IngestionStatus,Rows:RowInfo.RowsIngested,Errors:ErrorInfo}'
```

**Rate limits:** Enterprise 32/day, Standard 8/day per dataset. Ingestion ID must be unique
within a dataset — always append a timestamp.

**Bulk refresh:**

```bash
for ds in $DATASET_ID_1 $DATASET_ID_2 $DATASET_ID_3; do
  aws quicksight create-ingestion --aws-account-id $ACCOUNT_ID --profile $PROFILE \
    --data-set-id "$ds" --ingestion-id "manual-$(date +%s)-$ds"
done
```

## 9. SPICE Troubleshooting

Check `describe-ingestion` for ErrorInfo.Type:

| Error Type                        | Cause                              | Fix                                                  |
|-----------------------------------|------------------------------------|------------------------------------------------------|
| SQL_SCHEMA_MISMATCH               | Source columns changed             | Update dataset definition, then re-ingest            |
| DATA_SET_SIZE_LIMIT_EXCEEDED      | SPICE capacity exhausted           | Purchase more capacity or filter data                |
| INGESTION_SUPERSEDED              | Another ingestion started          | Normal — newer ingestion takes over                  |
| FAILURE_TO_ASSUME_ROLE            | IAM role trust issue               | Check trust policy allows QuickSight                 |
| PERMISSION_DENIED                 | DB credentials wrong/revoked       | Update via `update-data-source`                      |
| SOURCE_API_LIMIT_EXCEEDED_FAILURE | Source rate-limited                | Stagger dataset refreshes                            |
| CONNECTION_FAILURE                | Cannot reach database              | Check VPC connection and security groups             |
| QUERY_TIMEOUT                     | Source query too slow              | Optimize SQL or add indexes                          |

**Schema change detection:** QuickSight does NOT auto-detect source schema changes. If you
modify columns in a view, update the dataset definition with `update-data-set` to match.

**Debugging:** Run `describe-ingestion` for ErrorInfo. For SQL_SCHEMA_MISMATCH, compare
`describe-data-set` InputColumns against actual DB schema, then `update-data-set`. For
unclear errors, check the QuickSight console — the UI often shows more detail than the API.

## 10. Row-Level Security

**Dataset-based RLS** — create a permissions dataset (columns: `user_name`, filter column)
mapping users to allowed values, then attach it:

```bash
aws quicksight update-data-set \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --data-set-id $DATASET_ID --name "My Dataset" \
  --import-mode SPICE --physical-table-map file://physical.json \
  --row-level-permission-data-set '{
    "Arn": "$RLS_DATASET_ARN",
    "PermissionPolicy": "GRANT_ACCESS",
    "FormatVersion": "VERSION_2"
  }'
```

**Tag-based RLS** (for embedding) — add `RowLevelPermissionTagConfiguration`. Tags pass at
runtime via embedding session tags. Use when RLS rules come from your application.

## 11. Column-Level Security

```bash
aws quicksight update-data-set \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --data-set-id $DATASET_ID --name "My Dataset" \
  --import-mode SPICE --physical-table-map file://physical.json \
  --column-level-permission-rules '[{
    "Principals": ["arn:aws:quicksight:$REGION:$ACCOUNT_ID:user/default/$RESTRICTED_USER"],
    "ColumnNames": ["customer_name", "status"]
  }]'
```

The rule lists columns the principal CAN see — all others are hidden. Omit a principal from
all rules for full column access. CLS with SPICE duplicates data per rule set — consider
DIRECT_QUERY for datasets with many CLS rules.

## 12. Quotas

| Resource                       | Limit    |
|--------------------------------|----------|
| SPICE capacity (Enterprise)    | 500 GB   |
| Datasets per analysis          | 50       |
| Columns per dataset            | 2,048    |
| Physical tables per dataset    | 32       |
| Logical tables per dataset     | 64       |
| Refresh schedules per dataset  | 5        |
| Manual refreshes/24h (Ent/Std) | 32 / 8   |
| CustomSql max length           | 168K chars |
| Calculated fields per dataset  | 500      |
| Datasets per account           | 2,500    |
| Data sources per account       | 2,500    |

SPICE capacity is shared across all datasets in the account and is regional. Purchase
additional capacity at $0.25/GB/month in 1 GB increments.
