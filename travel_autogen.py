
import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from autogen.agentchat import AssistantAgent

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("❗️ GOOGLE_API_KEY not found in environment variables. Please set it up in your .env file.")
    st.stop()

# Streamlit UI setup
st.set_page_config(page_title="🌐 myTravel Planner", layout="wide")
st.markdown(
    """
    <style>
        .title {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: #ff5733;
        }
        .subtitle {
            text-align: center;
            font-size: 20px;
            color: #555;
        }
        .stSlider > div {
            background-color: #f9f9f9;
            padding: 10px;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title and subtitle
st.markdown('<h1 class="title">✈️  my Travel Planner (AI Based)</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">my dream trip with AI having personalized recommendations for flights, hotels, and activities.</p>', unsafe_allow_html=True)

# User Inputs Section
st.markdown("## 🌐 Where are you going?")
source = st.text_input("🛫 Departure City (IATA Code):", "EWR")
destination = st.text_input("🛬 Destination (IATA Code):", "ORD")
travel_theme = st.selectbox(
    "🎭 Select Your Travel Theme:",
    ["👨‍👩‍👧 Family Vacation","🧗‍♂️ Adventure Trip","🧳 Solo Exploration","🚶 Hiking"]
)
st.markdown("--")
st.markdown(
    f"""
    <div style="
        text-align: center; 
        padding: 15px; 
        background-color: #ADD8E6; 
        border-radius: 15px; 
        margin-top: 10px;
    ">
        <h3>my {travel_theme} to {destination} is about to start!</h3>
        <p>Let's find the best deals in flights, stays, and experiences for unforgettable and happy journey.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

def format_datetime(iso_string):
    try:
        dt = datetime.strptime(iso_string, "%Y-%m-%d %H:%M")
        return dt.strftime("%b-%d, %Y | %I:%M %p")
    except Exception:
        return "N/A"

activity_preferences = st.text_area(
    "💡 Activities that I like to enjoy? (Like exploring historical sites,Indian foods, Cultural Experiences, Nature Walks, Museums,sport activitiess,adventure, nightlife, )",
    " Sightseeing, Indian Foods, Hiking, Shopping, Cultural Experiences, Beach, Historical sites"
)
st.markdown("## 📅 Plan Your Trip!!")
num_days = st.slider("🕒 Trip Duration (days):", 1, 15, 5)
departure_date = st.date_input("Departure Date")
return_date = st.date_input("Return Date")
st.sidebar.subheader("Personalize my Trip")
budget = st.sidebar.radio("💰 Budget Preference:", ["Economy", "Standard", "Luxury"])
hotel_rating = st.sidebar.selectbox("🏨 Preferred Hotel Rating:", ["Any","3⭐", "4⭐", "5⭐"])
flight_class = st.sidebar.radio("✈️ Flight Class:", ["Economy", "Business", "First Class"])
st.sidebar.subheader("🎒 Packing Checklist")
packing_list = {
    "🧳 Luggage": True,
    "👕 Clothes": True,
    "🩴 Comfortable Footwear": True,
    "📱 Mobile Phone & Charger": True,
    "💊 Medications & First-Aid": True,
    "💻 Laptop/Tablet": False,
    "📷 Camera": False,
    "📚 Books/Kindle": False,
    "🕶️ Sunglasses & Sunscreen": False,
    "📖 Travel Guidebook": False
}
for item, checked in packing_list.items():
    st.sidebar.checkbox(item, value=checked)

# Define AutoGen agents

# Define AutoGen agents (fixed model name and agent instantiation)


llm_config_google = {
    "config_list": [
        {
            "model": "gemini-2.0-flash",
            "api_key": GOOGLE_API_KEY,
        }
    ]
}


travel_researcher = AssistantAgent(
    name="TravelResearcherAgent",
    llm_config=llm_config_google,
    system_message="You are a travel researcher. Find attractions, activities, and general info for the user's destination."
)
hotel_finder = AssistantAgent(
    name="HotelRestaurantFinderAgent",
    llm_config=llm_config_google,
    system_message="You are a hotel and restaurant expert. Find the best hotels and restaurants near the user's destination and preferences."
)
travel_planner = AssistantAgent(
    name="TravelPlannerAgent",
    llm_config=llm_config_google,
    system_message="You are a travel planner. Create a detailed itinerary based on research, hotels, restaurants, and user preferences."
)

def mytravelplanner():
    if st.button("✈️ Generate My Travel Plan"):
        research_prompt = (
            f"Research the best attractions and activities in {destination} for a {num_days}-day {travel_theme} trip. "
            f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. "
            f"Hotel Rating: {hotel_rating}."
        )
        hotel_prompt = (
            f"Find the best hotels and restaurants near popular attractions in {destination} for a {travel_theme} trip. "
            f"Budget: {budget}. Hotel Rating: {hotel_rating}. Preferred activities: {activity_preferences}."
        )
        planning_prompt = (
            f"Based on the following data, create a {num_days}-day itinerary for a {travel_theme} trip to {destination}. "
            f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. Hotel Rating: {hotel_rating}."
        )


        # Use list of messages for generate_reply (and fix duplicate legacy code at bottom)
        with st.spinner("🔍 Researching best attractions &  activities as per your choice..."):
            research_content = travel_researcher.generate_reply([
                {"role": "user", "content": research_prompt}
            ])
            if not isinstance(research_content, str):
                research_content = str(research_content)

        with st.spinner("🏩 Searching for hotels & restaurants suitable for you..."):
            hotel_content = hotel_finder.generate_reply([
                {"role": "user", "content": hotel_prompt}
            ])
            if not isinstance(hotel_content, str):
                hotel_content = str(hotel_content)

        with st.spinner("🗺️ Creating your personalized itinerary for your trip.."):
            planner_input = (
                f"{planning_prompt}\n"
                f"Research: {research_content}\n"
                f"Hotels & Restaurants: {hotel_content}"
            )
            itinerary_content = travel_planner.generate_reply([
                {"role": "user", "content": planner_input}
            ])
            if not isinstance(itinerary_content, str):
                itinerary_content = str(itinerary_content)

        st.subheader("🛫 Attractions & Activities")
        st.write(research_content)
        st.subheader("🏨 Hotels & Restaurants")
        st.write(hotel_content)
        st.subheader("🗺️ Your Personalized Itinerary")
        st.write(itinerary_content)
        st.success("✅ Travel plan generated successfully!")
        st.download_button(
            label="📥 Download Itinerary",
            data=itinerary_content,
            file_name=f"itinerary_{destination}_{departure_date}.txt",
            mime="text/plain"
        )



if __name__ == "__main__":
    try:
        mytravelplanner()
    except Exception as e:
        st.error(f"An error occurred: {e}")