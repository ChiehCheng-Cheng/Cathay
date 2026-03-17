import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
import os

# 1. 讀取真實的條文資料集
df = pd.read_excel("faq_data.xlsx")
# 將標題與內容結合，作為模型比對的基準
corpus = [f"{row['Clause_Title']}: {row['Original_Text']}" for _, row in df.iterrows()]

# 2. 載入模型 (原始 vs 進化版)
model_org = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
model_tuned = SentenceTransformer('./tuned_cathay_minilm')

# 3. 事先對所有條文進行向量化 (這樣測試時會比較快)
print("⏳ 正在進行條文向量化，請稍候...")
corpus_embs_org = model_org.encode(corpus, convert_to_tensor=True)
corpus_embs_tuned = model_tuned.encode(corpus, convert_to_tensor=True)

def test_query_ranking():
    while True:
        user_query = input("\n請輸入測試問句 (輸入 'exit' 退出): ")
        if user_query.lower() == 'exit':
            break

        # 計算問題向量
        q_emb_org = model_org.encode(user_query, convert_to_tensor=True)
        q_emb_tuned = model_tuned.encode(user_query, convert_to_tensor=True)

        # 進行語義搜尋
        hits_org = util.semantic_search(q_emb_org, corpus_embs_org, top_k=3)[0]
        hits_tuned = util.semantic_search(q_emb_tuned, corpus_embs_tuned, top_k=3)[0]

        print(f"\n 測試問題：{user_query}")
        print("="*50)
        
        print("--- [原始模型] TOP 3 ---")
        for i, hit in enumerate(hits_org):
            print(f"{i+1}. 分數: {hit['score']:.4f} | {corpus[hit['corpus_id']][:60]}...")

        print("\n--- [進化版模型 (您微調的)] TOP 3 ---")
        for i, hit in enumerate(hits_tuned):
            print(f"{i+1}. 分數: {hit['score']:.4f} | {corpus[hit['corpus_id']][:60]}...")
        print("="*50)

if __name__ == "__main__":
    test_query_ranking()