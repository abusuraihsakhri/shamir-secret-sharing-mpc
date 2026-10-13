"""CSV parsing regressions for audit batch CLI."""
import csv
from pathlib import Path

import pytest
from shamir_mpc_agent.cli import main, parse_bool, parse_metric


@pytest.mark.parametrize("value,expected", [
    ("False", False), ("false", False), ("0", False),
    ("True", True), ("1", True), ("yes", True), ("", False)
])
def test_parse_bool(value, expected):
    assert parse_bool(value) is expected


def test_bad_boolean_rejected():
    with pytest.raises(ValueError):
        parse_bool("perhaps")


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_metric_rejected(bad):
    with pytest.raises(ValueError):
        parse_metric(bad, "metric")


def test_sample_csv_false_flag_is_not_critical(tmp_path):
    source = Path(__file__).parent.parent / "sample.csv"
    target = tmp_path / "results.csv"
    assert main(["batch", "-i", str(source), "-o", str(target)]) == 0
    with target.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3
    assert rows[1]["task_id"] == "TASK-002"
    assert rows[1]["overall_status"] == "NOMINAL_OPTIMAL"
    assert rows[1]["critical_count"] == "0"
