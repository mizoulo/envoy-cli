# Envoy Hooks

Envoy supports shell hooks that run automatically at key points in the
`push` / `pull` lifecycle. Hooks let you validate secrets, notify services,
or run any custom logic around env-file operations.

## Hook directory

Place executable scripts in `.envoy/hooks/` inside your project root:

```
.envoy/
  hooks/
    pre-push
    post-push
    pre-pull
    post-pull
```

Each file must be executable (`chmod +x .envoy/hooks/pre-push`).

## Supported events

| Event       | When it runs                          |
|-------------|---------------------------------------|
| `pre-push`  | Before an env file is uploaded        |
| `post-push` | After a successful upload             |
| `pre-pull`  | Before an env file is downloaded      |
| `post-pull` | After a successful download           |

## Exit codes

- **0** — hook succeeded; envoy continues normally.
- **non-zero** — hook failed; envoy aborts the operation and prints the
  hook's stderr output.

## Example: lint env file before pushing

```sh
#!/bin/sh
# .envoy/hooks/pre-push
if grep -q 'SECRET=changeme' .env; then
  echo "ERROR: default secret detected in .env" >&2
  exit 1
fi
```

## Listing installed hooks

```bash
envoy hooks list
```

This prints each installed hook name, one per line.

## Programmatic usage

```python
from pathlib import Path
from envoy.hooks import HookRunner

runner = HookRunner(Path(".envoy/hooks"))
result = runner.run("pre-push")
if result and not result.success:
    raise SystemExit(f"Hook failed: {result.stderr}")
```
