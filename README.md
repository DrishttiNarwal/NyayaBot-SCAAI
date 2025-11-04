# 🧠 NyayaBot
------------------
**NyayaBot** is an AI-powered chatbot designed to help individuals access and understand their **legal rights** and **government policies** based on their **age**, **gender**, and **region**.

Built using:
- ⚙️ **FastAPI** (Backend)
- 💻 **React** (Frontend)
- 🧠 **LangChain RAG Architecture** (LLM-powered QA)

---

## 📁 Project Structure

```
NyayaBot/
│
├── backend/          # FastAPI app
│   ├── app/          # FastAPI application files
│   ├── venv/         # Python virtual environment (excluded via .gitignore)
│   ├── main.py       # FastAPI entry point
│   └── requirements.txt
|   |---.gitignore
│
├── frontend/         # React app
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── ...
│
└── README.md
```

---

## 🐍 Backend Setup (FastAPI)

### 1. Navigate to backend
```bash
cd backend
```

### 2. Create virtual environment (if not already created)
```bash
python -m venv venv
```

### 3. Activate the virtual environment

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```

- **macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the FastAPI server
```bash
uvicorn main:app --reload
```

> The backend will be running at: **http://127.0.0.1:8000**

---

## ⚛️ Frontend Setup (React)

### 1. Open a new terminal and navigate to frontend
```bash
cd frontend
```

### 2. Install frontend dependencies
```bash
npm install
```

### 3. Start the React development server
```bash
npm start
```

> The frontend will run on: **http://localhost:3000**

---

## 🔗 Connecting Frontend to Backend

Make sure to call your API endpoints using the correct base URL (e.g., `http://localhost:8000`) in your React frontend.

You can use `axios` or `fetch()` to make HTTP requests to the FastAPI server.

---

Happy coding! 🚀
