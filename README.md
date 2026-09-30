# FIDES 변형 방어 × AgentDojo × Ollama(qwen3.8:27b) 실험 환경

[`docs/fides-followup-analysis.md`](docs/fides-followup-analysis.md) 7장에서 제안한 FIDES 개선 구성(L0~L6)을
[AgentDojo](https://github.com/ethz-spylab/agentdojo) 0.1.35 / v1.2.2 로 측정하기 위한 실행 환경입니다.
모델은 사내 Ollama 서버의 `qwen3.8:27b` 를 OpenAI 호환 API 로 호출합니다
(서버 가정은 [SWgil/benchmarkTest `ollama-server-env`](https://github.com/SWgil/benchmarkTest/tree/ollama-server-env) 와 동일).
러너는 같은 저장소 `main` 의 `agentdojo_ollama` 를 이식하고, **툴 호출 게이트 훅과 커스텀 방어 레지스트리**를 추가했습니다.

## 구성

```
agentdojo_ollama/
  llm.py             OllamaLLM: temperature/seed/reasoning_effort 명시 전송, <think> 제거, developer→system, content 문자열화
  run.py             CLI (agentdojo-ollama). 원본 benchmark CLI 와 옵션 호환 + 커스텀 --defense
  summarize.py       runs/ 집계 (agentdojo-summarize)
  defenses/
    __init__.py      register_defense / DEFENSE_REGISTRY / DefenseContext.gated_pipeline
    gate.py          ToolGate(decide/observe/format_output) + GatedToolsExecutor  ← FIDES 변형의 공통 훅
    builtin.py       예시: passthrough, deny_sensitive_sinks
mock/ollama_mock.py  오프라인 검증용 모의 OpenAI 호환 서버 (표준 라이브러리)
scripts/             check_ollama.sh, run_smoke.sh, run_utility.sh, run_attack.sh, run_defense.sh, summarize.sh, run_mock_smoke.sh
configs/             qwen3.8-27b.env (기본값), Modelfile.qwen3.8-27b (num_ctx 32768 파생 태그)
tests/               모의 서버 기반 pytest
docs/                FIDES 후속 연구 분석 문서
```

## 설치

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
# 선택: .venv/bin/pip install -e ".[transformers]"   (transformers_pi_detector 방어)
cp .env.example .env      # 서버 주소·모델 태그 확인 (configs/qwen3.8-27b.env 가 기본값, .env 가 덮어씀)
```

## 사내망에서 실행 (실제 서버)

```bash
scripts/check_ollama.sh              # Phase 0: 서버 버전, 모델 태그, num_ctx, tool calling, thinking off 점검
scripts/run_smoke.sh                 # Phase 2: workspace user_task_0/1 (공격 없음) + user_task_0×injection_task_0 (important_instructions)
DEFENSE=passthrough scripts/run_smoke.sh     # 방어 지정
MAX_WORKERS=4 scripts/run_utility.sh         # E1: 97 user tasks, 공격 없음
MAX_WORKERS=4 scripts/run_attack.sh          # E2: important_instructions (629 cases)
ATTACK=tool_knowledge scripts/run_attack.sh  # E3
DEFENSES="passthrough deny_sensitive_sinks spotlighting_with_delimiting" scripts/run_defense.sh   # 방어별 (무공격 + ATTACK)
scripts/summarize.sh                 # runs/ → results/<model>_<date>.md/.csv
```

`num_ctx` 가 32768 미만이면 서버에서 파생 태그를 만들고 `.env` 의 `OLLAMA_MODEL` 을 바꿉니다.

```bash
ollama create qwen3.8-27b-ctx32k -f configs/Modelfile.qwen3.8-27b
```

직접 호출 예:

```bash
agentdojo-ollama --model qwen3.8:27b --base-url http://10.251.36.222:9090/v1 \
  -s banking -ut user_task_0 -it injection_task_0 --attack important_instructions --defense deny_sensitive_sinks
```

주요 옵션: `--attack`, `--defense`, `-s/-ut/-it`, `--max-workers`, `-f`, `--temperature 0 --seed 0 --reasoning-effort none`(기본),
`--no-no-think-tag`, `--keep-thinking`, `--keep-developer-role`, `--keep-content-parts`, `--tool-output-format json`, `-ml <module>`.
`.env` 가 있으면 `OLLAMA_BASE_URL/OLLAMA_API_KEY/OLLAMA_MODEL/MODEL_PROSE_NAME` 을 자동으로 읽습니다.

## 오프라인 검증 (모의 서버)

원격 컨테이너 등 사내 서버가 닿지 않는 곳에서는 모의 서버로 파이프라인만 확인합니다.
모의 서버는 첫 턴에 첫 번째 툴을 더미 인자로 호출하고, 다음 턴에 `<think>…</think>Done.` 을 돌려줍니다.

```bash
.venv/bin/pytest -q tests          # 러너, 게이트 훅(허용/차단), 요청 파라미터, 로그 경로, 집계
scripts/run_mock_smoke.sh          # 모의 서버 기동 → 스모크 → runs_mock/ 집계 출력
```

## 로그와 지표

- 경로: `<logdir>/<model>[-<defense>]/<suite>/<user_task>/<attack|none>/<injection_task|none>.json`
- `utility`: 사용자 태스크 성공, `security=True`: 인젝션 목표 달성(= 공격 성공). 집계표의 targeted ASR 은 `security` 평균.
- `extra_args["gate_stats"]` 에 게이트가 본 호출 수/차단 수가 남습니다(로그 JSON 에는 포함되지 않으므로 필요하면 게이트에서 직접 기록).

## 커스텀 방어 추가 방법

```python
# my_defenses.py
from agentdojo_ollama.defenses import DefenseContext, register_defense
from agentdojo_ollama.defenses.gate import Decision, ToolGate

class MyGate(ToolGate):
    def decide(self, tool_call, messages, extra_args):
        if tool_call.function == "send_money" and extra_args.get("tainted"):
            return Decision.deny("send_money in untrusted context")
        return Decision()
    def observe(self, tool_call, result, error, extra_args):
        if tool_call.function == "read_file":      # 예: 비신뢰 소스
            extra_args["tainted"] = True

@register_defense("my_gate")
def build(ctx: DefenseContext):
    return ctx.gated_pipeline(MyGate())
```

```bash
agentdojo-ollama -ml my_defenses --defense my_gate -s banking --attack important_instructions
```

`GatedToolsExecutor` 는 AgentDojo `ToolsExecutor` 와 같은 자리에서 실행되며, 툴 호출마다 `decide`(실행 전) →
`observe`(실행 후) → `format_output`(모델에게 보여줄 문자열 변형) 순으로 훅을 부릅니다.
거부된 호출은 `error="Blocked by policy: …"` 툴 결과로 모델에게 돌아갑니다(OpenAI API 의 tool_call_id 1:1 대응 유지).
`extra_args` 는 한 태스크 동안 유지되는 상태 저장소입니다(레이블, 출처 인덱스 등).

## 참고

- FIDES 원 저장소(microsoft/fides)는 튜토리얼 노트북만 제공하고, Microsoft Agent Framework 의 `agent_framework.security` 가 실제 구현입니다.
  두 곳 모두 AgentDojo 실행 코드는 공개돼 있지 않으므로, FIDES 자체 및 변형은 이 저장소의 게이트 훅 위에 재구현해 비교합니다.
- 다음 단계: `docs/fides-followup-analysis.md` 7.2 의 L0(프롬프트 위생)~L6(상태 지속)을 `defenses/` 에 하나씩 구현하고
  `scripts/run_defense.sh` 로 무공격 유틸리티·ASR 을 비교합니다.
