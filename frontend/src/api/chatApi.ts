import axios from 'axios';
import type { ChatRequest, ChatResponse } from '../types/chatTypes';

// 建立 Axios 實體
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api', 
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, 
});

// 封裝發送對話的函式
export const sendMessageToAPI = async (data: ChatRequest): Promise<ChatResponse> => {
  try {
    const response = await apiClient.post<ChatResponse>('/chat', data);
    return response.data;
  } catch (error) {
    console.error('API 請求失敗:', error);
    throw new Error('無法連線至伺服器，請確認後端已啟動或稍後再試。');
  }
};