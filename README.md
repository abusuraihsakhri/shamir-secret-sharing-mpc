# Shamir's Secret Sharing Calculator

A pure-Python implementation of Shamir's (k, n) threshold secret sharing scheme over prime finite fields. Uses only the Python standard library.

## Features

- **Secret Splitting**: Split secret S into n shares with threshold k (any k shares reconstruct)
- **Polynomial**: `f(x) = S + a₁x + a₂x² + ... + aₖ₋₁xᵏ⁻¹ (mod p)`
- **Share Generation**: `share_i = f(i) mod p` for `i = 1..n`
- **Lagrange Interpolation**: `S = Σ(yᵢ × Π(j≠i) xⱼ/(xⱼ-xᵢ)) mod p`
- **Prime Field Operations**: Modular arithmetic, modular inverse via Fermat's little theorem
- **Share Verification**: Validate coordinates, check consistency across subsets
- **Information-Theoretic Security**: k-1 shares reveal zero information about S
- **SHA-256 Commitments**: Commit to shares for later verification

## CLI Usage

```bash
# Split a secret into 5 shares with threshold 3
python cli.py split --secret 12345 --k 3 --n 5

# Reconstruct from shares
python cli.py reconstruct --shares '[[1,12346],[3,12350],[5,12358]]' --prime 12347

# Verify shares reconstruct to expected secret
python cli.py verify --shares '[[1,12346],[3,12350],[5,12358]]' --secret 12345 --k 3 --prime 12347

# Information-theoretic security analysis
python cli.py info --k 3 --n 5 --prime 12347

# Generate commitment for a share
python cli.py commit --share '[1, 12346]' --prime 12347
```

## Python API

```python
from shamir_mpc_agent.engine import split_secret, reconstruct_from_shares

# Split
result = split_secret(secret=12345, k=3, n=5)
shares = result["shares"]
p = result["prime"]

# Reconstruct from any 3 shares
recon = reconstruct_from_shares(shares[:3], p)
print(recon["secret"])  # 12345
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## License

MIT License.
