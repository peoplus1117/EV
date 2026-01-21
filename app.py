import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

class CarCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("2026 친환경차(전기차) 제외 여부 확인기")
        self.root.geometry("600x500")
        
        # 데이터 저장 변수
        self.df = None
        
        # 1. 파일 선택 영역
        self.file_frame = tk.Frame(root, pady=10)
        self.file_frame.pack(fill="x", padx=10)
        
        self.btn_load = tk.Button(self.file_frame, text="📂 엑셀 파일 불러오기", command=self.load_file, bg="#ddd")
        self.btn_load.pack(side="left")
        
        self.lbl_file = tk.Label(self.file_frame, text="파일을 선택해주세요", fg="gray")
        self.lbl_file.pack(side="left", padx=10)

        # 2. 선택 영역 (업체 -> 모델)
        self.select_frame = tk.Frame(root, pady=10)
        self.select_frame.pack(fill="x", padx=10)

        tk.Label(self.select_frame, text="1. 업체명:").grid(row=0, column=0, sticky="w")
        self.combo_brand = ttk.Combobox(self.select_frame, state="readonly", width=30)
        self.combo_brand.grid(row=0, column=1, padx=5, pady=5)
        self.combo_brand.bind("<<ComboboxSelected>>", self.on_brand_change)

        tk.Label(self.select_frame, text="2. 모델명:").grid(row=1, column=0, sticky="w")
        self.combo_model = ttk.Combobox(self.select_frame, state="disabled", width=30)
        self.combo_model.grid(row=1, column=1, padx=5, pady=5)
        self.combo_model.bind("<<ComboboxSelected>>", self.on_model_change)

        # 3. 결과 출력 영역
        self.result_frame = tk.LabelFrame(root, text="조회 결과", padx=10, pady=10)
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.txt_result = tk.Text(self.result_frame, height=15, state="disabled", font=("맑은 고딕", 10))
        self.txt_result.pack(fill="both", expand=True)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
        
        self.lbl_file.config(text=os.path.basename(file_path), fg="black")
        self.log("파일을 읽는 중입니다...")
        
        try:
            # 시트 이름 설정
            sheet_name = "별표 5의 제2호(전기자동차)"
            self.df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # 업체명 목록 설정 (요청하신 순서)
            preferred_order = [
                "현대자동차", "기아", "한국GM", "르노코리아", "케이지모빌리티", 
                "BMW", "메르세데스벤츠", "Audi", "폭스바겐", "볼보", 
                "테슬라", "폴스타", "포르쉐코리아", "BYD", "Lexus"
            ]
            
            # 실제 데이터에 있는 업체만 추출 (A열: index 0)
            existing_brands = self.df.iloc[:, 0].dropna().astype(str).unique().tolist()
            
            # 순서 정렬
            sorted_brands = [b for b in preferred_order if b in existing_brands]
            # 목록에 없는 나머지 브랜드 추가
            sorted_brands += [b for b in existing_brands if b not in preferred_order]
            
            self.combo_brand['values'] = sorted_brands
            self.combo_brand.set("업체를 선택하세요")
            self.combo_model.set("")
            self.combo_model['state'] = 'disabled'
            
            self.log("✅ 파일 로드 완료! 업체를 선택해주세요.")
            
        except Exception as e:
            messagebox.showerror("오류", f"파일을 읽을 수 없습니다.\n{e}")
            self.log("❌ 파일 로드 실패")

    def on_brand_change(self, event):
        if self.df is None:
            return
        
        selected_brand = self.combo_brand.get()
        
        # 해당 업체의 모델명 추출 (B열: index 1)
        brand_cars = self.df[self.df.iloc[:, 0] == selected_brand]
        models = brand_cars.iloc[:, 1].dropna().astype(str).unique().tolist()
        
        self.combo_model['values'] = models
        self.combo_model.set("모델을 선택하세요")
        self.combo_model['state'] = 'readonly'
        self.log(f"👉 [{selected_brand}] 선택됨. 모델을 선택하세요.")

    def on_model_change(self, event):
        if self.df is None:
            return
            
        selected_brand = self.combo_brand.get()
        selected_model = self.combo_model.get()
        
        # 데이터 조회
        target_rows = self.df[
            (self.df.iloc[:, 0] == selected_brand) & 
            (self.df.iloc[:, 1] == selected_model)
        ]
        
        self.txt_result.config(state="normal")
        self.txt_result.delete(1.0, tk.END) # 기존 내용 삭제
        
        found_exclusion = False
        
        self.txt_result.insert(tk.END, f"🔍 조회 모델: [{selected_brand}] {selected_model}\n")
        self.txt_result.insert(tk.END, "-"*50 + "\n")
        
        for _, row in target_rows.iterrows():
            # I열 (index 8) 확인 -> 제외일자
            exclusion_value = row.iloc[8]
            
            # 제외일자가 있으면 (비어있지 않으면)
            if pd.notna(exclusion_value) and str(exclusion_value).strip() != "":
                found_exclusion = True
                
                # C~H열 (index 2~7) 정보 가져오기
                info_values = row.iloc[2:8].tolist()
                # 보기 좋게 포맷팅
                info_str = " / ".join([str(val) for val in info_values])
                
                self.txt_result.insert(tk.END, "🚨 [결과: 매입 제외 모델]\n", "warning")
                self.txt_result.insert(tk.END, f"📅 제외일자: {exclusion_value}\n")
                self.txt_result.insert(tk.END, f"ℹ️ 상세정보: {info_str}\n\n")
        
        if not found_exclusion:
            self.txt_result.insert(tk.END, "✅ [결과: 정상 등재 모델]\n", "safe")
            self.txt_result.insert(tk.END, "   (제외일자가 확인되지 않았습니다.)\n")
            
        # 텍스트 색상 태그 설정
        self.txt_result.tag_config("warning", foreground="red", font=("맑은 고딕", 11, "bold"))
        self.txt_result.tag_config("safe", foreground="blue", font=("맑은 고딕", 11, "bold"))
        
        self.txt_result.config(state="disabled")

    def log(self, msg):
        self.txt_result.config(state="normal")
        self.txt_result.delete(1.0, tk.END)
        self.txt_result.insert(tk.END, msg)
        self.txt_result.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = CarCheckerApp(root)
    root.mainloop()