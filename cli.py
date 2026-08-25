"""
CLI for Shamir's Secret Sharing Calculator.
Supports: split, reconstruct, verify, info-theoretic security analysis.
"""
import argparse
import json
import sys

from shamir_mpc_agent.engine import (
    split_secret, reconstruct_from_shares,
    verify_shares, verify_reconstruction, verify_consistency,
    information_theoretic_security, commit_share, verify_commitment,
    generate_shares, reconstruct_secret,
)


def cmd_split(args):
    """Split a secret into shares."""
    result = split_secret(args.secret, args.k, args.n, args.prime)
    # Convert shares to serializable format
    output = {
        "secret_length": result["secret_length"],
        "threshold": result["threshold"],
        "num_shares": result["num_shares"],
        "prime": result["prime"],
        "shares": [[s[0], s[1]] for s in result["shares"]],
        "commitments": result["commitments"],
        "security": result["security"],
    }
    print(json.dumps(output, indent=2))


def cmd_reconstruct(args):
    """Reconstruct secret from shares."""
    shares = json.loads(args.shares)
    shares = [(s[0], s[1]) for s in shares]
    result = reconstruct_from_shares(shares, args.prime)
    print(json.dumps(result, indent=2))


def cmd_verify(args):
    """Verify shares reconstruct to expected secret."""
    shares = json.loads(args.shares)
    shares = [(s[0], s[1]) for s in shares]
    
    valid_coords = verify_shares(shares, args.prime)
    reconstructs_correctly = verify_reconstruction(shares, args.prime, args.secret)
    consistent = verify_consistency(shares, args.k, args.prime)
    
    print(json.dumps({
        "valid_coordinates": valid_coords,
        "reconstructs_to_secret": reconstructs_correctly,
        "consistent_subsets": consistent,
        "all_checks_pass": valid_coords and reconstructs_correctly and consistent,
    }, indent=2))


def cmd_info(args):
    """Show information-theoretic security analysis."""
    result = information_theoretic_security(args.k, args.n, args.prime)
    print(json.dumps(result, indent=2))


def cmd_commit(args):
    """Generate commitment for a share."""
    share = tuple(json.loads(args.share))
    commitment = commit_share(share, args.prime)
    print(json.dumps({"share": list(share), "commitment": commitment}, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="shamir-secret-sharing-mpc",
        description="Shamir's Secret Sharing Calculator: (k,n) threshold scheme over prime fields")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Split
    p_split = subparsers.add_parser("split", help="Split secret into shares")
    p_split.add_argument("--secret", type=int, required=True, help="Secret integer to share")
    p_split.add_argument("--k", type=int, required=True, help="Threshold (min shares to reconstruct)")
    p_split.add_argument("--n", type=int, required=True, help="Total number of shares")
    p_split.add_argument("--prime", type=int, default=None, help="Prime modulus (auto-generated if omitted)")

    # Reconstruct
    p_recon = subparsers.add_parser("reconstruct", help="Reconstruct secret from shares")
    p_recon.add_argument("--shares", type=str, required=True, help='JSON array of [x,y] pairs')
    p_recon.add_argument("--prime", type=int, required=True, help="Prime modulus")

    # Verify
    p_verify = subparsers.add_parser("verify", help="Verify shares reconstruct correctly")
    p_verify.add_argument("--shares", type=str, required=True, help='JSON array of [x,y] pairs')
    p_verify.add_argument("--secret", type=int, required=True, help="Expected secret")
    p_verify.add_argument("--k", type=int, required=True, help="Threshold")
    p_verify.add_argument("--prime", type=int, required=True, help="Prime modulus")

    # Info
    p_info = subparsers.add_parser("info", help="Information-theoretic security analysis")
    p_info.add_argument("--k", type=int, required=True, help="Threshold")
    p_info.add_argument("--n", type=int, required=True, help="Number of shares")
    p_info.add_argument("--prime", type=int, required=True, help="Prime modulus")

    # Commit
    p_commit = subparsers.add_parser("commit", help="Generate share commitment")
    p_commit.add_argument("--share", type=str, required=True, help='JSON [x,y] pair')
    p_commit.add_argument("--prime", type=int, required=True, help="Prime modulus")

    args = parser.parse_args(argv)

    cmd_map = {
        "split": cmd_split,
        "reconstruct": cmd_reconstruct,
        "verify": cmd_verify,
        "info": cmd_info,
        "commit": cmd_commit,
    }
    return cmd_map[args.command](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
