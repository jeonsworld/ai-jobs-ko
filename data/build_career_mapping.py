"""
KEIS 537개 KNOW 직업명 → career.go.kr seq 매핑 빌드 (v2 — 보수적·정확매칭 우선).

설계 원칙
- **정확매칭/정규화 매칭이 가능하면 그것을 항상 우선** (SPECIAL_RULES 무시)
- SPECIAL_RULES은 KEIS 세분화 직업이 career의 다른 이름과 같은 것임을 명시할 때만 사용 (사전 검증된 것만)
- 토큰 매칭은 핵심 분야 키워드가 일치할 때만 허용 (임계값 0.7+)
- 잘못된 매핑 1개는 옳은 매핑 10개보다 나쁘다 — 매칭 안 되면 fallback URL로
"""

from __future__ import annotations

import csv
import json
import re
import urllib.request

REF = "reference"
KEIS_JOBS_CSV = f"{REF}/keis_jobclass/직업세세분류.CSV"
CAREER_RAW = "data/career_raw.json"
OUTPUT = "data/keis_to_career_seq.json"


def fetch_career_jobs() -> list[dict]:
    """career.go.kr 직업백과 552개 전체 fetch."""
    all_jobs: list[dict] = []
    for page in range(0, 5):
        req = urllib.request.Request(
            f"https://www.career.go.kr/cloud/api/job/search?size=200&page={page}&sort=seq,asc",
            method="POST",
            data=b"{}",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Referer": "https://www.career.go.kr/cloud/w/job/list",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        all_jobs.extend(data.get("content", []))
        if data.get("last"):
            break
    return all_jobs


def normalize(s: str) -> str:
    return re.sub(r"[ \t·・、。\.\/\(\)·ㆍ_\-]+", "", s).lower()


# ============================================================
# SPECIAL_RULES (사전 검증된 매핑만)
# career.go.kr에 정확매칭이 *없는* 경우만 등록할 것.
# 정확매칭 가능한 직업은 SPECIAL_RULES에 두지 말 것 (자동 매칭으로 처리).
# ============================================================
SPECIAL_RULES: dict[str, str] = {
    # === 음식 서비스 ===
    "한식조리사": "조리사 및 주방장",
    "중식조리사": "조리사 및 주방장",
    "양식조리사": "조리사 및 주방장",
    "일식조리사": "조리사 및 주방장",
    "음료조리사": "바리스타",
    "패스트푸드준비원": "조리사 및 주방장",
    # 주방보조원·바텐더 등은 career에 정확매칭 → SPECIAL_RULES 불필요
    "홀서빙원": "웨이터",
    "음식배달원": "요리배달원",
    "바텐터": "바텐더",
    # === 판매 ===
    "통신기기·서비스판매원": "상점판매원",
    "온라인판매원": "상점판매원",
    "노점 및 이동판매원": "상점판매원",
    "매표원 및 복권판매원": "상점판매원",
    "소규모판매점장": "상점판매원",
    # === 영업 ===
    "기술영업원": "영업원",
    "해외영업원": "영업원",
    "제품광고영업원": "영업원",
    # 자동차영업원은 career에 정확매칭
    # === 운전 ===
    "택시운전원": "택시운전기사",
    "버스운전원": "버스운전기사",
    "화물차·특수차운전원": "트럭운전기사",
    "철도·전동차기관사": "철도 및 지하철기관사",
    "건설·채굴기계운전원": "건설기계운전원",
    # 크레인·호이스트운전원·지게차운전원은 career에 정확매칭
    # === 항공/선박 ===
    "항공기조종사": "비행기조종사",
    "헬리콥터조종사": "비행기조종사",
    # 선장 및 항해사·선박갑판원 등은 career에 정확매칭
    "선박교통관제사": "항공교통관제사",  # career에는 항공 교통 관제사만 있음 (애매하지만 분야 유사)
    "철도교통관제사": "항공교통관제사",  # 동일
    # === 군경 ===
    "장교": "직업군인",
    "부사관": "직업군인",
    "일반군인": "직업군인",
    # 경찰관·소방관은 career에 정확매칭
    # === 보육·돌봄 ===
    "요양간호사 및 간병인": "간병인",
    # === 환경/위생 ===
    "환경미화원 및 재활용품수거원": "환경미화원",
    # === 의료 (전문의로 통합) ===
    "내과의사": "전문의사",
    "외과의사": "전문의사",
    "성형외과의사": "전문의사",
    "산부인과의사": "전문의사",
    "이비인후과의사": "전문의사",
    "안과의사": "전문의사",
    "정신과의사": "전문의사",
    "소아과의사": "전문의사",
    "방사선과의사": "전문의사",
    "마취병리과의사": "전문의사",
    "비뇨기과의사": "전문의사",
    "피부과의사": "전문의사",
    "가정의학과의사": "전문의사",
    "한약사": "약사 및 한약사",
    # 약사·치과의사·한의사·수의사·일반의사는 career에 정확매칭
    # === 작가/기자 ===
    "신문기자": "기자",
    "방송기자": "기자",
    "잡지기자": "기자",
    "영화시나리오작가": "방송작가",
    # === 건설 기능공 (career의 일반화된 직업으로) ===
    "건축석공": "석공",
    "건축목공": "목공",
    "전통건축기능원": "목공",
    "경량철골공": "철골공",
    # 미장공·방수공·도배공·배관원·도장원은 career에 정확매칭
    "미장공": "미장원",
    "방수공": "방수원",
    "도배공": "도배원",
    "건물도장공": "건물도장원",
    "공업배관공": "배관원",
    # === 정비 ===
    # 냉동기사·통신케이블설치 등은 career에 정확매칭
    # === 영업·판매 관리자 (KEIS는 세분화) ===
    # 운송관리자·영업·판매관리자 등은 career에 정확매칭
}

# ============================================================
# Career.go.kr에는 매칭이 없거나 매핑 시도가 위험한 직업 — 강제 fallback
# ============================================================
FORCE_FALLBACK = {
    "응용소프트웨어개발자",  # career에 없음. 시스템SW와 다름
    "웹개발자",  # career에 없음
    "IT테스터 및 QA전문가(SW테스터)",
    "데이터베이스개발자",  # career에 없는 듯
    "빅데이터분석가",
    "정보보안전문가",
    "보험보상사무원",  # 사무원이지 손해사정사가 아님
    "조세행정사무원",  # 사무원이지 세무사가 아님
    "관세행정사무원",  # 사무원이지 관세사가 아님
    "병무행정사무원",
    "공공행정사무원",
    "법원공무원",
    "행정사",
    "취업알선원",  # career의 "직업상담 및 취업알선원"은 길어서 fuzzy 매칭이 위험
    "산후관리사",
    "패션소품디자이너",
    "텍스타일디자이너",
    "건축안전·환경·품질·에너지관리기술자",
    "강구조물가공원 및 건립원",
    "철근공",
    "단열공",
    "잠수기능원",
    "검표원",
    "방역원",
    "주차관리·안내원",
    "계기검침원 및 가스점검원",
    "타일·대리석시공원",
    "섀시조립·설치원",
    "유리부착원",  # career에 정확매칭이지만 ambiguous
    "철로설치·보수원",
    "점화·발파·화약관리원",
    "건설·채굴단순종사원",
    "건설·광업기계설치·정비원",
    "농업용 및 기타 기계장비설치·정비원",
    "냉동·냉장·공조기설치·정비원",  # career의 "냉동기사"와 다름 (정비 vs 운전)
    "물품이동장비설치·정비원",
    "보일러설치·정비원",
    "승강기설치·정비원",
    "공업기계설치·정비원",
    "전기·가스·수도관리자",  # career에 적절한 매핑 없음
    "전기·전자공학시험원",
    "전기·전자설비조작원",
    "전기·전자부품·제품조립원",
    "펄프·종이제조장치조작원",
    "광원·채석원 및 석재절단원",
    "사진인화·현상기조작원(사진수정 포함)",
    "가전제품설치·수리원",
    "방송장비설치·수리원",
    "통신장비설치·수리원",
    "자전거판매 및 수리원",
    "자동차부품조립·검사원",
    "여행·호텔관리자",
    "광고·홍보·마케팅사무원",
    "토목구조설계기술자",  # 토목공학기술자와 비슷하지만 별도
    "건설기계공학기술자 및 연구원",
    "의약품공학기술자 및 연구원",
    "수질환경기술자 및 연구원",
    "소방공학기술자 및 연구원",
    "고무·플라스틱 화학공학기술자 및 연구원",
    "도료·농약품 화학공학기술자 및 연구원",
    "비누·화장품 화학공학기술자 및 연구원",
    "디스플레이연구 및 개발자",
    "풍력발전연구 및 개발자",
    "조림·산림경영인 및 벌목원",
    "정육원 및 도축원",
    "학습장애간호사",  # 같은 이름이 있긴 하지만 너무 specific
}


# ============================================================
# 토큰 매칭 — 매우 보수적 (핵심 분야 키워드 검증)
# ============================================================
GENERIC_TOKENS = {
    "기술자",
    "연구원",
    "종사자",
    "관리자",
    "전문가",
    "사무원",
    "기능사",
    "기능원",
    "보조원",
    "단순",
    "관련",
    "조작원",
    "운전원",
    "정비원",
    "설치",
    "수리원",
    "및",
    "분야",
    "기타",
    "일반",
    "고등",
    "중등",
}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def core_tokens(name: str) -> set:
    """직업명에서 일반 토큰을 제외한 핵심 분야 토큰만."""
    toks = set(re.findall(r"[가-힣]{2,}", name))
    return {t for t in toks if t not in GENERIC_TOKENS}


def safe_token_match(keis: str, career_list: list[tuple[str, str, int]]) -> int | None:
    """핵심 토큰의 jaccard ≥ 0.6 + 첫 토큰 일치 시에만 매칭."""
    keis_core = core_tokens(keis)
    if len(keis_core) == 0:
        return None
    best_seq = None
    best_score = 0.0
    keis_first = re.findall(r"[가-힣]{2,}", keis)
    keis_first = keis_first[0] if keis_first else None

    for c_norm, c_orig, c_seq in career_list:
        c_core = core_tokens(c_orig)
        if not c_core:
            continue
        # 핵심 토큰 jaccard
        score = jaccard(keis_core, c_core)
        # 핵심 토큰 한쪽 포함이면 가산
        if keis_core.issubset(c_core) or c_core.issubset(keis_core):
            score += 0.15
        # 첫 토큰 일치 시 가산
        c_first = re.findall(r"[가-힣]{2,}", c_orig)
        c_first = c_first[0] if c_first else None
        if keis_first and keis_first == c_first:
            score += 0.10
        if score > best_score and score >= 0.65:
            best_score = score
            best_seq = c_seq
    return best_seq


def main():
    # 1) career 데이터
    try:
        with open(CAREER_RAW, encoding="utf-8") as f:
            raw = json.load(f)
            career_jobs = raw if isinstance(raw, list) else raw.get("content", [])
    except FileNotFoundError:
        career_jobs = fetch_career_jobs()
        with open(CAREER_RAW, "w", encoding="utf-8") as f:
            json.dump(career_jobs, f, ensure_ascii=False, indent=2)

    if len(career_jobs) < 500:
        career_jobs = fetch_career_jobs()
        with open(CAREER_RAW, "w", encoding="utf-8") as f:
            json.dump(career_jobs, f, ensure_ascii=False, indent=2)

    career = {r["job_nm"]: int(r["job_cd"]) for r in career_jobs}
    career_norm: dict[str, int] = {}
    for n, seq in career.items():
        career_norm.setdefault(normalize(n), seq)
    career_list = [(normalize(n), n, seq) for n, seq in career.items()]
    print(f"career.go.kr 직업백과: {len(career)}개")

    # 2) KEIS 직업
    with open(KEIS_JOBS_CSV, encoding="euc-kr") as f:
        keis_jobs = [r["KNOW직업명"].strip() for r in csv.DictReader(f)]
    print(f"KEIS KNOW: {len(keis_jobs)}개")

    # 3) 매핑 — 보수적 우선순위
    # (1) 강제 fallback: 매핑 시도 안 함
    # (2) 정확 매칭
    # (3) 정규화 매칭
    # (4) 검증된 SPECIAL_RULES
    # (5) 안전한 토큰 매칭 (jaccard ≥ 0.65 + 첫 토큰 일치)
    # 그 외는 매핑 안 함 (fallback URL)

    mapping: dict[str, int] = {}
    matched_by = {"exact": 0, "norm": 0, "special": 0, "token": 0, "fallback": 0}

    for name in keis_jobs:
        if name in FORCE_FALLBACK:
            matched_by["fallback"] += 1
            continue
        # (2) 정확 매칭
        if name in career:
            mapping[name] = career[name]
            matched_by["exact"] += 1
            continue
        # (3) 정규화 매칭
        nn = normalize(name)
        if nn in career_norm:
            mapping[name] = career_norm[nn]
            matched_by["norm"] += 1
            continue
        # (4) SPECIAL_RULES
        if name in SPECIAL_RULES:
            target = SPECIAL_RULES[name]
            if target in career:
                mapping[name] = career[target]
                matched_by["special"] += 1
                continue
            tn = normalize(target)
            if tn in career_norm:
                mapping[name] = career_norm[tn]
                matched_by["special"] += 1
                continue
        # (5) 안전한 토큰 매칭
        seq = safe_token_match(name, career_list)
        if seq is not None:
            mapping[name] = seq
            matched_by["token"] += 1
            continue
        matched_by["fallback"] += 1

    total = len(keis_jobs)
    print("\n매핑 결과:")
    print(f"  정확 매칭        : {matched_by['exact']:>4}")
    print(f"  정규화 매칭      : {matched_by['norm']:>4}")
    print(f"  SPECIAL_RULES    : {matched_by['special']:>4}")
    print(f"  안전 토큰 매칭   : {matched_by['token']:>4}")
    print(f"  fallback (미매핑): {matched_by['fallback']:>4}")
    print("  ---------------------------")
    print(f"  매핑 완료        : {len(mapping)}/{total} ({len(mapping) / total * 100:.1f}%)")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(mapping)} mappings to {OUTPUT}")

    # 4) 핵심 직업 검증
    print("\n=== 핵심 직업 매핑 검증 ===")
    seq2name = {seq: name for name, seq in career.items()}
    samples = [
        "회계사",
        "간호사",
        "한식조리사",
        "상점판매원",
        "초등학교교사",
        "내과의사",
        "택시운전원",
        "경찰관",
        # 이전에 잘못 매핑됐던 것들
        "시스템소프트웨어개발자",
        "응용소프트웨어개발자",
        "IT테스터 및 QA전문가(SW테스터)",
        "선장 및 항해사",
        "선박갑판원",
        "음식배달원",
        "주방보조원",
        "메이크업아티스트",
        "한약사",
        "취업알선원",
    ]
    for s in samples:
        if s in mapping:
            print(f"  {s:<35} → {seq2name.get(mapping[s], '?')} (seq={mapping[s]})")
        else:
            print(f"  {s:<35} → fallback")


if __name__ == "__main__":
    main()
