"""
Felten et al. 2021 AIOE → KEIS 한국 직업명 매핑.

전략:
1. Felten 774개 직업: SOC Code + Occupation Title (영문) + AIOE 점수 (0~5)
2. 한·영 키워드 사전으로 KEIS 한글 직업명을 영문 토큰 셋으로 변환
3. Felten 영문 직업명에 토큰 매칭 → 가장 강한 매칭의 AIOE 점수 적용
4. 점수 정규화: AIOE의 분포(0~5)를 0~10 척도로 선형 변환

데이터:
- Felten: reference/aioe_data.xlsx (Appendix A)
- KEIS: reference/keis_jobclass/직업세세분류.CSV
- 출력: data/felten_mapping.json — {직업명: {aioe_raw, aioe_score10, soc, en_match}}
"""

from __future__ import annotations

import csv
import json
import re

import openpyxl

KEIS_CSV = "reference/keis_jobclass/직업세세분류.CSV"
FELTEN_XLSX = "reference/aioe_data.xlsx"
OUT = "data/felten_mapping.json"

# 한 → 영 키워드 사전 (KEIS 직업명 토큰을 Felten 영문 직업명 매칭에 사용)
KO_EN: dict[str, list[str]] = {
    # 관리자
    "관리자": ["manager", "manager", "executive"],
    "임원": ["executive", "officer"],
    "총장": ["president"],
    "학장": ["dean"],
    "원장": ["president", "principal"],
    "교장": ["principal"],
    "교감": ["principal"],
    "공무원": ["public", "government"],
    # 사무
    "사무원": ["clerk", "specialist", "officer"],
    "행정": ["administrative", "administration"],
    "경영": ["management", "business"],
    "기획": ["planner", "planning"],
    "회계": ["accountant", "accounting"],
    "경리": ["bookkeeping", "accounting clerk"],
    "감사": ["auditor"],
    "총무": ["general affairs", "administrative"],
    "인사": ["human resources", "personnel"],
    "마케팅": ["marketing"],
    "광고": ["advertising"],
    "홍보": ["public relations"],
    # 금융
    "은행": ["bank", "teller"],
    "텔러": ["teller"],
    "보험": ["insurance"],
    "증권": ["securities", "stock"],
    "투자": ["investment"],
    "재무": ["finance", "financial"],
    # 영업
    "영업": ["sales"],
    "판매": ["sales", "retail"],
    "상점": ["retail"],
    # 연구·공학
    "연구원": ["scientist", "researcher"],
    "엔지니어": ["engineer"],
    "기술자": ["technician", "engineer"],
    "개발자": ["developer", "programmer"],
    "프로그래머": ["programmer"],
    "소프트웨어": ["software"],
    "시스템": ["systems"],
    "데이터": ["data"],
    "보안": ["security", "information security"],
    "네트워크": ["network"],
    "통신": ["telecommunications", "communications"],
    "전기": ["electrical"],
    "전자": ["electronics"],
    "기계": ["mechanical"],
    "화학": ["chemical"],
    "건축": ["architect", "architectural"],
    "토목": ["civil"],
    "건설": ["construction"],
    "도시계획": ["urban planner"],
    "물리": ["physicist"],
    "수학": ["mathematician", "statistician"],
    "통계": ["statistician"],
    "생물": ["biologist", "biological"],
    "지질": ["geologist"],
    # 교육
    "교사": ["teacher"],
    "교수": ["professor"],
    "강사": ["instructor"],
    "유치원": ["preschool", "kindergarten"],
    "초등학교": ["elementary", "primary"],
    "중·고등학교": ["secondary"],
    "중등": ["secondary"],
    "특수교육": ["special education"],
    "보육": ["childcare"],
    # 법률
    "변호사": ["lawyer"],
    "판사": ["judge"],
    "검사": ["prosecutor"],
    "법무사": ["paralegal", "legal"],
    "변리사": ["patent"],
    "관세사": ["customs"],
    "세무사": ["tax preparer"],
    "감정평가사": ["appraiser"],
    "노무사": ["labor relations"],
    # 사회복지
    "사회복지사": ["social worker"],
    "상담사": ["counselor"],
    "상담전문가": ["counselor", "therapist"],
    # 보건의료
    "의사": ["physician", "doctor"],
    "전문의": ["physician"],
    "내과": ["internal medicine"],
    "외과": ["surgeon"],
    "치과의사": ["dentist"],
    "한의사": ["acupuncturist"],  # 정확 매칭 어려움
    "수의사": ["veterinarian"],
    "약사": ["pharmacist"],
    "간호사": ["nurse"],
    "간호조무사": ["nursing aide", "nursing assistant"],
    "물리치료사": ["physical therapist"],
    "작업치료사": ["occupational therapist"],
    "임상병리사": ["medical laboratory"],
    "방사선사": ["radiologic technologist"],
    "치과위생사": ["dental hygienist"],
    "치과기공사": ["dental laboratory"],
    "영양사": ["dietitian", "nutritionist"],
    "응급구조사": ["emergency medical", "paramedic"],
    "임상심리사": ["clinical psychologist"],
    # 예술·디자인
    "디자이너": ["designer"],
    "그래픽디자이너": ["graphic designer"],
    "패션디자이너": ["fashion designer"],
    "산업디자이너": ["industrial designer"],
    "건축가": ["architect"],
    "사진작가": ["photographer"],
    "영상편집": ["film and video editor"],
    "방송": ["broadcast"],
    "기자": ["news", "reporter", "journalist"],
    "아나운서": ["broadcaster", "news"],
    "성우": ["voice"],
    "작가": ["writer"],
    "번역가": ["translator", "interpreter"],
    "통역가": ["interpreter"],
    "편집자": ["editor"],
    "사서": ["librarian"],
    "큐레이터": ["curator"],
    "학예사": ["curator"],
    "지휘자": ["conductor"],
    "연주가": ["musician"],
    "가수": ["singer"],
    "배우": ["actor"],
    "무용가": ["dancer"],
    "안무가": ["choreographer"],
    "화가": ["painter", "artist"],
    "조각가": ["sculptor"],
    "작곡가": ["composer"],
    "만화가": ["cartoonist"],
    "애니메이터": ["animator"],
    # 스포츠
    "운동선수": ["athlete"],
    "코치": ["coach"],
    "트레이너": ["trainer"],
    "심판": ["umpire", "referee"],
    # 미용
    "미용사": ["hairdresser", "barber"],
    "이용사": ["barber"],
    "메이크업": ["makeup"],
    "피부관리사": ["skincare"],
    # 음식
    "조리사": ["cook", "chef"],
    "주방장": ["chef"],
    "제빵사": ["baker"],
    "바리스타": ["barista"],
    "바텐더": ["bartender"],
    # 여행·숙박
    "승무원": ["flight attendant"],
    "호텔": ["hotel"],
    # 운전
    "운전기사": ["driver"],
    "운전원": ["driver"],
    "택시": ["taxi"],
    "버스": ["bus"],
    "트럭": ["truck"],
    "기관사": ["locomotive engineer"],
    "조종사": ["pilot"],
    "선장": ["captain"],
    "항해사": ["mate"],
    # 농림어업
    "농업": ["farmer"],
    "어업": ["fishing"],
    "임업": ["logger", "forestry"],
    "축산": ["livestock"],
    "양식": ["aquaculture"],
    # 군경소방
    "경찰관": ["police"],
    "소방관": ["firefighter"],
    "교도": ["correctional officer"],
    "군인": ["military"],
    # 단순노무
    "청소원": ["janitor", "cleaner"],
    "환경미화원": ["sanitation", "cleaner"],
    "경비원": ["security guard"],
    "택배원": ["package", "courier"],
    "배달원": ["delivery"],
    "보육교사": ["preschool", "childcare worker"],
    "요양보호사": ["personal care", "nursing aide"],
    "간병인": ["personal care"],
    # 건설 기능공
    "목공": ["carpenter"],
    "석공": ["stone", "mason"],
    "철골공": ["structural iron", "steel"],
    "미장원": ["plasterer"],
    "도배원": ["paperhanger"],
    "도장원": ["painter"],
    "방수원": ["roofer"],
    "배관원": ["plumber"],
    "용접": ["welder"],
    "전기기사": ["electrician"],
    # 정비·생산
    "기계공": ["machinist"],
    "정비원": ["mechanic", "repairer"],
    "조립원": ["assembler"],
    "포장원": ["packer"],
    "검사원": ["inspector"],
    # 텔레마케터·고객
    "텔레마케터": ["telemarketer"],
    "콜센터": ["customer service"],
    "고객": ["customer service"],
    # 우편
    "우편": ["postal"],
    "우체국": ["postal"],
    # 자료입력
    "자료입력": ["data entry"],
}


def normalize(s: str) -> str:
    return re.sub(r"[ \t·・、。\.\/\(\)·ㆍ_\-]+", "", s).lower()


def keis_to_en_tokens(keis_name: str) -> list[str]:
    """KEIS 한글 직업명 → 영문 토큰 리스트 (사전 기반)."""
    tokens: list[str] = []
    for ko, ens in KO_EN.items():
        if ko in keis_name:
            tokens.extend(ens)
    return tokens


def main():
    # 1) Felten 데이터 로드
    wb = openpyxl.load_workbook(FELTEN_XLSX, data_only=True)
    ws = wb["Appendix A"]
    felten = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        soc, title, aioe = row[0], row[1], row[2]
        if not soc or aioe is None:
            continue
        felten.append(
            {
                "soc": soc,
                "title": title.strip(),
                "title_lc": title.strip().lower(),
                "aioe": float(aioe),
            }
        )
    print(f"Felten 직업: {len(felten)}")

    # AIOE 분포 확인 → 0~10 정규화 기준
    aioes = [f["aioe"] for f in felten]
    aioe_min, aioe_max = min(aioes), max(aioes)
    aioe_p10 = sorted(aioes)[int(len(aioes) * 0.10)]
    aioe_p90 = sorted(aioes)[int(len(aioes) * 0.90)]
    print(f"AIOE 분포: min={aioe_min:.2f} p10={aioe_p10:.2f} p90={aioe_p90:.2f} max={aioe_max:.2f}")

    # 0~10 정규화: p10 → 1, p90 → 9 (양 극단 4단계로 보전)
    def to_score10(aioe: float) -> int:
        # 선형 매핑: p10=1, p90=9, clamp 0~10
        if aioe_p90 == aioe_p10:
            return 5
        v = 1 + (aioe - aioe_p10) / (aioe_p90 - aioe_p10) * 8
        return max(0, min(10, round(v)))

    # 2) KEIS 직업 로드
    with open(KEIS_CSV, encoding="euc-kr") as f:
        keis_jobs = [r["KNOW직업명"].strip() for r in csv.DictReader(f)]
    print(f"KEIS 직업: {len(keis_jobs)}")

    # 3) 매칭
    mapping: dict[str, dict] = {}
    for keis_name in keis_jobs:
        en_tokens = keis_to_en_tokens(keis_name)
        if not en_tokens:
            continue
        # Felten 직업명 중 가장 많은 영문 토큰을 포함하는 항목 찾기
        best = None
        best_score = 0
        for f in felten:
            ft = f["title_lc"]
            score = 0
            for tok in en_tokens:
                if tok.lower() in ft:
                    score += 1
            if score > best_score:
                best_score = score
                best = f
        if best and best_score >= 1:
            mapping[keis_name] = {
                "soc": best["soc"],
                "en_title": best["title"],
                "aioe_raw": round(best["aioe"], 3),
                "aioe_score10": to_score10(best["aioe"]),
                "tokens_matched": best_score,
            }

    print(f"매핑: {len(mapping)}/{len(keis_jobs)} ({len(mapping) / len(keis_jobs) * 100:.1f}%)")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"Wrote to {OUT}")

    # 핵심 직업 검증
    print("\n=== 핵심 직업 매핑 검증 ===")
    samples = [
        "회계사",
        "간호사",
        "응용소프트웨어개발자",
        "한식조리사",
        "상점판매원",
        "내과의사",
        "변호사",
        "초등학교교사",
        "텔레마케터",
        "건축가(건축설계사)",
        "미용사",
        "택시운전원",
        "경찰관",
        "농업종사자",
    ]
    for s in samples:
        if s in mapping:
            m = mapping[s]
            print(f"  ✓ {s:<25} → {m['en_title']:<35} AIOE={m['aioe_raw']} → {m['aioe_score10']}/10")
        else:
            print(f"  ✗ {s:<25} → 미매핑")


if __name__ == "__main__":
    main()
