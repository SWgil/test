# 저장소 작업 규칙

## 브랜치 이름

- 브랜치 이름은 작업 내용을 설명하는 `claude/<주제-kebab-case>` 형식으로 짓는다.
  예: `claude/fides-agentdojo-bench`, `claude/progent-source-analysis`
- 자동 생성 ID 만으로 된 이름(`ccr-…`, 무작위 접미사만 있는 이름)은 쓰지 않는다.
- 자동 생성 브랜치에서 작업을 시작했다면 **첫 푸시 전에** `git branch -m` 으로 의미 있는 이름으로 바꾸고,
  이미 푸시했다면 새 이름으로 푸시한 뒤 옛 원격 브랜치를 삭제한다.

## 저장소 개요

- `docs/fides-followup-analysis.md`: FIDES 후속 연구 분석과 상용 에이전트용 개선 제안(7장).
- `agentdojo_ollama/`: AgentDojo × Ollama 러너. 진입점 `agentdojo-ollama`, 집계 `agentdojo-summarize`.
  커스텀 방어(FIDES 변형)는 `agentdojo_ollama/defenses/` 의 `register_defense` 로 등록한다.
- 검증: `.venv/bin/pytest -q tests` (모의 서버), 사내망에서는 `scripts/check_ollama.sh` → `scripts/run_smoke.sh`.
