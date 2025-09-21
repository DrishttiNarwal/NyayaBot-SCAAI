from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_pipeline import setup_chatbot

app = FastAPI()

# Enable CORS for React or other frontend running on localhost
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

# Health check route to confirm frontend-backend connection
@app.get("/health")
def health_check():
    print("✅ Frontend connected to backend!")  # Prints in terminal whenever called
    return {"status": "ok"}

# Define request body structure for chat
class ChatRequest(BaseModel):
    state: str
    query: str

# Store initialized QA chains per state
qa_chains = {}

@app.post("/chat")
def chat(req: ChatRequest):
    state = req.state.lower()

    # Initialize the QA chain for the state if not already done
    if state not in qa_chains:
        qa_chain = setup_chatbot(state)
        if qa_chain is None:
            return {"response": f"No scheme data available for {state.title()}."}
        qa_chains[state] = qa_chain
    else:
        qa_chain = qa_chains[state]

    # Run the query using the QA chain
    result = qa_chain.invoke({"query": req.query})
    return {"response": result["result"]}
