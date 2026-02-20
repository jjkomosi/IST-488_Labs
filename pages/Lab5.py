import requests
import json
import streamlit as st
from openai import OpenAI

st.title("Weather Bot")
st.write("Enter a city to get, weather data, weather-appropriate clothing suggestions and outdoor activity ideas!")

open_weather_api_key = st.secrets["OPEN_WEATHER_API_KEY"]
# location in form City, State, Country
# e.g., Syracuse, NY, US
# default units is degrees Fahrenheit
def get_current_weather(location, api_key, units='imperial'):
    url = (
        f'https://api.openweathermap.org/data/2.5/weather'
        f'?q={location}&appid={api_key}&units={units}'
        )
    response = requests.get(url)
    if response.status_code == 401:
     raise Exception('Authentication failed: Invalid API key (401 Unauthorized)')
    if response.status_code == 404:
        error_message = response.json().get('message')
        raise Exception(f'404 error: {error_message}')
    data = response.json()
    temp = data['main']['temp']
    feels_like = data['main']['feels_like']
    temp_min = data['main']['temp_min']
    temp_max = data['main']['temp_max']
    humidity = data['main']['humidity']
    return {'location': location,
        'temperature': round(temp, 2),
        'feels_like': round(feels_like, 2),
        'temp_min': round(temp_min, 2),
        'temp_max': round(temp_max, 2),
        'humidity': round(humidity, 2)
        }

# --- Tool definition for OpenAI ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather for a given location. Use this whenever the user wants weather-based clothing or activity suggestions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state/country, e.g. 'Syracuse, NY, US' or 'Lima, Peru'"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# --- UI ---
location_input = st.text_input("Enter a city (e.g., Syracuse, NY, US):", placeholder="Syracuse, NY, US")

if st.button("Get Suggestions"):
    if not location_input.strip():
        location_input = "Syracuse, NY"

    openai_api_key = st.secrets["OPENAI_API_KEY"]

    client = OpenAI(api_key=openai_api_key)

    user_message = f"What should I wear today in {location_input}? Also suggest some outdoor activities."

    with st.spinner("Thinking..."):
        try:
            # Step 1: Send user message with tools
            messages = [
                {"role": "system", "content": "You are a helpful assistant that provides clothing suggestions and outdoor activity recommendations based on current weather conditions."},
                {"role": "user", "content": user_message}
            ]

            response = client.chat.completions.create(
                model="gpt-5",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            # Step 2: Check if the model wants to call the weather function
            if assistant_message.tool_calls:
                # Process each tool call
                messages.append(assistant_message)

                for tool_call in assistant_message.tool_calls:
                    if tool_call.function.name == "get_current_weather":
                        args = json.loads(tool_call.function.arguments)
                        loc = args.get("location", "Syracuse, NY")

                        # Call the actual weather API
                        weather_data = get_current_weather(loc, open_weather_api_key)

                        # Display weather info
                        st.subheader(f"🌤️ Current Weather in {weather_data['location']}")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Temperature", f"{weather_data['temperature']}°F")
                        col2.metric("Feels Like", f"{weather_data['feels_like']}°F")
                        col3.metric("Humidity", f"{weather_data['humidity']}%")
                        st.write(f"**Conditions:** {weather_data['description'].title()}")
                        st.write(f"**High/Low:** {weather_data['temp_max']}°F / {weather_data['temp_min']}°F")

                        # Append the tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(weather_data)
                        })

                # Step 3: Get final response with weather data included
                final_response = client.chat.completions.create(
                    model="gpt-5",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )

                st.subheader("👕 Clothing & Activity Suggestions")
                st.write(final_response.choices[0].message.content)

            else:
                # Model responded without calling a tool
                st.write(assistant_message.content)

        except Exception as e:
            st.error(f"Error: {e}")