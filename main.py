from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
import fitz
from pptx import Presentation
from io import BytesIO

from ai import ask_ai, ask_ai_json

from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from fastapi.responses import StreamingResponse
from html import escape

import re

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase.pdfmetrics import registerFontFamily

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

app = FastAPI(title="StudyAI")
app.mount("/static", StaticFiles(directory="static"), name="static")

class StudyRequest(BaseModel):
    lecture_text: str = Field(min_length=1, max_length=100000)

class SummaryPDFRequest(BaseModel):
    summary: str = Field(min_length=1, max_length=100000)

@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    filename = file.filename.lower()
    
    if not filename.endswith((".pdf", ".pptx")):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF or PowerPoint file."
        )

    content = await file.read()

    try:
        extracted_text = ""
        page_count = 0

        if filename.endswith(".pdf"):
            document = fitz.open(
                stream=content,
                filetype="pdf"
            )

            page_count = len(document)

            for page in document:
                extracted_text += page.get_text() + "\n"

            document.close()

        else:
            presentation = Presentation(BytesIO(content))

            page_count = len(presentation.slides)

            for slide_number, slide in enumerate(presentation.slides, start=1):
                extracted_text += f"\nSlide {slide_number}\n"

                for shape in slide.shapes:
                    if shape.has_table:
                        for row in shape.table.rows:
                            extracted_text += " | ".join(
                                cell.text for cell in row.cells
                            ) + "\n"

                    elif shape.has_text_frame:
                        extracted_text += shape.text + "\n"

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text found in this file."
            )

        return {
            "filename": file.filename,
            "pages": page_count,
            "extracted_text": extracted_text
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read this file. Make sure it is a valid PDF or PPTX."
        )


@app.post("/generate-summary")
def generate_summary(request: StudyRequest):
    prompt = f"""
        Create an organized and easy-to-read study guide using these lecture notes.
    
        Use the following format:
    
        # Lecture Summary
    
        ## 1. Main Topics
        Explain the major topics covered in detail. Only this major topic section doesn't require bullet points.
        Make each major topic explanation 3-5 sentences.
    
        ## 2. Important Definitions
        List important terms and their meanings.
    
        ## 3. Key Concepts
        Explain important concepts using bullet points.
    
        ## 4. Important Things to Remember
        Highlight information students should remember for exams.
    
        ## 5. Quick Review
        Provide a short recap of the lecture.
    
        Formatting rules:
        - Use headings and subheadings.
        - Use bullet points instead of wide tables.
        - Bold important terms.
        - Keep explanations simple and clear.
        - Avoid unnecessary repetition.
        - Only use information from the lecture notes.
    
        Lecture material:
        {request.lecture_text}
        """

    return {"summary": ask_ai(prompt)}


@app.post("/download-summary")
def download_summary(request: SummaryPDFRequest):
    pdf_buffer = BytesIO()

    # Register Windows Arial fonts
    pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Bold", "C:/Windows/Fonts/arialbd.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Italic", "C:/Windows/Fonts/ariali.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-BoldItalic", "C:/Windows/Fonts/arialbi.ttf"))

    registerFontFamily(
        "Arial",
        normal="Arial",
        bold="Arial-Bold",
        italic="Arial-Italic",
        boldItalic="Arial-BoldItalic"
    )

    document = SimpleDocTemplate(
        pdf_buffer,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontName="Arial-Bold",
        fontSize=24,
        leading=30,
        textColor=colors.HexColor("#4f46e5"),
        alignment=TA_LEFT,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName="Arial",
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=25
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontName="Arial-Bold",
        fontSize=15,
        leading=20,
        textColor=colors.HexColor("#4f46e5"),
        spaceBefore=18,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=10,
        leading=16,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8
    )

    content = [
        Paragraph("StudyAI", title_style),
        Paragraph("Lecture Summary", subtitle_style)
    ]

    for line in request.summary.splitlines():
        line = line.strip()

        if not line:
            content.append(Spacer(1, 5))
            continue

        # Escape special HTML characters
        text = escape(line)

        # Convert Markdown bold and italic
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)

        # Format headings
        if line.startswith("### "):
            content.append(
                Paragraph(text[4:], heading_style)
            )

        elif line.startswith("## "):
            content.append(
                Paragraph(text[3:], heading_style)
            )

        elif line.startswith("# "):
            content.append(
                Paragraph(text[2:], heading_style)
            )

        # Format bullet points
        elif line.startswith("- ") or line.startswith("* "):
            content.append(
                Paragraph("• " + text[2:], body_style)
            )

        else:
            content.append(
                Paragraph(text, body_style)
            )

    document.build(content)

    pdf_buffer.seek(0)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="StudyAI_Summary.pdf"'
        }
    )

@app.post("/generate-flashcards")
def generate_flashcards(request: StudyRequest):
    prompt = f"""
    Create 20 flashcards using only these lecture notes.

    Return JSON in this exact structure:
    {{
        "flashcards": [
            {{
                "question": "What is a database?",
                "answer": "An organized collection of data."
            }}
        ]
    }}

    Lecture material:
    {request.lecture_text}
    """

    try:
        result = ask_ai_json(prompt)
        return result
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Could not generate flashcards. Please try again."
        )


@app.post("/generate-quiz")
def generate_quiz(request: StudyRequest):
    prompt = f"""
    Create 15 multiple-choice questions using only these lecture notes.

    Each question must have four choices and exactly one correct answer.

    Return JSON in this exact structure:
    {{
        "questions": [
            {{
                "question": "What is a database?",
                "choices": {{
                    "A": "An organized collection of data",
                    "B": "A programming language",
                    "C": "A computer processor",
                    "D": "An operating system"
                }},
                "correct_answer": "A",
                "explanation": "A database stores organized information."
            }}
        ]
    }}

    The correct_answer must be A, B, C, or D.

    Lecture material:
    {request.lecture_text}
    """

    try:
        result = ask_ai_json(prompt)
        return result
    except Exception as e:
        print("QUIZ GENERATION ERROR:", repr(e))

        raise HTTPException(
            status_code=502,
            detail="Could not generate quiz. Please try again."
        )


class FlashcardsExcelRequest(BaseModel):
    flashcards: list[dict]


class QuizExcelRequest(BaseModel):
    questions: list[dict]


def create_excel(headers, rows, sheet_name):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name

    # Add headers
    sheet.append(headers)

    # Header styling
    header_fill = PatternFill(
        fill_type="solid",
        fgColor="4F46E5"
    )

    for cell in sheet[1]:
        cell.font = Font(
            bold=True,
            color="FFFFFF",
            size=12
        )
        cell.fill = header_fill
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    # Add data
    for row in rows:
        sheet.append(row)

    # Style data cells
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True
            )

            cell.border = Border(
                bottom=Side(
                    style="thin",
                    color="D1D5DB"
                )
            )

            if cell.row % 2 == 0:
                cell.fill = PatternFill(
                    fill_type="solid",
                    fgColor="EEF2FF"
                )

    # Set column widths
    for column in sheet.columns:
        column_letter = column[0].column_letter
        max_length = max(
            len(str(cell.value or ""))
            for cell in column
        )

        sheet.column_dimensions[column_letter].width = min(
            max(max_length + 4, 18),
            55
        )

    # Set row heights
    for row in range(2, sheet.max_row + 1):
        sheet.row_dimensions[row].height = 55

    sheet.row_dimensions[1].height = 30

    # Make headers stay visible and enable filters
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    # Save workbook to memory
    excel_buffer = BytesIO()
    workbook.save(excel_buffer)
    excel_buffer.seek(0)

    return excel_buffer


@app.post("/download-flashcards")
def download_flashcards_excel(request: FlashcardsExcelRequest):
    headers = ["Question", "Answer"]

    rows = [
        [card.get("question", ""), card.get("answer", "")]
        for card in request.flashcards
    ]

    excel_file = create_excel(
        headers,
        rows,
        "Flashcards"
    )

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="StudyAI_Flashcards.xlsx"'
        }
    )


@app.post("/download-quiz")
def download_quiz_excel(request: QuizExcelRequest):
    headers = [
        "Question",
        "Choice A",
        "Choice B",
        "Choice C",
        "Choice D",
        "Correct Answer",
        "Explanation"
    ]

    rows = []

    for question in request.questions:
        choices = question.get("choices", {})

        rows.append([
            question.get("question", ""),
            choices.get("A", ""),
            choices.get("B", ""),
            choices.get("C", ""),
            choices.get("D", ""),
            question.get("correct_answer", ""),
            question.get("explanation", "")
        ])

    excel_file = create_excel(
        headers,
        rows,
        "Quiz"
    )

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="StudyAI_Quiz.xlsx"'
        }
    )

