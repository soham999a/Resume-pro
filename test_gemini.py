import google.generativeai as genai
import sys

# Set the API key
api_key = "your-gemini-api-key-here"  # Replace with your actual API key
# Alternative key
alt_key = "your-alternative-gemini-api-key-here"  # Replace with your alternative API key

print(f"Gemini API Key: {'*' * 5}{api_key[-4:] if api_key else 'Not set'}")

try:
    # Configure the Gemini API
    genai.configure(api_key=api_key)

    # Try to call the Gemini API
    print("Calling Gemini API...")
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content("Hello, are you using the Gemini API or mock data?")

    # Print the response
    print("Gemini API response received successfully")
    print(f"Response: {response.text}")
    print("This confirms we are using the REAL Gemini API, not mock data")

except Exception as e:
    print(f"Error calling Gemini API with first key: {e}")
    print("Trying alternative key...")

    try:
        # Configure the Gemini API with alternative key
        genai.configure(api_key=alt_key)

        # Try to call the Gemini API
        print("Calling Gemini API with alternative key...")
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content("Hello, are you using the Gemini API or mock data?")

        # Print the response
        print("Gemini API response received successfully")
        print(f"Response: {response.text}")
        print("This confirms we are using the REAL Gemini API, not mock data")

    except Exception as e2:
        print(f"Error calling Gemini API with alternative key: {e2}")
        print("This suggests we would be using MOCK DATA in the application")
        sys.exit(1)
