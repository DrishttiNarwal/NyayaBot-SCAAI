from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_pipeline import setup_chatbot, chatbot_query, translate_text, SRC_HI, TGT_EN, SRC_EN, TGT_HI
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch
import re
import speech_recognition as sr

app = FastAPI()

# Enable CORS for React frontend or other clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route to confirm backend is running
@app.get("/")
def root():
    print("🚀 Backend started successfully!")
    return {"message": "Backend started successfully!"}

# Health check route
@app.get("/health")
def health_check():
    print("✅ Frontend connected to backend!")
    return {"status": "ok"}

# Request body structure for chat
class ChatRequest(BaseModel):
    state: str
    query: str
    # lang optional; if not provided, it will be auto-detected
    lang: str = None  

# Request body for summarization
class SummarizeRequest(BaseModel):
    chat_history: list  # List of {"role": "user"|"bot", "content": str}

# Store initialized QA chains per state
qa_chains = {}

def detect_language(text: str) -> str:
    """
    Detects if the text is Hindi or English.
    - Returns 'hi' if significant Devanagari characters are present
    - Returns 'en' otherwise
    """
    # Count Hindi and English characters
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    total_chars = hindi_chars + english_chars
    
    if total_chars == 0:
        return "en"
    
    hindi_percentage = hindi_chars / total_chars
    # More conservative threshold for single message detection
    return "hi" if hindi_percentage >= 0.5 else "en"

@app.post("/chat")
def chat(req: ChatRequest):
    state = req.state.lower().strip()

    # Initialize QA chain for the state if not already done
    if state not in qa_chains:
        qa_chain = setup_chatbot(state)
        if qa_chain is None:
            return {"response": f"No scheme data available for {state.title()}."}
        qa_chains[state] = qa_chain
    else:
        qa_chain = qa_chains[state]

    # Auto-detect language if not provided
    lang = req.lang.lower().strip() if req.lang else detect_language(req.query)
    if lang not in ["en", "hi"]:
        lang = "en"

    # Query chatbot
    try:
        final_response = chatbot_query(qa_chain, req.query, lang=lang)
    except Exception as e:
        return {"response": f"⚠️ Error while processing query: {str(e)}"}

    return {"response": final_response}


# Load T5-FLAN base model for summarization
T5_MODEL = "google/flan-t5-base"
_tokenizer = AutoTokenizer.from_pretrained(T5_MODEL)
_model = AutoModelForSeq2SeqLM.from_pretrained(
    T5_MODEL,
    dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)
_summarizer = pipeline(
    "text2text-generation",
    model=_model,
    tokenizer=_tokenizer,
    device=0 if torch.cuda.is_available() else -1,
    max_length=512,
    do_sample=True,
    temperature=0.7
)

def format_chat_history(chat_history):
    """Format chat history into a readable string."""
    formatted = []
    for turn in chat_history:
        role = turn.get("role", "user").capitalize()
        content = turn.get("content", "")
        formatted.append(f"{role}: {content}")
    return "\n".join(formatted)

def detect_chat_language(chat_history):
    """Detect the primary language used in the chat history with enhanced accuracy."""
    combined_text = " ".join([turn.get("content", "") for turn in chat_history])
    
    print(f"Language detection - Combined text: {combined_text[:200]}...")  
    
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', combined_text))
    
    english_chars = len(re.findall(r'[a-zA-Z]', combined_text))
    
    total_meaningful_chars = hindi_chars + english_chars
    
    print(f"Language detection - Hindi chars: {hindi_chars}, English chars: {english_chars}, Total: {total_meaningful_chars}")
    
    if total_meaningful_chars == 0:
        print("Language detection - No meaningful text, defaulting to English")
        return "en"  
    
    hindi_percentage = hindi_chars / total_meaningful_chars
    print(f"Language detection - Hindi percentage: {hindi_percentage:.2%}")
    
    hindi_words = ["योजना", "सरकार", "लाभ", "आवेदन", "पात्रता", "मंत्रालय", "विभाग", "सहायता", "क्या", "है", "के", "लिए", "में", "को", "की"]
    has_hindi_words = any(word in combined_text for word in hindi_words)
    hindi_word_count = sum(1 for word in hindi_words if word in combined_text)
    
    print(f"Language detection - Has Hindi words: {has_hindi_words}, Hindi word count: {hindi_word_count}")
    
    if (hindi_percentage >= 0.6 or
        (hindi_percentage >= 0.4 and hindi_word_count >= 3) or
        (hindi_percentage >= 0.2 and hindi_word_count >= 5)):
        print("Language detection - Detected as Hindi")
        return "hi"
    
    print("Language detection - Detected as English")
    return "en"

def enhance_summary_formatting(summary, chat_history):
    """Enhance summary with proper bold formatting for key information."""
    enhanced = summary
    
    scheme_keywords = [
        "scheme", "yojana", "mission", "program", "programme",
        "ministry", "department", "government", "मंत्रालय", "विभाग", "सरकार",
        "eligibility", "eligible", "criteria", "पात्रता", "योग्यता",
        "benefit", "benefits", "assistance", "subsidy", "loan", "लाभ", "सहायता", "सब्सिडी",
        "farmer", "women", "student", "entrepreneur", "किसान", "महिला", "छात्र", "उद्यमी",
        "application", "apply", "registration", "आवेदन", "पंजीकरण"
    ]
    
    for turn in chat_history:
        if turn.get("role") == "bot":
            content = turn.get("content", "")
            scheme_matches = re.findall(r'([A-Za-z\u0900-\u097F][A-Za-z\s\u0900-\u097F]*(?:Scheme|Yojana|Mission|Program|Programme|योजना|मिशन))', content)
            for scheme_name in scheme_matches:
                scheme_clean = scheme_name.strip()
                if scheme_clean in enhanced and f"**{scheme_clean}**" not in enhanced:
                    enhanced = enhanced.replace(scheme_clean, f"**{scheme_clean}**")
    
    for keyword in scheme_keywords:
        pattern = rf'\b({re.escape(keyword)})\b(?=\s*[:\-]|\s+(?:is|are|include|for|है|हैं|के लिए))'
        enhanced = re.sub(pattern, r'**\1**', enhanced, flags=re.IGNORECASE)
    
    enhanced = re.sub(r'(₹[\d,]+|Rs\.?\s*[\d,]+)', r'**\1**', enhanced)
    
    enhanced = re.sub(r'(\d+%)', r'**\1**', enhanced)
    
    return enhanced

def generate_english_summary(chat_text):
    """Generate summary using T5-FLAN model for English text."""
    try:
        system_prompt = (
            "You are an assistant specialized in summarizing conversations about Indian government schemes. "
            "Provide a concise and accurate summary highlighting key schemes, eligibility criteria, benefits, and application processes mentioned. "
            "Format important information in **bold**."
        )
        
        input_text = f"{system_prompt}\n\nConversation:\n{chat_text}\n\nSummary:"
        
        max_input_len = 1024
        if len(input_text) > max_input_len:
            truncated_chat = chat_text[-800:] if len(chat_text) > 800 else chat_text
            input_text = f"{system_prompt}\n\nConversation:\n{truncated_chat}\n\nSummary:"
        
        result = _summarizer(
            input_text,
            max_length=300,
            min_length=50,
            do_sample=True,
            temperature=0.6,
            top_p=0.85,
            num_beams=3,
            early_stopping=True,
            repetition_penalty=1.1
        )
        
        summary = result[0]["generated_text"].strip()
        
        if (len(summary) < 10 or 
            summary.lower().startswith("user:") or 
            summary.lower().startswith("bot:") or
            "conversation" in summary.lower() or
            summary == input_text[:len(summary)]):
            raise ValueError("T5 generated inadequate summary")
        
        return summary
        
    except Exception as e:
        print(f"T5-FLAN summarization failed: {e}")
        raise e

def create_manual_summary(chat_history, language):
    """Create a manual summary when the AI model fails."""
    user_queries = []
    bot_responses = []
    
    for turn in chat_history:
        if turn.get("role") == "user":
            user_queries.append(turn.get("content", ""))
        elif turn.get("role") == "bot":
            bot_responses.append(turn.get("content", ""))
    
    if language == "hi":
        summary_parts = []
        summary_parts.append("**बातचीत का सारांश:**")
        
        if user_queries:
            summary_parts.append("\n**उपयोगकर्ता के प्रश्न:**")
            for i, query in enumerate(user_queries[:3], 1):
                summary_parts.append(f"{i}. {query[:100]}..." if len(query) > 100 else f"{i}. {query}")
        
        if bot_responses:
            summary_parts.append("\n**मुख्य जानकारी:**")
            key_info = []
            for response in bot_responses:
                if "योजना" in response:
                    key_info.append("सरकारी योजनाओं की जानकारी प्रदान की गई")
                if "पात्रता" in response or "योग्यता" in response:
                    key_info.append("पात्रता मानदंड की चर्चा")
                if "आवेदन" in response:
                    key_info.append("आवेदन प्रक्रिया की जानकारी")
                if "लाभ" in response or "सहायता" in response:
                    key_info.append("योजना के लाभों की व्याख्या")
            
            for info in list(set(key_info))[:4]:  
                summary_parts.append(f"- {info}")
        
        return "\n".join(summary_parts)
    
    else:
        summary_parts = []
        summary_parts.append("**Conversation Summary:**")
        
        if user_queries:
            summary_parts.append("\n**User Queries:**")
            for i, query in enumerate(user_queries[:3], 1):  
                summary_parts.append(f"{i}. {query[:100]}..." if len(query) > 100 else f"{i}. {query}")
        
        if bot_responses:
            summary_parts.append("\n**Key Information Provided:**")
            key_info = []
            for response in bot_responses:
                if "scheme" in response.lower() or "program" in response.lower():
                    key_info.append("Government scheme information provided")
                if "eligib" in response.lower():
                    key_info.append("Eligibility criteria discussed")
                if "application" in response.lower() or "apply" in response.lower():
                    key_info.append("Application process information")
                if "benefit" in response.lower() or "assistance" in response.lower():
                    key_info.append("Benefits and assistance explained")
            
            for info in list(set(key_info))[:4]:  
                summary_parts.append(f"- {info}")
        
        return "\n".join(summary_parts)

@app.post("/summarize")
def summarize(req: SummarizeRequest):
    """Generate summary of chat history using translation-based pipeline similar to chatbot, with manual fallback."""
    
    detected_lang = detect_chat_language(req.chat_history)
    chat_str = format_chat_history(req.chat_history)
    
    print(f"Detected language: {detected_lang}")
    print(f"Chat history length: {len(req.chat_history)}")
    
    try:
        if detected_lang == "hi":
            print("Using translation-based summarization for Hindi")
            
            try:
                print("Translating chat history from Hindi to English...")
                english_chat_str = translate_text(chat_str, SRC_HI, TGT_EN)
                print(f"Translation successful")
                
                print("Generating English summary...")
                english_summary = generate_english_summary(english_chat_str)
                print(f"English summary generated: {english_summary[:100]}...")
                
                print("Translating summary back to Hindi...")
                hindi_summary = translate_text(english_summary, SRC_EN, TGT_HI)
                print(f"Hindi summary generated successfully")
                
                enhanced_summary = enhance_summary_formatting(hindi_summary, req.chat_history)
                return {"summary": enhanced_summary}
                
            except Exception as translation_error:
                print(f"Translation-based summarization failed: {translation_error}")
                print("Falling back to manual Hindi summary")
                manual_summary = create_manual_summary(req.chat_history, "hi")
                return {"summary": manual_summary}
        
        else:
            print("Using direct English summarization")
            
            try:
                english_summary = generate_english_summary(chat_str)
                print(f"English summary generated successfully")
                
                enhanced_summary = enhance_summary_formatting(english_summary, req.chat_history)
                return {"summary": enhanced_summary}
                
            except Exception as english_error:
                print(f"English T5 summarization failed: {english_error}")
                print("Falling back to manual English summary")
                manual_summary = create_manual_summary(req.chat_history, "en")
                return {"summary": manual_summary}
    
    except Exception as general_error:
        print(f"General summarization error: {general_error}")
        fallback_msg = (
            "सारांश उत्पन्न करने में असमर्थ। कृपया पुनः प्रयास करें।" 
            if detected_lang == "hi" 
            else "Unable to generate summary at this time. Please try again."
        )
        return {"summary": fallback_msg}
    
@app.websocket("/ws/voice-command")
async def voice_command_ws(websocket: WebSocket):
    await websocket.accept()
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            await websocket.send_text("Listening...")
            print("Listening for voice command...")
            
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source)
            
            await websocket.send_text("Processing...")
            print("Processing voice command...")

        try:
            query = r.recognize_google(audio)
            await websocket.send_text(f"You said: {query}")
            print(f"Recognized: '{query}'")

        except sr.UnknownValueError:
            await websocket.send_text("Error: Could not understand audio")
            print("Could not understand audio")
        except sr.RequestError as e:
            await websocket.send_text(f"Error: Could not request results; {e}")
            print(f"Could not request results; {e}")

    except WebSocketDisconnect:
        print("Client disconnected from voice command.")
    except Exception as e:
        print(f"An error occurred in the voice websocket: {e}")
        try:
            await websocket.send_text(f"Error: An unexpected error occurred: {e}")
        except Exception as send_error:
            print(f"Could not send error to client: {send_error}")
    finally:
        await websocket.close()