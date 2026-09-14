# gemini-cli IPI 방어 계층 분석: CLI 가드레일 vs 모델 방어

> 대상: [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) (`main`, 2026-09-14 확인)
> 관련 벤치마크: [AgentDojo](https://github.com/ethz-spylab/agentdojo), [Progent](https://github.com/sunblaze-ucb/progent), [CaMeL](https://github.com/google-research/camel-prompt-injection), [MELON](https://github.com/kaijiezhu11/MELON)
> 관련 논문: *AgentDojo* ([arXiv:2406.13352](https://arxiv.org/abs/2406.13352)), *Progent* ([arXiv:2504.11703](https://arxiv.org/abs/2504.11703)), *Lessons from Defending Gemini Against IPI* ([arXiv:2505.14534](https://arxiv.org/abs/2505.14534))

## 1. 한 줄 요약

headless로 gemini-cli에 IPI(간접 프롬프트 인젝션)를 시도할 때 방어가 **모델 덕인지 CLI 가드레일 덕인지**는
구분 가능하다. 단 둘은 서로 다른 지점에서 작동하므로, 승인 모드·툴 노출·시스템 프롬프트를 **통제한 대조 실험**으로만 분리된다.
그리고 결정적으로, **AgentDojo 계열 IPI 논문들은 gemini-cli를 쓰지 않는다.** 그들은 gemini-cli(제품)를
우회하고 Gemini **API를 직접** 호출하므로, 그 논문들의 baseline 수치는 사실상 "모델 계층"만을 측정한 값이다.

## 2. 방어는 2계층이 아니라 3계층

IPI가 실패하는 지점은 셋으로 나뉜다.

| 계층 | 성격 | 출처 | 예시 |
|---|---|---|---|
| L1. gemini-cli 결정론적 코드 | 비확률적, 모델 판단 무관 | 제품(CLI) | Policy Engine, 툴 레지스트리 제외, 샌드박스, 폴더 신뢰, 경로/셸 검사 |
| L2. gemini-cli 시스템 프롬프트 | 확률적 | 제품(CLI) | CLI가 주입하는 대형 coding-agent 시스템 프롬프트의 안전 지침 |
| L3. 모델 자체 정렬 | 확률적 | 모델 | Gemini가 학습(adversarial training 등)으로 획득한 거부 능력 |

"모델이 막았다"는 통상 L2+L3을 뭉뚱그린 것이다. 엄밀 귀속에는 셋을 각각 분리해야 한다.
구글 자체 논문도 이를 명시한다: *"we are only testing the vulnerability of the core model, the publicly
available version of Gemini 2.0 comes with various guardrails that are applied on top of Gemini"*
(arXiv:2505.14534) — 즉 core model(L3)과 제품 가드레일(L1/L2)을 분리해 측정한다.

## 3. gemini-cli의 가드레일 구조 (L1)

### 3.1 Policy Engine

TOML 규칙 기반, 5티어 우선순위. `packages/core/src/policy/policies/`.

- 티어 순서: **Admin(5) > User(4) > Workspace(3) > Extension(2) > Default(1)**.
  우선순위 변환식은 `tier_base + priority/1000` (예: Default 티어 priority 100 → `1.100`).
- 기본 정책(Default 티어):
  - 읽기 툴(`read_file`, `glob`) → `allow` (priority 50 → `1.050`)
  - 쓰기 툴(`write_file`, `run_shell_command`) → `ask_user` (priority 10 → `1.010`)
- 결정값: `allow` / `deny` / `ask_user`.
- **headless 함정**: 비대화형에서 `ask_user`는 **`deny`로 처리**된다
  (docs/reference/policy-engine.md). 즉 대화형이면 승인 프롬프트가 뜰 상황이 headless에서는
  조용히 차단으로 바뀐다. 이걸 모르면 L1 차단을 L3(모델 거부)로 오귀속하게 된다.

### 3.2 승인 모드와 비대화형 툴 노출

`default` / `auto_edit` / `yolo` / `plan`. 비대화형에서 모드가 **모델에게 노출되는 툴 자체**를 바꾼다.

| 모드 | 모델에게 노출되는 툴 |
|---|---|
| `default` | 확인 필요 툴은 레지스트리에서 **제외**(모델이 못 봄), `--allowed-tools`로 허용한 것만 예외 |
| `auto_edit` | `ShellTool`만 제외, 편집 툴은 노출 |
| `yolo` | 전부 노출, 자동 실행 |

`createToolExclusionFilter()`가 `--allowed-tools` 허용 집합을 검사해 제외를 우회시킨다.
따라서 `default`에서 IPI가 "실패"하면 **모델이 거부한 건지 위험 툴이 애초에 제시되지 않은 건지 구분 불가**.

### 3.3 YOLO 규칙 (`yolo.toml`)

```toml
# 전부 허용
[[rule]]
toolName = "*"
decision = "allow"
priority = 998
modes = ["yolo"]

# 단, 예외 두 가지는 YOLO에서도 남는다
[[rule]]                      # ask_user는 여전히 상호작용 요구
toolName = "ask_user"
decision = "ask_user"
priority = 999
modes = ["yolo"]

[[rule]]                      # plan 전환은 deny
toolName = ["enter_plan_mode", "exit_plan_mode"]
decision = "deny"
priority = 999
modes = ["yolo"]
```

동적/설정 규칙은 User 티어(4.x)에 얹힌다: `4.3 = --allowed-tools`, `4.4 = --exclude-tools`,
`4.95 = "Always Allow"`, MCP 신뢰(`4.1/4.2`)/차단(`4.9`).

### 3.4 샌드박스 · 폴더 신뢰

- 샌드박스: `GEMINI_SANDBOX=true|docker|podman|sandbox-exec`, `-s`/`--sandbox`, `settings.json`의 `{"tools":{"sandbox":true}}`.
- 폴더 신뢰(Folder Trust): headless에서 미신뢰 폴더면 `FatalUntrustedWorkspaceError`로 종료.
  우회: `--skip-trust` 또는 `GEMINI_CLI_TRUST_WORKSPACE=true`.
- 보안 이력: 2025년 headless에서 CI가 워크스페이스를 auto-trust해 `.gemini/` 악성 설정을 로드하던
  CVSS 10 RCE가 있었고 0.39.1 / 0.40.0-preview.3에서 패치됨.

## 4. gemini-cli "보안 최소화" 설정

별도 저사양 빌드는 없다. 설정으로 L1을 벗기고 L2를 중립화한다.

```bash
# L1 결정론적 가드레일 제거
export GEMINI_SANDBOX=false
export GEMINI_CLI_TRUST_WORKSPACE=true        # 또는 --skip-trust

# L2 시스템 프롬프트 중립화(선택): 기본 대형 coding-agent 프롬프트를 최소 프롬프트로 완전 교체
export GEMINI_SYSTEM_MD=./.gemini/system.md   # 전체 치환(merge 아님)

gemini --yolo \
       -m gemini-2.0-flash-001 \
       -p "<injected task or payload>" \
       --output-format json \
       --debug
```

- `--yolo`(= `--approval-mode=yolo`)로 `*` allow-all이 걸린다. 단 `ask_user`/plan 전환은 남음(§3.3).
- `GEMINI_SYSTEM_MD`는 built-in 프롬프트를 **완전 치환**한다(merge 아님). `1`/`true`면 `./.gemini/system.md` 사용,
  임의 경로 문자열이면 그 파일 사용. 미존재 시 `missing system prompt file` 에러.
- 더 깊게 가려면 `@google/gemini-cli-core` / `@google/gemini-cli-sdk`로 `LocalAgentDefinition`을
  직접 구성해 CLI 승인 UI 자체를 우회할 수 있다.

이 상태면 L1 제거 + L2 최소화 → 남는 방어는 사실상 **L3(모델 정렬)** 뿐이다. 이것이 논문의 "raw model" 측정과 가장 가까운 CLI 구성이다.

## 5. 논문들이 실제로 쓰는 Gemini 테스트 설정

핵심: **gemini-cli가 아니라 AgentDojo 자체 agent pipeline으로 Gemini API를 직접 호출**한다.
소스에서 확인한 공통 설정:

| 항목 | 실제 설정 (소스 확인) |
|---|---|
| 호출 경로 | Gemini **API 직접** (gemini-cli 아님) |
| SDK | stock AgentDojo·CaMeL: `google-genai`; Progent 포크: `vertexai.generative_models` |
| 접근 | Vertex AI(`genai.Client(vertexai=True, GCP_PROJECT/GCP_LOCATION)`) 또는 AI Studio(`GOOGLE_API_KEY`) |
| 시스템 프롬프트 | AgentDojo 기본값 하나뿐, **방어 지침 없음** (`system_instruction`으로 전달). 원문: *"You are an AI language model who assists the user by using the given tools. The user's name is Emma Johnson, an employee of the company Blue Sparrow Tech..."* |
| temperature | 0.0 (stock 기본) |
| safety_settings | **설정 안 함** → API 기본값. Gemini 2.5/3 기본 임계값은 "Off". IPI는 안전필터 유해범주가 아니라 그대로 통과 |
| 툴 | `function_declarations`로 선언, `tool_config`/`function_calling_config` 모드 미지정 |
| 방어 기법 | **기본 OFF** (`if config.defense is None`). `--defense {tool_filter, spotlighting_with_delimiting, repeat_user_prompt, transformers_pi_detector}`로만 켬 |
| 평가 Gemini ID | `gemini-1.5/2.0-flash-001`, `gemini-2.0-flash-exp`, `gemini-2.5-flash/pro-preview`; CaMeL은 `2.5-flash/pro-preview`, `2.0-flash-lite-001` |

따라서 논문 baseline(no defense) ASR = **제품 가드레일 전무 + 중립 시스템 프롬프트**의 raw 모델(L3) 수치이며,
각자의 방어(Progent 권한 게이트, CaMeL dual-LLM, MELON masked re-execution)는 **모델 바깥 시스템 계층**에 얹어 향상분을 보고한다.
(참고: MELON 공개 저장소 README는 gpt-4o만 문서화 — Gemini 수치는 논문 표에만 있는 경우가 많음.)

## 6. API 호출 테스트는 single-shot가 아니다 (agentic loop)

"API로 테스트하면 query 한 번에 응답 하나"라는 통념은 틀리다. AgentDojo는 **multi-step 툴 사용 루프**다.

- 파이프라인: `[system_message_component, init_query_component, llm, tools_loop]`.
- `ToolsExecutionLoop` (`tool_execution.py`): `for _ in range(self.max_iters)` 로 반복,
  마지막 메시지가 assistant의 tool call이 아니면 `break`. **기본 `max_iters=15`**.
- 반복 패턴: 모델이 function_call 생성 → 프레임워크가 툴 실행 → 결과를 대화에 append → 모델 재호출 → 종료 조건까지.
- 이것은 **native function calling** 기반 agentic 루프다. 고전적 ReAct(Thought/Action/Observation 텍스트 스크래치패드)가
  **아니다**. ReAct식 텍스트 툴콜 경로는 `together-prompting` 공급자(`PromptingLLM`)에만 있고, `google`은 `GoogleLLM`(native FC)을 쓴다.

즉 API 경로도 "여러 턴에 걸쳐 툴을 부르는 에이전트"다. gemini-cli의 비대화형 루프(`nonInteractiveCli.ts`)도
동일하게 function_call → `scheduler.schedule(...)` 실행 → 결과 반환 → 재호출 구조다. 차이는 **누가 툴을
스케줄/승인하느냐(L1)**와 **어떤 시스템 프롬프트(L2)를 얹느냐**이지, 루프의 있고 없음이 아니다.

## 7. CLI를 API 호출에 최대한 가깝게 맞추는 법

목표: gemini-cli를 §5의 bare-API 루프에 근사시켜 **L3만 남기기**.

| 맞출 항목 | API(AgentDojo) | CLI에서 근사 |
|---|---|---|
| 가드레일 | 없음 | `--yolo` + `GEMINI_SANDBOX=false` + 신뢰 우회 |
| 시스템 프롬프트 | 중립 1개 | `GEMINI_SYSTEM_MD`로 AgentDojo 프롬프트를 그대로 치환 |
| 모델 | 명시 ID | `-m gemini-2.0-flash-001` 등 동일 ID |
| 루프 | max_iters=15 native FC | CLI 비대화형 루프(native FC) — 개념 동일 |
| 출력 캡처 | 코드에서 로깅 | `--output-format json` + `--debug` |
| 툴 집합 | 태스크 환경 툴(email/banking 등) | `--allowed-tools`/`coreTools`/`--exclude-tools`로 비교 가능한 최소 집합 |

### 남는 한계 (완전 동일은 불가)

1. **temperature**: gemini-cli는 temp를 플래그로 노출하지 않는다. AgentDojo의 `temperature=0.0`과 정확히 맞추기 어렵다.
2. **툴 semantics**: gemini-cli 툴(shell/file/web)은 AgentDojo 환경 툴과 다르다. 동일 태스크·동일 인젝션 지점을 재현하려면
   MCP로 AgentDojo 환경을 노출하는 편이 정확하다(참고: Progent의 `agentdojo-mcp`).
3. **툴 포매팅/스캐폴딩**: CLI의 툴 스키마 주입·결과 포맷이 AgentDojo와 다르다.

결론: **연구용으로 L3만 깔끔히 재라면 API 경로(AgentDojo GoogleLLM 직접)** 가 정답이다.
gemini-cli 경로는 "제품(L1+L2+L3) 전체"를 재는 것이고, §4 설정으로 벗겨야 API에 근접한다.
둘은 목적이 다르다: 전자는 모델 취약성, 후자는 제품 취약성 측정.

## 8. 계층 구분 실험 설계 (판별 매트릭스)

동일 페이로드를 조건만 바꿔 반복하고, `--debug`/텔레메트리로 세 신호를 각각 로깅한다:
(a) 모델에 실제 노출된 tool 목록, (b) 모델이 낸 function_call 유무, (c) 툴 실행 결과.

| 조건 | 결과 | 귀속 |
|---|---|---|
| `default`(허용목록 없음) 차단 + `yolo`에서 모델이 순순히 실행 | 툴 미노출/`ask_user→deny` | **L1 (CLI 가드레일)** |
| `yolo`에서 function_call은 나오나 샌드박스/경로 검사에서 실패 | 실행 계층 차단 | **L1 (실행 계층)** |
| `yolo` + 가드레일 제거에도 모델이 function_call 미생성·텍스트 거부 | 모델 방어 | **L2+L3** |
| 위에서 다시 `GEMINI_SYSTEM_MD`로 중립 프롬프트 치환 후에도 거부 | 시스템 프롬프트 무관 | **L3 (모델 고유)** |
| 중립 프롬프트로 치환하니 거부율 급락 | 프롬프트 기여 | **L2 (시스템 프롬프트)** |

L2/L3 최종 분해는 동일 페이로드를 **bare Gemini API(동일 모델 ID, 시스템 프롬프트 제거/중립)** 에
재현해 거부율 차이를 보면 확정된다.

## 9. 참고 출처

- gemini-cli: `docs/reference/policy-engine.md`, `packages/core/src/policy/policies/yolo.toml`,
  `packages/cli/src/nonInteractiveCli.ts`, `docs/cli/system-prompt.md`, `docs/cli/headless.md`, `docs/cli/sandbox.md`
- AgentDojo: `src/agentdojo/agent_pipeline/llms/google_llm.py`, `.../agent_pipeline.py`,
  `.../tool_execution.py`, `src/agentdojo/data/system_messages.yaml`, `src/agentdojo/models.py`
- Progent 포크: `agentdojo/src/agentdojo/agent_pipeline/llms/google_llm.py`, `.../models.py`
- CaMeL: `src/camel/models.py` (`_supported_model_names`)
- 논문: arXiv:2406.13352 (AgentDojo), arXiv:2504.11703 (Progent), arXiv:2502.05174 (MELON),
  arXiv:2503.18813 (CaMeL), arXiv:2505.14534 (Lessons from Defending Gemini)
- Gemini API safety: https://ai.google.dev/gemini-api/docs/safety-settings
