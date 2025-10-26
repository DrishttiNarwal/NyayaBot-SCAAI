import os
import json
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

# === Paths ===
DATA_PATH = os.environ.get("DATA_PATH")
CHROMA_DIR = os.environ.get("CHROMA_DIR")

# === Load main LLM globally (RAG) ===
MODEL_ID = "google/flan-t5-large"
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID)
pipe = pipeline(
    "text2text-generation",
    model=model,
    tokenizer=tokenizer,
    max_length=1024,
    do_sample=False,
    num_beams=4
)
llm = HuggingFacePipeline(pipeline=pipe)

# === Load NLLB model for translation ===
NLLB_MODEL = "facebook/nllb-200-distilled-600M"
NLLB_TOKENIZER = AutoTokenizer.from_pretrained(NLLB_MODEL)
NLLB_MODEL_OBJ = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)

translator = pipeline(
    "translation",
    model=NLLB_MODEL_OBJ,
    tokenizer=NLLB_TOKENIZER,
    max_length=1024,
    truncation=True
)

# NLLB language codes
SRC_HI = "hin_Deva"
TGT_EN = "eng_Latn"
SRC_EN = "eng_Latn"
TGT_HI = "hin_Deva"

def translate_text(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Translate text using NLLB-200.
    src_lang and tgt_lang: BCP-47 codes like 'hin_Deva', 'eng_Latn'
    """
    translated = translator(text, src_lang=src_lang, tgt_lang=tgt_lang)
    return translated[0]["translation_text"]

# === Prompt template (global) ===
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are NyayaBot, a helpful assistant that explains Indian government schemes in clear, factual, and complete language.

Instructions:
- If a government scheme is asked, include its name, eligibility, benefits, application process (if possible), and important dates.
- Format the response with bullet points or full sentences.
- Do not mention 'as an AI model'.
- Keep answers concise but informative.

Context:
{context}

Question:
{question}

Answer:
"""
)

def setup_chatbot(state: str):
    state = state.lower().strip()

    # Create folder for Chroma DB if not exists
    os.makedirs(CHROMA_DIR, exist_ok=True)

    # Check if Chroma DB for this state exists
    state_db_path = os.path.join(CHROMA_DIR, state)
    if os.path.exists(state_db_path):
        vectordb = Chroma(
            persist_directory=state_db_path,
            embedding_function=HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
        )
    else:
        # Load dataset
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Filter relevant documents
        filtered_docs = [
            entry for entry in data
            if entry.get("state", "").lower() == state
            and "final_cleaned_content" in entry
            and len(entry["final_cleaned_content"].strip()) > 50
        ]

        if not filtered_docs:
            return None

        # Convert to LangChain Documents
        documents = []
        for doc in filtered_docs:
            content = doc.get("final_cleaned_content", "")
            context = f"""Scheme Title: {doc.get('title', 'N/A')}
Target Audience: {', '.join(doc.get('target_audience', []))}
Details: {content}"""
            documents.append(Document(page_content=context))

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=100)
        split_docs = text_splitter.split_documents(documents)

        # Generate embeddings and create Chroma vectorstore
        embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
        vectordb = Chroma.from_documents(split_docs, embedding_model, persist_directory=state_db_path)
        vectordb.persist()  # Save to disk

    # Setup QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectordb.as_retriever(search_kwargs={"k": 5}),
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt_template},
        return_source_documents=False
    )

    return qa_chain

def chatbot_query(qa_chain, user_query: str, lang: str = "en") -> str:
    """
    Handles user query in English or Hindi.
    - If lang='en': directly process query (dataset is in English).
    - If lang='hi': translate Hindi -> English -> RAG -> English -> Hindi.
    """
    if lang == "hi":
        english_query = translate_text(user_query, SRC_HI, TGT_EN)
    else:
        english_query = user_query

    # Query RAG
    english_answer = qa_chain.invoke({"query": english_query})["result"]

    if lang == "hi":
        final_answer = translate_text(english_answer, SRC_EN, TGT_HI)
    else:
        final_answer = english_answer

    return final_answer
