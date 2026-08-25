"""
Real tests for Shamir's Secret Sharing Engine.
"""
import random
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shamir_mpc_agent.engine import (
    evaluate_polynomial, generate_coefficients,
    generate_shares, reconstruct_secret,
    verify_share, verify_shares, verify_reconstruction, verify_consistency,
    information_theoretic_security,
    commit_share, verify_commitment,
    split_secret, reconstruct_from_shares,
    _is_prime, _find_prime_larger_than, _mod_inverse,
)


class TestPrimeArithmetic(unittest.TestCase):

    def test_mod_inverse_fermat(self):
        # 3 * 5 = 15 ≡ 1 (mod 7), so inv(3) = 5
        self.assertEqual(_mod_inverse(3, 7), 5)

    def test_mod_inverse_self(self):
        # inv(1) = 1 for any prime
        self.assertEqual(_mod_inverse(1, 13), 1)

    def test_mod_inverse_larger_prime(self):
        p = 257
        a = 42
        inv = _mod_inverse(a, p)
        self.assertEqual((a * inv) % p, 1)


class TestPrimality(unittest.TestCase):

    def test_small_primes(self):
        for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]:
            self.assertTrue(_is_prime(p), f"{p} should be prime")

    def test_small_composites(self):
        for c in [4, 6, 8, 9, 10, 12, 15, 21]:
            self.assertFalse(_is_prime(c), f"{c} should not be prime")

    def test_find_prime_larger_than(self):
        p = _find_prime_larger_than(100)
        self.assertGreaterEqual(p, 100)
        self.assertTrue(_is_prime(p))

    def test_find_prime_larger_than_exact(self):
        p = _find_prime_larger_than(7)
        self.assertEqual(p, 7)


class TestPolynomialEvaluation(unittest.TestCase):

    def test_constant_polynomial(self):
        # f(x) = 42 for all x
        self.assertEqual(evaluate_polynomial([42], 1, 257), 42)
        self.assertEqual(evaluate_polynomial([42], 5, 257), 42)

    def test_linear_polynomial(self):
        # f(x) = 3 + 2x mod 7
        # f(1) = 5, f(2) = 0 (7 mod 7), f(3) = 2 (9 mod 7)
        self.assertEqual(evaluate_polynomial([3, 2], 1, 7), 5)
        self.assertEqual(evaluate_polynomial([3, 2], 2, 7), 0)
        self.assertEqual(evaluate_polynomial([3, 2], 3, 7), 2)

    def test_quadratic_polynomial(self):
        # f(x) = 1 + 2x + 3x^2 mod 7
        # f(1) = 1+2+3 = 6 mod 7 = 6
        self.assertEqual(evaluate_polynomial([1, 2, 3], 1, 7), 6)
        # f(2) = 1+4+12 = 17 mod 7 = 3
        self.assertEqual(evaluate_polynomial([1, 2, 3], 2, 7), 3)

    def test_empty_coefficients_raises(self):
        with self.assertRaises(ValueError):
            evaluate_polynomial([], 1, 7)


class TestGenerateCoefficients(unittest.TestCase):

    def test_length(self):
        coeffs = generate_coefficients(3, 257, 42)
        self.assertEqual(len(coeffs), 3)

    def test_first_is_secret(self):
        coeffs = generate_coefficients(3, 257, 42)
        self.assertEqual(coeffs[0], 42)

    def test_coefficients_in_field(self):
        p = 17
        coeffs = generate_coefficients(5, p, 10)
        for c in coeffs:
            self.assertGreaterEqual(c, 0)
            self.assertLess(c, p)

    def test_k_too_small(self):
        with self.assertRaises(ValueError):
            generate_coefficients(1, 257, 42)

    def test_secret_out_of_range(self):
        with self.assertRaises(ValueError):
            generate_coefficients(3, 7, 10)  # 10 >= 7


class TestShareGeneration(unittest.TestCase):

    def test_correct_number_of_shares(self):
        random.seed(42)
        shares, p = generate_shares(42, 3, 5)
        self.assertEqual(len(shares), 5)

    def test_share_x_values_sequential(self):
        random.seed(42)
        shares, p = generate_shares(42, 3, 5)
        x_values = [s[0] for s in shares]
        self.assertEqual(x_values, [1, 2, 3, 4, 5])

    def test_shares_in_field(self):
        random.seed(42)
        shares, p = generate_shares(42, 3, 5)
        for x, y in shares:
            self.assertGreaterEqual(y, 0)
            self.assertLess(y, p)

    def test_k_greater_than_n_raises(self):
        with self.assertRaises(ValueError):
            generate_shares(42, 5, 3)

    def test_auto_prime(self):
        random.seed(42)
        shares, p = generate_shares(100, 3, 5)
        self.assertTrue(_is_prime(p))
        self.assertGreater(p, 100)


class TestReconstruction(unittest.TestCase):

    def test_basic_reconstruction(self):
        random.seed(42)
        secret = 12345
        shares, p = generate_shares(secret, 3, 5)
        reconstructed = reconstruct_secret(shares[:3], p)
        self.assertEqual(reconstructed, secret)

    def test_any_k_shares_work(self):
        random.seed(42)
        secret = 999
        shares, p = generate_shares(secret, 3, 5)
        # Try different subsets of 3 shares
        for i in range(3):
            subset = [shares[j] for j in range(5) if j != i and j != i + 1][:3]
            if len(subset) >= 3:
                self.assertEqual(reconstruct_secret(subset, p), secret)

    def test_all_shares_reconstruct(self):
        random.seed(42)
        secret = 42
        shares, p = generate_shares(secret, 2, 4)
        reconstructed = reconstruct_secret(shares, p)
        self.assertEqual(reconstructed, secret)

    def test_too_few_shares_error(self):
        with self.assertRaises(ValueError):
            reconstruct_secret([(1, 5)], 7)

    def test_duplicate_x_raises(self):
        with self.assertRaises(ValueError):
            reconstruct_secret([(1, 5), (1, 10)], 7)

    def test_large_secret(self):
        random.seed(42)
        # Use a known large prime and a secret that fits
        p = 104729  # known prime
        secret = 100000
        shares, p = generate_shares(secret, 3, 5, p)
        reconstructed = reconstruct_secret(shares[:3], p)
        self.assertEqual(reconstructed, secret)


class TestVerification(unittest.TestCase):

    def test_verify_share_valid(self):
        self.assertTrue(verify_share((1, 5), 7))

    def test_verify_share_invalid_y(self):
        self.assertFalse(verify_share((1, 7), 7))

    def test_verify_share_invalid_x(self):
        self.assertFalse(verify_share((0, 5), 7))

    def test_verify_shares_all_valid(self):
        random.seed(42)
        shares, p = generate_shares(42, 3, 5)
        self.assertTrue(verify_shares(shares, p))

    def test_verify_reconstruction_correct(self):
        random.seed(42)
        secret = 42
        shares, p = generate_shares(secret, 3, 5)
        self.assertTrue(verify_reconstruction(shares[:3], p, secret))

    def test_verify_reconstruction_wrong_secret(self):
        random.seed(42)
        shares, p = generate_shares(42, 3, 5)
        self.assertFalse(verify_reconstruction(shares[:3], p, 999))

    def test_verify_consistency(self):
        random.seed(42)
        shares, p = generate_shares(42, 3, 5)
        self.assertTrue(verify_consistency(shares, 3, p))


class TestInformationTheoreticSecurity(unittest.TestCase):

    def test_returns_dict(self):
        result = information_theoretic_security(3, 5, 257)
        self.assertIsInstance(result, dict)

    def test_perfect_secrecy(self):
        result = information_theoretic_security(3, 5, 257)
        self.assertTrue(result["is_perfect_secrecy"])

    def test_shares_revealing_no_info(self):
        result = information_theoretic_security(3, 5, 257)
        self.assertEqual(result["shares_revealing_no_info"], 2)

    def test_possible_secrets_count(self):
        result = information_theoretic_security(3, 5, 257)
        self.assertEqual(result["possible_secrets_with_k_minus_1_shares"], 257)


class TestCommitments(unittest.TestCase):

    def test_commit_deterministic(self):
        c1 = commit_share((1, 42), 257)
        c2 = commit_share((1, 42), 257)
        self.assertEqual(c1, c2)

    def test_commit_different_for_different_shares(self):
        c1 = commit_share((1, 42), 257)
        c2 = commit_share((2, 42), 257)
        self.assertNotEqual(c1, c2)

    def test_verify_commitment(self):
        share = (1, 42)
        p = 257
        commitment = commit_share(share, p)
        self.assertTrue(verify_commitment(share, p, commitment))

    def test_verify_commitment_wrong(self):
        self.assertFalse(verify_commitment((1, 42), 257, "wrong_hash"))


class TestHighLevelAPI(unittest.TestCase):

    def test_split_secret(self):
        random.seed(42)
        result = split_secret(42, 3, 5)
        self.assertEqual(result["threshold"], 3)
        self.assertEqual(result["num_shares"], 5)
        self.assertEqual(len(result["shares"]), 5)
        self.assertEqual(len(result["commitments"]), 5)

    def test_split_and_reconstruct(self):
        random.seed(42)
        secret = 123456
        split_result = split_secret(secret, 3, 5)
        shares = split_result["shares"]
        p = split_result["prime"]
        recon_result = reconstruct_from_shares(shares[:3], p)
        self.assertTrue(recon_result["valid"])
        self.assertEqual(recon_result["secret"], secret)

    def test_reconstruct_with_all_shares(self):
        random.seed(42)
        secret = 777
        split_result = split_secret(secret, 2, 4)
        recon_result = reconstruct_from_shares(split_result["shares"], split_result["prime"])
        self.assertEqual(recon_result["secret"], secret)


if __name__ == "__main__":
    unittest.main()
