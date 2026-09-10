# Conseca 인용 논문 분석 리포트: 컨텍스트 기반 에이전트 보안 아이디어의 발전 계보

- 작성일: 2026-09-10
- 대상 논문: Lillian Tsai, Eugene Bagdasarian. **"Contextual Agent Security: A Policy for Every Purpose"** (Conseca), HotOS '25, arXiv:2501.17070 (초기 버전 제목: *"Context is Key for Agent Security"*)
- 분석 범위: Semantic Scholar 기준 인용 논문 58편 + 웹 검색으로 추가 확인한 인용 논문. 이 중 Conseca의 핵심 아이디어(태스크·컨텍스트로부터 실행 전에 최소권한 정책을 자동 생성하고 결정적으로 강제)를 실질적으로 **발전·확장·검증·비판**한 논문을 선별해 분석.
- 주의: 인용 목록은 2026-09-10 시점 Semantic Scholar API와 웹 검색 결과에 기반하며 완전하지 않을 수 있음. 각 논문의 세부 내용은 arXiv 원문(HTML/abs)에서 확인했으며, 확인하지 못한 항목은 본문에 명시함.

---

## 목차

1. Conseca 원논문 요약
2. Conseca의 산업 구현: Gemini CLI의 `ConsecaSafetyChecker`
3. 인용 논문 전체 지형도(58편 분류)
4. 아이디어를 발전시킨 핵심 논문 심층 분석
   - 4.1 자동 정책 생성 계열(직계 후속)
   - 4.2 컨텍스트 최소권한 + 정보흐름/제어흐름 계열
   - 4.3 사용자 참여·개인화·Contextual Integrity 계열(공저자 후속 연구 포함)
   - 4.4 평가·비판·형식화 계열(SoK, 적응형 공격, 형식 기반)
5. 발전 축별 종합 비교
6. Conseca가 남긴 미해결 과제와 후속 연구가 제시한 답
7. 결론
8. 참고문헌

---

## 1. Conseca 원논문 요약

### 1.1 문제 제기

범용(generalist) LLM 에이전트는 이메일, 파일시스템, 웹 등 다수의 도구를 다양한 맥락에서 사용한다. 저자들은 "시스템이 마주치는 컨텍스트의 규모가 커질수록 정책의 세분화 수준도 함께 커져야 하며, 그렇지 않으면 과대 허용 또는 과소 허용이 유용성이나 보안을 크게 훼손한다"고 지적한다. 예를 들어 `이메일 삭제`는 이메일 내용, 목표(민감 메일 정리 vs 스팸 청소), 계정 종류(업무 vs 개인)에 따라 적절할 수도 부적절할 수도 있다. 기존 접근인 (a) 수동으로 작성된 정적 정책과 (b) 사용자 확인(confirmation)은 각각 과소/과대 허용 문제와 확인 피로(habituation) 문제를 가진다.

### 1.2 위협 모델

에이전트 자체는 선의이지만 실수할 수 있고, 공격자는 **컨텍스트의 일부(예: 악성 이메일, 서드파티 도구 응답)만 조작**할 수 있다고 가정한다. 컨텍스트는 다음 둘로 나뉜다.

- **신뢰 컨텍스트(trusted context)**: 사용자 자격 정보, 파일시스템 구조, 도구 명세 등 공격자가 조작할 수 없는 정보
- **비신뢰 컨텍스트(untrusted context)**: 이메일 본문, 웹 콘텐츠, 도구 반환값 등

### 1.3 아키텍처

| 구성요소 | 설명 |
|---|---|
| **정책 생성기(Policy Generator)** | LLM이 *사용자 요청 + 신뢰 컨텍스트만* 입력받아 태스크 전용 정책을 실행 전에 생성. 비신뢰 데이터를 보지 않으므로 정책 생성 단계는 프롬프트 인젝션에 노출되지 않음 |
| **정책 형식** | 허용되는 도구 API 목록과 인자에 대한 불리언 제약(프로토타입은 정규식), 그리고 사람이 읽을 수 있는 근거(rationale). 예: `rm "/tmp/.*"` — "정리 작업 시 임시 파일만 삭제" |
| **강제(Enforcement)** | `is_allowed(cmd, policy)`가 제안된 명령을 정책과 **결정적으로** 대조. 거부 시 근거를 함께 반환해 감사 가능성 확보 |
| **이중 모델 격리** | 플래너 전체를 격리하는 Dual-LLM/CaMeL과 달리 **정책 생성만** 격리. 플래너는 전체 컨텍스트를 그대로 보므로 기존 에이전트 설계 변경이 최소화됨 |

### 1.4 평가

파일시스템·이메일 도구를 사용하는 20개의 합성 다단계 태스크, 5회 반복.

| 설정 | 태스크 완료율 | 부적절 행동 차단 |
|---|---|---|
| 제한 없는 에이전트 | 70% (14/20) | 불가 |
| **Conseca** | 60% (12/20) | 가능 |
| 정적 허용적 정책 | 61% (12.2/20) | 실패 |
| 정적 제한적 정책 | 0% | 과도 |

즉 Conseca는 정적 허용 정책과 유사한 유용성을 유지하면서 컨텍스트상 부적절한 행동(예: 긴급하지 않은 상황에서 이메일 무단 전달)을 차단했다.

### 1.5 저자들이 명시한 한계와 열린 질문

1. 정책 품질이 "정책 생성기가 사용자의 선호, 사회적 규범, 태스크 수행에 필요한 행동을 얼마나 이해하는가"에 전적으로 의존
2. 신뢰 컨텍스트만 보므로 **데이터 의존적 행동**("매니저 이메일에 적힌 일을 처리해줘")을 예측하기 어려움
3. 합성 벤치마크 규모의 한계. 실제 워크로드 기반 ground-truth 필요
4. 개별 행동 단위 정책은 **궤적(trajectory) 수준의 복합 피해**("이메일 한 통은 무해하나 폭탄 발송은 유해")를 놓침
5. 사용자 상호작용(승인 요청, undo-log), 근거의 형식 검증, LLM 없는 정책 생성, 비용 절감(경량 모델 증류), 수동 정책·사용자 확인과의 하이브리드 등이 향후 과제

이 다섯 가지 한계는 이후 인용 논문들이 발전시킨 방향과 거의 1:1로 대응된다(6장 참조).

---

## 2. Conseca의 산업 구현: Gemini CLI의 `ConsecaSafetyChecker`

논문 아이디어는 Google의 오픈소스 코딩 에이전트 **Gemini CLI**에 `feat(security): Introduce Conseca framework`(PR #13193, 2025년 11~12월)로 실제 반영되었다. 리포지토리를 직접 확인한 결과는 다음과 같다(경로: `packages/core/src/safety/conseca/`).

| 항목 | 논문 설계 | Gemini CLI 구현 |
|---|---|---|
| 정책 생성 입력 | 사용자 요청 + 신뢰 컨텍스트 | 마지막 사용자 프롬프트 + **도구 함수 선언(tool declarations) JSON**만 신뢰 컨텍스트로 사용 |
| 정책 생성 모델 | LLM(모델 미특정) | Gemini Flash, JSON 스키마 강제 출력 |
| 정책 형식 | 도구별 정규식 제약 + 근거 | 도구별 `{permissions: allow/deny/ask_user, constraints: 자연어, rationale}` |
| 강제 방식 | `is_allowed` **결정적** 정규식 매칭 | **두 번째 LLM 호출**(Gemini Flash)이 정책과 tool call을 읽고 allow/deny/ask_user 판정 |
| 실패 처리 | 명시 없음 | 생성기 미초기화, 빈 응답, JSON 파싱 오류, 예외 등 **모두 ALLOW로 fail-open** |
| 기본값 | — | `security.enableConseca = false` (기본 비활성) |
| 정책 캐싱 | 태스크당 1회 | 동일 사용자 프롬프트면 재사용, 프롬프트가 바뀌면 재생성 |
| 텔레메트리 | 근거 로그 | `gemini_cli.conseca.verdict` 이벤트로 정책·판정·근거 기록 |

**시사점.** 실제 구현은 논문의 두 가지 핵심 보장 중 하나(정책 생성의 비신뢰 데이터 격리)는 유지했으나, 다른 하나(**결정적 강제**)는 LLM 판정으로 대체하여 "생성은 LLM, 강제는 결정적"이라는 논문의 신뢰 경계가 약화되었다. 또한 `ask_user` 결정을 추가해 저자들이 향후 과제로 언급한 "사용자 확인과의 하이브리드"를 일부 구현했다. Gemini CLI 이슈 #25829는 이 구현에 대해 "사용자 의도와 의미적으로 정렬된 인젝션(예: '테스트 고쳐줘' + 오염된 테스트 파일의 `curl ... | bash`)은 통과시킨다"는 한계를 지적하고, 사용자 지시 제거/비신뢰 데이터 제거 시 행동 확률 변화를 비교하는 **Leave-One-Out 인과 귀인**을 보완책으로 제안했다. 이 한계는 뒤에서 다룰 학술 논문들(ROPE, ARGUS, Abdelnabi & Bagdasarian의 불가능성 결과)의 핵심 논지와 정확히 일치한다.

---
## 3. 인용 논문 전체 지형도

Semantic Scholar 기준 58편(2026-09-10) 중 arXiv 원문으로 인용 맥락을 확인할 수 있었던 논문을 **Conseca와의 관계 유형**으로 분류했다. 웹 검색에서 추가 확인된 인용 논문(Agent Control Protocol, LLM Agents Should Employ Security Principles)도 포함했다. 반대로 검색 결과에서 인용 후보로 언급되었으나 원문 확인 결과 Conseca를 인용하지 않은 논문(VeriGuard, Deontic Policies, CaMeL, SkillScope, SkillGuard, AgentBound, ceLLMate 등)은 제외했다.

| 관계 유형 | 의미 | 대표 논문 |
|---|---|---|
| **A. 직계 후속(정책 자동 생성)** | "태스크에서 최소권한 정책을 자동 생성"이라는 Conseca의 핵심 기제를 계승하면서 생성·검증 방식을 개선 | Progent, MiniScope, ROPE, Prismata, ControlValve, Dynamic Capability Scoping, Autoformalization→Cedar, Policy-as-Prompt, CSAgent |
| **B. 강제 계층 확장(정보흐름·제어흐름·자원 모델)** | Conseca가 다루지 않은 데이터 출처, 흐름 경로, 제어 흐름, 자원 단위 권한을 정책 대상으로 확장 | AgentFlow, AgentArmor, SEAgent(MAC), AC4A, Plan-Then-Execute, Firewalls, Agent Control Protocol |
| **C. 사용자·개인화·규범 이론** | 정책의 원천을 LLM 추론에서 사용자 선호, 개인 규범, Contextual Integrity 이론으로 옮김. 공저자(Bagdasarian, Tsai)의 후속 연구 다수 | How Agents Ask for Permission, Janus, Reframing AHI, GAAP, AI Agents May Always Fall for Prompt Injections, ARIEL, PSG-Agent, Overlaying Governance, CUGA |
| **D. 평가·비판·형식화** | Conseca류 "LLM 생성 정책" 방어의 취약점을 체계화하거나 적응형 공격으로 검증, 또는 형식적 토대 제공 | Adaptive Evaluation of Out-of-Band Defenses, IPI 방어 SoK, Trust-Authorization Mismatch SoK, Systems Security Foundations, AIOracles, Attack & Defense Landscape 서베이, VIGIL, ARGUS, 확률적 검증, Agent libOS |
| **E. 배경 인용** | 동기·위협 모델 문단에서 한 줄 인용. 아이디어 발전과 무관 | LLM Agents Should Employ Security Principles, Cloak and Detonate, MOSAIC, DualView, Agent Data Injection, Site Isolation is Dead, Spider-Sense, Network-Level Leakage, AI Snitches, Zero-Trust 프레임워크, CapChain, Topology Linearization 등 |

이 리포트의 4장은 A~D 유형을 심층 분석하고, E 유형은 참고문헌에만 수록한다.

---

## 4. 아이디어를 발전시킨 핵심 논문 심층 분석

각 논문에 대해 (1) Conseca를 어떻게 인용·위치시켰는지, (2) 핵심 기제, (3) Conseca 대비 발전점, (4) 한계를 정리한다. 인용문은 arXiv 원문에서 그대로 발췌했다.

### 4.1 자동 정책 생성 계열(직계 후속)

이 계열의 공통 출발점은 Conseca의 명제 "정책은 태스크마다 달라야 하며 실행 전에 신뢰 컨텍스트로부터 생성되어야 한다"이다. 공통된 비판점은 **"LLM이 생성한 정책 자체가 검증되지 않는다"**는 것이며, 각 논문은 이를 서로 다른 방식으로 해결한다.

#### 4.1.1 Progent: Securing AI Agents with Privilege Control (Shi, He, Wang, Li, Wu, Guo, Song; UC Berkeley, arXiv 2504.11703)

**Conseca 인용 맥락(관련 연구, 비판적 대비):**
> "Conseca (Tsai and Bagdasarian, 2025) and DRIFT (Li et al., 2025) also propose generating policies for agents, but both rely on an LLM for generating the policies without deterministic verification. ... In Progent, even if the LLM-generated policy update is manipulated by adversarial inputs, the expansion check prevents any silent privilege escalation, enabling monotonic confinement guarantees that neither Conseca nor DRIFT can provide."

**핵심 기제.** 권한을 도구 이름과 인자에 대한 기호적 규칙(JSON 스키마 유사 형식)으로 표현하고 모든 tool call을 결정적으로 검사한다. LLM이 사용자 태스크로부터 초기 정책을 생성하고, 도구 결과가 도착할 때마다 **정책 업데이트**를 제안한다. SMT 솔버가 각 업데이트를 *축소(narrowing)*와 *확장(expansion)*으로 분류하여, 축소는 자동 적용하고 확장은 사용자 승인을 요구한다("monotonic confinement"). 조직 차원의 수동 정책과 태스크별 정책의 합성도 지원하며, LangChain·OpenAI Agents SDK 라이브러리와 MCP 프록시(OpenHands)로 배포된다.

**Conseca 대비 발전점.**
- Conseca는 정책을 실행 전 1회 생성하지만 Progent는 **실행 중 정책 업데이트**를 허용해 Conseca의 한계 (2)(데이터 의존적 행동 예측 불가)를 직접 해결
- LLM 생성 정책이 조작되어도 SMT 확장 검사로 **권한 상승이 불가능**함을 보장
- AgentDojo 공격 성공률(ASR) 39.9% → 1.0%, ASB 70.3% → 3.9%, 유용성 유지. 업데이트 중 약 6%만 확장으로 판정되어 사용자 승인 필요

**한계.** 초기 LLM 생성 정책은 여전히 미검증이며 태스크 설명이 모호하면 과도하게 넓어질 수 있다. 사용자가 확장을 잘못 승인할 위험, 텍스트 전용 공격(도구 호출 없는 피싱 메시지) 미방어, GUI/멀티모달 행동 미지원. Conseca가 강조한 사람이 읽는 근거(rationale)는 다루지 않는다.

#### 4.1.2 MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents (Zhu, Tseng, Vernik, Huang, Patil, Fang, Popa; IBM Research·UC Berkeley, arXiv 2512.11147)

**Conseca 인용 맥락(서론·관련 연구, 비판):**
> "The core idea is to treat a separate LLM as the 'expert' that takes input only from trusted sources and produces per-task policies that satisfy the required security properties. While this approach offers better flexibility, it introduces new security concerns. ... because security specifications are provided in natural language (e.g., 'Please adhere to the principle of least privilege during policy generation'), there is no guarantee that the LLM will interpret or follow these instructions consistently or correctly."

**핵심 기제.** 실제 서비스(Gmail, Calendar, Drive, Slack, Dropbox, Outlook, Notion, Zoom 등)의 OAuth 스코프 정의로부터 권한 계층을 재구성하고, 에이전트의 실행 계획이 주어지면 **정수 선형 계획법(ILP)**으로 최소 스코프 집합을 기계적으로 선택한다. 정책 생성에 LLM을 사용하지 않는다. 부여 범위를 벗어나는 요청은 모바일식 권한 모델(항상 허용/한 번 허용/세션 허용/거부)로 처리하며, 권한 검사기가 실제 자격 증명을 보유해 비신뢰 에이전트가 자격 증명을 절대 갖지 않게 한다.

**Conseca 대비 발전점.**
- Conseca가 열린 질문으로 남긴 **"LLM 없이 컨텍스트 정책을 만들 수 있는가"**에 최적화 기반의 답을 제시
- Conseca류 LLM 정책 생성기(논문 내 "LLMScope" 베이스라인)를 정량 평가: 상용 모델(GPT-5, Claude Sonnet 4.5, Gemini 2.5)에서도 최적성 70~83%, 오픈소스 모델은 20~34%, 과대권한 비율 1.04~2.19배
- MiniScope 지연 오버헤드 1~7% vs LLM 베이스라인 요청당 $0.063. 실제 ChatGPT/Claude 커넥터 설정 6건에서 과대권한 발견

**한계.** 세분화가 OAuth 스코프 단위에 묶여 있어 Conseca의 인자 수준 정규식 제약("이 채널에만 전송")은 기본 지원하지 않는다. 부여된 스코프 안에서 일어나는 인젝션은 막지 못하고, 서비스가 스코프형 OAuth를 제공해야 한다.

#### 4.1.3 ROPE: Routed Origin Policy Enforcement against Indirect Prompt Injection (Ma, Xiao, Yeoh, Zhang, Vorobeychik; WashU·JHU, arXiv 2608.27496)

**Conseca 인용 맥락(관련 연구, "구조적으로 가장 유사한 선행 연구"로 명시하며 비판):**
> "Conseca partially addressed this problem: it generates the per-task policy from trusted context alone, and it enforces the result deterministically. This is structurally similar to what we designed. Conseca differs in what a policy can say and in how far a weak policy generator can go wrong. Conseca's per-parameter constraints are syntactic regexes, which cannot separate a legitimate value from an injected one when both match the pattern, and its generator emits a free-form policy with no audited default beneath it."

**핵심 기제.** 도구 호출 인자에 대한 **출처(origin) 기반 정보흐름 제어**. 세 가지 신뢰 앵커(T1 사용자 요청, T2 사용자가 명시한 위조 불가 런타임 신원, T3 사용자 본인의 권위 있는 기록)를 정의한다. 태스크별 *라우터* LLM은 신뢰 요청만 읽고 명세 수준(완전 명세/파라미터 개방/행동 개방)과 범위를 출력하며, 결정적 컴파일러가 각 민감 파라미터에 출처 마커(prompt/sourced/record/dest/explicit/free)를 부여한다. 런타임 출처 추적기는 텍스트가 아니라 플랫폼 메타데이터(발신자 신원, 계정 소유권)로 값에 라벨을 붙이고, 강제는 결정적 출처 매칭으로 이뤄진다. 강제 시점에 LLM이 정당성을 판단하지 않는다.

**Conseca 대비 발전점.**
- Conseca의 **구문적(regex) 제약을 의미적(출처) 제약으로 대체**. 정규식을 통과하는 주입 값과 정당한 값을 구별 가능
- 작고 고정된 마커 어휘가 정책으로 컴파일되므로, 약하거나 저렴한 라우터 모델을 사용해도 **감사된 기본값(audited default)이 하한**을 보장. Conseca의 자유 형식 정책에 대한 직접적 개선
- 요청이 얼마나 위임적인지에 따라 정책 엄격도를 조건화
- AgentDyn(GPT-4o-mini): ROPE ASR 1.8%/클린 유용성 43.3% vs DRIFT 3.4%/18.3%, Progent 5.0%/6.7%. 적응형 공격(AutoDojo)에서 ROPE 1.8%→1.6%로 견고, DRIFT는 3.4%→7.4%로 악화. 장기 벤치마크 AgentLAB ASR 0%/유용성 65.8%

**한계.** 공격 성공 90건 중 44건은 도구 인자 밖(에이전트 *메시지* 내 피싱), 46건은 정당·주입 값이 동일 출처를 공유한 경우. 플랫폼이 위조 불가 출처 메타데이터를 노출해야 한다. 사람이 읽는 근거는 없고 민감 파라미터만 다룬다.

#### 4.1.4 Prismata: Confining Cross-Site Prompt Injection in Web Agents (Villa, Ozdarendeli, Tan, Popa; UC Berkeley, arXiv 2607.08147)

**Conseca 인용 맥락(관련 연구, 긍정적 동기):**
> "Some work (Tsai and Bagdasarian, 2025) has begun to explore solutions that leverage context to enable just-in-time security policies across open-ended tasks, balancing both utility with fine-grained controls."

**핵심 기제.** 에이전트와 브라우저 사이에 위치해 **관찰(observation)과 행동(action) 모두를 제한**한다. "정책 모델"은 DOM을 보지 않고 사용자 태스크만 읽어 필요한 콘텐츠 출처 클래스(개발자/사용자 생성/호스팅 서드파티/외부)를 결정한다. "Biba 파싱"은 구조적 단서(헤딩, 접근성 속성)로 DOM 노드에 출처 라벨을 재귀적으로 부여하고, 신뢰 경계 아래의 하위 노드는 라벨링에 영향을 못 미치게 하여 라벨 오류를 구조적으로 한정한다. "행동 게이트"는 각 상호작용 요소의 핵심 DOM 조상 경로만 보고 태스크 범위 여부를 판단한다.

**Conseca 대비 발전점.**
- Conseca의 "신뢰 입력만으로 실행 전 정책 생성"을 **웹 도메인**으로 옮기고, 행동뿐 아니라 **에이전트가 보는 것(관찰)까지 최소권한** 적용
- 규제 대상이 도구/인자 허용목록에서 **DOM 수준 구조적 출처 + Biba 무결성 라벨 전파**로 확장
- ASR 85.5% → 0.7%, 공격 하 태스크 성공 4.5% → 23.0%, 정상 태스크 성공 29.9% → 26.6%, 라벨링 정밀도 98.69%

**한계.** 웹 전용. 시맨틱 HTML/접근성 구조에 의존해 구조가 나쁜 사이트는 오라벨링. 정책 단위가 출처 클래스로 Conseca의 API 인자별 제약+근거보다 거칠다. 이미지/멀티모달 공격 미방어, 오버헤드가 크다(20 태스크당 정책 모델 +459초, 행동 게이팅 +1,098초).

#### 4.1.5 ControlValve — Breaking and Fixing Defenses Against Control-Flow Hijacking in Multi-Agent Systems (Jha, Triedman, Wagle, Shmatikov; Cornell·Microsoft, arXiv 2510.17276)

**Conseca 인용 맥락(관련 연구, 비판):**
> "Conseca (Tsai and Bagdasarian, 2025) relies on user requests and trusted internal context to define regex-based security policies and the corresponding runtime checks. It is not clear how to define regex policies that prevent context manipulation via control-flow hijacking and confused-deputy attacks."

**핵심 기제.** 먼저 LlamaFirewall류 정렬 검사(alignment check) 방어가 멀티에이전트 시스템의 제어흐름 하이재킹으로 우회됨을 보인다. ControlValve는 계획 시점(비신뢰 콘텐츠를 읽기 전)에 오케스트레이터가 (1) 허용되는 에이전트 호출 순서의 제어흐름 그래프(문맥 자유 문법, Lark로 컴파일)와 (2) 간선별 자연어 컨텍스트 규칙을 생성한다. 런타임에는 LLM 판정기가 "태스크와 정렬되는가"라는 개방형 추론 대신 CFG·간선 규칙에 대한 **좁은 검사**만 수행한다.

**Conseca 대비 발전점.**
- Conseca의 "실행 전·비신뢰 데이터 노출 전 정책 생성"을 **멀티에이전트 오케스트레이션의 제어흐름 무결성(CFI)**으로 확장. Conseca가 명시한 한계 (4) 궤적 수준 제약에 대한 한 가지 답
- 혼동된 대리인(confused deputy) 위협 모델을 명시
- CFH-Hard 코딩 벤치마크: 무방어 97~100%, LlamaFirewall 7~43%, ControlValve 0% ASR. 컴퓨터 사용: 67~89% → 0%. 정상 태스크 성능은 유지·개선(97% vs 93%)

**한계.** 간선 규칙은 자연어이고 LLM 판정기가 검사하므로 Conseca의 결정적 강제보다 약하다. 생성된 CFG가 과대/과소 근사될 수 있고 런타임 오버헤드가 있다. Conseca에 대한 비판(정규식이 제어흐름 제약을 표현 못함)은 타당하나 실험으로 검증하지는 않았다.

#### 4.1.6 Dynamic Capability Scoping for Enterprise AI Agents (Noyan; AIWILD@ICML 2026, arXiv 2607.22445)

**Conseca 인용 맥락(설계 절, 명시적 대비):**
> "This differs from prior context-aware approaches such as Conseca (Tsai and Bagdasarian, 2025), which generates just-in-time policies per action from trusted context but evaluates the agent's own action attempts. Source 2 instead predicts the full task-required permission set up front from the user's task description."

**핵심 기제.** 세 원천의 교집합에서만 권한 부여: (1) 조직 정책에서 결정적으로 도출한 역할 기반 상한, (2) 사용자 태스크 설명만으로 필요한 권한 집합을 예측하는 **미세조정 다중라벨 분류기**(에이전트 실행 전, 에이전트 출력과 무관), (3) 위험한 조합을 금지하는 정책 기반 조합 금지("치명적 삼중주": 개인 데이터 + 비신뢰 콘텐츠 + 외부 통신). 배포되지 않은 자격 증명은 오용될 수 없다. 강제 모드와 관찰 전용 모드(범위 밖 요청을 정렬 실패 신호로 기록)를 지원한다.

**Conseca 대비 발전점.**
- 런타임 행동 검사 대신 **자격 증명 부재에 의한 예방**. Conseca의 "LLM 없는 정책" 질문에 경량 분류기로 답
- 정책 생성기를 LLM에서 작은 분류기로 대체해 비용·인젝션 가능성 감소, 조합 금지 규칙 추가
- 600개 기업 프롬프트·15개 권한 분류 체계 데이터셋. 전문가 검토 후 Cohen's κ 0.967, 심각도 가중 과대권한 15.0 → 2.0(86.7% 감소)

**한계.** 15개 권한 수준의 거친 세분화(인자 수준 제약 없음). 태스크 중 발견되는 권한 필요에 대응 불가. 분류기에 비신뢰 텍스트가 들어가면 인젝션 취약. 합성 데이터와 단일 검토자, 공격/유용성 벤치마크 없음.

#### 4.1.7 Autoformalization of Agent Instructions into Policy-as-Code (Mondl, Maisel, Brock; Sondera, AIWILD@ICML 2026, arXiv 2606.26649)

**Conseca 인용 맥락(선행 연구, 컨텍스트 인식 정책의 필요성 근거):**
> "As AI agents have arisen with the ability to autonomously control and call tools in a loop, the need to define context-aware policies to govern their behavior has emerged (Tsai & Bagdasarian, 2025)."

**핵심 기제.** 3계층 파이프라인: 접지(grounding) 계층이 엔터티와 MCP 도구 스키마를 추출, 모델 계층의 LLM이 Amazon **Cedar** 정책 언어로 후보 정책 생성, 안전 계층이 하드 비평가(Cedar 구문·스키마 검증)와 소프트 비평가(LLM-as-judge 의미 정합성)를 생성기-비평가 루프로 적용해 통과할 때까지 반복한다. 검증된 Cedar 정책은 에이전트 추론과 분리된 결정적 외부 엔진이 강제한다.

**Conseca 대비 발전점.**
- Conseca의 정규식을 **형식적으로 명세된 정책 언어(Cedar)**로 대체하고 기계 검증 가능한 유효성 확보. Conseca가 향후 과제로 언급한 "근거의 형식 검증"에 접근
- 1회 생성 대신 반복 비평가 루프. 입력에 사용자 요청뿐 아니라 조직 정책 문서·도구 설명 포함
- MedAgentBench에서 88개 규칙 자동 생성(기존 수작업 23개). POST 쓰기 시도 궤적 차단율 98.8~100%

**한계.** 정책이 요청/목적별 just-in-time이 아니라 배포별 오프라인 생성. Cedar는 무상태여서 순서·다중 턴 제약 미지원. 규칙별 근거 제시는 강조되지 않는다.

#### 4.1.8 Policy-as-Prompt: Turning AI Governance Rules into Guardrails for AI Agents (Kholkar, Ahuja; Pure Storage, Regulatable ML@NeurIPS 2025, arXiv 2509.23994)

**Conseca 인용 맥락(서론, Conseca의 요구를 구현했다고 직접 주장):**
> "As recent research points out, security for these flexible agents needs to be just-in-time and context-aware (Kholkar and Ahuja, 2025; Tsai and Bagdasarian, 2025). ... Our system offers a practical way to implement the contextual security that Tsai and Bagdasarian (2025) called for."

**핵심 기제.** POLICY-TREE-GEN이 LLM으로 PRD·TDD·코드를 읽어 요구사항을 분포 내/외 입력·출력 범주(ID-I, OOD-I, ID-O, OOD-O)로 분류하고 각 규칙을 원본 예시에 연결한다. POLICY-AS-PROMPT-GEN은 사람이 검토한 트리를 마크다운 few-shot 프롬프트로 컴파일해 기본 거부 자세의 경량 LLM 분류기가 런타임에 입력과 출력을 판정하며 출처·감사 로그를 남긴다. 후속 논문 "The AI Agent Code of Conduct"(같은 저자)도 동일 계열이다.

**Conseca 대비 발전점.**
- 정책의 원천을 사용자 요청에서 **조직의 설계 산출물**로 확장. 거버넌스·컴플라이언스(추적성, 사람 승인) 프레이밍
- 도구 호출뿐 아니라 **출력 콘텐츠**(유해성, 범위 외)까지 대상
- 정책 추출 F1 60.0%(HR), 런타임 분류기 GPT-4o 입력 73%/출력 71% 정확도

**한계.** 강제 자체가 프롬프트 기반 LLM 분류기라 **결정적이지 않다**. Conseca가 피하려던 인젝션·비일관성 위험을 강제 계층이 그대로 물려받는다. 정책이 요청별이 아니라 애플리케이션별이며 평가 규모가 작다. 흥미롭게도 Gemini CLI의 Conseca 구현(2장)도 같은 방향(LLM 강제)으로 후퇴했다.

#### 4.1.9 CSAgent: Secure and Efficient Access Control for Computer-Use Agents via Context Space (Gong, Li, Chang, Shen; Zhejiang University, arXiv 2509.22256)

**Conseca 인용 맥락(관련 연구, "동적 정책 생성" 그룹으로 분류하며 정적 접근의 우위를 주장):**
> "Conseca and Progent achieve dynamic security policy generation, enabling more autonomous responses to diverse task scenarios."

**핵심 기제.** 개발 시점에 정의되는 정적·의도·컨텍스트 인식 정책. 클래스 → 함수 → 의도 → 정책 구조로, 각 정책은 "컨텍스트 공간"(시스템/사용자 상태 변수)에 대한 논리 제약 집합이다. LLM 기반 컨텍스트 분석기가 API 문서·CLI 매뉴얼·GUI 앱 소스로부터 후보 정책을 자동 생성한다. 런타임에는 OS 수준 서비스가 행동을 가로채고 LLM으로 사용자 의도를 추출해 대응 정책을 가져온 뒤 현재 컨텍스트 벡터로 제약을 검증한다. 정책 진화 프레임워크가 런타임 피드백으로 정책을 개선하고, 컨텍스트 관리자(핫/웜/콜드 캐시)가 오버헤드를 낮춘다.

**Conseca 대비 발전점.**
- **OS 수준 강제**로 API·CLI·**GUI** 컴퓨터 사용 에이전트까지 커버
- 정책을 요청별 생성이 아니라 배포 전 고정하여 개발자가 감사·검토 가능. "just-in-time"을 예측 가능성과 교환
- AgentDojo ASR 46.61% → 0%, 지연 오버헤드 1.99%, 평균 유용성 저하 5.42%

**한계.** 정적 정책은 진정으로 새로운 요청별 목적에 적응 불가. 의도 추출은 여전히 런타임 LLM 의존. GUI 정책 생성에 앱 소스 필요, 단일 에이전트, 웹 환경 취약.

### 4.2 강제 계층 확장 계열(정보흐름·제어흐름·자원 모델)

이 계열은 Conseca의 "결정적 참조 모니터" 부분을 계승하되, 정책이 말할 수 있는 대상을 **데이터 출처, 흐름 경로, 자원**으로 확장한다. 다만 대부분 정책을 운영자가 수작업으로 작성하므로, Conseca의 "태스크별 자동 생성"은 계승하지 않는다. 이들은 Conseca의 정책 생성기가 얹힐 수 있는 **강제 인프라**로 보는 것이 적절하다.

#### 4.2.1 AgentFlow: A Flow-Centric Policy Language and Framework (Shivakumar, Priya, Gao; Virginia Tech, arXiv 2608.22868)

**Conseca 인용 맥락(서론·관련 연구, 보완적):**
> "Conseca generates task-specific policies, while AgentArmor analyzes runtime traces. ... AgentFlow complements these systems by making lineage, labels, and path constraints explicit policy objects."

**핵심 기제.** 참조 모니터가 도구 호출과 응답 싱크를 가로챈다. 모든 데이터 객체는 다차원 라벨(민감도 격자 Public..TopSecret, 계층적 범주 분류, 신뢰/비신뢰)을 가지며 전이 함수로 전파되고 계보(lineage) DAG에 기록된다. 정책은 *흐름 규칙*(단일 홉)과 *경로 규칙*(다단계 이력), 태스크 범위 능력, 명시적 해제(declassification) 컨텍스트를 갖는 흐름 중심 언어로 작성된다. SMT 기반 검증기가 배포 전 정책의 유계 안전 속성을 검사한다.

**발전점.** Conseca가 다루지 않은 **정보흐름 제어·계보·경로(이력) 제약·형식 검증·멀티에이전트 위임 경계**를 정책 객체로 만든다. AgentDojo 유용성 46.7% → 63.3%, 손상률 33.0% → 0.0%. 인터셉트당 6.4μs.

**한계.** 태스크로부터의 자동 정책 생성 없음(운영자가 스위트별로 작성). 메시지 중심 워크플로에서 과잉 오염(overtainting). 비신뢰 콘텐츠를 정당하게 전달해야 하는 태스크에는 명시적 해제 규칙 필요.

#### 4.2.2 AgentArmor: Enforcing Program Analysis on Agent Runtime Trace (Wang et al.; ByteDance, arXiv 2508.01249)

**Conseca 인용 맥락(관련 연구, 대비되는 부류로 분류):**
> "Diverging from Information Flow Control paradigms, other approaches focus on declarative policy languages and Domain-Specific Languages (DSLs) to manage tool access [Progent, Conseca, ...]. However, these works can not track the sensitive data flow among the agent runtime, making them prone to privacy leakage attacks."

**핵심 기제.** 에이전트 런타임 트레이스를 프로그램으로 취급한다. 그래프 생성기가 트레이스에서 도구 호출 파라미터 수준까지 데이터·제어 의존성을 갖는 프로그램 의존 그래프(PDG)를 만들고, 그래프 주석기가 각 노드에 기밀성×무결성 격자 라벨과 규칙 타입을 부여하며(일부 LLM 보조), 그래프 검사기가 타입 검사(높은 기밀성 → 낮은 기밀성 흐름 금지, 낮은 무결성 소스의 영향 금지)와 노드별 규칙을 평가해 위반 행동을 실행 전 차단한다.

**발전점.** Conseca의 정규식 제약은 현재 호출의 인자만 보지만, AgentArmor는 **전체 트레이스에 대한 세밀한 taint/IFC와 격자 타입 시스템**을 제공한다. AgentDojo ASR 3%(GPT-4o-mini), 유용성 72% vs 무방어 73%, Progent 64%, CaMeL 48%.

**한계.** 규칙이 사전 정의되어 있고 just-in-time 생성이 아니다. 논문 스스로 "동적 생성 규칙 타입"을 향후 과제로 명시하는데, 이는 곧 Conseca의 기여다. 의존성 추론이 LLM에 의존해 우회 여지가 있고, 근거 제시가 없다.

#### 4.2.3 SEAgent: Taming Various Privilege Escalation in LLM-Based Agent Systems (Ji, Wu, Jiang, Ma, Li, Gao, Wang, Li; arXiv 2601.11893)

**Conseca 인용 맥락(서론, 그룹 비판):**
> "Notable examples include Conseca, Security Analyzer, AgentArmor, and Progent. Nevertheless, these frameworks exhibit rather narrow practicality; most of them exhibit limited defense coverage by primarily focusing on simple indirect prompt injection attacks, failing to address broader attack vectors."

**핵심 기제.** SELinux에서 영감을 받은 강제적 접근 제어(MAC). 에이전트·도구·RAG 데이터베이스에 정적 보안 속성(무결성 수준, 민감도, 행동 유형)을 부여하고, 시스템 뷰가 사용자→에이전트, 에이전트→도구, 도구→에이전트, 에이전트→에이전트, DB→에이전트 간선의 정보흐름 그래프를 구성한다. 결정 엔진이 관찰된 경로를 정책 DB(목표 deny/allow/ask + 경로 패턴 + 속성 규칙)와 first-match로 대조한다. SEMemory가 오염된 컨텍스트를 재도입하지 않고 안전한 컨텍스트를 라운드 간 유지한다.

**발전점.** 문제를 **권한 상승**(RAG 오염, 멀티에이전트 혼동된 대리인 포함)으로 재정의하고 정적 라벨 MAC과 경로 패턴으로 커버리지를 넓혔다. InjecAgent·AgentDojo ASR 0%, API-Bank 태스크 정확도 74.73%, 정책 검사 약 0.006초.

**한계.** 정적 속성은 런타임 적응 불가, 라벨 생성에 수동 검증 필요, 기본 정책 4개 외 시나리오별 정책은 수작업. 열린 사용자 요청에 대한 just-in-time 컨텍스트 최소권한은 없다.

#### 4.2.4 AC4A: Access Control for Agents (Sharma, Grossman; University of Washington, arXiv 2603.20933)

**Conseca 인용 맥락(관련 연구, Progent와 함께 "가장 가까운 연구"로 소개하며 자원 모델과 대비):**
> "Progent and Conseca are closest to AC4A in providing access control specifically for agents. They differ in how policies are defined. ... Conseca takes a context-aware approach. A separate Policy Generator LLM, given only trusted context (user intent, system state), produces a task-specific security policy for each request. ... AC4A differs from both by modeling permissions over resources rather than over tool calls or task contexts."

**핵심 기제.** 자원 중심 접근 제어. 애플리케이션이 계층적 자원 타입 트리, 행동, 미충족 권한을 계산하는 `resource_difference` 함수를 정의한다. 에이전트는 런타임에 권한을 요청하고, AC4A가 API 호출과 DOM 상호작용을 가로채 필요한 권한을 계산해 부여 내역과 대조하며, 거부는 설정 가능한 핸들러로 라우팅한다. API 기반과 브라우저 기반 에이전트를 동일 모델로 다룬다.

**발전점.** **API와 브라우저 표면을 아우르는 균일한 자원 추상화**(동일 권한이 두 접근 경로를 모두 커버). OS식 기제/정책 분리.

**한계.** 정량 평가 없음(두 사례 연구). 정책 도출은 의도적으로 범위 밖(수동, LLM 보조, 요청 기반 추론 모두 가능). 조건부 제약("200달러 미만 결제만") 표현이 어렵다. Conseca류 정책 생성기의 **강제 백엔드**로 결합될 가능성이 있다.

#### 4.2.5 Web Agents Should Adopt the Plan-Then-Execute Paradigm (Piet, Chow, Hou, Lyu, Venuto, Zhu, Popa, Wagner; UC Berkeley, arXiv 2605.14290)

**Conseca 인용 맥락(토론 절 "대안적 관점", 정책 모니터 접근의 약점을 지적하며 그 보완책으로 언급):**
> "A runtime policy monitor could be used to reject actions unaligned with user intent. However, complete mediation is hard to achieve: policies are expensive to write, may not be expressive enough ... Policies could be auto-generated [Tsai & Bagdasarian] and a model could auto-approve actions."

**핵심 기제.** ReAct를 Plan-Then-Execute로 대체. 플래너는 사용자 요청과 신뢰된 타입 API 스키마만 읽고 결정적 프로그램을 산출한다. 실행 단계는 그 프로그램을 돌리며 비신뢰 웹 콘텐츠는 타입화된 데이터 파라미터와 격리된 LLM 서브루틴으로만 흐른다. 주입 콘텐츠는 사전 정의된 분기 내 데이터 값에 영향을 줄 수 있지만 행동을 추가하거나 제어흐름을 바꿀 수 없다.

**발전점.** "보안 관련 결정은 비신뢰 콘텐츠 노출 전 신뢰 요청으로부터 내린다"는 Conseca의 원칙을 **정책 대신 프로그램**으로 구현. 별도 강제기 없이 계획 자체가 제약이 된다. WebArena 860 태스크 중 81.28%가 런타임 LLM 없이 "Safe".

**한계.** 프롬프트에서 제어흐름을 결정할 수 있는 태스크만 가능하고 탐색 위주 태스크는 배제. 사이트가 시맨틱 API를 노출해야 한다(Postmill의 REST API 16개가 129 태스크 중 33%만 커버). Conseca의 태스크 중 just-in-time 적응은 없다.

#### 4.2.6 Firewalls to Secure Dynamic LLM Agentic Networks (Abdelnabi, Gomaa, Bagdasarian, Kristensson, Shokri; TMLR, arXiv 2502.01822)

**Conseca 인용 맥락.** 버전 의존적이다. v5(2025년 5월)에는 "allowed actions and data flows can be decided before interacting with untrusted data (... Tsai and Bagdasarian, 2025)"로 인용되었으나, 현재 v6/v7(2026)에서는 해당 인용이 제거되었다(원문 확인). 공저자 논문이라는 점에서 Conseca와 같은 연구 계보에 속한다.

**핵심 기제(v7).** 사용자 어시스턴트와 외부 서비스 에이전트 사이의 이중 방화벽. Language Converter Firewall은 들어오는 자연어를 닫힌 스키마 타입 프로토콜(열거형 필드)로 변환해 결정적으로 검증하므로 자유 텍스트 인젠션이 어시스턴트에 도달하지 못한다. Data Abstraction Firewall은 사용자 개인 데이터를 태스크에 적절한 세분화 수준으로 추상화한다. 두 방화벽 규칙은 시연 대화로부터 오프라인 자동 학습된다.

**발전점.** Conseca의 "태스크가 컨텍스트를 정의한다"는 원리를 **에이전트 간 네트워크와 프라이버시(Contextual Integrity식 데이터 추상화)**로 확장. ConVerse 벤치마크 프라이버시 ASR 84.68% → 10.20%, 보안 ASR 60.39% → 3.42%, 계획 품질 유지.

**한계.** 규칙이 도메인별·오프라인 학습으로 요청별 just-in-time이 아니다. 올바른 타입이지만 거짓인 데이터는 막지 못하고 개방형 도메인에 취약.

#### 4.2.7 Agent Control Protocol: Admission Control for Agent Actions (Fernandez; arXiv 2603.18829)

**Conseca 인용 맥락(관련 연구, 원리적 동기):**
> "Tsai and Bagdasarian argue at HotOS 2025 that security policies must be purpose-specific rather than uniformly applied ... a perspective consistent with ACP's per-agent isolation and stateful enforcement boundaries."

**핵심 기제.** 모든 행동 요청에 6단계 승인 제어: Ed25519 기관 키 신원 검증, 위임 체인을 갖는 능력 토큰 검증, 상태 기반 위험 평가(정적 점수 + 누적 이상 신호, 쿨다운), 결정(승인/에스컬레이션/거부), 일회용 실행 토큰, 서명된 추가 전용 원장.

**발전점.** Conseca가 다루지 않은 **요청 간 상태 기반 시간적 행동 분석, 암호학적 신원, 변조 방지 감사, 기관 간 배포, 프로토콜 불변식 모델 검사**. 결정당 약 0.8μs. 개별적으로 유효한 500건 요청 중 상태 기반 엔진은 2건(0.4%)만 자율 실행.

**한계.** 정책 계층에서는 "목적별 정책" 원리만 차용. 태스크에 대한 컨텍스트 이해나 인자 수준 제약, 근거가 없고, 업스트림 프롬프트 인젝션은 명시적으로 범위 밖이다.

### 4.3 사용자 참여·개인화·Contextual Integrity 계열

Conseca는 정책의 원천을 "LLM이 이해한 사용자 선호·사회적 규범"에 두었고, 사람은 생성된 근거를 사후 검증하는 역할이었다. 이 계열은 정책의 원천과 사람의 역할을 재정의한다. Conseca 공저자(Bagdasarian, Tsai)의 직접 후속 연구 세 편(Janus, AI Agents May Always Fall for Prompt Injections, GAAP)이 여기에 속하며, 각각 Conseca의 서로 다른 약점을 공격한다.

#### 4.3.1 GAAP: An AI Agent Execution Environment to Safeguard User Data (Stanley, Verma, **Tsai**, Kallas, Kumar; UCLA·Google, arXiv 2604.19657)

**Conseca 인용 맥락.** 관련 연구, 비교표(Table 1), 그리고 **평가 베이스라인**의 세 가지 역할. 인용 논문 중 Conseca를 실제로 구현·실험한 유일한 논문이다.
> "Conseca sandboxes a tool-calling agent with contextual tool call policies generated by an isolated LLM informed only by trusted context. ... Because Conseca relies on trusted data, we give it only segments of the system prompt defining the available tools and database, but not the prompt or context. We also let Conseca ask the user for a policy in highly uncertain cases."

**핵심 기제.** 개인 데이터와 권한을 에이전트 LLM이 읽을 수 없는 데이터베이스에 두고, 에이전트가 산출한 코드 아티팩트의 실행에 **동적 정보흐름 제어(taint tracking)**를 적용한다. 추적은 도구 호출 간, LLM 라운드 간(multi-shot), 그리고 영속적 Disclosure Log를 통해 태스크 간에도 이어진다. 사용자는 (개인 데이터 유형, 외부 수신자) 쌍에 대한 허용/거부로 권한을 지정하며, 이는 필요할 때 수집되어 Permission Database에 영속된다. 보장은 결정적이며 프롬프트·모델·에이전트가 모두 비신뢰여도 성립한다.

**Conseca 대비 발전점.**
- 강제 경로에 **신뢰 LLM이 전혀 없음**. Conseca의 "정책 생성기는 안전한 LLM"이라는 가정을 제거
- 사용자 결정이 영속되어 태스크 간 **프라이버시 회계**가 가능. Conseca는 도구 호출별 결정을 재사용하지 못함
- 사용자 개입을 잘 정의된 (데이터, 수신자) 질문으로 한정

**Conseca에 대한 실증 결과(가장 날카로운 비판).**

| 지표 | 무방어 | GAAP | LLM-Judge | **Conseca** |
|---|---|---|---|---|
| 자체 20태스크 유용성 | 81.0% | 76.0% | 75.0% | 72.0% |
| AgentDojo 유용성 | 80.1% | 64.6% | 69.8% | **45.3%** |
| SSN 유출 공격 차단 | 25% | 100% | 85% | 100% |
| SSN을 전화번호로 위장(SSN-swap) 차단 | 실패 | 성공 | 실패 | **실패** |

> "Conseca's lack of context leads it to aggressively reject tool calls without asking the user." / "an SSN disguised as a phone number looks innocuous in an email, Conseca, without context, approves the request."

즉 신뢰 컨텍스트만 보는 설계는 정책 생성기에 정보를 굶겨 **과도 거부**(AgentDojo 유용성 45.3%)와 **의미적으로 위장된 유출 미탐지**를 동시에 낳는다. Conseca 원논문의 한계 (2)를 정량적으로 확인한 것이다.

**한계.** GAAP은 기밀성만 보호하고 무결성(데이터를 유출하지 않는 인젠션)은 막지 않는다. 저자들은 두 접근이 상보적이라고 명시한다.

#### 4.3.2 Janus: a Playground for User-Involved Agentic Permission Management (Brigham, **Bagdasarian**, Kohno, Roesner; UW·UMass·Georgetown, arXiv 2607.01510)

**Conseca 인용 맥락(관련 연구 및 설계 공간 Table I):**
> "Conseca proposes a privileged 'policy generator' that creates task and context specific policies, under the theory of contextual integrity." / "in Conseca and Claude Auto Mode, the system uses an LLM to assess the sensitivity of a tool call based on the user's prompted task."

**핵심 기제.** 연구 인프라. Janus-Core(이메일·캘린더·파일 도구와 플러그형 "권한 어시스턴트"를 갖는 모듈형 에이전트 프레임워크)와 Janus-Harness(시나리오, 사용자 의도를 인코딩한 하위 시나리오, 사용자 행동을 모사하는 합성 "응답자"로 구성된 자동 평가). 다섯 축(영속 정책, 정책 밖 자율성, 사용자 참여 수준, 근거 기반, 성찰)의 설계 공간을 제안하고 여섯 가지 어시스턴트(risk_assessment, auto_approve, user_confirmation, constitution, policy_suggestion 등)를 구현했다.

**Conseca 대비 발전점.**
- **사용자를 권한 결정의 참여자**로 명시적으로 다룬다(Conseca의 사람은 근거의 사후 검증자). Conseca 향후 과제 "사용자 상호작용"을 체계적으로 탐구
- 사용자 참여 vs 권한 피로의 정량 연구. 정렬 인식 응답자와 결합한 user_confirmation은 공격 실행 0%, risk_assessment는 허용치 0.2에서 공격의 40~60% 차단, 0.7로 올리면 메시지 수는 절반이지만 공격 실행은 약 두 배
- 설계 지침: 잘못된 사용자 승인에 대비한 설계, 비결정성 최소화, 영속 정책의 장기 영향 고려

**한계.** 위협 모델이 (적대적일 수 있는) 데이터에 한정. 시나리오 3개×하위 4개로 규모가 작고, 실제 사용자 연구 없이 메시지 수를 인지 부하의 대리 지표로 사용.

#### 4.3.3 AI Agents May Always Fall for Prompt Injections (Abdelnabi, **Bagdasarian**; arXiv 2605.17634)

**Conseca 인용 맥락(서론, 유망하나 초기 단계인 방어 방향으로):**
> "Approaches like contextual security (Tsai and Bagdasarian, 2025) and semantic firewalls could dynamically protect an agent, yet are only early steps in fully determining the appropriateness of contexts."

**핵심 논증.** 프롬프트 인젠션을 **Contextual Integrity(CI)** 이론으로 재해석한다. 공격은 데이터에 명령을 숨기는 것이 아니라 CI 파라미터(발신자, 수신자, 주제, 정보 유형, 전송 원칙)나 에이전트의 규범 평가를 하이재킹함으로써 성공한다. **불가능성 결과**: 공격자는 언제나 "참이라면 그 행동을 정당화할" 파라미터 값을 주장할 수 있으므로, 고정된 정책은 모든 조작된 컨텍스트 공격을 막으면서 정당한 흐름을 보존할 수 없다. 규범을 강화하면 반드시 정당한 요청도 막는다.

**Conseca 대비 발전점.**
- Conseca가 아키텍처로 접근한 것을 **이론적으로 정초**하고, 컨텍스트 기반 정책이 도달할 수 있는 상한을 부정적 결과로 제시
- Prompt Guard의 컨텍스트 조작 공격 AUROC 0.43~0.59, 컨텍스트 파라미터 공격 성공률 96.7%(베이스라인 0.67%) 등 분류기와 안전 훈련이 컨텍스트 조작에 실패함을 실증
- 시스템 계층이 컨텍스트 주장을 *추론*하지 말고 **검증**(증명, 외부 기록)해야 한다고 주장. 이는 ROPE(4.1.3)의 출처 기반 접근과 정확히 맞닿는다

**한계.** 위임 범위가 명시적이라고 가정하지만 실제 사용자는 모호하게 위임. 규범 근거로 쓰는 상호작용 이력 자체가 공격 표면. 적절성 라벨은 주관적·문화 의존적.

#### 4.3.4 How Agents Ask for Permission (Michael, Roesner; UW, arXiv 2607.13718)

**Conseca 인용 맥락.** 21개 학술 권한 시스템 서베이의 분류 대상([53]). Conseca는 "사용자 대면 명세 없음", "사용자 질의·암묵적 컨텍스트로부터 AI 예측", "비-AI 결정적 강제", "선의이나 오류 가능한 에이전트" 위협 모델로 분류된다.

**핵심 논증.** 문헌에서 세 가지 반복 목표(낮은 사용자 부담, 형식적 근거, 결정적 강제)를 식별하지만 **21개 중 어느 시스템도 셋을 동시에 달성하지 못한다**. 상용 에이전트(Claude, ChatGPT agent, Codex 등)는 높은 부담의 사용자 개입 또는 불투명한 LLM 자동 검토를 기본값으로 삼는다. 12/21이 결정적 강제, 11/21이 형식적 근거, 6/21만 명세 후 정책 업데이트 허용.

**Conseca에 대한 시사.** "암묵적 컨텍스트 정책 예측은 예측된 정책과 사용자 의도 정책의 불일치 위험이 있다." 조사된 어떤 시스템도 강제를 형식 검증하지 않으며, 지속적·명세 후 제어가 부족하다.

#### 4.3.5 Reframing LLM Agent Security as an Agent-Human Interaction Problem (Wang, Li, Tian; UCLA, arXiv 2605.24309)

**Conseca 인용 맥락(정책 명세 범주 C1 분석 전반):**
> "LLM-generated policy with human review (Conseca, AGrail, DRIFT, AgentGuardian) accounts for 4 papers and 0 production layers." / "The high-security low-burden quadrant is occupied only by academic proposals: RTBAS, TaskShield, CaMeL, and Conseca (C1 dynamic policy). The same mechanisms that could in principle dominate the desirable quadrant are the ones with zero production adoption."

**핵심 논증.** 에이전트 보안 실패는 근본적으로 에이전트-인간 상호작용 실패다. 사람은 쓸 수 없는 정책을 작성하고, 평가할 수 없는 행동을 승인하고, 검증할 수 없는 출력을 신뢰하도록 요구받는다. 학술 논문 13편과 상용 시스템 21개를 다섯 범주로 분석해 보안-사용성 평면에 투영한다.

**Conseca 대비 발전점.** 학계-산업 격차의 체계적 분석. Conseca류 동적 정책은 학술적 최전선이지만 **상용 배포 0건**(이 리포트가 확인한 Gemini CLI 구현은 이 조사 시점 이후 또는 범위 밖). "사람이 정책을 *작성*하지 않고 LLM 초안을 *편집*한다"는 제안으로 사람을 최종 권위자로 재배치. 주의: 이 논문은 Conseca의 강제를 "LLM-as-checker"로 분류하는데, 원논문의 강제는 결정적이므로 부정확한 서술이다(다만 Gemini CLI 구현에는 정확히 부합한다).

#### 4.3.6 ARIEL: Personalizing Agent Privacy Decisions via Logical Entailment (Flemings, Yi, Suciu, Fawaz, Annavaram, Gruteser; USC·Google Research·UW-Madison, PETS, arXiv 2512.05065)

**Conseca 인용 맥락(한계 절, 적대적 방어를 위임하는 상보적 구성요소로):**
> "defense against adversarial attacks, such as prompt injection, is delegated to separate system components that focus specifically on these attacks (Meng et al., 2025; Tsai and Bagdasarian, 2025)."

**핵심 기제.** 사용자의 *과거* 프라이버시 판단이 새 데이터 공유 요청에 대한 결정을 논리적으로 함의(entail)하는지 판정한다. LLM이 과거 판단으로부터 사용자별 온톨로지(데이터 민감도 계층, 수신자 신뢰 순서)를 구축하고, 결정적 함의 규칙이 새 요청을 이전 요청에 대응시킨다. 함의가 성립하면 투명하게 결정하고, 아니면 사용자에게 에스컬레이션한다.

**Conseca 대비 발전점.** Conseca가 태스크·신뢰 컨텍스트로부터 정책을 도출하는 데 비해 ARIEL은 **사용자 본인의 이력으로 개인화**한다. LLM 온톨로지 생성과 결정적 추론의 신경기호적 분리, 특정 과거 결정에 연결된 감사 가능한 추론. SPA 데이터셋 F1 87.2%(ICL 82.4%), ICL 대비 F1 오류 40.6% 감소.

**한계.** 비적대적 설정 가정(적대적 방어는 Conseca류에 위임). 조건부 의존성 표현 불가, 선호 변화 미처리, 콜드 스타트.

#### 4.3.7 PSG-Agent: Personality-Aware Safety Guardrail (Wu et al.; arXiv 2509.23614)

**Conseca 인용 맥락(서론·관련 연구, 적응형 LLM 가드레일로 분류 후 비판):**
> "adaptive LLM-based methods, such as Conseca and Agrail, which generate safety policies tailored to specific contexts and tasks. However, current methods have two limitations: (1) They apply a 'one-size-fits-all' unified strategy, ignoring that the same agent behavior can have very different risk levels for different users ... (2) They perform static detection on single-round output, failing to track cumulative risks in multi-round interactions."

**핵심 기제.** 프로파일 마이너가 대화 이력에서 안정적 사용자 특성을, 입력 가드가 실시간 상태를 추출해 개인화된 안전 기준을 생성하고, Plan Monitor·Tool Firewall·Response Guard·Memory Guardian이 파이프라인 여러 지점에서 강제하며 턴 간 누적 위험을 추적한다.

**Conseca 대비 발전점.** "사용자 프로파일 × 컨텍스트 상태 × 에이전트 행동"의 개인화 위협 모델과 **턴 간 위험 누적**. Conseca 한계 (4)(궤적 수준 피해)에 대한 사용자 안전 관점의 답. 정확도 0.797/F1 0.744(LlamaGuard3 0.583/0.262). 대상이 도구 호출 보안이 아닌 사용자 웰빙이라는 점에서 방향이 다르다.

#### 4.3.8 Overlaying Governance (Ibrahim, Li; Huawei, arXiv 2606.03518) 및 Governance by Construction / CUGA (Shlomov et al.; IBM Research, CAIS '26, arXiv 2605.20874)

두 논문은 Conseca를 한 줄씩 인용한다. Overlaying Governance는 "행동 공간 전체를 제약하는 것보다 자원 접근을 제약하는 것이 더 다루기 쉽다"는 설계 전제의 근거로, CUGA는 "프롬프트 엔지니어링·사후 검증에 의존하는 거버넌스 전략"의 예로 인용한다(Conseca의 결정적 사후 검사를 고려하면 느슨한 분류다).

- **Overlaying Governance**: 위임을 일급 인가 기본 요소로 취급. 타입화된 그래프 재작성 "오버레이" 연산자가 기존 ReBAC 스키마(OpenFGA)에 위임 체인·범위 봉투·세션을 주입한다. 에이전트는 사람 주체가 접근 권한을 갖고, 유효한 위임 체인이 사람과 에이전트를 연결하고, 호환되는 범위 안에서 행동할 때만 인가된다. 건전성 증명 포함, 정책 경로에 LLM 없음. 780k 관계에서 검사 지연 중앙값 2~7ms
- **CUGA**: 다섯 가지 타입화된 기본 요소(Intent Guard, Playbook, Tool Guide, Tool Approval, Output Formatter)가 고정 체크포인트에서 실행을 가로채는 정책-코드 계층. 사람이 작성한 영속 기업 정책. OAK 벤치마크 태스크 성공률 75% → 100%(GPT-OSS-120B)로 **거버넌스가 유용성도 높인다**는 결과

둘 다 Conseca와 상보적이다. Conseca가 "이 태스크에 무엇이 필요한가"를 답한다면, 이들은 "누가 무엇을 누구에게 위임할 수 있는가"와 "조직 정책을 어디서 강제하는가"를 답한다.

### 4.4 평가·비판·형식화 계열

이 계열은 새 시스템보다 Conseca류 "LLM 생성 정책 + 결정적 강제" 방어의 **약점을 체계화**한다. 인용 논문 전체에서 반복되는 비판은 일곱 가지로 수렴한다(5장 표 참조).

#### 4.4.1 AIOracles: Extending the Formalism and Theoretical Foundations of Cryptography to AI (Villa, Durak, Kohno, Maharramli, Roesner; ETH·MSR·Georgetown·UW, arXiv 2603.02590)

Conseca에 **전용 절(§5.2.3)**을 할애한 유일한 논문이다. AIOracle 추상화로 Conseca를 "이중 구성(dual construction)"으로 형식화한다(플래너 = AIOracle, 실행기 = 환경, 정책 생성기 = 비평가 AIOracle).

> "A significant limitation of Conseca is its vulnerability to adversarial planning attacks, where a compromised planner strategically evades security policies. Since the planner processes all (un/trusted) context while Conseca is assumed to see trusted context, a planner compromised via prompt injection can model Conseca's policy generation and propose sequences of individually benign-looking actions that collectively achieve malicious goals. ... Conseca's approach of using an LM-based policy generator to defend against prompt injection attacks on the planner LM creates a fundamental 'LM-to-secure-LM' paradox."

**기여.** (1) **적대적 계획(adversarial planning)** 공격을 명명: 오염된 플래너가 정책 생성을 모델링해 개별적으로는 무해해 보이는 행동 시퀀스를 구성. Conseca가 행동 단위로만 검사한다는 한계 (4)를 공격 가능성으로 구체화. (2) **"LM으로 LM을 보호하는 역설"**: 정책 생성기가 안전한 AIOracle이라는 암묵적 가정이 보안 보장을 약화. (3) Progent와 Conseca를 비교 가능하게 하는 공통 형식 어휘 제공. 순수 이론 논문으로 실험은 없다.

#### 4.4.2 Adaptive Evaluation of Out-of-Band Defenses Against Prompt Injection (Narisetty et al.; LaunchSafe Research, arXiv 2606.26479)

CaMeL, FIDES, Progent, Conseca, RTBAS, FORGE, Dual-LLM 일곱 방어를 Biba 무결성·참조 모니터·IFC 기본 요소로 8차원 체계화한다. Conseca 행: 강제 기본 요소 "신뢰 컨텍스트로부터 JIT 정책", 게이트 "결정적", 무결성 "예", 기밀성 "부분", 암묵 흐름 "적대적 계획 위험", **비용 "미보고"**, **레트로핏 "불가(플래너 분리 필요)"**.

> "Progent constructs adaptive attacks on its own policy LLM, and FORGE and Conseca name adversarial-planning risks, yet the systematic, independent, multi-attack adaptive evaluation that the in-band defenses received has not been assembled for this class. Until that happens, the field is largely in the position it was in for in-band defenses just before they broke."

**기여.** 대역 외 방어가 대역 내 탐지기를 무너뜨린 것과 같은 **정적 벤치마크 방법론**으로 평가되고 있다고 경고. "LLM이 정책을 작성하면 검증 가능성이 약화된다"고 정책 생성기를 약점으로 명명. Progent에 대한 첫 적응형 평가(정책 업데이트 LLM이 허용목록을 넓히도록 유도)를 수행: ASR 25.8% → 4.2%(방어) → 2.6%(적응형, 증가 없음), 그러나 유용성 45.2% → 27.1%.

#### 4.4.3 Taxonomy, Evaluation and Exploitation of IPI-Centric LLM Agent Defense Frameworks (Ji et al.; HKUST 등, arXiv 2511.15203)

Conseca를 기술 패러다임 ⑥ "Policy Enforcing", 사후 추론 단계 개입, 결정적 설명 가능성으로 분류한다. Conseca는 비공개 소스여서 직접 평가하지 않고 같은 범주의 Progent를 평가했다.

**근본 원인 5 "보안 정책의 불충분한 커버리지"**가 Conseca류에 직접 해당한다:
> "in the Progent-LLM framework, LLM generated policies do not adequately consider tool parameters. Given the user query 'Can you please pay the bill...', the LLM for policy generation correctly designs a policy for the read_file tool with parameter constraints. However, for the send_money tool, it only applies tool-level policy and does not consider parameter constraints. This allows injected content from the bill file to control the recipient parameter of send_money." / "the manually designed policy set performs significantly better than the LLM-generated policy set, representing the foremost challenge of such frameworks."

**수치.** Progent 수동 정책 ASR 0.00% vs LLM 생성 정책 4.63%. 새 적응형 공격 Semantic-Masquerading은 ASR을 최대 약 4배, Cascading은 약 4.8배 증가. 수동 정책 오버헤드 3.95초 vs LLM 정책 16.35초.

#### 4.4.4 Systems Security Foundations for Agentic Computing (Christodorescu, Fernandes, Hooda, Jha, Rehberger 등; arXiv 2512.01295)

Conseca를 "사용자 프롬프트로부터 정책 추론"의 대표 사례로 인용하며, 정책 생성기를 **"확률적 TCB(Trusted Computing Base)"**로 프레이밍한다:
> "such TCBs fall short of providing strong security guarantees, as determined and patient attackers can always find a bypass ... agents may counterintuitively try to evade the security policy due to their propensity to reward hacking."

"동적·태스크별 보안 정책"을 에이전트 보안의 네 가지 근본 과제 중 하나로 명명하고, 정책 기반 시스템이 "도구에 적절한 의미 정의가 있다"고 가정하지만 컴퓨터/브라우저 사용 에이전트에는 성립하지 않음을 지적한다. 열린 문제로 "LLM의 추론 능력으로 사용자와 대화하며 자연어 태스크 명세의 빈틈을 명확히 하는 정책 어시스턴트"를 제안하는데, 이는 Conseca + Janus의 결합 방향이다.

#### 4.4.5 VIGIL: Runtime Enforcement of Behavioral Specifications in AI Agent Skills (Li, Chen, Wen, Zhang, Liu, Wang, Feng, Tian; UCSB·UCLA, arXiv 2606.26524)

> "Action-level monitors such as AgentSpec, Progent, Conseca, and PCAS gate individual calls, yet lack the memory to enforce rules that span earlier events, value flows, or the identity of artifacts produced steps ago." / "Vigil instead treats the observed trace as the policy context, so the enforceable specification can be refined online as the run unfolds."

**기제.** 도구 호출을 아티팩트 신원과 값 흐름을 보존하는 타입화된 이벤트로 추상화하고, 자연어 스킬 명세를 LLM으로 **1회 컴파일**(캐시 가능)해 유한 트레이스 시간 안전 속성으로 변환한다. 모든 강제 결정은 SMT 충족 가능성 질의이고, UNSAT 코어가 위반 호출의 국소적 증거를 제공한다.

**Conseca 대비 발전점.** 강제 세분화를 **행동별 정규식에서 궤적 수준 시간 속성**으로 이동(한계 (4) 해결). LLM 사용을 1회 컴파일에 한정하고 결정 시점은 결정적 SMT. SB+SI 벤치마크 F1 92.6, AgentDojo F1 94.2, 실제 스킬 실행 216건에서 34건 위반 확인(1건 NVIDIA 인정).

#### 4.4.6 ARGUS: Defending LLM Agents Against Context-Aware Prompt Injection (Weng, Feng, Zhang, Xie, Yu, Liu; Nanjing·SMU, arXiv 2605.03378)

> "Existing defenses use isolation, information-flow control, and detection or policy checking [Conseca 포함]. These methods constrain channels, policies, or suspicious traces, but they usually stop before the key question for context-dependent tasks: whether the concrete action follows from the user's task and benign runtime evidence."

**기제.** 프롬프트·런타임 컨텍스트 스팬·행동에 대한 영향-출처 그래프(Influence-Provenance Graph)를 유지하고, 스팬을 정상/이상으로 라벨링한 뒤 각 상태 변경 행동의 인자를 뒷받침 증거에 접지시켜, 정상 증거가 행동을 함의하고 태스크 불변식이 성립할 때만 실행을 허용한다. 컨텍스트 의존 태스크 벤치마크 AgentLure(320 샘플, 8개 공격 벡터) 제안.

**Conseca 대비 발전점.** 정규식 JIT 정책의 어려운 사례를 정면으로 다룬다: 파라미터의 올바른 값(예: 수신자)이 정당하게 비신뢰 데이터에서 와야 할 때, 인자 패턴은 주입 값과 정당 값을 구별할 수 없지만 **출처 기반 함의**는 가능하다. Gemini CLI 이슈 #25829가 지적한 "의미적으로 정렬된 인젠션" 문제에 대한 학술적 답이며 ROPE와 같은 방향이다. ASR 28.8% → 3.8%, 클린 유용성 87.5%, 적응형 화이트박스 공격 ASR 5.9%.

#### 4.4.7 기타: 확률적 검증, Agent libOS, 서베이

- **Efficient and Sound Probabilistic Verification for AI Agents** (Solko-Breslin, Mudrakarta, Christodorescu, Jha, Dvijotham; Google·UW-Madison, arXiv 2606.20510): Conseca류 결정적 참조 모니터는 "노이즈가 있는 확률적 술어(예: PII 탐지기 출력)와 호환되지 않으며 임의 임계값을 적용해야 한다"고 비판. 분포 강건 최적화 기반의 SDP 완화로 최악 위반 확률의 건전한 상한을 다항 시간에 계산. 세 벤치마크에서 재현율 1.0, 정밀도 0.98~1.0
- **Agent libOS** (Zhang; Tsinghua, arXiv 2606.03895): "Conseca associates contextual policies with task purpose"로 인용. 모델이 보는 도구 스키마 위의 정책은 권한의 앵커가 아니며, 가시적 행동 표면 확장(스킬, JIT 도구)이 자원 권한을 확장해서는 안 된다는 입장. 호스트가 설정한 능력·IFC를 OS 기본 요소 수준에서 강제. 119건 무단 효과 0, 오거부 0
- **The Attack and Defense Landscape of Agentic AI** (Kim, Liu, Wang, Qiu, Li, Guo, Song; UC Berkeley 등, arXiv 2603.11088): 128편 서베이. Conseca(와 Progent)를 **"컨텍스트 보안(contextual security)"이라는 보안 목표를 정의한 연구**로 인정하고 CIA와 나란히 일곱 번째 위험 범주로 격상. 방어 분류에서는 런타임 보호 → 출력 가드레일 → "하이브리드(구조화 정책 + 모델)"
- **SoK: Trust-Authorization Mismatch** (Shi et al.; Beihang, arXiv 2512.06914): v1 제목("Context is key for agent security")으로 인용하되 "오래된 데이터 기반 추론" 논점에 사용해 다소 빗나간 인용. 논지 자체(Belief-Intention-Permission 프레임워크, 신념 상태 불확실성으로 권한을 연속 조절하는 Belief-Aware Access Control)는 Conseca의 "인가는 동적이어야 한다"를 한 단계 더 밀어붙인다

---

## 5. 발전 축별 종합 비교

### 5.1 Conseca 설계 요소별 계승·변형

| 설계 요소 | Conseca | 계승 | 변형·대체 |
|---|---|---|---|
| 정책 생성 시점 | 실행 전 1회 | Prismata, ROPE, ControlValve, Plan-Then-Execute, Dynamic Capability Scoping | **실행 중 갱신**: Progent(SMT 단조 축소), VIGIL(트레이스가 정책 컨텍스트) / **배포 전 고정**: CSAgent, Autoformalization, AgentFlow, SEAgent |
| 정책 생성 주체 | LLM | Progent, Prismata, ROPE(라우터), ControlValve, Policy-as-Prompt, Autoformalization | **LLM 없음**: MiniScope(ILP), Dynamic Capability Scoping(분류기), GAAP(사용자), Overlaying Governance(스키마) |
| 정책 입력 | 사용자 요청 + 신뢰 컨텍스트 | ROPE, Prismata, ControlValve, Progent(초기) | **조직 문서**: Policy-as-Prompt, Autoformalization / **사용자 이력**: ARIEL, PSG-Agent / **런타임 트레이스**: VIGIL, ARGUS |
| 정책 표현 | 도구 API + 인자 정규식 | Progent(기호 규칙) | **출처 마커**: ROPE / **Biba 라벨**: Prismata / **CFG**: ControlValve / **Cedar**: Autoformalization / **IFC 격자+경로**: AgentFlow, AgentArmor / **시간 논리**: VIGIL / **OAuth 스코프**: MiniScope |
| 강제 방식 | 결정적 `is_allowed` | Progent, ROPE, AgentFlow, SEAgent, AC4A, MiniScope, GAAP | **LLM 판정으로 후퇴**: Policy-as-Prompt, ControlValve(간선 규칙), Gemini CLI 구현 / **SMT**: VIGIL / **확률적 상한**: 2606.20510 |
| 정책 단위 | 개별 행동 | 대부분 | **궤적·경로**: VIGIL, AgentFlow, ControlValve, PSG-Agent, ACP(상태 기반) |
| 사람의 역할 | 근거의 사후 검증 | — | **확장 승인**: Progent / **참여자**: Janus / **초안 편집자**: Reframing AHI / **(데이터,수신자) 결정자**: GAAP / **정책 트리 검토**: Policy-as-Prompt |
| 위협 모델 | 컨텍스트 일부 조작 | 대부분 | **혼동된 대리인·멀티에이전트**: ControlValve, SEAgent / **적대적 계획**: AIOracles / **CI 파라미터 조작**: Abdelnabi & Bagdasarian / **비신뢰 모델·프롬프트**: GAAP |

### 5.2 Conseca류 접근에 대한 반복 비판과 대응 논문

| # | 비판 | 제기 논문 | 대응(해결 시도) 논문 |
|---|---|---|---|
| 1 | LLM 정책 생성기가 검증되지 않은 확률적 TCB("LM으로 LM을 보호하는 역설") | Progent, MiniScope, AIOracles, Systems Security Foundations, Adaptive Evaluation | Progent(SMT 확장 검사), ROPE(감사된 기본값 하한), MiniScope(ILP), Autoformalization(비평가 루프), VeriGuard(형식 검증, 단 Conseca 미인용) |
| 2 | 생성 정책의 인자 제약 누락(커버리지 부족) | IPI 방어 SoK(RC5), MiniScope(최적성 70~83%) | ROPE(출처 마커), Progent(수동 정책 합성) |
| 3 | 정규식은 주입 값과 정당 값을 구별 불가(의미적 정렬 인젠션) | ROPE, ARGUS, Gemini CLI 이슈 #25829 | ROPE(출처), ARGUS(인과 출처 함의), Plan-Then-Execute(데이터를 값으로만 허용) |
| 4 | 행동 단위 검사가 궤적·제어흐름 공격(적대적 계획, 혼동된 대리인)을 놓침 | AIOracles, ControlValve, VIGIL, PSG-Agent | ControlValve(CFG), VIGIL(시간 속성), AgentFlow(경로 규칙), SEAgent(흐름 그래프) |
| 5 | 신뢰 컨텍스트만 보면 정보 부족으로 과도 거부·위장 유출 미탐지 | GAAP(실증: AgentDojo 유용성 45.3%) | GAAP(IFC), Progent(런타임 갱신), Janus(사용자 질의) |
| 6 | 컨텍스트 추론 기반 정책의 이론적 상한(고정 정책은 조작된 컨텍스트를 모두 막을 수 없음) | Abdelnabi & Bagdasarian | ROPE·Prismata(추론 대신 구조적 검증), Firewalls(닫힌 프로토콜) |
| 7 | 정적 벤치마크 평가, 비용 미보고, 레트로핏 불가, 상용 배포 0건 | Adaptive Evaluation, Reframing AHI, How Agents Ask for Permission | Gemini CLI 구현(배포), ROPE·ARGUS(적응형 공격 평가) |

---

## 6. Conseca가 남긴 미해결 과제와 후속 연구가 제시한 답

Conseca 저자들이 1.5절에서 명시한 한계·향후 과제와 후속 연구를 대응시키면 다음과 같다.

| Conseca의 열린 질문 | 후속 연구의 답 | 남은 공백 |
|---|---|---|
| **사용자 상호작용**(승인, undo-log) | Progent의 확장 승인, Janus의 여섯 어시스턴트와 설계 공간, GAAP의 (데이터,수신자) 질문 영속화, Reframing AHI의 "초안 편집" 제안 | 실제 사용자 연구 부재(Janus는 합성 응답자). 권한 피로와 보안의 트레이드오프 정량화는 초기 단계 |
| **근거의 형식 검증** | Autoformalization(Cedar 구문·의미 비평가), VIGIL(SMT), Progent(SMT 단조성), AIOracles(형식 어휘) | 생성된 정책이 사용자 *의도*와 일치하는지의 검증은 여전히 LLM 판정 또는 사람에 의존 |
| **궤적 수준 제약** | VIGIL(시간 속성), ControlValve(CFG), AgentFlow(경로 규칙), PSG-Agent(누적 위험), ACP(상태 기반 위험) | 궤적 정책의 *자동 생성*은 ControlValve만 시도. 대부분 수작성 |
| **LLM 없는 컨텍스트 정책** | MiniScope(ILP over OAuth 스코프), Dynamic Capability Scoping(분류기), GAAP(사용자 지정 + IFC), Overlaying Governance(스키마 재작성) | 세분화 손실(스코프·15개 권한 수준). 인자 수준 제약과 LLM 없는 생성의 결합은 미해결 |
| **효율성**(경량 모델) | ROPE의 "약한 라우터도 감사된 기본값으로 한정", Gemini CLI의 Flash 모델 사용, VIGIL의 1회 컴파일 캐싱 | Adaptive Evaluation이 지적한 대로 Conseca 자체 비용은 미보고 |
| **하이브리드**(수동 정책·사용자 확인 결합) | Progent(조직 정책 합성), CSAgent(개발 시 정책 + 런타임 의도), Gemini CLI(`ask_user` + 기존 TOML 정책 엔진 위 계층) | 정책 충돌 해소 규칙과 우선순위는 시스템별로 상이 |
| **실제 워크로드 평가** | GAAP(AgentDojo에서 Conseca 재구현), ROPE·ARGUS(적응형 공격), AgentLure·AgentDyn 등 컨텍스트 의존 벤치마크 | Adaptive Evaluation의 경고대로 독립적·다중 공격 적응형 평가는 이 부류 전체에 부족 |

**전반적 흐름.** 2025년 상반기 Conseca가 제기한 "정책은 목적마다 달라야 한다"는 명제는 2026년 서베이에서 "컨텍스트 보안"이라는 독립 보안 목표로 격상되었다. 그러나 그 명제를 *어떻게* 실현하느냐에 대해서는 후속 연구가 Conseca의 구체적 설계(LLM이 정규식 정책을 생성)에서 **세 방향으로 이탈**했다.

1. **생성기를 검증 가능하게**: SMT(Progent), 형식 언어(Cedar), 감사된 기본값(ROPE), 최적화(MiniScope)
2. **정책 대상을 구문에서 구조로**: 값의 출처(ROPE, ARGUS), DOM 무결성(Prismata), 정보흐름(AgentFlow, AgentArmor, GAAP), 제어흐름(ControlValve, Plan-Then-Execute)
3. **사람을 검증자에서 참여자로**: Janus, GAAP, Reframing AHI

동시에 이론 측(Abdelnabi & Bagdasarian, AIOracles)은 "LLM이 컨텍스트를 *추론*해 정책을 만드는" 접근 자체에 상한이 있음을 보였고, 이는 방향 2(추론 대신 구조적 *검증*)를 정당화한다.

---

## 7. 결론

- Conseca는 58편 이상에 인용되었고, 그중 약 35편이 아이디어를 실질적으로 발전·검증·비판했다. **Progent, ROPE, MiniScope, GAAP, AIOracles, AC4A**가 Conseca를 가장 깊이 다루며(전용 절, 직접 비교 또는 베이스라인 구현), Prismata·ControlValve·Dynamic Capability Scoping·Policy-as-Prompt가 설계 동기로 명시적으로 계승한다.
- Conseca의 두 가지 핵심 보장 중 **"정책 생성의 비신뢰 데이터 격리"**는 거의 모든 후속 연구(그리고 Gemini CLI 구현)가 유지했지만, **"결정적 강제"**는 일부(Policy-as-Prompt, ControlValve 간선 규칙, Gemini CLI)에서 LLM 판정으로 후퇴했다. 이 후퇴는 Reframing AHI 서베이가 Conseca를 "LLM-as-checker"로 잘못 분류한 것과 맞물려, 실제 구현들이 논문의 신뢰 경계를 약화시키는 경향을 시사한다.
- Conseca에 대한 가장 강력한 실증 비판은 공저자 Tsai가 참여한 **GAAP**에서 나왔다(AgentDojo 유용성 45.3%, 위장 유출 미탐지). 가장 강력한 이론 비판은 공저자 Bagdasarian의 **불가능성 결과**와 **AIOracles의 적대적 계획·"LM-to-secure-LM" 역설**이다. 즉 Conseca 저자들 스스로가 원 설계의 한계를 가장 적극적으로 밀어붙이고 있다.
- 실무적 시사점: Conseca류 JIT 정책을 배포하려면 (a) 생성 정책 아래에 감사된 기본값 또는 조직 정책을 하한으로 두고(ROPE, Progent), (b) 인자 제약을 정규식이 아닌 출처 기반으로 표현하고(ROPE, ARGUS), (c) 강제는 LLM이 아닌 결정적 검사기에 맡기고 실패 시 fail-closed로 하며(Gemini CLI의 fail-open 13경로는 반례), (d) 궤적 수준 제약(VIGIL, ControlValve)과 사용자 참여 설계(Janus)를 결합해야 한다는 것이 후속 연구의 합의에 가깝다.

---

## 8. 참고문헌

### 원논문
- Tsai, L., Bagdasarian, E. *Contextual Agent Security: A Policy for Every Purpose.* HotOS '25. arXiv:2501.17070. https://arxiv.org/abs/2501.17070 (v1 제목: *Context is Key for Agent Security*)
- Google Gemini CLI, `packages/core/src/safety/conseca/` (PR #13193 "feat(security): Introduce Conseca framework"); Issue #25829 "Strengthen Conseca with Causal Attribution". https://github.com/google-gemini/gemini-cli

### 4.1 자동 정책 생성 계열
- Shi, T. et al. *Progent: Securing AI Agents with Privilege Control.* arXiv:2504.11703
- Zhu, J. et al. *MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents.* arXiv:2512.11147
- Ma, X. et al. *ROPE: Routed Origin Policy Enforcement against Indirect Prompt Injection.* arXiv:2608.27496
- Villa, C. et al. *Prismata: Confining Cross-Site Prompt Injection in Web Agents.* arXiv:2607.08147
- Jha, R. et al. *Breaking and Fixing Defenses Against Control-Flow Hijacking in Multi-Agent Systems.* arXiv:2510.17276
- Noyan, H. B. *Dynamic Capability Scoping for Enterprise AI Agents.* AIWILD@ICML 2026. arXiv:2607.22445
- Mondl, A. et al. *Autoformalization of Agent Instructions into Policy-as-Code.* AIWILD@ICML 2026. arXiv:2606.26649
- Kholkar, G., Ahuja, R. *Policy-as-Prompt: Turning AI Governance Rules into Guardrails for AI Agents.* Regulatable ML@NeurIPS 2025. arXiv:2509.23994; 동 저자 *The AI Agent Code of Conduct: Automated Guardrail Policy-as-Prompt Synthesis* (2025)
- Gong, H. et al. *Secure and Efficient Access Control for Computer-Use Agents via Context Space (CSAgent).* arXiv:2509.22256

### 4.2 강제 계층 확장 계열
- Shivakumar, B. A. et al. *AgentFlow: A Flow-Centric Policy Language and Framework for Securing LLM Agent Systems.* arXiv:2608.22868
- Wang, P. et al. *AgentArmor: Enforcing Program Analysis on Agent Runtime Trace to Defend Against Prompt Injection.* arXiv:2508.01249
- Ji, Z. et al. *Taming Various Privilege Escalation in LLM-Based Agent Systems: A Mandatory Access Control Framework (SEAgent).* arXiv:2601.11893
- Sharma, R. K., Grossman, D. *AC4A: Access Control for Agents.* arXiv:2603.20933
- Piet, J. et al. *Web Agents Should Adopt the Plan-Then-Execute Paradigm.* arXiv:2605.14290
- Abdelnabi, S. et al. *Firewalls to Secure Dynamic LLM Agentic Networks.* TMLR. arXiv:2502.01822 (Conseca 인용은 v5에만 존재)
- Fernandez, M. *Agent Control Protocol: Admission Control for Agent Actions.* arXiv:2603.18829
- Zhang, Y. *Agent libOS: A Runtime Substrate for Capability-Controlled Self-Evolving LLM Agents.* arXiv:2606.03895

### 4.3 사용자 참여·개인화·Contextual Integrity 계열
- Stanley, R., Verma, A., Tsai, L., Kallas, K., Kumar, S. *An AI Agent Execution Environment to Safeguard User Data (GAAP).* arXiv:2604.19657
- Brigham, N. G., Bagdasarian, E., Kohno, T., Roesner, F. *Janus: a Playground for User-Involved Agentic Permission Management.* arXiv:2607.01510
- Abdelnabi, S., Bagdasarian, E. *AI Agents May Always Fall for Prompt Injections.* arXiv:2605.17634
- Michael, A. E., Roesner, F. *How Agents Ask for Permission: User Permissions for AI Agents, from Interfaces to Enforcement.* arXiv:2607.13718
- Wang, P., Li, Y., Tian, Y. *Reframing LLM Agent Security as an Agent-Human Interaction Problem.* arXiv:2605.24309
- Flemings, J. et al. *Personalizing Agent Privacy Decisions via Logical Entailment (ARIEL).* PoPETs. arXiv:2512.05065
- Wu, Y. et al. *PSG-Agent: Personality-Aware Safety Guardrail for LLM-based Agents.* arXiv:2509.23614
- Ibrahim, A., Li, Y. *Overlaying Governance: A Compositional Authorization Framework for Delegation and Scope in Agentic AI.* arXiv:2606.03518
- Shlomov, S. et al. *Governance by Construction for Generalist Agents.* ACM CAIS '26. arXiv:2605.20874

### 4.4 평가·비판·형식화 계열
- Villa, F., Durak, F. B., Kohno, T., Maharramli, T., Roesner, F. *Extending the Formalism and Theoretical Foundations of Cryptography to AI (AIOracles).* arXiv:2603.02590
- Narisetty, P. et al. *Adaptive Evaluation of Out-of-Band Defenses Against Prompt Injection in LLM Agents.* arXiv:2606.26479
- Ji, Z. et al. *Taxonomy, Evaluation and Exploitation of IPI-Centric LLM Agent Defense Frameworks.* arXiv:2511.15203
- Christodorescu, M. et al. *Systems Security Foundations for Agentic Computing.* arXiv:2512.01295
- Li, Y. et al. *VIGIL: Runtime Enforcement of Behavioral Specifications in AI Agent Skills.* arXiv:2606.26524
- Weng, S. et al. *ARGUS: Defending LLM Agents Against Context-Aware Prompt Injection.* arXiv:2605.03378
- Solko-Breslin, A. et al. *Efficient and Sound Probabilistic Verification for AI Agents.* arXiv:2606.20510
- Kim, J. et al. *The Attack and Defense Landscape of Agentic AI: A Comprehensive Survey.* arXiv:2603.11088
- Shi, G. et al. *SoK: Trust-Authorization Mismatch in LLM Agent Interactions.* arXiv:2512.06914

### 배경 인용(E 유형, 분석 제외)
- Zhang, K. et al. *LLM Agents Should Employ Security Principles.* arXiv:2505.24019
- Ji, Z. et al. *Cloak and Detonate: Scanner Evasion and Dynamic Detection of Agent Skill Malware.* arXiv:2607.02357
- Wu, J. et al. *MOSAIC: Knowledge-Guided CLI Command Composition Attack in LLM Coding Agents.* arXiv:2607.02857
- Kim, J. et al. *DualView: Preventing Indirect Prompt Injection in Personal AI Agents.* arXiv:2607.03821
- Choi, W. et al. *Agent Data Injection Attacks are Realistic Threats to AI Agents.* arXiv:2607.05120
- Lee, S. et al. *Site Isolation is Dead: How Site Isolation is Broken in Agentic Browsers and Extensions.* IEEE S&P 2026
- Yu, Z. et al. *Spider-Sense: Intrinsic Risk Sensing for Efficient Agent Defense.* arXiv:2602.05386
- Jeong, H. et al. *Network-Level Prompt and Trait Leakage in Local Research Agents.* arXiv:2508.20282
- Jeong, H., Pham, D., Houmansadr, A., Bagdasarian, E. *AI Snitches Get Glitches: Towards Evading Agentic Surveillance.* arXiv:2606.25836
- Adam, J. et al. *Towards Practically-Secure Tools for AI Agents.* EuroMLSys@EuroSys 2026
- Yu, X. et al. *SUDP: Secret-Use Delegation Protocol for Agentic Systems.* arXiv:2604.24920
- Li, N. et al. *Security Considerations for Artificial Intelligence Agents.* arXiv:2603.12230
- Laws, M. D. et al. *Attacks and Mitigations for Distributed Governance of Agentic AI under Byzantine Adversaries.* arXiv:2605.12364
- Geambasu, R. et al. *Engineering Robustness into Personal Agents with the AI Workflow Store.* arXiv:2605.10907
- Zhou, T. et al. *Language-Based Agent Control.* arXiv:2605.12863
- Summers, C., Wu, E. *Data Flow Control: Data Safety Policies for AI Agents.* arXiv:2606.05679
- Ge, K., Assis, A. *ClayBuddy: A Framework, Evaluation, & Mitigation of Coding Agent Failures.* arXiv:2606.19380
- Choong, T.-W. et al. *CapChain.* Applied Sciences 2026; Liu, Y. et al. *Topology Linearization for Multi-Agent Systems Security.* IEEE TNSE 2026; Theodorakopoulos, L. et al. *Auditable LLM Autonomy.* CMC 2026; Rubio-Medrano, C. E. et al. *Towards Agentic AI for Access Control in Cyber-infrastructures.* SACMAT 2026; *Security Architecture for Agentic AI in Enterprise Cloud Environments (ZT-AASF).* IJISRT 2026; Lamprou, E. et al. *Controlling Opaque-Component Effects with Semisolates and Try*

### 인용 후보로 검색되었으나 원문 확인 결과 Conseca를 인용하지 않은 논문
VeriGuard (2510.05156), Deontic Policies for Runtime Governance (2606.19464), CaMeL (2503.18813), SkillScope (2605.05868), SkillGuard (2606.03024), AgentBound (2510.21236), Towards Secure Agent Skills (2604.02837), Securing the MCP (2511.20920), Multi-Agent LLM Defense Pipeline (2509.14285), ceLLMate (2512.12594)
