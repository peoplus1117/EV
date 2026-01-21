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

    .car-info-line:last-child {
        border-bottom: none;
    }

    .info-item {
        white-space: nowrap;        
        display: inline-flex;
        align-items: center;
    }

    /* 라벨 (볼드 X) */
    .label {
        font-weight: normal; 
        color: var(--primary-color);
        margin-right: 4px;
        font-size: 0.9em;
    }

    /* 모델명 (볼드 O) */
    .model-name {
        font-weight: bold;    
        color: var(--text-color);
        font-size: 1.05em;
        margin-right: 5px;
    }

    /* 강조값 (볼드 X) */
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

def get_core_model_name(original_name, brand):
    if not isinstance(original_name, str): return str(original_name)
    name = original_name.upper()
    name = re.sub(r'\(.*?\)', '', name)
    for g in ["THE NEW", "ALL NEW", "FACELIFT", "MERCEDES-BENZ", "MERCEDES", "BENZ"]:
        name = name.replace(g, "")
    name = name.strip()

    if brand == "메르세데스벤츠":
        match = re.search(r'(EQ[A-Z])', name)
        if match: return match.group(1)
        return name.split()[0] if name else original_name

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
            
            # 제외 여부 확인
            excluded_mask = target_df['제외일자_raw'].notna() & (target_df['제외일자_raw'].astype(str).str.strip() != "")
            excluded_df = target_df[excluded_mask]
            normal_df = target_df[~excluded_mask]
            
            # --- ★ [핵심 로직] 그룹 전체의 '최소 기준' 추론 ---
            # 1. 정상 차량들의 연비 수집
            normal_effs = []
            for _, row in normal_df.iterrows():
                # 헤더에서 '효율'이나 '연비'가 포함된 컬럼의 값을 찾음
                for h, v in zip(headers, row.iloc[2:8].tolist()):
                    if "효율" in str(h) or "연비" in str(h):
                        try: normal_effs.append(float(v))
                        except: pass
            
            # 2. 그룹의 '대표 차급' 결정 (가장 낮은 연비로 살아남은 녀석 기준)
            # 기본값: 알 수 없음 (중형으로 가정)
            detected_class_name = "중형" 
            detected_threshold = 4.2
            
            if normal_effs:
                min_eff = min(normal_effs)
                if min_eff < 4.2:
                    # 4.2 미만인데 살아남았다 -> 대형이 확실함
                    detected_class_name = "대형"
                    detected_threshold = 3.4
                elif min_eff < 5.0:
                    # 5.0 미만인데 살아남았다 -> 중형(또는 대형) -> 보통 중형으로 봄
                    detected_class_name = "중형"
                    detected_threshold = 4.2
                else:
                    # 살아남은 애들이 다 5.0 넘음 -> 소형일 확률 높음
                    detected_class_name = "소형"
                    detected_threshold = 5.0
            
            # --- HTML 생성 함수 (추론된 차급 적용) ---
            def make_html_line(row, is_excluded):
                orig_name = row.iloc[1]
                display_name = orig_name.replace("The New", "").replace("Mercedes-Benz", "").strip()
                vals = row.iloc[2:8].tolist()
                
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
                
                # 배지 생성 (detected_class_name 사용)
                badge = ""
                if is_excluded:
                    # 제외된 경우: 왜 제외됐는지?
                    # 추론된 기준(예: 대형 3.4)보다 낮아서? 아니면 원래 기준보다 낮아서?
                    # 제외된 차는 해당 차급 기준 미달로 표시
                    if my_eff < detected_threshold:
                         badge = f"<span class='grade-badge-fail'>{detected_class_name}({detected_threshold}) 미달</span>"
                    else:
                         # 추론된 기준은 넘었는데 제외됐다? -> 사실 더 높은 차급이었을 수 있음
                         # 예: 추론은 대형(3.4)인데, 얘는 3.8인데 죽음 -> 사실 중형(4.2)이었던 거임
                         badge = "<span class='grade-badge-fail'>기준 미달</span>"
                else:
                    # 정상인 경우: 추론된 차급 기준 충족 표시
                    badge = f"<span class='grade-badge-pass'>{detected_class_name}({detected_threshold}) 충족</span>"

                if badge: parts.append(f"<div class='info-item'>{badge}</div>")
                return "<div class='car-info-line'>" + "".join(parts) + "</div>"

            # 1. 제외된 차량 출력
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

            # 2. 정상 차량 출력
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
