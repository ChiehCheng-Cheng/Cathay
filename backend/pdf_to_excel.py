import re
import os
import pandas as pd
from langchain_community.document_loaders import PyMuPDFLoader

def extract_clauses_to_excel(pdf_path, output_excel):
    print(f"⏳ 正在讀取並解析 PDF: {pdf_path}...")
    
    # 1. 載入並初步清洗文字
    loader = PyMuPDFLoader(pdf_path)
    pages = loader.load()
    full_text = "\n" + "\n".join([p.page_content for p in pages]) # 開頭加換行方便 Regex 偵測
    
    # 清洗雜訊：移除頁碼與多餘換行
    full_text = re.sub(r"\n\s*\d+\s*\n", "\n", full_text) 
    full_text = re.sub(r"\n+", "\n", full_text)
    
    # 2. 定義切割模式：捕捉「第XX條」與其後的「標題」
    # 模式解釋：(第XX條) + 空格 + (直到換行前的所有字作為標題)
    pattern = r"(\n第[一二三四五六七八九十百]+條)\s+([^\n]+)"
    
    # 使用 re.finditer 找出所有條文的起點與位置
    matches = list(re.finditer(pattern, full_text))
    
    data = []
    for i in range(len(matches)):
        # 獲取當前條款的 ID 與 標題
        clause_id = matches[i].group(1).strip()    # 例如：第二十七條 [cite: 2]
        clause_title = matches[i].group(2).strip() # 例如：旅程取消保險承保範圍 [cite: 2]
        
        # 獲取條款內容 (當前匹配點到下一個匹配點之間的文字)
        start_pos = matches[i].end()
        end_pos = matches[i+1].start() if i + 1 < len(matches) else len(full_text)
        original_text = full_text[start_pos:end_pos].strip()
        
        data.append({
            "Clause_ID": clause_id,
            "Clause_Title": clause_title,
            "Original_Text": original_text
        })

    # 3. 轉換為 DataFrame 並匯出 Excel
    df = pd.DataFrame(data)
    df.to_excel(output_excel, index=False)
    
    print(f"🎉 成功提取 {len(df)} 筆條文至 {output_excel}！")

if __name__ == "__main__":
    pdf_file = "../data/海外旅行不便險條款.pdf"
    output_file = "faq_data.xlsx"
    extract_clauses_to_excel(pdf_file, output_file)