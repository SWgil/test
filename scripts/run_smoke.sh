#!/usr/bin/env bash
# Phase 2: 스모크 테스트. 첫 suite 태스크 2개(공격 없음) + 1개(공격 있음). DEFENSE=passthrough 등으로 방어 지정 가능.
source "$(dirname "$0")/common.sh"
SMOKE_SUITE="${SMOKE_SUITE:-$(echo $SUITES | cut -d' ' -f1)}"
DEFENSE_ARGS=""; [[ -n "${DEFENSE:-}" ]] && DEFENSE_ARGS="--defense $DEFENSE"
$RUN -s "$SMOKE_SUITE" -ut user_task_0 -ut user_task_1 $DEFENSE_ARGS $EXTRA_ARGS
$RUN -s "$SMOKE_SUITE" -ut user_task_0 -it injection_task_0 --attack important_instructions $DEFENSE_ARGS $EXTRA_ARGS
echo "로그: $LOGDIR/"
