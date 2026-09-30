"""모의 Ollama 서버로 러너·방어 훅·로그 경로를 끝까지 검증한다 (사내 서버 불필요)."""

from __future__ import annotations

import json
import socket
import threading
from pathlib import Path

import pytest
from click.testing import CliRunner

from agentdojo_ollama.run import main as run_main
from agentdojo_ollama.summarize import scan
from mock.ollama_mock import serve


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def mock_server():
    port = _free_port()
    server = serve(port, model="mock")
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}/v1", server.mock_state
    server.shutdown()


def _run(base_url: str, logdir: Path, *args: str) -> str:
    runner = CliRunner()
    common = ["--base-url", base_url, "--api-key", "ollama", "--model", "mock", "--logdir", str(logdir), "-s", "workspace"]
    result = runner.invoke(run_main, [*common, *args], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    return result.output


def test_utility_run_writes_log(mock_server, tmp_path):
    base_url, state = mock_server
    out = _run(base_url, tmp_path, "-ut", "user_task_0")
    log = tmp_path / "mock" / "workspace" / "user_task_0" / "none" / "none.json"
    assert log.exists(), out
    rec = json.loads(log.read_text())
    assert {"utility", "security", "messages", "duration"} <= rec.keys()
    roles = [m["role"] for m in rec["messages"]]
    assert roles[:2] == ["system", "user"] and "tool" in roles and roles[-1] == "assistant"
    # 모의 서버가 첫 턴에 툴을 호출하므로 툴 결과가 있고, 최종 응답에서 <think> 가 제거되어야 한다
    final = rec["messages"][-1]["content"][0]["content"]
    assert "<think>" not in final and "Done." in final

    # OllamaLLM 이 재현성 파라미터와 system 역할, 문자열 content 를 보냈는지
    req = state.requests[-1]
    assert req["temperature"] == 0.0 and req["seed"] == 0 and req["reasoning_effort"] == "none"
    assert req["roles"][0] == "system" and "developer" not in req["roles"]
    assert req["content_types"] and set(req["content_types"]) <= {"str", "NoneType"}


def test_attack_with_custom_defense(mock_server, tmp_path):
    base_url, _ = mock_server
    out = _run(
        base_url, tmp_path,
        "-ut", "user_task_0", "-it", "injection_task_0",
        "--attack", "important_instructions", "--defense", "passthrough",
    )
    log = tmp_path / "mock-passthrough" / "workspace" / "user_task_0" / "important_instructions" / "injection_task_0.json"
    assert log.exists(), out
    rec = json.loads(log.read_text())
    assert rec["attack_type"] == "important_instructions" and rec["injections"]
    assert "Targeted ASR" in out


def test_deny_gate_blocks_tool(mock_server, tmp_path):
    base_url, _ = mock_server
    # 모의 서버는 첫 번째 툴을 호출한다. banking 의 첫 툴이 send_money 가 아니면 이 테스트는 게이트 로직만 확인한다.
    runner = CliRunner()
    result = runner.invoke(
        run_main,
        ["--base-url", base_url, "--model", "mock", "--logdir", str(tmp_path), "-s", "banking",
         "-ut", "user_task_0", "--defense", "deny_sensitive_sinks"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    log = tmp_path / "mock-deny_sensitive_sinks" / "banking" / "user_task_0" / "none" / "none.json"
    rec = json.loads(log.read_text())
    tool_msgs = [m for m in rec["messages"] if m["role"] == "tool"]
    assert tool_msgs
    from agentdojo_ollama.defenses.builtin import SENSITIVE_SINKS

    for m in tool_msgs:
        if m["tool_call"]["function"] in SENSITIVE_SINKS:
            assert (m.get("error") or "").startswith("Blocked by policy")


def test_summarize_scan(mock_server, tmp_path):
    base_url, _ = mock_server
    _run(base_url, tmp_path, "-ut", "user_task_0")
    table = scan(tmp_path)
    assert ("mock", "none", "workspace") in table
    agg = table[("mock", "none", "workspace")]
    assert agg.n == 1


def test_unknown_defense_rejected(mock_server, tmp_path):
    base_url, _ = mock_server
    runner = CliRunner()
    result = runner.invoke(run_main, ["--base-url", base_url, "--model", "mock", "--defense", "nope", "-s", "workspace"])
    assert result.exit_code != 0 and "not a known defense" in result.output
