#!/usr/bin/env bash
# 방어 기법별 실행: 각 방어에 대해 (공격 없음) + (ATTACK) 두 번 실행한다.
# DEFENSES 에는 AgentDojo 내장 이름과 agentdojo_ollama.defenses 에 등록된 커스텀 이름을 섞어 쓸 수 있다.
#   transformers_pi_detector 는 `pip install -e ".[transformers]"` 필요.
source "$(dirname "$0")/common.sh"
ATTACK="${ATTACK:-important_instructions}"
DEFENSES="${DEFENSES:-passthrough deny_sensitive_sinks spotlighting_with_delimiting}"
for d in $DEFENSES; do
  echo "### defense=$d (no attack)"
  $RUN $SUITE_ARGS --defense "$d" --max-workers "$MAX_WORKERS" $EXTRA_ARGS "$@"
  echo "### defense=$d attack=$ATTACK"
  $RUN $SUITE_ARGS --defense "$d" --attack "$ATTACK" --max-workers "$MAX_WORKERS" $EXTRA_ARGS "$@"
done
