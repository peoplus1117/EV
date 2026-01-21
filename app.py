import streamlit as st
import pandas as pd
import datetime
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="2026 친환경차 조회", page_icon="🚗")

st.title("🚗 2026 친환경차(전기차) 제외 여부 확인")

# --- [핵심] 파일 자동 찾기 및 로드 함수 ---
@st.cache_data
def load_data():
    # 1. 우리가 원하는 정확한 파일명
    target_name = "2026환경친화적 자동차 등재 목록.xlsx"
    sheet_name = "별표 5의 제2호(전기자동차)"
    
    # 2. 현재 폴더에 있는 모든 파일 목록 확인
    current_files = os.listdir('.')
    
    # 3. 정확한 파일이 있는지 확인
    if target_name in current_files:
        try:
            return pd.read_excel(target_name, sheet_name=sheet_name), "성공"
        except Exception as e:
            return None, f"파일은 찾았으나 읽기 실패: {e}"
            
    # 4. 없다면? 이름이 비슷한 엑셀 파일이라도 찾아서 열어보기 (스마트 검색)
    excel_files = [f for f in current_files if f.endswith('.xlsx')]
    
    if len(excel_files) > 0:
        # 첫 번째 발견된 엑셀 파일 시도
        found_file = excel_files[0]
        try:
            return pd.read_excel(found_file, sheet_name=sheet_name), f"대체 파일 로드됨: {found_file}"
        except Exception as e:
            # 시트 이름이 틀렸을 수도 있음
            return None, f"'{found_file}'을 열었으나 '{sheet_name}' 시트가 없습니다. 시트 이름을 확인하세요."
            
    return None, "엑셀 파일 없음"

# 데이터 로드 시도
df, status_msg = load_data()

# --- 결과 처리 ---
if df is None:
    st.error("❌ 여전히 엑셀 파일을 열 수 없습니다.")
    
    # 디버깅용: 현재 서버에 어떤 파일이 있는지 사용자에게 보여줌
    st.warning("👇 [진단 결과] 서버(GitHub)에 있는 파일 목록은 아래와 같습니다.")
    
    current_files = os.listdir('.')
    st.code("\n".join(current_files))
    
    st.info(f"🔍 상태 메시지: {status_msg}")
    st.markdown("""
    **[해결 방법]**
    1. 위 검은 박스 안에 `.xlsx` 파일이 보이나요?
    2. 안 보인다면: **GitHub에 파일 업로드가 안 된 것**입니다. (Add file -> Upload files 다시 시도)
    3. 보인다면: 파일 안의 **'시트 이름(탭 이름)'**이 `별표 5의 제2호(전기자동차)`가 맞는지 확인해주세요.
    """)

else:
    # 파일 로드 성공 시 (경고 메시지가 있다면 작게 표시)
    if "대체 파일" in status_msg:
        st.caption(f"ℹ️ 참고: {status_msg}")

    # --- 여기서부터는 정상 작동 코드 ---
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
    
    models = []
    if selected_brand != "선택하세요":
        brand_cars = df[df.iloc[:, 0] == selected_brand]
        models = brand_cars.iloc[:, 1].dropna().astype(str).unique().tolist()
        models.sort(reverse=True)
    
    with col2:
        selected_model = st.selectbox("2. 모델명 선택", ["선택하세요"] + models)

    st.divider()

    if selected_brand != "선택하세요" and selected_model != "선택하세요":
        target_rows = df[
            (df.iloc[:, 0] == selected_brand) & 
            (df.iloc[:, 1] == selected_model)
        ]
        
        excluded_rows = []
        
        for _, row in target_rows.iterrows():
            exclusion_value = row.iloc[8]
            if pd.notna(exclusion_value) and str(exclusion_value).strip() != "":
                excluded_rows.append(row)

        if excluded_rows:
            st.error(f"🚨 [매입 제외 모델입니다] - {selected_model}")
            st.warning("⚠️ 아래 상세 사유를 확인하세요.")
            
            for i, row in enumerate(excluded_rows):
                ex_date = row.iloc[8]
                if isinstance(ex_date, datetime.datetime):
                    ex_date_str = ex_date.strftime("%Y-%m-%d")
                else:
                    ex_date_str = str(ex_date).split(" ")[0]

                with st.container():
                    st.markdown(f"**📌 상세 정보 #{i+1} (제외일: {ex_date_str})**")
                    headers = df.columns[2:8].tolist()
                    vals = row.iloc[2:8].tolist()
                    
                    info_dict = {}
                    for h, v in zip(headers, vals):
                        if isinstance(v, datetime.datetime):
                            v = v.strftime("%Y-%m-%d")
                        info_dict[h] = [v]
                    
                    st.table(pd.DataFrame(info_dict))
                    
        else:
            st.success(f"✅ [정상 등재 모델입니다] - {selected_model}")
            st.info("제외일자가 확인되지 않았습니다.")
