import streamlit as st
import pandas as pd
import datetime
import os
import re

# --- 페이지 설정 ---
st.set_page_config(page_title="2026 친환경차 현황 by 김희주", page_icon="⚡", layout="wide")

# --- 스타일 설정 ---
st.markdown("""
    <style>
    /* 결과 박스 */
    .result-container {
        background-color: var(--secondary-background-color);
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    /* 반응형 레이아웃 */
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
    .car-info-line:last-child { border-bottom: none; }

    .info-item {
        white-space: nowrap;        
        display: inline-flex;
        align-items: center;
    }

    .label {
        font-weight: normal; 
        color: var(--primary-color);
        margin-right: 4px;
        font-size: 0.9em;
    }

    /* 모델명만 볼드 */
    .model-name {
        font-weight: bold;    
        color: var(--text-color);
        font-size: 1.05em;
        margin-right: 5px;
    }

    .highlight {
        background-color: rgba(255, 255, 0, 0.2);
        color: #ff4b4b;
        font-weight: normal;
        padding: 1px 4px;
        border-radius: 3px;
    }
    
    .value-text {
        color: var(--text-color);
        font-weight: normal;
    }

    /* 배지 스타일 */
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

# --- 모델명 통합 및 클렌징 로직 ---
def get_core_model_name(original_name, brand):
    if not isinstance(original_name, str): return str(original_name)
    name = original_name.upper()
    name = re.sub(r'\(.*?\)', '', name)
    for g in ["THE NEW", "ALL NEW", "FACELIFT", "MERCEDES-BENZ", "MERCEDES", "BENZ"]:
        name = name.replace(g, "")
    name = name.strip()

    # [쓰레기 데이터 제거] 브랜드명이 모델명으로 들어간 경우 삭제
    if brand == "한국GM":
        if name in ["CHEVROLET", "쉐보레"]: return None
    if brand == "볼보":
        if name in ["VOLVO", "볼보"]: return None

    # 벤츠 EQ
    if brand == "메르세데스벤츠":
        match = re.search(r'(EQ[A-Z])', name)
        if match: return match.group(1)
        return name.split()[0] if name else original_name

    # 현대/기아/제네시스
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

    # BMW
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

    # 공통 접미사 제거
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
    # 1. 브랜드 노출 제한 (현대 ~ 렉서스)
    allowed_brands = [
        "현대자동차", "기아", "한국GM", "르노코리아", "케이지모빌리티", 
        "BMW", "메르세데스벤츠", "Audi", "폭스바겐", "볼보", 
        "테슬라", "폴스타", "포르쉐코리아", "BYD", "Lexus"
    ]
    
    existing_brands = df.iloc[:, 0].dropna().astype(str).unique().tolist()
    # 엑셀에 있어도 allowed_brands에 없으면 제외됨 (닛산 등 비노출)
    sorted_brands = [b for b in allowed_brands if b in existing_brands]

    col1, col2 = st.columns(2)
    with col1:
        selected_brand = st.selectbox("1. 업체명 선택", ["선택하세요"] + sorted_brands)
    
    # 2. 모델 리스트 생성
    display_models = []
    
    # 브랜드별 모든 데이터를 미리 처리 (등급 판정용)
    if selected_brand != "선택하세요":
        brand_df = df[df.iloc[:, 0] == selected_brand].copy()
        
        # 핵심 모델명 컬럼 추가
        brand_df['Core_Model'] = brand_df.iloc[:, 1].apply(lambda x: get_core_model_name(str(x), selected_brand))
        
        # None(쓰레기 데이터) 및 상용차 필터링
        brand_df = brand_df.dropna(subset=['Core_Model'])
        if selected_brand == "현대자동차":
            brand_df = brand_df[~brand_df.iloc[:, 1].str.contains("포터|ST1")]
        if selected_brand == "기아":
            brand_df = brand_df[~brand_df.iloc[:, 1].str.contains("봉고")]
            
        # 모델 목록 추출
        display_models = sorted(list(brand_df['Core_Model'].unique()))
    
    with col2:
        if selected_brand == "선택하세요":
            st.selectbox("2. 모델명 선택", ["업체를 먼저 선택하세요"], disabled=True)
            selected_display_model = None
        else:
            # 기본값: 전체 보기 (None 대신 "전체 보기" 옵션 제공)
            model_options = ["전체 보기"] + display_models
            selected_display_model = st.selectbox("2. 모델명 선택", model_options)

    st.markdown("---") 

    # --- 결과 처리 및 출력 ---
    if selected_brand != "선택하세요":
        
        # 1. 필터링 (전체 보기 vs 특정 모델)
        if selected_display_model == "전체 보기":
            target_df = brand_df # 이미 위에서 전처리된 DF 사용
        else:
            target_df = brand_df[brand_df['Core_Model'] == selected_display_model]
        
        if not target_df.empty:
            headers = df.columns[2:8].tolist()
            target_df['제외일자_raw'] = target_df.iloc[:, 8]
            
            # --- [핵심] 지능형 차급(Threshold) 판정 로직 ---
            # 모델별로 그룹핑하여 각 모델 가문의 '최소 생존 기준'을 계산해둡니다.
            # 예: "아이오닉5" 그룹은 4.2 기준, "코나" 그룹은 5.0 기준
            
            model_threshold_map = {} # {모델명: (차급명, 기준값)}

            # 모델별로 순회하며 기준 수립
            for model_name, group in target_df.groupby('Core_Model'):
                # 정상인 차들의 연비만 수집
                alive_mask = ~(group['제외일자_raw'].notna() & (group['제외일자_raw'].astype(str).str.strip() != ""))
                alive_group = group[alive_mask]
                
                normal_effs = []
                for _, row in alive_group.iterrows():
                    for h, v in zip(headers, row.iloc[2:8].tolist()):
                        if "효율" in str(h) or "연비" in str(h):
                            try: normal_effs.append(float(v))
                            except: pass
                
                # 기본값 (중형)
                c_name, c_th = "중형", 4.2
                
                if normal_effs:
                    min_eff = min(normal_effs)
                    if min_eff < 4.2: c_name, c_th = "대형", 3.4
                    elif min_eff < 5.0: c_name, c_th = "중형", 4.2
                    else: c_name, c_th = "소형", 5.0
                
                model_threshold_map[model_name] = (c_name, c_th)

            # --- 데이터 분리 (제외 / 정상) ---
            excluded_mask = target_df['제외일자_raw'].notna() & (target_df['제외일자_raw'].astype(str).str.strip() != "")
            excluded_df = target_df[excluded_mask]
            normal_df = target_df[~excluded_mask]

            # HTML 생성 함수
            def make_html_line(row, is_excluded):
                core_model = row['Core_Model']
                orig_name = row.iloc[1]
                display_name = str(orig_name).replace("The New", "").replace("Mercedes-Benz", "").strip()
                vals = row.iloc[2:8].tolist()
                
                # 이 모델의 기준 가져오기
                detected_class, detected_th = model_threshold_map.get(core_model, ("중형", 4.2))

                parts = []
                parts.append(f"<div class='info-item'><span class='label'>모델:</span><span class='model-name'>{display_name}</span></div>")
                
                my_eff = 0
                for h, v in zip(headers, vals):
                    val_str = v.strftime("%Y-%m-%d") if isinstance(v, datetime.datetime) else format_value(v)
                    short_h = shorten_header(h)
                    
                    if "효율" in short_h or "주행" in short_h:
                        parts.append(f"<div class='info-item'><span class='label'>{short_h}:</span><span class='highlight'>{val_str}</span></div>")
                        if "효율" in short_h: 
                            try: my_eff = float(v)
                            except: pass
                    else:
                        parts.append(f"<div class='info-item'><span class='label'>{short_h}:</span><span class='value-text'>{val_str}</span></div>")
                
                # 배지 생성
                badge = ""
                if is_excluded:
                    if my_eff < 3.4: badge = "<span class='grade-badge-fail'>대형(3.4) 미달</span>"
                    elif 3.4 <= my_eff < 4.2: badge = "<span class='grade-badge-fail'>중형(4.2) 미달</span>"
                    elif 4.2 <= my_eff < 5.0: badge = "<span class='grade-badge-fail'>소형(5.0) 미달</span>"
                    else: badge = "<span class='grade-badge-fail'>기준 미달</span>"
                else:
                    badge = f"<span class='grade-badge-pass'>{detected_class}({detected_th}) 충족</span>"

                if badge: parts.append(f"<div class='info-item'>{badge}</div>")
                return "<div class='car-info-line'>" + "".join(parts) + "</div>"

            # 1. 제외된 차량 (그룹핑)
            if not excluded_df.empty:
                excluded_df['제외일_str'] = excluded_df['제외일자_raw'].apply(
                    lambda x: x.strftime("%Y-%m-%d") if isinstance(x, datetime.datetime) else str(x).split(" ")[0]
                )
                
                st.error(f"📉 [기준 미달/제외] - 총 {len(excluded_df)}건")
                for date_str, group in excluded_df.groupby('제외일_str'):
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
