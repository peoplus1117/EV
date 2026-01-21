import streamlit as st
import pandas as pd
import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="2026 친환경차 조회", page_icon="🚗")

# --- 제목 및 설명 ---
st.title("🚗 2026 친환경차(전기차) 제외 여부 확인")
st.write("업체명과 모델명을 선택하여 매입 제외 여부를 확인하세요.")

# --- 데이터 로드 함수 (캐싱 적용) ---
@st.cache_data
def load_data():
    # 엑셀 파일 이름이 정확해야 합니다
    file_name = "2026환경친화적 자동차 등재 목록.xlsx"
    sheet_name = "별표 5의 제2호(전기자동차)"
    
    try:
        df = pd.read_excel(file_name, sheet_name=sheet_name)
        return df
    except Exception as e:
        return None

df = load_data()

# --- 파일 로드 결과 처리 ---
if df is None:
    st.error("❌ 엑셀 파일을 찾을 수 없습니다!")
    st.warning("GitHub 저장소(Repository)에 '2026환경친화적 자동차 등재 목록.xlsx' 파일이 함께 업로드되어 있는지 꼭 확인해주세요.")
else:
    # --- 데이터 전처리 ---
    preferred_order = [
        "현대자동차", "기아", "한국GM", "르노코리아", "케이지모빌리티", 
        "BMW", "메르세데스벤츠", "Audi", "폭스바겐", "볼보", 
        "테슬라", "폴스타", "포르쉐코리아", "BYD", "Lexus"
    ]
    
    existing_brands = df.iloc[:, 0].dropna().astype(str).unique().tolist()
    sorted_brands = [b for b in preferred_order if b in existing_brands]
    sorted_brands += [b for b in existing_brands if b not in preferred_order]

    # --- UI 구성 ---
    col1, col2 = st.columns(2)
    
    with col1:
        selected_brand = st.selectbox("1. 업체명 선택", ["선택하세요"] + sorted_brands)
    
    # 모델명 선택 로직
    models = []
    if selected_brand != "선택하세요":
        brand_cars = df[df.iloc[:, 0] == selected_brand]
        models = brand_cars.iloc[:, 1].dropna().astype(str).unique().tolist()
        models.sort(reverse=True) # 내림차순 정렬
    
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
        
        excluded_rows = []
        normal_rows = []
        
        # 제외 여부 판별 (I열: index 8)
        for _, row in target_rows.iterrows():
            exclusion_value = row.iloc[8]
            # 제외일자가 있으면(비어있지 않으면) 제외 차량
            if pd.notna(exclusion_value) and str(exclusion_value).strip() != "":
                excluded_rows.append(row)
            else:
                normal_rows.append(row)

        if excluded_rows:
            st.error(f"🚨 [매입 제외 모델입니다] - {selected_model}")
            st.warning("⚠️ 아래 상세 사유를 확인하세요.")
            
            for i, row in enumerate(excluded_rows):
                # 날짜 포맷
                ex_date = row.iloc[8]
                if isinstance(ex_date, datetime.datetime):
                    ex_date_str = ex_date.strftime("%Y-%m-%d")
                else:
                    ex_date_str = str(ex_date).split(" ")[0]

                with st.container():
                    st.markdown(f"**📌 상세 정보 #{i+1} (제외일: {ex_date_str})**")
                    
                    # 헤더 및 값 가져오기 (C~H열)
                    headers = df.columns[2:8].tolist()
                    vals = row.iloc[2:8].tolist()
                    
                    # 표 만들기
                    info_dict = {}
                    for h, v in zip(headers, vals):
                        if isinstance(v, datetime.datetime):
                            v = v.strftime("%Y-%m-%d")
                        info_dict[h] = [v]
                    
                    st.table(pd.DataFrame(info_dict))
                    
        else:
            st.success(f"✅ [정상 등재 모델입니다] - {selected_model}")
            st.info("제외일자가 확인되지 않았습니다. 안심하고 진행하세요.")
