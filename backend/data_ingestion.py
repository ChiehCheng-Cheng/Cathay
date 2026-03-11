import re
import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def process_insurance_pdf(file_path):
    print(f" 開始讀取 PDF 檔案: {file_path}")
    
    # 【新增防呆機制】：先檢查 PDF 檔案到底在不在
    if not os.path.exists(file_path):
        print(f" 嚴重錯誤：找不到檔案！請確認 {file_path} 路徑是否正確。")
        return
        
    # 1. 載入 PDF
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    full_text = "".join([p.page_content for p in pages])
    # (1) 移除頁首頁尾固定文字 (請根據 PDF 內容確認這串字是否完全一致)
    full_text = full_text.replace("國泰產險海外旅行不便保險條款", "")
    
    # (2) 移除單獨一行的頁碼 (例如：\n 43 \n)
    # 這能防止像「第六十一條」被數字切斷
    full_text = re.sub(r"\n\s*\d+\s*\n", "\n", full_text)
    
    # (3) 方案 B：壓縮換行符號
    # 將多個空行縮減為一個，讓標題與內容靠得更近，避免 AI 覺得內容不完整
    full_text = re.sub(r"\n+", "\n", full_text)

    # 2. 使用 Regex 根據「第 XX 條+條款名稱」分割文本
    pattern = r"(\n第[一二三四五六七八九十百]+條[^\n]+)"
    parts = re.split(pattern, full_text)

    documents = []
    for i in range(1, len(parts), 2):
        # 此時 parts[i] 會拿到 "第三十二條 班機延誤保險理賠文件"
        clause_full_title = parts[i].strip() 
        clause_content = parts[i+1] if i+1 < len(parts) else ""
        
        doc = Document(
            page_content=f"{clause_full_title}\n{clause_content.strip()}",
            metadata={
                "clause_id": clause_full_title, # 現在這裡有完整名稱了！
                "source": os.path.basename(file_path)
            }
        )
        documents.append(doc)

    print(f" 成功切分出 {len(documents)} 條保險條款！")
    print(" 開始下載並載入多語系 Embedding 模型 (只需下載一次)...")

    # 3. 初始化 Embedding 模型
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    print(" 模型載入完成！正在將文字轉換為向量並存入 FAISS 資料庫...")

    # 4. 存入 FAISS 並持久化
    os.makedirs("vector_store", exist_ok=True)  # 確保資料夾一定存在
    vector_db = FAISS.from_documents(documents, embeddings)
    vector_db.save_local("vector_store")
    
    print(f" 成功處理完畢！共計 {len(documents)} 條條款已存入 vector_store 資料夾。")

if __name__ == "__main__":
    # 確保路徑是相對 backend 目錄往外找 data
    process_insurance_pdf("../data/海外旅行不便險條款.pdf")