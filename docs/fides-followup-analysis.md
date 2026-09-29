# FIDES 후속 연구 분석: 단점 개선 및 대체 기법 정리

- 작성일: 2026-09-29
- 대상: FIDES (Costa et al., *Securing AI Agents with Information-Flow Control*, arXiv:2505.23643, v1 2025-05-29 / v2 2025-09-03, Microsoft Research)
- 조사 범위: Semantic Scholar 기준 FIDES 인용 논문 124편(2026-09-25 기준) 중 IFC·플래너·권한/출처 추적·공격/평가·시스템 계열 약 60편과, FIDES와 직접 비교되는 동시대 대안(Progent, RTBAS, PFI, CaMeL 등)
- 문서 목적: FIDES의 구조적 한계를 정리하고, 각 한계를 (a) FIDES 위에 **추가 도입**해 개선할 수 있는 기법과 (b) FIDES를 **대체**할 수 있는 기법으로 나누어 정리한다.

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
