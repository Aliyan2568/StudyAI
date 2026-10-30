# StudyAI – AI-Powered Study Assistant

StudyAI is an AI powered study assistant that transforms lecture materials into useful study resources. Users can upload PDF documents or PowerPoint presentations and generate summaries, flashcards, and interactive quizzes using AI.

## Features

- **PDF & PowerPoint Uploads:** Extracts text from PDF and PPTX lecture materials.
- **AI Summaries:** Generates organized study guides with important topics, definitions, and key concepts.
- **Interactive Flashcards:** Review questions and answers, track mastered concepts, and identify areas that need improvement.
- **AI-Generated Quizzes:** Generate multiple-choice questions with randomized answer choices, instant feedback, and final scores.
- **PDF Export:** Download generated summaries as PDF files.
- **Excel Export:** Download flashcards and quizzes as formatted Excel spreadsheets.

## Tech Stack

- **Backend:** Python, FastAPI
- **AI:** Groq API (`openai/gpt-oss-20b`)
- **Frontend:** HTML, CSS, JavaScript
- **PDF Processing:** PyMuPDF, ReportLab
- **PowerPoint Processing:** python-pptx
- **Excel Export:** OpenPyXL

## Getting Started

### 1. Clone the Repository

git clone https://github.com/Aliyan2568/StudyAI.git
cd StudyAI

### 2. Create a Virtual Environment

python -m venv .venv

.venv\Scripts\Activate.ps1

### 3. Install Dependencies

pip install -r requirements.txt

### 4. Configure Environment Variables

Create a `.env` file in the project root:

GROQ_API_KEY=your_groq_api_key

Get an API key from [Groq](https://console.groq.com/).

### 5. Run the Application

uvicorn main:app --reload

Open the application at:

http://127.0.0.1:8000

