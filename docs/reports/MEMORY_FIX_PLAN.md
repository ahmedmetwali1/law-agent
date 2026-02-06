# خطة إصلاح ذاكرة الوكيل (Memory Fix Plan)

## المشكلة الحالية (Diagnosis)
1.  **فقدان الذاكرة (Amnesia):** عند إنشاء `create_graph_agent` في `ChatService.process_message`، يتم تمرير رسالة المستخدم الحالية *فقط*.
2.  **تجاهل الأرشيف:** لا يتم استدعاء أي دالة لقراءة جدول `ai_chat_messages` وحقنه في `AgentState`.
3.  **النتيجة:** الوكيل يبدأ كل مرة "نظيفاً" (Clean Slate) ولا يعرف ماذا حدث سابقاً.

## الحل المقترح (Strategy)

سنقوم بتعديل دالة `create_graph_agent` لتستقبل `session_id` وتقوم هي (أو المستدعي) بجلب التاريخ من قاعدة البيانات وتحويله إلى كائنات `LangChain Message`.

### 1. مخطط قاعدة البيانات (Schema Verification)
جدول الرسائل الحالي (`ai_chat_messages`) يحتوي على:
-   `role` (user/assistant)
-   `content` (text)
-   `metadata` (jsonb) - **هام:** يجب التأكد من أنه يخزن مخرجات الأدوات ()

### 2. الكود الجديد (Implementation)

#### أ. دالة استرجاع التاريخ (`fetch_history`)
سنضيف دالة جديدة في `api/services/chat_service.py` تقوم بجلب آخر X رسالة من قاعدة البيانات وتحويلها.

```python
async def fetch_history(self, session_id: str, limit: int = 20) -> List[BaseMessage]:
    """
    Hydrate LangChain History from SQL Table
    تحويل صفوف قاعدة البيانات إلى كائنات ذاكرة
    """
    # 1. Fetch from DB
    db = self._get_db()
    response = db.table("ai_chat_messages") \
        .select("*") \
        .eq("session_id", session_id) \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    
    rows = sorted(response.data, key=lambda x: x['created_at'])
    
    # 2. Convert to BaseMessage
    messages = []
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    
    for row in rows:
        role = row['role']
        content = row['content']
        
        if role == 'user':
            messages.append(HumanMessage(content=content))
        elif role == 'assistant':
            messages.append(AIMessage(content=content))
        # Handle Tool/System messages if stored
            
    return messages
```

#### ب. تعديل `create_graph_agent`
تحويلها لتقبل `history` كمعامل إدخال في الـ input_state.

```python
# في ChatService.process_message
history = await self.fetch_history(session_id)
input_state = {
    "messages": history + [HumanMessage(content=message_text)], # Hydration + New Input
    # ... rest of state
}
```

### 3. مخاطر "نوع البيانات" (Mismatch Risks)
-   **مخرجات الأدوات (ToolMessage):** حالياً الجدول يخزن `content` كنص. إذا قام الوكيل باستدعاء أداة، فإن مخرجاتها غالباً ما تكون JSON. تخزينها كنص قد يفقد التنسيق.
    -   *الحل المؤقت:* تخزين مخرجات الأدوات كـ `role='tool'` في جدول الرسائل (إذا كان الجدول يدعمه) أو تجاهلها في الذاكرة طويلة المدى (الاعتماد على التلخيص).
-   **بيانات الميتا (Metadata):** تأكد من أن حقل `metadata` في AIMessage يتم حفظه في عمود `metadata` في الجدول لاسترجاع "عملية التفكير" إذا لزم الأمر.

## خطوة بخطوة للتنفيذ (Action Plan)
1.  **[Service Layer]** إضافة `_convert_db_row_to_message` في `ChatService`.
2.  **[Logic]** تعديل `process_message` لاستدعاء `get_session_messages` (الموجودة أصلاً) واستخدام دالة التحويل.
3.  **[Graph Injection]** تمرير القائمة الكاملة `history` إلى `graph.ainvoke`.

هذا سيجعل الوكيل "يتذكر" ما قيل سابقاً حتى بعد إعادة تشغيل السيرفر.
