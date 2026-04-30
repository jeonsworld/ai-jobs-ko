"""
KEIS 537개 KNOW 직업명 → career.go.kr seq 매핑 빌드.

데이터 흐름:
1. career.go.kr 직업백과 검색 API (POST /cloud/api/job/search) 로 552개 전체 직업 수집
2. 정확/정규화 매칭 + 변환 규칙(KEIS 세분화 직업 → career 일반화 직업) + 토큰 매칭
3. 매칭 결과를 data/keis_to_career_seq.json에 저장
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


# KEIS 세분화 직업명 → career 일반화 직업명
SPECIAL_RULES: dict[str, str] = {
    # 조리사
    "한식조리사": "조리사 및 주방장",
    "중식조리사": "조리사 및 주방장",
    "양식조리사": "조리사 및 주방장",
    "일식조리사": "조리사 및 주방장",
    "음료조리사": "바리스타",
    "패스트푸드준비원": "조리사 및 주방장",
    "주방보조원": "조리사 및 주방장",
    "주방장": "조리사 및 주방장",
    "홀서빙원": "웨이터",
    "음식배달원": "택배원",
    "바텐터": "바텐더",
    # 판매원
    "통신기기·서비스판매원": "상점판매원",
    "온라인판매원": "상점판매원",
    "노점 및 이동판매원": "상점판매원",
    "방문판매원": "방문판매원",
    "매표원 및 복권판매원": "상점판매원",
    "소규모판매점장": "상점판매원",
    # 영업
    "기술영업원": "영업원",
    "해외영업원": "영업원",
    "제품광고영업원": "영업원",
    "자동차영업원": "자동차영업원",
    # 운전
    "택시운전원": "택시운전기사",
    "버스운전원": "버스운전기사",
    "화물차·특수차운전원": "트럭운전기사",
    "철도·전동차기관사": "철도 및 지하철기관사",
    "건설·채굴기계운전원": "건설기계운전원",
    "크레인·호이스트운전원": "크레인 및 호이스트운전원",
    "지게차운전원": "지게차운전원",
    # 항공/선박
    "항공기조종사": "비행기조종사",
    "헬리콥터조종사": "비행기조종사",
    "선박교통관제사": "항공교통관제사",
    "철도교통관제사": "항공교통관제사",
    "선장 및 항해사": "선박갑판원",
    "선박기관사": "선박정비원",
    # 군경/소방
    "장교": "직업군인",
    "부사관": "직업군인",
    "일반군인": "직업군인",
    # 보육·돌봄
    "요양간호사 및 간병인": "간병인",
    "육아도우미": "보육교사",
    "산후관리사": "간병인",
    "베이비시터": "보육교사",
    # 환경/검침
    "환경미화원 및 재활용품수거원": "환경미화원",
    "방역원": "방역원",
    "주차관리·안내원": "주차관리원",
    "검표원": "안내원",
    "계기검침원 및 가스점검원": "검침원",
    # 사무
    "행정사": "행정공무원",
    "취업알선원": "직업상담사",
    "공공행정사무원": "행정공무원",
    "법원공무원": "행정공무원",
    "조세행정사무원": "세무사",
    "관세행정사무원": "관세사",
    "병무행정사무원": "행정공무원",
    "출납창구사무원": "은행원",
    "은행사무원": "은행원",
    "증권사무원": "증권중개인",
    "보험보상사무원": "손해사정사",
    "법률사무원": "법률사무원",
    # 교사
    "중·고등학교교사": "인문계중등학교교사",
    # 디자이너
    "제품디자이너": "산업디자이너",
    "패션소품디자이너": "패션디자이너",
    "텍스타일디자이너": "패션디자이너",
    # 농림/어업
    "양식원": "양식기술자",
    "어부": "어부 및 해녀",
    "임업종사자": "임업기술자",
    "축산종사자": "축산기술자",
    # 작가/기자
    "신문기자": "기자",
    "방송기자": "기자",
    "잡지기자": "기자",
    "방송작가": "방송작가",
    "영화시나리오작가": "방송작가",
    "출판물기획자": "출판물기획자",
    # 의료 — 전문의 통합
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
    "한약사": "약사",
    # IT — 일반개발자는 시스템소프트웨어개발자(가장 일반)에 매핑
    "응용소프트웨어개발자": "시스템소프트웨어개발자",
    "웹개발자": "응용소프트웨어 개발자",
    "모바일앱개발자": "모바일앱개발자",
    "데이터베이스개발자": "데이터베이스 개발자",
    "빅데이터분석가": "빅데이터분석가",
    "정보시스템운영자": "시스템운영관리자",
    "정보보안전문가": "정보보안전문가",
    # 건설
    "건축가(건축설계사)": "건축가",
    "건축설계기술자": "건축가",
    "건축구조기술자": "건축구조기술자",
    "토목구조설계기술자": "토목공학기술자",
    "도시계획·설계가": "도시계획전문가",
    # 미용
    "이용사": "이용사",
    "메이크업아티스트": "메이크업아티스트",
    "피부관리사": "피부미용사",
    # 기능공
    "강구조물가공원 및 건립원": "강철구조물조립원",
    "경량철골공": "강철구조물조립원",
    "철근공": "강철구조물조립원",
    "건축석공": "석공",
    "건축목공": "목공",
    "전통건축기능원": "목공",
    "조적원": "조적원",
    "미장공": "미장원",
    "방수공": "방수원",
    "단열공": "단열공",
    "타일·대리석시공원": "타일공",
    "도배공": "도배원",
    "건물도장공": "건물도장원",
    "섀시조립·설치원": "섀시조립원",
    "배관공": "배관원",
    "공업배관공": "배관원",
    "철로설치·보수원": "건설기계운전원",
    "점화·발파·화약관리원": "발파원",
    "잠수기능원": "잠수원",
    "건설·채굴단순종사원": "건설노무자",
    "건설노무자": "건설노무자",
    # 정비
    "냉동·냉장·공조기설치·정비원": "냉동기사",
    "건설·광업기계설치·정비원": "건설기계운전원",
    "농업용 및 기타 기계장비설치·정비원": "농업기술자",
    # 경비
    "시설·특수경비원": "경비원",
}

STOP = {"및", "분야", "일반", "전문", "관리", "관련", "연구", "기술자", "종사자", "기능사", "기능원", "단순"}


def token_match(name: str, career: dict[str, int], career_list: list[tuple[str, str, int]]):
    keis_norm = normalize(name)
    keis_tokens = [t for t in re.findall(r"[가-힣]{2,}", name) if t not in STOP]
    if not keis_tokens:
        return None
    best = None
    best_score = 0.0
    for c_norm, c_orig, c_seq in career_list:
        c_tokens = [t for t in re.findall(r"[가-힣]{2,}", c_orig) if t not in STOP]
        if not c_tokens:
            continue
        overlap = len(set(keis_tokens) & set(c_tokens))
        if overlap == 0:
            continue
        score = overlap / len(set(keis_tokens) | set(c_tokens))
        if keis_tokens[0] == c_tokens[0]:
            score += 0.2
        if abs(len(keis_norm) - len(c_norm)) < 3:
            score += 0.1
        if score > best_score and score >= 0.4:
            best_score = score
            best = c_seq
    return best


def main():
    # 1) career 데이터 로드 (없으면 fetch)
    try:
        with open(CAREER_RAW, encoding="utf-8") as f:
            raw = json.load(f)
            career_jobs = raw if isinstance(raw, list) else raw.get("content", [])
    except FileNotFoundError:
        career_jobs = fetch_career_jobs()
        with open(CAREER_RAW, "w", encoding="utf-8") as f:
            json.dump(career_jobs, f, ensure_ascii=False, indent=2)

    # 552개 다 받았는지 확인 → 부족하면 새로 fetch
    if len(career_jobs) < 500:
        career_jobs = fetch_career_jobs()
        with open(CAREER_RAW, "w", encoding="utf-8") as f:
            json.dump(career_jobs, f, ensure_ascii=False, indent=2)

    career = {r["job_nm"]: int(r["job_cd"]) for r in career_jobs}
    career_norm: dict[str, int] = {}
    for n, seq in career.items():
        career_norm.setdefault(normalize(n), seq)
    career_list = [(normalize(n), n, seq) for n, seq in career.items()]
    print(f"career 직업백과: {len(career)}개")

    # 2) KEIS 직업
    with open(KEIS_JOBS_CSV, encoding="euc-kr") as f:
        keis_jobs = [r["KNOW직업명"].strip() for r in csv.DictReader(f)]
    print(f"KEIS KNOW: {len(keis_jobs)}개")

    # 3) 매핑
    mapping: dict[str, int] = {}
    unmatched: list[str] = []
    for name in keis_jobs:
        if name in SPECIAL_RULES:
            target = SPECIAL_RULES[name]
            if target in career:
                mapping[name] = career[target]
                continue
            tn = normalize(target)
            if tn in career_norm:
                mapping[name] = career_norm[tn]
                continue
        if name in career:
            mapping[name] = career[name]
            continue
        nn = normalize(name)
        if nn in career_norm:
            mapping[name] = career_norm[nn]
            continue
        # substring (양방향, 길이 4 이상)
        cands = [
            (c_seq, c_orig)
            for c_norm, c_orig, c_seq in career_list
            if len(nn) >= 4 and (nn in c_norm or (len(c_norm) >= 4 and c_norm in nn))
        ]
        if cands:
            cands.sort(key=lambda x: -len(x[1]))
            mapping[name] = cands[0][0]
            continue
        tm = token_match(name, career, career_list)
        if tm:
            mapping[name] = tm
            continue
        unmatched.append(name)

    print(f"매칭: {len(mapping)}/{len(keis_jobs)} ({len(mapping) / len(keis_jobs) * 100:.1f}%)")
    print(f"미매칭: {len(unmatched)}")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(mapping)} mappings to {OUTPUT}")


if __name__ == "__main__":
    main()
