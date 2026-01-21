import streamlit as st
import pandas as pd
import datetime
import os

# --- 페이지 설정 (레이아웃 넓게) ---
st.set_page_config(page_title="2026 친환경차 조회", page_icon="🚗", layout="centered")

# --- 커스텀 CSS (가운데 정렬 & 테이블 스타일) ---
st.markdown("""
    <style>
    /* 테이블 헤더와 셀 내용 가운데 정렬 */
    th, td {
        text-align: center !important;
        vertical-align: middle !important;
    }
    /* 테이블 외곽선 깔끔하게 */
    table {
        width: 100%;
        border-collapse: collapse;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚗 2026 친환경차(전기차) 등재 현황")
st.write("업체명과 모델명을 선택하여 제외 여부를 확인하세요.")

# --- 값 포맷팅 함수 (소수점 1자리) ---
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

    st.divider()

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

        # 공통: 테이블 HTML 생성 함수 (Index 제거 + 가운데 정렬)
        def make_html_table(rows):
            data_list = []
            for r in rows:
                data_list.append([format_value(v) for v in r.iloc[2:8].tolist()])
            
            temp_df = pd.DataFrame(data_list, columns=headers)
            # index=False로 "0" 표시 제거
            return temp_df.to_html(index=False, classes='table', escape=False)

        # 1. 제외된 차량
        if excluded_rows:
            st.error(f"🚨 [매입 제외] - {len(excluded_rows)}건")
            for i, row in enumerate(excluded_rows):
                ex_val = row.iloc[8]
                ex_date = ex_val.strftime("%Y-%m-%d") if isinstance(ex_val, datetime.datetime) else str(ex_val).split(" ")[0]
                
                st.markdown(f"**🔻 제외 상세 정보 #{i+1} (제외일: {ex_date})**")
                # HTML 테이블 렌더링
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
