# Conseca 이후: LLM 기반 보안 정책 생성(Policy Generation LLM) 아이디어의 발전 계보 분석

- 작성일: 2026-09-10
- 범위: Conseca(Tsai & Bagdasarian, HotOS '25)를 인용한 논문 58편(Semantic Scholar 인용 그래프 기준)과, "LLM이 에이전트 보안 정책을 생성한다"는 아이디어를 제안·확장한 논문들을 웹에서 조사하여, **Conseca의 아이디어를 실질적으로 발전시킨 논문**을 선별·분석함.
- 주의: 각 논문의 수치는 arXiv 본문/초록에서 추출한 것으로, 버전(v1/v2/v3)에 따라 달라질 수 있음. 인용 여부는 arXiv HTML 본문 검색 결과 기준이며, 일부 논문은 Semantic Scholar에는 인용으로 잡히지만 본문에서 명시적 언급을 찾지 못한 경우가 있어 별도로 표기함.

---

## 목차

1. [요약 (Executive Summary)](#1-요약-executive-summary)
2. [기준점: Conseca가 제안한 것과 스스로 남긴 과제](#2-기준점-conseca가-제안한-것과-스스로-남긴-과제)
3. [발전 축(Axis)별 분류](#3-발전-축axis별-분류)
4. [핵심 논문 상세 분석](#4-핵심-논문-상세-분석)
5. [비교표](#5-비교표)
6. [Conseca 저자들 자신의 후속 방향](#6-conseca-저자들-자신의-후속-방향)
7. [비판적 관점: LLM 정책 생성의 한계를 실증한 논문들](#7-비판적-관점-llm-정책-생성의-한계를-실증한-논문들)
8. [미해결 과제와 연구 기회](#8-미해결-과제와-연구-기회)
9. [부록: Conseca 인용 논문 전체 목록(58편)과 관련도 분류](#9-부록-conseca-인용-논문-전체-목록58편과-관련도-분류)
10. [참고문헌](#10-참고문헌)

---

## 1. 요약 (Executive Summary)

Conseca(2025.01)는 "에이전트 보안 정책은 정적으로 미리 쓸 수 없으니, **신뢰된 컨텍스트만 보는 LLM이 작업마다(just-in-time) 정책을 생성**하고, 그 정책을 **결정론적으로 집행**하며, 사람이 검증할 수 있게 하자"는 아이디어를 제시한 HotOS 비전 논문이다. 프로토타입은 regex 기반 인자 제약과 20개 합성 태스크 평가에 그쳤고, 저자 스스로 (a) 정책 생성 LLM의 오판, (b) 다단계 공격을 막을 궤적(trajectory) 제약 부재, (c) 초 단위 생성 지연, (d) LLM 없이도 가능한지를 열린 문제로 남겼다.

이후 약 18개월 동안 이 아이디어는 다음 다섯 방향으로 발전했다.

| 발전 축 | 핵심 문제 | 대표 논문 |
|---|---|---|
| **A. 생성된 정책의 결정론적 검증** | LLM이 만든 정책 자체가 조작될 수 있다 | **Progent**(SMT 기반 단조 축소 보장), **Autoformalization→Cedar**(generator-critic + 정적 검증), **AgentFlow**(SMT 사전 검증), **VeriGuard** |
| **B. 정책 표현력 확장** | regex/인자 제약만으로는 다단계·정보흐름 공격을 못 막는다 | **DRIFT**(최소 함수 궤적), **ControlValve**(CFG 문법 + 엣지별 컨텍스트 규칙), **AgentGuardian**(CFG+ABAC), **PolicyGuide**(워크플로 그래프), **VIGIL**(트레이스 SMT), **ROPE/AgentFlow/ARGUS**(출처·정보흐름) |
| **C. 정책 생성 시점의 이동** | 런타임 LLM 생성은 느리고 불안정하다 | **CSAgent**(오프라인 컨텍스트 공간 + Policy Evolution), **AgentGuardian**(스테이징 트레이스 학습), **Firewalls**(데모 기반 규칙 학습), **AutoSpec**(ILP 규칙 진화), **AI Workflow Store** |
| **D. LLM 신뢰 표면의 축소** | LLM은 "신뢰된 요청"만 읽고, 나머지는 기계적으로 | **ROPE**(단일 라우팅 호출 후 출처 기반 결정론적 집행), **Prismata**(critical path만 보는 Action Gate), **MiniScope**(LLM 제거, ILP 최소 권한) |
| **E. 인간 검증/권한 UX** | Conseca의 "human-verifiable"이 실제로 어떻게 구현되나 | **Reframing(Agent–Human Interaction)**, **How Agents Ask for Permission**, **Janus** |

**가장 직접적인 발전형**은 Progent(정책 생성 LLM을 유지하되, 업데이트를 SMT로 검증하여 "조용한 권한 확장"을 원천 차단)와 ROPE(정책 생성 LLM의 입력을 사용자 요청 하나로 줄이고 집행에서 LLM을 완전히 제거)이며, **가장 강한 반론**은 MiniScope(LLM 기반 최소권한 추론이 최적해 대비 70~83%에 그침), IPI-SoK(Progent-LLM 자동 정책이 수동 정책 대비 ASR 4.63% 열세), Adaptive Evaluation(LLM 정책 작성 부분이 "검증 가능할 만큼 작다"는 참조 모니터 원칙을 위협)에서 나온다.

---

## 2. 기준점: Conseca가 제안한 것과 스스로 남긴 과제

**서지**: Lillian Tsai, Eugene Bagdasarian (Google). "Contextual Agent Security: A Policy for Every Purpose." HotOS '25 (2025.05). arXiv:2501.17070 (v1 제목 "Context is Key for Agent Security").

### 2.1 설계

- **컨텍스트 이분법**: 개발자가 지정한 *trusted context*(사용자 요청, 파일시스템 경로, 사용자명, 시간, 툴 문서)와 *untrusted context*(이메일 본문, 외부 툴 응답 등 공격자가 통제 가능한 데이터)를 분리한다.
- **정책 생성기(Policy Generator)**: LLM이 **trusted context + 사용자 태스크 + 툴 API 문서만** 입력받아 정책을 생성한다. 프롬프트 인젝션이 정책 생성기에 도달하지 못하게 하는 것이 핵심 격리다.
- **정책 형식**: 허용 API 호출 목록 + 인자별 regex 제약 + 사람이 읽을 수 있는 근거(rationale). 예: `send_email` 에 대해 `re.search(r'alice', $1) ∧ re.search(r'^.*@work\.com', $2)`.
- **집행(Enforcer)**: 결정론적 검사. 거부 시 근거를 플래너에 돌려보내 대안 행동을 유도하거나 사용자 확인을 요청한다.
- **인간 검증**: 정책과 근거를 로깅하여 사용자/개발자/제3자가 감사할 수 있고, 개발자는 실행 전 사용자 승인을 요구할 수 있다.
- **CaMeL과의 차이**: Dual-LLM 패턴에서 플래너가 아니라 *정책 생성기*를 격리하므로, 플래너는 전체 컨텍스트를 보고 기존 에이전트 설계 변경이 적다.

### 2.2 평가

20개 수작업 합성 태스크(파일시스템+이메일). 무정책 14.0/20 완료(단, 악성 이메일에 속아 유해 행동 수행), 정적 관대 정책 12.2/20, 정적 엄격 정책 0/20, Conseca 12.0/20 완료하면서 부적절 행동 거부.

### 2.3 저자가 명시한 한계와 열린 문제 (후속 연구의 출발점)

1. 정책은 생성기가 사용자 선호·사회 규범·필요 행동을 얼마나 이해하느냐에 달려 있다. 데이터 의존적 태스크("매니저 이메일에 적힌 일을 해줘")는 trusted context만으로 예측 불가.
2. regex는 복잡하고 ReDoS 위험이 있으며 위치 기반 인자를 가정한다.
3. **LLM 없이 contextual security를 달성할 수 있는가?**
4. **다단계 행동 조합 공격을 막을 궤적 제약을 어떻게 넣을 것인가?**
5. 초 단위 정책 생성 지연을 어떻게 줄일 것인가?
6. 출력 정화(sanitization)로 trusted context를 넓힐 수 있는가?
7. 실제 워크로드 기반 평가 부재.

아래 분석은 이 7개 항목 중 어느 것을 각 후속 논문이 해결(또는 반박)했는지를 기준으로 한다.

---

## 3. 발전 축(Axis)별 분류

### 축 A. 생성된 정책의 결정론적 검증 (Conseca 한계 1 대응)

Conseca는 "정책 생성기는 신뢰된 입력만 본다"는 *입력 격리*로 안전성을 확보했지만, 생성기 자체의 오판·환각이나 동적 업데이트 시의 조작에는 대책이 없었다. 이 축의 논문들은 **정책 생성은 LLM에 맡기되, 생성 결과를 기계적으로 검증**한다.

- **Progent** (Shi et al., 2025; arXiv:2504.11703): JSON-Schema 기반 DSL. 초기 정책은 사용자 태스크에서 생성, 실행 중 업데이트는 SMT 솔버가 "축소(narrowing)"인지 "확장(expansion)"인지 판정. 확장만 승인 요구 → **단조 격리(monotonic confinement)** 보장. 논문은 명시적으로 "Conseca와 DRIFT는 LLM이 정책을 생성하지만 결정론적 검증이 없다"고 비교한다.
- **Autoformalization of Agent Instructions into Policy-as-Code** (Mondl et al., 2026; arXiv:2606.26649): 에이전트 프롬프트·MCP 툴 설명·정책 문서를 LLM generator-critic 루프로 **Cedar** 정책으로 변환. Hard critic(Cedar 정적 분석: 문법·스키마·모순·공허 정책)과 Soft critic(LLM 의미 정렬)의 "Verification Sandwich". Conseca를 관련 연구로 인용.
- **AgentFlow** (Shivakumar et al., 2026; arXiv:2608.22868): 정책은 수동 작성이지만 배포 전 SMT(Z3)로 비누설·자격증명 탈출 저항 등 7개 속성을 검증. Conseca를 "태스크별 정책 생성" 계열로 인용하며 대비.
- **VeriGuard** (Miculicich et al., 2025; arXiv:2510.05156): 오프라인에서 사용자 의도 명확화 → 정책 합성 → 테스트+형식 검증 반복, 온라인은 경량 모니터.

### 축 B. 정책 표현력 확장 (Conseca 한계 2, 4 대응)

- **궤적/제어흐름 제약**: DRIFT(최소 함수 궤적 + 노드별 JSON 파라미터 체크리스트), ControlValve(태스크별 문맥자유문법 CFG를 LLM이 생성, Lark 파서로 결정론 검사 + 엣지별 최대 3개 컨텍스트 규칙), AgentGuardian(스테이징 트레이스에서 CFG+ABAC 학습), PolicyGuide(정책 문서→워크플로 그래프 컴파일, 턴 경계에서 검사), VIGIL(스킬 명세→SMT 제약, 이벤트 순서·인자 관계·호출 간 값 흐름).
- **출처/정보흐름 제약**: ROPE(민감 파라미터별 허용 출처 T1/T2/T3), AgentFlow(3차원 레이블 격자 + 경로 규칙), ARGUS(Influence-Provenance Graph), Prismata(Biba 무결성 모델 기반 DOM 레이블).

### 축 C. 정책 생성 시점의 이동 (Conseca 한계 5 대응)

- **런타임 → 개발/스테이징 단계**: CSAgent(오프라인 LLM+정적분석으로 함수·의도·정책 컨텍스트 공간 구축, 런타임은 검색만; Conseca를 "런타임 LLM 정책 생성에 의존하는 근본 한계"로 직접 비판), AgentGuardian(스테이징 트레이스→임베딩 클러스터링→regex 템플릿/수치 범위 일반화), Firewalls(양성 대화 코퍼스에서 프로토콜 어휘를, 양성+공격 대조 코퍼스에서 데이터 추상화 규칙을 오프라인 학습), VeriGuard.
- **런타임 동적 업데이트**: Progent(호출 결과마다 축소 업데이트 자동 적용), DRIFT(Read/Write/Execute 권한 계층별 편차 승인 후 제약 갱신), AGrail(Analyzer/Executor 두 LLM이 테스트타임에 안전 검사를 반복 정제, 메모리에 저장·재사용).
- **배포 후 진화**: AutoSpec(레이블된 트레이스의 반례로 ILP(ILASP) 기반 규칙 편집, LLM 불필요), LiSA(희소·노이즈 있는 사용자 실패 보고→보수적 정책 유도), PolicyBank(툴 수준 정책 인사이트 메모리 정제), CSAgent PEF.

### 축 D. LLM 신뢰 표면의 축소 (Conseca 열린 문제 3 대응)

- **ROPE**: "LLM은 신뢰된 사용자 요청 하나만 읽는 단일 라우팅 호출"로 태스크 명세 수준(fully-specified / parameter-open / action-open)과 파라미터별 출처 정책을 만들고, 이후 집행은 완전히 결정론. Conseca를 "부분적으로 이 문제를 해결했으나, 제약이 구문적 regex라 정당한 값과 주입된 값이 같은 패턴이면 구분 못 하고, 정책 아래에 감사된 기본값(default floor)이 없다"고 정확히 비판.
- **Prismata**: Action Gate LLM은 각 인터랙티브 요소의 DOM critical path만 보고 사용자 태스크와 대조 → 경로 밖의 인젝션은 라벨링에 영향 불가.
- **MiniScope**: OAuth 스코프 문서에서 권한 계층을 결정론적으로 재구성하고 ILP로 최소 권한 계산. "LLM을 격리 루프에 넣는" Conseca류 접근을 "환각·적응 공격에 취약"하다고 비판하며 LLMScope 베이스라인으로 실증.

### 축 E. 인간 검증/권한 UX (Conseca의 "human-verifiable" 구체화)

- **Reframing LLM Agent Security as an Agent–Human Interaction Problem** (Wang, Li, Tian, 2026): 59편 학술 논문·21개 제품·26개 플러그인 분석. "LLM 생성 정책 + 인간 검토(Conseca, AGrail, DRIFT, AgentGuardian)"는 학술 4편, **제품 0개**. 연구 의제로 NL→formal 번역과 "쓰기가 아닌 편집(edit-rather-than-write)" 정책 작성 제안.
- **How Agents Ask for Permission** (Michael & Roesner, 2026): 정책 도출 방식을 5분류(No translation / AI prediction / AI compilation / Deterministic compilation / Exact use). "낮은 사용자 부담 + 형식 명세 + 결정론 집행"을 모두 만족하는 시스템 부재, 집행 코드 검증 부재, 지속적 제어(갱신/철회) 부재를 gap으로 지적.
- **Janus** (Brigham, Bagdasarian, Kohno, Roesner, 2026): 권한 관리 설계 공간 탐색 플레이그라운드. 6개 permission assistant 비교, "보편 최적 설계 없음".

---

## 4. 핵심 논문 상세 분석

선정 기준: (i) Conseca를 인용하거나 명시적으로 비교하고, (ii) "LLM/자동화된 정책 생성 + 결정론적 집행" 구조를 유지하면서 Conseca의 한계 중 하나 이상을 실질적으로 해결한 논문. 발전 정도가 큰 순서로 배치.

### 4.1 Progent: Securing AI Agents with Privilege Control

- **서지**: Tianneng Shi, Jingxuan He, Zhun Wang, Linyu Wu, Hongwei Li, Wenbo Guo, Dawn Song (UC Berkeley 등). arXiv:2504.11703 (2025.04, 이후 개정).
- **Conseca와의 관계**: 본문에서 "Conseca and DRIFT also propose generating policies for agents, but both rely on an LLM for generating the policies without deterministic verification. ... enabling monotonic confinement guarantees that neither Conseca nor DRIFT can provide."라고 명시.
- **핵심 아이디어**:
  - 정책 = 툴별 규칙 리스트(effect allow/forbid, 인자 조건식: 논리·비교·멤버십·regex, 배열 길이 등) + 차단 시 fallback(종료/사용자 통지/오류 메시지 반환).
  - 초기 정책 P₁은 사용자 태스크(양성 입력)만으로 LLM 생성. 이후 각 스텝에서 (1) 업데이트 필요 여부를 툴 결과 없이 판단, (2) 필요 시 전체 컨텍스트로 후보 정책 P′ 생성.
  - **SMT 확장 검사**: A(P′) ⊆ A(P)이면 자동 적용(축소), 아니면 승인자(사람/자동 거부) 필요. 따라서 A(P)⁽⁰⁾ ⊇ A(P)⁽¹⁾ ⊇ … 가 보장되어, 정책 생성 LLM이 주입에 속아도 **조용한 권한 상승 불가**.
- **Conseca 대비 발전**: 한계 1(생성기 오판)에 대해 "생성 결과의 방향성(축소/확장)만은 기계적으로 검증"하는 우아한 타협. regex→구조화 DSL(한계 2). 동적 업데이트로 데이터 의존적 태스크 일부 대응.
- **결과**: AgentDojo ASR 39.9%→1.0%, ASB 70.3%→3.9%(개정판 기준; v1은 41.2%→2.2%). 초기 정책만으로도 AgentDojo ASR 2.5%. 업데이트의 6%만 승인 필요. LangChain/OpenAI Agents SDK/OpenHands 통합 시 ~1% ASR.
- **한계**: 사용자가 확장을 잘못 승인하거나 태스크가 모호하면 최소권한 초과. 툴 호출을 동반하지 않는 텍스트 출력 공격, GUI/멀티모달 행동은 범위 밖. 후속 SoK(§7)에서 **LLM 생성 정책이 파라미터 수준 제약을 놓쳐 수동 정책 대비 열세**임이 드러남.

### 4.2 ROPE: Routed Origin Policy Enforcement against Indirect Prompt Injection

- **서지**: Xinhang Ma, Chaowei Xiao, William Yeoh, Ning Zhang, Yevgeniy Vorobeychik. arXiv:2608.27496 (2026.08).
- **Conseca와의 관계**: §7 관련연구에서 "Conseca partially addressed this problem: it generates the per-task policy from trusted context alone, and it enforces the result deterministically." 이어서 두 가지 차이를 지적: (1) Conseca 제약은 **구문적 regex**라 정당한 값과 주입된 값이 같은 패턴에 매칭되면 구분 불가, (2) 정책 아래 **감사된 기본값(default floor)** 이 없어 약한 정책 생성기를 보완할 수 없음.
- **핵심 아이디어**:
  - 출처 추적기가 각 툴 결과에 구조적 출처 라벨을 붙인다(T1 사용자 요청, T2 서명된 이메일 등 위조불가 런타임 신원, T3 사용자의 권위 있는 기록). **추적기는 텍스트를 읽지 않으므로** 텍스트 내 인젝션이 자기 라벨에 영향을 줄 수 없다.
  - **단일 LLM 라우팅 호출**이 신뢰된 사용자 요청만 읽고, 태스크의 미명세 수준(fully-specified / parameter-open / action-open)과 민감 파라미터별 허용 출처(`prompt`=T1, `sourced`=T1+T2, `record`=T1+T2+T3)를 산출.
  - 런타임 집행은 결정론적: 상태 변경 툴의 민감 파라미터 값이 허용 출처에서 읽은 값과 일치해야 통과. 읽기 전용 툴은 항상 통과.
- **Conseca 대비 발전**: "정책 생성 LLM은 trusted context만 본다"는 Conseca 원칙을 극단까지 밀어 **입력을 사용자 요청 하나로 축소**하고, 정책의 표현을 regex(값의 모양)에서 **출처(값의 유래)** 로 바꿔 한계 1·3을 동시에 공략. 감사된 기본값으로 라우터 실패를 바닥에서 받친다.
- **결과**: AgentDyn(GPT-4o-mini) 무방어 clean utility 46.7%/ASR 80% → ROPE 43.3%/1.8%. 비교: DRIFT 18.3%/3.4%, Progent 6.7%/14.6%, PFI 15.0%/3.4%. 4개 모델에서 ASR 1.6~2.6%, 클린 유틸리티 82~100% 유지. AutoDojo 적응 공격에서도 ASR 불변(DRIFT는 3.4%→7.4%). AgentLAB 장기 공격 ASR 0.0%.
- **한계**: 상태 변경 툴만 보호(메시지 내용 유해성 23건 미방어). 자유 텍스트 파라미터(이메일 본문 내 피싱 링크) 방어 불가. 사용자가 민감 파라미터를 공격자 쓰기 가능 콘텐츠에 전적으로 위임하면 출처 기반 방어의 구조적 공백(46건). 출처 노출이 가능한 인프라 필요. 값 재표현(paraphrase) 시 매칭 실패.

### 4.3 CSAgent: Secure and Efficient Access Control for Computer-Use Agents via Context Space

- **서지**: Haochen Gong, Chenxiao Li, Rui Chang, Wenbo Shen (Zhejiang Univ.). arXiv:2509.22256 (2025.09).
- **Conseca와의 관계**: Conseca를 "동적 보안 정책 생성" 접근의 예로 인용하면서 "자동화를 보존하며 보안을 강화하지만, **런타임 LLM 기반 동적 정책 생성에 의존한다는 근본적 한계**"를 지적. Progent도 같은 이유로 비판.
- **핵심 아이디어**:
  - 컨텍스트 공간 = (class) → function → intent → policy 계층. 함수 F = ⟨desc, sec_level∈{normal, conditional, dangerous}, 의도 집합 I, I→Policy 매핑⟩. 컨텍스트 벡터의 각 원소는 type/source(user_request, system_api, system_cli, func_params, agent_history)/갱신 빈도(cold/warm/hot) 메타데이터를 가짐. 규칙 = ⟨ctx_id, constraint, guidance⟩.
  - **정책 생성은 개발 단계에서 오프라인**: API/CLI는 문서 분석, GUI 앱은 LLM 코드 이해 + CodeQL 정적 분석으로 이벤트 핸들러/호출 그래프 추출(DeepSeek-R1 사용). 런타임은 OS 서비스가 의도 추출·정책 검색·검증만 수행.
  - **Policy Evolution Framework(PEF)**: 앱 업데이트 동기화, 런타임 이상(누락 함수/의도, 사용자 오버라이드) 로그 기반 정책 개선 제안.
- **Conseca 대비 발전**: 한계 5(지연)를 정면으로 해결 — 정책 생성을 런타임에서 개발 단계로 옮김. GUI/CLI/API 3개 모달리티로 확장. "의도(intent)"를 정책 인덱스로 도입하여 Conseca의 "context"를 구조화.
- **결과**: 기하평균 ASR 0.64%(PVAgent 2.91%, vanilla AgentDojo 47.18%). 지연 오버헤드 6.83%(PVAgent 34~58%). AgentBench/AgentDojo/AndroidWorld. 단, AgentDojo 유틸리티 36.94% 감소(신뢰되지 않은 정보원 제한 탓).
- **한계**: 정책 완전성에 의존. GUI 앱 소스 분석 필요. 단일 에이전트만. 의도 추출 LLM 오류 가능.

### 4.4 DRIFT: Dynamic Rule-Based Defense with Injection Isolation

- **서지**: Hao Li, Xiaogeng Liu 외. NeurIPS 2025. arXiv:2506.12104.
- **Conseca와의 관계**: 본문에 Conseca 직접 인용은 확인되지 않음(Progent가 둘을 나란히 비교). 구조적으로 Conseca와 같은 "사용자 쿼리만 보는 Secure Planner가 정책 생성" 계열.
- **핵심 아이디어**: Secure Planner가 사용자 쿼리에서 (1) 제어 제약 = 최소 함수 궤적, (2) 데이터 제약 = 함수 노드별 JSON 파라미터 체크리스트를 생성. Dynamic Validator가 실행 후 편차를 검사하되, Read는 자동 승인, Write/Execute 편차는 LLM이 사용자 의도 정합성 판단 후 제약 갱신. Injection Isolator가 툴 응답에서 사용자 의도와 충돌하는 지시를 제거하여 메모리 오염 방지.
- **Conseca 대비 발전**: 한계 4(궤적 제약)에 직접 대응 — 정책이 "허용 API 집합"이 아니라 "예상 궤적"이 됨. 파라미터 값 의존성(예: "파리→런던"이면 같은 함수라도 "런던→뉴욕"은 차단)을 명시. OS식 권한 계층(Read/Write/Execute)으로 유연성 확보. 메모리 격리는 Conseca에 없던 장기 위험 대응.
- **결과**: AgentDojo(GPT-4o-mini) ASR 1.4%(무방어 30.7%), 양성 유틸리티 57.29%(CaMeL 35.4%). ASB ASR 4.8%.
- **한계**: 편차 승인에 LLM 판단이 개입(Progent가 이를 비판). ROPE 평가에서 AgentDyn 클린 유틸리티 18.3%로 급락, 적응 공격 시 ASR 상승.

### 4.5 ControlValve: Breaking and Fixing Defenses Against Control-Flow Hijacking in Multi-Agent Systems

- **서지**: Rishi Jha, Harold Triedman, Justin Wagle, Vitaly Shmatikov (Cornell Tech). arXiv:2510.17276 (2025.10).
- **Conseca와의 관계**: Conseca를 "사용자 요청과 신뢰된 컨텍스트 기반 regex 보안 정책", Progent를 "단일 에이전트 툴 접근제어 언어"로 인용. 자신은 **오케스트레이션 계층/다중 에이전트**로 확장.
- **핵심 아이디어**: 오프라인 계획 단계(신뢰되지 않은 콘텐츠 유입 전)에서 LLM이 사용자 쿼리+가용 에이전트로부터 태스크별 **문맥자유문법**(허용 에이전트 호출 시퀀스)을 생성 → Lark로 파서 컴파일. 각 CFG 엣지 A→B에 대해 LLM이 최대 3개의 자연어 컨텍스트 규칙(입력 검증·문맥 적절성·데이터 출처)을 zero-shot 생성. 런타임: 그래프 준수는 결정론, 규칙 준수는 좁은 범위의 LLM 판정. 실패 시 최대 3회 재계획.
- **Conseca 대비 발전**: 정책 단위를 "툴 호출"에서 "에이전트 간 제어흐름"으로 올림. 문법은 regex보다 표현력이 높고 결정론 검사가 가능. LlamaFirewall류 "정렬 검사"의 취약성을 실증한 뒤 CFI 원리로 고침.
- **결과**: CFH 공격 ASR 0%(LlamaFirewall 7~23%), CFH-Hard 0%(LlamaFirewall 43~100%), 컴퓨터 사용 공격 0%(6~89%). 유틸리티: 코딩 97%(무방어 93%), 컴퓨터 사용 100%(89%), AgentDojo 양성 62%(65%).
- **한계**: CFG가 과대/과소 근사될 수 있음(CFI 연구와 동일). 규칙 판정은 여전히 LLM. 오류 복구 시 새 에이전트 호출 제한.

### 4.6 Autoformalization of Agent Instructions into Policy-as-Code

- **서지**: Adam Mondl, Matthew Maisel, John H. Brock. ICML 2026 AIWILD 워크숍. arXiv:2606.26649.
- **Conseca와의 관계**: Tsai & Bagdasarian(2025)을 "contextual agent policies" 관련 연구로 인용. Policy-as-Prompt(Kholkar & Ahuja)도 함께 인용.
- **핵심 아이디어**: "Verification Sandwich" — Grounding layer(엔티티·툴 스키마·principal-resource-action 온톨로지) / Model layer(LLM이 후보 Cedar 정책 생성) / Safety layer(Hard critic = Cedar 정적 분석으로 문법·스키마·모순·공허 정책 검출, Soft critic = LLM 루브릭 기반 의미 정렬). 통과할 때까지 generator-critic 반복.
- **Conseca 대비 발전**: Conseca의 "사람이 근거와 제약의 일치를 검증"하는 부담을 **critic 루프로 자동화**. 정책 언어를 regex에서 검증 가능한 Cedar로 교체. 입력을 사용자 태스크에서 **정책 문서·MCP 툴 설명·에이전트 프롬프트**로 확장(조직 거버넌스 규칙의 코드화).
- **결과**: MedAgentBench 88개 규칙 중 Hong et al.의 수작업 심볼릭 가드레일이 23개만 커버한 데 비해 훨씬 넓은 커버리지. 쓰기(POST) 포함 궤적에서 차단률 94~100%.
- **한계**: 과도하게 엄격한 정책이 유틸리티를 떨어뜨려 개발자가 보호를 끄는 현상(현장 관찰). Cedar는 무상태라 다중 턴 순서 의존 정책 불가. 88개 중 약 32개 규칙은 출력 분류기/퍼지 판단이 필요해 심볼릭 집행 불가.

### 4.7 Prismata: Confining Cross-Site Prompt Injection in Web Agents

- **서지**: Corban Villa, Alp Eren Ozdarendeli, Sijun Tan, Raluca Ada Popa (UC Berkeley). arXiv:2607.08147 (2026.07).
- **Conseca와의 관계**: §6.1에서 "컨텍스트를 활용해 개방형 태스크에 걸쳐 just-in-time 보안 정책을 가능하게 하는" 연구로 인용.
- **핵심 아이디어**: Action Gate LLM이 각 인터랙티브 요소의 **DOM critical path(루트→요소 조상 체인)만** 보고 사용자 태스크 대비 권한 라벨을 부여 → 경로 밖의 인젝션은 라벨링에 영향 불가. Biba Parsing이 구조적 단서로 출처(developer/user/hosted-party/external)를 분류하고 "no-read-down, no-write-up"과 부모 초과 불가 잠금 적용. 유효 권한 = 둘의 최소. 기계적 격리: 콘텐츠 가지치기, 권한 다운그레이드, 행동 차단. 개발자 주석 불필요.
- **Conseca 대비 발전**: "정책 생성 LLM이 보는 입력을 구조적으로 최소화"하는 원칙을 웹 DOM에 적용. Conseca의 열린 문제 6(출력 정화로 trusted context 확장)에 대한 실질적 답변 — 신뢰 라벨을 요소 단위로 동적 도출.
- **결과**: ASR 85.5%→0.7%, 공격 하 TSR 4.5%→23.0%, 양성 TSR 29.9%→26.6%. GPT-5.4-nano 라벨링 정밀도 98.69%/재현율 82.69%.
- **한계**: critical path 위에 구조적 단서 없이 인젝션이 놓이는 경우(~0.1%). 모델 정확도 의존. 비텍스트 공격 미커버.

### 4.8 AgentGuardian: Learning Access Control Policies to Govern AI Agent Behavior

- **서지**: Nadya Abaev, Denis Klimov, Gerard Levinov, David Mimran, Yuval Elovici, Asaf Shabtai (Ben-Gurion Univ.). arXiv:2601.10440 (2026.01).
- **Conseca와의 관계**: "Reframing" 논문이 Conseca·AGrail·DRIFT와 함께 "LLM 생성 정책 + 인간 검토" 범주로 분류. 본문은 Progent의 "명시적 입력 열거"를 비판하며 일반화 계층을 도입.
- **핵심 아이디어**: 스테이징 단계에서 실행 트레이스(LLM 입력·추론·툴 호출·출력) 수집 → CFG 생성 + 텍스트/수치 속성을 150차원 임베딩으로 클러스터링 → regex 템플릿·수치 범위로 일반화한 ABAC 정책 합성. 런타임에 CFG에 없는 경로 차단.
- **Conseca 대비 발전**: 정책의 출처를 "태스크 설명"에서 "관측된 양성 행동 분포"로 바꿈. 사람이 읽고 편집할 수 있는 ABAC 규칙(human-verifiable 강화). CFG로 한계 4 대응.
- **결과**: FAR 0.10, FRR 0.10, BEFR 0.075 (2개 앱, 양성 80/공격 20).
- **한계**: 희귀 정당 입력 커버 불가, regex 추상화가 정교한 공격 구분 못함, 오케스트레이터 LLM 품질에 정책 품질 종속.

### 4.9 MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents

- **서지**: Jinhao Zhu, Kevin Tseng, Gil Vernik, Xiao Huang, Shishir G. Patil, Vivian Fang, Raluca Ada Popa (UC Berkeley). arXiv:2512.11147 (2025.12).
- **Conseca와의 관계**: Conseca류를 "LLM을 격리 루프에 넣는(bringing LLMs into the confinement loop)" 접근으로 지칭하며 "신뢰된 입력만 받는 별도 LLM이 태스크별 정책을 만든다는 아이디어는 유연하지만 환각·적응 공격에 여전히 취약하고 신뢰성 개선은 실험적 수준"이라고 비판. **Conseca 열린 문제 3("LLM 없이 가능한가")에 대한 '가능하다'는 답**.
- **핵심 아이디어**: OAuth 스코프 문서에서 method(s₁)⊆method(s₂)이면 s₁⊂s₂인 권한 계층을 결정론적으로 재구성. 런타임에 에이전트 실행 그래프의 API 호출 집합에 대해 ILP로 비용 최소 스코프 집합을 계산, 기존 부여 권한은 고정 변수로 두고 추가 필요 시에만 사용자 프롬프트.
- **결과**: 지연 오버헤드 1~7%. LLMScope(GPT-5/Claude Sonnet 4.5/Gemini 2.5 Flash 등) 최적성 70~83%, 오픈소스 20~34%, 과권한 비율 1.04~2.19. ChatGPT/Claude 커넥터에서 과권한 설정 6건 발견.
- **한계**: 권한 그룹 단위라 같은 스코프 내 툴 오용은 못 막음. 프롬프트 인젝션 자체는 범위 밖. 서비스의 스코프 설계 품질에 의존.

### 4.10 AGrail: A Lifelong Agent Guardrail with Effective and Adaptive Safety Detection

- **서지**: Weidi Luo 외. arXiv:2502.11448 (2025.02).
- **Conseca와의 관계**: "Conseca는 LLM으로 적응형 안전 정책을 생성하지만, 그 LLM이 태스크 요구를 오해하면 과도하게 제한적이거나 관대한 결과가 나온다"고 인용하며, 반복 최적화와 명시적 툴 기반 검증으로 대응.
- **핵심 아이디어**: 보편 안전 기준에서 태스크별 안전 검사를 동적 생성. Analyzer(메모리에서 검사 검색·수정)와 Executor(검증·정제) 두 LLM이 테스트타임에 협업하여 행동 유형별 최적 검사로 수렴. 메모리는 일반화된 행동으로 인덱싱하여 세션 간 재사용. OS 환경 감지기·EHR 권한 검사기·HTML 검증기 등 결정론 툴 선택적 호출.
- **Conseca 대비 발전**: 한계 1을 "한 번 생성"이 아니라 "반복 정제 + 메모리 축적"으로 완화. 결정론 툴을 검사 내부에 삽입.
- **결과**: 프롬프트 인젝션 ASR 0%, 양성 행동 95.6% 보존. 환경/시스템 사보타주 ASR 3.8~5%.
- **한계**: 추론 기반 방어 중심, 전용 가드레일 모델 부재, 툴 부족.

### 4.11 PolicyGuide / PolicyGuard (KAIST)

- **서지**: PolicyGuard: Kang et al., arXiv:2606.29225 (2026.06). PolicyGuide: Seongjae Kang, Taehyung Yu, Sung Ju Hwang, arXiv:2608.19861 (2026.08).
- **Conseca와의 관계**: 직접 인용 없음(ToolGuard, ShieldAgent 계열과 비교). 그러나 "정책 문서→LLM 오프라인 파이프라인→툴별 체크리스트 YAML→런타임 검증"이라는 구조는 Conseca의 정책 생성 LLM을 **조직 정책 문서 준수**로 재해석한 것.
- **핵심 아이디어**: PolicyGuard는 변경(mutating) 호출마다 전체 대화+원문 정책+생성 체크리스트를 보고 요구사항별 Met/Not Met → Pass/Block+remediation. PolicyGuide는 정책을 6단계 파이프라인으로 **워크플로 그래프**(actor/action 노드, 전이 엣지)로 컴파일하고, 코드가 소유하는 상태로 그래프 위치를 유지하며 사용자 턴 경계에서 단계별 remediation 제공.
- **Conseca 대비 발전**: "금지 행동 차단"에서 "**요구된 절차의 순서 보장**"으로 정책의 의미를 확장(τ²-bench 정책의 67~100%가 절차적 요구). 이진 차단 대신 안내형 개입.
- **결과**: τ²-bench Pass⁴ 0.42→0.62, Telecom 0.19→0.61. CRAFT 레드팀 ASR 0.087(PolicyGuard 0.125, 무방어 0.200).
- **한계**: 노드 판정이 LLM 기반이라 확률적. 매 행동 전이 아닌 턴 경계 개입(정리 1, 따름정리 2로 공백 정식화).

### 4.12 기타 주목할 발전형 (요약)

| 논문 | Conseca 연결 | 발전 포인트 |
|---|---|---|
| **AgentFlow** (VT, 2608.22868) | Conseca를 태스크별 정책 생성으로 인용 | 3차원 레이블 격자 + 흐름/경로 규칙, Z3로 배포 전 검증(12/12 안전하지 않은 변형 검출), AgentDojo compromise 33%→0%, 유틸리티 46.7→63.3% |
| **VIGIL** (2606.26524) | Conseca 인용 | 스킬의 자연어 명세를 SMT 제약으로, 재현율 95%+/FPR<10% |
| **AutoSpec** (HKUST, 2606.24245) | Conseca·Progent를 보완 관계로 인용 | ILP(ILASP) 반례 유도 규칙 진화, LLM 불필요, F1 0.98/0.93, FP 최대 94% 감소 |
| **Dynamic Capability Scoping** (2607.22445) | "Conseca는 행동마다 JIT 정책을 생성하지만 에이전트 자신의 행동 시도를 평가한다"며 차별화 | 에이전트와 독립된 fine-tuned 분류기가 태스크→권한 예측, 역할 상한∩태스크 예측∩금지 조합 교집합 |
| **Firewalls to Secure Dynamic LLM Agentic Networks** (Abdelnabi, Gomaa, **Bagdasarian**, Kristensson, Shokri, 2502.01822) | 공저자 동일 | "태스크 컨텍스트로의 투영"으로 재정의, 양성 코퍼스에서 프로토콜 어휘·대조 코퍼스에서 추상화 규칙을 오프라인 학습, 프라이버시 ASR 84.68%→10.20% |
| **GAAP** (Stanley, Verma, **Tsai**, Kallas, Kumar, 2604.19657) | 공저자 동일 | Conseca류 "LLM 생성 정책" 신뢰를 버리고, 에이전트 생성 코드에 IFC 적용 + 사용자 승인 결정 누적으로 정책 점진 구축 |
| **AI Workflow Store** (Geambasu, Raykova, Tholoniat, Tiwari, **Tsai**, Zhang, 2605.10907) | 공저자 동일 | "Conseca/CaMeL의 on-the-fly 제약 생성은 전체 컨텍스트 부재로 과소/과대 제한" → 사전 엔지니어링된 워크플로 저장소 |
| **Policy-as-Prompt** (Kholkar & Ahuja, NeurIPS 2025 RegML) | Conseca 인용 | PRD/설계문서→소스 연결 정책 트리→프롬프트 분류기 컴파일 |
| **ShieldAgent** (ICML 2025) / **GuardAgent** | 병렬 계보 | 정책 문서→검증 가능 규칙→확률적 규칙 회로; 가드 에이전트 패턴 |

---

## 5. 비교표

| 논문 | 정책 생성 주체/시점 | 생성기 입력 | 정책 표현 | 집행 | 생성 결과 검증 | 궤적/흐름 제약 | 인간 검증 |
|---|---|---|---|---|---|---|---|
| **Conseca** (2025.01) | LLM, 런타임 JIT | trusted context + 태스크 + 툴 문서 | 허용 API + regex 인자 | 결정론 | 없음 (rationale 감사) | 없음 (열린 문제) | 근거 로깅, 선택적 승인 |
| **Progent** | LLM, 초기+스텝별 업데이트 | 태스크(초기), 전체 컨텍스트(업데이트) | JSON-Schema DSL | 결정론 | **SMT 축소/확장 판정** | 없음 | 확장 시 승인 |
| **DRIFT** | LLM, 초기+편차 승인 | 사용자 쿼리 | 최소 궤적 + 파라미터 체크리스트 | 결정론+LLM(편차) | LLM 의도 정합 | **있음** | 없음 |
| **ControlValve** | LLM, 계획 단계 | 쿼리 + 에이전트 목록 | CFG 문법 + 엣지 규칙 | 결정론(문법)+LLM(규칙) | 없음 | **있음(다중 에이전트)** | 재계획 |
| **CSAgent** | LLM+정적분석, **개발 단계** | 툴 문서/앱 소스 | 함수-의도-정책 컨텍스트 공간 | 결정론(OS 서비스) | PEF 피드백 | 부분(agent_history) | 개발자 검토 |
| **ROPE** | LLM 1회, 런타임 | **사용자 요청만** | 파라미터별 허용 출처 | **완전 결정론** | 감사된 기본값 floor | 출처 기반 | 없음 |
| **Prismata** | LLM, 페이지별 | critical path + 태스크 | 요소별 권한 라벨 | 결정론(격리) | Biba 구조 규칙 min | 출처 기반 | 없음 |
| **Autoformalization** | LLM, 오프라인 | 프롬프트+MCP 설명+정책 문서 | Cedar | 결정론 | **Hard/Soft critic** | 없음(무상태) | 루브릭 |
| **AgentGuardian** | 트레이스 학습, 스테이징 | 실행 트레이스 | ABAC + CFG | 결정론 | 클러스터 일반화 | **있음** | 편집 가능 규칙 |
| **AGrail** | LLM 2개, 테스트타임 반복 | 태스크 + 메모리 | 안전 검사 목록 | LLM+툴 | 반복 정제 | 부분 | 없음 |
| **MiniScope** | **LLM 없음**, 런타임 ILP | 실행 그래프 + 스코프 문서 | OAuth 스코프 집합 | 결정론 | ILP 최적성 | 없음 | 추가 권한 시 프롬프트 |
| **AutoSpec** | ILP, 배포 후 | 레이블 트레이스 | 술어 규칙 | 결정론 | F1/복잡도 스코어 | 이벤트 단위 | 규칙 가독성 평가 |

---

## 6. Conseca 저자들 자신의 후속 방향

Conseca의 두 저자가 이후 발표한 논문은 원래 아이디어에 대한 가장 솔직한 자기 비판을 담고 있다.

1. **Tsai → GAAP (2604.19657)**: "Conseca 같은 trusted policy-based 방어는 LLM 생성 정책을 신뢰해야 한다"고 정리하고, GAAP은 **어떤 신뢰된 모델에도 의존하지 않는** 경로를 택했다. 에이전트가 생성한 코드에 정보흐름 분석을 적용하고, 사용자 승인 결정을 권한 DB에 누적하여 정책을 점진적으로 구축한다. 정책 생성을 "LLM의 추론"에서 "사용자 승인의 축적"으로 옮긴 셈이다.
2. **Tsai → AI Workflow Store (2605.10907)**: Conseca와 CaMeL을 "on-the-fly 제약 생성"의 선행 연구로 두고, "전체 컨텍스트가 없어 정책/스크립트 생성기가 가정을 해야 하고 이는 과소/과대 제한을 낳는다"고 진단. 해법은 소프트웨어 공학 수명주기(위협 모델링·설계·적대적 테스트)를 거친 **사전 강화 워크플로**를 저장소에서 재사용하는 것. 즉 정책 생성의 비용을 사용자 간에 상각한다.
3. **Bagdasarian → Firewalls (2502.01822)**: "태스크가 컨텍스트를 정의하고 방화벽은 그 컨텍스트로의 투영"이라는 Conseca의 철학을 에이전트 간 통신으로 확장하되, 규칙은 데모에서 **오프라인** 학습.
4. **Bagdasarian → "AI Agents May Always Fall for Prompt Injections" (2605.17634)**: 프롬프트 인젝션을 **Contextual Integrity 위반**으로 재정의. 고정 정책으로는 정당한 흐름을 막지 않으면서 모든 컨텍스트 조작 공격을 막을 수 없다는 근본 한계를 주장. 모호한 위임 하에서 규범을 추론해야 하는 정책 생성기의 어려움을 이론적으로 뒷받침.
5. **Bagdasarian → Janus (2607.01510)**: Conseca가 "선택적 사용자 승인"으로 남겨둔 인간 개입을 설계 공간으로 체계화. "사용자 입력은 결정적이지만 보편 최적 설계는 없다".

종합하면, 저자들은 (a) 런타임 LLM 정책 생성의 신뢰 문제를 인정하고, (b) 오프라인 학습/사전 엔지니어링/사용자 결정 누적으로 무게중심을 옮기며, (c) "완벽한 정책은 이론적으로 불가능"하다는 CI 관점을 정립하는 방향으로 움직였다.

---

## 7. 비판적 관점: LLM 정책 생성의 한계를 실증한 논문들

| 논문 | 실증 결과 | Conseca 계열에의 함의 |
|---|---|---|
| **Taxonomy, Evaluation and Exploitation of IPI-Centric Defense Frameworks** (Ji et al., 2511.15203) | Progent 수동 정책 ASR 0% vs **Progent-LLM 4.63%**. 근본 원인 RC5 "정책 커버리지 부족": LLM 생성 정책이 툴 수준은 맞추지만 **파라미터 수준 제약을 누락**. 적응 공격(Semantic-Masquerading: 기능 유사 툴로 우회) | Conseca의 regex 인자 제약은 이 문제를 직접 겨냥했으나, 생성기가 이를 일관되게 만들어낸다는 보장이 없음. 자동 생성기는 파라미터 제약을 명시적으로 강제해야 함 |
| **Adaptive Evaluation of Out-of-Band Defenses** (LaunchSafe, 2606.26479) | Progent는 적응 공격에도 ASR 상승 없음(4.2%→2.6%). 그러나 **정책 작성 LLM이 모델 계층 위험이 재진입하는 유일한 지점**이며 "검증 가능할 만큼 작다"는 참조 모니터 원칙을 위협. 권고: 결정론적 정책 작성으로 회귀, 전이적 출처 추적 | "생성은 LLM, 집행은 결정론"이라는 Conseca 구조의 급소를 정확히 지목 |
| **MiniScope** (2512.11147) | 최신 상용 LLM도 최소권한 추론 최적성 70~83%, 과권한 1.04~2.19배, 지연 수십 배 | LLM 없이 가능한 영역(OAuth 스코프)에서는 LLM 정책 생성이 열세 |
| **Reframing as Agent–Human Interaction** (2605.24309) | "LLM 생성 정책 + 인간 검토" 패턴: 학술 4편, **제품 0개** | Conseca의 human-verifiable 설계가 실무에 수용되지 못한 이유(검토 피로, NL↔formal 간극) 분석 필요 |
| **How Agents Ask for Permission** (2607.13718) | 21개 제안 중 "낮은 사용자 부담+형식 명세+결정론 집행" 동시 만족 0개, 집행 코드 검증 0개, 지속적 제어 6개 | 정책 생성뿐 아니라 집행기 자체의 검증이 공백 |
| **AI Agents May Always Fall for Prompt Injections** (2605.17634) | 고정 정책은 CI 관점에서 과/소 준수 트레이드오프를 피할 수 없음 | 정책 생성의 목표를 "완벽 차단"에서 "규범 근거 명시와 사용자 참여"로 재설정해야 함 |
| **Systems Security Foundations for Agentic Computing** (2512.01295) | Progent(사용자 정의 JSON) vs Progent-LLM(전체 컨텍스트 생성)을 "결정론적 보장 vs 적응성" 트레이드오프의 대표 사례로 정리 | 확률적 구성요소로부터 보안 보장을 구축하는 것이 6대 열린 문제 중 하나 |

---

## 8. 미해결 과제와 연구 기회

Conseca가 남긴 7개 과제 대비 현재 상태:

| Conseca의 열린 문제 | 현재 가장 진전된 답 | 남은 공백 |
|---|---|---|
| 1. 생성기 오판 | Progent SMT 단조성, Autoformalization critic 루프 | 축소/확장 판정은 "방향"만 검증하며 "초기 정책이 올바른가"는 미검증. 파라미터 제약 누락(IPI-SoK) |
| 2. regex의 한계 | Progent DSL, Cedar, ROPE 출처 정책, AgentFlow 레이블 | 값의 "모양"과 "출처"를 결합한 정책 언어 부재. 자유 텍스트 파라미터(이메일 본문) 미해결 |
| 3. LLM 없이 가능한가 | MiniScope(ILP), AutoSpec(ILP), AgentGuardian(트레이스) | 스코프/트레이스가 없는 개방형 태스크에서는 여전히 LLM 필요 |
| 4. 궤적 제약 | DRIFT, ControlValve, AgentGuardian CFG, PolicyGuide, VIGIL | 다중 에이전트·장기 세션에서 CFG 과대/과소 근사, Cedar 무상태 문제 |
| 5. 생성 지연 | CSAgent 오프라인(6.83%), ROPE 단일 호출, MiniScope 1~7% | 오프라인은 정책 완전성, 온라인은 지연 — 하이브리드 캐싱 연구 부족 |
| 6. 출력 정화로 trusted context 확장 | Prismata(DOM critical path), ROPE(출처 추적기), DualView | 사용자가 신뢰되지 않은 콘텐츠를 복사해 넣는 경우 출처 붕괴(Adaptive Evaluation §8) |
| 7. 실제 워크로드 평가 | AgentDojo/ASB/AgentDyn/τ²-bench/AgentLAB | 대부분 합성. 적응 공격 표준 프로토콜 부재(Adaptive Evaluation 권고) |

**유망한 연구 방향** (여러 논문의 한계 교집합에서 도출):

1. **출처 + 값 제약의 결합 정책 언어**: ROPE의 출처 마커와 Progent의 인자 조건식을 하나의 DSL에 통합하고 SMT 검증 가능하게 하기. IPI-SoK의 "파라미터 수준 커버리지" 문제를 생성기 프롬프트가 아니라 언어 수준에서 강제.
2. **정책 생성기의 입력 최소화 원칙의 정식화**: Conseca(trusted context) → ROPE(사용자 요청만) → Prismata(critical path만)로 이어지는 흐름을 "정책 생성기가 볼 수 있는 최소 정보량"으로 정식화하고 유틸리티 손실과의 트레이드오프 측정.
3. **오프라인 정책 + 온라인 축소 하이브리드**: CSAgent/AgentGuardian의 오프라인 정책을 상한(ceiling)으로 두고, Progent식 런타임 축소만 허용하면 지연·완전성·단조성을 동시에 확보 가능. Dynamic Capability Scoping의 3-source 교집합이 초기 형태.
4. **집행기 검증**: How Agents Ask for Permission이 지적한 "집행 코드 검증 0건" 공백. Conseca가 "Conseca 코드 자체를 신뢰"로 가정한 부분.
5. **정책 편집 UX**: Reframing 논문의 "edit-rather-than-write". Conseca의 rationale을 편집 가능한 초안으로 제시하고 사용자 수정이 정책에 반영되는 루프.
6. **CI 기반 정책 목표 재정의**: Bagdasarian의 CI 관점을 정책 생성기의 출력 스키마(sender/receiver/subject/type/transmission principle)로 채택하여 "왜 이 흐름이 적절한가"를 구조화.

---

## 9. 부록: Conseca 인용 논문 전체 목록(58편)과 관련도 분류

Semantic Scholar 인용 그래프(2026-09-10 조회) 기준. ★ = 본 리포트에서 상세 분석, ☆ = 요약 분석, ○ = 정책 생성과 직접 관련 낮음(인용만).

**정책 생성/집행 프레임워크 (직접 발전형)**
- ★ Progent: Securing AI Agents with Privilege Control (2504.11703)
- ★ ROPE: Routed Origin Policy Enforcement (2608.27496)
- ★ Secure and Efficient Access Control for Computer-Use Agents via Context Space / CSAgent (2509.22256)
- ★ Breaking and Fixing Defenses Against Control-Flow Hijacking in MAS / ControlValve (2510.17276)
- ★ Autoformalization of Agent Instructions into Policy-as-Code (2606.26649)
- ★ Prismata: Confining Cross-Site Prompt Injection in Web Agents (2607.08147)
- ★ MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents (2512.11147)
- ☆ AgentFlow: A Flow-Centric Policy Language and Framework (2608.22868)
- ☆ VIGIL: Runtime Enforcement of Behavioral Specifications in AI Agent Skills (2606.26524)
- ☆ Dynamic Capability Scoping for Enterprise AI Agents (2607.22445)
- ☆ Policy-as-Prompt / The AI Agent Code of Conduct (2509.23994)
- ☆ Firewalls to Secure Dynamic LLM Agentic Networks (2502.01822)
- ☆ An AI Agent Execution Environment to Safeguard User Data / GAAP (2604.19657)
- ☆ Engineering Robustness into Personal Agents with the AI Workflow Store (2605.10907)
- ☆ Taming Various Privilege Escalation in LLM-Based Agent Systems: MAC Framework / SEAgent (2601.11893)
- ☆ ARGUS: Defending LLM Agents Against Context-Aware Prompt Injection (2605.03378)
- ☆ AgentArmor: Enforcing Program Analysis on Agent Runtime Trace (2508.01249)
- ☆ Governance by Construction for Generalist Agents (2605.20874)
- ○ Data Flow Control: Data Safety Policies for AI Agents (2606.05679)
- ○ AC4A: Access Control for Agents (2603.20933)
- ○ Language-Based Agent Control (2605.12863)
- ○ Agent libOS (2606.03895)
- ○ Overlaying Governance (2606.03518)
- ○ CapChain (capability-token, 다중 에이전트)
- ○ SUDP: Secret-Use Delegation Protocol (2604.24920)
- ○ DualView: Preventing Indirect Prompt Injection in Personal AI Agents (2607.03821)
- ○ ceLLMate: Sandboxing Browser AI Agents (2512.12594)
- ○ Efficient and Sound Probabilistic Verification for AI Agents (2606.20510)
- ○ Web Agents Should Adopt the Plan-Then-Execute Paradigm (2605.14290)
- ○ Personalizing Agent Privacy Decisions via Logical Entailment / ARIEL (2512.05065)
- ○ PSG-Agent: Personality-Aware Safety Guardrail (2509.23614)
- ○ Spider-Sense (2602.05386)
- ○ Security Architecture for Agentic AI in Enterprise Cloud (Zero-Trust)
- ○ Towards Practically-Secure Tools for AI Agents (EuroMLSys '26)
- ○ Auditable LLM Autonomy for Operational Decision-Making
- ○ Controlling Opaque-Component Effects with Semisolates and Try

**SoK / 평가 / 비판**
- ☆ Reframing LLM Agent Security as an Agent–Human Interaction Problem (2605.24309)
- ☆ How Agents Ask for Permission (2607.13718)
- ☆ Janus: a Playground for User-Involved Agentic Permission Management (2607.01510)
- ☆ Taxonomy, Evaluation and Exploitation of IPI-Centric Defense Frameworks (2511.15203)
- ☆ Adaptive Evaluation of Out-of-Band Defenses Against Prompt Injection (2606.26479)
- ☆ AI Agents May Always Fall for Prompt Injections (2605.17634)
- ☆ Systems Security Foundations for Agentic Computing (2512.01295)
- ○ A Framework for Formalizing LLM Agent Security (2603.19469) — 본문에서 Conseca 직접 인용 미확인
- ○ The Attack and Defense Landscape of Agentic AI: A Comprehensive Survey (2603.11088)
- ○ Security Considerations for Artificial Intelligence Agents (2603.12230, NIST RFI 응답)
- ○ Extending the Formalism and Theoretical Foundations of Cryptography to AI (2603.02590)
- ○ Towards Agentic AI for Access Control in Cyber-infrastructures (BlueSky)
- ○ AIOracles: Modeling Agentic AI Security

**공격 / 기타**
- ○ Agent Data Injection Attacks are Realistic Threats (2607.05120)
- ○ MOSAIC: CLI Command Composition Attack (2607.02857)
- ○ Cloak and Detonate: Agent Skill Malware (2607.02357)
- ○ AI Snitches Get Glitches (2606.25836)
- ○ ClayBuddy: Coding Agent Failures (2606.19380)
- ○ Site Isolation is Dead (agentic browsers)
- ○ Attacks and Mitigations for Distributed Governance under Byzantine Adversaries (2605.12364)
- ○ Network-Level Prompt and Trait Leakage in Local Research Agents (2508.20282)
- ○ Topology Linearization for Multi-Agent Systems Security

**Conseca를 인용하지 않지만 같은 계보에 속하는 논문 (본문에서 언급)**
- DRIFT (2506.12104, NeurIPS 2025), AGrail (2502.11448, Conseca 인용 확인), AgentGuardian (2601.10440), AutoSpec (2606.24245), PolicyGuard (2606.29225), PolicyGuide (2608.19861), VeriGuard (2510.05156), LiSA (2605.14454), PolicyBank (2604.15505), ShieldAgent (2503.22738), AgentSpec (2503.18666), CaMeL, FIDES, FORGE, RTBAS, AIRGuard (2605.28914), SkillScope (2605.05868), ActPlane (2606.25189), Deontic Policies (2606.19464).

---

## 10. 참고문헌

- Tsai, L., Bagdasarian, E. "Contextual Agent Security: A Policy for Every Purpose." HotOS '25. https://arxiv.org/abs/2501.17070 · https://dl.acm.org/doi/10.1145/3713082.3730378
- Shi, T. et al. "Progent: Securing AI Agents with Privilege Control." https://arxiv.org/abs/2504.11703
- Ma, X. et al. "ROPE: Routed Origin Policy Enforcement against Indirect Prompt Injection." https://arxiv.org/abs/2608.27496
- Gong, H. et al. "Secure and Efficient Access Control for Computer-Use Agents via Context Space." https://arxiv.org/abs/2509.22256
- Li, H. et al. "DRIFT: Dynamic Rule-Based Defense with Injection Isolation for Securing LLM Agents." NeurIPS 2025. https://arxiv.org/abs/2506.12104
- Jha, R. et al. "Breaking and Fixing Defenses Against Control-Flow Hijacking in Multi-Agent Systems." https://arxiv.org/abs/2510.17276
- Mondl, A. et al. "Autoformalization of Agent Instructions into Policy-as-Code." ICML 2026 AIWILD. https://arxiv.org/abs/2606.26649
- Villa, C. et al. "Prismata: Confining Cross-Site Prompt Injection in Web Agents." https://arxiv.org/abs/2607.08147
- Abaev, N. et al. "AgentGuardian: Learning Access Control Policies to Govern AI Agent Behavior." https://arxiv.org/abs/2601.10440
- Zhu, J. et al. "MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents." https://arxiv.org/abs/2512.11147
- Luo, W. et al. "AGrail: A Lifelong Agent Guardrail with Effective and Adaptive Safety Detection." https://arxiv.org/abs/2502.11448
- Kang, S. et al. "PolicyGuide: From Guarding One Action to Guiding the Whole Workflow." https://arxiv.org/abs/2608.19861 · "PolicyGuard" https://arxiv.org/abs/2606.29225
- Shivakumar, B. A. et al. "AgentFlow: A Flow-Centric Policy Language and Framework." https://arxiv.org/abs/2608.22868
- Li, Y. et al. "VIGIL: Runtime Enforcement of Behavioral Specifications in AI Agent Skills." https://arxiv.org/abs/2606.26524
- Ma, P. et al. "AutoSpec: Safety Rule Evolution for LLM Agents via Inductive Logic Programming." https://arxiv.org/abs/2606.24245
- Noyan, H. B. "Dynamic Capability Scoping for Enterprise AI Agents." ICML 2026 AIWILD. https://arxiv.org/abs/2607.22445
- Abdelnabi, S. et al. "Firewalls to Secure Dynamic LLM Agentic Networks." https://arxiv.org/abs/2502.01822
- Stanley, R. et al. "An AI Agent Execution Environment to Safeguard User Data (GAAP)." https://arxiv.org/abs/2604.19657
- Geambasu, R. et al. "Engineering Robustness into Personal Agents with the AI Workflow Store." https://arxiv.org/abs/2605.10907
- Abdelnabi, S., Bagdasarian, E. "AI Agents May Always Fall for Prompt Injections." https://arxiv.org/abs/2605.17634
- Brigham, N. G. et al. "Janus: a Playground for User-Involved Agentic Permission Management." https://arxiv.org/abs/2607.01510
- Wang, P., Li, Y., Tian, Y. "Reframing LLM Agent Security as an Agent–Human Interaction Problem." https://arxiv.org/abs/2605.24309
- Michael, A. E., Roesner, F. "How Agents Ask for Permission." https://arxiv.org/abs/2607.13718
- Ji, Z. et al. "Taxonomy, Evaluation and Exploitation of IPI-Centric LLM Agent Defense Frameworks." https://arxiv.org/abs/2511.15203
- Narisetty, P. et al. "Adaptive Evaluation of Out-of-Band Defenses Against Prompt Injection in LLM Agents." https://arxiv.org/abs/2606.26479
- Christodorescu, M. et al. "Systems Security Foundations for Agentic Computing." https://arxiv.org/abs/2512.01295
- Siu, V. et al. "A Framework for Formalizing LLM Agent Security." https://arxiv.org/abs/2603.19469
- Kholkar, G., Ahuja, R. "Policy-as-Prompt." NeurIPS 2025 RegML. https://arxiv.org/abs/2509.23994
- Chen, Z. et al. "ShieldAgent: Shielding Agents via Verifiable Safety Policy Reasoning." ICML 2025. https://arxiv.org/abs/2503.22738
- Wang, H. et al. "AgentSpec: Customizable Runtime Enforcement for Safe and Reliable LLM Agents." https://arxiv.org/abs/2503.18666
- Miculicich, L. et al. "VeriGuard: Enhancing LLM Agent Safety via Verified Code Generation." https://arxiv.org/abs/2510.05156
- Kim, M. et al. "LiSA: Lifelong Safety Adaptation via Conservative Policy Induction." https://arxiv.org/abs/2605.14454
- Choi, J. et al. "PolicyBank: Evolving Policy Understanding for LLM Agents." https://arxiv.org/abs/2604.15505
- Ji, Z. et al. "Taming Various Privilege Escalation in LLM-Based Agent Systems (SEAgent)." https://arxiv.org/abs/2601.11893
- Weng, S. et al. "ARGUS: Defending LLM Agents Against Context-Aware Prompt Injection." https://arxiv.org/abs/2605.03378
- Wang, P. et al. "AgentArmor." https://arxiv.org/abs/2508.01249
- Semantic Scholar 인용 그래프: https://api.semanticscholar.org/graph/v1/paper/arXiv:2501.17070/citations
