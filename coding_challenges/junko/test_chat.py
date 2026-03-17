import openai, os
openai.api_key = os.getenv("OPENAI_API_KEY")

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Test message: how do you greet someone in Python?"}
    ],
    max_tokens=50,
    temperature=0.5,
)
print(response["choices"][0]["message"]["content"].strip())
