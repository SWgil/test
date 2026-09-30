#!/usr/bin/env bash
# 오프라인 검증: 모의 Ollama 서버를 띄우고 스모크(공격 없음 2개 + 공격 1개, DEFENSE 기본 passthrough)를 돌린다.
# 사내 서버 없이 러너·방어 훅·로그 경로가 끝까지 도는지만 확인한다. 로그는 LOGDIR (기본 runs_mock) 에 남는다.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
PORT="${PORT:-18080}"
export LOGDIR="${LOGDIR:-runs_mock}"
export OLLAMA_BASE_URL="http://127.0.0.1:$PORT/v1" OLLAMA_API_KEY=ollama OLLAMA_MODEL="${OLLAMA_MODEL:-mock}"
export DEFENSE="${DEFENSE:-passthrough}"
VENV="${VENV:-.venv}"
mkdir -p "$LOGDIR"
"$VENV/bin/python" -m mock.ollama_mock --port "$PORT" --model "$OLLAMA_MODEL" --log "$LOGDIR/mock_requests.jsonl" &
MOCK_PID=$!
trap 'kill $MOCK_PID 2>/dev/null || true' EXIT
for _ in $(seq 1 50); do curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1 && break; sleep 0.2; done
CONFIG=/dev/null scripts/run_smoke.sh
"$VENV/bin/agentdojo-summarize" --logdir "$LOGDIR"
