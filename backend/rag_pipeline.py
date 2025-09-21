import json
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain.prompts import PromptTemplate

# === Path to your dataset ===
DATA_PATH = r"D:\Drishtti_Narwal\NyayaBot-SCAAI\backend\data\indian_schemes_data_final_cleaned.json"

def setup_chatbot(state: str):
    # === Load data ===
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # === Normalize input state ===
    matched_state = state.lower().strip()

    # === Filter relevant documents ===
    filtered_docs = [
        entry for entry in data
        if entry.get("state", "").lower() == matched_state
        and "final_cleaned_content" in entry
        and len(entry["final_cleaned_content"].strip()) > 50
    ]

    if not filtered_docs:
        return None

    # === Convert to LangChain Documents ===
    documents = []
    for doc in filtered_docs:
        content = doc.get("final_cleaned_content", "")
        context = f"""Scheme Title: {doc.get('title', 'N/A')}
Target Audience: {', '.join(doc.get('target_audience', []))}
Details: {content}"""
        documents.append(Document(page_content=context))

    # === Split large text into chunks ===
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=100)
    split_docs = text_splitter.split_documents(documents)

    # === Generate embeddings & vectorstore ===
    embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    vectordb = Chroma.from_documents(split_docs, embedding_model)

    # === Load HF LLM ===
    model_id = "google/flan-t5-large"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

    pipe = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        max_length=1024,
        do_sample=False,
        num_beams=4
    )
    llm = HuggingFacePipeline(pipeline=pipe)

    # === Prompt template ===
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

    # === Setup QA chain ===
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectordb.as_retriever(search_kwargs={"k": 5}),
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt_template},
        return_source_documents=False
    )

    return qa_chain
