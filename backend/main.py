import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from rag_chains import ask_insurance_question  # 引入您剛才調校好的核心邏輯

# 1. 初始化 FastAPI 應用程式
app = FastAPI(
    title="國泰產險旅遊不便險 RAG 助手",
    description="基於 LangChain + Groq + FAISS 的保險條款諮詢系統"
)

# 2. CORS 處理：允許您的 Vue 3 前端 (預設為 5173 埠) 進行跨來源請求
origins = [
    "http://localhost:5173",  # Vite 預設埠
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],      # 允許所有方法 (GET, POST 等)
    allow_headers=["*"],      # 允許所有標頭
)

# 3. 定義 API 請求模型
class ChatRequest(BaseModel):
    message: str

# 4.定義 API 回應模型 (新增 type 與 source)
class ChatResponse(BaseModel):
    answer: str
    status: str = "success"
    type: Optional[str] = None   # 用來判斷是否為 KM_GENERATIVE
    source: Optional[str] = None # 用來傳遞參考的條款編號

# 5. 建立 /api/chat 接口
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    接收前端問句，呼叫 RAG 鏈，並回傳帶有條號標註的答案。
    """
    try:
        # 取得前端傳來的訊息
        user_input = request.message
        
        if not user_input:
            raise HTTPException(status_code=400, detail="訊息內容不能為空")

        # 呼叫 rag_chains.py 中的問答函式
        raw_result = ask_insurance_question(user_input)
        
        # 從 LangChain 回傳的字典中萃取出答案、類型與來源
        if isinstance(raw_result, dict) and "answer" in raw_result:
            final_answer = raw_result["answer"]
            res_type = raw_result.get("type", "")     # 取得 QA_EXACT 或 KM_GENERATIVE
            res_source = raw_result.get("source", "") # 取得來源條款
        else:
            final_answer = str(raw_result)
            res_type = ""
            res_source = ""
        
        # 將所有資訊打包回傳給前端
        return ChatResponse(
            answer=final_answer, 
            type=res_type, 
            source=res_source
        )

    except Exception as e:
        # 錯誤處理：若 API Key 失效或模型報錯，回傳 500 錯誤
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="系統暫時無法處理您的請求，請稍後再試")

# 6. 健康檢查接口 (確認伺服器運作中)
@app.get("/health")
async def health_check():
    return {"status": "online"}