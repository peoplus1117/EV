import streamlit as st
import pandas as pd
import datetime
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="2026 친환경차 조회", page_icon="⚡", layout="centered")

# --- 커스텀 CSS ---
st.markdown("""
    <style>
    th, td {
        text-align: center !important;
        vertical-align: middle !important;
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 제목 수정 (작게, 이모티콘 제거) ---
st.markdown("### 2026 친환경차(전기차) 등재 현황")
st.write("업체명과 모델명을 선택하여 제외 여부를 확인하세요.")

# --- 2. 이미지 내용 추가 (기준표 정리) ---
with st.expander("ℹ️ [참고] 전기자동차 에너지 소비효율 기준 보기", expanded=False):
    st.markdown("**3. 전기자동차의 기준 (승용자동차)**")
    
    # 보기 편하게 행/열을 바꿔서(Transposed) 표 생성
    ref_data = {
        "구분 (차급)": ["초소·경·소형", "중형", "대형"],
        "에너지 소비효율 (km/kWh)": ["5.0 이상", "4.2 이상", "3.4 이상"]
    }
    st.table(pd.DataFrame(ref_data))

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

    st.markdown("---") # 구분선

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

        # 공통: 테이블 HTML 생성 함수
        def make_html_table(rows):
            data_list = []
            for r in rows:
                data_list.append([format_value(v) for v in r.iloc[2:8].tolist()])
            
            temp_df = pd.DataFrame(data_list, columns=headers)
            return temp_df.to_html(index=False, classes='table', escape=False)

        # 1. 제외된 차량
        if excluded_rows:
            st.error(f"🚨 [매입 제외] - {len(excluded_rows)}건")
            for i, row in enumerate(excluded_rows):
                ex_val = row.iloc[8]
                ex_date = ex_val.strftime("%Y-%m-%d") if isinstance(ex_val, datetime.datetime) else str(ex_val).split(" ")[0]
                
                st.markdown(f"**🔻 제외 상세 정보 #{i+1} (제외일: {ex_date})**")
                st.markdown(make_html_table([row]), unsafe_allow_html=True)

        # 2. 정상 차량
        if normal_rows:
            if excluded_rows: st.markdown("---")
            st.success(f"✅ [정상 등재] - {len(normal_rows)}건")
            for i, row in enumerate(normal_rows):
                st.markdown(f"**🔹 상세 제원 #{i+1}**")
                st.markdown(make_html_table([row]), unsafe_allow_html=True)

        if not excluded_rows and not normal_rows:
            st.warning("데이터 오류")
