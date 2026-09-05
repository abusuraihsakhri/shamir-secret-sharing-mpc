# Shamir Secret Sharing MPC

> **Domain:** Post-Quantum Cryptography & Zero-Knowledge Architecture
> **Standards:** Shamir (k,n) Threshold Scheme, Feldman VSS

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)

</div>

---

## What It Does

**Shamir Secret Sharing MPC** implements Shamir (k,n) verifiable threshold secret sharing over prime fields, including share generation, Lagrange interpolation reconstruction, share verification, and information-theoretic security analysis. It also includes a FastAPI REST server and a multi-agent auditing framework.

---

## Key Features

- **Secret Sharing Engine**: Split secrets into n shares where any k can reconstruct (uses cryptographically secure randomness)
- **Lagrange Interpolation**: Reconstruct secrets from any k shares
- **Share Verification**: Validate shares and verify reconstruction correctness
- **Hash-based Commitments**: SHA-256 commitments for share integrity
- **Information-Theoretic Security Analysis**: Analyze the perfect secrecy guarantees
- **Multi-Agent Auditing Framework**: Sub-agent system for payload evaluation with HMAC-SHA256 audit trail
- **FastAPI REST API**: HTTP endpoints for remote operation
- **Prometheus Metrics**: Operational telemetry export

---

## Installation

```bash
pip install -e .
```

For development (with test dependencies):
```bash
pip install -e ".[dev]"
```

---

## CLI Usage

### Secret Sharing CLI

```bash
# Split a secret into shares
python cli.py split --secret 12345 --k 3 --n 5

# Reconstruct from shares
python cli.py reconstruct --shares '[[1, 123], [2, 456], [3, 789]]' --prime 257

# Verify shares reconstruct correctly
python cli.py verify --shares '[[1, 123], [2, 456], [3, 789]]' --secret 12345 --k 3 --prime 257

# Information-theoretic security analysis
python cli.py info --k 3 --n 5 --prime 257

# Generate a commitment for a share
python cli.py commit --share '[1, 123]' --prime 257
```

### Agent Framework CLI

```bash
# Run audit evaluation
python -m shamir_mpc_agent.cli audit --task-id TASK-001

# Batch process CSV
python -m shamir_mpc_agent.cli batch -i sample.csv -o results.csv

# Launch REST server
python -m shamir_mpc_agent.cli serve --host 127.0.0.1 --port 8000
```

---

## REST API

When running the server (`python -m shamir_mpc_agent.cli serve`), the following endpoints are available:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/audit` | Run audit evaluation |
| POST | `/api/chat` | Query supervisory chat |

---

## Testing

```bash
# Run all tests
pytest -v

# Run specific test module
pytest tests/test_shamir_secret_sharing_mpc.py -v
```

---

## Security Notes

- The secret sharing engine uses `secrets.randbelow()` for cryptographically secure coefficient generation
- The HMAC-SHA256 audit trail requires the `AUDIT_SECRET_KEY` environment variable (minimum 16 characters)
- Set the audit key before running:
  ```bash
  export AUDIT_SECRET_KEY="your-secure-key-here"
  ```

---

## Project Structure

```
shamir-secret-sharing-mpc/
├── shamir_mpc_agent/      # Core engine and agent framework
│   ├── engine.py          # Secret sharing math (split, reconstruct, verify)
│   ├── agents.py          # Sub-agent auditing system
│   ├── models.py          # Data models
│   ├── cli.py             # Agent CLI entry point
│   └── server.py          # FastAPI application
├── agents/                # Enterprise agent framework
│   ├── base.py            # PHI guard, audit trail, security
│   ├── supervisor.py      # Master orchestrator
│   ├── workers.py         # Domain worker agents
│   └── models.py          # Pydantic schemas
├── tests/                 # Test suite
├── cli.py                 # Secret sharing CLI
├── enrichment.py          # Enrichment feature suite
└── pyproject.toml         # Package configuration
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
