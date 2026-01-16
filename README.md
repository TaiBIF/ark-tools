# ark-tools

ARK resolver and minter for pid.biodiv.tw

Inspired from [internetarchive/arklet](https://github.com/internetarchive/arklet) and [jkunze/docker-noid](https://github.com/jkunze/docker-noid)

## What is an ARK?

ARK (Archival Resource Key) is a persistent identifier scheme. See https://arks.org/

## Features

- ARK resolver with shoulder-based redirect
- ARK minter with NOID template support
- NOID check digit validation (NCDA algorithm)
- API authentication
- CLI commands for NOID validation

## Dependencies

- Flask
- SQLite3
- Gunicorn (production)
- Docker

## Development

```bash
cp dotenv.sample .env
docker compose up
```

## Production Deployment

```bash
docker compose -f compose.yml -f compose.prod.yml up -d
```

Logs are stored at:
- Nginx: `../arktools-volumes/logs/nginx/`
- Gunicorn: `../arktools-volumes/logs/gunicorn/`

## API

### Resolver

```
GET /ark:/{naan}/{assigned_name}
```

Resolves ARK to target URL. Supports suffix passthrough.

Example:
```
GET /ark:/18474/b24x54g1g
→ Redirects to configured URL
```

### Minter

```
POST /api/mint
Header: X-API-Key: <your-api-key>
Content-Type: application/json
```

Request body:
```json
{
  "naan": 18474,
  "shoulder": "b2",
  "url": "https://example.com/resource/123",
  "who": "optional creator",
  "what": "optional description",
  "when": "optional date"
}
```

Response:
```json
{
  "ark": "ark:/18474/b2x7k9m2p",
  "identifier": "18474/b2x7k9m2p",
  "url": "https://example.com/resource/123"
}
```

## NOID Templates

Templates follow the [NOID specification](https://metacpan.org/dist/Noid/view/noid#TEMPLATES).

Format: `prefix.mask`

### Generator types (first char of mask)

| Char | Description |
|------|-------------|
| `r` | Random |
| `s` | Sequential (bounded) |
| `z` | Sequential (unlimited) |

### Mask characters

| Char | Description | Characters |
|------|-------------|------------|
| `d` | Digit | `0123456789` (10) |
| `e` | Extended | `0123456789bcdfghjkmnpqrstvwxz` (29) |
| `k` | Check digit | Computed, must be last |

### Example templates

| Template | Output | Description |
|----------|--------|-------------|
| `.reedeedk` | `b2x7k9m2p` | 6 random + check (default) |
| `.reeeeee` | `x7k9m2pq` | 7 random, no check |
| `.rddddd` | `38472` | 5 random digits |

### Check digit algorithm (NCDA)

The check digit is calculated on the full ARK: `{naan}/{shoulder}{random_part}`

```
base = "18474/b24x54g1"
sum = Σ(position × char_index)
check = EXTENDED[sum % 29]
```

Example:
```
Position: 1  2  3  4  5  6  7  8  9  10 11 12 13 14
Char:     1  8  4  7  4  /  b  2  4  x  5  4  g  1
Index:    1  8  4  7  4  -  10 2  4  27 5  4  14 1
Contrib:  1  16 12 28 20 -  70 16 36 270 55 48 182 14

Sum = 768
Check = 768 % 29 = 14
EXTENDED[14] = 'g'
```

## CLI Commands

### Check NOID validity

```bash
# Check single ARK
flask noid-check -a "18474/b24x54g1g"

# Check all ARKs for a shoulder
flask noid-check -s b2 --limit 100

# Show only invalid ARKs
flask noid-check -s b2 --show-invalid

# Verbose output
flask noid-check -s b2 --verbose
```

### Generate sample NOIDs

```bash
flask noid-generate -n 18474 -s b2 -t ".reedeedk" -c 5
```

## Database Schema

### Tables

**ark** - ARK identifiers
- `identifier` (PK): `{naan}/{assigned_name}`
- `naan`: NAAN number
- `assigned_name`: Name without shoulder
- `shoulder`: Shoulder prefix
- `url`: Target redirect URL
- `who`, `what`, `when`: Metadata

**naan** - Name Assigning Authority Numbers
- `naan` (PK): NAAN number
- `name`, `description`, `url`

**shoulder** - Shoulder prefixes
- `shoulder` (PK): Shoulder string
- `naan`: Associated NAAN
- `name`, `description`
- `redirect_prefix`: For shoulder-level redirects
- `template`: NOID template (e.g., `.reedeedk`)

## Configuration

Environment variables (`.env`):

```
WEB_ENV=prod
SECRET_KEY=your-secret-key
MINTER_API_KEY=your-api-key
```

## License

MIT
