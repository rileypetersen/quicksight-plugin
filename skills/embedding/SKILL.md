---
name: embedding
description: Embed AWS QuickSight dashboards and visuals in web applications. Use when asked to embed a QuickSight dashboard, add QuickSight to a web app, set up anonymous or registered embedding, configure the QuickSight embedding SDK, use session tags for multi-tenant RLS, embed in React/Next.js/Vue, or generate embed URLs. Also use when encountering CORS errors, expired embed URLs, UnsupportedPricingPlanException, or session capacity issues. Note - CORS errors in QuickSight embedding are usually NOT actual CORS issues.
---

# QuickSight Embedding

## Registered vs Anonymous Embedding

Choose based on who sees the dashboard. Internal tools where users already have QuickSight seats should use registered embedding. Customer-facing products where end users should never know QuickSight exists should use anonymous embedding.

| Factor | Registered | Anonymous |
|---|---|---|
| Auth | QuickSight user required | No user needed |
| Pricing | Per-user license | Session capacity (Enterprise) |
| RLS | User/group based | Session tag based |
| Setup | Simpler (fewer steps) | More steps (namespace, capacity) |
| Use case | Internal tools, admin panels | Customer-facing SaaS, portals |
| Features | Bookmarks, state persistence, alerts | Viewing and filtering only |
| Cost model | Predictable per-seat | Pay-per-session, scales with traffic |

Registered embedding is simpler but creates a scaling problem: every viewer needs a QuickSight user. Anonymous embedding avoids this by using session capacity pricing, where you pay for concurrent sessions rather than named users.

## Anonymous Embedding Flow

Follow these steps in order. Skipping any step produces opaque errors (usually misreported as CORS failures).

### 1. Enable session capacity pricing

Open the QuickSight admin console and switch to Enterprise Edition with session capacity. This is a one-time account-level change. Without it, every anonymous embed call returns `UnsupportedPricingPlanException`.

### 2. Verify namespace exists

Anonymous embedding requires a namespace. Most accounts have `default` already.

```bash
aws quicksight list-namespaces --aws-account-id $ACCOUNT_ID --profile $PROFILE
```

If missing, create one:

```bash
aws quicksight create-namespace \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --namespace default \
  --identity-store QUICKSIGHT
```

### 3. Create IAM role for embed URL generation

The backend service assumes this role to generate embed URLs. Scope the policy tightly to prevent URL generation for unauthorized dashboards.

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "quicksight:GenerateEmbedUrlForAnonymousUser",
    "Resource": "arn:aws:quicksight:$REGION:$ACCOUNT_ID:dashboard/$DASHBOARD_ID",
    "Condition": {
      "ForAllValues:StringEquals": {
        "quicksight:AllowedEmbeddingDomains": [
          "https://app.example.com",
          "https://*.example.com"
        ]
      }
    }
  }]
}
```

The `AllowedEmbeddingDomains` condition restricts which origins can render the embedded dashboard. Wildcards apply to subdomains only. Omitting this condition lets any domain embed if they obtain a URL.

### 4. Add allowed domains

Register domains in the QuickSight console under Manage QuickSight > Domains and Embedding, or pass them in the API call via `--allowed-domains`. Both approaches work; the API parameter is additive to the console list.

### 5. Configure RLS on datasets (if multi-tenant)

See the Session Tags section below. Skip this step for single-tenant dashboards.

### 6. Publish dashboard

Anonymous embedding requires a published dashboard. Analyses and draft dashboard versions cannot be embedded.

### 7. Generate embed URL (backend)

```bash
aws quicksight generate-embed-url-for-anonymous-user \
  --aws-account-id $ACCOUNT_ID \
  --namespace default \
  --authorized-resource-arns '["arn:aws:quicksight:$REGION:$ACCOUNT_ID:dashboard/$DASHBOARD_ID"]' \
  --experience-configuration '{"Dashboard": {"InitialDashboardId": "$DASHBOARD_ID"}}' \
  --session-tags '[{"Key": "tenant_id", "Value": "customer-123"}]' \
  --session-lifetime-in-minutes 600 \
  --allowed-domains '["https://app.example.com"]'
```

### 8. Return EmbedUrl to frontend

The URL is valid for 5 minutes and single-use. Generate a fresh URL on every page load. Never cache or reuse embed URLs -- once consumed by the SDK, the URL is permanently invalidated.

### 9. Initialize SDK and render

See the JavaScript SDK section below.

### 10. Handle events

Listen for `CONTENT_LOADED` (dashboard ready), `ERROR_OCCURRED` (embed failed), and `SIZE_CHANGED` (for responsive layouts). Always handle `ERROR_OCCURRED` -- silent failures frustrate users.

## Session Tags for Multi-Tenant RLS

Session tags filter dashboard data at the row level without maintaining per-user RLS rules. The backend injects the tenant's identity as a tag, and QuickSight automatically filters every dataset to matching rows.

### Configure RLS tag rules on the dataset

```bash
aws quicksight update-data-set \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --data-set-id $DATASET_ID \
  --row-level-permission-tag-configuration '{
    "Status": "ENABLED",
    "TagRules": [{
      "TagKey": "tenant_id",
      "ColumnName": "organization_id",
      "TagMultiValueDelimiter": ",",
      "MatchAllValue": "*"
    }]
  }' \
  # ... include other required dataset parameters
```

`TagKey` is the name you pass at embed time. `ColumnName` is the actual column in the dataset to filter on. These intentionally differ to decouple the API contract from the schema.

### Pass tags at embed time

```json
"SessionTags": [
  {"Key": "tenant_id", "Value": "org-123,org-456"}
]
```

### Tag logic

- **Multiple tags** = AND (all must match). Use for orthogonal dimensions like tenant + region.
- **Comma-separated values within a tag** = OR (any can match). Use when a user belongs to multiple orgs.
- **MatchAllValue ("*")** = bypass filtering entirely. Use for admin/super-user views.

### Security

Session tags are credentials. Set them exclusively from the trusted backend based on authenticated user identity. Never accept tag values from client-side input -- a user could pass `"*"` as the tenant_id and see all data.

## Registered User Embedding

Simpler setup because the QuickSight user already has permissions. No namespace or session capacity needed.

```bash
aws quicksight generate-embed-url-for-registered-user \
  --aws-account-id $ACCOUNT_ID \
  --user-arn "arn:aws:quicksight:$REGION:$ACCOUNT_ID:user/default/$USER" \
  --experience-configuration '{
    "Dashboard": {
      "InitialDashboardId": "$DASHBOARD_ID",
      "FeatureConfigurations": {
        "Bookmarks": {"Enabled": true},
        "StatePersistence": {"Enabled": true}
      }
    }
  }'
```

Enable `StatePersistence` for internal tools -- it remembers each user's filter selections across sessions, reducing repetitive setup. `Bookmarks` let users save and share specific dashboard views.

The user ARN must match an existing QuickSight user. Verify with:

```bash
aws quicksight describe-user \
  --aws-account-id $ACCOUNT_ID --profile $PROFILE \
  --namespace default \
  --user-name $USER
```

## JavaScript SDK

### Install

```bash
npm install amazon-quicksight-embedding-sdk
```

### Embed a dashboard

```javascript
import { createEmbeddingContext } from 'amazon-quicksight-embedding-sdk';

// Create context once per page. This spawns a hidden iframe
// for cross-frame communication with the QuickSight renderer.
const context = await createEmbeddingContext();

// Embed the dashboard into a container element.
const dashboard = await context.embedDashboard(
  {
    url: embedUrl,           // from backend API -- must be fresh (<5 min old)
    container: '#dashboard', // CSS selector or HTMLElement
    height: '700px',
    width: '100%',
  },
  {
    locale: 'en-US',
    sheetOptions: {
      initialSheetId: 'my-sheet',  // optional: open a specific tab
    },
    toolbarOptions: {
      export: true,      // allow PDF/CSV export
      undoRedo: false,    // hide undo/redo buttons
      reset: true,        // show "reset to default" button
    },
    onMessage: (event, metadata) => {
      if (event.eventName === 'CONTENT_LOADED') {
        console.log('Dashboard loaded:', event.message.title);
      }
      if (event.eventName === 'ERROR_OCCURRED') {
        console.error('Embed error:', event.message.errorCode);
      }
    },
  }
);

// Set parameters programmatically after load.
// Useful for syncing dashboard filters with your app's state.
await dashboard.setParameters([
  { Name: 'Region', Values: ['West'] }
]);

// Query available sheets for building a custom tab bar.
const sheets = await dashboard.getSheets();
```

### Embed a single visual

Use `embedVisual` instead of `embedDashboard` when integrating individual charts into existing page layouts rather than showing a full dashboard.

```javascript
const visual = await context.embedVisual(
  {
    url: embedUrl,
    container: '#chart',
    height: '400px',
  },
  {
    onMessage: (event) => { /* handle events */ },
  }
);
```

Generate the URL with `--experience-configuration '{"DashboardVisual": {"InitialDashboardVisualId": {"DashboardId": "$DASHBOARD_ID", "SheetId": "$SHEET_ID", "VisualId": "$VISUAL_ID"}}}'`.

## React Integration

```jsx
import { useEffect, useRef } from 'react';
import { createEmbeddingContext } from 'amazon-quicksight-embedding-sdk';

function QuickSightDashboard({ embedUrl }) {
  const containerRef = useRef(null);
  const dashboardRef = useRef(null);

  useEffect(() => {
    if (!embedUrl) return;

    const embed = async () => {
      const context = await createEmbeddingContext();
      dashboardRef.current = await context.embedDashboard(
        {
          url: embedUrl,
          container: containerRef.current,
          height: '700px',
          width: '100%',
        },
        {
          onMessage: (event) => {
            if (event.eventName === 'ERROR_OCCURRED') {
              console.error('QuickSight embed error:', event.message);
            }
          },
        }
      );
    };
    embed();

    // SDK manages iframe cleanup internally.
  }, [embedUrl]);

  return <div ref={containerRef} />;
}
```

Put the embed URL fetch in a server component or API route. The `generate-embed-url` call requires IAM credentials that must never reach the browser. In Next.js, use a Route Handler (`app/api/embed/route.ts`) to generate the URL and return it to the client component.

## Debugging Embed Failures

"CORS error" in QuickSight embedding is almost never an actual CORS issue. The browser reports CORS when the iframe refuses to load for any reason, because the browser cannot distinguish "server rejected the request" from "server blocked cross-origin access." Investigate the actual cause before adding CORS headers.

| Browser Shows | Actual Cause | Fix |
|---|---|---|
| CORS error | Domain not in allowed list | Add domain in QuickSight console or `--allowed-domains` |
| CORS error | Embed URL expired (>5 min) | Generate a fresh URL on each page load |
| CORS error | Wrong embed mode | Anonymous mode requires session capacity pricing |
| CORS error | Session capacity exhausted | Purchase more capacity or reduce session lifetime |
| CORS error | IP restrictions blocking browser | Check `UpdateIpRestriction` settings |
| CORS error | CSP headers on your app | Add `*.quicksight.$REGION.amazonaws.com` to `frame-src` directive |
| Access denied | Missing IAM permission | Add `GenerateEmbedUrlFor*` to the backend role |
| Blank iframe | Dashboard not shared with user | Grant permissions via `update-dashboard-permissions` |
| Blank iframe | Dashboard in draft state | Publish via `update-dashboard-published-version` |

### Diagnosis steps

1. Open browser DevTools Network tab. Look for the actual HTTP status code on the iframe request.
2. Check CloudTrail for `GenerateEmbedUrlForAnonymousUser` events -- the error message is in the trail even when the browser shows a generic CORS error.
3. Verify the embed URL has not expired by checking the timestamp in the URL query string.
4. Test with `--allowed-domains '["http://localhost:3000"]'` during development.

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `UnsupportedPricingPlanException` | Session capacity not enabled | Enable in QuickSight admin console |
| `UnsupportedUserEditionException` | Not Enterprise Edition | Upgrade from Standard to Enterprise |
| `QuickSightUserNotFoundException` | User ARN invalid or user deleted | Verify user exists via `describe-user` |
| `ResourceNotFoundException` | Dashboard ID wrong or no access | Verify ARN; check `describe-dashboard` |
| `SessionLifetimeInMinutesInvalidException` | Value outside allowed range | Use a value between 15 and 600 |
| `InvalidParameterValueException` on domains | Malformed domain (missing protocol) | Use full origin: `https://app.example.com` |
| `AccessDeniedException` | IAM role lacks permission | Add the specific `GenerateEmbedUrl*` action |

## Quotas and Limits

| Constraint | Limit | Notes |
|---|---|---|
| Embed URL validity | 5 minutes | Single-use; generate fresh on each load |
| Session lifetime | 15-600 minutes | Default 600; shorter values free capacity faster |
| AllowedDomains per API call | 3 | Additive to console-registered domains |
| SessionTags per call | 50 | Each tag key max 128 chars, value max 256 chars |
| AuthorizedResourceArns per call | 25 | List all dashboards the session can navigate to |
| RLS tag rules per dataset | 50 | Across all tag keys on that dataset |
| Concurrent anonymous sessions | Based on purchased capacity | Monitor via CloudWatch `ActiveAnonymousSessions` |

Session capacity is regional. If you embed in `us-east-1` but purchased capacity in `us-west-2`, anonymous embedding fails silently with a CORS-like error.
