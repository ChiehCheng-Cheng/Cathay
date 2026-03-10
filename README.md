國泰產險智能理賠助手：基於雙層 RAG 架構與 Llama-3.3-70B 之實作

-Project Overview

本專案開發一套具備高效檢索與精準生成的「智能理賠諮詢系統」。採用 RAG 架構，結合Regex 切分技術 與 Llama-3.3-70B 大語言模型。
本系統具備雙層路徑決策邏輯，能平衡日常對話的親和力與理賠建議的法律嚴謹性。


-技術核心亮點 (Technical Highlights)

雙層檢索架構 ：
QA 層（高精確度）：針對常見問題進行優先匹配。
KM 層：針對QA無法回答內容進行深度語義搜尋。


資料工程：利用正則表達式（Regex）對 PDF 進行結構化解析，確保 Chunk 邊界完整保留法律條文的邏輯單元。
LLM 智慧審核：模型不僅負責生成，更擔任審核者，針對檢索結果進行邏輯一致性審查，徹底杜絕 AI 幻覺。
地端隱私部署：選用開放權重模型 Llama-3.3-70B，支援私有化部署，確保敏感資料符合金融合規要求。

-系統架構 

1. 資料預處理

1.PDF 解析：提取非結構化文本，移除多餘雜訊（如頁碼）。
2.Regex 邏輯切分：按「條」進行切塊，並自動加入標題等 Metadata。
3.向量化與索引：
Model: paraphrase-multilingual-MiniLM-L12-v2 (多語系優化)。
Vector DB: FAISS (IndexFlatL2)。

2.雙層檢索層

1. 意圖判別**：LLM 識別輸入為社交或理賠需求。
2. QA 檢索與審核**：比對 FAQ 庫，若LLM判斷 Top-N 結果能完整解答則直接輸出。
3. KM 檢索層：若 QA 未命中，則啟動 KM 檢索，若LLM判斷 Top-N 結果能符合並能回答使用者問題的內容，則輸出並註明來源。


-專案使用工具

| 類別       | 工具 / 模型      | 關鍵選擇原因                                   |
| LLM        | Llama-3.3-70B   | 具備強大邏輯推理與地端部署能力。                 |
| Embedding  | MiniLM-L12-v2   | 輕量化、低延遲，且對繁體中文語義對齊有優異表現。  |
| Vector DB  | FAISS           | 採用暴力檢索 (FlatL2) 確保零精確度損失。        |
| Frontend   | Vue.js          | 建構使用者對話介面，提升用戶交互體驗。           |
| Backend    | Node.js / Python| 實現前後端分離與高效的 RAG API 串接。           |


-程式碼目錄結構 
CATHAY/
├── backend/                # 後端核心：RAG 邏輯與 API 實作
│   ├── faq_ingestion.py    # FAQ 資料處理與向量化腳本
│   ├── pdf_to_excel.py     # PDF 條款資料清洗與預處理工具
│   ├── inspect_db.py       # 向量資料庫檢查與驗證工具
│   ├── rag_chains.py       # 核心邏輯：QA 檢索、KM 檢索與 LLM 決策
│   └──main.py             # 後端 API 服務入口 (FastAPI/Flask)
│    
│
├── frontend/               # 前端介面：基於 Vue 3 + Vite 的對話系統
│   ├── src/                # 前端原始碼
│   ├── public/             # 靜態資源檔案
│   ├── index.html          # SPA 入口頁面
│   ├── package.json        # 前端相依套件定義
│   ├── vite.config.js      # Vite 建構配置
│   └── tailwind.config.js  # Tailwind CSS 樣式配置
│
├── data/                   # 原始資料層
│   └── 海外旅行不便險條款.pdf # 專案核心資料源
│
├── vector_store/           # 持久化向量資料庫 (FAISS Index)
│   ├── index.faiss         # 向量檢索索引檔案
│   └── index.pkl           # 結構化 Metadata 儲存檔案
│
├── .gitignore              # 排除敏感檔案與環境變數
└── README.md               # 專案總體說明文件
