import streamlit as st
import ollama
import requests
import json
from datetime import datetime
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.callbacks.streamlit import (
    StreamlitCallbackHandler,
)

from langchain_community.chat_message_histories import (
    StreamlitChatMessageHistory,
)

from langchain.callbacks.manager import CallbackManager
from langchain_ollama.llms import OllamaLLM
from langchain.chains import LLMChain
from langchain.agents import initialize_agent, Tool, AgentType
import yaml


class MainApp:

    def run():
             

        # Define LLM model and tools
        llm_model = 'llama3.1:8b'

        # msgs = StreamlitChatMessageHistory(key="langchain_messages")


        st.title("City Tour Planner")
        st.write("Welcome! Let's plan your one-day tour!")

        # Tools
        def gather_preferences(city, available_timings="", budget=0, interests=None, starting_point=None, places_to_visit=None):
            if interests is None:
                interests = []
            if places_to_visit is None:
                places_to_visit = []

            preferences = {
                "city": city,
                "available_timings": available_timings,
                "budget": budget,
                "interests": interests,
                "starting_point": starting_point or "First attraction will be considered as the starting point.",
                "places_to_visit": places_to_visit
            }

            response = f"Planning your trip to {city}...\n"
            response += f"Available timings: {available_timings or 'Not provided, assuming full day.'}\n"
            response += f"Budget: {budget or 'Not specified, suggesting economical options.'}\n"
            response += f"Interests: {', '.join(interests) if interests else 'Not specified, suggesting a mix of activities.'}\n"
            response += f"Starting point: {preferences['starting_point']}\n"
            
            # Customizing suggestions based on places_to_visit
            if places_to_visit:
                response += f"\nYour preferred places to visit: {', '.join(places_to_visit)}.\n"
            else:
                response += f"\nNo specific places to visit provided. Suggest popular attractions based on your preferences...\n"
            
            return response

        # get todays date-time
        def get_today_date():
            return datetime.today().strftime('%Y-%m-%d')


        # get todays weather
        def get_coordinates(location):
            """
            Fetches latitude and longitude of a location using Nominatim API (OpenStreetMap).
            """
            location = "+".join(location.strip().split())

            base_url = f"https://nominatim.openstreetmap.org/search.php?q={location}&format=json"
            headers = {
            "User-Agent": "MyApp/1.0 (myemail@example.com)" 
            }

            response = requests.get(base_url, headers=headers)
            data = response.json()
            
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
            else:
                return None, None

        def get_weather_recommendations(lat, lon, api_key = "b9bc9c55af7cace1124f42c863972d89"):
            """
            Fetches weather information for a selected location using latitude and longitude and provides recommendations based on the forecast.
            
            Parameters:
                lat (float): The latitude of the location.
                lon (float): The longitude of the location.
                api_key (str): OpenWeatherMap API key.
            
            Returns:
                str: Weather summary and activity recommendations.
            """
            # OpenWeatherMap One Call API endpoint
            weather_url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric" 
            }
            
            # Fetch weather data from the API
            response = requests.get(weather_url, params=params).json()

            if response.get("cod") != 200:
                return f"Error fetching weather data: {response.get('message', 'Unknown error')}"
            
            # Extract relevant weather details
            weather = response["weather"][0]["main"]
            temperature = response["main"]["temp"]
            humidity = response["main"]["humidity"]
            wind_speed = response["wind"]["speed"]
            
            # Prepare the weather summary
            weather_summary = f"Weather at coordinates ({lat}, {lon}): {weather}, Temperature: {temperature}°C, Humidity: {humidity}%, Wind Speed: {wind_speed} m/s."
            
            return weather_summary


        # Session state to store user preferences
        if 'preferences' not in st.session_state:
            st.session_state.preferences = {}

        if "history" not in st.session_state:
            st.session_state["history"] = []

        def update_preferences(key, value):
            st.session_state.preferences[key] = value

        def update_history(role, content):
            st.session_state["history"].append({"role": role, "content": content})


        # col1, col2 = st.columns(2)
        col1, col2 = st.columns([1, 1])
        preferences_response = ""
        weather_summary = ''
        with col1.container():

            # Collecting User Preferences
            city = st.text_input("Enter the city you want to visit:")

            if city:
                update_preferences("city", city)

            available_timings = st.text_input("Enter available timings for the day (e.g., 9:00 AM - 6:00 PM):")
            if available_timings:
                update_preferences("available_timings", available_timings)

            budget = st.number_input("Enter your budget (in local currency):", min_value=0)
            if budget:
                update_preferences("budget", budget)

            interests = st.multiselect("Select your interests:", options=["culture", "adventure", "food", "shopping"])
            if interests:
                update_preferences("interests", interests)

            starting_point = st.text_input("Enter your starting point (hotel or another location):")
            if starting_point:
                update_preferences("starting_point", starting_point)

            places_to_visit = st.text_area("Enter any specific places you'd like to visit (separated by commas):")
            if places_to_visit:
                update_preferences("places_to_visit", [place.strip() for place in places_to_visit.split(",")])

            # # Show current preferences
            # st.write("Current Preferences:")
            # st.write(st.session_state.preferences)


            # city = str(st.session_state.preferences['city'])



            # Call the tool functions based on preferences
            if st.button("Save Preferences", use_container_width = True):
                if 'city' in st.session_state.preferences:
                    city = st.session_state.preferences['city']
                    preferences_response = gather_preferences(
                        city,
                        st.session_state.preferences.get("available_timings"),
                        st.session_state.preferences.get("budget"),
                        st.session_state.preferences.get("interests"),
                        st.session_state.preferences.get("starting_point"),
                        st.session_state.preferences.get("places_to_visit")
                    )
                    # st.write(preferences_response)
                    st.session_state.preferences_response = preferences_response

                else:
                    st.warning("Please provide a city to get started.")

        if 'preferences_response' in st.session_state:
                
            with col2.container():
                callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
                st_callback = StreamlitCallbackHandler(st.container())

                llm = OllamaLLM(model=llm_model, temperature=0.6, callback_manager=callback_manager)


                # st.markdown(preferences_response)

                # Get coordinates of the city
                if city:
                    lat, lon = get_coordinates(city)

                    if lat and lon:
                        # Get weather recommendations based on the coordinates
                        weather_summary = get_weather_recommendations(lat, lon)
                        # print(weather_summary)
                    else:
                        print(f"Unable to retrieve coordinates for {city}.")


                user_preferences = f""" User Preference Information- {preferences_response}\n
                                        Todays date is {get_today_date()},
                                        Current Weather Summary of {city} is {weather_summary}"""
                
                system_prompt = """ 
                                    You are a helpful and flexible Day Trip Planner Assistant. Your role is to assist users in planning a personalized one-day city trip. Collect user preferences such as the city, available timings, budget, and interests (e.g., culture, adventure, food, shopping). If no starting point is provided, assume the first attraction as the start. Suggest popular attractions based on city, budget, and interests if the user is unsure.

                                    Generate an initial itinerary with a list of places to visit, optimal sequence, transportation methods, and travel times. Ensure the plan is budget-friendly, suggesting taxis or public transport when appropriate. Dynamically update the itinerary based on new inputs, such as adding activities or adjusting timing. Check attraction status for closures or renovations and adjust the plan accordingly.

                                    Provide weather recommendations based on the forecast (e.g., indoor activities for bad weather). Maintain memory of user preferences (e.g., food, walking pace) for future personalization. Update the memory as new preferences or changes occur during the planning.

                                    Optionally, provide a visual map of the itinerary with marked locations and a detailed schedule. Ensure the assistant is always polite, responsive, and adaptable, providing the best experience based on the user's evolving needs.
                                
                                """



                chat_template = ChatPromptTemplate.from_messages(
                    [
                        ("system", system_prompt),
                        ("ai", "Hi, I'm your personalised day trip planner. How can I help you today? "),
                        ("human", "{user_input}"),
                    ]
                )

                messages_ = chat_template.format_messages(user_input = user_preferences)
                response_content = llm.invoke(messages_, config= {"callbacks": [st_callback]})
                update_history("system", system_prompt)
                update_history("human", user_preferences)
                update_history("ai", response_content)
                st.chat_message("ai").write(response_content)


                # If user inputs a new prompt, generate and draw a new response
                if prompt := st.chat_input():
                    
                    st.chat_message("human").write(prompt)
                    update_history("human", prompt)

                    next_prompt = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state["history"]]
                    st.write(next_prompt)

                    response = llm.invoke(next_prompt, config={"callbacks": [st_callback]})
                    response_content = response.content

                    # Update history with AI response
                    update_history("ai", response_content)

                    # Display AI response
                    st.chat_message("ai").write(response_content)