// 定義前端送給後端的請求格式
export interface ChatRequest {
  message: string;
}

// 定義後端回傳的格式 (對應 FastAPI 的 ChatResponse)
export interface ChatResponse {
  answer: string;
  status: string;
  type?: string;   //  新增：接收後端傳來的 QA_EXACT 或 KM_GENERATIVE
  source?: string; //  新增：(可選) 接收來源條款編號
}

// 定義前端聊天室畫面的訊息狀態
export interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  type?: string;   //  新增：用來判斷是否在畫面上顯示「紅字標註」
}