"""기본 제공 커스텀 방어 (훅 동작 확인용 예시).

- passthrough: 모두 허용. 원본 파이프라인과 동일하게 동작해야 한다 (게이트 오버헤드/정합성 확인).
- deny_sensitive_sinks: AgentDojo 4개 suite 의 대표적 외부 전송/결제 툴을 이름만으로 차단.
  FIDES 의 "③ 비가역 툴은 신뢰 컨텍스트에서만" 을 극단적으로 단순화한 하한 기준선이다.
"""

from __future__ import annotations

from agentdojo.agent_pipeline.agent_pipeline import AgentPipeline

from agentdojo_ollama.defenses import DefenseContext, register_defense
from agentdojo_ollama.defenses.gate import AllowAllGate, DenyToolsGate

SENSITIVE_SINKS = {
    # workspace
    "send_email",
    # slack
    "send_direct_message",
    "send_channel_message",
    "invite_user_to_slack",
    "post_webpage",
    # banking
    "send_money",
    "schedule_transaction",
    "update_scheduled_transaction",
    "update_password",
    "update_user_info",
    # travel
    "reserve_hotel",
    "reserve_restaurant",
    "reserve_car_rental",
}


@register_defense("passthrough")
def build_passthrough(ctx: DefenseContext) -> AgentPipeline:
    return ctx.gated_pipeline(AllowAllGate())


@register_defense("deny_sensitive_sinks")
def build_deny_sensitive_sinks(ctx: DefenseContext) -> AgentPipeline:
    return ctx.gated_pipeline(DenyToolsGate(denied=set(SENSITIVE_SINKS)))
