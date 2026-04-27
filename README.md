# envoy-cli

> A CLI tool to manage and sync `.env` files across multiple projects with encrypted remote storage support.

---

## Installation

```bash
pip install envoy-cli
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended):

```bash
pipx install envoy-cli
```

---

## Usage

```bash
# Initialize envoy in your project
envoy init

# Push your local .env to remote storage
envoy push --env production

# Pull the latest .env from remote storage
envoy pull --env production

# List all stored environments
envoy list

# Sync .env across multiple projects
envoy sync --projects api,frontend,worker
```

All secrets are encrypted before leaving your machine using AES-256 encryption. Configure your remote backend (S3, GCS, or a self-hosted vault) in `~/.envoy/config.toml`.

---

## Configuration

```toml
# ~/.envoy/config.toml
[remote]
backend = "s3"
bucket  = "my-envoy-store"
region  = "us-east-1"
```

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## License

[MIT](LICENSE)