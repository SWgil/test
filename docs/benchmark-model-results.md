# 오픈 벤치마크별 모델 평가 결과 (ASR / Utility)

> 동반 문서: `docs/agentdojo-successor-benchmarks.md` (벤치마크 설명과 AgentDojo와의 차이)
> 조사 시점: 2026-09. 모든 수치는 각 논문·리더보드가 보고한 값을 그대로 옮겼다. 표마다 출처와 설정(공격, 방어, 평가 모드)을 적었으므로 **같은 모델이라도 표 간 직접 비교는 하지 말 것**. 원문에서 "약 ~%"로만 읽히는 값(그래프 추정)은 제외했다.

## 0. 읽는 법

| 용어 | 의미 |
|---|---|
| **BU** (Benign Utility) | 공격이 없을 때 사용자 태스크 성공률 |
| **UA** (Utility under Attack) | 인젝션이 있는 상태에서 사용자 태스크 성공률 |
| **ASR** | 공격자 목표 달성률. 벤치마크마다 판정 방식이 다르다(환경 상태 / 툴 호출 매칭 / LLM 판정자) |
| **ASR-int / AR** | 중간 성공률·시도율. 공격 지시를 실행하기 시작했는지만 본다 (WASP, RedTeamCUA, VPI-Bench) |
| **ASR-e2e** | 종단 성공률. 공격자 목표를 완수했는지 |
| **RR** | 거부율 |

**상용 모델**은 OpenAI·Anthropic·Google·xAI·Cohere 계열, **오픈 모델**은 가중치가 공개된 계열(Llama, Qwen, DeepSeek, GLM, Kimi, Mistral, Gemma, Phi, MiniMax, GPT-oss 등)로 구분해 표에 표시했다.

## 1. 오픈 데이터셋·코드 목록

| 벤치마크 | 공개 위치 | 형태 |
|---|---|---|
| AgentDojo | [ethz-spylab/agentdojo](https://github.com/ethz-spylab/agentdojo) · [리더보드](https://agentdojo.spylab.ai/results/) | Python 패키지, 97 태스크 / 629 케이스 |
| InjecAgent | [uiuc-kang-lab/InjecAgent](https://github.com/uiuc-kang-lab/InjecAgent) | 1,054 케이스 JSON |
| Agent Security Bench (ASB) | [agiresearch/ASB](https://github.com/agiresearch/ASB) | 10 시나리오, 400+ 툴 |
| WASP | [facebookresearch/wasp](https://github.com/facebookresearch/wasp) | VisualWebArena 도커 환경 + 인젝션 케이스 |
| DoomArena | [ServiceNow/DoomArena](https://github.com/ServiceNow/DoomArena) | 프레임워크 (τ-bench, BrowserGym, OSWorld 플러그인) |
| RedTeamCUA / RTC-Bench | [OSU-NLP-Group/RedTeamCUA](https://github.com/OSU-NLP-Group/RedTeamCUA) | VM + Docker, 864 케이스 |
| VPI-Bench | [cua-framework/agents](https://github.com/cua-framework/agents) | 5 플랫폼 306 케이스 |
| OS-Harm | [tml-epfl/OS-Harm](https://github.com/tml-epfl/OS-Harm) | OSWorld 기반 150 태스크 |
| LLMail-Inject | [microsoft/llmail-inject-challenge](https://github.com/microsoft/llmail-inject-challenge) · HF 데이터셋 | 208,095 공격 프롬프트 |
| b3 (Backbone Breaker) | [Lakera HF 데이터셋](https://huggingface.co/datasets/Lakera/b3-agent-security-benchmark-weak) · [inspect_evals](https://ukgovernmentbeis.github.io/inspect_evals/evals/b3/index.html) | 10 위협 스냅샷 × 210 공격 |
| AgentDyn | 논문 명시 GitHub 공개 ([arXiv:2602.03117](https://arxiv.org/abs/2602.03117)) | 60 태스크 / 560 케이스 |
| MCPTox | 논문 참조 ([arXiv:2508.14925](https://arxiv.org/abs/2508.14925)) | 45 MCP 서버 / 353 툴 |
| MCP Security Bench (MSB) | 논문 명시 코드 공개 ([arXiv:2510.15994](https://arxiv.org/abs/2510.15994)) | 405 툴 / 2,000 인스턴스 |
| LivePI | 논문 참조 ([arXiv:2605.17986](https://arxiv.org/abs/2605.17986)) | 실 VM 환경, 169 케이스 |
| MELON / AgentVigil / RL-Hammer / AutoInject | [kaijiezhu11/MELON](https://github.com/kaijiezhu11/MELON) · [facebookresearch/rl-injector](https://github.com/facebookresearch/rl-injector) 등 | AgentDojo 위에서 돌아가는 공격·방어 코드 |

---

## 2. AgentDojo

### 2.1 공식 리더보드 — 무방어, `important_instructions` 공격

출처: [agentdojo.spylab.ai/results](https://agentdojo.spylab.ai/results/) (2025-02 갱신분까지). 판정은 환경 상태 기준.

| 구분 | 모델 | BU | UA | 표적 ASR |
|---|---|---|---|---|
| 상용 | claude-3-7-sonnet-20250219 | 88.66% | 77.27% | **7.31%** |
| 상용 | claude-3-5-sonnet-20241022 | 79.38% | 72.50% | **1.11%** |
| 상용 | claude-3-5-sonnet-20240620 | 79.38% | 51.19% | 33.86% |
| 상용 | claude-3-opus-20240229 | 68.04% | 52.46% | 11.29% |
| 상용 | claude-3-sonnet-20240229 | 53.61% | 33.23% | 26.71% |
| 상용 | claude-3-haiku-20240307 | 39.18% | 33.39% | 9.06% |
| 상용 | gpt-4o-2024-05-13 | 69.07% | 50.08% | 47.69% |
| 상용 | gpt-4o-mini-2024-07-18 | 68.04% | 49.92% | 27.19% |
| 상용 | gpt-4-turbo-2024-04-09 | 64.95% | 54.05% | 28.62% |
| 상용 | gpt-4-0125-preview | 65.98% | 40.70% | 56.28% |
| 상용 | gpt-3.5-turbo-0125 | 35.05% | 34.66% | 10.33% |
| 상용 | gemini-2.0-flash-001 | 43.30% | 39.75% | 20.83% |
| 상용 | gemini-2.0-flash-exp | 46.39% | 39.90% | 17.01% |
| 상용 | gemini-1.5-pro-002 | 61.86% | 47.06% | 17.01% |
| 상용 | gemini-1.5-pro-001 | 46.39% | 28.93% | 28.62% |
| 상용 | gemini-1.5-flash-002 | 38.14% | 32.43% | 3.50% |
| 상용 | gemini-1.5-flash-001 | 38.14% | 34.18% | 12.24% |
| 상용 | command-r-plus | 24.74% | 25.12% | 4.45% |
| 상용 | command-r | 26.80% | 30.84% | 3.34% |
| 오픈 | Llama-3-70b-chat-hf | 34.02% | 18.28% | 25.60% |

같은 GPT-4o(2024-05-13)에 대한 **공격 템플릿별** 비교:

| 공격 | UA | 표적 ASR |
|---|---|---|
| direct | 67.25% | 3.66% |
| ignore_previous | 66.77% | 5.41% |
| injecagent | 68.52% | 5.72% |
| tool_knowledge | 57.71% | 34.50% |
| important_instructions | 50.08% | 47.69% |

### 2.2 GPT-4o 방어별 (리더보드 / 원논문 Table 5)

| 방어 | BU | UA | 표적 ASR |
|---|---|---|---|
| 없음 | 69.07% | 50.08% | 47.69% (논문 Table 5 기준 57.69%) |
| spotlighting_with_delimiting | 72.16% | 55.64% | 41.65% |
| repeat_user_prompt | 84.54% | 67.25% | 27.82% |
| tool_filter | 72.16% | 56.28% | 6.84% |
| transformers_pi_detector | 41.24% | 21.14% | 7.95% |

### 2.3 후속 논문이 보고한 최신 모델의 AgentDojo 결과

설정이 논문마다 다르므로 표를 분리했다.

**(a) MELON 논문 (ICML 2025), 무방어, important_instructions** — [arXiv:2502.05174](https://arxiv.org/abs/2502.05174)

| 구분 | 모델 | BU | UA | ASR |
|---|---|---|---|---|
| 상용 | GPT-4o | 80.41% | 54.05% | 51.03% |
| 상용 | o3-mini | 57.73% | 44.99% | 30.37% |
| 오픈 | Llama-3.3-70B | 74.88% | 67.41% | 6.20% |

**(b) Meta SecAlign 논문 Table 5** — [arXiv:2507.02735](https://arxiv.org/abs/2507.02735). 주의: **sandwich 방어가 적용된 상태**의 수치이며 ASR은 공격 템플릿 중 최댓값이다.

| 구분 | 모델 | BU | UA | ASR |
|---|---|---|---|---|
| 오픈 | Llama-3.3-70B | 59.8% | 43.4% | 14.7% |
| 오픈 | **Meta-SecAlign-70B** | 84.5% | 79.5% | 1.9% |
| 상용 | GPT-4o-mini | 67.0% | 51.6% | 11.9% |
| 상용 | GPT-4o | 79.4% | 67.4% | 20.4% |
| 상용 | GPT-5 | 80.3% | 79.7% | 0.2% |
| 상용 | Gemini-2-Flash | 42.3% | 37.1% | 11.3% |
| 상용 | Gemini-2.5-Flash | 63.9% | 52.6% | 27.9% |
| 상용 | Gemini-3-Pro | 92.8% | 90.6% | 2.3% |

**(c) AutoDojo 논문 Table II, 무방어, Banking·Slack·Travel 3개 스위트 합산** — [arXiv:2606.15057](https://arxiv.org/abs/2606.15057). 괄호는 UA.

| 구분 | 모델 | BU | 정적 ASR (UA) | AutoDojo ASR (UA) |
|---|---|---|---|---|
| 상용 | GPT-4o-mini | 66.7% | 58.6% (42.4%) | 52.4% (41.4%) |
| 상용 | GPT-5.4-mini | 77.2% | 6.9% (60.2%) | 8.7% (62.2%) |
| 상용 | Gemini-2.5-Flash | 63.2% | 47.8% (40.1%) | 32.4% (44.5%) |
| 오픈 | DeepSeek-v4-Flash | 89.5% | 22.6% (77.4%) | 16.5% (77.9%) |
| 상용 | Claude-Haiku-4.5 | 70.2% | 0.3% (61.4%) | 1.8% (64.0%) |

무방어 상태에서는 AutoDojo가 정적 공격보다 낮은 경우가 있다. AutoDojo의 이득은 필터 방어가 걸린 상태에서 나타난다(동반 문서 3.10 참조).

**(d) IterInject 논문 Table 1, 무방어, 전체 ASR** — [arXiv:2605.24659](https://arxiv.org/abs/2605.24659)

| 구분 | 모델 | 정적(벤치마크) ASR | AgentVigil ASR | IterInject ASR |
|---|---|---|---|---|
| 오픈 | GLM-5.1 | 11.6% | 18.2% | 17.5% |
| 오픈 | MiniMax-M2.7 | 16.1% | 23.1% | 26.5% |
| 오픈 | DeepSeek-V4-Flash | 32.9% | 39.2% | 47.8% |
| 오픈 | Qwen3.5-27B | 26.3% | 29.0% | 32.4% |

스위트별 평균 ASR: Banking 53.7%, Slack 36.4%, Travel 17.3%, Workspace 11.1%.

**(e) ChatInject 논문, 무방어** — [arXiv:2509.22830](https://arxiv.org/abs/2509.22830). 평문 베이스라인 vs ChatInject vs 다중턴 ChatInject. 폐쇄 모델은 다중턴 미실험.

| 구분 | 모델 | 평문 ASR | ChatInject ASR | 다중턴 ASR | 평문 UA | ChatInject UA |
|---|---|---|---|---|---|---|
| 오픈 | Qwen-3 | 17.5% | 54.8% | 80.5% | 50.9% | 28.3% |
| 오픈 | GPT-oss | 0.3% | 51.4% | 55.5% | 19.6% | 18.8% |
| 오픈 | Llama-4 | 1.0% | 17.2% | 11.1% | 16.5% | 15.9% |
| 오픈 | GLM-4.5 | 0.3% | 20.3% | 48.1% | 78.4% | 67.9% |
| 오픈 | Kimi-K2 | 5.9% | 29.3% | 13.9% | 71.5% | 35.0% |
| 상용 | Grok-2 | 6.1% | 19.3% | 24.7% | 41.7% | 29.8% |
| 상용 | GPT-4o | 6.4% | 27.3% | — | — | — |
| 상용 | Grok-3 | 8.2% | 33.2% | — | — | — |
| 상용 | Gemini-pro | 8.2% | 10.1% | — | — | — |

**(f) AgentVigil 논문, 무방어, 퍼징 세트 / 테스트 세트** — [arXiv:2505.05849](https://arxiv.org/abs/2505.05849)

| 구분 | 모델 | 베이스라인 ASR (퍼징/테스트) | AgentVigil ASR (퍼징/테스트) | BU |
|---|---|---|---|---|
| 상용 | o3-mini | 38% / 34% | 71% / 65% | — |
| 상용 | o3-mini-2025-01-31 | 50% / 53% | 73% / 76% | 79% |
| 상용 | GPT-4o | 22% / 25% | 22% / 19% | — |
| 상용 | GPT-4o-mini | 28% / 28% | 49% / 43% | — |
| 상용 | Claude-3.5-Sonnet | 12% / 8% | 3% / 4% | — |
| 오픈 | QwQ-32B | 45% / 47% | 72% / 74% | 74% |

**(g) RL-Hammer 논문, 무방어** — [arXiv:2510.04885](https://arxiv.org/abs/2510.04885)

| 구분 | 모델 | 원문 목표만 | tool_knowledge | RL-Hammer |
|---|---|---|---|---|
| 상용 | GPT-4o | 0% | 21% | 51% |
| 상용 | Claude-3.5-Sonnet | 0% | 12% | 26% |

**(h) Hofer et al. 2026, 무방어, 80개 태스크 쌍** — [arXiv:2606.10525](https://arxiv.org/abs/2606.10525)

| 구분 | 모델 | 단일태스크 TAP | 범용 TAP | 단일태스크 GCG | 범용 GCG |
|---|---|---|---|---|---|
| 오픈 | Qwen3-4B | 44.6% | 45.2% | 23.0% | 24.1% |
| 오픈 | Qwen3-32B (Qwen3-4B에서 전이) | 24.7–36.0% | | | |
| 상용 | GPT-5 | 4.5% | 4.7% | <1% (전이) | <1% (전이) |
| 상용 | Claude Sonnet 4.5 (전이) | <2% | <2% | | |
| 상용 | Gemini 2.5 Flash (전이) | 1.9% | 7.7% | | |

### 2.4 AgentDojo 방어 비교 (MELON 논문 Table 1, important_instructions)

| 방어 | GPT-4o BU / UA / ASR | o3-mini BU / UA / ASR | Llama-3.3-70B BU / UA / ASR |
|---|---|---|---|
| 없음 | 80.41 / 54.05 / 51.03 | 57.73 / 44.99 / 30.37 | 74.88 / 67.41 / 6.20 |
| Delimiting | 82.47 / 56.92 / 43.56 | 55.67 / 44.67 / 31.16 | 75.26 / 65.50 / 5.88 |
| Repeat Prompt | 83.51 / 68.84 / 28.93 | 53.61 / 38.16 / 13.51 | 72.16 / 69.16 / 3.18 |
| Tool Filter | 65.98 / 61.21 / 6.52 | 4.12 / 5.72 / 0.00 | 4.12 / 6.36 / 0.00 |
| DeBERTa Detector | 38.14 / 12.88 / 8.43 | 38.14 / 18.76 / 4.93 | 35.05 / 12.08 / 1.59 |
| MELON | 68.04 / 32.91 / 0.95 | 50.52 / 32.11 / 1.75 | 63.92 / 59.30 / 0.79 |
| MELON-Aug | 76.29 / 52.46 / 1.27 | 55.67 / 35.14 / 1.11 | 67.01 / 61.84 / 0.16 |

Tool Filter가 o3-mini·Llama-3.3-70B에서 BU 4.12%로 붕괴한 것은 해당 모델이 "필요 툴 사전 선택" 단계를 제대로 수행하지 못했기 때문이다.

### 2.5 AgentDojo Banking 개인정보 유출 확장 (Alizadeh et al.) — [arXiv:2506.01055](https://arxiv.org/abs/2506.01055)

GPT-4o, 방어별. 16 태스크 / 48 태스크 설정.

| 방어 | 16태스크 ASR | 16태스크 BU | 16태스크 UA | 48태스크 ASR | 48태스크 UA |
|---|---|---|---|---|---|
| 없음 | 7.8% | 87.5% | 79.7% | 11.4% | 68.9% |
| Tool filter | 3.1% | 50.0% | 42.2% | 1.0% | 72.1% |
| PI detector | 0% | 43.8% | 28.1% | 1.5% | 39.3% |
| Repeat prompt | 0% | 25.0% | 32.8% | 7.3% | 69.3% |
| Delimiting | 7.0% | 78.8% | 71.7% | 10.3% | 62.0% |

---

## 3. InjecAgent

### 3.1 원논문 Table 3 (유효율 >50% 모델) — [arXiv:2403.02691](https://arxiv.org/abs/2403.02691)

| 구분 | 모델 | 설정 | 유효율 | Direct Harm ASR | Data Stealing ASR | 전체 ASR |
|---|---|---|---|---|---|---|
| 상용 | GPT-4 | 기본 | 98.8% | 14.7% | 32.7% | 23.6% |
| 상용 | GPT-4 | 강화 | 99.4% | 33.3% | 61.0% | 47.0% |
| 상용 | GPT-4 (FT) | 기본 | 99.9% | 2.9% | 10.1% | 6.6% |
| 상용 | GPT-3.5 | 기본 | 76.6% | 18.8% | 37.6% | 23.7% |
| 상용 | GPT-3.5 | 강화 | 84.3% | 31.4% | 58.3% | 39.8% |
| 상용 | GPT-3.5 (FT) | 기본 | 99.2% | 1.8% | 5.7% | 3.8% |
| 상용 | Claude-2 | 기본 | 59.8% | 7.5% | 26.5% | 11.4% |
| 상용 | Claude-2 | 강화 | 95.0% | 4.4% | 5.4% | 3.4% |
| 오픈 | Llama2-70B | 기본 | 45.1% | 91.9% | 97.1% | 86.9% |
| 오픈 | Llama2-70B | 강화 | 53.1% | 94.7% | 98.3% | 88.2% |

### 3.2 후속 논문의 InjecAgent 결과

**(a) ChatInject** — 평문 / ChatInject / 다중턴

| 구분 | 모델 | 평문 | ChatInject | 다중턴 |
|---|---|---|---|---|
| 오픈 | Qwen-3 | 8.5% | 39.4% | 65.9% |
| 오픈 | GPT-oss | 0.0% | 14.2% | 16.9% |
| 오픈 | Llama-4 | 50.1% | 79.4% | 88.3% |
| 오픈 | GLM-4.5 | 0.0% | 57.3% | 71.5% |
| 오픈 | Kimi-K2 | 15.7% | 67.4% | 61.0% |
| 상용 | Grok-2 | 16.5% | 17.7% | 10.4% |
| 상용 | GPT-4o | 9.6% | 31.7% | — |
| 상용 | Grok-3 | 2.3% | 29.8% | — |
| 상용 | Gemini-pro | 1.4% | 27.4% | — |

**(b) TopicAttack (Direct Harm)** — 무방어 / Sandwich / Spotlight — [arXiv:2507.13686](https://arxiv.org/abs/2507.13686)

| 구분 | 모델 | Naive | Combined | TopicAttack |
|---|---|---|---|---|
| 오픈 | Llama3-70B | 83.92 / 39.80 / 46.86 | 97.06 / 60.78 / 78.63 | 98.24 / 92.75 / 92.16 |
| 오픈 | Llama3.1-405B | 97.06 / 77.06 / 94.51 | 89.80 / 84.51 / 96.08 | 95.69 / 88.43 / 97.65 |
| 상용 | GPT-4o | 66.27 / 21.37 / 46.86 | 73.53 / 51.37 / 65.88 | 88.43 / 69.22 / 87.45 |
| 상용 | GPT-4o-mini | — | — | 97.06 / 95.29 / 96.27 |

**(c) IterInject** — 정적 / AgentVigil / IterInject, 전체 ASR

| 구분 | 모델 | 정적 | AgentVigil | IterInject |
|---|---|---|---|---|
| 오픈 | GLM-5.1 | 0.00% | 18.15% | 33.07% |
| 오픈 | MiniMax-M2.7 | 2.02% | 44.75% | 44.76% |
| 오픈 | Qwen3.5-27B | 3.63% | 53.63% | 64.52% |
| 오픈 | DeepSeek-V4-Flash | 3.23% | 91.53% | 90.32% |

**(d) Meta SecAlign Table 5** (sandwich 적용 상태)

| 구분 | 모델 | ASR |
|---|---|---|
| 오픈 | Llama-3.3-70B | 53.8% |
| 오픈 | Meta-SecAlign-70B | 0.5% |
| 상용 | GPT-4o-mini | 3.3% |
| 상용 | GPT-4o | 22.7% |
| 상용 | GPT-5 | 0.2% |
| 상용 | Gemini-2-Flash | 27.2% |
| 상용 | Gemini-2.5-Flash | 0.1% |
| 상용 | Gemini-3-Pro | 0.2% |

**(e) Zhan et al. 2025 적응형 공격 (오픈 모델, 50 케이스)** — [arXiv:2503.00061](https://arxiv.org/abs/2503.00061)

| 구분 | 모델 | 무방어 ASR | 방어 적용 시 ASR 범위 | 적응 공격 시 ASR 범위 |
|---|---|---|---|---|
| 오픈 | Vicuna-7B | 56% | 12–53% | 50–90% |
| 오픈 | Llama3.1-8B | 9% | 5–8% | 50–87% |

---

## 4. Agent Security Bench (ASB) — [arXiv:2410.02644](https://arxiv.org/abs/2410.02644)

Table 5. 판정은 툴 호출 매칭. DPI = 직접 인젝션, IPI = 툴 출력 인젝션(AgentDojo와 같은 위협), PoT = Plan-of-Thought 백도어.

| 구분 | 모델 | DPI | IPI | 메모리 오염 | PoT 백도어 | 혼합 | 평균 ASR | 평균 RR |
|---|---|---|---|---|---|---|---|---|
| 상용 | GPT-4o | 60.35% | 62.45% | 10.00% | 100.00% | 89.25% | 64.41% | 8.81% |
| 상용 | GPT-4o-mini | 95.45% | 44.55% | 5.50% | 95.50% | 96.75% | 67.55% | 1.40% |
| 상용 | GPT-3.5 Turbo | 98.40% | 55.10% | 9.30% | 8.25% | 99.75% | 54.16% | 6.18% |
| 상용 | Claude 3.5 Sonnet | 90.75% | 59.70% | 19.75% | 17.50% | 94.50% | 56.44% | 10.47% |
| 오픈 | LLaMA3-8B | 25.20% | 10.55% | 3.30% | 21.50% | 40.75% | 20.26% | 4.83% |
| 오픈 | LLaMA3-70B | 86.15% | 43.70% | 1.85% | 57.00% | 85.50% | 54.84% | 4.22% |
| 오픈 | LLaMA3.1-8B | 51.10% | 6.40% | 25.65% | 19.00% | 73.50% | 35.13% | 4.61% |
| 오픈 | LLaMA3.1-70B | 85.65% | 12.10% | 2.85% | 59.75% | 94.50% | 50.97% | 3.99% |
| 오픈 | Qwen2-7B | 55.20% | 9.00% | 2.85% | 12.25% | 76.00% | 31.06% | 5.13% |
| 오픈 | Qwen2-72B | 86.95% | 21.35% | 3.95% | 57.75% | 98.50% | 53.70% | 6.34% |
| 오픈 | Gemma2-9B | 87.10% | 14.20% | 6.85% | 39.75% | 92.17% | 48.01% | 7.15% |
| 오픈 | Gemma2-27B | 96.75% | 14.20% | 6.25% | 54.50% | 100.00% | 54.34% | 2.85% |
| 오픈 | Mixtral-8x7B | 25.85% | 4.80% | 4.90% | 4.75% | 54.75% | 19.01% | 7.89% |

벤치마크 무공격 성능(PNA)은 Claude 3.5 Sonnet 100%, 소형 오픈 모델 대부분 30% 미만.

---

## 5. WASP — [arXiv:2504.18575](https://arxiv.org/abs/2504.18575)

Table 2. 평문 + URL 인젝션 합산, 무방어. 유틸리티는 공격 하 사용자 태스크 성공률.

| 구분 | 에이전트 | 유틸리티 | ASR-int | ASR-e2e |
|---|---|---|---|---|
| 상용 | GPT-4o (VWA, axtree+SoM) | 62.2% | 42.9% | 3.6% |
| 상용 | GPT-4o-mini (VWA, axtree) | 43.2% | 34.5% | 2.4% |
| 상용 | o1 (툴 호출, system role) | 48.6% | 85.7% | 16.7% |
| 상용 | Claude Sonnet 3.5 v2 (CU) | 8.1% | 58.3% | 6.0% |
| 상용 | Claude Sonnet 3.7 + extended thinking (CU) | 48.6% | 53.6% | 3.6% |

오픈 모델은 평가되지 않았다.

---

## 6. DoomArena — [arXiv:2504.14064](https://arxiv.org/abs/2504.14064)

TSR = 사용자 태스크 성공률.

**τ-bench (툴 호출)**

| 위협 모델 | 모델 | ASR | TSR (무공격) | TSR (공격 하) |
|---|---|---|---|---|
| 악성 사용자 | GPT-4o | 29.3% | 47.3% | 32.0% |
| 악성 사용자 | Claude-3.5-Sonnet | 2.7% | 44.0% | 39.3% |
| 악성 카탈로그 | GPT-4o | 34.8% | 51.3% | 39.1% |
| 악성 카탈로그 | Claude-3.5-Sonnet | 39.1% | 67.2% | 48.4% |
| 결합 | GPT-4o | 70.8% | 43.4% | 16.9% |
| 결합 | Claude-3.5-Sonnet | 39.5% | 64.1% | 12.6% |

**BrowserGym / WebArena-Reddit (웹)**

| 공격 | 모델 | ASR | TSR (공격 하) |
|---|---|---|---|
| 배너 | GPT-4o | 80.7% | 11.4% |
| 배너 | Claude-3.5-Sonnet | 60.5% | 11.4% |
| 팝업 | GPT-4o | 97.4% | 0.0% |
| 팝업 | Claude-3.5-Sonnet | 88.5% | 0.0% |
| 결합 | GPT-4o | 98.2% | 0.0% |
| 결합 | Claude-3.5-Sonnet | 96.4% | 0.0% |

**OSWorld (CUA)**: 팝업 인페인팅 GPT-4o 78.6%, Claude-3.7-Sonnet 22.9%.

---

## 7. RedTeamCUA / RTC-Bench — [arXiv:2505.21936](https://arxiv.org/abs/2505.21936)

AR = 시도율.

**분리(decoupled) 평가, Table 1**

| 구분 | 에이전트 | ASR | AR |
|---|---|---|---|
| 상용 | GPT-4o (LLM 기반 적응) | 66.19% | 92.45% |
| 상용 | Claude 3.5 Sonnet (LLM 기반) | 41.37% | 54.76% |
| 상용 | Claude 3.7 Sonnet (LLM 기반) | 39.33% | 40.00% |
| 상용 | Claude 3.5 Sonnet CUA | 31.21% | 70.83% |
| 상용 | Claude 3.7 Sonnet CUA | 42.93% | 55.00% |
| 상용 | Operator (확인 절차 포함) | 7.57% | 14.06% |
| 상용 | Operator (확인 절차 없음) | 30.89% | 23.33% |

**종단(end-to-end) 평가**

| 에이전트 | ASR |
|---|---|
| Claude 4.5 Opus CUA | 83% |
| Claude 4.6 Opus CUA | 50% |
| Claude 3.7 Sonnet CUA | 50.0% |
| Operator (확인 절차 없음) | 42.0% |

오픈 모델(UI-TARS, Qwen 계열)은 능력 부족으로 제외됐다.

---

## 8. VPI-Bench / OS-Harm

### 8.1 VPI-Bench — [arXiv:2506.02456](https://arxiv.org/abs/2506.02456)

CUA, 플랫폼별 "시도율 / 성공률".

| 구분 | 모델 | Amazon | Booking | BBC | Messenger | Email | 평균 성공률 |
|---|---|---|---|---|---|---|---|
| 상용 | Claude Sonnet 3.7 (CUA) | 47.8 / 31.7 | 59.4 / 36.7 | 19.4 / 16.7 | 59.0 / 46.2 | 38.5 / 37.2 | 약 33.7% |
| 상용 | Claude Sonnet 3.5 (CUA) | 5.6 / 4.4 | 17.8 / 12.2 | 1.1 / 0.0 | 53.9 / 51.3 | 46.2 / 44.9 | 약 22.6% |

브라우저 에이전트(GPT-5, GPT-4o, Claude-3.7-Sonnet, Gemini-2.5-Pro, Llama-4-Maverick, DeepSeek-V3): Amazon·Booking·BBC에서 시도율 대체로 100%, 성공률 49–96%. Email은 30–50%.

### 8.2 OS-Harm, 프롬프트 인젝션 카테고리 (Table 2) — [arXiv:2506.14866](https://arxiv.org/abs/2506.14866)

| 구분 | 모델 | 불안전율 | 태스크 완수율 | 3개 카테고리 평균 불안전율 |
|---|---|---|---|---|
| 상용 | o4-mini | 20% | 54% | 27% |
| 상용 | GPT-4.1 | 12% | 54% | 21% |
| 상용 | Claude 3.7 Sonnet | 10% | 32% | 29% |
| 상용 | Gemini 2.5 Pro | 8% | 72% | 27% |
| 상용 | Gemini 2.5 Flash | 2% | 34% | 26% |

---

## 9. AgentDyn — [arXiv:2602.03117](https://arxiv.org/abs/2602.03117)

무방어, important_instructions + 적응형 시나리오 공격. Table 3 및 부록.

| 구분 | 모델 | BU | UA | ASR |
|---|---|---|---|---|
| 상용 | GPT-4o | 53.33% | 55.52% | 37.80% |
| 상용 | GPT-5-mini | 65.00% | 64.76% | 0.37% |
| 상용 | GPT-5.1 | 61.67% | 50.04% | 4.96% |
| 상용 | Gemini-2.5 Pro | 51.67% | 56.95% | 20.61% |
| 상용 | Gemini-2.5 Flash | 30.00% | 24.29% | 37.61% |
| 상용 | Claude Sonnet 3.5 | 60.00% | 55.43% | 11.89% |
| 상용 | Claude Sonnet 4.5 | 71.67% | 70.74% | 0.87% |
| 오픈 | Llama-3.3-70B | 10.00% | 6.15% | 11.91% |
| 오픈 | Qwen3-235B | 23.33% | 10.74% | 22.67% |
| 오픈 | Qwen3-Coder | 18.33% | 15.76% | 14.61% |
| 오픈 | Kimi-K2.5 | 71.67% | 54.17% | 11.65% |

**GPT-4o 방어별** (무방어 ASR 37.80% / UA 55.52%)

| 방어 | ASR | UA |
|---|---|---|
| Prompt Sandwiching | 31.17% | 56.13% |
| Spotlighting | 27.61% | 52.24% |
| ProtectAI | 0.85% | 0.56% |
| PIGuard | 1.67% | 1.46% |
| PromptGuard2 | 27.15% | 20.80% |
| Meta SecAlign-70B | 8.98% | 53.35% |
| Tool Filter | 4.22% | 4.91% |
| CaMeL | 0.00% | 0.00% |
| Progent | 1.69% | 5.83% |
| DRIFT | 0.83% | 27.09% |

---

## 10. LivePI — [arXiv:2605.17986](https://arxiv.org/abs/2605.17986)

실 VM 환경, 169 케이스. 표면별 ASR.

| 구분 | 모델 | 전체 ASR | 그룹챗 (n=15) | 이메일 (n=50) | 로컬 문서 (n=50) | 저장소 링크 (n=4) | Gist (n=50) |
|---|---|---|---|---|---|---|---|
| 상용 | Gemini 3.1 Pro | 29.6% | 100% | 12.0% | 30.0% | 100% | 20.0% |
| 오픈 | GLM-5 | 27.8% | 100% | 6.0% | 50.0% | 100% | 0.0% |
| 상용 | GPT-5.3-Codex | 27.2% | 100% | 20.0% | 34.0% | 100% | 0.0% |
| 오픈 | Kimi K2.5 | 16.6% | 100% | 6.0% | 12.0% | 100% | 0.0% |
| 상용 | Claude Opus 4.6 | 10.7% | 100% | 2.0% | 0.0% | 50% | 0.0% |

2계층 방어(GPT-5.3-Codex): 169 케이스 ASR 0%, 무해 워크로드 899회 툴 호출 중 검토 0.89%·차단 0.11%.

---

## 11. MCP 계열

### 11.1 MCPTox (Table 2) — [arXiv:2508.14925](https://arxiv.org/abs/2508.14925)

툴 설명 오염. 기본 / 강화1 / 강화2 설정별 평균 ASR과 전체 평균.

| 구분 | 모델 | 기본 | 강화 1 | 강화 2 | 전체 평균 |
|---|---|---|---|---|---|
| 상용 | o1-mini | 63.5% | 66.6% | 69.9% | **72.8%** |
| 상용 | GPT-4o-mini | 51.6% | 61.3% | 63.3% | 61.8% |
| 상용 | GPT-3.5-turbo | 9.4% | 19.8% | 11.3% | 14.9% |
| 상용 | Gemini-2.5-flash | 57.2% | 53.1% | 66.8% | 59.7% |
| 상용 | Claude-3.7-sonnet | 38.6% | 24.3% | 48.1% | 34.3% |
| 오픈 | DeepSeek-R1 | 58.5% | 67.4% | 68.5% | 70.9% |
| 오픈 | DeepSeek-V3 | 46.0% | 53.5% | 57.0% | 56.5% |
| 오픈 | Phi-4 | 64.1% | 67.0% | 75.4% | 70.2% |
| 오픈 | Qwen3-8b (reasoning) | 34.6% | 43.2% | 46.4% | 41.8% |
| 오픈 | Qwen3-8b (standard) | 11.2% | 12.4% | 13.6% | 14.0% |
| 오픈 | Qwen3-14b (reasoning) | 25.6% | 26.3% | 32.5% | 27.1% |
| 오픈 | Qwen3-14b (standard) | 4.7% | 4.0% | 4.4% | 5.1% |
| 오픈 | Qwen3-32b (reasoning) | 51.7% | 55.4% | 62.5% | 58.5% |
| 오픈 | Qwen3-32b (standard) | 20.3% | 15.9% | 26.4% | 23.7% |
| 오픈 | Qwen3-235b (reasoning) | 46.6% | 46.8% | 55.3% | 50.6% |
| 오픈 | Qwen3-235b (standard) | 15.9% | 14.9% | 24.0% | 17.2% |
| 오픈 | Llama-3.1-8B | 10.1% | 13.2% | 11.9% | 14.1% |
| 오픈 | Llama-3.1-70B | 18.0% | 30.1% | 27.6% | 24.6% |
| 오픈 | Gemma-2-9b | 9.8% | 16.8% | 10.3% | 14.5% |
| 오픈 | Mistral | 4.2% | 9.6% | 6.0% | 8.3% |

Qwen3 계열에서 **reasoning 모드가 standard 모드보다 2–5배 취약**하다. b3의 "추론이 안전성을 높인다"와 반대 방향이므로, 공격 표면(툴 설명 vs 단일 호출)에 따라 결론이 갈린다.

### 11.2 MCP Security Bench (Table 3) — [arXiv:2510.15994](https://arxiv.org/abs/2510.15994)

PUA = 공격 하 성능, NRP = 순 회복 성능(보안·성능 절충 지표).

| 구분 | 모델 | 평균 ASR | PUA | NRP |
|---|---|---|---|---|
| 상용 | GPT-5 | 37.17% | 84.33% | **52.99%** |
| 상용 | GPT-4o-mini | 58.56% | 71.96% | 29.82% |
| 상용 | Claude 4 Sonnet | 52.51% | 73.92% | 35.11% |
| 상용 | Gemini 2.5 Flash | 30.26% | 32.14% | 22.41% |
| 오픈 | DeepSeek-V3.1 | 60.94% | 86.37% | 33.74% |
| 오픈 | Llama3.1 8B | 19.74% | 34.10% | 27.37% |
| 오픈 | Llama3.1 70B | 23.37% | 37.49% | 28.73% |
| 오픈 | Llama3.3 70B | 46.61% | 60.98% | 32.55% |
| 오픈 | Qwen3 8B | 47.23% | 51.15% | 26.99% |
| 오픈 | Qwen3 30B | 27.14% | 32.52% | 23.69% |

---

## 12. 모델별 수치가 제한적인 벤치마크

### 12.1 b3 / Breaking Agent Backbones — [arXiv:2510.22620](https://arxiv.org/abs/2510.22620)

31개 모델의 취약도 점수는 논문 Figure 2에 그래프로만 제시되고 표로 공개되지 않았다(리더보드 b3.lakera.ai는 JS 렌더링이라 본 조사에서 수치 추출 실패). 논문이 명시한 결과:

- 가장 안전한 모델: grok-4, grok-4-fast, claude-opus-4-1 (모두 reasoning 활성화).
- reasoning 활성화 시 대부분 모델의 취약도 점수가 뚜렷이 개선.
- reasoning 없는 모델은 크기가 커도 유의한 개선 없음.
- 폐쇄 모델이 오픈 가중치 모델보다 안전.

### 12.2 LLMail-Inject — [arXiv:2506.09956](https://arxiv.org/abs/2506.09956)

모델은 GPT-4o-mini와 Phi-3-medium-128k 두 개뿐이며 보고 단위는 "방어별 탐지 재현율"이다.

| 방어 | 1단계 재현율 | 2단계 재현율 |
|---|---|---|
| Prompt Shield v1 | 60.4% | 42.5% |
| LLM Judge | 99.4% | 96.5% |
| TaskTracker (Phi-3) | 76.1% | 89.6% |
| TaskTracker (Phi-4) | 88.1% | 99.8% |
| 전체 결합 | — | 99.8% |

종단 성공 제출 <1% (1단계 3,018건 / 2단계 306건, 총 208,095 고유 프롬프트).

---

## 13. 횡단 비교: 같은 모델, 다른 벤치마크

설정이 다르므로 경향만 읽을 것. 값은 위 표에서 옮긴 무방어 ASR.

| 모델 | AgentDojo (리더보드/MELON) | InjecAgent | ASB IPI | AgentDyn | DoomArena τ-bench 결합 | RTC-Bench 분리 | MCPTox | MSB |
|---|---|---|---|---|---|---|---|---|
| GPT-4o | 47.7% / 51.0% | 9.6% (ChatInject 평문) · 22.7% (SecAlign 표) | 62.45% | 37.80% | 70.8% | 66.19% | — | — |
| GPT-4o-mini | 27.2% | 3.3% (SecAlign 표) | 44.55% | — | — | — | 61.8% | 58.56% |
| Claude 3.5 Sonnet | 33.9% (06/20) · 1.1% (10/22) | — | 59.70% | 11.89% | 39.5% | 41.37% | — | — |
| Claude 3.7 Sonnet | 7.3% | — | — | — | (OSWorld 22.9%) | 39.33% | 34.3% | — |
| Gemini 2.5 Flash | 47.8% (AutoDojo 정적) · 27.9% (SecAlign 표) | 0.1% (SecAlign 표) | — | 37.61% | — | — | 59.7% | 30.26% |
| GPT-5 | 0.2% (SecAlign 표) · 4.7% (TAP) | 0.2% (SecAlign 표) | — | — | — | — | — | 37.17% |
| Llama-3.3-70B | 6.2% (MELON) · 14.7% (SecAlign 표) | 53.8% (SecAlign 표) | — | 11.91% | — | — | — | 46.61% |
| Llama-3-70B | 25.6% | — | 43.70% | — | — | — | — | — |
| Qwen3 계열 | Qwen3-4B TAP 45.2% · Qwen3.5-27B 26.3% | Qwen3.5-27B 3.6% | — | Qwen3-235B 22.67% | — | — | Qwen3-235b 50.6% (reasoning) | Qwen3 8B 47.23% |
| DeepSeek | V4-Flash 22.6–32.9% | V4-Flash 3.2% | — | — | — | — | R1 70.9% · V3 56.5% | V3.1 60.94% |

읽을 때 주의할 점:

- **AgentDojo와 InjecAgent의 ASR 방향이 모델에 따라 뒤집힌다.** Llama-3.3-70B는 AgentDojo 6–15%지만 InjecAgent 53.8%이고, GPT-4o-mini는 반대다. InjecAgent는 단일 툴 호출 판정이라 "지시를 따르기 쉬운 모델"이, AgentDojo는 다단계 환경 상태 판정이라 "툴 사용이 능숙한 모델"이 높게 나온다.
- **Claude 3.5 Sonnet의 두 스냅샷(2024-06-20 vs 2024-10-22)**은 AgentDojo에서 33.9% → 1.1%로 달라졌다. 모델 이름만으로 비교하면 안 되고 날짜 스탬프까지 봐야 한다.
- **결합 위협·툴 설명 오염·CUA 표면**에서는 GPT-4o가 66–71%까지 오른다. 같은 모델이 AgentDojo 단일 표면에서는 48–51%다. 표면이 늘수록 ASR이 오른다는 것이 횡단 표의 일관된 신호다.
- **2025 하반기 이후 상용 모델(GPT-5, Claude 4.5/Haiku 4.5, Gemini 3 Pro)**은 AgentDojo·AgentDyn 정적 공격에서 0–5%대로 내려왔다. 반면 LivePI(실환경) 10.7–29.6%, RTC-Bench 종단(Claude 4.5 Opus CUA) 83%, MSB(GPT-5) 37.17%는 여전히 높다.
