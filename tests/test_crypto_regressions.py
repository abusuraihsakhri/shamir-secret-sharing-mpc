"""Regression tests for finite-field and threshold correctness."""
import itertools

import pytest
from shamir_mpc_agent.engine import (
    _find_prime_larger_than, _is_prime, _mod_inverse, generate_shares,
    reconstruct_secret, reconstruct_from_shares, verify_share, verify_shares,
    verify_consistency, information_theoretic_security
)


def test_prime_two_and_strong_pseudoprime():
    assert _find_prime_larger_than(2) == 2
    assert not _is_prime(341550071728321)
    assert _is_prime(18446744073709551557)


@pytest.mark.parametrize("bad_modulus", [0, 1, 4, 9, 15, 341550071728321])
def test_reject_composite_field(bad_modulus):
    with pytest.raises(ValueError):
        generate_shares(2, 2, 3, bad_modulus)


def test_reject_noncanonical_x_values():
    assert not verify_share((257, 10), 257)
    assert not verify_shares([(1, 5), (258, 8)], 257)
    assert not verify_shares([(1, 5), (1, 8)], 257)
    with pytest.raises(ValueError):
        reconstruct_secret([(1, 5), (258, 8)], 257)


def test_consistency_checks_all_shares():
    valid = [(1, 1), (2, 2), (3, 3), (4, 4)]
    assert verify_consistency(valid, 2, 257)
    assert not verify_consistency(valid[:-1] + [(4, 88)], 2, 257)


def test_uniform_random_polynomial_roundtrips():
    for threshold in (2, 3, 4):
        shares, prime = generate_shares(123, threshold, 5, 257)
        for subset in itertools.combinations(shares, threshold):
            assert reconstruct_secret(list(subset), prime) == 123


def test_reject_modular_zero_inverse():
    with pytest.raises(ValueError):
        _mod_inverse(257, 257)


def test_validation_does_not_accept_missing_shares():
    assert not verify_shares([], 257)
    assert reconstruct_from_shares([], 257)["valid"] is False


def test_security_report_requires_valid_field():
    with pytest.raises(ValueError):
        information_theoretic_security(3, 2, 257)
    with pytest.raises(ValueError):
        information_theoretic_security(2, 3, 15)
