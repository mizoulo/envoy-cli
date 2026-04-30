# envoy watch

The `watch` command monitors `.env` files for changes and automatically pushes
updates to the vault, keeping your remote storage in sync without manual
intervention.

## Usage

```bash
# Start watching a file and auto-push on change
envoy watch start .env --project myapp --env production

# Use a custom poll interval (seconds)
envoy watch start .env -p myapp -e staging --interval 5

# Preview changes without pushing (dry-run)
envoy watch start .env -p myapp -e dev --dry-run

# List configured watch targets
envoy watch list
```

## How it works

`EnvWatcher` polls registered files at a configurable interval (default: 1 s).
It computes a SHA-256 hash of each file's contents on every tick. When the hash
changes, a `WatchEvent` is emitted and all registered callbacks are invoked.

The CLI callback calls `SyncEngine.push_file` so the updated file is encrypted
and stored in the vault immediately.

## Options

| Option | Default | Description |
|---|---|---|
| `--project`, `-p` | *(required)* | Project name in the vault |
| `--env`, `-e` | *(required)* | Environment label (e.g. `production`) |
| `--vault-dir` | `.envoy` | Path to local vault directory |
| `--interval` | `2.0` | Poll interval in seconds |
| `--dry-run` | off | Log changes without pushing |

## Programmatic use

```python
from pathlib import Path
from envoy.watch import EnvWatcher

watcher = EnvWatcher(interval=1.0)
watcher.add(Path(".env"), project="myapp", env_name="dev")
watcher.on_change(lambda ev: print(f"Changed: {ev}"))
watcher.run()  # blocks; Ctrl-C to stop
```

## Stopping

Press **Ctrl-C** to stop the watcher gracefully.
