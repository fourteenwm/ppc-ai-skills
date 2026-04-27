# Google Ads Resources

Mapping of short names to GAQL query templates.

## Resource Types

| Short Name | GAQL File | Description | Default Sort |
|------------|-----------|-------------|--------------|
| `search-terms` | `search-terms.gaql` | Search query report | cost DESC |
| `campaigns` | `campaigns.gaql` | Campaign performance | cost DESC |
| `keywords` | `keywords.gaql` | Keyword performance | cost DESC |
| `ad-groups` | `ad-groups.gaql` | Ad group performance | cost DESC |
| `conversions` | `conversions.gaql` | Conversion actions | conversions DESC |
| `budgets` | `budgets.gaql` | Budget utilization | spend DESC |
| `assets` | `assets.gaql` | Asset performance (PMAX) | cost DESC |
| `geo` | `geo.gaql` | Geographic performance | cost DESC |

## Aliases

Some resources have aliases for fuzzy matching:

- `search-terms`: `search`, `queries`, `sq`, `sqr`
- `campaigns`: `campaign`, `camps`
- `keywords`: `keyword`, `kw`
- `ad-groups`: `adgroups`, `ad-group`, `adgroup`, `ag`
- `conversions`: `conversion`, `conv`
- `budgets`: `budget`
- `assets`: `asset`
- `geo`: `geography`, `location`, `locations`

## Usage

The query script accepts these short names:

```bash
python query.py --resource search-terms
python query.py --resource campaigns
python query.py --resource keywords
```

## Adding New Resources

1. Create `references/{resource}.gaql` with GAQL template
2. Add entry to this file
3. Use `{DATE_RANGE}` placeholder for date filtering

## Template Format

Templates use `{DATE_RANGE}` as a placeholder:

```sql
SELECT ...
FROM ...
WHERE segments.date {DATE_RANGE}
ORDER BY metrics.cost_micros DESC
```

The query script replaces `{DATE_RANGE}` with:
```sql
BETWEEN '2026-01-01' AND '2026-01-09'
```
