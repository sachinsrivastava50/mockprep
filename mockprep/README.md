# MOCKPREP • Full-Stack AI Mock Interview Platform

**Mini Project Synopsis Implementation — Group 05**  
*Department of Computer Science & Engineering, IET Lucknow*  
*Members: Kshitij Varma (2400520100046), Sachin Srivastava (2400520100062), Tarun Kumar (2400520100068)*

---

## 🚀 Overview

**MockPrep** simulates real-world technical and behavioral job interviews:
1. **JWT User Authentication**: Secure token-based signup and login so candidate session history remains private.
2. **Role & Difficulty Selection**: Software Engineer, Data Analyst, Frontend, Backend, Product Manager, or Custom roles with Easy, Medium, or Hard difficulty.
3. **AI Question Generation**: Context-aware interview question prompts generated via an LLM API (with intelligent built-in fallback).
4. **Weighted Scoring Rubric (Out of 10.0)**:
   - **Correctness**: Weight 2.5 (25%)
   - **Clarity**: Weight 2.0 (20%)
   - **Technical Depth**: Weight 2.0 (20%)
   - **Relevance**: Weight 2.0 (20%)
   - **Communication**: Weight 1.5 (15%)
5. **Relational Database History**: Saves every session and evaluated response in PostgreSQL / SQLite.
6. **Analytics Dashboard**: Longitudinal Chart.js score trend graphs and full question-by-question review with model benchmark answers.

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3 (Tailwind CSS, Glassmorphism, Responsive Grids), Modern JavaScript (ES6+), Chart.js
- **Backend**: Python 3.10+, FastAPI, Uvicorn server, Pydantic, Passlib (Bcrypt), PyJWT
- **Database**: PostgreSQL / SQLite (via SQLAlchemy ORM)
- **AI Integration**: Claude / Gemini LLM API (with built-in heuristic rubric engine)

---

## 💻 How to Run

### Quick Start (Windows)
Double-click **`start.bat`** in the project root.

### Manual Launch via Terminal
1. Open terminal in `mockprep/backend`:
   ```bash
   cd mockprep/backend
   python run.py
   ```
2. Open your browser and navigate to:
   - **Web App**: `http://localhost:8000`
   - **Interactive Swagger API Docs**: `http://localhost:8000/docs`
