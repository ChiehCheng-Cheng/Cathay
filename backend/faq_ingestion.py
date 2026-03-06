import pandas as pd
import os
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def ingest_faq_excel(file_path):
    print(f"⏳ 正在讀取 QA Excel: {file_path}")
    df = pd.read_excel(file_path)
    
    documents = []
    for _, row in df.iterrows():
        # 這裡將 ID、標題、全文 合併，讓它們都被向量化
        # 使用標籤（Label）區分欄位，有助於 Embedding 模型理解語義關係
        combined_content = f"條號：{row['Clause_ID']}\n標題：{row['Clause_Title']}\n條文內容：{row['Original_Text']}"
        
        doc = Document(
            page_content=combined_content, # 這個字串會被轉換為向量
            metadata={
                "clause_id": row['Clause_ID'],     # 結構化儲存
                "clause_title": row['Clause_Title'], 
                "original_text": row['Original_Text'], # QA層可直接從這抓
                "source": "海外旅行不便險條款.pdf"
            }
        )
        documents.append(doc)
    
    # 使用與 KM 層相同的 Embedding 模型
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    vector_db = FAISS.from_documents(documents, embeddings)
    vector_db.save_local("faq_vector_store")
    print(f"🎉 QA 向量庫已建立，共計 {len(documents)} 筆。")

if __name__ == "__main__":
    ingest_faq_excel("faq_data.xlsx")