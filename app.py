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
    .result-container {
        background-color: var(--secondary-background-color);
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
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

    .model-name {
        font-weight: bold;    
        color: var(--text-color);
        font-size: 1.05em;
        margin-right: 5px;
    }

    .wb-tag {
        color: #666;
        font-size: 0.9em;
        margin-right: 10px;
        background-color: rgba(128, 128, 128, 0.1);
        padding: 1px 5px;
        border-radius: 4px;
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

with st.expander("ℹ️ [기준] 2026년 전기차 에너지 소비효율 기준 (축거 반영)", expanded=False):
    ref_data = {
        "구분": ["초소·경·소형", "중형 (축거 3,050mm 미만)", "대형 (축거 3,050mm 이상)"],
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

# --- 주요 전기차 축거(휠베이스) 데이터 베이스 ---
def get_car_wheelbase(full_name_raw):
    name = str(full_name_raw).upper().replace(" ", "")
    
    # 1. 제네시스
    if "G80" in name: return 3010
    if "GV60" in name: return 2900
    if "GV70" in name: return 2875
    if "G90" in name: return 3180
    if "GV80" in name: return 2955
    
    # 2. 현대
    if "IONIQ5" in name or "아이오닉5" in name: return 3000
    if "IONIQ6" in name or "아이오닉6" in name: return 2950
    if "KONA" in name or "코나" in name: return 2660
    if "CASPER" in name or "캐스퍼" in name: return 2580
    if "PORTER" in name or "포터" in name: return 2810
    if "ST1" in name: return 3500
    
    # 3. 기아
    if "EV9" in name: return 3100
    if "EV6" in name: return 2900
    if "EV3" in name: return 2680
    if "NIRO" in name or "니로" in name: return 2720
    if "RAY" in name or "레이" in name: return 2520
    if "BONGO" in name or "봉고" in name: return 2810
    
    # 4. 테슬라
    if "MODELS" in name: return 2960
    if "MODELX" in name: return 2965
    if "MODEL3" in name: return 2875
    if "MODELY" in name: return 2890
    
    # 5. 벤츠
    if "EQE" in name:
        if "SUV" in name: return 3030
        return 3120
    if "EQS" in name: return 3210
    if "EQA" in name: return 2729
    if "EQB" in name: return 2829
    
    # 6. BMW
    if "I7" in name: return 3215
    if "I5" in name: return 2995
    if "I4" in name: return 2856
    if "IX1" in name: return 2692
    if "IX3" in name: return 2864
    if "IX" in name and "X1" not in name and "X3" not in name: return 3000
    
    # 7. 아우디
    if "Q4" in name: return 2764
    if "Q8" in name: return 2928
    if "E-TRONGT" in name: return 2900
    
    # 8. 기타
    if "POLESTAR2" in name or "폴스타2" in name: return 2735
    if "POLESTAR4" in name or "폴스타4" in name: return 2999
    if "ID.4" in name: return 2765
    if "C40" in name or "XC40" in name: return 2702
    if "EX30" in name: return 2650
    if "TAYCAN" in name or "타이칸" in name: return 2900
    if "TORRES" in name or "토레스" in name: return 2680
    if "KORANDO" in name or "코란도" in name: return 2675
    if "SEAL" in name: return 2920
    if "ATTO" in name: return 2720
    
    return None

# --- 모델명 클렌징 로직 ---
def get_core_model_name(original_name, brand):
    if not isinstance(original_name, str): return str(original_name)
    name = original_name.upper()
    name = re.sub(r'\(.*?\)', '', name)
    
    garbage_words = ["THE NEW", "ALL NEW", "FACELIFT", "MERCEDES-BENZ", "MERCEDES", "BENZ", "CHEVROLET", "쉐보레", "VOLVO", "볼보", "BYD"]
    for g in garbage_words: name = name.replace(g, "")
    
    name = name.strip()
    if not name: return None

    if brand == "메르세데스벤츠":
        match = re.search(r'(EQ[A-Z])', name)
        if match: return match.group(1)
        return name.split()[0]
    
    if brand in ["기아", "현대자동차", "제네시스"]:
        if "EV" in name:
             match = re.search(r'(EV\s?\d+)', name)
             if match: return match.group(1).replace(" ", "")
        if "IONIQ" in name or "아이오닉" in name:
             match = re.search(r'(IONIQ\s?\d+|아이오닉\s?\d+)', name)
             if match: return "아이오닉" + re.sub(r'[^0-9]', '', match.group(1))
        match_g = re.search(r'(GV\d+|G\d+)', name)
        if match_g: return match_g.group(1)
        # [수정] for문 줄바꿈 처리하여 문법 에러 해결
        for k in ["KONA", "코나", "NIRO", "니로", "RAY", "레이", "CASPER", "캐스퍼"]: 
            if k in name: return k

    if brand == "BMW":
        first = name.split()[0]
        if first.startswith("I"): return first
        
    if brand in ["Audi", "아우디"]:
        if "Q4" in name: return "Q4 e-tron"
        if "Q8" in name: return "Q8 e-tron"
        if name.startswith("E-TRON"): return "e-tron"
        
    if brand == "테슬라" and "MODEL" in name:
        parts = name.split()
        try:
            idx = parts.index("MODEL")
            if idx + 1 < len(parts): return f"MODEL {parts[idx+1]}"
        except: pass
        
    if brand == "폴스타" and "POLESTAR" in name:
        parts = name.split()
        try:
             idx = parts.index("POLESTAR")
             if idx+1 < len(parts): return f"POLESTAR {parts[idx+1]}"
        except: pass
        
    if brand == "폭스바겐" and "ID." in name: return name.split()[0]

    remove_suffixes = ["LONG RANGE", "LONGRANGE", "STANDARD", "PERFORMANCE", "2WD", "4WD", "AWD", "RWD", "FWD", "GT-LINE", "GT", "PRO", "PRIME", "EUV", "EV"]
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
    allowed_brands = [
        "현대자동차", "기아", "한국GM", "르노코리아", "케이지모빌리티", 
        "BMW", "메르세데스벤츠", "Audi", "폭스바겐", "볼보", 
        "테슬라", "폴스타", "포르쉐코리아", "BYD", "Lexus"
    ]
    existing_brands = df.iloc[:, 0].dropna().astype(str).unique().tolist()
    sorted_brands = [b for b in allowed_brands if b in existing_brands]
    headers = df.columns[2:8].tolist()

    col1, col2 = st.columns(2)
    with col1:
        selected_brand = st.selectbox("1. 업체명 선택", ["선택하세요"] + sorted_brands)
    
    display_models = []
    # 등급 판정용 백업 맵 (데이터 없을 때 사용)
    model_threshold_map_backup = {} 

    if selected_brand != "선택하세요":
        brand_df = df[df.iloc[:, 0] == selected_brand].copy()
        brand_df['제외일자_raw'] = brand_df.iloc[:, 8]
        brand_df['Core_Model'] = brand_df.iloc[:, 1].apply(lambda x: get_core_model_name(str(x), selected_brand))
        brand_df = brand_df.dropna(subset=['Core_Model'])
        if selected_brand == "현대자동차": brand_df = brand_df[~brand_df.iloc[:, 1].str.contains("포터|ST1")]
        if selected_brand == "기아": brand_df = brand_df[~brand_df.iloc[:, 1].str.contains("봉고")]
        display_models = sorted(list(brand_df['Core_Model'].unique()))

    with col2:
        if selected_brand == "선택하세요":
            st.selectbox("2. 모델명 선택", ["업체를 먼저 선택하세요"], disabled=True)
            selected_display_model = None
        else:
            selected_display_model = st.selectbox("2. 모델명 선택", ["전체 보기"] + display_models)

    st.markdown("---") 

    if selected_brand != "선택하세요":
        if selected_display_model == "전체 보기": target_df = brand_df
        else: target_df = brand_df[brand_df['Core_Model'] == selected_display_model]
        
        if not target_df.empty:
            # 1. 백업용(통계적 추론) 기준 계산
            calc_df = brand_df 
            for model_name, group in calc_df.groupby('Core_Model'):
                alive_mask = ~(group['제외일자_raw'].notna() & (group['제외일자_raw'].astype(str).str.strip() != ""))
                alive_group = group[alive_mask]
                normal_effs = []
                for _, row in alive_group.iterrows():
                    for h, v in zip(headers, row.iloc[2:8].tolist()):
                        if "효율" in str(h) or "연비" in str(h):
                            try: normal_effs.append(float(v))
                            except: pass
                c_name, c_th = "중형", 4.2
                if normal_effs:
                    min_eff = min(normal_effs)
                    if min_eff < 4.2: c_name, c_th = "대형", 3.4
                    elif min_eff < 5.0: c_name, c_th = "중형", 4.2
                    else: c_name, c_th = "소형", 5.0
                model_threshold_map_backup[model_name] = (c_name, c_th)

            excluded_mask = target_df['제외일자_raw'].notna() & (target_df['제외일자_raw'].astype(str).str.strip() != "")
            excluded_df = target_df[excluded_mask]
            normal_df = target_df[~excluded_mask]

            def make_html_line(row, is_excluded):
                core_model = row['Core_Model']
                orig_name = str(row.iloc[1])
                
                # 화면 표시 이름
                display_name = orig_name
                for g in ["The New", "All New", "Mercedes-Benz", "MERCEDES-BENZ", "CHEVROLET", "Chevrolet", "Volvo", "VOLVO", "BYD"]:
                    display_name = display_name.replace(g, "")
                display_name = display_name.strip()
                
                vals = row.iloc[2:8].tolist()

                # --- [핵심] 축거 확인 및 기준 결정 ---
                wb = get_car_wheelbase(orig_name) # 전체 이름으로 조회
                
                detected_class = "중형"
                detected_th = 4.2

                if wb is not None:
                    # 데이터가 있으면 3050mm 기준으로 판정
                    if wb >= 3050:
                        detected_class = "대형"
                        detected_th = 3.4
                    else:
                        detected_class = "중형" # (소형도 포함)
                        detected_th = 4.2
                    
                    # 이름 옆에 축거 표시
                    display_name += f" <span class='wb-tag'>(축거 {wb}mm)</span>"
                else:
                    # 데이터 없으면 백업 로직(통계 추론) 사용
                    detected_class, detected_th = model_threshold_map_backup.get(core_model, ("중형", 4.2))

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
                
                badge = ""
                if is_excluded:
                    if my_eff < 3.4: badge = "<span class='grade-badge-fail'>대형(3.4) 미달</span>"
                    elif 3.4 <= my_eff < 4.2:
                        if detected_th == 3.4: # 대형 기준 적용받는 차라면
                             badge = "<span class='grade-badge-pass'>대형(3.4) 충족 (제외됨?)</span>" 
                        else:
                             badge = "<span class='grade-badge-fail'>중형(4.2) 미달</span>"
                    elif 4.2 <= my_eff < 5.0: badge = "<span class='grade-badge-fail'>소형(5.0) 미달</span>"
                    else: badge = "<span class='grade-badge-fail'>기준 미달</span>"
                else:
                    badge = f"<span class='grade-badge-pass'>{detected_class}({detected_th}) 충족</span>"

                if badge: parts.append(f"<div class='info-item'>{badge}</div>")
                return "<div class='car-info-line'>" + "".join(parts) + "</div>"

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
