"""커스텀 방어 레지스트리.

`--defense <name>` 이 AgentDojo 내장 4개(tool_filter, transformers_pi_detector,
spotlighting_with_delimiting, repeat_user_prompt)면 `AgentPipeline.from_config` 에 위임하고,
여기 등록된 이름이면 등록 함수가 파이프라인을 조립한다.

등록 예:

    from agentdojo_ollama.defenses import register_defense, DefenseContext
    from agentdojo_ollama.defenses.gate import GatedToolsExecutor, ToolGate

    @register_defense("my_gate")
    def build(ctx: DefenseContext) -> AgentPipeline:
        return ctx.gated_pipeline(MyGate())

외부 모듈은 `agentdojo-ollama -ml my_package.my_defense` 로 로드하면 등록된다.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial

from agentdojo.agent_pipeline.agent_pipeline import DEFENSES, AgentPipeline, PipelineConfig
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.agent_pipeline.basic_elements import InitQuery, SystemMessage
from agentdojo.agent_pipeline.tool_execution import ToolsExecutionLoop, tool_result_to_str

from agentdojo_ollama.defenses.gate import GatedToolsExecutor, ToolGate

BUILTIN_DEFENSES: tuple[str, ...] = tuple(DEFENSES)


@dataclass
class DefenseContext:
    """방어 조립에 필요한 재료."""

    model: str
    llm: BasePipelineElement
    system_message: str
    tool_output_format: str = "yaml"
    max_iters: int = 15
    extra: dict = field(default_factory=dict)

    @property
    def tool_output_formatter(self) -> Callable:
        if self.tool_output_format == "json":
            return partial(tool_result_to_str, dump_fn=json.dumps)
        return tool_result_to_str

    def gated_pipeline(
        self,
        gate: ToolGate,
        system_message: str | None = None,
        extra_loop_elements: list[BasePipelineElement] | None = None,
    ) -> AgentPipeline:
        """`[System, InitQuery, llm, Loop([GatedToolsExecutor, *extra, llm])]` 표준 조립."""
        loop_elements: list[BasePipelineElement] = [GatedToolsExecutor(gate, self.tool_output_formatter)]
        loop_elements += extra_loop_elements or []
        loop_elements.append(self.llm)
        tools_loop = ToolsExecutionLoop(loop_elements, max_iters=self.max_iters)
        return AgentPipeline(
            [SystemMessage(system_message or self.system_message), InitQuery(), self.llm, tools_loop]
        )


DefenseBuilder = Callable[[DefenseContext], AgentPipeline]
DEFENSE_REGISTRY: dict[str, DefenseBuilder] = {}


def register_defense(name: str) -> Callable[[DefenseBuilder], DefenseBuilder]:
    if name in BUILTIN_DEFENSES:
        raise ValueError(f"'{name}' is an AgentDojo built-in defense name")

    def deco(fn: DefenseBuilder) -> DefenseBuilder:
        DEFENSE_REGISTRY[name] = fn
        return fn

    return deco


def available_defenses() -> list[str]:
    return list(BUILTIN_DEFENSES) + sorted(DEFENSE_REGISTRY)


def build_pipeline(ctx: DefenseContext, defense: str | None) -> AgentPipeline:
    """defense 이름에 따라 파이프라인을 만들고 이름을 `<model>[-<defense>]` 로 맞춘다."""
    if defense is None or defense in BUILTIN_DEFENSES:
        config = PipelineConfig(
            llm=ctx.llm,
            model_id=ctx.model,
            defense=defense,
            system_message_name=None,
            system_message=ctx.system_message,
            tool_output_format=ctx.tool_output_format,
        )
        pipeline = AgentPipeline.from_config(config)
    elif defense in DEFENSE_REGISTRY:
        pipeline = DEFENSE_REGISTRY[defense](ctx)
    else:
        raise ValueError(f"Unknown defense '{defense}'. Available: {available_defenses()}")
    pipeline.name = ctx.model if defense is None else f"{ctx.model}-{defense}"
    return pipeline


# 기본 제공 방어 등록 (import 부수효과)
from agentdojo_ollama.defenses import builtin as _builtin  # noqa: E402,F401
