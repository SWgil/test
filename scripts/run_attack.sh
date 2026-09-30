#!/usr/bin/env bash
# Phase 3 E2/E3: 공격 실행. 기본 important_instructions (629 cases). ATTACK=tool_knowledge, DEFENSE=<name> 으로 변경.
source "$(dirname "$0")/common.sh"
ATTACK="${ATTACK:-important_instructions}"
DEFENSE_ARGS=""; [[ -n "${DEFENSE:-}" ]] && DEFENSE_ARGS="--defense $DEFENSE"
$RUN $SUITE_ARGS --attack "$ATTACK" $DEFENSE_ARGS --max-workers "$MAX_WORKERS" $EXTRA_ARGS "$@"
