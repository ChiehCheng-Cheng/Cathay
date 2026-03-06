import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# 載入環境變數
load_dotenv()

# ==========================================
# 1. 系統初始化 (模型與向量庫)
# ==========================================
llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

faq_db = FAISS.load_local("faq_vector_store", embeddings, allow_dangerous_deserialization=True)
vector_db = FAISS.load_local("vector_store", embeddings, allow_dangerous_deserialization=True)


# ==========================================
# 2. 核心路由與問答邏輯 (Agentic Routing)
# ==========================================
def ask_insurance_question(user_input, qa_top_n=5, km_top_n=5):
    print(f"\n💬 收到使用者提問: {user_input}")
    
    # 💡 新增：定義全域 System Prompt，設定最高指導原則與人設
    system_prompt = (
        "## # Role\n"
        "您是「海外旅行不便保險專業顧問」。您的唯一任務是根據提供的保險條款，精確地為「您（使用者）」解答關於旅程取消、延誤、更改及各項補償保險的理賠諮詢。\n\n"

        "## # 語氣與人設\n"
        "- 必須始終以「您」稱呼使用者，嚴禁使用其他稱謂。\n"
        "- 語氣必須專業、嚴謹、客觀且條理分明。\n\n"

        "## # 核心原則\n"
        "1. **絕對忠於條文**：所有回答必須嚴格依據參考資料（Context）中的條款。若資料中未提及某種情況，請誠實告知，不得自行推測或引用外部其他保險公司的規則。\n"
        "2. **精準引用**：在回答每一個要點時，必須在句末使用 `` 格式標註來源編號（例如 `[cite: 30]`），以確保資訊可被查證。\n"
        "3. **主動提醒「不保事項」**：保險理賠的爭議通常在於排除條款。當您在說明承保範圍時，必須同時檢查並列出該項目的「特別不保事項」。\n\n"

        "## # 服務範圍（精確對應條款內容）\n"
        "### 1. 旅程不便類（旅遊延誤）\n"
        "- **旅程取消**：預定旅程開始前 7 日至開始前，因親屬死亡/病危、罷工、天災致必須取消。\n"
        "- **班機延誤**：定期航班延誤達 4 小時以上。延誤期間計算自預定出發時起，至實際出發或第一班替代班機出發時止。\n"
        "- **旅程更改**：海外旅行期間因罷工、戰爭、天災、親屬死亡、護照遺失或交通意外致必須更改行程。\n"
        "- **行李延誤與損失**：抵達目的地 6 小時後未領得行李；或因竊盜、強盜及業者處理失當致行李毀損滅失。\n"
        "- **旅行文件損失**：旅行文件因強盜、搶奪、竊盜或遺失之損失。\n\n"

        "### 2. 補償保險類\n"
        "- **改降與劫機**：改降非原定機場；遭受劫機事故按日給付（最高 10 日）。\n"
        "- **財務保障**：包含現金竊盜、信用卡盜用（掛失前 36 小時內）、行動電話被竊。\n"
        "- **特殊補償**：食品中毒、居家竊盜、租車事故、特殊活動或賽事取消。\n\n"

        "### 3. 急難救助類\n"
        "- **救助費用**：未成年子女送回、親友前往探視、醫療轉送、遺體運送、搜索救助費用。\n\n"
    )

    # 【第一步：從 QA 知識庫抓取 Top N 候選】
    faq_docs = faq_db.similarity_search(user_input, k=qa_top_n)
    
    candidates_text = ""
    for i, doc in enumerate(faq_docs):
        # 這裡提取給 LLM 裁判看的資料
        c_id = doc.metadata.get('clause_id', '未知條款')
        c_text = doc.metadata.get('original_text', '')
        candidates_text += f"[候選 {i+1}]\n條款編號：{c_id}\n條文內容：{c_text}\n\n"

    # 【第二步：LLM 裁判 Prompt (QA 路由層)】
    routing_prompt = f"""
    您是一位嚴格的保險理賠審核員。
    請閱讀以下「使用者問題」，以及系統檢索出的 {qa_top_n} 筆「候選條款」。

    使用者問題：{user_input}

    候選條款：
    {candidates_text}

    任務：
    請判斷這 {qa_top_n} 筆候選條款中，是否有一筆能「直接且完整並金準」地回答使用者的問題。
    - 如果有，請「只輸出該候選的數字編號」（例如：1、2 、 3、4或5），絕對不要輸出任何解釋文字！
    - 如果這 {qa_top_n} 筆都無法精準回答，或者使用者的問題需要綜合多項條款才能回答，請「只輸出大寫英文字母 NONE」。
    """

    # 【第三步：呼叫 LLM 進行判定】
    decision = llm.invoke([
            ("system", system_prompt),
            ("human", routing_prompt)
    ]).content.strip().upper()
    print(f"🧠 QA 路由判定原始輸出: {decision}")

    # 【第四步：解析 LLM 決策並分流】
    match = re.search(r'\d+', decision)
    
    if "NONE" not in decision and match:
        index = int(match.group()) - 1
        if 0 <= index < len(faq_docs):
            selected_doc = faq_docs[index]
            print(f"🎯 判定結果：命中 QA 知識庫！(選中候選 {index + 1})")
            
            # 💡 修改點 2：這裡維持您的好設計，僅輸出 original_text，確保不會有 ID 和 Title 混入答案中
            return {
                "answer": selected_doc.metadata.get("original_text", "無原文資料"),
                "source": selected_doc.metadata.get("clause_id", "單一條款"),
                "type": "QA_EXACT"
            }

    # 【第五步：若 QA 未命中，進入 KM 知識庫 (篩選與生成模式)】
    print("🤖 判定結果：QA 未命中，進入 KM 知識庫進行 Top N 篩選與潤飾生成...")
    
    # 💡 修改點 3：手動從 KM 庫抓取 Top N
    km_docs = vector_db.similarity_search(user_input, k=km_top_n)
    
    km_candidates_text = ""
    for i, doc in enumerate(km_docs):
        km_candidates_text += f"[參考條款 {i+1}]\n{doc.page_content}\n\n"

    # 💡 修改點 4：重新設計 KM Prompt，明確要求 LLM 先「選/評估」，再「潤飾生成」
    km_generation_prompt = f"""
    您是一位專業的保險理賠顧問。
    請閱讀以下「使用者問題」，以及系統從知識庫檢索出的 Top {km_top_n} 筆「參考條款」。

    使用者問題：{user_input}

    參考條款：
    {km_candidates_text}

    任務指令：
    1. 篩選與評估：請先評估上述「參考條款」中，是否有符合並能回答使用者問題的內容。
    2. 潤飾與生成：如果有符合的內容，請根據這些內容進行潤飾，生成通順、專業且易懂的理賠回覆。請在回答中自然地提及是依據哪些條款。
    3. 拒絕回答：如果這 {km_top_n} 筆參考條款「完全無法」回答使用者的問題，請直接回覆：「很抱歉，根據目前的保險條款知識庫，我無法準確回答您的問題。」，絕對不要自行編造答案。
    
    ## # 語氣與人設規範
    - 必須始終以「您」稱呼使用者，嚴禁使用其他稱謂。
    - 語氣必須專業、嚴謹、客觀且條理分明。

    ## # 引用格式規範（強制指令）
    - **禁止使用 或任何方括號形式的標記**。
    - **必須使用自然語言嵌入語句中**，格式為：「依據海外旅行不便險第 XX 條款」。
    - **多項引用**格式為：「依據海外旅行不便險第 XX 跟第 YY 條款」。
     **總結引用（固定最後一行）**：**必須在回答的最末尾，獨立一行寫出**本次回答參考的所有條款，格式為「依據海外旅行不便險第 XX 跟第 YY 條款」或「依據海外旅行不便險第 XX 條款」。

    """

    # 呼叫 LLM 進行最終生成
    km_answer = llm.invoke([
            ("system", system_prompt),
            ("human", km_generation_prompt)
    ]).content.strip()

    # 擷取來源 (簡單抓取第一個文件作為參考，若需更複雜來源追蹤可再擴充)
    km_source = km_docs[0].metadata.get("clause_id", "多項條款彙整") if km_docs else "系統生成"

    return {
        "answer": km_answer,
        "source": km_source,
        "type": "KM_GENERATIVE"
    }