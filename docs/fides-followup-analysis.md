# FIDES 후속 연구 분석: 단점 개선 및 대체 기법 정리

- 작성일: 2026-09-29
- 대상: FIDES (Costa et al., *Securing AI Agents with Information-Flow Control*, arXiv:2505.23643, v1 2025-05-29 / v2 2025-09-03, Microsoft Research)
- 조사 범위: Semantic Scholar 기준 FIDES 인용 논문 124편(2026-09-25 기준) 중 IFC·플래너·권한/출처 추적·공격/평가·시스템 계열 약 60편과, FIDES와 직접 비교되는 동시대 대안(Progent, RTBAS, PFI, CaMeL 등)
- 문서 목적: FIDES의 구조적 한계를 정리하고, 각 한계를 (a) FIDES 위에 **추가 도입**해 개선할 수 있는 기법과 (b) FIDES를 **대체**할 수 있는 기법으로 나누어 정리한다.

## 목차

1. FIDES 요약 (메커니즘·성능·자인한 한계·실무 적용 현황)
2. 후속 연구가 지적한 FIDES의 단점 W1~W8
3. FIDES에 추가 도입하여 개선하는 기법 (3.1~3.13)
4. FIDES를 대체할 수 있는 접근 (4.1~4.7)
5. 종합 권고: 개선 로드맵과 평가 방법
6. 참고 문헌

---

## 1. FIDES 요약

### 1.1 핵심 메커니즘

| 구성 요소 | 내용 |
|---|---|
| 레이블 격자 | 무결성(Trusted/Untrusted)과 기밀성(독자 집합 기반) 2축 레이블. 툴 결과 JSON 트리의 각 노드에 `metadata` 레이블을 붙이고, 없으면 부모 레이블을 상속 |
| 동적 taint tracking | 툴 래퍼가 lattice join으로 레이블을 전파. LLM 응답은 입력된 모든 메시지·툴 선언 레이블의 join으로 taint (보수적) |
| 정책 | 툴별 정책 2종만 사용: **P-T**(신뢰된 컨텍스트에서만 호출 허용, 무결성 = 제어흐름 무결성), **P-F**(인자 기밀성이 툴의 허용 독자 집합에 포함되어야 함). P-T-or-P-F 조합은 robust declassification |
| 선택적 은닉(Hide) | 툴 결과를 그대로 컨텍스트에 넣으면 컨텍스트 레이블이 올라가는 경우에만 해당 필드를 변수(`#tool-result-n.field#`)로 치환. 플래너는 변수를 참조(by-reference)로 후속 툴 인자에 전달 |
| 제한된 검사(Inspect) | `inspect`(변수를 컨텍스트로 확장 → 컨텍스트 taint) 또는 `query_llm`(툴 없는 격리 LLM + constrained decoding으로 지정 스키마 타입의 값만 추출, 결과는 새 변수) |
| 보안 속성 | 무결성: 비간섭(non-interference). 기밀성: **explicit secrecy**(명시적 흐름만 차단, 제어흐름을 통한 암묵적 흐름은 허용하는 실용적 타협) |
| 작업 분류 | DI(데이터 독립), DIQ(`query_llm`으로 해결 가능한 데이터 독립), DD(데이터 의존). 변수 전달만으로는 DI만, FIDES는 DI+DIQ+일부 DD 해결 |

### 1.2 논문이 보고한 성능 (AgentDojo, 97 user task × 35 injection task)

| 항목 | 결과 |
|---|---|
| 공격 차단 | 정책 적용 시 Tool Knowledge 공격 949건 중 성공 1건(응답 텍스트만 조작하는 text-to-text 공격, 툴 호출 정책 밖) |
| 정책 없는 유틸리티 | 추론 모델(o1/o3/o4-mini)에서는 Basic 플래너와 동등, 비추론 모델(gpt-4o)에서는 최대 23.6%p 하락 |
| 정책 적용 시 유틸리티 | Basic 대비 최대 16.7%p 우위이나, 정책 적용으로 최대 24.5%p 하락(o3/o4-mini). 이상적 오라클 대비 DI/DIQ에서도 큰 격차 |
| 토큰 비용 | Basic 대비 평균 2~3배 |

### 1.3 논문 스스로 인정한 한계 및 향후 과제 (Appendix E 등)

1. **유틸리티 손실 원인**: (1) `query_llm` 오용·계획 실패, (2) 실패 후 변수를 직접 확장하여 컨텍스트를 taint시켜 정책 위반(“compensatory leakage”).
2. **보수적 레이블 전파**: LLM 응답이 입력 전체의 join으로 taint됨. 더 관대한 전파(permissive IFC)를 수용할 수 있는 구조라고만 언급.
3. **정적·범용 정책 2종**: 사용자 질의·툴 인자 값에 따른 동적/세분화 정책, 동적 레이블 생성은 향후 과제. 단, 확률적 판단(LLM)에 의존하면 보장이 희석된다고 경고.
4. **정책 인지 플래너 부재**: 플래너가 레이블/정책을 모른 채 계획하다 위반에 부딪힘 (예: 신뢰/비신뢰 발신자를 구분 못해 실패한 workspace task 22).
5. **효율**: `query_llm` 추가 턴으로 지연·토큰 2~3배.
6. **범위 제한**: 정책은 툴 호출에만 적용되어 최종 응답에 대한 text-to-text 공격은 막지 못함. 기밀성은 explicit secrecy까지만(암묵적 흐름·툴 호출 순서/여부 채널 미차단). 단일 에이전트·단일 세션 모델이며 장기 메모리, 위임/멀티에이전트, OS/브라우저 수준 자원은 모델 밖.
7. **레이블 출처 가정**: 모든 툴에 신뢰된 래퍼가 있어 레이블이 올바르다고 가정. 실제로는 Purview/MOTW/발신 도메인 같은 힌트를 래퍼로 변환해야 하며, 힌트가 없으면 “외부 데이터는 모두 Untrusted”로 안전 기본값.

### 1.4 실무 적용 현황 (참고)

- Microsoft Agent Framework v1.3.0 `agent_framework.security` 모듈에 통합(무결성 trusted/untrusted, 기밀성 public/private/user_identity, 툴별 `accepts_untrusted`/`max_allowed_confidentiality` 선언, 격리 LLM). GitHub Copilot CLI에 `FIDES_IFC` 실험 플래그, MCP `_meta` 필드로 레이블·정책(JSONPath/OPA Rego) 전달, MCP 게이트웨이 공개.
- 공개 토론에서 지적된 문제: 레이블이 세션 전체에 누적되어 장기 세션을 오염시킴(label persistence). 메시지/검색 배치/태스크/메모리 단위의 명시적 스코프 경계와 untrusted→trusted 승격 검증 절차 필요.
- Microsoft 측이 스스로 밝힌 미해결 과제: 혼합 출처 구조화 결과의 레이블 세분화, constrained decoding 기반 정제 추출, 정책 제약을 미리 고려하는 오케스트레이터 계획.

---

## 2. 후속 연구가 지적한 FIDES의 단점 (종합)

후속 논문 약 60편에서 FIDES(또는 FIDES류 동적 taint IFC)에 대해 제기한 문제를 8개 축으로 묶었다. 각 축 옆에 근거 논문을 표시한다.

| # | 단점 | 구체적 내용 | 근거 |
|---|---|---|---|
| W1 | **유틸리티 붕괴 / 실행 좌초(stranding)** | 정책 위반 시 그냥 중단. 레이블은 단조 하강만 하므로 한 번 taint되면 이후 실행이 “좌초”됨. AuthGraph는 FIDES TCR ≈25%로 인용. APPA의 직접 비교에서 FIDES(Agent Framework 구현) 유틸리티 36~46% vs APPA 87~91% | APPA(2607.24625), AuthGraph(2605.26497), Preemptive Hardening(2607.18847), AutoDojo(2606.15057), Trojan Hippo(2605.01970) |
| W2 | **과잉 오염(over-tainting, label creep)** | LLM 출력 = 입력 전체 레이블 join. 툴 호출 단위(whole-call) 레이블은 인자별 출처를 구분 못해 혼합 신뢰 작업을 과잉 차단하고, 반대로 권한을 갖는 인자에 툴 유래 값이 도달하는 공격은 놓침 | GIF(2606.23277), PACT(2605.11039), ChainCaps(2605.26542), NeuroTaint(2604.23374), Permissive IFA(2410.03055), 서베이(2603.11088) |
| W3 | **불리언/열거형 완전 은닉 → 데이터 의존 제어흐름 불가** | `verify_hypothesis` 같은 불리언 결과도 변수로 가려져 분기 불가. 소량 정보(small-domain) 탈출구는 논문에서 제안만 하고 평가 안 함. 정책 차단 시 어떤 값이 “의도된 다운그레이드”인지 “진짜 누출”인지 구분 불가 | CaMeL-CUA(2601.09923), Type-Directed(2509.25926), LLMbda(2602.20064), UCM(2607.05277) |
| W4 | **암묵적 흐름·부수 채널 미처리** | explicit secrecy만 보장. (a) 툴 예외/에러 메시지가 taint 없이 플래너로 되돌아가 인젝션 전달, (b) 정책 **거부** 자체가 정보 채널(causality laundering), (c) 격리 LLM 경계에서 타입 추출 시 레이블 소실 및 구분자 스푸핑(ADI) | SoK IPI(2511.15203), Causality Laundering(2604.04035), ADI(2607.05120), LLMbda, CFH(2510.17276) |
| W5 | **정책·레이블 작성 부담, 정적 정책** | 툴별 수동 정책·신뢰 래퍼 전제. 사용자 의도와 무관하게 “런타임에 읽은 것은 모두 Untrusted” 고정 규칙 → 위임(delegation) 작업에서 정당한 값 차단. 이력·경로·시간 조건을 표현할 정책 언어 없음 | ROPE(2608.27496), AgentFlow(2608.22868), FORGE(2602.16708), Agent-Sentry(2603.22868), AgentGuardian(2601.10440), Verifiably Safe Tool Use(2601.08012) |
| W6 | **메모리·장기 세션·외부 상태 미추적** | 컨텍스트 내부에서만 심볼/레이블을 추적. 저장 후 재읽기(stored IPI), RAG 메모리, 파일/셸/캘린더 상태를 거치면 레이블 소실. 세션 단위 taint를 적용하면 유틸리티 0 | DualView(2607.03821), Trojan Hippo, Structurally Close(2609.05911), NeuroTaint, SPA(2608.27234), Agent Framework 토론 |
| W7 | **비용·지연** | 매 스텝 플래너 재호출 + `query_llm` 추가 턴. CaMeL-CUA 측정: Fides-NOVA 토큰 29.6배 vs 단발 계획 1.88배. Prudentia도 FIDES 대비 약 2배 | CaMeL-CUA, Prudentia(2602.11416), Agent-Sentry |
| W8 | **범위: 단일 에이전트·툴 호출 싱크만** | 최종 응답 text-to-text 공격, 액션 없는 요약/RAG 작업, 멀티에이전트 오케스트레이션(불투명 서브에이전트, 에러 기반 재계획), 커밋 시점의 상태적 권한(중복 실행, 만료) 등은 모델 밖 | CFH, ObliInjection(2512.09321), FORGE, AID-Guard(2608.21159), AGATE(2609.30830), 서베이(2603.11088, 2606.04990) |

이 밖에 “레이블이 의미를 모른다”는 근본 비판(사용자 승인 주장 같은 콘텐츠 내 주장을 검증 못함, 컨텍스트 무결성 관점)은 *AI Agents May Always Fall for Prompt Injections*(2605.17634)과 *SoK: Trust-Authorization Mismatch*(2512.06914)가 제기한다.

---

## 3. FIDES에 **추가 도입**하여 단점을 개선하는 기법

FIDES의 결정적(deterministic) 집행 구조와 레이블 격자를 유지한 채, 모듈로 덧붙일 수 있는 기법들이다. 각 항목에 대상 단점, 핵심 아이디어, 근거 수치, 도입 시 주의점을 적는다.

### 3.1 정책 인지 플래너 + 사용자 보증(endorsement) — **Prudentia** (2602.11416, FIDES 저자진)

- 대상: W1, W5(정적 정책), W7 일부
- 아이디어: 툴 설명에 정책을 실어 플래너가 자신의 컨텍스트 레이블과 정책을 알고 계획하게 함. 변수 확장 전 `plan` 툴로 근거를 강제하고, `expand_variables(ask_endorsement=True)`로 사용자가 비신뢰 데이터를 한 번 Trusted로 보증하면 이후 호출마다 승인받지 않아도 됨(declassification은 의도적으로 제외).
- 결과(AgentDojo, o3/o4-mini): TCR@0 59.1% vs FIDES 50.1%(+9%p), 사람 개입(HITL) 최대 1.9배 감소, 데이터 독립 작업 +25%p. WASP에서 ASR 0, HITL 0. 비용은 FIDES 대비 약 2배.
- 주의: FIDES 코드베이스 위에 그대로 얹을 수 있는 가장 직접적인 개선. 비용 증가와 HITL UI 설계는 미해결.

### 3.2 정책 위반 시 복구 의미론 — **APPA** (2607.24625)

- 대상: W1(좌초), W5(롤아웃 부담)
- 아이디어: 레이블 전파는 FIDES처럼 보수적으로 두되, 참조 모니터를 2단계(호출 전 예측 검사 + 반환값 검사)로 확장하고, 차단 시 “실행 가능하게 만드는 상태 전이”(선행 호출, 호출 범위 권한, 정제기, 격리 하위 계산)를 유한 도달성 그래프에서 탐색해 구조화된 **remedy**로 돌려줌. 하위 브랜치가 taint를 흡수하고 attest-schema로 형태가 제한된 값만 반환. 주석 없는 툴은 점진적 타이핑(gradual typing)으로 부분 레이블 부여.
- 결과(FIDES를 Agent Framework 위에 두 구성으로 직접 재현): Bench-Corp 유틸리티 APPA 87~91% / ASR 0% vs FIDES 36~46% / ASR 26~35%. remedy 또는 브랜칭 제거 시 유틸리티 35%/56.5%로 하락.
- 주의: 저자도 “평가된 FIDES 정책이 벤치마크 제약을 인코딩하지 않았다”고 인정. 신뢰된 계약/정제기가 TCB에 들어감. FIDES의 `query_llm`이 하는 일을 “remedy 탐색 + 격리 브랜치”로 일반화한 것으로, FIDES 위에 반영 가능.

### 3.3 관대한(permissive) 레이블 전파 — **Permissive IFA**(2410.03055, 같은 Microsoft 그룹), **GIF**(2606.23277), **PRISM**(2603.28345)

- 대상: W2
- Permissive IFA: LLM 응답 레이블을 입력 join이 아니라 “유틸리티(원 완성문 perplexity)가 λ 이내로 유지되는 가장 관대한 하위 컨텍스트”의 레이블로 부여. 격자 DAG 탐색으로 최소 레이블 보장. 에이전트 대화에서 85% 이상 더 관대한 레이블. FIDES 논문 Appendix E가 수용 가능하다고 명시한 방식.
- GIF: 모델 **내부**를 통과하는 흐름을 Jacobian 기반 상호정보량 상한으로 정량화(Lean 4 국소 건전성 증명). 싱크 토큰별로 영향 준 입력 span을 순위화하고, 소형 LLM 선언해제기(declassifier)가 상위 k span만 보고 판단. 대리 모델(최대 200배 소형)로 계산해 블랙박스 모델에도 적용. RTBAS attention 방식이 9%를 taint하는 곳에서 0비트 인증. FIDES를 “모델 주변만 추적, 모델 내부는 추적 안 함”으로 비판하며 상보적이라고 명시.
- PRISM: 빌드 타임에 프롬프트 플레이스홀더→출력 쌍마다 25종 보존 레이블을 3모델 합의로 부여해 LLM 호출의 데이터플로 요약을 생성. FIDES식 “모두 전파” 대비 F1 47.5% → 81.7%.
- 같은 계열의 확률적 전파기: **RTBAS**(2502.08966)는 LM 판정기 또는 attention 기반 LSTM(정확도 ~81~85%)으로 다음 생성에 영향을 준 이력 영역만 골라 join(무공격 시 유틸리티 손실 7~10%, 토큰 약 2배). **AgentArmor**(2508.01249)는 실행 트레이스를 프로그램 의존 그래프로 복원해 3단계 기밀성/무결성 타입을 제어 의존(암묵적 흐름)까지 전파(AgentDojo ASR 3%, 유틸 72% vs 무방어 73%, 20.9초/작업). 둘 다 의존성 추출이 LLM에 의존해 놓친 의존성은 곧 비건전 레이블이 된다.
- 주의: 이들 방식은 모두 확률적 요소가 있어 FIDES 논문이 경고한 “보장 희석”을 감수해야 함. GIF는 그래디언트(또는 대리 모델) 필요. 무결성 축에는 Permissive IFA가 적대 입력 시 최저 무결성을 부여하도록 설계돼 있어 기밀성 축에 우선 적용하는 것이 안전.

### 3.4 소량 정보 타입 탈출구(typed handoff) — **Type-Directed Privilege Separation**(2509.25926), **UCM**(2607.05277), **CaMeL-CUA의 Fides-NOVA**(2601.09923)

- 대상: W3
- 아이디어: 격리 LLM이 플래너에 돌려줄 수 있는 값을 int/float/bool/사전 검증된 열거형 및 그 배열·객체로 제한(자유 문자열 금지). FIDES가 “불리언·열거형은 플래너로 돌려줄 수 있다”고 언급만 한 것을 실제로 설계·평가. Type-Directed: WebShop/Calendar/SWE-bench에서 ASR 31.7/63/98.9% → 0%, 유틸리티 유지(SWE-bench는 68.3→45.0%). CaMeL-CUA는 FIDES에서 불리언 변수 검사를 허용하고 `max_steps=15, max_variable_reuse=5` 등 상한으로 누출량을 캡핑한 Fides-NOVA를 제안(OSWorld pass@5 66.7%).
- 주의: 타입이 맞는 허위 정보(well-typed misinformation)와 분기 조종(branch steering, CaMeL-CUA에서 최대 87~100%)은 막지 못함. LLMbda(3.6)의 bounded endorsement 규율과 함께 쓰면 누출 상한을 형식적으로 둘 수 있음.

### 3.5 인자 수준 출처 계약 — **PACT**(2605.11039), **IntentCap**(2609.14631), **ChainCaps**(2605.26542)

- 대상: W2, W4(권한 인자 탈취), W8(위임)
- PACT: 툴 인자마다 의미 역할(target/command/credential/content/selector/control)과 최소 신뢰·금지 출처·의무를 계약으로 부여하고, 값 출처를 재계획 넘어 추적해 호출 전 결정적으로 검사. FIDES 추상화를 재구현한 기준선과 비교: 17개 진단 시나리오에서 PACT 100/100 vs FIDES 유틸 66.7/보안 37.5. AgentDojo 5개 모델에서 보안 100%, 유틸리티 38~46%(CaMeL 대비 +8~16%p). 모니터 P99 < 272µs.
- IntentCap: 각 결정 필드(툴, 목적지, 승인 범위, 인자)가 정확히 하나의 소유 출처(사용자 의도/워크플로 지시/툴 스키마/런타임 환경)에서 와야 하는 단기 lease. 3,746건 재생에서 unsafe accept 0, 출처를 합치면 오탐 94%.
- ChainCaps: 값마다 “도달 가능한 싱크” 비트벡터 예산을 두고 합성 시 교집합으로만 축소(비증폭 정리). 스칼라 레이블만으로 싱크 부분집합을 구분하려면 지수 개 레이블이 필요하다는 표현력 논증. 모델링한 Fides 대비 차단율 59.5% vs 16.1%. MCP 프록시로 무수정 배포, P95 0.34ms.
- 주의: 역할/출처 추론 정확도(PACT 87.1%/77.4%), 매니페스트 품질(ChainCaps 전문가 100% vs 초보 27.3%)이 병목. FIDES의 JSON 노드별 레이블 구조는 이미 필드 단위 부착이 가능하므로, “레이블 값”을 스칼라에서 싱크 집합/역할 계약으로 바꾸는 형태로 흡수 가능.

### 3.6 암묵적 흐름·에러·거부 채널 봉쇄 — **LLMbda**(2602.20064), **Causality Laundering/ARM**(2604.04035), **SoK IPI**(2511.15203), **ADI**(2607.05120)

- 대상: W4
- LLMbda Calculus: 모든 값에 레이블 + 프로그램 카운터 레이블로 제어흐름까지 추적하는 계산체계. prompt/fork/clear/endorse 원시어로 dual-LLM을 프로그램 수준 정책으로 표현. Lean으로 검증된 인터프리터가 곧 하네스. FIDES의 small-domain 가정을 Appendix E.3에서 실제로 **강제**하는 방법 제시. AgentDojo banking에서 집행을 항상 켠 채 유틸리티 64.6~75%(CaMeL 정책 적용 시 37.5%).
- ARM: 거부된 툴 호출을 출처 그래프의 1급 노드로 두고 거부 레이블 ≥ 보호 자원 레이블로 설정, 이후 행동에 반사실(counterfactual) 간선 연결. FIDES는 “거부 시 출력이 없어 레이블 전파도 없다”는 점을 정확히 지적.
- SoK IPI/ADI가 요구하는 수정: (1) 예외 메시지는 피연산자 레이블의 join을 상속하고 플래너에서 은닉, (2) `query_llm` 추출 결과는 타입과 무관하게 입력 레이블 상속(CaMeL 구현의 버그 사례), (3) 직렬화 시 nonce/무작위 필드명으로 구분자 위조 차단(ADI ASR 49% → 28.7%, 유틸 83.3% 유지).
- 주의: 완전 비간섭(implicit flow 포함)으로 가면 CaMeL Strict처럼 유틸리티 36.5%로 떨어짐. 선택적으로 “에러·거부·타입 추출 경계”만 먼저 막는 것이 현실적.

### 3.7 정책 언어·이력 조건·작업별 출처 라우팅 — **AgentFlow**(2608.22868), **FORGE**(2602.16708), **ROPE**(2608.27496), **CaMeLoT**(2609.18674)

- 대상: W5, W8(멀티에이전트)
- AgentFlow: (민감도, 계층 카테고리, 신뢰) 레이블 위의 선언형 정책 언어. 흐름 규칙, 경로/이력 규칙, 작업 범위 capability, 통제된 해제, 작업별 taint 리셋. 유한 SMT 검증. AgentDojo 949건 공격: 손상 33.0%→0.0%, 유틸리티 46.7→63.3%. 개입당 6.4ms.
- FORGE: Datalog 정책을 관측 서비스가 제공하는 실행 컨텍스트(메시지·툴 호출·에이전트 간 인과 의존)에 대해 aspect 지향 조인 포인트에서 집행. 재귀로 전이적 출처·ReBAC 표현, 정책 모순/중복/도달성 정적 분석. 표에서 FIDES를 “표현력 있는 정책 언어 ✗, 재귀 ✗, 멀티에이전트 ✗, 결정적 ✓”로 평가하고 상보적이라 명시.
- ROPE: 작업당 1회, 신뢰된 요청만 읽는 LLM이 민감 매개변수마다 출처 규칙(const/sourced/record/oneof/free/dest/explicit)을 배정. 런타임 원본 추적기가 값이 사용자(T1)·사용자가 지명한 소스(T2)·사용자 권위 기록(T3)으로 위조 불가능하게 거슬러 올라갈 때만 허용. 재작성으로 허용 결과가 바뀌지 않음을 증명. AgentDyn ASR 1.6~2.6%, 무방어 유틸리티의 82~100%(CaMeL 0 작업 완료). FIDES류를 “작업과 무관한 고정 규칙”으로 비판.
- 정책 **생성** 자동화: **Progent**(2504.11703)는 사용자 작업에서 LLM이 툴 이름·인자 값에 대한 JSON 허용/금지 정책을 초기 생성하고, 실행 중 갱신 제안을 SMT로 “축소(자동 적용)/확장(사용자 승인)”으로 분류(단조 confinement). AgentDojo ASR 39.9→1.0%, 확장 승인은 갱신의 6%. FIDES를 “데이터 소스에 사전 레이블 배정 필요”로 비판하지만 정작 흐름 레이블·기밀성은 없음 → FIDES의 툴별 정책 공급원으로 결합. **AgentSpec**(2503.18666)은 trigger+predicate+enforcement DSL로 LLM(o1) 규칙 생성 정밀도 95.6%/재현율 71%이나 출처 개념이 없어 “비신뢰 데이터가 싱크 도달” 자체를 표현 못함 → FIDES 레이블을 predicate로 노출하면 보완.
- CaMeLoT: 계획 AST → 전이 시스템 → CTL 정책 nuXmv 검증, 반례를 수리 프롬프트로. CaMeL 정책 22/28 정적 재현. FIDES는 계획을 미리 내놓지 않으므로 Prudentia의 `plan` 툴처럼 look-ahead 계획을 낼 때만 적용 가능.

### 3.8 메모리·환경 상태로 레이블 확장 — **DualView**(2607.03821), **SPA**(2608.27234), **Trojan Hippo**(2605.01970), **NeuroTaint**(2604.23374)

- 대상: W6
- DualView: 심볼 추적을 컨텍스트 밖(파일·셸·네트워크·타 에이전트)으로 확장. AgentView는 쓰고 다시 읽어도 심볼 유지(stored IPI 차단), HumanView는 원문 유지, 뷰별 툴 라우팅. 컨텍스트 한정 Dual LLM이 stored-IPI ASR 53.3%를 허용하는 데 비해 0%, 유틸리티 83.4→81.6, 토큰 +44~68%.
- SPA: 쿼리마다 계획을 한 번 내고 결과를 레이블 붙은 아티팩트로 커밋, 이후 플래너는 메타데이터만 봄. 다중 쿼리 벤치마크 AgentDojo-MQ 제안. 단 엄격한 Biba 무결성으로 유틸리티 53→29%.
- Trojan Hippo: FIDES식 2레이블 IFC를 메모리(쓰기 시 세션 레이블 스탬프, 검색 시 세션 taint)로 확장하면 ASR 0%지만 조화평균 유틸리티 ≈0. 중간 지대로 “비신뢰 쓰기 금지 / 사용자 프롬프트만 메모리 저장” 정책 권고.
- NeuroTaint: 메모리 쓰기 시 레이블을 함께 저장하고 검색 시 재수화(rehydrate). 오프라인 감사기이지만 FIDES 대비 TaintBench F1 0.928 vs 0.522, 암묵적 제어 부분집합 재현율 0.925 vs 0.425.
- **MemLineage**(2605.14421): Ed25519 서명 + Merkle 로그 메모리, 파생 DAG로 “어떤 검색 항목이 새 메모리에 영향을 줬는지” 기록, 외부 조상에서 내려온 근거의 민감 행동 거부. FIDES를 “가장 강한 결정적 기준선이나 레이블 상태가 실행 단위라 플래너 실행 경계에서 지워진다”고 정확히 지적하고 “FIDES를 MemLineage 위에서 실행”을 권고. **TMA-NM**(2606.24322): 콘텐츠·계보 기반 메모리 권한은 자기 요약·신뢰 툴 에코·조작된 교차 검증으로 세탁 가능(FIDES식 단일 세션 IFC 셀 세탁 ASR 최대 68%)함을 TLA+로 증명하고, 쓰기 시점 출처에 권한을 묶는 비가단(non-malleable) 설계로 ASR 0%. CaMeL/FIDES의 capability 토큰이 하위 값과 함께 흐르면 출처 레이블과 직접 합성 가능하다고 명시.
- 주의: FIDES에 필요한 최소 변경은 (1) 메모리/파일 쓰기 시 레이블 동반 저장, (2) RAG 청크·요약에도 레이블 상속, (3) 세션 단위가 아닌 레코드 단위 taint. 그 위에 3.3의 선언해제가 없으면 유틸리티 0이 됨.

### 3.9 레이블·정책 공급망(빌드 타임) — **Preemptive Hardening**(2607.18847), **Passant/DFC**(2606.05679), **Verifiably Safe Tool Use**(2601.08012), **AgentGuardian**(2601.10440), **Agent-Sentry**(2603.22868)

- 대상: W5, W1
- Preemptive Hardening: CI/CD에서 툴·호출 지점·프롬프트 템플릿을 추출해 누출 패턴을 랭킹하고 스키마 강화·경계 정제·허용목록 게이팅 패치를 자동 적용, 런타임 가드레일 규칙 생성. FIDES에 “레이블/정책 제안, 소스·싱크 후보 식별”로 공급 가능하다고 명시. 실제 앱 5종 benign 성공률: 수정 FIDES 0/38.5/0/90/80% vs 제안 100/76.9/97.1/91/100%.
- Passant: DBMS 내부에서 출력 튜플의 출처 다항식에 대한 정책을 SQL 재작성으로 인라인 평가(TPC-H 한 자릿수 % 오버헤드). DB 툴 결과를 “정책 통과됨”으로 취급하면 FIDES가 DB 결과 전체를 taint하지 않아도 됨.
- Verifiably Safe Tool Use: STPA 위험 분석 → 안전 요구 → 데이터플로·시퀀스 명세, capability/기밀성/신뢰 레이블을 실은 MCP 확장 제안. Microsoft의 MCP `_meta` 레이블 확장과 방향 일치.
- AgentGuardian/Agent-Sentry: 스테이징 트레이스에서 툴 입력 제약·CFG(또는 XGBoost 분류기+허용목록+LLM 판정)를 학습. 수동 정책 없이 초기 정책을 부트스트랩하는 용도. 형식 보장은 없음.

### 3.10 커밋 시점 상태적 권한·효과 원장 — **AID-Guard**(2608.21159), **AGATE**(2609.30830), **Consent/Approval Integrity** 계열

- 대상: W8(중복 실행·만료·승인 후 변조)
- AID-Guard: 승인된 요청을 예약(reservation)으로 만들고 커밋 시점에 요청·제공자 상태를 재검증, 재시도/복구 시 예약당 최대 1회 효과. Stripe 210회 시험 중복 0.
- AGATE: 운영자 툴 선언·호스트 승인 이벤트에서 권한을 얻고, 매개변수 바인딩·만료·사용 횟수 제한 grant와 효과 원장, 포렌식 재생. 여러 하네스에 어댑터로 무수정 적용.
- 주의: FIDES는 호출 “허가” 시점까지만 다룬다. 이 계열은 그 아래 커밋 계층으로 결합하면 되고, IFC와 충돌하지 않는다.

### 3.11 선언해제(declassification) 오라클: “LLM은 제안, 결정적 검증기가 승인” — **OCELOT**(2606.12341), **FlowSeal**(2609.14003), **MNC**(2608.01719), **확률적 검증**(2606.20510)

- 대상: W1, W2(기밀성 축), W8(응답 싱크)
- FIDES는 Prudentia에서도 기밀성 선언해제를 의도적으로 거부했다(상황 의존적이라 개별 승인이 낫다는 이유). 후속 연구는 이 빈자리를 “보장을 희석하지 않는” 형태로 메우려 한다.
- OCELOT: 비신뢰 로컬 LLM이 민감 원자(atom)를 표시하고 generalize/substitute 연산을 제안하면, 결정적 검증기가 인증된 min-entropy 비용을 계산해 궤적당 싱크 가중 예산 내에서 최소 공개 변형만 승인(witness-verified declassification). CaMeL은 “한계를 정할 수 없는 공개는 모두 거부해 0을 기록”하는 반면 유틸리티 25~41%p 우위. 오버헤드 18.3%, 토큰 1.4배.
- FlowSeal: 발신자/ACL 같은 출처 메타데이터에서 소유권 레이블 유도, LLM 컨텍스트 밖의 툴 수준 인터셉터가 모든 쓰기/공유를 가로채며, 격리 LLM 콘텐츠 검사기가 (오염 레코드, 제안 출력)만 보고 Safe/Blocked 판정. 프롬프트 인젝션이 아닌 **사회공학적 수신자**(협업 워크스페이스 유인, 생략을 통한 의미 난독화, 채널 분리) 위협을 다룸. 누출 43.8~75.6% → 0~3.3%, 유틸리티 72.4%(최고 기준선 75.9%), 실 MCP Gmail+Notion 34.7%→0%.
- MNC: 수신자·목적·전달·수명·로깅·메모리 범위로 묶인 의미 기반 선언해제와 누적 원장. 저자 스스로 “FIDES 재현이 아니며 우월성을 주장하지 않음”.
- 확률적 검증(Praline 확장): 오류율이 알려진 PII 탐지기/선언해제기를 Datalog 참조 모니터의 확률적 술어로 두고, 술어 간 상관과 무관하게 성립하는 위반 확률 상한을 SDP 완화로 계산. 이진 레이블을 “실패 확률이 붙은 레이블”로 바꾸면서도 건전한 상한 유지. 지연 221ms(vs Praline 1,015ms).
- 주의: FIDES 논문의 경고대로 확률적 오라클은 TCB에 LLM 한 번을 남긴다. OCELOT/확률적 검증처럼 **결정적 검증기 + 정량적 예산/상한**이 붙은 설계만 FIDES의 보장 수준과 양립한다.

### 3.12 승인 경로·효과 검증 — **Consent Integrity**(2606.02668), **Explanation-Bound Execution**(2607.25364), **Intent-to-Execution Integrity**(2605.16976)

- 대상: Prudentia식 사용자 보증(endorsement)의 위조 가능성, 툴 효과 미검증
- Consent Integrity: 에이전트가 자기 승인 대화를 서술(Lies-in-the-Loop)하는 문제에 대해, 신뢰된 중재자가 경계에서 실제 저수준 행동을 디코딩해 신뢰 경로로 렌더링하고 승인을 실행되는 정확한 행동에 바인딩. 분류 불가한 행동은 “검사 불가”로 표면화. FIDES 등을 “실행되는 것은 통제하나 사람의 승인은 보장하지 않는다”고 지적.
- Explanation-Bound: 에이전트 근거를 타입화된 행동 주장(의도·정책·페이로드·툴·위험·출처·신선도)으로 변환해 서버 보유 사실과 대조. 불일치는 거부, 불완전은 검토, 일치만 실행(권한 비확장). FIDES 레이블을 입력 사실로 소비 가능.
- Intent-to-Execution Integrity: Tool/Instruction/Judgment/Data-Flow 4가지 무결성이 동시에 성립해야 한다는 틀. FIDES는 Instruction·Data-Flow는 강하게 다루지만 Judgment(판단) 무결성과 Tool(효과) 무결성은 다루지 않는다고 평가.

### 3.13 응답·출력 싱크와 인젝션 정제 — **DRIFT Injection Isolator**(2506.12104), **MELON**(2502.05174), **ToolMinimize**(2608.24957), **ADI nonce 직렬화**(2607.05120)

- 대상: W8(text-to-text 공격), W2(과공유)
- DRIFT의 격리기(Injection Isolator)는 툴 결과 중 사용자 의도와 충돌하는 지시를 메모리 저장 전에 마스킹. FIDES `query_llm` 앞단의 정제기 또는 최종 응답 필터로 결합 가능(전체 DRIFT: ASR 30.7→1.4%, 토큰 1.89배).
- MELON은 사용자 프롬프트를 가린 재실행과 툴 호출이 일치하면 “작업 독립 행동 = 공격”으로 판정(ASR 0.24%, 유틸리티 손실 거의 없음, API 호출 2배). 확률적이므로 변수 확장 전 사전 필터 용도.
- ToolMinimize는 툴 인자를 필요 최소로 재작성(제거·일반화·치환·절단). 툴 호출의 81~88%가 과공유, 프라이버시 비용 81~92% 감소, 인자 유효성 100%, 중앙값 1.77ms. FIDES의 allow/deny 이진 결정을 “단계적 재작성”으로 보완.
- ADI 논문의 권고: 툴 결과 직렬화 시 nonce/무작위 필드명으로 구분자 위조를 막아 격리 LLM이 공격자 값을 “변수”로 돌려주는 경로 차단.

---

## 4. FIDES를 **대체**할 수 있는 접근

FIDES의 “반복적 플래너 + 동적 taint + 툴 호출 게이트” 구조 자체를 다른 구조로 바꾸는 계열이다. 각 접근이 FIDES 대비 무엇을 얻고 무엇을 잃는지 정리한다.

### 4.1 단발 계획(plan-first) 계열 — CaMeL(2503.18813), CaMeL-CUA(2601.09923), SPA(2608.27234), Plan-Then-Execute(2605.14290), CaMeLoT(2609.18674)

- 구조: 신뢰된 질의만 보고 전체 계획(제한된 Python/DSL)을 한 번 생성, 인터프리터가 실행하며 capability 그래프로 정책 검사. 격리 LLM은 비신뢰 결과를 타입 값으로 파싱. 제어흐름이 툴 결과를 보기 전에 고정됨.
- 얻는 것: 비용(CaMeL-CUA: 단발 1.88배 vs FIDES 재호출 29.6배 토큰), 실행 전 정적 검증 가능(CaMeLoT의 CTL/nuXmv, SPA의 정적 이중 격자 검증), 쿼리 간 상태(SPA의 레이블 아티팩트).
- 잃는 것: 데이터 의존 작업의 적응성. 여러 제3자 평가에서 CaMeL 유틸리티 붕괴가 일관되게 관측됨(AgentDojo 26~48%, AgentDyn 0%, Agent-Sentry 측정 31.0%/지연 26.6초). SPA도 IFC 적용 시 53→29%. 오류 발생 시 재계획 불가.
- 판단: 정적으로 분해 가능한 작업(웹 사이트 API, 배치 워크플로)에서는 FIDES보다 싸고 검증 가능. 탐색적·대화형 작업에서는 FIDES의 반복 구조가 낫다. Prudentia의 `plan` 툴처럼 FIDES에 look-ahead를 넣는 절충이 현실적.

### 4.2 복구 가능 참조 모니터 — APPA(2607.24625), SecureClaw(2606.09549)

- 구조: FIDES와 같은 보수적 레이블 전파를 두되, 실행 좌초 대신 “복구 전이”를 제공. APPA는 remedy 탐색·격리 브랜치·점진적 타이핑, SecureClaw는 불투명 핸들 + 경계 있는 스키마 요약만을 선언해제 인터페이스로 두고 PREVIEW→COMMIT 실행기와 거부 인지 복구.
- 수치: APPA vs FIDES(Agent Framework 구현) Bench-Corp 87~91% vs 36~46% 유틸리티, ASR 0% vs 26~35%. SecureClaw AgentDojo ASR 0.64%, ASB 0% / 유틸 88.9%, 복구로 ASB 유틸 70→86%.
- 판단: FIDES의 상위 집합(superset)으로 볼 수 있어 가장 직접적인 대체 후보. 단 APPA는 단일 저자·자체 벤치마크이며 FIDES 정책을 벤치마크에 맞게 조정하지 않은 비교라 재현이 필요.

### 4.3 언어/타입 기반 IFC — LLMbda Calculus(2602.20064), Language-Based Agent Control/TypeGuard(2605.12863)

- 구조: 에이전트가 생성하는 프로그램이 곧 정책 대상. LLMbda는 모든 값+PC 레이블로 제어흐름 포함 비간섭을 증명(Lean)하고 dual-LLM을 프로그램 수준 정책으로 표현. LBAC는 Haskell 타입 검사로 정책을 강제(RIO/TIO/LIO 모나드), 서브에이전트를 재귀 호출로 다룸.
- 얻는 것: 암묵적 흐름까지 건전한 보장, 고정된 루프가 아닌 임의 아키텍처, small-domain 탈출구의 형식적 강제. LLMbda는 집행을 항상 켠 채 유틸 64.6~75%(CaMeL 정책 적용 37.5%).
- 잃는 것: 도구/데이터 소스가 프로그램 안에 모델링돼야 하고 실제 프레임워크와의 브리지 비용. TypeGuard는 정책 적용 시 CaMeL과 같은 수준으로 유틸리티 하락(21건 중 8건).
- 판단: FIDES의 **의미론적 기반**을 대체할 후보. 시스템으로서는 아직 벤치마크 1개 수준.

### 4.4 출처/권한 기반 결정적 모니터 — ROPE(2608.27496), PACT(2605.11039), ChainCaps(2605.26542), AuthGraph(2605.26497), Agent-Sentry(2603.22868)

- 구조: “데이터가 얼마나 오염됐나” 대신 “이 인자 값이 어디서 왔고 어디로 갈 수 있나”를 추적. ROPE는 작업별 출처 규칙, PACT는 인자 역할 계약, ChainCaps는 싱크 예산 비트벡터, AuthGraph는 깨끗한 컨텍스트에서 만든 권한 그래프와 실행 출처 그래프의 정렬, Agent-Sentry는 정상 실행 트레이스에서 학습한 경계.
- 수치: ROPE AgentDyn 무방어 유틸리티의 82~100%에서 ASR 1.6~2.6%(CaMeL 0 작업). PACT 보안 100%/유틸 38~46%. AuthGraph AgentDojo ASR 40→1%, 유틸 76%. Agent-Sentry 95.1%/94.3%.
- 판단: FIDES의 기밀성 축(독자 집합)이 없거나(ROPE, Agent-Sentry) LLM 귀속에 의존(AuthGraph)한다. 무결성/제어흐름 방어만 필요하고 정책 부담을 줄이려면 대체 가능. 기밀성이 필요하면 3.5처럼 FIDES 레이블 값을 확장하는 형태가 낫다.

### 4.5 기밀성 전용 실행 환경 — GAAP(2604.19657)

- 구조: 모델·프롬프트를 신뢰하지 않고 에이전트 생성 코드를 IFC 하에 실행. 개인 데이터 항목 이름이 곧 taint 레이블, (데이터 항목→허용 외부 당사자) 권한 DB를 사용자 질문으로 점진적 구축, 서비스 응답은 그 서비스에 이전에 보낸 것으로 taint(간접 공개 로그). 중간 결과 중 어떤 것을 LLM에 돌려줄지 계획이 선택(선택적 공개).
- 수치: 공개 공격 100% 차단, 작업 성공 감소 ≤10%.
- 판단: 기밀성 축에서 FIDES를 대체(신뢰된 플래너·정적 정책·세션 소멸 권한 불필요). 무결성/제어흐름 보장은 없으므로 FIDES와 결합하는 편이 맞다.

### 4.6 확률적 대안 — Twin Agent(2607.19595), DRIFT(2506.12104), MELON(2502.05174)

- Twin Agent: 탐색 에이전트가 비신뢰 콘텐츠를 읽고 50~200자 힌트만 안전 에이전트에 전달. SWE-bench 유틸 62.5%/ASR 0, AgentDojo 62.9%/0.1%(CaMeL 30.9%). 형식 보장 없음, 힌트 예산이 커지면 ASR 상승, 적응 공격(PAIR 다중 턴)에서 11건 성공.
- DRIFT/MELON: LLM 판정 기반. 적응 공격(AutoDojo)에서 DRIFT ASR 2배, 학습 기반 탐지기는 붕괴(PIGuard 0→28%).
- 판단: 결정적 보장이 필요 없고 유틸리티가 우선인 경우에만 대체. FIDES 앞뒤의 보조층으로 쓰는 것이 안전.

### 4.7 시스템/OS 수준 기판 — Agent libOS(2606.03895), ceLLMate(2512.12594), Prismata(2607.08147), UCM(2607.05277)

- 구조: 계획 신뢰를 요구하지 않고 프로바이더·원시 연산 경계에서 권한·흐름·정산(settle)을 검사(libOS), HTTP 계층 최소권한 정책(ceLLMate), DOM 구조에서 Biba 레이블 유도(Prismata/UCM).
- 판단: FIDES가 다루지 못하는 웹/파일/셸 싱크와 오케스트레이션 경계를 담당. 제어흐름 비간섭은 주장하지 않으므로 대체가 아니라 FIDES **아래** 계층.

---

## 5. 종합 권고: FIDES 개선 로드맵

각 단점(W1~W8)에 대해 결정성(보장 유지) 여부와 성숙도를 기준으로 도입 순서를 제안한다.

| 우선순위 | 조치 | 대상 단점 | 근거 기법 | 보장 영향 |
|---|---|---|---|---|
| 1 | 예외·거부·격리 LLM 추출 경계의 레이블 누수 봉쇄: 에러 메시지에 피연산자 레이블 join, 거부 이벤트에 자원 레이블 부여, `query_llm` 결과가 타입 무관하게 입력 레이블 상속, 직렬화 nonce | W4 | SoK IPI, ARM, ADI, LLMbda | 유지(강화) |
| 2 | 정책 인지 플래너 + `plan` 툴 + 사용자 보증 1회 | W1, W5 | Prudentia | 유지 |
| 3 | 정책 위반 시 복구 전이(remedy)와 격리 브랜치, 점진적 타이핑 | W1, W5 | APPA, SecureClaw | 유지(계약·정제기가 TCB에 추가) |
| 4 | 스칼라 레이블 → 필드/인자 수준 출처·역할·싱크 예산 | W2, W4 | PACT, ChainCaps, IntentCap | 유지 |
| 5 | 타입 제한 handoff(bool/int/enum/구조체)를 FIDES 1급 원시어로, 누출 상한(step·reuse cap 또는 bounded endorsement) 명시 | W3 | Type-Directed, UCM, CaMeL-CUA, LLMbda App. E | 정량 완화(상한 있음) |
| 6 | 메모리·파일·외부 상태에 레이블 동반 저장, 쓰기 시점 출처에 권한 바인딩, 레코드 단위 taint | W6 | DualView, MemLineage, TMA-NM, NeuroTaint | 유지 |
| 7 | 정책 언어 분리(이력·경로·위임 규칙, SMT/Datalog 정적 검사) + LLM/트레이스 기반 정책 부트스트랩 | W5, W8 | AgentFlow, FORGE, ROPE, Progent, Preemptive Hardening | 유지(생성된 정책은 검토 필요) |
| 8 | 선언해제 오라클은 “LLM 제안 + 결정적 검증기 + 정량 예산” 형태만 허용, 기밀성 축에 우선 적용 | W1, W2 | OCELOT, 확률적 검증, Permissive IFA, GIF | 확률적 상한으로 완화 |
| 9 | 커밋 계층(예약·재검증·1회 효과·만료 grant)과 승인 바인딩 | W8 | AID-Guard, AGATE, Consent Integrity | 유지 |
| 10 | 응답 싱크 정책: 최종 응답에도 P-F 적용 + 정제기/과공유 최소화 | W8 | FIDES 논문 자체 제안, DRIFT isolator, ToolMinimize, FlowSeal | 확률적 |
| 11 | 멀티에이전트: 에이전트 간 메시지에 서명된 출처, 오케스트레이션 제어흐름 문법을 비신뢰 입력 수집 전에 고정 | W8 | ControlValve(2510.17276), FORGE, When the Agent Becomes the Kernel | 유지 |
| 12 | 비용: 단발 look-ahead 계획과 반복 플래너의 하이브리드, 대리 모델 기반 흐름 계산 | W7 | CaMeL-CUA, SPA, GIF | 유지 |

**평가 방법 권고.** 정적 AgentDojo만으로는 방어 효과가 과대평가된다(AutoDojo). 후속 연구가 제안한 벤치마크를 함께 써야 한다: AgentDyn(동적·개방 작업), AgentDojo-MQ(다중 쿼리, SPA), TaintBench(NeuroTaint), MEM-INV-Bench(TMA-NM), AgentThreatBench/Bench-Corp(APPA), CI 기반 레드팀(2605.17634), 장기 궤적 출처 분석(2609.05911). 특히 3.4/3.11처럼 완화된 경로마다 적응 공격 평가가 필요하다.

**FIDES를 유지해야 하는 이유.** 조사한 후속 연구 중 무결성·제어흐름 비간섭을 결정적으로 보장하면서 FIDES보다 유틸리티가 높다고 **독립 재현된** 시스템은 없다. APPA만 직접 비교했으나 자체 벤치마크·단일 저자다. 반면 FIDES는 Microsoft Agent Framework/Copilot CLI/MCP `_meta`로 실제 배포 경로가 있고, 후속 연구 대부분(MemLineage, FORGE, GIF, ChainCaps, libOS, Consent Integrity 등)이 스스로를 “FIDES 위/아래에 놓는 상보 계층”으로 위치시킨다. 따라서 현실적인 전략은 FIDES를 결정적 하한(floor)으로 두고 위 표의 순서대로 계층을 덧붙이는 것이다.

---

## 6. 참고 문헌 (arXiv ID)

### FIDES 및 직접 확장
- Costa et al., Securing AI Agents with Information-Flow Control (FIDES), 2505.23643
- Kolluri et al., Optimizing Agent Planning for Security and Autonomy (Prudentia), 2602.11416
- Siddiqui et al., Permissive Information-Flow Analysis for LLMs, 2410.03055
- Microsoft, Towards secure, autonomous agents with IFC (commandline.microsoft.com); Agent Framework Discussion #5624; github.com/microsoft/fides

### IFC 확장·세분화
- NeuroTaint 2604.23374 · GIF 2606.23277 · FlowSeal 2609.14003 · APPA 2607.24625 · Passant/DFC 2606.05679 · Preemptive Hardening 2607.18847 · LLMbda 2602.20064 · LBAC/TypeGuard 2605.12863 · PRISM 2603.28345 · OCELOT 2606.12341 · MNC 2608.01719 · Probabilistic Verification 2606.20510

### 플래너 구조
- CaMeL 2503.18813 · CaMeL-CUA 2601.09923 · SPA 2608.27234 · CaMeLoT 2609.18674 · Plan-Then-Execute 2605.14290 · Type-Directed Privilege Separation 2509.25926 · Twin Agent 2607.19595 · DualView 2607.03821 · UCM 2607.05277 · PES 2608.27427

### 출처·권한·정책
- Agent-Sentry 2603.22868 · AuthGraph 2605.26497 · PACT 2605.11039 · ChainCaps 2605.26542 · AC4A 2603.20933 · AID-Guard 2608.21159 · AGATE 2609.30830 · ROPE 2608.27496 · AgentFlow 2608.22868 · Verifiably Safe Tool Use 2601.08012 · FORGE 2602.16708 · AgentGuardian 2601.10440 · IntentCap 2609.14631 · Progent 2504.11703 · RTBAS 2502.08966 · PFI 2503.15547 · AgentArmor 2508.01249 · DRIFT 2506.12104 · MELON 2502.05174 · AgentSpec 2503.18666 · IsolateGPT 2403.04960 · f-secure 2409.19091 · SecureClaw 2606.09549 · GAAP 2604.19657 · ToolMinimize 2608.24957

### 공격·평가·SoK
- ControlValve/CFH 2510.17276 · AutoDojo 2606.15057 · AI Agents May Always Fall for PI 2605.17634 · SoK IPI Defense Frameworks 2511.15203 · ADI 2607.05120 · ObliInjection 2512.09321 · Causality Laundering/ARM 2604.04035 · Structurally Close, Temporally Distant 2609.05911 · SoK Trust-Authorization Mismatch 2512.06914 · Trojan Hippo 2605.01970 · Agent Traces to Trust 2606.04990 · Attack and Defense Landscape 2603.11088 · CI-Work 2604.21308

### 시스템·포지션
- Agent Security is a Systems Problem 2605.18991 · Systems Security Foundations 2512.01295 · Agent libOS 2606.03895 · When the Agent Becomes the Kernel 2609.23700 · Intent-to-Execution Integrity 2605.16976 · Consent Integrity 2606.02668 · Explanation-Bound Execution 2607.25364 · Composable Trust 2607.13149 · MemLineage 2605.14421 · TMA-NM 2606.24322 · ceLLMate 2512.12594 · Prismata 2607.08147 · Meta Agents Rule of Two (2025-10) · Google Approach to Secure AI Agents (2025)

> 수치는 각 논문이 보고한 값을 그대로 옮긴 것이며, 벤치마크·모델·정책 설정이 서로 달라 논문 간 직접 비교에는 주의가 필요하다. 특히 FIDES와의 “직접 비교”는 APPA, PACT, ChainCaps, NeuroTaint, Preemptive Hardening, Trojan Hippo, TMA-NM이 각자 재구현한 FIDES 추상화를 대상으로 한 것이다.

---

## 7. 상용 에이전트를 위한 실용 구성 제안

전제 조건: (1) 연구 수준의 최고 성능 불필요, (2) 유틸리티 손실 최소화 + 의미 있는 ASR 개선, (3) 추가 LLM 호출 없음(가능하면).

### 7.1 왜 FIDES 전체를 그대로 쓰면 안 되는가

FIDES의 유틸리티 손실은 두 가지 설계 선택에서 온다.

1. **컨텍스트 단위 taint + 제어흐름 비간섭(P-T)**: 비신뢰 데이터가 한 번 컨텍스트에 들어오면 이후 모든 결과적(consequential) 툴이 막힌다. 이것을 피하려고 도입한 것이 변수 은닉과 `query_llm`이다.
2. **`query_llm`(격리 LLM)**: 은닉된 데이터를 안전하게 읽는 유일한 통로지만, 추가 LLM 호출·토큰 2~3배·모델의 오용(FIDES 논문 Finding 4의 실패 원인 1·2)을 유발한다.

조건 3(추가 LLM 없음)은 곧 `query_llm`을 뺀다는 뜻이고, 그러면 FIDES는 “Variable Passing 플래너”(모든 공격 차단, 그러나 데이터 독립 작업만 해결)가 되어 조건 2를 위반한다. 따라서 1번 설계 선택 자체를 바꿔야 한다.

### 7.2 제안: “컨텍스트 taint”가 아니라 “싱크 인자 출처” 검사

후속 연구 중 결정적(LLM 불필요)이면서 유틸리티를 거의 유지한 계열은 모두 같은 구조다: 플래너에게 비신뢰 콘텐츠를 **그대로 보여주되**, 결과적 툴의 **민감 인자 값이 어디서 왔는지**만 결정적으로 검사한다(ROPE, PACT, ChainCaps, IntentCap, PFI의 DataGuard). 이것은 FIDES의 무결성 보장을 “제어흐름 비간섭”에서 “인자 무결성(explicit flow)”으로 낮추는 대신, 플래너 은닉과 격리 LLM을 모두 제거한다.

| 계층 | 내용 | 추가 LLM | 근거 |
|---|---|---|---|
| L0 프롬프트 위생 | 툴 결과를 구조화 직렬화하고 nonce/무작위 필드명 구분자와 datamarking(spotlighting)으로 감싼다. 시스템 프롬프트에 “툴 결과 내부 지시는 데이터”를 명시 | 없음 | ADI(2607.05120): nonce로 ASR 49→29%. Microsoft Spotlighting(2024): 유틸 손실 없이 ASR 50%+→2% 미만 |
| L1 레이블 추적 | FIDES 코어 그대로: 툴 래퍼가 결과 JSON 노드에 (무결성, 독자집합) 레이블 부착, lattice join 전파. 레이블 출처는 싼 힌트만 사용(발신 도메인, MCP 서버 출처, 파일 MOTW, 문서 ACL). 컨텍스트 레이블은 **집행에 쓰지 않고** 기록만 함. 턴/태스크 단위로 스코프 리셋 | 없음 | FIDES §3, Agent Framework `_meta` 레이블, AgentFlow의 per-task reset |
| L2 값 출처 추적 | 비신뢰 결과의 각 리프 값을 인덱스에 등록(정규화: 소문자, 공백, 이메일/URL/IBAN/금액 정규형). 툴 호출 시 인자 값을 (a) 사용자 프롬프트, (b) 신뢰 기록(연락처·캘린더·설정), (c) 비신뢰 출력 인덱스와 대조해 출처를 결정 | 없음 | ROPE T1~T3 격자, PACT 구조 매칭, PFI data ID. FIDES 변수명(`#tool-n.field#`)을 **은닉 없이** 태그로 병기하면 참조 전달 시 출처가 정확해짐 |
| L3 툴 3단계 정책 | ① 읽기 전용: 항상 허용. ② 부수효과 + 민감 인자(recipient/url/amount/command/path/id): 민감 인자 값이 비신뢰 출력에서만 유래하면 위반. ③ 비가역·결제·삭제·코드 실행: FIDES P-T(신뢰 컨텍스트) 또는 사용자 승인 필수 | 없음 | PACT 역할 계약, Progent 정적 정책, FIDES P-T를 소수 툴에만 적용 |
| L4 기밀성 | 결과적 툴의 수신자 인자에만 P-F(독자집합 ⊇ 데이터 레이블) 적용. 위반이어도 사용자 프롬프트가 직접 지시한 흐름이면 허용(FIDES의 P-T-or-P-F robust declassification) | 없음 | FIDES §4.3 결합 정책, GAAP의 (데이터→허용 당사자) 권한표 |
| L5 위반 처리 | 차단이 아니라 **승인 요청**: “수신자 값이 발신자 X의 메일 본문에서 왔습니다. 진행할까요?”처럼 출처를 보여주고, 승인은 정확한 호출(툴+인자)에 바인딩. 승인 1회는 해당 값에 대한 보증(U→T)으로 기록 | 없음 | Prudentia endorsement, Consent Integrity, Progent 확장 승인(갱신의 6%) |
| L6 상태 지속 | 메모리·파일 쓰기 시 레이블 동반 저장, 재읽기 시 복원. 에러 메시지는 피연산자 레이블 join 상속 | 없음 | DualView, MemLineage, SoK IPI RC3 |

**응답 싱크.** 최종 응답에 비신뢰 콘텐츠가 포함되면 UI에 “외부 콘텐츠 포함” 배지와 출처 표시(FIDES 논문 §8.1의 제안). 링크는 비신뢰 출처면 클릭 전 도메인 표시. LLM 불필요.

### 7.3 기대 효과와 포기하는 것

문헌 수치(벤치마크·모델이 달라 방향성 참고):

| 구성 | 유틸리티 | ASR |
|---|---|---|
| FIDES 전체(정책 적용) | 무방어 대비 최대 −24.5%p, AuthGraph 인용 TCR ≈25% | ≈0 |
| 인자 출처 검사 계열(ROPE, AgentDyn) | 무방어의 82~100% | 1.6~2.6% |
| 싱크 예산(ChainCaps) | benign 96~100% | 0~4.8% |
| 프롬프트 위생만(Spotlighting/nonce) | ≈0 손실 | 수십%→수%~수십% |

포기하는 것:

- **제어흐름 비간섭**: 인젝션이 “어떤 벤인 툴이 호출되는가”를 조종할 수 있다(예: 불필요한 검색, 작업 방해). 인자가 공격자 유래가 아니면 통과한다. ③ 계층(비가역 툴 P-T/승인)이 이 공백의 실질 피해를 막는다.
- **타입이 맞는 허위정보·의미 공격**: 값이 신뢰 기록에 존재하면(예: 연락처에 있는 다른 수신자) 통과. 이는 FIDES도 막지 못한다.
- **암묵적 흐름**: FIDES와 동일하게 explicit secrecy까지만.

### 7.4 선택적 확장(LLM 1회, 신뢰 입력만)

조건 3이 “가능하면”이라면, 작업당 1회 **사용자 프롬프트만 읽는** LLM 호출은 인젝션 불가능하고 비용이 작다. ROPE(민감 매개변수별 출처 규칙 배정)나 Progent(초기 허용 정책 생성)를 이 방식으로 붙이면 L3의 정적 정책을 작업 맞춤으로 좁힐 수 있다. 격리 LLM으로 비신뢰 콘텐츠를 읽는 방식(FIDES `query_llm`, RTBAS 판정기, DRIFT 격리기)은 매 스텝 호출이므로 제외한다.

### 7.5 구현 순서와 검증

1. L0 + L1: 기존 Agent Framework FIDES 모듈을 쓰되 격리 LLM 비활성화, `accepts_untrusted=False`는 ③ 계층 툴에만 설정. 1~2주.
2. L2 + L3: 툴 스키마에 민감 인자 표기(PACT처럼 스키마에서 자동 추정 후 검토), 값 인덱스·정규화 매처 구현. 매처는 서브 ms(PACT P99 272µs, ChainCaps P95 0.34ms). 2~3주.
3. L5 승인 UI, L4 수신자 정책, L6 메모리 레이블. 2주.
4. 검증: AgentDojo(무공격 유틸리티, tool_knowledge/important_instructions ASR) + AgentDyn(개방형 작업) + 자체 트래픽 리플레이. 지표는 유틸리티, ASR, **승인 요청률**(목표: 작업의 10% 미만), 오탐(정당한 값 차단) 건수. AutoDojo식 적응 공격은 L2 매처의 정규화 우회(인코딩·분할)에 집중해 테스트한다.

### 7.6 한 줄 요약

FIDES의 레이블 추적은 유지하고, 유틸리티를 갉아먹는 두 요소(컨텍스트 단위 차단, 격리 LLM)를 “민감 인자 값의 출처 검사 + 비가역 툴에만 신뢰 컨텍스트 요구 + 위반 시 출처를 보여주는 승인”으로 바꾼다. 추가 LLM 없이 결정적으로 동작하며, 문헌상 유틸리티 80~100% 유지, ASR 한 자릿수가 기대 범위다.
