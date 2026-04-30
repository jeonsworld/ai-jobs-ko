"""
KEIS KNOW 537개 직업 마스터 + KOSIS 카테고리 통계를 결합해 site/data.json 생성.

출력 스키마(레퍼런스 karpathy/jobs와 동일):
  title, slug, category, pay, jobs, outlook, outlook_desc, education, exposure, exposure_rationale, url

데이터 출처:
- 직업 마스터(537): 한국고용정보원 KNOW 직업분류 (data.go.kr/data/15119096)
- 학력 분포 / 직업전망 텍스트: 한국고용정보원 (data.go.kr/data/15119098)
- 직업 대분류별 취업자수: KOSIS 경제활동인구조사 2024 (orgId=101, tblId=DT_1DA7E08S)
- 직업 대분류별 평균임금: 고용노동부 사업체노동력조사 + 통계청 임금근로일자리행정통계 2023~2024
- AI 노출도(0~10): 직업 특성 휴리스틱 평가 (디지털 업무 비중·물리/대인 의존도 기반)
"""

from __future__ import annotations

import csv
import json
import os
import re
import unicodedata
from collections import defaultdict

from data.categories import (
    KNOW_BIG,
    KNOW_MID,
    KNOW_MID_WEIGHT,
)

REF = "reference"
KEIS_JOBS_CSV = f"{REF}/keis_jobclass/직업세세분류.CSV"
KEIS_EDU_CSV = f"{REF}/keis_edu/교육훈련및학력,전공분포.CSV"
KEIS_OUTLOOK_CSV = f"{REF}/keis_edu/직업전망.CSV"
CAREER_SEQ_MAP = "data/keis_to_career_seq.json"

# career.go.kr 직업백과 매핑 (직업명 → seq 정수)
try:
    with open(CAREER_SEQ_MAP, encoding="utf-8") as _f:
        CAREER_SEQ: dict[str, int] = json.load(_f)
except FileNotFoundError:
    CAREER_SEQ = {}

# career.go.kr 직업백과 raw 데이터 (seq → {wage, work, views, ...})
CAREER_DETAIL: dict[int, dict] = {}
try:
    with open("data/career_raw.json", encoding="utf-8") as _f:
        for r in json.load(_f):
            CAREER_DETAIL[int(r["job_cd"])] = r
except FileNotFoundError:
    pass


def career_url(title: str) -> str:
    """매핑된 seq가 있으면 직업 상세 페이지, 없으면 직업백과 메인."""
    seq = CAREER_SEQ.get(title)
    if seq is not None:
        return f"https://www.career.go.kr/cloud/w/job/view?seq={seq}"
    # fallback: 직업백과 목록 페이지 (인기 직업 + 검색 폼이 있는 메인)
    return "https://www.career.go.kr/cloud/w/job/list"


def career_extra(title: str) -> dict:
    """매핑된 직업의 실제 임금·직무 설명·조회수 등."""
    seq = CAREER_SEQ.get(title)
    if seq is None:
        return {}
    d = CAREER_DETAIL.get(seq, {})
    out: dict = {}
    if d.get("wage"):
        try:
            out["pay_real"] = int(d["wage"].replace(",", ""))
        except ValueError:
            pass
    if d.get("work"):
        out["work"] = d["work"].strip()
    if d.get("views"):
        try:
            out["views"] = int(d["views"])
        except ValueError:
            pass
    if d.get("wage_level"):
        out["wage_level"] = d["wage_level"]
    return out


def load_jobs():
    """537개 KNOW 직업 마스터 로드."""
    with open(KEIS_JOBS_CSV, encoding="euc-kr") as f:
        rows = list(csv.DictReader(f))
    jobs = []
    for r in rows:
        big = r["KNOW직업대분류"]
        mid = r["KNOW직업중분류"]
        # 중분류 키 정규화: 30(보건), 70(건설), 90(농림어업)는 자릿수 0 채움
        mid_key = f"{big}{mid}"
        # 일부 카테고리(0,1,8 등)는 1자리 중분류 → 그대로 사용
        # 카테고리 매핑 사전에 맞춤
        if mid_key not in KNOW_MID:
            # 일부 데이터는 0이 빠진 형태 → 보정 시도
            alt = f"{big}0{mid}" if len(mid_key) == 2 else mid_key
            if alt in KNOW_MID:
                mid_key = alt
        jobs.append(
            {
                "big": big,
                "mid_key": mid_key,
                "mid_name": KNOW_MID.get(mid_key, "기타"),
                "code": f"{big}{mid}{r['KNOW직업소분류']}{r['KNOW직업세분류']}{r['KNOW직업세세분류']}",
                "title": r["KNOW직업명"].strip(),
            }
        )
    return jobs


def load_outlook_texts():
    """KEIS 직업전망 텍스트(직업명 매칭용)."""
    out = {}
    with open(KEIS_OUTLOOK_CSV, encoding="euc-kr") as f:
        for r in csv.DictReader(f):
            out[r["KNOW직업코드"]] = r["직업전망내용"]
    return out


# ── AI 노출도 휴리스틱 ──────────────────────────────────────────────────────

# 직업 대분류별 기본 AI 노출도 (디지털 업무 비중 기준)
BIG_BASE_EXPOSURE = {
    "0": 7.5,  # 경영·사무·금융 — 디지털 업무 다수
    "1": 8.0,  # 연구·공학기술 — IT 분야 매우 높음
    "2": 5.5,  # 교육·법률·사회복지·공안 — 대인접촉 일부
    "3": 4.0,  # 보건·의료 — 신체적 진료/치료
    "4": 6.5,  # 예술·디자인·방송·스포츠 — 디자인/방송 높음, 스포츠 낮음
    "5": 2.0,  # 미용·여행·음식·경비·돌봄 — 신체/대인 접촉
    "6": 3.5,  # 영업·판매·운전·운송 — 대면+물리
    "7": 1.5,  # 건설·채굴 — 거의 물리
    "8": 3.0,  # 설치·정비·생산 — 물리 작업 중심
    "9": 1.5,  # 농림어업 — 물리/현장
}

# 직업명 키워드 가산점 (+/-)
EXPOSURE_KEYWORDS = [
    # 매우 높음 (+2~+3)
    (r"(소프트웨어|개발자|프로그래머|데이터|알고리즘|인공지능|AI|머신러닝|빅데이터)", +2.5),
    (r"(웹 ?개발|앱 ?개발|시스템 ?엔지니어|시스템엔지니어|클라우드|DBA|네트워크 ?엔지니어)", +2.5),
    (r"(번역|통역|작가|카피라이터|편집자|기자|언론|콘텐츠 ?기획)", +2.0),
    (r"(애니메이터|일러스트|그래픽 ?디자이너|3D|UI|UX|영상편집|영상 ?편집)", +2.0),
    (r"(공인회계사|회계사$|세무사|보험계리사|애널리스트|증권|펀드매니저|투자분석)", +2.0),
    (r"(텔레마케터|상담원|콜센터|텔레마케팅|입력원|자료입력)", +3.0),
    (r"(번역사|교정사|교열|문서)", +2.5),
    # 높음 (+1)
    (r"(기획|관리|행정|사무|마케팅|광고|홍보|컨설턴트|연구원)", +1.0),
    (r"(변호사|법무사|판사|검사|법률)", +1.0),
    (r"(교사|교수|강사|학원)", +0.5),
    (r"(의사|약사|간호사|치과의사|한의사|수의사)", -0.5),
    # 낮음 (-1~-2)
    (r"(미용|네일|메이크업|피부관리|이용)", -1.5),
    (r"(요리|조리|제과제빵|제빵|바리스타|소믈리에|조주)", -1.0),
    (r"(운전|기관사|택시|버스|화물|배달|택배)", -0.5),
    (r"(경비|경호|보안|소방|구조)", -1.0),
    (r"(간병|돌봄|보육|보모|어린이집|유치원)", -1.5),
    (r"(농업|어업|임업|축산|양식|원예|화훼)", -1.0),
    (r"(건설|건축|토목|배관|설비|굴착|채굴)", -1.0),
    (r"(용접|단조|주조|판금|선반|밀링|용해)", -0.5),
    (r"(청소|환경미화|위생|세탁)", -1.5),
    (r"(스포츠|운동|체육|코치|트레이너|선수|심판)", -1.0),
    (r"(가수|배우|성우|연예인|개그맨|연기|모델|뮤지컬|무용)", -0.5),
    (r"(승무원|호텔|숙박|관광)", -0.5),
]


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\w가-힣A-Za-z0-9]+", "-", text)
    return text.strip("-").lower()[:80]


def calc_exposure(title: str, big: str) -> tuple[int, str]:
    base = BIG_BASE_EXPOSURE.get(big, 5.0)
    score = base
    matched = []
    for pat, delta in EXPOSURE_KEYWORDS:
        if re.search(pat, title):
            score += delta
            matched.append(pat)
    score = max(0, min(10, round(score)))

    rationale_parts = []
    if score >= 8:
        rationale_parts.append(
            "디지털·정보처리 중심 업무로 LLM·자동화에 의한 업무 재편이 빠르게 진행될 가능성이 큽니다."
        )
    elif score >= 6:
        rationale_parts.append(
            "문서·데이터·커뮤니케이션이 주요 업무로 AI 보조 도구가 생산성을 크게 끌어올릴 영역입니다."
        )
    elif score >= 4:
        rationale_parts.append("디지털 업무와 대면·현장 업무가 혼재되어 부분적으로 AI 보조가 가능합니다.")
    elif score >= 2:
        rationale_parts.append("주로 신체·대면 업무로 AI는 일부 행정·일정관리 업무 정도에 영향을 미칩니다.")
    else:
        rationale_parts.append("물리적 작업·현장 대응이 핵심이라 현재 AI의 직접적 영향은 제한적입니다.")
    if matched:
        rationale_parts.append(f"(대분류 기본 {base:.1f}점, 직업명 키워드 가중)")
    return score, " ".join(rationale_parts)


# ── 향후 전망 점수 (-10 ~ +20%) ────────────────────────────────────────────

OUTLOOK_KEYWORDS = [
    (r"(인공지능|AI|머신러닝|반도체|2차전지|배터리|바이오|로봇|클라우드|보안 ?엔지니어|데이터)", +12),
    (r"(소프트웨어|앱 ?개발|웹 ?개발|콘텐츠 ?기획|UI|UX)", +10),
    (r"(간병|돌봄|요양|간호|보건|의료|재활|상담|심리|사회복지)", +8),
    (r"(에너지|친환경|환경|기후|풍력|태양광|수소)", +8),
    (r"(트레이너|코치|영양사|반려동물|애견)", +6),
    (r"(번역|통역|기자|편집|아나운서|성우|언어)", -4),
    (r"(텔레마케터|입력원|자료입력|타자|속기)", -10),
    (r"(은행원|보험설계사|텔러|증권 ?사무)", -6),
    (r"(인쇄|제본|단순|단순노무|판매원|매장|점원)", -4),
    (r"(농업|어업|임업|광부|채굴)", -6),
    (r"(섬유|봉제|제직|방적|염색)", -8),
]

OUTLOOK_DESC = [
    (-10, "감소"),
    (-2, "다소 감소"),
    (3, "현 수준 유지"),
    (8, "다소 증가"),
    (15, "증가"),
    (100, "크게 증가"),
]


def calc_outlook(title: str, big: str) -> tuple[int, str]:
    # 대분류 기본 outlook
    base_by_big = {
        "0": 4,
        "1": 8,
        "2": 5,
        "3": 9,
        "4": 4,
        "5": 6,
        "6": 1,
        "7": 1,
        "8": 0,
        "9": -3,
    }
    score = base_by_big.get(big, 3)
    for pat, delta in OUTLOOK_KEYWORDS:
        if re.search(pat, title):
            score += delta
    score = max(-15, min(25, score))
    desc = next(d for thr, d in OUTLOOK_DESC if score <= thr)
    return score, desc


# ── 학력 추정 ──────────────────────────────────────────────────────────────

EDU_LEVELS = ["고졸 이하", "전문대졸", "대졸", "석사", "박사"]

EDU_KEYWORDS = [
    # 단어 끝(\b는 한글에서 안먹히므로 명시적 매칭 활용; "사무원"은 사무직으로 우선 처리)
    (r"사무원|사무 ?보조|비서|속기사|행정사|취업알선원", "대졸"),
    (r"교수|총장|학장|박사", "박사"),
    (r"연구원|연구·개발자|연구개발자|개발 ?연구원", "석사"),
    (
        r"전문의|내과의사|외과의사|성형외과의사|산부인과의사|이비인후과의사|안과의사|정신과의사|소아과의사|방사선과의사|마취병리과의사|비뇨기과의사|피부과의사|가정의학과의사|일반의사",
        "석사",
    ),
    (r"한의사|치과의사|수의사|약사|한약사", "석사"),
    (r"변호사|법무사|판사|검사|변리사|관세사|회계사$|공인회계사|감정평가사|보험계리사|노무사", "석사"),
    (r"개발자|엔지니어|프로그래머|데이터 ?사이언티스트|애널리스트|컨설턴트|건축사|기획자|관리자|디렉터", "대졸"),
    (r"교사|강사|디자이너|기자|아나운서|상담사|상담전문가|사회복지사|상담교사", "대졸"),
    (r"간호사|간호조무사|물리치료사|작업치료사|영양사|치과위생사|치과기공사|임상병리사|방사선사", "전문대졸"),
    (r"미용|네일|이용사|요리|조리|제빵|바리스타|용접|배관|건설|운전|기관사|기능공|점원|판매원|미장공", "고졸 이하"),
    (r"농업|어업|임업|청소|경비|돌봄|간병|보육|보안|환경미화|단순|배달|택배", "고졸 이하"),
]


def estimate_education(title: str, big: str) -> str:
    # 직업명 키워드 우선
    for pat, edu in EDU_KEYWORDS:
        if re.search(pat, title):
            return edu
    # 대분류 기본
    big_default = {
        "0": "대졸",
        "1": "대졸",
        "2": "대졸",
        "3": "전문대졸",
        "4": "대졸",
        "5": "고졸 이하",
        "6": "고졸 이하",
        "7": "고졸 이하",
        "8": "고졸 이하",
        "9": "고졸 이하",
    }
    return big_default.get(big, "고졸 이하")


# ── 임금 / 취업자수 분배 ──────────────────────────────────────────────────


# KOSIS 경제활동인구조사 2024 평균 + KSCO→KNOW 매핑 후 추정
# 합계 약 2,720만명 (한국 총 취업자 ≈ 2,857만명, 학생/주부 등 분류불명 제외)
KNOW_BIG_TOTAL_MAN = {
    "0": 600,  # 경영·사무·금융 (관리자 41 + 사무 502 + 금융전문가 약 60)
    "1": 220,  # 연구·공학기술 (전문가 중 IT/공학/연구)
    "2": 260,  # 교육·법률·사회복지·공안 + 군인
    "3": 145,  # 보건·의료
    "4": 70,  # 예술·디자인·방송·스포츠
    "5": 340,  # 서비스 (음식·미용·돌봄·경비·청소)
    "6": 400,  # 영업·판매·운전·운송
    "7": 150,  # 건설·채굴
    "8": 400,  # 설치·정비·생산
    "9": 130,  # 농림어업
}


def big_total_employment(big: str) -> int:
    """KNOW 대분류별 한국 총 취업자수 (명 단위)."""
    return KNOW_BIG_TOTAL_MAN[big] * 10000


def big_avg_pay(big: str) -> int:
    """KNOW 대분류별 평균 연봉 (만원). KSCO 기반 가중 평균."""
    pay_by_big = {
        "0": 6300,  # 관리자 + 사무 평균
        "1": 6000,  # 전문가(공학) — 경력 5년 기준
        "2": 4800,  # 교육·사회복지 평균
        "3": 6500,  # 보건의료 평균 (의사 영향)
        "4": 4200,  # 예술 — 비정기성 반영
        "5": 2700,  # 서비스종사자
        "6": 3300,  # 판매·운전·운송
        "7": 4000,  # 건설·채굴
        "8": 3900,  # 설치·정비·생산
        "9": 2700,  # 농림어업
    }
    return pay_by_big[big]


# 일부 직업명 키워드별 임금 가중치 (× 배수)
# "회계사"는 단독으로 매치되도록 \b 대신 명시적 양극 처리 (회계사무원과 구분)
PAY_MULTIPLIERS = [
    (r"기업고위임원|CEO|대표이사|총장|학장", 2.5),
    (r"고위공무원|행정부고위공무원|입법공무원|차관|장관", 2.0),
    (r"판사|검사", 2.0),
    (r"변호사|변리사|관세사|법무사|공인회계사|회계사$|세무사|감정평가사|보험계리사|노무사", 1.6),
    (
        r"전문의|내과의사|외과의사|성형외과의사|산부인과의사|이비인후과의사|안과의사|정신과의사|소아과의사|방사선과의사|마취병리과의사|비뇨기과의사|피부과의사|가정의학과의사",
        2.0,
    ),
    (r"일반의사|한의사|치과의사|수의사|약사|한약사", 1.8),
    (r"항공기조종사|선장|선박기관사", 1.8),
    (r"소프트웨어개발자|AI|머신러닝|빅데이터|반도체|클라우드|보안엔지니어", 1.5),
    (r"교수|연구원|연구·개발자|애널리스트|컨설턴트|개발자|엔지니어", 1.3),
    (r"중·고등학교교사|초등학교교사|간호사$|간호조무사|디자이너|기자|건축사", 1.0),
    (r"^보조원$|보조원$|점원|단순|아르바이트|미화|환경미화|배달원|음식관련단순", 0.65),
    (r"인턴|훈련생|연수생", 0.55),
]


def adjust_pay(title: str, base: int) -> int:
    factor = 1.0
    for pat, mul in PAY_MULTIPLIERS:
        if re.search(pat, title):
            factor *= mul
            break
    return int(base * factor)


# 직업명 가중치(취업자수 분배용)
# 실제 한국 직업명에 substring 매치되는 형태로 정의 (KEIS KNOW 537개 직업명 기준)
# 한국 노동시장 실제 직업별 종사자 분포 반영 (KOSIS·고용행정통계 참고)
JOBS_KEYWORDS = [
    # 매우 큼 (수십~수백만 명)
    (r"상점판매원", 14.0),  # 약 200만 (한국 최대 직업)
    (r"한식조리사", 5.0),
    (r"경리사무원|회계사무원", 6.0),
    (r"총무사무원|일반사무원", 5.0),
    (r"공공행정사무원|기획사무원", 4.0),
    (r"간호사$", 4.0),
    (r"간호조무사", 4.5),
    (r"초등학교교사|중·고등학교교사", 4.0),
    (r"보육교사", 4.0),
    (r"택시운전원|버스운전원|화물차·특수차운전원", 4.0),
    (r"택배원|배달원", 1.5),
    (r"경비원", 4.0),
    (r"청소원|환경미화원", 4.0),
    (r"작물재배종사자|농업종사자|곡식작물재배자|채소", 4.0),
    (r"건설단순종사자|건설노무자|건설및광업단순종사자", 3.5),
    (r"식당서비스원|주방보조원|음식관련단순종사원", 2.5),
    (r"음식배달원", 1.0),
    (r"요양보호사|간병인|돌봄종사자", 3.5),
    (r"미용사", 3.0),
    # 큼
    (r"방문판매원|온라인판매원|통신기기·서비스판매원", 1.8),
    (r"노점 및 이동판매원", 1.5),
    (r"소규모판매점장", 1.5),
    (r"보험설계사|투자전문가|금융영업원", 1.5),
    (r"자동차영업원|기술영업원|해외영업원|제품광고영업원", 1.5),
    (r"사회복지사|직업상담사|상담전문가|심리상담사", 2.0),
    (r"응용소프트웨어개발자|시스템소프트웨어개발자|웹개발자|모바일앱개발자", 1.8),
    (r"중식조리사|양식조리사|일식조리사|음료조리사", 1.5),
    (r"제과·제빵사|바리스타|패스트푸드준비원|주방장 및 조리사|음식관리원", 1.5),
    (r"제조단순종사원|포장원|조립원|조립종사원|단순노무", 2.5),
    (r"이용사|피부관리사|네일아티스트|메이크업아티스트", 1.5),
    (r"경찰관|소방관|일반군인|부사관|장교", 1.5),
    (r"우편집배원|우편물집배원|우편물접수사무원", 1.0),
    (r"보안 및 경호 관리원|시설·특수경비원", 1.5),
    (r"산업안전 및 위험관리원", 0.8),
    # 중간 (1.0 = 평균)
    (r"인사·교육·훈련사무원|총무사무원|마케팅사무원", 1.5),
    (r"비서|사무 ?보조원|문서 ?작성원", 1.0),
    (r"건축사|건축구조기술자|토목 ?기술자", 0.8),
    (r"기관사|선박|항해사|항공기 ?조종사", 0.3),
    (r"양식원|어부|어업종사자|임업종사자|산림", 0.8),
    # 작음 (0.3~0.7)
    (r"임원|CEO|대표|총장|학장|이사 ?장|관리자|원장 및 원감|교장 및 교감", 0.15),
    (r"고위공무원|행정부고위공무원|입법공무원", 0.1),
    (r"판사|검사", 0.2),
    (r"변호사|법무사|변리사|관세사|세무사|회계사|감정평가사|노무사", 0.5),
    (
        r"전문의|내과의사|외과의사|성형외과의사|산부인과의사|이비인후과의사|안과의사|정신과의사|소아과의사|방사선과의사|마취병리과의사|비뇨기과의사|피부과의사|가정의학과의사",
        0.4,
    ),
    (r"일반의사|한의사|치과의사|수의사|약사|한약사", 0.7),
    (r"교수|대학교수|시간강사|학원강사", 0.6),
    (r"연구원|연구·개발자|연구개발자", 0.5),
    (r"애널리스트|컨설턴트|회계감사|평가사", 0.6),
    (r"보조원|아르바이트|훈련생|인턴|실습생", 0.4),
    (r"특수교육교사|보건교사|영양교사|사서|상담교사", 0.6),
    (r"번역가|통역가|성우|아나운서|기자|작가|시인|소설가|영화시나리오작가|방송작가|시나리오", 0.3),
    (r"가수|배우|모델|개그맨|성악가|무용가|국악인|지휘자|작곡가|연주가|만화가|화가|조각가|사진작가", 0.3),
    (r"항공기조종사|선장|선박기관사|해기사|기관사", 0.2),
    (r"문화재|학예사|기록물|큐레이터", 0.3),
    (r"건축감리|건축구조기술자|토목구조 ?설계", 0.5),
    (r"풍력발전|태양광발전|원자력|핵공학|우주공학", 0.3),
    (r"디자이너", 0.7),  # 디자이너 너무 광범위 → 일반 약화
]


def job_weight(title: str) -> float:
    w = 1.0
    for pat, mul in JOBS_KEYWORDS:
        if re.search(pat, title):
            w *= mul
    return w


# ── 메인 빌드 ──────────────────────────────────────────────────────────────


def main():
    jobs = load_jobs()
    print(f"Loaded {len(jobs)} jobs")

    # 1) 직업별 취업자수 분배: 대분류 총량 → 카테고리 가중치 × 직업 키워드 가중치
    by_big = defaultdict(list)
    for j in jobs:
        by_big[j["big"]].append(j)

    job_records = []
    for big, big_jobs in by_big.items():
        total = big_total_employment(big)
        # 카테고리 가중치 계산
        weights = []
        for j in big_jobs:
            cw = KNOW_MID_WEIGHT.get(j["mid_key"], 1.0)
            jw = job_weight(j["title"])
            weights.append(cw * jw)
        wsum = sum(weights)
        for j, w in zip(big_jobs, weights, strict=False):
            jobs_count = int(round(total * w / wsum))
            base_pay = big_avg_pay(big)
            pay_estimated = adjust_pay(j["title"], base_pay)
            outlook, outlook_desc = calc_outlook(j["title"], big)
            education = estimate_education(j["title"], big)
            exposure, rationale = calc_exposure(j["title"], big)

            # career.go.kr 실제 임금이 있으면 우선 사용 (정확도 ★)
            extra = career_extra(j["title"])
            if "pay_real" in extra:
                pay = extra["pay_real"]
                pay_source = "career.go.kr"
            else:
                pay = pay_estimated
                pay_source = "추정"

            job_records.append(
                {
                    "title": j["title"],
                    "slug": slugify(j["title"]) or j["code"],
                    "category": j["mid_name"],
                    "big_category": KNOW_BIG[big],
                    "code": j["code"],
                    "pay": pay,
                    "pay_source": pay_source,
                    "work": extra.get("work"),
                    "views": extra.get("views"),
                    "jobs": jobs_count,
                    "outlook": outlook,
                    "outlook_desc": outlook_desc,
                    "education": education,
                    "exposure": exposure,
                    "exposure_rationale": rationale,
                    "url": career_url(j["title"]),
                    "career_seq": CAREER_SEQ.get(j["title"]),
                }
            )

    # 정렬: 대분류 → 중분류 → 취업자 내림차순
    job_records.sort(key=lambda r: (r["category"], -r["jobs"]))

    os.makedirs("site", exist_ok=True)
    with open("site/data.json", "w", encoding="utf-8") as f:
        json.dump(job_records, f, ensure_ascii=False, indent=None)

    total_jobs = sum(r["jobs"] for r in job_records)
    avg_pay = sum(r["pay"] * r["jobs"] for r in job_records) / total_jobs
    avg_exposure = sum(r["exposure"] * r["jobs"] for r in job_records) / total_jobs

    seq_matched = sum(1 for r in job_records if r.get("career_seq"))
    print(f"Wrote {len(job_records)} jobs to site/data.json")
    print(f"Total jobs: {total_jobs:,} ({total_jobs / 1e4:,.0f}만명)")
    print(f"Job-weighted avg annual pay: {avg_pay:,.0f}만원")
    print(f"Job-weighted avg AI exposure: {avg_exposure:.2f}/10")
    print(
        f"career.go.kr 직업백과 직접 매핑: {seq_matched}/{len(job_records)} "
        f"({seq_matched / len(job_records) * 100:.1f}%) — 나머지는 검색 페이지 fallback"
    )

    # 카테고리 통계
    cat_jobs = defaultdict(int)
    for r in job_records:
        cat_jobs[r["category"]] += r["jobs"]
    print("\nJobs by category (top 10):")
    for cat, j in sorted(cat_jobs.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cat}: {j / 1e4:.0f}만명")


if __name__ == "__main__":
    main()
