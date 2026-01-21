import streamlit as st
import pandas as pd
import datetime
import os
import re

# --- 페이지 설정 ---
# 브라우저 탭 제목에도 이름을 넣었습니다.
st.set_page_config(page_title="2026 친환경차 현황 by 김희주", page_icon="⚡", layout="wide")

# --- 스타일 설정 ---
st.markdown("""
    <style>
    /* 결과 박스 스타일 */
    .result-container {
        background-color: var(--secondary-background-color);
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    /* 반응형 레이아웃 (줄바꿈 허용) */
    .car-info-line {
        display: flex;
        flex-wrap: wrap;            
        align-items: center;        
        gap: 8px 15px;              
        font-size: 15px;
        padding: 8px 0;
        border-bottom: 1px dashed rgba(128, 128, 128, 0.3);
        line-height: 1.6;
    }

    .car-info-line:last-child {
        border-bottom: none;
    }

    .info-item {
        white-space: nowrap;        
        display: inline-flex;
        align-items: center;
    }

    /* 항목 제목 (볼드 제거) */
    .label {
        font-weight: normal; 
        color: var(--primary-color);
        margin-right: 4px;
        font-size: 0.9em;
    }

    /* ★ 모델명만 유일하게 볼드 처리 */
    .model-name {
        font-weight: bold;    
        color: var(--text-color);
        font-size: 1.05em;
        margin-right: 5px;
    }

    /* 연비/주행거리 강조 (색상만, 볼드 X) */
    .highlight {
        background-color: rgba(255, 255, 0, 0.2);
        color: #ff4b4b;
        font-weight: normal;
        padding: 1px 4px;
        border-radius: 3px;
    }
    
    /* 일반 값 */
    .value-text {
        color: var(--text-color);
        font-weight: normal;
    }

    /* 판정 결과 배지 스타일 */
    .grade-badge-fail {
        background-color: #ffebee;
        color: #c62828;
        border: 1px solid #c62828;
        font-size: 0.85em;
        padding: 2px 6px;
        border-radius: 12px;
        font-weight: bold;
    }
    .grade-badge-pass {
        background-color: #e8f5e9;
        color: #2e7d32;
        border: 1px solid #2e7d32;
        font-size: 0.85em;
        padding: 2px 6px;
        border-radius: 12px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 메인 타이틀 (서명 포함) ---
st.markdown("### 2026 친환경차(전기차) 등재 현황 by 김희주")

# --- 기준표 ---
with st.expander("ℹ️ [기준] 2026년 전기차 에너지 소비효율 기준", expanded=False):
    ref_data = {
        "구분": ["초소·경·소형", "중형", "대형"],
        "기준 (km/kWh)": ["5.0 이상", "4.2 이상", "3.4 이상"]
    }
    st.table(pd.DataFrame(ref_data).set_index("구분"))

st.divider()

# --- 헬퍼 함수 ---
def format_value(val):
    if isinstance(val, float): return f"{val:.1f}"
    if isinstance(val, datetime.datetime): return val.strftime("%Y-%m-%d")
    return val

def shorten_header(header):
    if "에너지소비효율" in header: return "효율"
    if "1회충전주행거리" in header: return "주행"
    if "정격전압" in header: return "배터리"
    if "타이어" in header: return "타이어"
    if "구동방식" in header: return "구동"
    if "적용일자" in header: return "적용일"
    return header

# 등급 판정 로직 (역추적 방식)
def analyze_grade(efficiency_val, is_excluded):
    try:
        eff = float(efficiency_val)
    except:
        return "" 

    if is_excluded:
        if eff < 3.4:
            return "<span class='grade-badge-fail'>대형(3.4) 미달</span>"
        elif 3.4 <= eff < 4.2:
            return "<span class='grade-badge-fail'>중형(4.2) 미달</span>"
        elif 4.2 <= eff < 5.0:
            return "<span class='grade-badge-fail'>소형(5.0) 미달</span>"
        else:
            return "<span class='grade-badge-fail'>기준 미달</span>"
    else:
        if eff >= 5.0:
            return "<span class='grade-badge-pass'>소형(5.0) 충족</span>"
        elif eff >= 4.2:
            return "<span class='grade-badge-pass'>중형(4.2) 충족</span>"
        elif eff >= 3.4:
            return "<span class='grade-badge-pass'>대형(3.4) 충족</span>"
        else:
            return "<span class='grade-badge-pass'>기준 충족</span>"

# 모델명 통합 로직
def get_core_model_name(original_name, brand):
    if not isinstance(original_name, str): return str(original_name)
    name = original_name.upper()
    name = re.sub(r'\(.*?\)', '', name)
    for g in ["THE NEW", "ALL NEW", "FACELIFT", "MERCEDES-BENZ", "MERCEDES", "BENZ"]:
        name = name.replace(g, "")
    name = name.strip()

    # 벤츠: EQ+알파벳 (EQB, EQE 등) 추출
    if brand == "메르세데스벤츠":
        match = re.search(r'(EQ[A-Z])', name)
        if match: return match.group(1)
        return name.split()[0] if name else original_name

    # 현대/기아: EV시리즈, 아이오닉, GV시리즈
    if brand in ["기아", "현대자동차", "제네시스"]:
        if "EV" in name:
             match = re.search(r'(EV\s?\d+)', name)
             if match: return match.group(1).replace(" ", "")
        if "IONIQ" in name or "아이오닉" in name:
             match = re.search(r'(IONIQ\s?\d+|아이오닉\s?\d+)', name)
             if match: return "아이오닉" + re.sub(r'[^0-9]', '', match.group(1))
        match_g = re.search(r'(GV\d+|G\d+)', name)
        if match_g: return match_g.group(1)
        for k in ["KONA", "코나", "NIRO", "니로", "RAY", "레이", "CASPER", "캐스퍼"]:
             if k in name: return k

    # BMW: i로 시작하는 첫 단어
    if brand == "BMW":
        first = name.split()[0]
        if first.startswith("I"): return first
        
    # 아우디
    if brand in ["Audi", "아우디"]:
        if "Q4" in name: return "Q4 e-tron"
        if "Q8" in name: return "Q8 e-tron"
        if name.startswith("E-TRON"): return "e-tron"

    # 테슬라
    if brand == "테슬라" and "MODEL" in name:
        parts = name.split()
        try:
            idx = parts.index("MODEL")
            if idx + 1 < len(parts): return f"MODEL {parts[idx+1]}"
        except: pass

    # 폴스타
    if brand == "폴스타" and "POLESTAR" in name:
        parts = name.split()
        try:
             idx = parts.index("POLESTAR")
             if idx+1 < len(parts): return f"POLESTAR {parts[idx+1]}"
        except: pass

    # 폭스바겐
    if brand == "폭스바겐" and "ID." in name: return name.split()[0]

    # 공통: 수식어 제거
    remove_suffixes = ["LONG RANGE", "LONGRANGE", "STANDARD", "PERFORMANCE", "2WD", "4WD", "AWD", "RWD", "FWD", "GT-LINE", "GT", "PRO", "PRIME"]
    for w in remove_suffixes: name = name.replace(w, "")
    
    clean = name.strip()
    return clean.split()[0] if clean else original_name

# --- 데이터 로드 ---
@st.cache_data
def load_data():
    target_name = "2026환경친화적 자동차 등재 목록.xlsx"
    sheet_name = "별표 5의 제2호(전기자동차)"
    current_files = os.listdir('.')
    file_to_load = target_name if target_name in current_files else ([f for f in current_files if f.endswith('.xlsx')] + [None])[0]
            
    if file_to_load:
        try: return pd.read_excel(file_to_load, sheet_name=sheet_name)
        except: return None
    return None

df = load_data()

# --- 메인 로직 ---
if df is None:
    st.error("❌ 엑셀 파일을 찾을 수 없습니다.")
else:
    preferred_order = ["현대자동차", "기아", "한국GM", "르노코리아", "케이지모빌리티", "BMW", "메르세데스벤츠", "Audi", "폭스바겐", "볼보", "테슬라", "폴스타", "포르쉐코리아", "BYD", "Lexus"]
    existing_brands = df.iloc[:, 0].dropna().astype(str).unique().tolist()
    sorted_brands = [b for b in preferred_order if b in existing_brands] + [b for b in existing_brands if b not in preferred_order]

    col1, col2 = st.columns(2)
    with col1:
        selected_brand = st.selectbox("1. 업체명 선택", ["선택하세요"] + sorted_brands)
    
    display_models = []
    if selected_brand != "선택하세요":
        brand_df = df[df.iloc[:, 0] == selected_brand]
        filtered_models = set()
        for idx, row in brand_df.iterrows():
            orig_name = str(row.iloc[1])
            # 상용차 제외
            if selected_brand == "현대자동차" and ("포터" in orig_name or "ST1" in orig_name): continue
            if selected_brand == "기아" and ("봉고" in orig_name): continue
            
            filtered_models.add(get_core_model_name(orig_name, selected_brand))
        display_models = sorted(list(filtered_models))
    
    with col2:
        if selected_brand == "선택하세요":
            st.selectbox("2. 모델명 선택", ["업체를 먼저 선택하세요"], disabled=True)
            selected_display_model = None
        else:
            selected_display_model = st.selectbox("2. 모델명 선택", display_models, index=0) if display_models else None

    # --- 결과 출력 ---
    if selected_brand != "선택하세요" and selected_display_model:
        brand_df = df[df.iloc[:, 0] == selected_brand]
        target_rows = []
        for idx, row in brand_df.iterrows():
            if get_core_model_name(str(row.iloc[1]), selected_brand) == selected_display_model:
                target_rows.append(row)
        
        if target_rows:
            target_df = pd.DataFrame(target_rows)
            headers = df.columns[2:8].tolist()
            target_df['제외일자_raw'] = target_df.iloc[:, 8]
            
            excluded_df = target_df[target_df['제외일자_raw'].notna() & (target_df['제외일자_raw'].astype(str).str.strip() != "")]
            normal_df = target_df[~target_df.index.isin(excluded_df.index)]

            def make_html_line(row, is_excluded):
                orig_name = row.iloc[1]
                display_name = orig_name.replace("The New", "").replace("Mercedes-Benz", "").strip()
                vals = row.iloc[2:8].tolist()
                
                parts = []
                # 모델명 (볼드)
                parts.append(f"<div class='info-item'><span class='label'>모델:</span><span class='model-name'>{display_name}</span></div>")
                
                eff_val = 0
                for h, v in zip(headers, vals):
                    val_str = v.strftime("%Y-%m-%d") if isinstance(v, datetime.datetime) else format_value(v)
                    short_h = shorten_header(h)
                    
                    if "효율" in short_h or "주행" in short_h:
                        parts.append(f"<div class='info-item'><span class='label'>{short_h}:</span><span class='highlight'>{val_str}</span></div>")
                        if "효율" in short_h: eff_val = v 
                    else:
                        parts.append(f"<div class='info-item'><span class='label'>{short_h}:</span><span class='value-text'>{val_str}</span></div>")
                
                # 판정 배지
                grade_badge = analyze_grade(eff_val, is_excluded)
                if grade_badge:
                    parts.append(f"<div class='info-item'>{grade_badge}</div>")
                
                return "<div class='car-info-line'>" + "".join(parts) + "</div>"

            # 1. 제외된 차량 (그룹핑)
            if not excluded_df.empty:
                excluded_df['제외일_str'] = excluded_df['제외일자_raw'].apply(
                    lambda x: x.strftime("%Y-%m-%d") if isinstance(x, datetime.datetime) else str(x).split(" ")[0]
                )
                grouped = excluded_df.groupby('제외일_str')
                
                st.error(f"📉 [기준 미달/제외] - 총 {len(excluded_df)}건")
                for date_str, group in grouped:
                    with st.container():
                        st.markdown(f"**📅 제외일: {date_str}** ({len(group)}대)")
                        html_content = "<div class='result-container'>"
                        for _, row in group.iterrows():
                            html_content += make_html_line(row, is_excluded=True)
                        html_content += "</div>"
                        st.markdown(html_content, unsafe_allow_html=True)

            # 2. 정상 차량
            if not normal_df.empty:
                if not excluded_df.empty: st.markdown("---")
                st.success(f"✅ [기준 충족/정상] - 총 {len(normal_df)}건")
                html_content = "<div class='result-container'>"
                for _, row in normal_df.iterrows():
                    html_content += make_html_line(row, is_excluded=False)
                html_content += "</div>"
                st.markdown(html_content, unsafe_allow_html=True)
        else:
            st.warning("데이터가 없습니다.")
