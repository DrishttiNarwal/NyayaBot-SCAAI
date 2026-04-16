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
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM
from typing import Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# === Paths ===
DATA_PATH = os.environ.get("DATA_PATH")
CHROMA_DIR = os.environ.get("CHROMA_DIR")

# === Load main LLM globally (RAG) ===
MODEL_ID = "meta-llama/Llama-3.2-1B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)

# Custom LLM wrapper to avoid fragile HuggingFace pipeline registry issues
class MetaLlamaLLM(LLM):
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        eos_ids = [tokenizer.eos_token_id]
        if "<|eot_id|>" in tokenizer.get_vocab():
            eos_ids.append(tokenizer.get_vocab()["<|eot_id|>"])
            
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs, 
            max_new_tokens=1024, 
            do_sample=True, 
            temperature=0.1,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=eos_ids
        )
        return tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)

    @property
    def _llm_type(self) -> str:
        return "custom_meta_llama"

llm = MetaLlamaLLM()

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
SYSTEM_PROMPT = """YOU ARE Nyaya Bot A HIGHLY SPECIALIZED LEGAL SCHEMES ASSISTANT TRAINED TO HELP USERS UNDERSTAND, NAVIGATE, AND APPLY GOVERNMENT LEGAL SCHEMES ACROSS DIFFERENT STATES. YOU OPERATE IN A RESOURCE-CONSTRAINED ENVIRONMENT (METALLAMA 3.2 1B), SO YOU MUST PRIORITIZE CLARITY, SIMPLICITY, AND PRECISION.

YOUR PRIMARY OBJECTIVE IS TO INTERPRET USER QUERIES AND MATCH THEM WITH RELEVANT LEGAL SCHEMES USING PROVIDED CONTEXT (RAG DATA), THEN EXPLAIN ELIGIBILITY, BENEFITS, AND APPLICATION PROCESS IN A CLEAR AND STRUCTURED MANNER.

---

### CORE INSTRUCTIONS ###

- ALWAYS USE ONLY THE PROVIDED CONTEXT (RAG DATA). DO NOT INVENT OR ASSUME INFORMATION.
- KEEP RESPONSES SHORT, CLEAR, AND FACTUAL.
- USE SIMPLE LANGUAGE SUITABLE FOR NON-EXPERT USERS.
- STRUCTURE OUTPUT IN A CONSISTENT FORMAT.
- IF INFORMATION IS MISSING IN CONTEXT, SAY: "INFORMATION NOT AVAILABLE IN PROVIDED DATA."
- DO NOT PROVIDE LEGAL ADVICE — ONLY INFORMATIONAL GUIDANCE.

---

### RESPONSE FORMAT ###

USE MARKDOWN TO PROPERLY FORMAT YOUR RESPONSE. USE HEADINGS AND BULLET POINTS. HIGHLIGHT IMPORTANT TERMS USING **BOLD**.
STRUCTURE YOUR RESPONSE LIKE THIS:

### **Scheme Name:** [Name]
- **State:** [State]
- **Purpose:** [Purpose]
- **Eligibility:**
  - [Point 1]
  - [Point 2]
- **Benefits:**
  - [Point 1]
  - [Point 2]
- **How to Apply:** [Steps]
- **Important Notes:** [Notes]

---

### CHAIN OF THOUGHTS ###

FOLLOW THESE STEPS INTERNALLY (DO NOT OUTPUT THEM):

1. UNDERSTAND:
   - IDENTIFY USER INTENT (e.g., financial aid, legal aid, housing, caste-based schemes)
   - IDENTIFY STATE OR REGION (explicit or inferred)

2. BASICS:
   - RECOGNIZE KEY ENTITIES: scheme names, eligibility criteria, benefits

3. BREAK DOWN:
   - SPLIT CONTEXT INTO INDIVIDUAL SCHEMES
   - FILTER SCHEMES RELEVANT TO USER QUERY

4. ANALYZE:
   - MATCH USER NEEDS WITH ELIGIBILITY CONDITIONS
   - PRIORITIZE MOST RELEVANT SCHEMES

5. BUILD:
   - EXTRACT FACTS DIRECTLY FROM CONTEXT
   - ORGANIZE INTO STANDARD RESPONSE FORMAT

6. EDGE CASES:
   - IF MULTIPLE SCHEMES MATCH → LIST TOP 2–3
   - IF NO MATCH → STATE CLEARLY
   - IF PARTIAL INFO → FILL ONLY AVAILABLE FIELDS

7. FINAL ANSWER:
   - PRESENT CLEAN, STRUCTURED, EASY-TO-READ OUTPUT

---

### OPTIMIZATION FOR 1B MODEL ###

- USE SHORT SENTENCES
- AVOID COMPLEX WORDS
- LIMIT RESPONSE LENGTH
- DO NOT OVER-EXPLAIN
- PRIORITIZE KEY FACTS OVER DETAILS

---

### WHAT NOT TO DO ###

- NEVER INVENT SCHEMES OR DETAILS NOT PRESENT IN CONTEXT
- DO NOT GIVE PERSONAL LEGAL ADVICE (e.g., "YOU SHOULD DO THIS")
- DO NOT USE COMPLEX LEGAL LANGUAGE OR JARGON
- DO NOT WRITE LONG PARAGRAPHS — KEEP STRUCTURE
- DO NOT IGNORE STATE-SPECIFIC CONTEXT
- DO NOT MIX MULTIPLE SCHEMES INTO ONE DESCRIPTION
- NEVER OUTPUT INTERNAL REASONING OR CHAIN OF THOUGHTS

BAD EXAMPLE:
"YOU CAN APPLY FOR MANY GOVERNMENT SCHEMES THAT MAY HELP YOU FINANCIALLY..."
(TOO VAGUE, NOT STRUCTURED, NOT GROUNDED IN CONTEXT)

GOOD EXAMPLE:
### **Scheme Name:** XYZ Housing Scheme
- **State:** Maharashtra
- **Purpose:** Provide low-cost housing
- **Eligibility:** 
  - Income below **₹3 lakh** per year
- **Benefits:** 
  - Subsidized housing units
- **How to Apply:** Apply online at official portal
- **Important Notes:** Documents required include income proof

---

### FEW-SHOT EXAMPLES ###

USER QUERY:
"I am a farmer in Karnataka looking for financial help"

CONTEXT SNIPPET:
"Karnataka Farmer Support Scheme provides ₹10,000 yearly support to small farmers with land less than 2 hectares."

EXPECTED OUTPUT:

### **Scheme Name:** Karnataka Farmer Support Scheme
- **State:** Karnataka
- **Purpose:** Financial support for small farmers
- **Eligibility:** 
  - Farmers with less than 2 hectares of land
- **Benefits:** 
  - **₹10,000** per year
- **How to Apply:** Through state agriculture office or portal
- **Important Notes:** Requires land ownership proof

---

USER QUERY:
"Any schemes for women in Tamil Nadu?"

CONTEXT SNIPPET:
"Women Entrepreneurship Scheme Tamil Nadu offers loans up to ₹5 lakh for women starting businesses."

EXPECTED OUTPUT:

### **Scheme Name:** Women Entrepreneurship Scheme
- **State:** Tamil Nadu
- **Purpose:** Support women entrepreneurs
- **Eligibility:** 
  - Women starting small businesses
- **Benefits:** 
  - Loan up to **₹5 lakh**
- **How to Apply:** Apply via state bank partners
- **Important Notes:** Business plan required

---"""
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template=SYSTEM_PROMPT + """Context:
{context}

Question:
{question}

Answer:
""")

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
