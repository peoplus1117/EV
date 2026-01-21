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

# --- ★ 핵심: 브랜드별 맞춤형 모델명 단순화 ---
def simplify_name(name, brand):
    if not isinstance(name, str): return str(name)
    
    # 1. 공통: 괄호 및 내용 제거
    name = re.sub(r'\(.*?\)', '', name).strip()
    upper_name = name.upper()

    # 2. 브랜드별 네이밍 전략 적용
    
    # [전략 A] 독일 3사: 첫 단어가 곧 모델명 (파워트레인 제거)
    # 예: "i4 eDrive40" -> "i4", "EQE 350+" -> "EQE"
    if brand in ["BMW", "메르세데스벤츠", "Audi", "폭스바겐", "볼보"]:
        # 공백으로 쪼개서 첫 번째 단어만 가져옴
        first_word = upper_name.split()[0]
        # 예외처리: Audi e-tron 같은 경우 유지, Q4 e-tron은 Q4로? 
        # 아우디는 'Q4', 'e-tron', 'Q8' 등으로 나뉨. 첫단어가 가장 깔끔함.
        return first_word

    # [전략 B] 테슬라: "Model" + "X" 까지 가져옴
    if brand == "테슬라":
        if upper_name.startswith("MODEL"):
            parts = upper_name.split()
            if len(parts) >= 2:
                return f"{parts[0]} {parts[1]}" # MODEL 3, MODEL Y
        return upper_name

    # [전략 C] 국산차 및 기타: 불필요한 수식어 제거
    remove_words = [
        "LONG RANGE", "LONGRANGE", "STANDARD", "PERFORMANCE", 
        "2WD", "4WD", "AWD", "RWD", "FWD", 
        "PRESTIGE", "EXCLUSIVE", "SIGNATURE", "GT-LINE", "GT", 
        "THE NEW", "ALL NEW", "PE", "ELECTRIC", "EV"
    ]
    
    for word in remove_words:
        if word == "EV": 
            # EV는 단독 단어일 때만 제거 (NIRO EV -> NIRO)
            upper_name = re.sub(r'\bEV\b', '', upper_name)
        else:
            upper_name = upper_name.replace(word, "")
            
    clean_name = upper_name.strip()
    if len(clean_name) < 2: return name.split()[0]
    return clean_name.strip()

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
            # 여기서는 원본만 로드하고, 단순화는 선택된 브랜드에 따라 실시간으로 처리
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
        # 브랜드 선택 (기본값: 선택하세요)
        selected_brand = st.selectbox("1. 업체명 선택", ["선택하세요"] + sorted_brands)
    
    display_models = []
    
    # [UX 개선] 업체 선택 시 모델명 리스트 즉시 생성
    if selected_brand != "선택하세요":
        brand_df = df[df.iloc[:, 0] == selected_brand]
        
        # (단순화된 이름, 원본 이름) 추출 -> 이때 브랜드를 넘겨줌
        pairs = []
        for idx, row in brand_df.iterrows():
            orig_name = str(row.iloc[1])
            simple = simplify_name(orig_name, selected_brand) # 브랜드별 로직 적용
            pairs.append((simple, orig_name))
        
        filtered_models = set()
        for simple_name, orig_name in pairs:
            orig_str = str(orig_name)
            # 상용차 필터
            if selected_brand == "현대자동차" and ("포터" in orig_str or "ST1" in orig_str): continue
            if selected_brand == "기아" and ("봉고" in orig_str): continue
            
            filtered_models.add(simple_name)
        
        # 오름차순 정렬
        display_models = sorted(list(filtered_models))
    
    with col2:
        # [UX 개선] 모델명 선택 박스에서 "선택하세요" 제거
        # 업체가 선택되었다면 바로 모델 리스트를 보여줌 (첫 번째 모델 자동 선택)
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
        
        # 선택된 단순 모델명에 해당하는 '모든 원본 모델' 찾기
        brand_df = df[df.iloc[:, 0] == selected_brand]
        target_rows = []
        
        for idx, row in brand_df.iterrows():
            orig_name = str(row.iloc[1])
            # 현재 선택된 브랜드의 로직으로 이름을 단순화해서 비교
            if simplify_name(orig_name, selected_brand) == selected_display_model:
                target_rows.append(row)
        
        # DataFrame으로 변환
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
