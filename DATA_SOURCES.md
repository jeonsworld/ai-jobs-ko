# Data Sources & Augmentation Plan

> ai-jobs-ko 사이트의 데이터를 어떻게 *최신·정확*하게 끌어올릴지 정리. 2026-04-30 웹서치 기준.

## 1. 현재 데이터 자산 (이미 통합됨)

| # | 데이터 | 현재 활용 | 한계 |
| --- | --- | --- | --- |
| C1 | KEIS KNOW 537개 직업 마스터 (2023) | 직업 분류 체계 + 카테고리(35) | 4년 된 데이터. 2024 갱신본 없음 |
| C2 | KEIS 직업전망 텍스트 (CSV, 1108행) | **사용 안 함** (코드 매핑 실패) | 직업코드 6자리 vs 마스터 5자리 비호환 |
| C3 | KEIS 학력 분포 데이터 | 사용 안 함 (코드 매핑 실패) | 동상 |
| C4 | KOSIS 직업별 취업자 (KSCO 대분류) | KSCO_TIMESERIES 16년치 하드코드 | 2025·2026 최신 갱신 필요 |
| C5 | 고용노동부 사업체노동력조사 | 카테고리별 평균 임금 (대분류 가중) | 17개 업종별 최신값 미반영 |
| C6 | 커리어넷 직업백과 552개 | 478개 실측 임금·직무 설명·조회수 | 매핑 232개만 — 추가 매핑 가능 |

## 2. 새로 발견한 데이터 (보강 후보)

### S1. ★★★ KOSIS 2025년 직업별 취업자 (최신)

- **출처**: 통계청 KOSIS `DT_1DA7E08S` 경제활동인구조사 / [국가데이터처](https://mods.go.kr/statDesc.es?act=view&mid=a10501010000&sttr_cd=S002001)
- **수치**: 2025년 8월 취업자 **28,967천명** (2,897만)
- **현재 우리 값**: 2,749만 (2025년 합계) — **~150만 ↓**
- **적용**: `KSCO_TIMESERIES`의 2025 컬럼을 +5.4% 스케일 보정 또는 발표값으로 직접 교체
- **신뢰도**: 공식 통계 ★★★★★

### S2. ★★★ 한국고용정보원 중장기 인력수급 전망 2024-2034

- **출처**: [KEIS 발표](https://statistics.keis.or.kr/keis/ko/bbs/225/detail.do?pageIndex=1&pstSn=64329) (2024년 12월 발간)
- **핵심**: 향후 10년 취업자 +6.4만 (연평균 0.0%). **2030년부터 감소세 전환**. 전기('24-29) +36.7만 / 후기('29-34) -30.3만
- **세부**: 보건복지 강세, 제조·도소매 약세
- **현재 우리 값**: 2030년 합계 ~2,800만 (자체 추정). 공식 전망과 비교 가능
- **적용**: KSCO_TIMESERIES 2026~2030 미래 시리즈를 KEIS 공식 전망으로 보정. **단순한 outlook 외삽이 아닌 *공식 전망*을 노출** → 신뢰도 ↑
- **신뢰도**: 정부 공식 ★★★★★

### S3. ★★★ Felten et al. AI Occupational Exposure (AIOE)

- **출처**: Felten, Raj, Seamans (2021) "Occupational, industry, and geographic exposure to artificial intelligence" SMJ 42(12), 데이터셋 [GitHub](https://github.com/AIOE-Data/AIOE)
- **수치**: O*NET 약 770개 직업의 AI 노출도 (Felten AIOE 점수)
- **현재 우리 값**: 직업명 키워드 휴리스틱 (정확도 낮음)
- **적용**: O*NET SOC 코드 ↔ KSCO 매핑 표를 통해 한국 직업으로 변환. 우리 휴리스틱 점수를 *학술 데이터로 부분 교체* + 출처 명시
- **신뢰도**: Peer-reviewed ★★★★

### S4. ★★ WEF Future of Jobs Report 2025 (Jan 2025)

- **출처**: [WEF Report PDF](https://reports.weforum.org/docs/WEF_Future_of_Jobs_Report_2025.pdf)
- **핵심**: 2030년까지 22% 일자리 변화 (170M new / 92M displaced, net +78M)
- **빠르게 성장**: 빅데이터 전문가, 핀테크 엔지니어, AI/ML 전문가, 보안 관리자, SW 개발자, 농민, 배달 운전사, 간호사, 중등교사, 자율주행/EV 전문가, 환경/재생에너지 엔지니어
- **빠르게 감소**: 캐셔, 행정보조, **그래픽 디자이너**(생성형 AI 영향), 우편사무원, 은행 텔러, 데이터 입력원
- **적용**: 매핑되는 한국 직업의 `outlook` 수치를 ±5~10 보정 (예: 그래픽디자이너 -8% → -15%, 빅데이터 +12% → +18%)
- **신뢰도**: 글로벌 ★★★★ (한국 특수성은 직접 적용 불가)

### S5. ★★ 고용노동부 2024 사업체노동력조사

- **출처**: [고용노동통계 laborstat.moel.go.kr](https://laborstat.moel.go.kr/) / [정책브리핑 2024년 8월분](https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=17112)
- **수치**: 2025년 상반기 평균 418.8만원/월 = **5,025만원/년**. 17개 업종별 분포 (금융·보험 805만, 숙박·음식 263만)
- **현재 우리 값**: 가중평균 4,717만 (커리어넷 실측 + 카테고리 추정 혼합)
- **적용**: KNOW 대분류별 임금 baseline을 17개 업종 가중치로 재산정. 격차 (8백만 vs 2.6백만)을 더 넓게 반영
- **신뢰도**: 공식 통계 ★★★★★

### S6. ★ KEIS 직업전망 텍스트 (CSV, 이미 보유)

- **출처**: 이미 `reference/keis_edu/직업전망.CSV` 보유 (1108행)
- **현재 우리 값**: 코드 매핑 실패로 미사용
- **적용**: 직업명 *substring 매칭*으로 KEIS 텍스트의 첫 1~2문장을 디테일 카드의 "공식 5년 전망 코멘트"로 추가 (work 필드 옆에)
- **공수**: 매우 작음 (이미 데이터 있음)
- **신뢰도**: 정부 공식 ★★★★

### S7. ★ 워크넷 직업정보 KNOW 시스템 직업별 페이지

- **출처**: career.go.kr 직업백과 (이미 552개 fetch). 추가로 *상세 페이지*에 평균 만족도, 5년 후 전망(증가/유지/감소 라벨), 적성·흥미 등 풍부 데이터.
- **현재**: 검색 API의 list 응답만 사용 (work, wage, views 등). 상세 페이지는 미사용.
- **적용**: 매핑된 232개 직업의 view 페이지를 한 번 fetch → 만족도·증감 라벨 추가
- **공수**: 232 페이지 fetch (1~2시간), HTML 파싱
- **신뢰도**: 정부 공식 ★★★★

## 3. 즉시 적용 우선순위

| 순위 | 항목 | 공수 | 효과 |
| --- | --- | :-: | --- |
| 1 | **S6 KEIS 직업전망 텍스트** 직업명 substring 매칭 후 디테일 카드에 통합 | S | 디테일 정보 풍부 + 정부 공식 인용 |
| 2 | **S1 KOSIS 2025 시계열 보정** (단순 스케일링) | S | 합계 정확도 ↑ |
| 3 | **S2 KEIS 중장기 전망**으로 미래 시리즈(2026~2030) 재계산 | M | 공식 전망 인용 가능, 사이트 권위 ↑ |
| 4 | **S5 고용노동부 17개 업종 임금**으로 카테고리 baseline 재산정 | M | 임금 정확도 ↑ |
| 5 | **S4 WEF 2025 직업** 한국어 매핑 → outlook 보정 | M | 글로벌 추세 반영 |
| 6 | **S3 Felten AIOE** 매핑 (O*NET ↔ KSCO 표 필요) | L | 노출도 점수 *학술 근거* |
| 7 | **S7 KNOW 상세 페이지** crawl | L | 만족도·전망 라벨 추가 |

## 4. 즉시 적용 (이번 사이클)

이번 작업 사이클에서는 **#1 (KEIS 직업전망 텍스트)** 와 **#2 (KOSIS 2025 시계열 보정)** 두 개를 즉시 적용한다.

이유
- #1: 이미 data.go.kr에서 받은 CSV 가 `reference/keis_edu/직업전망.CSV` 에 있음. 추가 fetch 없이 통합 가능. 디테일 카드에 *공식 KEIS 5년 전망 텍스트*가 표시되면 사이트 신뢰도 크게 ↑.
- #2: KOSIS 2025년 8월 취업자 1개 수치만으로 KSCO_TIMESERIES 2025 컬럼 보정 가능. 빌드 한 줄.

## 5. 후속 사이클 권장 순서

- **다음 사이클**: #3 KEIS 중장기 전망으로 KSCO_TIMESERIES 2026~2030 교체 → "공식 전망" 출처 명시
- **다다음**: #5 17개 업종 임금 표 통합 → 카테고리 임금 정확화
- **분기 정기 갱신**: KOSIS 발표 신규 데이터 자동 수집 스크립트 (Python)

## 6. 데이터 신뢰도 표시 강화 제안

현재 사이트는 임금에 [실측]/[추정] 뱃지를 표시. 이를 더 확장:
- `pay_source` 외에 `outlook_source`, `jobs_source`, `exposure_source` 필드 추가
- 디테일 카드에 각 지표가 어디서 왔는지 명시 (예: "KEIS 공식 / WEF 보정 / Felten 학술")
- 사용자가 *어느 수치가 권위 있는지* 즉시 알 수 있게

## Sources

- [KOSIS 국가통계포털](https://kosis.kr/)
- [KEIS 중장기 인력수급 2024-2034 발표](https://statistics.keis.or.kr/keis/ko/bbs/225/detail.do?pageIndex=1&pstSn=64329)
- [WEF Future of Jobs Report 2025](https://reports.weforum.org/docs/WEF_Future_of_Jobs_Report_2025.pdf)
- [Felten, Raj, Seamans (2021) AIOE](https://onlinelibrary.wiley.com/doi/10.1002/smj.3286)
- [고용노동부 노동통계](https://laborstat.moel.go.kr/)
- [Yale Budget Lab — Labor Market AI Exposure](https://budgetlab.yale.edu/research/labor-market-ai-exposure-what-do-we-know)
- [Economic Innovation Group — AI and Jobs (Aug 2025)](https://eig.org/ai-and-jobs-the-final-word/)

---

*ai-jobs-ko 라이브: <https://jeonsworld.github.io/ai-jobs-ko/>*
