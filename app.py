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
    </style>
    """, unsafe_allow_html=True)

st.markdown("### 2026 친환경차(전기차) 등재 현황")
st.write("2026년 효율 기준 변경에 따른 제외/정상 여부를 확인하세요.")

# --- 기준표 ---
with st.expander("ℹ️ [기준] 2026년 전기차 에너지 소비효율 기준", expanded=False):
    ref_data = {
        "구분 (차급)": ["초소·경·소형", "중형", "대형"],
        "기준 (km/kWh)": ["5.0 이상", "4.2 이상", "3.4 이상"]
    }
    st.table(pd.DataFrame(ref_data).set_index("구분 (차급)"))

st.divider()

# --- 포맷팅 함수 ---
def format_value(val):
    if isinstance(val, float): return f"{val:.1f}"
    if isinstance(val, datetime.datetime): return val.strftime("%Y-%m-%d")
    return val

# --- ★ 핵심: 모델명 '과격한' 단순화 함수 ---
def simplify_name(name):
    if not isinstance(name, str): return str(name)
    
    # 1. 괄호 제거
    name = re.sub(r'\(.*?\)', '', name)
    
    # 2. 불필요한 수식어 제거 (롱레인지, 4WD, 스탠다드 등)
    #    목록을 계속 추가해서 걸러낼 수 있습니다.
    remove_words = [
        "LONG RANGE", "LONGRANGE", "STANDARD", "PERFORMANCE", 
        "2WD", "4WD", "AWD", "RWD", "FWD", 
        "PRESTIGE", "EXCLUSIVE", "SIGNATURE", "GT-LINE", "GT", 
        "THE NEW", "ALL NEW", "PE", "ELECTRIC", "EV"
    ]
    
    upper_name = name.upper()
    for word in remove_words:
        # 단어 단위로 정확히 일치할 때만 제거 (EV6의 EV는 지우면 안됨)
        # 단순히 replace하면 EV6 -> 6이 되어버리므로 주의
        if word == "EV": 
            # EV는 단독으로 쓰일 때만 제거 (NIRO EV -> NIRO)
            upper_name = re.sub(r'\bEV\b', '', upper_name)
        else:
            upper_name = upper_name.replace(word, "")
            
    # 3. 공백 및 특수문자 정리
    clean_name = upper_name.strip()
    
    # 4. 너무 짧아졌거나 이상하면 원본 앞단어만 사용 (안전장치)
    if len(clean_name) < 2:
        return name.split()[0]
        
    return clean_name.strip()

# 검색용 키워드 생성 (공백 제거 버전)
def make_search_key(name):
    return simplify_name(name).replace(" ", "")

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
            # 검색용 단순화된 이름 컬럼 미리 생성
            df['단순_모델명'] = df.iloc[:, 1].astype(str).apply(simplify_name)
            df['검색_키'] = df['단순_모델명'].str.replace(" ", "")
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
        
        # (단순화된 이름, 원본 이름) 추출
        pairs = brand_df[['단순_모델명', brand_df.columns[1]]].values.tolist()
        
        # ★ 상용차 필터링 로직 (이름으로 판단)
        filtered_models = set()
        
        for simple_name, orig_name in pairs:
            orig_str = str(orig_name)
            
            # 현대: 포터, ST1 제거
            if selected_brand == "현대자동차":
                if "포터" in orig_str or "ST1" in orig_str: continue
            
            # 기아: 봉고 제거
            elif selected_brand == "기아":
                if "봉고" in orig_str: continue
            
            # 필터 통과한 것만 추가
            filtered_models.add(simple_name)
        
        # 오름차순 정렬 (ㄱ -> ㅎ)
        display_models = sorted(list(filtered_models))
    
    with col2:
        selected_display_model = st.selectbox("2. 모델명 선택", ["선택하세요"] + display_models)

    st.markdown("---") 

    if selected_brand != "선택하세요" and selected_display_model != "선택하세요":
        
        # 선택된 '단순 모델명'을 가진 모든 원본 차량 검색
        # 예: 선택은 'IONIQ 5' -> 검색 결과는 'IONIQ 5 Long Range', 'IONIQ 5 Standard' 모두 포함
        search_key_selected = selected_display_model.replace(" ", "")
        
        target_rows = df[
            (df.iloc[:, 0] == selected_brand) & 
            (df['검색_키'] == search_key_selected)
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
