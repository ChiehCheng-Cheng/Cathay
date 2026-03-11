<script setup lang="ts">
import { ref, nextTick } from 'vue';
import MarkdownIt from 'markdown-it'; //  新增：引入 Markdown 解析器
import { sendMessageToAPI } from './api/chatApi'; 
import type { Message } from './types/chatTypes'; 

//  新增：初始化與設定 Markdown 解析器
const md = new MarkdownIt({
  linkify: true, // 自動識別純文字網址並轉為連結
  breaks: true   // 支援換行符號
});

// 設定讓連結都在新分頁開啟 (target="_blank") 
const defaultRender = md.renderer.rules.link_open || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options);
};

md.renderer.rules.link_open = function(tokens, idx, options, env, self) {
  tokens[idx].attrPush(['target', '_blank']); // 新分頁開啟
  tokens[idx].attrPush(['rel', 'noopener noreferrer']); // 安全性設定
  return defaultRender(tokens, idx, options, env, self);
};
// ----------------------------------------------------

const userInput = ref('');
const isLoading = ref(false);
const chatContainer = ref<HTMLElement | null>(null);

const messages = ref<Message[]>([
  {
    id: Date.now(),
    role: 'assistant',
    content: '您好！我是國泰產險旅遊不便險 AI 助手。請問有什麼我可以協助您的？例如：「班機延誤多久可以理賠？」',
  },
]);

const scrollToBottom = async () => {
  await nextTick();
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

const handleSend = async () => {
  const text = userInput.value.trim();
  if (!text) return;

  messages.value.push({ id: Date.now(), role: 'user', content: text });
  userInput.value = '';
  isLoading.value = true;
  scrollToBottom();

  try {
    const response = await sendMessageToAPI({ message: text });
    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: response.answer,
      type: response.type, 
    });
  } catch (error: any) {
    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: error.message || '發生未知錯誤，請稍後再試。',
    });
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
};
</script>

<template>
  <div class="flex flex-col h-screen w-full font-sans bg-white">
    
    <header class="bg-[#00a850] text-white p-4 text-center shadow-md z-10">
      <h1 class="text-xl font-bold">國泰產險智能助理阿發</h1>
    </header>

    <main class="flex-1 overflow-y-auto p-4 bg-gray-50 space-y-4" ref="chatContainer">
      <div 
        v-for="msg in messages" 
        :key="msg.id" 
        class="flex items-start gap-3"
        :class="msg.role === 'user' ? 'flex-row-reverse' : ''"
      >
        <div v-if="msg.role === 'user'" class="flex items-center justify-center w-10 h-10 rounded-full bg-[#00a850] text-white font-bold shrink-0">
          您
        </div>
        <img v-else src="/smart_alpha_survey.png" alt="AI" class="w-10 h-10 rounded-full object-cover shrink-0 border border-gray-200 shadow-sm" />
        
        <div 
          class="p-3 rounded-lg max-w-[70%] shadow-sm leading-relaxed relative markdown-body"
          :class="msg.role === 'user' ? 'bg-[#e6f7ed] text-gray-800' : 'bg-white text-gray-800'"
        >
          <div v-html="md.render(msg.content)"></div>

          <div 
            v-if="msg.type === 'KM_GENERATIVE'" 
            style="color: red; font-size: 0.8em; margin-top: 8px; border-top: 1px solid #fee2e2; padding-top: 4px;"
          >
            ⚠ 答案由GPT生成
          </div>
        </div>
      </div>
      
      <div v-if="isLoading" class="flex items-start gap-3">
        <img src="/smart_alpha_survey.png" alt="AI" class="w-10 h-10 rounded-full object-cover shrink-0 border border-gray-200 shadow-sm animate-pulse" />
        <div class="p-3 rounded-lg bg-white shadow-sm text-gray-500 italic">
          檢索條款與思考中...
        </div>
      </div>
    </main>

    <footer class="flex p-4 bg-white border-t border-gray-200">
      <input 
        v-model="userInput" 
        @keyup.enter="handleSend"
        type="text" 
        placeholder="請輸入保險相關問題..." 
        :disabled="isLoading"
        class="flex-1 p-3 border border-gray-300 rounded-md outline-none focus:border-[#00a850] focus:ring-1 focus:ring-[#00a850] transition-all disabled:bg-gray-100"
      />
      <button 
        @click="handleSend" 
        :disabled="isLoading || !userInput.trim()"
        class="ml-3 px-6 py-3 bg-[#00a850] text-white rounded-md font-medium hover:bg-[#008c43] disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        發送
      </button>
    </footer>
  </div>
</template>

<style scoped>
:deep(.markdown-body a) {
  color: #0070cc;
  text-decoration: underline;
  font-weight: 500;
  transition: color 0.2s;
}

:deep(.markdown-body a:hover) {
  color: #0056b3;
}

:deep(.markdown-body p) {
  margin-bottom: 0.5rem;
}

:deep(.markdown-body p:last-child) {
  margin-bottom: 0;
}
</style>