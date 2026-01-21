import streamlit as st
import pandas as pd
import datetime
import os
import re

# --- 페이지 설정 ---
st.set_page_config(page_title="2026 친환경차 조회", page_icon="⚡", layout="centered")

# --- 스타일 설정 ---
st.markdown("""
    <style>
    .info-box {
        text-align: center;
        background-color: var(--secondary-background-color);
        color: var(--text-color);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        font-size: 15px;
        line-height: 1.8;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .info-header {
        font-weight: bold;
        color: var(--primary-color); 
    }
    .highlight-efficiency {
        background-color: rgba(255, 255, 0, 0.2);
        color: #d32f2f;
        font-weight: 900;
        padding: 2px 5px;
        border-radius: 4px;
    }
    .separator {
        opacity: 0.3;
        margin: 0 8px;
    }
    th, td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("### 2026 친환경차(전기차) 등재 현황")
st.write("2026년 효율 기준 변경에 따른 제외/정상 여부를 확인하세요.")

# --- 기준표 ---
with st.expander("ℹ️ [기준] 2026년 전기차 에너지 소비효율 기준 (이보다 낮으면 제외됨)", expanded=False):
    ref_data = {
        "구분 (차급)": ["초소·경·소형", "중형 (가장 흔함)", "대형"],
        "기준 (km/kWh)": ["5.0 이상", "4.2 이상", "3.4 이상"]
    }
    st.table(pd.DataFrame(ref_data).set_index("구분 (차급)"))

st.divider()

# --- 포맷팅 함수 ---
def format_value(val):
    if isinstance(val, float): return f"{val:.1f}"
    if isinstance(val, datetime.datetime): return val.strftime("%Y-%m-%d")
    return val

def normalize_name(name):
    if not isinstance(name, str): return str(name)
    name = re.sub(r'\(.*?\)', '', name)
    name = name.replace(" ", "")
    return name.upper()

# --- 데이터 로드 ---
@st.cache_data
def load_data():
    target_name = "2026환경친화적 자동차 등재 목록.xlsx"
    sheet_name = "별표 5의 제2호(전기자동차)"
    
    current_files = os.listdir('.')
    file_to_load = None
    if target_name in current_files:
        file_to_load = target_name
    else:
        excel_files = [f for f in current_files if f.endswith('.xlsx')]
        if excel_files: file_to_load = excel_files[0]
            
    if file_to_load:
        try:
            df = pd.read_excel(file_to_load, sheet_name=sheet_name)
            df['검색용_이름'] = df.iloc[:, 1].astype(str).apply(normalize_name)
            return df
        except: return None
    return None

df = load_data()

# --- 메인 로직 ---
if df is None:
    st.error("❌ 엑셀 파일을 찾을 수 없습니다.")
else:
    preferred_order = [
        "현대자동차", "기아", "한국GM", "르노코리아", "케이지모빌리티", 
        "BMW", "메르세데스벤츠", "Audi", "폭스바겐", "볼보", 
        "테슬라", "폴스타", "포르쉐코리아", "BYD", "Lexus"
    ]
    
    existing_brands = df.iloc[:, 0].dropna().astype(str).unique().tolist()
    sorted_brands = [b for b in preferred_order if b in existing_brands]
    sorted_brands += [b for b in existing_brands if b not in preferred_order]

    col1, col2 = st.columns(2)
    with col1:
        selected_brand = st.selectbox("1. 업체명 선택", ["선택하세요"] + sorted_brands)
    
    display_models = []
    if selected_brand != "선택하세요":
        brand_df = df[df.iloc[:, 0] == selected_brand]
        unique_pairs = brand_df[['검색용_이름', brand_df.columns[1]]].values.tolist()
        
        # [필터링 로직] 상용차 제외
        filtered_pairs = []
        for pair in unique_pairs:
            orig_name = str(pair[1])
            
            # 현대자동차: 포터, ST1 제외
            if selected_brand == "현대자동차":
                if "포터" in orig_name or "ST1" in orig_name:
                    continue 
            
            # 기아: 봉고 제외
            elif selected_brand == "기아":
                if "봉고" in orig_name:
                    continue 
            
            filtered_pairs.append(pair)
            
        # 중복 제거 및 대표 이름 선정
        model_map = {}
        for search_name, original_name in filtered_pairs:
            if search_name not in model_map:
                model_map[search_name] = str(original_name).split('(')[0].strip()
        
        # ★ [수정됨] 오름차순 정렬 (reverse=False)
        display_models = sorted(list(model_map.values()), reverse=False)
    
    with col2:
        selected_display_model = st.selectbox("2. 모델명 선택", ["선택하세요"] + display_models)

    st.markdown("---") 

    if selected_brand != "선택하세요" and selected_display_model != "선택하세요":
        search_key = normalize_name(selected_display_model)
        target_rows = df[
            (df.iloc[:, 0] == selected_brand) & 
            (df['검색용_이름'] == search_key)
        ]
        
        headers = df.columns[2:8].tolist()
        excluded_rows = [] 
        normal_rows = []

        for _, row in target_rows.iterrows():
            exclusion_value = row.iloc[8]
            if pd.notna(exclusion_value) and str(exclusion_value).strip() != "":
                excluded_rows.append(row)
            else:
                normal_rows.append(row)

        # HTML 생성 함수
        def make_one_line_html(row):
            items = []
            vals = row.iloc[2:8].tolist()
            original_model_name = row.iloc[1]
            
            items.append(f"<span class='info-header' style='color:#000;'>모델:</span> <b>{original_model_name}</b>")

            for h, v in zip(headers, vals):
                if isinstance(v, datetime.datetime):
                    v_str = v.strftime("%Y-%m-%d")
                else:
                    v_str = format_value(v)
                
                # 연비/효율 강조
                if any(keyword in str(h) for keyword in ['연비', '효율', 'km']):
                     items.append(f"<span class='info-header'>{h}:</span> <span class='highlight-efficiency'>{v_str}</span>")
                else:
                     items.append(f"<span class='info-header'>{h}:</span> {v_str}")
            
            full_str = "<span class='separator'> | </span>".join(items)
            return f"<div class='info-box'>{full_str}</div>"

        # 1. 제외된 차량
        if excluded_rows:
            st.error(f"📉 [기준 미달/제외] - {len(excluded_rows)}건")
            for i, row in enumerate(excluded_rows):
                ex_val = row.iloc[8]
                ex_date = ex_val.strftime("%Y-%m-%d") if isinstance(ex_val, datetime.datetime) else str(ex_val).split(" ")[0]
                
                st.markdown(f"**🔻 제외 정보 #{i+1} (제외일: {ex_date})**")
                st.markdown(make_one_line_html(row), unsafe_allow_html=True)

        # 2. 정상 차량
        if normal_rows:
            if excluded_rows: st.markdown("---")
            st.success(f"✅ [기준 충족/정상] - {len(normal_rows)}건")
            for i, row in enumerate(normal_rows):
                st.markdown(f"**🔹 등재 상세 #{i+1}**")
                st.markdown(make_one_line_html(row), unsafe_allow_html=True)

        if not excluded_rows and not normal_rows:
            st.warning("데이터 오류")
