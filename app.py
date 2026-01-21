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
st.write("모델명 단순화 및 통합 검색 기능이 적용되었습니다.")

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

# --- ★ 핵심: 더 강력해진 단순화 로직 ---
def simplify_name(name, brand):
    if not isinstance(name, str): return str(name)
    
    # 1. 공통 전처리: 대문자 변환, 괄호 제거
    name = name.upper()
    name = re.sub(r'\(.*?\)', '', name).strip()

    # 2. [벤츠] 브랜드명 중복 제거 (가장 중요!)
    if brand == "메르세데스벤츠":
        # 모델명에 있는 'MERCEDES-BENZ' 또는 'MERCEDES' 삭제
        name = name.replace("MERCEDES-BENZ", "").replace("MERCEDES", "").strip()
        # 남은 것 중 첫 단어만 가져옴 (예: "EQE 350+" -> "EQE")
        if name: return name.split()[0]
        return name

    # 3. [기아/현대] EV 시리즈 및 아이오닉 강제 통합
    if brand in ["기아", "현대자동차"]:
        # EV + 숫자 패턴 찾기 (예: EV3, EV6, EV9)
        ev_match = re.match(r'(EV\s?\d+)', name)
        if ev_match:
            # EV3 GT-Line이든 뭐든 그냥 "EV3"로 리턴
            return ev_match.group(1).replace(" ", "")
        
        # 아이오닉 + 숫자 패턴 찾기
        ioniq_match = re.match(r'(IONIQ\s?\d+)', name.replace("아이오닉", "IONIQ"))
        if ioniq_match:
            return ioniq_match.group(1).replace(" ", "") # IONIQ5 로 통일

    # 4. [BMW/아우디/폭스바겐/볼보] 첫 단어 전략
    if brand in ["BMW", "Audi", "폭스바겐", "볼보", "폴스타"]:
        # i4 eDrive40 -> i4
        # Q4 e-tron -> Q4 (아우디는 보통 앞단어가 시리즈명)
        return name.split()[0]

    # 5. [테슬라] MODEL + 명칭 유지
    if brand == "테슬라":
        if name.startswith("MODEL"):
            parts = name.split()
            if len(parts) >= 2: return f"{parts[0]} {parts[1]}" # MODEL 3
        return name

    # 6. [기타 일반적인 경우] 잡다한 수식어 제거 후 첫 단어 사용
    remove_words = [
        "LONG RANGE", "LONGRANGE", "STANDARD", "PERFORMANCE", 
        "2WD", "4WD", "AWD", "RWD", "FWD", "GT-LINE", "GT", "PRO", "PRIME"
    ]
    for w in remove_words:
        name = name.replace(w, "")
    
    clean_name = name.strip()
    if not clean_name: return name # 다 지워졌으면 원본 리턴
    
    # 안전하게 첫 단어만 반환 (코란도 이모션 -> 코란도)
    return clean_name.split()[0]

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
            return pd.read_excel(file_to_load, sheet_name=sheet_name)
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
        
        # 단순화 로직 적용 및 필터링
        filtered_models = set()
        
        for idx, row in brand_df.iterrows():
            orig_name = str(row.iloc[1])
            simple_name = simplify_name(orig_name, selected_brand)
            
            # 상용차 필터링
            if selected_brand == "현대자동차" and ("포터" in orig_name or "ST1" in orig_name): continue
            if selected_brand == "기아" and ("봉고" in orig_name): continue
            
            filtered_models.add(simple_name)
        
        # 오름차순 정렬
        display_models = sorted(list(filtered_models))
    
    with col2:
        if selected_brand == "선택하세요":
            st.selectbox("2. 모델명 선택", ["업체를 먼저 선택하세요"], disabled=True)
            selected_display_model = None
        else:
            if display_models:
                selected_display_model = st.selectbox("2. 모델명 선택", display_models)
            else:
                st.selectbox("2. 모델명 선택", ["표시할 모델이 없습니다"], disabled=True)
                selected_display_model = None

    st.markdown("---") 

    # --- 결과 출력 ---
    if selected_brand != "선택하세요" and selected_display_model:
        
        # 선택된 단순 모델명과 일치하는 원본 데이터 찾기
        brand_df = df[df.iloc[:, 0] == selected_brand]
        target_rows = []
        
        for idx, row in brand_df.iterrows():
            orig_name = str(row.iloc[1])
            # 원본 이름을 똑같은 로직으로 단순화해서 비교
            if simplify_name(orig_name, selected_brand) == selected_display_model:
                target_rows.append(row)
        
        if target_rows:
            target_df = pd.DataFrame(target_rows)
            headers = df.columns[2:8].tolist()
            excluded_rows = [] 
            normal_rows = []

            for _, row in target_df.iterrows():
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
                    if isinstance(v, datetime.datetime): v_str = v.strftime("%Y-%m-%d")
                    else: v_str = format_value(v)
                    
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

        else:
            st.warning("해당 모델 데이터를 찾을 수 없습니다.")
