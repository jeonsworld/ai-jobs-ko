# Wanted × ai-jobs-ko — Geek Edition

> 평범한 매칭 강화·대시보드를 넘어, **연구급·생성형·인터랙티브·오픈데이터**를 무기로 하는 차별화 후보. 기존 [IDEATION.md](./IDEATION.md)는 비즈니스 보강. 이 문서는 *세상에 없던 것*.

각 카드의 평가 축
- **Geek score**: 기술적 도전·신선함 (★~★★★★★)
- **Moat**: 모방 난이도·데이터 의존도 (낮음/중간/높음)
- **Stack**: 핵심 기술
- **Reference**: 유사 선례 (있으면)

---

## I. 연구급 (Research-grade)

### G1. Counterfactual Career Simulator — "만약 그 때 ML로 갔다면"
> 매칭/추천이 아니라 *반사실 인과추론*. 동일 출발점의 코호트에서 한쪽은 분기 A, 다른 쪽은 분기 B로 갈라졌을 때 5년 후 임금·만족도·이직률 차이를 추정.

- **무엇**: 지원자의 이력서를 입력 → 다른 직군 5개로 갔을 때 각각의 expected outcome (임금/이직/승진 확률) 표시.
- **방법**: Doubly Robust Estimation, T-learner / X-learner, Counterfactual Outcome Networks. 이력서 임베딩 + treatment(직군 선택) + outcome(N년 후 임금) triple.
- **Stack**: `EconML`, `causalml`, PyTorch, 임베딩 retrieval
- **Geek**: ★★★★★ — 채용 플랫폼이 인과추론 프로덕션화한 사례 거의 없음. 논문·블로그 글감.
- **Moat**: 높음 — 원티드 합격·이직 시계열 풍부함이 결정적
- **Reference**: Microsoft EconML, Uplift Modeling at Booking.com
- **차별**: 추천 모델은 "확률"만, 이건 "다른 길의 결과"를 보여줌.

### G2. Career Embedding Atlas (3D Constellation)
> 모든 익명화 이력서를 임베딩 → UMAP/t-SNE → 3D 우주 시각화. 사용자는 자신의 별 위치를 보고, 가까운 별(비슷한 사람)이 어디로 이동했는지 *궤적*으로 본다.

- **무엇**: three.js 기반 3D 우주. 각 별 = 익명 이력서. 직업 카테고리 = 성단. 사용자 위치 = 광점.
- **방법**: 이력서 → SBERT/Voyage embeddings → UMAP 3차원 → WebGL 렌더 (instanced mesh로 100k 점 60fps).
- **Stack**: SBERT, UMAP, three.js, deck.gl
- **Geek**: ★★★★★ — Visual·embedding·web3D 결합. PR/언론 즉시 반응
- **Moat**: 중간 — 임베딩 기술은 일반적이나 *익명화 + 권한 + UX*가 어려움
- **Reference**: Atlas of Spotify (Wrapped), Pinterest visual search, OpenAI's "world embeddings"
- **차별**: 직업 *지도*가 아니라 *우주*. 카테고리 추상이 아니라 실제 사람이 별이 됨.

### G3. Career Path Markov Chain — "직업 → 직업 흡수 확률"
> 한국 노동시장의 직업 이동을 537×537 transition matrix로 추정 → 사용자 출발점에서 모든 종점의 *흡수 확률* 시각화.

- **무엇**: "당신의 현 직업에서 50대까지 가장 높은 확률로 도달하는 종착지 top 10". *경로 길이별 확률*도 표시 (1년 후, 3년 후, 7년 후).
- **방법**: 익명화 이력서 시계열 → state(직업) transition 계수 → Higher-order Markov / Hidden Markov로 hidden state(스킬)도 추론.
- **Stack**: `pomegranate`, NumPy, 시각화 d3 Sankey
- **Geek**: ★★★★ — 학부생 모델이지만 실제로 풀-사이즈 데이터로 돌리는 곳은 거의 없음
- **Moat**: 높음 — 시계열 이력서 데이터 필수
- **차별**: "추천 직업"이 아니라 *통계적 운명*을 보여줌

### G4. AI-as-Coworker Index (ACI)
> 디지털 노출도(이론값)를 넘어, "이 직무에서 *실제로* AI와 협업하는 비율"을 측정해 새 지표로 발표.

- **무엇**: 매년 합격자에게 micro-survey ("주간 AI 도구 사용 시간", "AI에게 위임한 업무 비율") + 공고 텍스트의 "AI/Copilot/LLM" 키워드 시계열 → ACI 0~100 지수.
- **방법**: 설문 + 공고 NER + 시계열 분석. 직업별 ACI를 ai-jobs-ko 트리맵에 5번째 레이어로 추가.
- **Stack**: 설문 인프라, spaCy/KoNLPy, Plotly 시계열
- **Geek**: ★★★★ — 새 *지표 발명*. WEF·OECD가 인용할 가능성
- **Moat**: 매우 높음 — 매년 측정한 데이터 자체가 자산
- **Reference**: Stack Overflow Developer Survey의 AI usage 섹션
- **차별**: 노출도(이론) → 협업도(실측). 산업 표준 지표 자리 노림.

---

## II. 생성형 / 에이전트 (Generative / Agentic)

### G5. Career Coach Agent — Multi-step Reasoning
> 단발 LLM 답변이 아니라, 이력서 + 매칭 풀을 *retrieve* → *plan* → *simulate* → *recommend* 4단계 reasoning agent.

- **무엇**: 사용자가 "내가 5년 후 어디 있어야 할까?"라고 물으면, agent가 (1) 이력서를 537 분류로 매핑, (2) 비슷한 코호트의 종착점을 retrieve, (3) 각 경로의 임금·노출도·자격요건 시뮬레이션, (4) 3개 경로 추천 + 첫 90일 액션 플랜.
- **방법**: Anthropic Claude tool-use API + 이력서 vector DB + 직업 분류 retriever + 통계 계산 tool. LangGraph 또는 직접 agent loop.
- **Stack**: Claude Sonnet 4.6, vector DB (pgvector/Qdrant), LangGraph
- **Geek**: ★★★★★ — 에이전트 프로덕션화. 일반 챗봇과 격이 다름
- **Moat**: 중간 — 데이터+프롬프트 엔지니어링
- **Reference**: AlphaCareer 같은 표준은 없음. Anthropic Skills 기반.
- **차별**: 멘토 컨텐츠를 자동화·개인화

### G6. 모의 면접 시뮬레이터 (다인 모드)
> 사용자가 가상의 회사 인터뷰를 끝까지 시뮬레이션. *기술면접관·HR·CEO* 3명의 LLM agent가 멀티턴으로 대화. 마지막에 합격 확률 + 약점 리포트.

- **무엇**: 공고를 입력하면 그 회사 페르소나 3명 자동 생성 (실제 회사 리뷰 데이터 RAG). 사용자가 채팅 UI에서 면접 진행. 끝나면 합격 예측 모델 점수 + 개선 포인트.
- **방법**: 공고 + 회사 리뷰 → 페르소나 prompts. Multi-agent (각 에이전트가 자기 영역 질문). Final scoring = 별도 분류 모델.
- **Stack**: Claude/GPT, RAG (회사 리뷰), 합격 예측 모델
- **Geek**: ★★★★ — 멀티에이전트 + RAG + 모델 결합
- **Moat**: 높음 — 회사별 리뷰·합격 데이터가 *원티드만 보유*
- **차별**: ChatGPT로 흉내낼 수 없는 페르소나 *깊이*

### G7. 이력서 Diff Bot — "당신과 같은 출발점인데 합격한 사람의 이력서 차이"
> 익명화된 합격 이력서 코호트와 사용자 이력서를 *문장 단위 diff*. AI가 차이를 자연어로 요약 ("이 사람들은 평균적으로 1.7개의 사이드 프로젝트를 더 적었음").

- **무엇**: 합격 이력서 N개를 retrieval, 사용자 이력서와 LLM diff. 결과: "공통 키워드 17개, 당신만 있는 키워드 4개, 코호트만 있는 키워드 9개" + 사례 인용.
- **방법**: K-means로 합격자 클러스터 → 가장 가까운 cluster의 prototype이력서 합성 (LLM averaging) → diff 분석.
- **Stack**: SBERT, Claude, k-means, semantic diff
- **Geek**: ★★★ — 의미적 diff는 새로운 UX
- **Moat**: 매우 높음 — 익명화된 합격자 풀 필요
- **차별**: "더 노력하세요"가 아닌 *구체적 격차 측정*

---

## III. 인터랙티브 / 데이터 아트

### G8. Career Time Machine (1999~2030)
> 한국 노동시장 트리맵의 시계열 morphing 애니메이션. 슬라이더로 연도를 움직이면 직업이 부풀거나 줄어듦. 2030년 예측치까지 포함.

- **무엇**: 25년치 KOSIS 직업별 취업자 시계열 + 원티드 공고 추세 → *interpolated treemap morphing* (D3 transition).
- **방법**: 직업 인구 시계열을 ARIMA/Prophet로 보간 + 미래 예측. 트리맵 layout이 부드럽게 변하도록 *animated squarify*.
- **Stack**: D3.js, Prophet, 통계청 시계열 API
- **Geek**: ★★★★ — 트리맵 morphing은 의외로 어려움 (cell stability)
- **Moat**: 중간 — 데이터는 공개. 차별은 UX 디테일.
- **Reference**: Gapminder (Hans Rosling), NYT election dot animation
- **차별**: 한국 노동시장 25년 흐름을 30초에 보여줌. 강력한 PR.

### G9. Wanted Wrapped — 분기/연간 개인 채용 활동 회고
> Spotify Wrapped 형식으로 사용자의 1년 활동을 미니 영상/시리즈 카드로 생성. "당신은 올해 47개 공고를 봤고, 가장 많이 본 직군은 ML, 평균 매칭 점수는 73점, 한국 상위 12%."

- **무엇**: 9-12장의 풀스크린 카드 (애니메이션·생성 비주얼). 마지막에 SNS 공유 카드 자동 생성.
- **방법**: Generative gradient/typography (Three.js or Lottie), 사용자 데이터 → 카드 템플릿 채움. 각 카드는 음악·motion 디자인.
- **Stack**: Lottie, Framer Motion, OG image API, GPT 인트로/아웃트로 카피
- **Geek**: ★★★ — 기술 스택은 평범하지만 *디자인 완성도와 유저 발기점*이 핵심
- **Moat**: 낮음 (기술적), 매우 높음 (브랜드 가치)
- **Reference**: Spotify Wrapped, GitHub Wrapped
- **차별**: 채용 플랫폼에서 Wrapped는 처음. SNS 트래픽 폭발 가능

### G10. Career Genome — 직업 DNA 시각화
> 이력서를 64-bit "직업 게놈"으로 표현 (스킬 비트맵). 같은 게놈 사람들의 운명을 추적. 사용자에게 "당신 게놈의 87%는 백엔드, 11%는 데이터, 2%는 디자인. 같은 게놈 사람들의 5년 후 분포는…"

- **무엇**: 64개 스킬·역량 차원을 1bit씩 → 직업 게놈 string (`A7F3...`). 시각화는 helix·circular barcode.
- **방법**: 스킬 임베딩 → quantization → 64-dim binary code (Locality-sensitive hashing). 동일 prefix(접두) 사용자끼리 cluster.
- **Stack**: SBERT + LSH, 시각화 d3 helix
- **Geek**: ★★★★ — Bioinformatics × HR. 컨셉이 새롬
- **Moat**: 중간
- **차별**: "당신의 직업 DNA"라는 인지적 hook. 매우 sticky한 컨셉.

---

## IV. 오픈데이터 / Moat

### G11. Open Korea Career Graph (Open Source Dataset)
> 익명화·집계된 한국 직업 이동 그래프를 Hugging Face Hub에 공개. 학계 인용·정부 자문·미디어 인용의 단일 소스 자처. CC-BY-NC.

- **무엇**: 직업 → 직업 이동 weighted graph (537 nodes), 시계열 snapshot 10개 (2015~2024). README + 사용 예시 노트북.
- **방법**: 익명화 수준 결정 (k-anonymity ≥ 5), 집계 단위, IRB 검토. 데이터 카드(Datasheet for Datasets) 작성.
- **Stack**: Hugging Face Datasets, NetworkX, Pandas
- **Geek**: ★★★★ — 채용 회사가 자발적으로 데이터 공개한 사례 드뭄
- **Moat**: ★★★★★ — *데이터 발행자* 라는 비싼 포지션. OECD/논문 인용시 자동 광고
- **Reference**: LinkedIn Economic Graph (closed), Indeed Hiring Lab (reports only)
- **차별**: 한국 노동시장 *유일한* 공개 graph. 정책 영향력으로 직결.

### G12. Wanted Research API — 연구자·기자 전용
> 익명화된 마이크로데이터를 rate-limited API로 제공. 학생·기자·연구자가 신청 → 승인 → 토큰. 활용 보고서 발행 의무.

- **무엇**: REST API. `/api/v1/transitions?from_job=백엔드&year=2023` 등 엔드포인트. 결과는 집계·익명화.
- **방법**: FastAPI + Postgres + 토큰 mgmt + audit log. 활용 보고서를 publication 페이지에 큐레이션.
- **Stack**: FastAPI, PostgreSQL, Hasura/PostgREST
- **Geek**: ★★★ — 인프라 자체는 평범. *정책·거버넌스가 어려움*
- **Moat**: 매우 높음 — 사용자 락인 (논문 cite 한 번 박히면 영구)
- **차별**: 한국에서 *처음* 시도. 원티드의 thought leadership 결정적 자산.

---

## V. 보너스 — 게이미피케이션 / 색다른 UX

### G13. Career RPG — 경력을 게임으로
> 사용자 이력서 = RPG 캐릭터 시트. 스킬 트리, 클래스 변경 (직업 전환), 퀘스트 (스킬 학습 추천), 던전 (도전적 공고). 길드 (회사 컬쳐). 레벨업 시 노출도/임금 지표 변화.

- **무엇**: 풀-게임 메타. UI는 Diablo·POE 영감. 매칭 추천 = "퀘스트 보드".
- **방법**: 기존 매칭 엔진 위에 게임 레이어. 스킬 트리 = 직업 분류 graph 시각화 변형.
- **Stack**: React + 픽셀아트 또는 isometric 3D
- **Geek**: ★★★★ — 모험적. 하드코어 사용자에게 폭발적
- **Moat**: 낮음 (기술), 중간 (브랜드 정체성)
- **차별**: 채용 플랫폼이 *게임이 되는* 첫 시도

### G14. Adversarial Resume Stress Test
> 사용자가 이력서를 올리면 합격 예측 모델이 *공격받는다*. "키워드 1개를 추가하면 합격률 +12%, 그런데 이건 모델의 spurious feature일 가능성 ★★★." 모델 해석성 + 사용자 피드백.

- **무엇**: SHAP·integrated gradient로 합격 모델의 변수 중요도 → 사용자에게 "이 단어 추가 시 점수 X" + "그러나 이 변수는 noise일 수 있음" 경고.
- **방법**: 모델 + 해석성 라이브러리 + adversarial example 생성.
- **Stack**: SHAP, Captum, 자체 합격 모델
- **Geek**: ★★★★ — ML 해석성 + UX. 한국 채용에서 처음.
- **Moat**: 중간
- **차별**: ATS 키워드 hack 방지·교육 효과. ML 윤리적 포지셔닝 가능.

### G15. Public Anonymized Salary Whisper
> 합격자가 익명으로 *whisper* (협상 후 연봉) 등록 → 같은 직군·연차의 분포 즉시 노출. 단, 본인 데이터를 등록한 사람만 볼 수 있음 (give-to-get).

- **무엇**: Levels.fyi의 한국·B2C 버전. 원티드 합격 데이터로 부트스트랩. 사용자 voluntary 갱신.
- **방법**: 등록·검증·익명화 파이프라인. 직업명 매핑은 ai-jobs-ko 537 분류.
- **Stack**: 단순 backend + 시각화
- **Geek**: ★★★ — 기술적으로는 단순, 하지만 *사회적 임팩트* 큼
- **Moat**: 매우 높음 — Network effect (사용자 많을수록 가치 ↑)
- **Reference**: Levels.fyi, Glassdoor, Blind
- **차별**: 한국에 levels.fyi급 임금 투명성 사이트 부재. 시장 기회.

---

## 가장 야심찬 3개 추천

| Top | 이름 | 한 줄 |
| --- | --- | --- |
| **#1** | G1 Counterfactual Career Simulator | 채용 플랫폼이 인과추론을 프로덕션화한 *세계 최초 사례*. 논문급 모트. |
| **#2** | G2 Career Embedding Atlas (3D) | "사람의 별이 떠 있는 우주" — 한 번만 보면 잊혀지지 않는 비주얼. 강력한 PR + 회원 가입 핵폭. |
| **#3** | G11 Open Korea Career Graph | 데이터 공개 = 시장 *주도자* 포지션. 학계·정책·미디어가 *원티드를 인용해야만* 하는 상태. |

세 가지를 합치면 **"AI 시대 한국 직업 변화의 단일 권위자"** 포지션을 1년 안에 점유 가능.

---

## 6주 PoC 추천 — G1 Counterfactual

가장 임팩트·도전·차별 모두 큰 후보. 짧은 PoC 가능.

| 주차 | 작업 |
| --- | --- |
| 1주 | Treatment 정의 (직군 5개 분기) + 코호트 정의 (출발점 직업·연차·학력) |
| 2주 | 익명화 이력서 시계열 추출, outcome metric 정의 (3년 후 임금) |
| 3주 | T-learner / X-learner 학습 (EconML), bias 진단 |
| 4주 | 추정 통계 검증, 사례 5개 cherry-pick하여 의사결정자에게 데모 |
| 5주 | UI 프로토타입 (이력서 입력 → 5개 분기 결과 카드) |
| 6주 | 내부 베타, A/B 트래픽 1%로 매칭 영향 측정 |

성공 조건: 추정값이 직관과 부합 + 사례 5개 중 4개 이상 의사결정자가 신뢰

---

## 보너스 ― 메타 코멘트

이 카드들의 공통 패턴
1. **거대 데이터 × 지적 호기심** — 단순 매칭 강화가 아니라 *질문이 새로움*
2. **모방 어려움** — 데이터·정책·UX 중 최소 2가지 layer가 동시에 필요
3. **외부 연결** — 학계·언론·정부와 자연스러운 접점
4. **PR 가능성** — 한 줄 헤드라인이 잘 잡힘 ("한국 직업의 우주", "AI 시대 진로 인과추론")

가장 빠른 quick-win이라도 *quirky한 한 줄 컨셉*은 잡고 시작하는 게 핵심. "Wanted Wrapped"는 기술적으로 쉬워도 컨셉만으로 유사 사례를 1년 압도할 수 있음.

---

*작성: 2026-04-30. ai-jobs-ko 라이브: <https://jeonsworld.github.io/ai-jobs-ko/>. 기존 비즈니스 보강 IDEATION.md와 함께 검토.*
