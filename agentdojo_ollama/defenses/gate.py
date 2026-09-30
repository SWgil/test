"""툴 호출 게이트: FIDES 변형 방어들이 공유하는 실행 전/후 훅.

AgentDojo 의 `ToolsExecutor.query` 는 assistant 메시지의 tool_calls 를 순서대로 실행하고
tool_call 마다 정확히 하나의 `ChatToolResultMessage`(같은 tool_call_id)를 만든다.
OpenAI 호환 API 는 이 1:1 대응을 요구하므로, 호출을 "빼는" 대신 거부된 호출에
`error=` 메시지를 돌려주는 방식으로 게이트를 구현한다.

게이트 상태(레이블, 출처 인덱스 등)는 파이프라인이 넘겨주는 `extra_args` dict 에 보관한다.
`extra_args` 는 한 태스크 실행 동안 파이프라인 요소 사이를 그대로 흐른다.
"""

from __future__ import annotations

from ast import literal_eval
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from agentdojo.agent_pipeline.tool_execution import EMPTY_FUNCTION_NAME, ToolsExecutor, is_string_list, tool_result_to_str
from agentdojo.functions_runtime import EmptyEnv, Env, FunctionCall, FunctionReturnType, FunctionsRuntime
from agentdojo.types import ChatMessage, ChatToolResultMessage, text_content_block_from_string


@dataclass
class Decision:
    """게이트 판정. allow=False 면 툴을 실행하지 않고 `reason` 을 에러로 돌려준다.

    `args` 를 주면 실행 인자를 그 값으로 바꾼다 (예: 인자 재작성/최소화).
    """

    allow: bool = True
    reason: str | None = None
    args: dict | None = None

    @classmethod
    def deny(cls, reason: str) -> "Decision":
        return cls(allow=False, reason=reason)


class ToolGate:
    """방어 변형이 구현하는 훅. 기본 구현은 모두 허용하고 아무것도 기록하지 않는다."""

    name: str = "gate"

    def reset(self, extra_args: dict) -> None:
        """태스크 시작 시 상태 초기화용. GatedToolsExecutor 가 첫 호출 때 한 번 부른다."""

    def decide(self, tool_call: FunctionCall, messages: Sequence[ChatMessage], extra_args: dict) -> Decision:
        return Decision()

    def observe(
        self,
        tool_call: FunctionCall,
        result: FunctionReturnType,
        error: str | None,
        extra_args: dict,
    ) -> None:
        """툴 실행 결과를 관찰한다 (레이블 부착, 출처 인덱스 갱신 등)."""

    def format_output(self, tool_call: FunctionCall, formatted: str, extra_args: dict) -> str:
        """모델에게 보여줄 툴 결과 문자열을 변형한다 (예: 구분자/nonce 감싸기)."""
        return formatted


class AllowAllGate(ToolGate):
    name = "passthrough"


@dataclass
class DenyToolsGate(ToolGate):
    """툴 이름 목록만으로 차단하는 데모 게이트 (훅 동작 확인용)."""

    denied: set[str] = field(default_factory=set)
    name: str = "deny_tools"

    def decide(self, tool_call: FunctionCall, messages: Sequence[ChatMessage], extra_args: dict) -> Decision:
        if tool_call.function in self.denied:
            return Decision.deny(f"tool '{tool_call.function}' is not allowed by policy")
        return Decision()


class GatedToolsExecutor(ToolsExecutor):
    """`ToolsExecutor` 와 동일하되 실행 직전에 `gate.decide`, 직후에 `gate.observe` 를 부른다."""

    def __init__(
        self,
        gate: ToolGate,
        tool_output_formatter: Callable[[FunctionReturnType], str] = tool_result_to_str,
        blocked_prefix: str = "Blocked by policy: ",
    ) -> None:
        super().__init__(tool_output_formatter)
        self.gate = gate
        self.blocked_prefix = blocked_prefix

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = [],
        extra_args: dict = {},
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict]:
        if len(messages) == 0:
            return query, runtime, env, messages, extra_args
        if messages[-1]["role"] != "assistant":
            return query, runtime, env, messages, extra_args
        if messages[-1]["tool_calls"] is None or len(messages[-1]["tool_calls"]) == 0:
            return query, runtime, env, messages, extra_args

        if not extra_args.get("_gate_initialized"):
            self.gate.reset(extra_args)
            extra_args["_gate_initialized"] = True
        stats = extra_args.setdefault("gate_stats", {"calls": 0, "blocked": 0})

        tool_call_results = []
        for tool_call in messages[-1]["tool_calls"]:
            if tool_call.function == EMPTY_FUNCTION_NAME:
                tool_call_results.append(
                    ChatToolResultMessage(
                        role="tool",
                        content=[text_content_block_from_string("")],
                        tool_call_id=tool_call.id,
                        tool_call=tool_call,
                        error="Empty function name provided. Provide a valid function name.",
                    )
                )
                continue
            if tool_call.function not in (tool.name for tool in runtime.functions.values()):
                tool_call_results.append(
                    ChatToolResultMessage(
                        role="tool",
                        content=[text_content_block_from_string("")],
                        tool_call_id=tool_call.id,
                        tool_call=tool_call,
                        error=f"Invalid tool {tool_call.function} provided.",
                    )
                )
                continue

            for arg_k, arg_v in tool_call.args.items():
                if isinstance(arg_v, str) and is_string_list(arg_v):
                    tool_call.args[arg_k] = literal_eval(arg_v)

            stats["calls"] += 1
            decision = self.gate.decide(tool_call, messages, extra_args)
            if not decision.allow:
                stats["blocked"] += 1
                tool_call_results.append(
                    ChatToolResultMessage(
                        role="tool",
                        content=[text_content_block_from_string("")],
                        tool_call_id=tool_call.id,
                        tool_call=tool_call,
                        error=f"{self.blocked_prefix}{decision.reason or 'denied'}",
                    )
                )
                continue
            if decision.args is not None:
                tool_call.args = decision.args

            tool_call_result, error = runtime.run_function(env, tool_call.function, tool_call.args)
            self.gate.observe(tool_call, tool_call_result, error, extra_args)
            formatted = self.output_formatter(tool_call_result)
            formatted = self.gate.format_output(tool_call, formatted, extra_args)
            tool_call_results.append(
                ChatToolResultMessage(
                    role="tool",
                    content=[text_content_block_from_string(formatted)],
                    tool_call_id=tool_call.id,
                    tool_call=tool_call,
                    error=error,
                )
            )
        return query, runtime, env, [*messages, *tool_call_results], extra_args
