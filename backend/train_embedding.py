import json
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
from tqdm import tqdm

# 1. 載入原始模型與設定路徑
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
TRAIN_DATA_PATH = 'insurance_train_data.jsonl'
OUTPUT_MODEL_PATH = 'tuned_cathay_minilm'

# 2. 讀取 JSONL 資料集
train_examples = []
print(f" 正在從 {TRAIN_DATA_PATH} 讀取訓練資料...")
with open(TRAIN_DATA_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        # InputExample 需要配對：[問題, 正確條文]
        train_examples.append(InputExample(texts=[data['query'], data['positive_document']]))

print(f" 成功載入 {len(train_examples)} 筆訓練樣本。")

# 3. 初始化模型與 DataLoader
model = SentenceTransformer(MODEL_NAME)
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)

# 4. 定義損失函數：MultipleNegativesRankingLoss
# 這是 RAG 領域最推薦的微調方法，能有效提升相似度排序 [cite: 2026-03-15]
train_loss = losses.MultipleNegativesRankingLoss(model=model)

# 5. 開始執行微調訓練 (Fine-tuning)
print(" 啟動模型微調中，這可能需要幾分鐘...")
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=3,           # 建議 3-5 個 Epoch 即可達到理想效果
    warmup_steps=100,
    show_progress_bar=True,
    output_path=OUTPUT_MODEL_PATH
)

print(f"✨ 恭喜！微調模型已儲存至：{OUTPUT_MODEL_PATH}")