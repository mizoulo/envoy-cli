# Envoy Search

The `search` command group lets you grep across all `.env` files stored in a vault project without having to pull them individually.

## Commands

### `envoy search grep PATTERN`

Search for a regular expression pattern across every environment in a project.

```bash
envoy search grep DB_HOST --project myapp
```

**Options:**

| Flag | Description |
|------|-------------|
| `--project, -p` | *(required)* Project name to search within |
| `--keys-only` | Match against variable names only, ignoring values |
| `--ignore-case, -i` | Case-insensitive matching |
| `--password` | Decryption password (or set `ENVOY_PASSWORD`) |

**Example output:**

```
myapp/production:1: DB_HOST=prod.db
myapp/staging:1: DB_HOST=staging.db

2 match(es) for 'DB_HOST'.
```

### `envoy search list-keys`

List every key defined in a specific environment file.

```bash
envoy search list-keys --project myapp --env production
```

Comments and blank lines are automatically ignored.

**Options:**

| Flag | Description |
|------|-------------|
| `--project, -p` | *(required)* Project name |
| `--env, -e` | *(required)* Environment name |
| `--password` | Decryption password (or set `ENVOY_PASSWORD`) |

## Tips

- Use `--keys-only` to audit which projects define a particular variable without exposing its value.
- Combine with shell tools: `envoy search grep SECRET --project myapp | wc -l`
- Set `ENVOY_PASSWORD` in your shell session to avoid repeated prompts.
