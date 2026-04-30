# Env Templates

envoy supports `.env` template files that use `{{ VARIABLE }}` placeholders. This lets you define a canonical structure for your environment configuration and render it with project-specific values.

## Template Syntax

Placeholders use double-curly-brace syntax:

```
DB_HOST={{ DB_HOST }}
DB_PORT={{ DB_PORT }}
SECRET_KEY={{ SECRET_KEY }}
```

Whitespace inside the braces is ignored: `{{ FOO }}` and `{{FOO}}` are equivalent.

## Commands

### `envoy template render`

Render a template file by substituting placeholders.

```bash
# Supply values inline
envoy template render template.env -v DB_HOST=localhost -v DB_PORT=5432

# Write output to a file
envoy template render template.env -o .env -v DB_HOST=localhost

# Load values from an existing .env file
envoy template render template.env --env-file base.env -o .env
```

If any placeholders remain unresolved a warning is printed to stderr but the command still succeeds so you can inspect partial output.

### `envoy template inspect`

List all placeholders found in a template without rendering it:

```bash
envoy template inspect template.env
# Found 3 placeholder(s):
#   - DB_HOST
#   - DB_PORT
#   - SECRET_KEY
```

## Workflow Example

1. Commit `template.env` to version control (no secrets).
2. Each developer or CI job runs `envoy template render` with their own values.
3. The generated `.env` is kept out of version control via `.gitignore`.

## Integration with Vault

You can combine templates with `envoy push`/`envoy pull` to distribute rendered files securely:

```bash
envoy template render template.env --env-file secrets.env -o .env
envoy push .env myproject production
```
