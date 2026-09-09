# Progent 소스 코드 분석

> 대상: [sunblaze-ucb/progent](https://github.com/sunblaze-ucb/progent) (commit `8a8eb89`, 2026-05-13)
> 논문: *Progent: Securing AI Agents with Privilege Control* — [arXiv:2504.11703](https://arxiv.org/abs/2504.11703)

## 1. 한 줄 요약

Progent는 LLM 에이전트의 **툴 호출 단계에 최소 권한(least privilege) 정책을 강제하는 게이트**다.
모델을 고치거나 프롬프트 인젝션을 "탐지"하지 않고, "이 사용자 요청을 수행하는 데 꼭 필요한 툴 호출인가"를
JSON Schema 기반 정책으로 판정해 차단한다. 정책 자체도 LLM이 사용자 질의로부터 자동 생성/갱신한다.

## 2. 저장소 구조

| 경로 | 역할 |
|---|---|
| `secagent/` | **핵심 라이브러리** (약 2,700 LOC). PyPI 패키지명도 `secagent` |
| `agentdojo/` | AgentDojo 벤치마크 포크 (Progent 훅 삽입) |
| `agentdojo-mcp/` | AgentDojo 환경을 MCP 서버로 노출 |
| `asb/` | Agent Security Bench 포크 (AIOS/pyopenagi 기반) |
| `real-world-agents/` | LangChain / OpenAI Agents SDK / AutoGen / OpenHands 통합 실험 |

`secagent/` 내부:

| 파일 | LOC | 역할 |
|---|---|---|
| `tool.py` | 770 | 정책 저장소, 정책 생성/갱신 LLM 프롬프트, **집행 엔진**, 프레임워크 래퍼 |
| `role_analyzer.py` | 900 | 정규식 → Z3 표현식 변환 (Teleport `rbac-linter`에서 가져옴) |
| `policy_analysis.py` | 441 | JSON Schema → Z3 제약. 정책 충돌 검사 / 부분집합(축소) 검증 |
| `progent_proxy.py` | 363 | MCP 프록시 + OpenAI API 프록시 (코드 수정 없는 통합 경로) |
| `policy_type_check.py` | 130 | 정책의 타입/스키마 정합성 린팅 |
| `mcp_proxy.py` | 57 | GitHub Copilot MCP 대상 최소 예제 |
| `utils.py` | 43 | LLM 응답에서 JSON 추출 |

## 3. 정책 모델 (핵심 자료구조)

`tool.py`의 전역 `security_policy` 하나가 전부다.

```python
security_policy = {
    "tool_name": [
        (priority, effect, condition, fallback),
        ...
    ]
}
```

- **priority** — 낮을수록 먼저 평가. `sort_policy()`가 `(priority, -effect)`로 정렬해
  같은 우선순위면 **deny(1)가 allow(0)보다 앞**에 온다.
  `1` = 사람이 손으로 쓴 정책, `100` = LLM이 생성한 정책(리셋 대상).
- **effect** — `0` = allow, `1` = forbid
- **condition** — `{인자명: JSON Schema}`. 인자별 `enum`/`pattern`/`minimum`/`maxLength` 등
- **fallback** — 매칭 실패 시 동작: `0` = 에러 메시지 반환, `1` = `sys.exit()`(종료), `2` = 사람에게 y/N 확인

정책 문법이 곧 "특권 정의"라서, 사람이 쓴 규칙과 LLM이 만든 규칙이 우선순위 숫자만으로 공존한다.
`reset_security_policy()`는 기본적으로 priority 100짜리(생성분)만 지운다.

## 4. 집행(enforcement) 경로 — `check_tool_call`

`tool.py:521 _check_tool_call` / `tool.py:573 check_tool_call`

1. 툴 이름이 정책에 아예 없으면 → **거부** (기본 deny)
2. 정책 리스트를 우선순위 순으로 훑는다.
   - `effect == 0`(allow): condition의 모든 인자가 스키마를 통과하면 **즉시 허용 후 return**
   - `effect == 1`(forbid): 조건이 매칭되면 fallback 실행 (거부/종료/사용자 확인)
3. 어떤 규칙도 매칭 안 되면 **기본 거부**
4. 모든 예외는 `ValidationError`로 감싸져
   `"...Please try other tools or arguments and continue to finish the user task: {init_user_query}"`
   라는 메시지로 에이전트에게 되돌아간다 → 에이전트가 죽지 않고 재시도하게 만드는 설계

인자 검사는 `check_arg`(`tool.py:508`)에서 세 형태를 지원한다: JSON Schema(dict), 정규식(str), 파이썬 콜러블.

한 가지 중요한 특성: **호출에 없는 인자에는 제약이 적용되지 않는다** (`if arg_name in kwargs`).
선택적 인자를 생략하는 방식으로는 제약을 우회할 수 없지만, 정책이 "인자가 반드시 존재해야 함"을 요구할 수는 없다.

## 5. 정책 자동 생성 (LLM 기반)

### 5.1 초기 생성 — `generate_security_policy(query)`

입력: `TOOLS: [...스키마...]` + `USER_QUERY: ...` → 출력: 툴별 JSON Schema 제약 배열.

시스템 프롬프트(`SYS_PROMPT`, `tool.py:266`)의 핵심 규칙:
- 질의와 무관한 툴은 목록에서 **제거**한다 (= 그 툴은 호출 불가)
- 질의에서 명시적으로 확인되는 값에만 제약을 건다
- **"사용자 질의에서 찾을 수 없는 정보는 절대 쓰지 마라"** — 모델이 계좌번호/이메일을 환각으로
  채워 넣어 공격자 값이 허용되는 것을 막는 가장 중요한 규칙
- 날짜/시간은 추측 금지, URL은 스킴·경로를 과도하게 제한하지 말 것, 배열은 `items` 안에 제약을 둘 것

생성된 정책은 priority `100`, effect `0`으로 등록된다.

### 5.2 실행 중 갱신 — `generate_update_security_policy(param, result)`

툴 호출 **결과**를 보고 정책을 조이거나 넓힌다. 2단계다.
1. `decide_whether_to_update()` — 결과 내용 없이 "이 호출 결과가 정책 갱신에 도움이 되나?"만 Yes/No로 물어 비용 절감
2. Yes면 결과 본문까지 넣어 정책 재생성

여기가 이 설계의 **가장 민감한 지점**이다. 툴 결과는 신뢰할 수 없는 데이터(= 프롬프트 인젝션 진입점)인데
그것으로 정책을 넓힐 수 있기 때문이다. 코드가 취한 방어는 두 가지:
- 프롬프트에 "결과에 악성 데이터가 있을 수 있으니 양성 데이터만 골라 쓰라"고 명시
- 환경변수 `SECAGENT_ONLY_ALLOW_NARROW=True`면 Z3로 **새 정책 ⊆ 기존 정책**임을 증명하고, 아니면 폐기

두 번째가 진짜 방어인데 **기본값이 off**다. 실험 스크립트(`run.sh`)에서도 주석 처리되어 있다.

## 6. Z3 기반 정책 분석 — `policy_analysis.py`

JSON Schema를 Z3 제약으로 컴파일한다.
- 타입별 변수: `String`/`Int`/`Real`/`Bool`, `null`용 대수적 자료형,
  그리고 배열용 `ArrayWrapper_*`(`Array(Int, T)` + `len` 필드) 5종
- `pattern`은 `role_analyzer.regex_to_z3_expr`로 정규식 → Z3 정규 표현으로 변환
  (`sre_parse` AST를 순회하며 `Union`/`Star`/`Range`/`\d \w \s` 카테고리까지 처리)
- `anyOf`/`allOf`/`oneOf`/`not`/`if-then-else` 지원

두 가지 용도:
- `security_policy_analysis()` — 같은 툴의 두 규칙이 겹치는지 (`allOf`가 SAT이면 충돌) 경고
- `security_policy_subset_check()` — `{"allOf": [{"not": 기존}, 신규]}`가 UNSAT이면 신규 ⊆ 기존.
  SAT이면 반례 값을 출력하고 갱신을 거부

솔버 타임아웃 5초, 실패 시 타입 후보를 바꿔가며 재시도한다.

## 7. 프레임워크 통합 — 4가지 경로

Progent가 "어디에 꽂히는가"가 실질적인 설계의 절반이다.

1. **함수 래핑** — `apply_secure_tool_wrapper(tool)` (`tool.py:718`)
   docstring과 타입 힌트를 파싱해 pydantic 모델로 툴 스키마를 만들고,
   호출 시 `sig.bind()`로 인자를 정규화한 뒤 `check_tool_call`을 거친다. AgentDojo 통합에 사용.
2. **LangChain 미들웨어** — `SecAgentLangchainMiddleware.awrap_tool_call`.
   차단 시 예외 대신 `ToolMessage("Tool error: ...")`를 반환해 에이전트 루프를 유지.
3. **OpenAI Agents SDK** — `openai_agent_wrapper`가 `FunctionTool.on_invoke_tool`을 몽키패치하고,
   `get_mcp_tools`를 교체해 MCP 툴까지 잡아낸다.
4. **MCP 프록시** — `progent_proxy.py`. **에이전트 코드를 전혀 고치지 않는 경로**.
   - `ListingFilterMiddleware.on_list_tools`: 툴 목록을 가로채 정책 생성 + 역할(`agent_expert` 헤더)별 툴 필터링
   - `ToolCallFilterMiddleware.on_call_tool`: 호출 전 `check_tool_call`, 호출 후 정책 갱신
   - 동시에 FastAPI로 OpenAI API를 프록시해서 **첫 사용자 메시지를 훔쳐보고** 정책 생성 트리거

## 8. 실험 하네스

- **AgentDojo** (`agentdojo/`): banking/slack/travel/workspace 스위트.
  `basic_elements.py`의 `InitQuery`에서 정책 생성, `tool_execution.py`에서 정책 갱신,
  `benchmark.py`에서 태스크 간 정책 리셋. 스위트별 읽기 전용 툴은 `update_always_allowed_tools`로 화이트리스트.
  README에 slack injection task 5는 채점 로직 특성상 수동 보정했다고 명시.
- **ASB** (`asb/`): `react_agent_attack.py`가 툴 실행 직전 `check_tool_call(function_name, {})` —
  **인자 없이 툴 이름만 검사**한다. ASB 툴 메타데이터에 인자 스키마가 없기 때문.
  대신 ASB 전용 프롬프트(`SYS_PROMPT_ASB`)에 "공격자 툴은 이름 규칙(snake_case vs PascalCase)이 튄다"는
  휴리스틱이 들어가 있다 — 벤치마크 특성에 맞춘 것이라 일반화하기는 어려운 부분.

환경변수로 동작을 스위치한다: `ENABLE_SECAGENT`, `SECAGENT_POLICY_MODEL`, `SECAGENT_GENERATE`,
`SECAGENT_UPDATE`, `SECAGENT_SUITE`, `SECAGENT_TASK_TYPE`, `SECAGENT_ONLY_ALLOW_NARROW`,
`SECAGENT_IGNORE_UPDATE_ERROR`.

## 9. 설계 평가

**강점**
- 집행 지점이 툴 호출 하나로 좁고 명확하다. 모델을 신뢰하지 않고 결정론적으로 차단한다.
- 정책이 JSON Schema라서 사람이 읽고 쓰고 감사할 수 있고, Z3로 형식 검증까지 가능하다.
- 기본 deny + 차단 메시지를 에이전트에게 되돌려 유틸리티 손실을 줄이는 처리가 일관적이다.
- 프레임워크 침습 없이 MCP 프록시로 얹을 수 있는 경로가 있다.

**한계 / 위험 지점**
- **정책 생성이 LLM 의존**이다. 집행은 결정론적이지만 "무엇을 허용할지"는 여전히 모델이 정한다.
  질의가 모호하면 정책이 느슨해지고, 과도하게 조이면 정상 태스크가 실패한다.
- **정책 갱신이 신뢰 불가 데이터를 먹는다.** `ONLY_ALLOW_NARROW`가 꺼진 기본 설정에서는
  인젝션된 툴 결과가 정책을 넓히도록 유도할 여지가 남는다.
- **`pattern` 제약은 앵커되지 않는다.** `check_arg`의 `re.match`(부분 매치)와 jsonschema `pattern`(search 의미)
  모두 앵커가 없어, LLM이 `^...$` 없이 패턴을 만들면 접미사 삽입형 우회가 가능하다.
  (예: `pattern: "US1234"` 는 `"US1234' AND ..."` 도 통과)
- `security_policy_subset_check`는 각 툴의 `policies[0]`만 비교한다. 규칙이 여러 개인 툴에서는 불완전.
- `_check_tool_call` 말미의 기본 거부 경로가 **루프의 마지막 규칙에서 남은 `fallback` 값**을 재사용한다.
  마지막 규칙이 `fallback=1`이면 매칭 실패 시 프로세스가 `sys.exit()`으로 종료된다 — 의도된 동작으로 보기 어렵다.
- `raise ValidationError(f"...", file=sys.stderr)` (2곳) — 예외 생성자에 키워드 인자를 넘겨 실제로는
  `TypeError: ValidationError() takes no keyword arguments`가 발생한다.
  바깥 `except Exception`에 잡혀 최종 동작은 "거부"로 같지만, 에이전트에게 가는 메시지가 엉뚱해진다.
- 전역 가변 상태(`available_tools`, `security_policy`) 기반이라 멀티 에이전트/동시 세션에서
  정책이 서로 섞인다. 실험 코드로는 충분하지만 프로덕션에는 세션 스코프가 필요하다.

## 10. 흐름 요약

```
사용자 질의
   └─> generate_security_policy()  ── LLM ──> {tool: [(100, allow, JSON Schema, fallback)]}
                                                   │
에이전트가 툴 호출 ──> check_tool_call(name, args) ─┤
                            │                      │
                    우선순위 순 규칙 평가            │
                    ├ allow 매칭 → 실행             │
                    └ 불일치/deny → ValidationError → 에이전트에게 재시도 유도
                                    │
                              툴 결과 반환
                                    └─> decide_whether_to_update() ──> generate_update_security_policy()
                                                                             │
                                                          (ONLY_ALLOW_NARROW 시) Z3 부분집합 증명
```
