import streamlit as st
import pandas as pd
import datetime
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="2026 친환경차 조회", page_icon="⚡", layout="centered")

# --- 스타일 설정 (다크모드/라이트모드 자동 호환) ---
st.markdown("""
    <style>
    /* 결과 박스: 테마에 따라 배경색과 글자색이 자동 변환되는 변수(var) 사용 */
    .info-box {
        text-align: center;
        /* Streamlit 기본 보조 배경색 사용 (다크모드에선 어둡게, 라이트모드에선 밝게) */
        background-color: var(--secondary-background-color);
        /* 기본 텍스트 색상 */
        color: var(--text-color);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        font-size: 15px;
        line-height: 1.8;
        /* 은은한 테두리 */
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    /* 항목(헤더) 강조 색상: 테마의 포인트 컬러(Primary Color) 사용 */
    .info-header {
        font-weight: bold;
        color: var(--primary-color); 
    }
    
    /* 구분선 색상 */
    .separator {
        opacity: 0.3;
        margin: 0 8px;
    }
    
    /* 기준표 테이블 텍스트 정렬 */
    th, td {
        text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 제목 (작게) ---
st.markdown("### 2026 친환경차(전기차) 등재 현황")
st.write("업체명과 모델명을 선택하여 제외 여부를 확인하세요.")

# --- 2. 기준표 ---
with st.expander("ℹ️ [참고] 전기자동차 에너지 소비효율 기준 보기", expanded=False):
    ref_data = {
        "구분 (차급)": ["초소·경·소형", "중형", "대형"],
        "기준 (km/kWh)": ["5.0 이상", "4.2 이상", "3.4 이상"]
    }
    st.table(pd.DataFrame(ref_data).set_index("구분 (차급)"))

st.divider()

# --- 값 포맷팅 함수 ---
def format_value(val):
    if isinstance(val, float):
        return f"{val:.1f}"
    if isinstance(val, datetime.datetime):
        return val.strftime("%Y-%m-%d")
    return val

# --- 데이터 로드 ---
@st.cache_data
def load_data():
    target_name = "2026환경친화적 자동차 등재 목록.xlsx"
    sheet_name = "별표 5의 제2호(전기자동차)"
    
    current_files = os.listdir('.')
    if target_name in current_files:
        try:
            return pd.read_excel(target_name, sheet_name=sheet_name)
        except: return None
            
    excel_files = [f for f in current_files if f.endswith('.xlsx')]
    if excel_files:
        try:
            return pd.read_excel(excel_files[0], sheet_name=sheet_name)
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

    # --- 선택 UI ---
    col1, col2 = st.columns(2)
    with col1:
        selected_brand = st.selectbox("1. 업체명 선택", ["선택하세요"] + sorted_brands)
    
    models = []
    if selected_brand != "선택하세요":
        brand_cars = df[df.iloc[:, 0] == selected_brand]
        models = brand_cars.iloc[:, 1].dropna().astype(str).unique().tolist()
        models.sort(reverse=True)
    
    with col2:
        selected_model = st.selectbox("2. 모델명 선택", ["선택하세요"] + models)

    st.markdown("---") 

    # --- 결과 출력 ---
    if selected_brand != "선택하세요" and selected_model != "선택하세요":
        target_rows = df[
            (df.iloc[:, 0] == selected_brand) & 
            (df.iloc[:, 1] == selected_model)
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

        # ★ 한 줄 정보 HTML 생성 (다크모드 호환)
        def make_one_line_html(row):
            items = []
            vals = row.iloc[2:8].tolist()
            
            for h, v in zip(headers, vals):
                if isinstance(v, datetime.datetime):
                    v_str = v.strftime("%Y-%m-%d")
                else:
                    v_str = format_value(v)
                
                # 항목 명에 강조 클래스 적용
                items.append(f"<span class='info-header'>{h}:</span> {v_str}")
            
            full_str = "<span class='separator'> / </span>".join(items)
            return f"<div class='info-box'>{full_str}</div>"

        # 1. 제외된 차량
        if excluded_rows:
            st.error(f"🚨 [매입 제외] - {len(excluded_rows)}건")
            for i, row in enumerate(excluded_rows):
                ex_val = row.iloc[8]
                ex_date = ex_val.strftime("%Y-%m-%d") if isinstance(ex_val, datetime.datetime) else str(ex_val).split(" ")[0]
                
                st.markdown(f"**🔻 제외 정보 #{i+1} (제외일: {ex_date})**")
                st.markdown(make_one_line_html(row), unsafe_allow_html=True)

        # 2. 정상 차량
        if normal_rows:
            if excluded_rows: st.markdown("---")
            st.success(f"✅ [정상 등재] - {len(normal_rows)}건")
            for i, row in enumerate(normal_rows):
                st.markdown(f"**🔹 상세 제원 #{i+1}**")
                st.markdown(make_one_line_html(row), unsafe_allow_html=True)

        if not excluded_rows and not normal_rows:
            st.warning("데이터 오류")
