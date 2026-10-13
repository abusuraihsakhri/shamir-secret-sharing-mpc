"""Audit HMAC must authenticate entries and keep internal chain private."""
from agents.base import AuditTrail


def test_trail_rechecks_hmac_and_is_not_mutable():
    trail = AuditTrail("unit-test-key-not-for-production")
    first = trail.log("tester", "unit", "EVENT", {"status": "OK"})
    assert trail.verify_integrity()
    first["actor"] = "attacker"
    assert trail.verify_integrity()
    snapshot = trail.get_trail()
    snapshot[0]["actor"] = "attacker"
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "attacker"
    assert not trail.verify_integrity()


def test_changed_hash_does_not_verify_even_with_relinked_blocks():
    trail = AuditTrail("unit-test-key-not-for-production")
    trail.log("tester", "unit", "ONE", {"v": 1})
    trail.log("tester", "unit", "TWO", {"v": 2})
    assert trail.verify_integrity()
    trail.logs[0]["current_hash"] = "0" * 64
    trail.logs[1]["prev_hash"] = "0" * 64
    assert not trail.verify_integrity()
