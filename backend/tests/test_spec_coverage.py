import re
from pathlib import Path

SPEC = Path(__file__).resolve().parents[2] / "SPEC.md"


def test_every_spec_statement_has_a_test():
    spec_ids = {int(n) for n in re.findall(r"\*\*S(\d+)\.\*\*", SPEC.read_text(encoding="utf-8"))}
    tested = set()
    for path in Path(__file__).parent.glob("test_*.py"):
        tested |= {int(n) for n in re.findall(r"def test_S(\d+)_", path.read_text(encoding="utf-8"))}
    assert spec_ids, "No statements found in SPEC.md"
    assert not spec_ids - tested, f"Statements without a test: {sorted(spec_ids - tested)}"
