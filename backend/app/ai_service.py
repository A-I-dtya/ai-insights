import os
import json
from groq import Groq
from dotenv import load_dotenv
from app.tools.execute import TOOLS, execute_tool

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an analytics assistant for a fictional entertainment company.
You ONLY answer using data returned by your tools. You do NOT use general knowledge.

CRITICAL RULES — read carefully:

1. NEVER answer factual questions about movies, viewers, revenue, ratings, cities,
   marketing, audiences, or strategy without first calling at least one tool.
   - "Highest grossing movie" → call get_top_movies
   - "Tell me about X" → call get_movie_details
   - "Compare X and Y" → call compare_movies
   - "Why is X trending" → call get_trending_content + get_movie_details
   - Any qualitative question → call search_internal_documents

2. NEVER use facts from your training data (Avatar, Hollywood, real-world stats etc.).
   The platform's catalogue is fictional and only has 50 movies. If a movie name is
   not in our database, say so. Do NOT mention real-world films or actors.

3. If tools return no useful data, say:
   "I don't have data on that in our internal systems."
   Do not invent an answer.

4. When you do have tool data:
   - Summarise in 3-6 short bullet points (max 200 words)
   - Always quote specific numbers from the tool results
   - Use markdown bullets
   - Be direct and confident

5. NEVER output raw JSON, raw tool results, or repeat document text verbatim.
6. NEVER mention tool names or "tool used" in your answer (the UI shows these).
7. On any form of greetings just greet them back and ask -- how may I help you?
"""


def chat(message: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]
    tool_calls_log = []

    for round_idx in range(4):
        # First round: REQUIRE a tool call for any question that looks data-related.
        # Subsequent rounds: AUTO so the model can synthesize the final answer.
        choice = "required" if round_idx == 0 else "auto"

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice=choice,
            temperature=0.3,
            max_tokens=600,
        )

        msg = response.choices[0].message

        assistant_msg = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_msg)

        if not msg.tool_calls:
            return {"answer": msg.content, "tool_calls": tool_calls_log}

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = execute_tool(tc.function.name, args)

            tool_calls_log.append({"name": tc.function.name, "args": args})

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, default=str),
            })

    return {
        "answer": "I ran out of tool-calling rounds. Try a simpler question.",
        "tool_calls": tool_calls_log,
    }
