
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
    import re

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are StudyAI. Return valid JSON only. Never use markdown or trailing commas."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_completion_tokens=6000
    )

    result = response.choices[0].message.content

    if not result:
        raise ValueError("AI returned an empty response.")

    result = result.strip()

    if result.startswith("```"):
        result = re.sub(r"^```(?:json)?\s*", "", result)
        result = re.sub(r"\s*```$", "", result)

    result = re.sub(r",\s*([}\]])", r"\1", result)

    try:
        return json.loads(result)

    except json.JSONDecodeError:
        repair_response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a JSON repair tool. Fix the supplied text "
                        "so it becomes valid JSON. Preserve all information. "
                        "Return JSON only, without markdown."
                    )
                },
                {
                    "role": "user",
                    "content": result
                }
            ],
            max_completion_tokens=6000
        )

        repaired = repair_response.choices[0].message.content.strip()

        if repaired.startswith("```"):
            repaired = re.sub(r"^```(?:json)?\s*", "", repaired)
            repaired = re.sub(r"\s*```$", "", repaired)

        repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

        return json.loads(repaired)


