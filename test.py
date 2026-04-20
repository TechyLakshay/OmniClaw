# import requests
# import os

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # set this in env, don't hardcode

# url = "https://api.groq.com/openai/v1/chat/completions"

# headers = {
#     "Authorization": f"Bearer {GROQ_API_KEY}",
#     "Content-Type": "application/json",
# }

# payload = {
#     "model": "llama3-8b-8192",  # fast + cheap
#     "messages": [
#         {"role": "user", "content": "Explain RAG in 2 lines"}
#     ],
#     "temperature": 0.7,
# }

# response = requests.post(url, headers=headers, json=payload)

# print(response.status_code)
# print(response.json())

import requests
import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    # Optional but recommended (for tracking)
    "HTTP-Referer": "http://localhost",
    "X-Title": "mini-claw",
}

payload = {
    "model": "meta-llama/llama-3-8b-instruct",
    "messages": [
        {"role": "user", "content": "Explain agents in 2 lines"}
    ],
    "temperature": 0.7,
}

res = requests.post(url, headers=headers, json=payload, timeout=30)

print(res.status_code)
print(res.json())