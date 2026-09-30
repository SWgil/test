"""Ollama 의 OpenAI 호환 API 를 흉내내는 모의 서버 (표준 라이브러리만 사용).

사내 Ollama 서버에 접근할 수 없는 환경에서 러너·방어·로그 경로가 끝까지 도는지 확인하는 용도다.
모델 품질과는 무관하다.

동작:
- GET  /v1/models            → {"data":[{"id": <model>}]}
- POST /v1/chat/completions  →
    * tools 가 있고 대화에 tool 결과 메시지가 아직 없으면: 첫 번째(또는 --tool 로 지정한) 툴을
      required 인자를 더미 값으로 채워 호출하는 tool_calls 응답 (finish_reason="tool_calls")
    * 그 외: "<think>...</think>Done." 텍스트 응답 (finish_reason="stop")
- 받은 요청의 model/temperature/seed/reasoning_effort/역할 목록/tools 수를 --log 파일(JSONL)에 기록한다.

실행: python -m mock.ollama_mock --port 18080 [--model mock] [--log runs/mock_requests.jsonl]
"""

from __future__ import annotations

import argparse
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def _dummy_value(schema: dict):
    t = schema.get("type")
    if "enum" in schema:
        return schema["enum"][0]
    if t == "integer":
        return 1
    if t == "number":
        return 1.0
    if t == "boolean":
        return True
    if t == "array":
        return []
    if t == "object":
        return {}
    if "anyOf" in schema:
        for alt in schema["anyOf"]:
            if alt.get("type") != "null":
                return _dummy_value(alt)
    return "mock"


def _pick_tool(tools: list[dict], preferred: str | None) -> dict | None:
    if not tools:
        return None
    if preferred:
        for t in tools:
            if t.get("function", {}).get("name") == preferred:
                return t
    return tools[0]


class MockState:
    def __init__(self, model: str, tool: str | None, log_path: str | None, delay: float) -> None:
        self.model = model
        self.tool = tool
        self.log_path = log_path
        self.delay = delay
        self.lock = threading.Lock()
        self.requests: list[dict] = []

    def record(self, entry: dict) -> None:
        with self.lock:
            self.requests.append(entry)
            if self.log_path:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def make_handler(state: MockState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # 조용히
            pass

        def _send(self, code: int, body: dict) -> None:
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path.rstrip("/").endswith("/models"):
                self._send(200, {"object": "list", "data": [{"id": state.model, "object": "model"}]})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):
            if not self.path.rstrip("/").endswith("/chat/completions"):
                self._send(404, {"error": "not found"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(length) or b"{}")
            messages = req.get("messages", [])
            tools = req.get("tools", [])
            state.record(
                {
                    "model": req.get("model"),
                    "temperature": req.get("temperature"),
                    "seed": req.get("seed"),
                    "reasoning_effort": req.get("reasoning_effort"),
                    "roles": [m.get("role") for m in messages],
                    "content_types": sorted({type(m.get("content")).__name__ for m in messages}),
                    "n_tools": len(tools),
                }
            )
            if state.delay:
                time.sleep(state.delay)

            has_tool_result = any(m.get("role") == "tool" for m in messages)
            tool = _pick_tool(tools, state.tool)
            if tool and not has_tool_result:
                fn = tool["function"]
                params = fn.get("parameters", {})
                props = params.get("properties", {})
                required = params.get("required", list(props))
                args = {k: _dummy_value(props.get(k, {})) for k in required}
                message = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": f"call_{uuid.uuid4().hex[:12]}",
                            "type": "function",
                            "function": {"name": fn["name"], "arguments": json.dumps(args)},
                        }
                    ],
                }
                finish = "tool_calls"
            else:
                message = {"role": "assistant", "content": "<think>mock reasoning</think>Done."}
                finish = "stop"

            self._send(
                200,
                {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": req.get("model", state.model),
                    "choices": [{"index": 0, "message": message, "finish_reason": finish}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                },
            )

    return Handler


def serve(port: int, model: str = "mock", tool: str | None = None, log_path: str | None = None, delay: float = 0.0):
    """서버를 만들어 반환한다 (호출자가 serve_forever / shutdown 을 관리)."""
    state = MockState(model, tool, log_path, delay)
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(state))
    server.mock_state = state  # type: ignore[attr-defined]
    return server


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=18080)
    ap.add_argument("--model", default="mock")
    ap.add_argument("--tool", default=None, help="첫 턴에 호출할 툴 이름 (기본: 첫 번째 툴)")
    ap.add_argument("--log", default=None, help="요청 기록 JSONL 경로")
    ap.add_argument("--delay", type=float, default=0.0, help="응답 지연(초)")
    args = ap.parse_args()
    server = serve(args.port, args.model, args.tool, args.log, args.delay)
    print(f"mock ollama listening on http://127.0.0.1:{args.port}/v1 (model={args.model})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
