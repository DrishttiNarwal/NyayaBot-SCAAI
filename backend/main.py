from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_pipeline import setup_chatbot, chatbot_query

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

# Store initialized QA chains per state
qa_chains = {}

def detect_language(text: str) -> str:
    """
    Detects if the text is Hindi or English.
    - Returns 'hi' if Devanagari characters are present
    - Returns 'en' otherwise
    """
    hindi_regex = r"[\u0900-\u097F]"
    return "hi" if any(char for char in text if char >= "\u0900" and char <= "\u097F") else "en"

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
