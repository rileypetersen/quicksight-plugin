---
name: deployment
description: Deploy, migrate, and publish AWS QuickSight dashboards and analyses. Use when asked to deploy a dashboard, migrate QuickSight across accounts, export or import asset bundles, set up CI/CD for QuickSight, publish a dashboard from an analysis, create templates, promote to production, set up scheduled email reports, or manage dashboard versioning. Also use for cross-account migration, rollback, or template alias management.
---

# QuickSight Deployment

## Dashboard Publishing

Publish an analysis as a read-only dashboard. Analyses are the authoring surface; dashboards are the consumption surface. Users without Author seats can only view dashboards, not analyses.

### Template-based approach (recommended for reuse)

Create a template from the analysis first, then publish a dashboard from that template. This decouples the dashboard from the analysis, allowing multiple dashboards from one template and cross-account sharing.

```bash
aws quicksight create-dashboard \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --dashboard-id $DASHBOARD_ID \
  --name "My Dashboard" \
  --source-entity '{
    "SourceTemplate": {
      "Arn": "arn:aws:quicksight:$REGION:$ACCOUNT_ID:template/$TEMPLATE_ID",
      "DataSetReferences": [
        {"DataSetPlaceholder": "my_dataset", "DataSetArn": "arn:aws:quicksight:$REGION:$ACCOUNT_ID:dataset/$DATASET_ID"}
      ]
    }
  }'
```

### Definition-based approach (direct from analysis)

Skip the template and push a JSON definition directly. Useful when version-controlling the analysis definition in code (e.g., a Python build script).

```bash
aws quicksight create-dashboard \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --dashboard-id $DASHBOARD_ID \
  --name "My Dashboard" \
  --definition file://dashboard-definition.json
```

### Promote a draft to published

`create-dashboard` and `update-dashboard` create draft versions. Users see the last *published* version until you promote the draft explicitly.

```bash
aws quicksight update-dashboard-published-version \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --dashboard-id $DASHBOARD_ID \
  --version-number $VERSION_NUMBER
```

Get the latest version number from `describe-dashboard` response under `Version.VersionNumber`.

## Asset Bundle Export/Import

Prefer asset bundles over templates for cross-account migration. Bundles capture the full dependency graph (data sources, datasets, analyses, dashboards) in a single portable file, eliminating the need to manually recreate each resource.

### Export (async operation)

```bash
aws quicksight start-asset-bundle-export-job \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --asset-bundle-export-job-id "export-$(date +%s)" \
  --resource-arns '["arn:aws:quicksight:$REGION:$ACCOUNT_ID:dashboard/$DASHBOARD_ID"]' \
  --include-all-dependencies \
  --export-format QUICKSIGHT_JSON
```

Use `--include-all-dependencies` to pull in datasets and data sources automatically. Without it, only the dashboard shell exports and the import fails on missing references.

### Poll for completion

```bash
aws quicksight describe-asset-bundle-export-job \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --asset-bundle-export-job-id $EXPORT_JOB_ID \
  --query '{Status:JobStatus,URL:DownloadUrl}'
```

Poll every 10-15 seconds. Status transitions: `QUEUED_FOR_IMMEDIATE_EXECUTION` -> `IN_PROGRESS` -> `SUCCESSFUL` or `FAILED`. Download the bundle immediately when successful -- the URL expires in 5 minutes.

```bash
curl -o export.qs "$DOWNLOAD_URL"
```

### Import into target account

```bash
aws quicksight start-asset-bundle-import-job \
  --aws-account-id $TARGET_ACCOUNT_ID --profile $TARGET_PROFILE \
  --asset-bundle-import-job-id "import-$(date +%s)" \
  --asset-bundle-import-source '{"Body": "fileb://export.qs"}' \
  --failure-action ROLLBACK \
  --override-parameters '{
    "DataSources": [{
      "DataSourceId": "$SOURCE_DS_ID",
      "DataSourceParameters": {
        "AuroraPostgreSqlParameters": {
          "Host": "$TARGET_DB_HOST",
          "Port": 5432,
          "Database": "$TARGET_DB_NAME"
        }
      },
      "Credentials": {
        "CredentialPair": {
          "Username": "$TARGET_DB_USER",
          "Password": "$TARGET_DB_PASS"
        }
      }
    }]
  }'
```

Use `fileb://` (not `file://`) for binary `.qs` bundles. The `b` suffix tells the AWS CLI to send the file as raw bytes rather than UTF-8 text, which corrupts the bundle. For files larger than 20 MB, upload to S3 first and use `S3Uri` instead of `Body`.

Set `--failure-action ROLLBACK` so a partial import does not leave orphaned resources in the target account.

### Poll import status

```bash
aws quicksight describe-asset-bundle-import-job \
  --aws-account-id $TARGET_ACCOUNT_ID --profile $TARGET_PROFILE \
  --asset-bundle-import-job-id $IMPORT_JOB_ID \
  --query '{Status:JobStatus,Errors:Errors}'
```

Check `Errors` even on `SUCCESSFUL_WITH_WARNINGS` -- warnings often indicate silently skipped resources like themes or refresh schedules.

## What Transfers and What Doesn't

| Transfers | Does NOT Transfer |
|---|---|
| Analysis/dashboard definitions | Permissions (account-specific user ARNs) |
| Dataset configurations | Refresh schedules |
| Data source connection settings | SPICE data (must re-ingest) |
| Folder structure | Theme customizations (export separately) |
| Calculated fields and parameters | Alert subscriptions |
| Filter controls and actions | Scheduled email reports |

Always re-apply permissions, recreate refresh schedules, and trigger SPICE ingestion after import. These are account-specific settings that reference local user ARNs and infrastructure, so they cannot be ported automatically.

## Template-Based Promotion

Templates remain useful when deploying the same dashboard layout to multiple accounts with different data sources. Each consumer account provides its own dataset ARNs at dashboard-creation time.

### Create template from analysis

```bash
aws quicksight create-template \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --template-id $TEMPLATE_ID \
  --name "My Template v1" \
  --source-entity '{
    "SourceAnalysis": {
      "Arn": "arn:aws:quicksight:$REGION:$ACCOUNT_ID:analysis/$ANALYSIS_ID",
      "DataSetReferences": [
        {"DataSetPlaceholder": "my_dataset", "DataSetArn": "arn:aws:quicksight:$REGION:$ACCOUNT_ID:dataset/$DATASET_ID"}
      ]
    }
  }'
```

Each `create-template` or `update-template` call creates a new version number. QuickSight retains all versions indefinitely.

### Template aliases for version management

Aliases decouple consumers from version numbers. Point `PROD` at a tested version and `STAGING` at the latest. Consumers reference the alias ARN, so promoting a new version is a single alias update with no downstream changes.

```bash
# Create PROD alias pointing to version 1
aws quicksight create-template-alias \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --template-id $TEMPLATE_ID \
  --alias-name "PROD" \
  --template-version-number 1

# Promote version 2 to production
aws quicksight update-template-alias \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --template-id $TEMPLATE_ID \
  --alias-name "PROD" \
  --template-version-number 2
```

### Cross-account template sharing

Grant the target account permission to use the template, then create a dashboard in that account referencing the template ARN.

```bash
aws quicksight update-template-permissions \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --template-id $TEMPLATE_ID \
  --grant-permissions '[{
    "Principal": "arn:aws:iam::$TARGET_ACCOUNT_ID:root",
    "Actions": ["quicksight:DescribeTemplate"]
  }]'
```

## CI/CD Pattern

Version-control the analysis definition as a Python build script. On merge to main, rebuild the definition JSON and push it to QuickSight. This gives you git history, code review, and rollback via revert.

```yaml
name: Deploy QuickSight
on:
  push:
    branches: [main]
    paths: ['scripts/build_analysis.py']

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::$ACCOUNT_ID:role/QuickSightDeployRole
          aws-region: $REGION

      - name: Validate definition
        run: python3 scripts/build_analysis.py --dry-run

      - name: Push to QuickSight
        run: python3 scripts/build_analysis.py --push

      - name: Refresh SPICE datasets
        run: |
          for ds in $DATASET_ID_1 $DATASET_ID_2; do
            aws quicksight create-ingestion \
              --aws-account-id $ACCOUNT_ID \
              --data-set-id "$ds" \
              --ingestion-id "ci-$(date +%s)-$ds"
          done
```

Use `--dry-run` as a validation gate before pushing. The build script should exit non-zero if the definition JSON fails schema validation, catching errors before they reach QuickSight.

The IAM role needs: `quicksight:UpdateAnalysis`, `quicksight:DescribeAnalysis`, `quicksight:CreateIngestion`, and `quicksight:DescribeIngestion`.

## Cross-Account Considerations

Data source ARNs embed the account ID and region, so they differ between accounts. Always provide `--override-parameters` during asset bundle import to remap data sources to the target account's infrastructure.

Credential pairs must be provided explicitly for each data source in the target account. QuickSight never exports credentials -- this is a security feature, not a bug.

Permissions reference account-specific QuickSight user ARNs (`arn:aws:quicksight:$REGION:$ACCOUNT_ID:user/default/$USER`). Re-apply them after import using `update-dashboard-permissions` or `update-analysis-permissions`.

SPICE data is not portable. After import, trigger a full ingestion for every SPICE dataset. Direct Query datasets work immediately once the data source credentials are valid.

## Rollback Strategies

Three approaches, from fastest to most thorough:

1. **Template alias rollback** -- point the alias back to the previous version number. Takes effect immediately for all dashboards referencing the alias. No data re-ingestion needed.

```bash
aws quicksight update-template-alias \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --template-id $TEMPLATE_ID \
  --alias-name "PROD" \
  --template-version-number $PREVIOUS_VERSION
```

2. **Asset bundle re-import** -- re-import a previously exported bundle file. Restores the full resource graph to a known-good state. Keep timestamped exports in S3 for this purpose.

3. **Git revert** -- revert the build script commit and re-run CI/CD. Slowest but most auditable. Produces a clear git history of what changed and when it was rolled back.

## Scheduled Email Reports

Deliver dashboard snapshots to stakeholders on a recurring schedule. Recipients do not need QuickSight accounts -- reports arrive as PDF attachments.

```bash
aws quicksight create-schedule \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --schedule-id "weekly-exec-report" \
  --dashboard-id $DASHBOARD_ID \
  --schedule '{
    "StartTime": "2024-01-01T08:00:00Z",
    "ScheduleFrequency": {
      "Interval": "WEEKLY",
      "DayOfWeek": "MONDAY"
    }
  }' \
  --email-destination '{"ToAddresses": ["team@example.com"]}'
```

Schedules do not transfer across accounts via asset bundles. Recreate them after migration. The dashboard must be published (not in draft state) for the schedule to execute.
