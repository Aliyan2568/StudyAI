import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = "openai/gpt-oss-20b"


def ask_ai(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are StudyAI, an educational assistant. Only use the provided lecture material. Do not invent facts."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_completion_tokens=3000
    )

    return response.choices[0].message.content


def ask_ai_json(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are StudyAI. Only use the provided lecture material. Return valid JSON only, with no markdown or extra text."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_completion_tokens=3000
    )

    result = response.choices[0].message.content.strip()

    if result.startswith("```"):
        result = result.split("\n", 1)[1]
        result = result.rsplit("```", 1)[0].strip()

    return json.loads(result)
