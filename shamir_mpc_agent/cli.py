"""
Command-Line Interface for Shamir (k, n) Verifiable Threshold Secret Sharing & Distributed Key Generation Agent.
"""
import argparse
import csv
import json
import math
import sys
from .models import FrontierPayload
from .agents import ThresholdSecretCoordinator

coordinator = ThresholdSecretCoordinator()

def parse_bool(value):
    """Parse CSV boolean strings without treating 'False' as true."""
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    if normalized in ("true", "1", "yes", "y", "on"):
        return True
    if normalized in ("false", "0", "no", "n", "off", ""):
        return False
    raise ValueError(f"Unrecognized boolean value: {value!r}")


def parse_metric(value, name):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    return result



def main(argv=None):
    parser = argparse.ArgumentParser(prog="shamir-secret-sharing-mpc", description="Shamir (k, n) Verifiable Threshold Secret Sharing & Distributed Key Generation Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="TARGET-GEN-01")
    p_audit.add_argument("--primary", type=float, default=29.4)
    p_audit.add_argument("--secondary", type=float, default=15.1)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = FrontierPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = coordinator.process(payload)
        print("=" * 80)
        print(f"  SHAMIR (K, N) VERIFIABLE THRESHOLD SECRET SHARING & DISTRIBUTED KEY GENERATION AGENT")
        print(f"  Domain: Post-Quantum Cryptography & Zero-Knowledge | Standard: Shamir (k,n) & Feldman VSS")
        print(f"  Task: {dossier['task_id']} | Status: [{dossier['overall_status']}] | Total Alerts: {dossier['total_alerts']}")
        print("=" * 80)
        for a in dossier["alerts"]:
            print(f"\n  [{a['status']}] from {a['origin_agent']}:")
            print(f"  Summary: {a['summary']}")
            print(f"  Details: {a['technical_details']}")
            print(f"  Action:  {a['actionable_remediation']}")
        print("\n" + "=" * 80)
        return 0

    if args.command == "chat":
        ans = coordinator.query_supervisory_chat(" ".join(args.query))
        print(f"\n[ThresholdSecretCoordinator]:\n{ans}\n")
        return 0

    if args.command == "batch":
        with open(args.input, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        derived_fields = ["overall_status", "total_alerts", "critical_count", "consensus_summary"]
        out_fields = fieldnames + [name for name in derived_fields if name not in fieldnames]
        out_rows = []
        for r in rows:
            payload = FrontierPayload(
                task_id=r.get("task_id", "TASK-01"),
                target_identifier=r.get("target_identifier", "TARGET-01"),
                primary_metric=parse_metric(r.get("primary_metric", 15.0), "primary_metric"),
                secondary_metric=parse_metric(r.get("secondary_metric", 5.0), "secondary_metric"),
                status_descriptor=r.get("status_descriptor", "NOMINAL"),
                is_critical_flag=parse_bool(r.get("is_critical_flag", False)),
            )
            dossier = coordinator.process(payload)
            row_dict = dict(r)
            row_dict["overall_status"] = dossier["overall_status"]
            row_dict["total_alerts"] = dossier["total_alerts"]
            row_dict["critical_count"] = dossier["critical_count"]
            row_dict["consensus_summary"] = dossier["consensus_summary"]
            out_rows.append(row_dict)

        with open(args.output, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from .server import create_app
            app = create_app()
            if app:
                print(f"Starting Shamir (k, n) Verifiable Threshold Secret Sharing & Distributed Key Generation Agent on http://{args.host}:{args.port}")
                uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("FastAPI / uvicorn not installed. Run 'pip install fastapi uvicorn'")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
