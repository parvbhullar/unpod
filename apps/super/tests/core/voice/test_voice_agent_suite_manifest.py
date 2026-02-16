from pathlib import Path


def test_voice_agent_coverage_script_exists() -> None:
    script = Path("scripts/test_voice_agent_coverage.sh")
    assert script.exists()
    assert script.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash")
