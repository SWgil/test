#!/usr/bin/env bash
# Phase 3 E1: 공격 없이 전체 suite 유틸리티 (97 user tasks). DEFENSE=<name> 으로 방어 적용.
source "$(dirname "$0")/common.sh"
DEFENSE_ARGS=""; [[ -n "${DEFENSE:-}" ]] && DEFENSE_ARGS="--defense $DEFENSE"
$RUN $SUITE_ARGS $DEFENSE_ARGS --max-workers "$MAX_WORKERS" $EXTRA_ARGS "$@"
