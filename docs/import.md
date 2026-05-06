# Importing Environment Variables

envoy-cli supports importing `.env` variables from external files in multiple formats into the vault.

## Supported Formats

| Format   | Description                              | Example file        |
|----------|------------------------------------------|---------------------|
| `dotenv` | Standard `.env` key=value pairs (default)| `.env`, `.env.prod` |
| `json`   | Flat JSON object `{ "KEY": "value" }`    | `env.json`          |
| `shell`  | Shell `export KEY=value` lines           | `env.sh`            |

## Commands

### `envoy import run`

Import variables from a file directly into the vault.

```bash
envoy import run .env.production --project myapp --env production --password secret
```

**Options:**

- `--project / -p` — Target project name (required).
- `--env / -e` — Environment name (default: `default`).
- `--format / -f` — Source format: `dotenv`, `json`, or `shell` (default: `dotenv`).
- `--skip-existing` — Skip keys that already exist in the vault, preserving current values.
- `--password` — Vault encryption password (prompted if not provided).

### `envoy import preview`

Inspect what would be imported without writing anything to the vault.

```bash
envoy import preview env.json --format json
```

Output:

```
Would import 3 key(s) from 'env.json' [json]:
  API_KEY=s3cr3t
  DEBUG=false
  TIMEOUT=30
```

## Skip Existing Keys

Use `--skip-existing` to perform a non-destructive import. Keys already present in the vault will not be overwritten:

```bash
envoy import run .env.new --project api --env staging --skip-existing --password secret
# Imported 2 key(s) into api/staging (skipped 4).
```

## Format Examples

### dotenv
```env
DB_HOST=localhost
DB_PORT=5432
# comment
SECRET_KEY="my secret"
```

### json
```json
{
  "DB_HOST": "localhost",
  "DB_PORT": "5432"
}
```

### shell
```bash
export DB_HOST=localhost
export DB_PORT=5432
```
