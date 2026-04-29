# Envoy Snapshots

Snapshots let you capture a point-in-time copy of a `.env` file and restore it later. They are stored in the same encrypted vault as your regular env files.

## Capturing a Snapshot

```bash
envoy snapshot capture <project> <env_name> <file> [--label <label>]
```

**Example:**
```bash
envoy snapshot capture myapp prod .env --label before-deploy
```

This stores the contents of `.env` under:
```
myapp/prod/snapshots/<timestamp>[_<label>]
```

## Listing Snapshots

```bash
envoy snapshot list <project> <env_name>
```

**Example:**
```bash
envoy snapshot list myapp prod
# myapp/prod/snapshots/1700000000_before-deploy
# myapp/prod/snapshots/1700001234
```

## Restoring a Snapshot

```bash
envoy snapshot restore <project> <env_name> <timestamp> [--label <label>] [--output <file>]
```

**Example:**
```bash
envoy snapshot restore myapp prod 1700000000 --label before-deploy --output .env
```

The `--output` flag defaults to `.env` in the current directory.

## Python API

```python
from envoy.snapshot import SnapshotManager
from envoy.vault import Vault
from envoy.storage import LocalStorage

storage = LocalStorage(".envoy_vault", password="my-secret")
vault = Vault(storage)
manager = SnapshotManager(vault, project="myapp")

# Capture
snap = manager.capture("prod", open(".env").read(), label="v2")
print(snap.snapshot_key)

# List
for key in manager.list_snapshots("prod"):
    print(key)

# Restore
content = manager.restore("prod", timestamp=1700000000, label="v2")
print(content)
```

## Notes

- Snapshots are encrypted with the same password as the rest of the vault.
- Timestamps are Unix epoch integers; use `list` to find available snapshots.
- Labels are optional but recommended for human readability.
