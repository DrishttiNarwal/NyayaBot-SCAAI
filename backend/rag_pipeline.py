import os
import re
import json
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models.llms import LLM
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# === Paths ===
DATA_PATH = os.environ.get("DATA_PATH")
CHROMA_DIR = os.environ.get("CHROMA_DIR")

# === Load main LLM globally (RAG) ===
MODEL_ID = "google/flan-t5-large"
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID)

# Custom LLM wrapper to avoid fragile HuggingFace pipeline registry issues
class FlanT5LLM(LLM):
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_length=1024, do_sample=False, num_beams=4)
        return tokenizer.decode(outputs[0], skip_special_tokens=True)

    @property
    def _llm_type(self) -> str:
        return "custom_flan_t5"

llm = FlanT5LLM()

# === Load NLLB model for translation ===
NLLB_MODEL = "facebook/nllb-200-distilled-600M"
NLLB_TOKENIZER = AutoTokenizer.from_pretrained(NLLB_MODEL)
NLLB_MODEL_OBJ = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)

# NLLB language codes
SRC_HI = "hin_Deva"
TGT_EN = "eng_Latn"
SRC_EN = "eng_Latn"
TGT_HI = "hin_Deva"

def translate_text(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Translate text using NLLB-200 directly with model.generate.
    """
    NLLB_TOKENIZER.src_lang = src_lang
    inputs = NLLB_TOKENIZER(text, return_tensors="pt", truncation=True, max_length=1024)
    forced_bos_token_id = NLLB_TOKENIZER.lang_code_to_id[tgt_lang]
    outputs = NLLB_MODEL_OBJ.generate(**inputs, forced_bos_token_id=forced_bos_token_id, max_length=1024)
    return NLLB_TOKENIZER.decode(outputs[0], skip_special_tokens=True)


def _clean_content(text: str) -> str:
    """Remove leftover JavaScript artifacts and ad remnants from scraped content."""
    text = re.sub(r'\s*\.push\(\{?\}?\);\s*', ' ', text)
    text = re.sub(r'\(adsbygoogle\s*=\s*window\.adsbygoogle\s*\|\|\s*\[\]\)\.push\(\{?\}?\);?', '', text)
    text = re.sub(r'\s*SAVE AS PDF\s*', '', text)
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def _extract_title(entry: dict) -> str:
    """
    Extract a meaningful title from the entry.
    """
    if entry.get("title"):
        return entry["title"]

    content = entry.get("final_cleaned_content", "")
    if not content:
        return entry.get("filename", "Unknown Scheme")

    first_line = content.split('\n')[0].strip()
    match = re.match(r'^(.+?[.!])\s', first_line)
    if match and len(match.group(1)) > 20:
        title = match.group(1)[:150]
    else:
        title = first_line[:120]
        if len(first_line) > 120:
            title += "..."

    return title


def _format_docs(docs):
    """Format retrieved documents into a single context string."""
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


# === Prompt template (global) ===
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are NyayaBot, a helpful assistant that explains Indian government schemes in clear, factual, and complete language.

Instructions:
- If a government scheme is asked, include its name, eligibility, benefits, application process (if possible), and important dates.
- Format the response with bullet points or full sentences.
- Do not mention 'as an AI model'.
- Keep answers concise but informative.
- If the context does not contain relevant information, say so honestly.

Context:
{context}

Question:
{question}

Answer:
"""
)

def setup_chatbot(state: str):
    state = state.lower().strip()

    os.makedirs(CHROMA_DIR, exist_ok=True)
    embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    state_db_path = os.path.join(CHROMA_DIR, state)
    
    if os.path.exists(state_db_path):
        vectordb = Chroma(
            persist_directory=state_db_path,
            embedding_function=embedding_model
        )
    else:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        filtered_docs = [
            entry for entry in data
            if entry.get("state", "").lower() == state
            and "final_cleaned_content" in entry
            and len(entry["final_cleaned_content"].strip()) > 50
        ]

        if not filtered_docs:
            return None

        documents = []
        for doc in filtered_docs:
            raw_content = doc.get("final_cleaned_content", "")
            content = _clean_content(raw_content)
            title = _extract_title(doc)

            target_audience = doc.get("target_audience", [])
            if isinstance(target_audience, list):
                audience_str = ", ".join(target_audience)
            else:
                audience_str = str(target_audience)

            budget = doc.get("budget_estimate", "Unknown")

            context = f"""Scheme Title: {title}
Target Audience: {audience_str}
Budget Estimate: {budget}
Details: {content}"""

            metadata = {
                "state": state,
                "filename": doc.get("filename", ""),
                "target_audience": audience_str,
                "budget_estimate": budget,
                "language": doc.get("language", "en"),
            }

            documents.append(Document(page_content=context, metadata=metadata))

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
        split_docs = text_splitter.split_documents(documents)

        vectordb = Chroma.from_documents(
            split_docs,
            embedding_model,
            persist_directory=state_db_path
        )

    retriever = vectordb.as_retriever(search_kwargs={"k": 5})

    rag_chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )

    return rag_chain

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

    # Invoke LCEL chain
    english_answer = qa_chain.invoke(english_query)

    if lang == "hi":
        final_answer = translate_text(english_answer, SRC_EN, TGT_HI)
    else:
        final_answer = english_answer

    return final_answer
