"""
Shamir's Secret Sharing Engine
Implements: (k, n) threshold secret sharing with polynomial evaluation over prime fields,
Lagrange interpolation reconstruction, share verification, and information-theoretic security.
Uses only Python stdlib.
"""
import secrets
import hashlib
import hmac
import json
import math
from typing import List, Tuple, Dict, Any, Optional


# ---------------------------------------------------------------------------
# Prime field arithmetic
# ---------------------------------------------------------------------------

def _mod_inverse(a: int, p: int) -> int:
    """Compute modular inverse of a mod p using Fermat's little theorem (p must be prime)."""
    if a % p == 0:
        raise ValueError("Zero has no multiplicative inverse")
    return pow(a, -1, p)


def _mod_pow(base: int, exp: int, mod: int) -> int:
    """Modular exponentiation."""
    return pow(base, exp, mod)


# ---------------------------------------------------------------------------
# Polynomial operations over GF(p)
# ---------------------------------------------------------------------------

def evaluate_polynomial(coefficients: List[int], x: int, p: int) -> int:
    """
    Evaluate polynomial f(x) = c[0] + c[1]*x + c[2]*x^2 + ... mod p.
    coefficients[0] is the constant term (the secret).
    Uses Horner's method for efficiency.
    """
    if not coefficients:
        raise ValueError("Coefficients list cannot be empty")
    result = 0
    for c in reversed(coefficients):
        result = (result * x + c) % p
    return result


def generate_coefficients(k: int, p: int, secret: int) -> List[int]:
    """
    Generate random polynomial coefficients for a (k, n) sharing scheme.
    Returns [secret, a1, a2, ..., a_{k-1}] where each ai is random in [0, p).
    Uses cryptographically secure randomness (secrets module).
    """
    if not all(type(v) is int for v in (k, p, secret)):
        raise TypeError("Threshold, modulus and secret must be integers")
    if k < 2:
        raise ValueError("Threshold k must be at least 2")
    if not _is_prime(p):
        raise ValueError("Modulus p must be prime")
    if secret < 0 or secret >= p:
        raise ValueError(f"Secret must be in [0, {p})")
    coefficients = [secret]
    for _ in range(k - 1):
        coefficients.append(secrets.randbelow(p))
    return coefficients


# ---------------------------------------------------------------------------
# Share generation
# ---------------------------------------------------------------------------

def generate_shares(secret: int, k: int, n: int, p: Optional[int] = None) -> Tuple[List[Tuple[int, int]], int]:
    """
    Split secret into n shares with threshold k.
    Returns (shares, prime) where shares = [(x1, y1), (x2, y2), ...].
    Any k shares can reconstruct the secret; k-1 shares reveal nothing.
    
    Args:
        secret: The secret integer to share
        k: Threshold (minimum shares needed to reconstruct)
        n: Total number of shares to generate
        p: Prime modulus (must be > secret and > n). Auto-generated if None.
    
    Returns:
        Tuple of (list of (x, y) share tuples, prime p)
    """
    if not all(type(v) is int for v in (secret, k, n)) or (p is not None and type(p) is not int):
        raise TypeError("Secret, threshold, share count and modulus must be integers")
    if k > n:
        raise ValueError("Threshold k cannot exceed number of shares n")
    if k < 2:
        raise ValueError("Threshold k must be at least 2")
    if n < 1:
        raise ValueError("Number of shares n must be at least 1")

    # Auto-generate a suitable prime if not provided
    if p is None:
        p = _find_prime_larger_than(max(secret, n) + 1)
    
    if not _is_prime(p):
        raise ValueError("Modulus p must be prime")
    if secret < 0 or secret >= p:
        raise ValueError(f"Secret must be in [0, {p})")
    if n >= p:
        raise ValueError(f"n ({n}) must be less than p ({p})")

    coefficients = generate_coefficients(k, p, secret)
    shares = []
    for i in range(1, n + 1):
        y = evaluate_polynomial(coefficients, i, p)
        shares.append((i, y))
    return shares, p


def _find_prime_larger_than(min_val: int) -> int:
    """Find the first (probable for >64-bit) prime >= min_val."""
    if type(min_val) is not int:
        raise TypeError("Prime lower bound must be an integer")
    if min_val <= 2:
        return 2
    candidate = min_val | 1
    while not _is_prime(candidate):
        candidate += 2
    return candidate


def _is_prime(n: int) -> bool:
    """Miller-Rabin: deterministic for n < 2**64; 40 random rounds above.

    Above 64 bits this is a strong probable-prime test, not a proof.
    """
    if type(n) is not int or n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for prime in small:
        if n == prime:
            return True
        if n % prime == 0:
            return False
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1

    def witness(a: int) -> bool:
        x = pow(a, d, n)
        if x in (1, n - 1):
            return False
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                return False
        return True

    if n < 2**64:
        bases = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
    else:
        bases = (secrets.randbelow(n - 3) + 2 for _ in range(40))
    return not any(witness(a % n) for a in bases)


# ---------------------------------------------------------------------------
# Reconstruction via Lagrange interpolation
# ---------------------------------------------------------------------------

def reconstruct_secret(shares: List[Tuple[int, int]], p: int) -> int:
    """
    Reconstruct the secret from shares using Lagrange interpolation at x=0.
    
    S = Σ(y_i × Π(j≠i) x_j / (x_j - x_i)) mod p
    
    Args:
        shares: List of (x, y) tuples
        p: Prime modulus
    
    Returns:
        The reconstructed secret
    """
    if len(shares) < 2:
        raise ValueError("Need at least 2 shares to reconstruct")

    # Verify all x values are distinct
    x_values = [s[0] for s in shares]
    if len(set(x_values)) != len(x_values):
        raise ValueError("Duplicate x values in shares")

    secret = 0
    for i, (xi, yi) in enumerate(shares):
        # Compute Lagrange basis polynomial L_i(0)
        numerator = 1
        denominator = 1
        for j, (xj, _) in enumerate(shares):
            if i == j:
                continue
            numerator = (numerator * (-xj)) % p
            denominator = (denominator * (xi - xj)) % p
        
        lagrange_coeff = (numerator * _mod_inverse(denominator % p, p)) % p
        secret = (secret + yi * lagrange_coeff) % p

    return secret


# ---------------------------------------------------------------------------
# Share verification
# ---------------------------------------------------------------------------

def verify_share(share: Tuple[int, int], p: int) -> bool:
    """
    Verify that a share has valid coordinates.
    x must be > 0 and y must be in [0, p).
    """
    x, y = share
    return x > 0 and 0 <= y < p


def verify_shares(shares: List[Tuple[int, int]], p: int) -> bool:
    """Verify that all shares have valid coordinates."""
    return all(verify_share(s, p) for s in shares)


def verify_reconstruction(shares: List[Tuple[int, int]], p: int, expected_secret: int) -> bool:
    """
    Verify that a set of shares reconstructs to the expected secret.
    """
    reconstructed = reconstruct_secret(shares, p)
    return reconstructed == expected_secret


def verify_consistency(shares: List[Tuple[int, int]], k: int, p: int) -> bool:
    """
    Verify that shares are consistent: any subset of k shares
    should reconstruct to the same secret.
    """
    if len(shares) < k:
        return False
    
    # Take first k shares and reconstruct
    subset1 = shares[:k]
    secret1 = reconstruct_secret(subset1, p)
    
    # Take a different subset of k shares if possible
    if len(shares) > k:
        subset2 = shares[1:k+1]
        secret2 = reconstruct_secret(subset2, p)
        return secret1 == secret2
    
    return True


# ---------------------------------------------------------------------------
# Information-theoretic security analysis
# ---------------------------------------------------------------------------

def information_theoretic_security(k: int, n: int, p: int) -> Dict[str, Any]:
    """
    Analyze information-theoretic security of the sharing scheme.
    With k-1 shares, every possible secret value in [0, p) is equally likely.
    """
    return {
        "threshold": k,
        "num_shares": n,
        "prime": p,
        "shares_needed_for_reconstruction": k,
        "shares_revealing_no_info": k - 1,
        "possible_secrets_with_k_minus_1_shares": p,
        "bits_of_uncertainty": p.bit_length() - 1 if p > 1 else 0,
        "is_perfect_secrecy": True,
        "security_note": f"With {k-1} or fewer shares, every value in [0, {p}) is equally likely as the secret.",
    }


# ---------------------------------------------------------------------------
# Hash-based commitment for shares
# ---------------------------------------------------------------------------

def commit_share(share: Tuple[int, int], p: int) -> str:
    """Create a SHA-256 commitment to a share."""
    data = json.dumps({"x": share[0], "y": share[1], "p": p}, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()


def verify_commitment(share: Tuple[int, int], p: int, commitment: str) -> bool:
    """Verify a share commitment."""
    return commit_share(share, p) == commitment


# ---------------------------------------------------------------------------
# High-level API
# ---------------------------------------------------------------------------

def split_secret(secret: int, k: int, n: int, p: Optional[int] = None) -> Dict[str, Any]:
    """
    High-level API: split a secret and return all information needed.
    """
    shares, prime = generate_shares(secret, k, n, p)
    commitments = [commit_share(s, prime) for s in shares]
    security = information_theoretic_security(k, n, prime)
    
    return {
        "secret_length": secret.bit_length(),
        "threshold": k,
        "num_shares": n,
        "prime": prime,
        "shares": shares,
        "commitments": commitments,
        "security": security,
    }


def reconstruct_from_shares(shares: List[Tuple[int, int]], p: int) -> Dict[str, Any]:
    """
    High-level API: reconstruct secret from shares.
    """
    if not verify_shares(shares, p):
        return {"error": "Invalid share coordinates", "valid": False}

    secret = reconstruct_secret(shares, p)

    return {
        "secret": secret,
        "num_shares_used": len(shares),
        "prime": p,
        "valid": True,
    }


# ---------------------------------------------------------------------------
# Frontier Domain Engine — parameter evaluation for agent auditing
# ---------------------------------------------------------------------------

class FrontierDomainEngine:
    """
    Domain-specific evaluation engine used by the sub-agents to audit
    payloads against Shamir (k,n) & Feldman VSS operational thresholds.
    """

    PRIMARY_THRESHOLD = 25.0
    SECONDARY_THRESHOLD = 12.0

    @classmethod
    def evaluate_primary_parameter(cls, primary_metric: float) -> Optional[Dict[str, Any]]:
        """Evaluate primary metric against reference threshold."""
        if primary_metric > cls.PRIMARY_THRESHOLD:
            return {
                "summary": "Primary parameter exceeds operational reference limit",
                "details": f"Primary metric ({primary_metric:.2f}) exceeds upper reference limit ({cls.PRIMARY_THRESHOLD:.2f}) under Shamir (k,n) & Feldman VSS.",
                "remediation": "Initiate recalibration workflow and review secondary parameters.",
            }
        return None

    @classmethod
    def evaluate_secondary_kinetics(cls, secondary_metric: float, is_critical_flag: bool) -> Optional[Dict[str, Any]]:
        """Evaluate secondary metric and critical flag against safety thresholds."""
        if is_critical_flag or secondary_metric > cls.SECONDARY_THRESHOLD:
            return {
                "summary": "Critical safety interlock triggered",
                "details": f"CriticalFlag={is_critical_flag} with secondary index {secondary_metric:.2f}.",
                "remediation": "Execute immediate closed-loop escalation and notify attending supervisor.",
            }
        return None

    @classmethod
    def audit_specification_conformance(cls, status_descriptor: str, attributes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Audit status descriptor for protocol conformance."""
        desc_upper = str(status_descriptor).upper()
        discordant_markers = ["DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT"]
        if any(w in desc_upper for w in discordant_markers):
            return {
                "summary": "Protocol conformance discordance detected",
                "details": f"Descriptor '{status_descriptor}' indicates discordance with Shamir (k,n) & Feldman VSS specifications.",
                "remediation": "Re-evaluate input or rerun secondary confirmation.",
            }
        return None
