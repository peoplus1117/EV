import streamlit as st
import pandas as pd
import datetime
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="2026 친환경차 조회", page_icon="🚗")

st.title("🚗 2026 친환경차(전기차) 등재 현황")
st.write("업체명과 모델명을 선택하여 제외 여부 및 상세 정보를 확인하세요.")

# --- 값 포맷팅 함수 (소수점 1자리) ---
def format_value(val):
    # 숫자인 경우 (실수형)
    if isinstance(val, float):
        return f"{val:.1f}"
    # 날짜인 경우
    if isinstance(val, datetime.datetime):
        return val.strftime("%Y-%m-%d")
    return val

# --- 데이터 로드 함수 ---
@st.cache_data
def load_data():
    target_name = "2026환경친화적 자동차 등재 목록.xlsx"
    sheet_name = "별표 5의 제2호(전기자동차)"
    
    # 파일 찾기 로직
    current_files = os.listdir('.')
    if target_name in current_files:
        try:
            return pd.read_excel(target_name, sheet_name=sheet_name)
        except:
            return None
            
    # 이름이 조금 달라도 엑셀 파일이면 시도
    excel_files = [f for f in current_files if f.endswith('.xlsx')]
    if excel_files:
        try:
            return pd.read_excel(excel_files[0], sheet_name=sheet_name)
        except:
            return None
    return None

df = load_data()

# --- 메인 로직 ---
if df is None:
    st.error("❌ 엑셀 파일을 찾을 수 없습니다. (GitHub 업로드 확인 필요)")
else:
    # 업체명 정렬
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
        # 데이터 조회
        target_rows = df[
            (df.iloc[:, 0] == selected_brand) & 
            (df.iloc[:, 1] == selected_model)
        ]
        
        # 헤더 이름 가져오기 (C~H열)
        headers = df.columns[2:8].tolist()
        
        # 결과 분류
        excluded_rows = [] # 제외된 차량
        normal_rows = []   # 정상 차량

        for _, row in target_rows.iterrows():
            exclusion_value = row.iloc[8] # I열 (제외일자)
            if pd.notna(exclusion_value) and str(exclusion_value).strip() != "":
                excluded_rows.append(row)
            else:
                normal_rows.append(row)

        # 1. 제외된 차량 출력 (빨간색)
        if excluded_rows:
            st.error(f"🚨 [매입 제외] - 총 {len(excluded_rows)}건")
            for i, row in enumerate(excluded_rows):
                # 제외일자 표시
                ex_val = row.iloc[8]
                ex_date = ex_val.strftime("%Y-%m-%d") if isinstance(ex_val, datetime.datetime) else str(ex_val).split(" ")[0]
                
                with st.expander(f"🔻 제외 상세 정보 #{i+1} (제외일: {ex_date})", expanded=True):
                    # 데이터 포맷팅
                    vals = [format_value(v) for v in row.iloc[2:8].tolist()]
                    
                    # 표 그리기
                    info_df = pd.DataFrame([vals], columns=headers)
                    st.table(info_df)

        # 2. 정상 등재 차량 출력 (초록색)
        if normal_rows:
            # 제외된 차량이 있는 경우 구분선 추가
            if excluded_rows: 
                st.markdown("---")
                
            st.success(f"✅ [정상 등재] - 총 {len(normal_rows)}건")
            for i, row in enumerate(normal_rows):
                # 정상 모델은 바로 상세정보 보여줌
                with st.container():
                    st.markdown(f"**🔹 상세 제원 #{i+1}**")
                    
                    # 데이터 포맷팅 (소수점 처리)
                    vals = [format_value(v) for v in row.iloc[2:8].tolist()]
                    
                    # 표 그리기
                    info_df = pd.DataFrame([vals], columns=headers)
                    st.table(info_df)

        if not excluded_rows and not normal_rows:
            st.warning("데이터는 존재하지만 표시할 수 없는 형식이거나 오류가 있습니다.")
