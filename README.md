# Shamir Secret Sharing MPC

A Python demonstration of Shamir (k, n) threshold secret sharing over prime fields, with a separate rule-based audit API and a static browser demonstration.

## Browser application

The self-contained interface is in [web/index.html](web/index.html). It uses JavaScript BigInt and Web Crypto to generate shares and reconstruct integers in the browser. It does not submit secrets to a server or use analytics/browser storage. It limits the demonstration to 64 shares and 256-bit secret integers.

To run locally:

```bash
python -m http.server 8080 --directory web
```

Open http://localhost:8080/ in a modern browser with JavaScript BigInt and Web Crypto support. A GitHub Pages publishing workflow is included; a public URL will be documented after deployment is verified.

## Python installation

Python 3.9+ is supported. The core engine uses the standard library.

```bash
python -m pip install -e .
# For API and test dependencies:
python -m pip install -e ".[all]"
```

## Secret-sharing CLI

```bash
shamir-share split --secret 12345 --k 3 --n 5
shamir-share reconstruct --shares '[[1,100],[2,70],[3,200]]' --prime 257
shamir-share verify --shares '[[1,100],[2,70],[3,200]]' --secret 123 --k 3 --prime 257
shamir-share info --k 3 --n 5 --prime 257
```

The reconstruction command requires the *same modulus* supplied at splitting and at least k authentic shares. The sample share arrays above illustrate syntax only; they are not a valid reconstruction vector. The full module entry point `python cli.py` is also supported.

Run the separate deterministic audit coordinator with:

```bash
python -m shamir_mpc_agent.cli audit --task-id DEMO-001
python -m shamir_mpc_agent.cli batch -i sample.csv -o results.csv
```

This audit coordinator applies **illustrative numerical threshold rules**, not cryptographic Feldman verification.

## API and container

The Docker image runs `agents.api:app`, an in-memory rule-based audit service with HMAC-SHA256 audit-chain records. **Its API has no authentication. Do not expose it to untrusted networks.** Compose binds the host port to `127.0.0.1:8000`.

Generate a new audit key locally (never commit the value):

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

API endpoints include `GET /health`, `GET /metrics`, `POST /api/audit`, `POST /api/chat`, and `GET /api/audit/logs`. Interactive local documentation is at http://127.0.0.1:8000/docs. The separate legacy API can be started with `python -m shamir_mpc_agent.cli serve` and has a different response schema.

## Correctness, privacy, and security limits

- The arithmetic uses prime fields GF(p), cryptographically sourced random coefficients, and Lagrange interpolation. The Python and browser primality tests are deterministic below 2^64; beyond that they perform **40 probabilistic Miller–Rabin rounds** rather than mathematical prime certification.
- Share-coordinate validation and polynomial consistency checks **do not authenticate** a share or prove dealer honesty. The deterministic SHA-256 share hashes are integrity fingerprints, **not hiding or Feldman commitments**; publishing them can disclose low-entropy shares by enumeration.
- This repository does **not** implement Feldman VSS, secure multiparty computation, distributed key generation, proactive rotation, cryptographic side-channel resistance, or certified post-quantum cryptography. The additional rule-based enrichment classes do not constitute independent cryptographic validation.
- The Shamir information-theoretic privacy claim applies to fewer than k **private shares**, uniformly random polynomial coefficients, and does not account for publicly revealing share hashes. The secrecy *entropy* estimate assumes a uniform secret prior.
- Both Python and browser implementations are educational and **not validated for production key custody**. Python big-integer arithmetic and JavaScript BigInt are not constant-time. Avoid inputting real secrets into the browser, command-line arguments (shell history/process listings), or the unauthenticated REST service.
- The audit API stores records only in process memory, uses heuristic identifier filtering rather than comprehensive deidentification, and is not an immutable or externally anchored log. A previously hard-coded Compose key existed in repository history; treat it as disclosed and do not reuse it.

## Tests

```bash
python -m pip install -e ".[all]"
python -m pytest -q
node --test tests/web.test.cjs  # Node.js 20+
```

GitHub Actions runs Python tests across 3.9–3.13, JavaScript regression tests, dependency checks, and a test-key-only HMAC integrity smoke test. The Pages workflow deploys the `web/` folder when GitHub Pages is enabled for the repository.

## Code layout

- `shamir_mpc_agent/engine.py` — Shamir arithmetic, share validation and interpolation
- `cli.py` — core secret-sharing CLI
- `shamir_mpc_agent/` — additional rule-based coordinator and legacy API
- `agents/` — illustrative audit workers, HMAC log, and container API
- `web/` — static browser demonstration
- `enrichment.py` — rule-based heuristic templates (not cryptographic primitives)
- `tests/` — Python and browser regression tests

## License

[MIT](LICENSE).
