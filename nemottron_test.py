# pip install openai
import os

from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1", api_key=os.environ["NVIDIA_API_KEY"]
)

r = client.chat.completions.create(
    model="nvidia/nemotron-3.5-super-vl-120b-a12b",
    messages=[{"role": "user", "content": "What is 17*23? Use the tool."}],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "calc",
                "description": "Evaluate an arithmetic expression",
                "parameters": {
                    "type": "object",
                    "properties": {"expr": {"type": "string"}},
                    "required": ["expr"],
                },
            },
        }
    ],
    max_tokens=512,
)
print(r.choices[0].message)
