from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# 1. 載入跟之前一樣的 Embedding 模型
embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")

# 2. 讀取您已經產生的向量庫
# 注意：路徑請根據您執行指令的位置調整，如果在 backend 下就用 "vector_store"
vector_db = FAISS.load_local("vector_store", embeddings, allow_dangerous_deserialization=True)

# 3. 提取所有的文件內容與 Metadata
# FAISS 將文件存在 docstore 中
content_dict = vector_db.docstore._dict

print(f"目前向量庫中共有 {len(content_dict)} 個 Chunk。\n")

# 4. 列出前 5 個 Chunk 來檢查格式
for i, (doc_id, doc) in enumerate(content_dict.items()):
    if i < 56:  # 只看前 5 筆，免得洗版
        print(f"--- Chunk {i+1} ---")
        print(f"【Metadata】: {doc.metadata}")
        print(f"【內容摘要】: {doc.page_content[:30]}...") # 只印前 100 字
        print("\n")