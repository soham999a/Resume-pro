import openai
import sys

# Set the API key
api_key = "your-openai-api-key-here"  # Replace with your actual API key
openai.api_key = api_key

print(f"OpenAI API Key: {'*' * 5}{api_key[-4:] if api_key else 'Not set'}")
print(f"OpenAI module: {openai}")

try:
    # Try to call the OpenAI API
    print("Calling OpenAI API...")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, are you using the OpenAI API or mock data?"}
        ],
        temperature=0.7,
        max_tokens=100
    )

    # Print the response
    print("OpenAI API response received successfully")
    print(f"Response: {response.choices[0].message.content}")
    print("This confirms we are using the REAL OpenAI API, not mock data")

except Exception as e:
    print(f"Error calling OpenAI API: {e}")
    print("This suggests we would be using MOCK DATA in the application")
    sys.exit(1)
