"""
AI Helper Endpoints
Endpoints for AI question generation and response analysis
"""

from fastapi import APIRouter
import requests
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

LLM_URL = "http://152.67.159.164:3000/api/chat/completions"


@router.post("/generate-question")
async def generate_question(request: dict):
    """Generate intelligent question using AI"""
    try:
        case_facts = request.get("case_facts", "")
        conversation_history = request.get("conversation_history", [])
        
        # Build context
        conversation_summary = "\n".join([
            f"مستخدم: {turn.get('user', '')}\nمحامي: {turn.get('lawyer', '')}"
            for turn in conversation_history[-3:]
        ])
        
        prompt = f"""أنت مستخدم عادي تبحث عن مساعدة قانونية في قضية أحوال شخصية.

وقائع قضيتك:
{case_facts}

المحادثة حتى الآن:
{conversation_summary if conversation_summary else 'لم تبدأ بعد'}

قواعد السلوك:
1. تحدث بشكل طبيعي كمستخدم عادي (ليس محامٍ)
2. أجب على أسئلة المحامي بوضوح وبساطة
3. إذا سألك عن معلومات ليست في الوقائع، قل "لا أعلم"
4. اسأل أسئلة منطقية تتعلق بحقوقك كأب
5. لا تعطِ كل المعلومات دفعة واحدة

المطلوب: اكتب سؤالك/ردك التالي فقط (جملة واحدة أو جملتين)
لا تكتب شرح، فقط الكلام المباشر:"""

        # Call LLM
        response = requests.post(
            LLM_URL,
            json={
                "model": "gpt-oss-120b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 150
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            question = data["choices"][0]["message"]["content"].strip()
            question = question.replace('"', '').replace("'", "").strip()
            return {"question": question}
        else:
            # Fallback to default questions
            defaults = [
                "مرحباً، أنا أب وأريد المساعدة",
                "أحوال شخصية رؤية صغار",
                "أريد معرفة حقوقي في رؤية أطفالي",
                "كم مرة يمكنني رؤية أطفالي؟",
                "ماذا أفعل إذا منعت الأم الرؤية؟",
                "هل يمكنني طلب تعديل حكم الرؤية؟"
            ]
            turn_index = len(conversation_history) % len(defaults)
            return {"question": defaults[turn_index]}
            
    except Exception as e:
        logger.error(f"Error generating question: {e}")
        return {"question": "أريد استشارة قانونية بخصوص حقوقي"}


@router.post("/analyze-response")
async def analyze_response(request: dict):
    """Analyze lawyer's response using AI"""
    try:
        lawyer_response = request.get("response", "")
        
        prompt = f"""أنت محلل خبير لسلوك وكلاء AI القانونيين.

رد المحامي:
{lawyer_response}

قيّم الرد من 1 إلى 10:
1. الودية والتعاطف
2. الوضوح والفهم
3. الدقة القانونية
4. طرح أسئلة مفيدة
5. التقدم نحو الحل

اكتب تقييمك:
ودية: X/10
وضوح: X/10
دقة: X/10
أسئلة: X/10
تقدم: X/10
ملاحظة: [قصيرة]"""

        response = requests.post(
            LLM_URL,
            json={
                "model": "gpt-oss-120b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 200
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            analysis = data["choices"][0]["message"]["content"].strip()
            return {"analysis": analysis}
        else:
            return {"analysis": "تحليل غير متاح"}
            
    except Exception as e:
        logger.error(f"Error analyzing response: {e}")
        return {"analysis": f"خطأ في التحليل"}


@router.post("/chat")
async def chat_endpoint(request: dict):
    """
    AI Chat endpoint for ChatPage
    Accepts: { message: str, session_id: str, generate_title: bool, lawyer_id: str }
    Returns: { message: str, suggested_title: str? }
    
    Security: Input validation, message length limits, XSS prevention
    """
    try:
        from agents.core.enhanced_general_lawyer_agent import EnhancedGeneralLawyerAgent
        from agents.storage.user_storage import user_storage
        from api.utils.security import validate_message_content, validate_lawyer_id
        
        message = request.get("message", "")
        session_id = request.get("session_id")
        generate_title = request.get("generate_title", False)
        lawyer_id = request.get("lawyer_id")
        
        # ✅ Security: Validate inputs
        validate_message_content(message)
        validate_lawyer_id(lawyer_id)
        
        logger.info(f"💬 Chat request from lawyer {lawyer_id}: {message[:50]}...")
        
        # Get user context like /api/chat does
        agent = None
        
        if lawyer_id:
            # Get the current user details
            current_user = user_storage.get_user_by_id(lawyer_id)
            
            if current_user:
                current_user.pop("password_hash", None)
                
                # Determine who the "Office Owner" (Lawyer) is
                if current_user.get("office_id"):
                    # This is an ASSISTANT
                    target_lawyer_id = current_user.get("office_id")
                    agent = EnhancedGeneralLawyerAgent(
                        lawyer_id=target_lawyer_id,
                        lawyer_name=None,
                        current_user=current_user
                    )
                else:
                    # This is the LAWYER
                    target_lawyer_id = lawyer_id
                    agent = EnhancedGeneralLawyerAgent(
                        lawyer_id=target_lawyer_id,
                        lawyer_name=None,
                        current_user=current_user
                    )
            else:
                # Fallback to global agent
                from api.main import general_agent
                agent = general_agent
        else:
            # No lawyer_id - use global agent
            from api.main import general_agent
            agent = general_agent
        
        # Process message
        response = agent.process_user_message(message)
        
        # Extract text from response
        if isinstance(response, dict):
            ai_message = response.get("response", response.get("message", str(response)))
        else:
            ai_message = str(response)
        
        # ✅ Security: Validate AI response length
        if len(ai_message) > 50000:
            logger.warning(f"AI response too long: {len(ai_message)} chars, truncating")
            ai_message = ai_message[:50000] + "..."
        
        result = {"message": ai_message}
        
        # Generate title if first message
        if generate_title:
            title_prompt = f"اقترح عنواناً قصيراً (3-5 كلمات) لهذه المحادثة:\nالمستخدم: {message}\nالمساعد: {ai_message[:100]}"
            
            try:
                title_response = requests.post(
                    LLM_URL,
                    json={
                        "model": "gpt-oss-120b",
                        "messages": [{"role": "user", "content": title_prompt}],
                        "temperature": 0.7,
                        "max_tokens": 20
                    },
                    timeout=10
                )
                
                if title_response.status_code == 200:
                    title_data = title_response.json()
                    suggested_title = title_data["choices"][0]["message"]["content"].strip().replace('"', '')
                    # ✅ Security: Validate title length
                    if len(suggested_title) > 100:
                        suggested_title = suggested_title[:100]
                    result["suggested_title"] = suggested_title
            except Exception as e:
                logger.warning(f"Title generation failed: {e}")
                pass  # Title generation is optional
        
        logger.info(f"✅ Chat response generated for lawyer {lawyer_id}")
        return result
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions (validation errors)
    except Exception as e:
        logger.error(f"❌ Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="حدث خطأ في معالجة الرسالة")
