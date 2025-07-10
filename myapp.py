import streamlit as st
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY")
if not SCRAPINGBEE_API_KEY:
    st.error("❗️ SCRAPINGBEE_API_KEY not found in environment variables. Please set it up in your .env file.")  
    st.stop()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("❗️ GOOGLE_API_KEY not found in environment variables. Please set it up in your .env file.")  
    st.stop()

# Set up Streamlit UI with a travel-friendly theme
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
        .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f0f2f6; /* Optional: background color for the footer */
        color: #808080; /* Optional: text color */
        text-align: center;
        padding: 10px;
        font-size: 0.8em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title and subtitle
st.markdown('<h1 class="title">✈️  my Travel Planner (AI Based)</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">my dream trip with AI having personalized recommendations for flights, hotels, and activities.</p>', unsafe_allow_html=True)
 # Display the "Made by" text using a div with the custom class
        st.markdown('<div class="footer">Made with ❤️ by Pramod Lal</div>', unsafe_allow_html=True)
# User Inputs Section
st.markdown("## 🌐 Where are you going?")
source = st.text_input("🛫 Enter Departure City OR IATA Code:", "JFK")
destination = st.text_input("🛬 Enter Departure City OR IATA Code:", "ORD")

travel_theme = st.selectbox(
    "🎭 Select Your Travel Theme:",
    ["👨‍👩‍👧 Family Vacation","🧗‍♂️ Adventure Trip","🧳 Solo Exploration","🚶 Hiking"]
)

# Divider for aesthetics
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
    except:
        return "N/A"

activity_preferences = st.text_area(
    "💡 Activities that I like to enjoy? (Like exploring historical sites,Indian foods, Cultural Experiences, Nature Walks, Museums,sport activitiess,adventure, nightlife, )",
    " Sightseeing, Indian Foods, Hiking, Shopping, Cultural Experiences, Beach, Historical sites"
)

st.markdown("## 📅 Plan Your Trip!!")
num_days = st.slider("🕒 Trip Duration (days):", 1, 15, 5)

departure_date = st.date_input("Departure Date")
return_date = st.date_input("Return Date")

# Sidebar Setup
st.sidebar.subheader("Personalize my Trip")

hotel_rating = st.sidebar.selectbox("🏨 Preferred Hotel Rating:", ["Any","3⭐", "4⭐", "5⭐"])
budget = st.sidebar.radio("💰 Budget Preference:", ["Economy", "Standard", "Luxury"])
flight_class = st.sidebar.radio("✈️ Flight Class:", ["Economy", "Business", "First Class"])

# Packing Checklist
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
# Function to fetch flights using ScrapingBee

def fetch_flights(source, destination, departure_date, return_date):
    google_flights_url = (
        f"https://www.google.com/flights?hl=en#flt={source}.{destination}.{departure_date}*"
        f"{destination}.{source}.{return_date}"
    )
    params = {
        "api_key": SCRAPINGBEE_API_KEY,
        "url": google_flights_url,
        "render_js": "true",
        "custom_google": "true"  # Required for Google scraping, costs 20 credits/request
    }
    response = requests.get("https://app.scrapingbee.com/api/v1/", params=params)
    print("ScrapingBee status:", response.status_code)
    print("ScrapingBee response:", response.text[:1000])  # Print first 1000 chars for inspection
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        # DEBUG: Print a snippet of the HTML to help user inspect structure
        print("--- FLIGHTS HTML SNIPPET ---")
        print(soup.prettify()[:2000])
        print("--- END SNIPPET ---")
        flights = []
        # Try multiple selectors for robustness
        cards = soup.find_all("div", class_="gws-flights-results__result-item")
        if not cards:
            # Try a more generic selector as fallback
            cards = soup.find_all("div", class_="U3gSDe")
        for card in cards:
            airline = card.find("div", class_="gws-flights-results__carriers")
            price = card.find("div", class_="gws-flights-results__itinerary-price")
            # Try alternative selectors if above are None
            if not airline:
                airline = card.find("span", class_="sSHqwe tPgKwe ogfYpf")
            if not price:
                price = card.find("div", class_="YMlIz FpEdX")
            times = card.find_all("span", class_="gws-flights-results__times-row")
            if not times:
                times = card.find_all("span", class_="mv1WYe")
            flights.append({
                "airline": airline.get_text(strip=True) if airline else "Unknown",
                "price": price.get_text(strip=True) if price else "N/A",
                "departure_time": times[0].get_text(strip=True) if len(times) > 0 else "N/A",
                "arrival_time": times[1].get_text(strip=True) if len(times) > 1 else "N/A"
            })
        print(f"Extracted {len(flights)} flights from HTML.")
        return {"best_flights": flights}
    else:
        # Show more detailed error from ScrapingBee
        try:
            error_json = response.json()
            st.error(f"Failed to fetch flight data from ScrapingBee: {error_json}")
        except Exception:
            st.error("Failed to fetch flight data from ScrapingBee.")
        return {"best_flights": []}
# Initialize the Gemini LLM with Google API key
llm = ChatGoogleGenerativeAI(
    google_api_key=GOOGLE_API_KEY,
    model="models/gemini-2.0-flash"#gemini-1.5-flash"
)


# Use Gemini LLM directly instead of LangChain agent (no tools needed)
# No agent initialization required; use llm.invoke(prompt) for LLM calls

def extract_cheapest_flights(flight_data):
    if not flight_data or not isinstance(flight_data, dict):
        return []
    best_flights = flight_data.get("best_flights", [])
    # Ensure price is a number for sorting, fallback to a high value if not parsable
    def parse_price(f):
        price = f.get("price", "")
        if isinstance(price, (int, float)):
            return price
        if isinstance(price, str):
            digits = ''.join(c for c in price if c.isdigit())
            try:
                return float(digits)
            except:
                return float("inf")
        return float("inf")
    sorted_flights = sorted(best_flights, key=parse_price)[:3]
    return sorted_flights

# Main function to handle the travel planning process

def travelplanner():

    booking_options = ""
    if st.button("✈️ Generate My Travel Plan"):
        with st.spinner("✈️ Fetching best/cheapest flight options ..."):
            flight_data = fetch_flights(source, destination, departure_date, return_date)
            cheapest_flights = extract_cheapest_flights(flight_data)

        with st.spinner("🔍 Searching best attractions & activities, hotels, and creating itinerary..."):
            research_prompt = (
                f"Research the best attractions and activities in {destination} for a {num_days}-day {travel_theme} trip. "
                f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. "
                f"Hotel Rating: {hotel_rating}."
            )
            research_results = llm.invoke(research_prompt)

            hotel_restaurant_prompt = (
                f"Find the best hotels and restaurants near popular attractions in {destination} for a {travel_theme} trip. "
                f"Budget: {budget}. Hotel Rating: {hotel_rating}. Preferred activities: {activity_preferences}."
            )
            hotel_restaurant_results = llm.invoke(hotel_restaurant_prompt)

            planning_prompt = (
                f"Based on the following data, create a {num_days}-day itinerary for a {travel_theme} trip to {destination}. "
                f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. Hotel Rating: {hotel_rating}. "
                f"Research: {getattr(research_results, 'content', str(research_results))}. "
                f"Flights: {json.dumps(cheapest_flights)}. Hotels & Restaurants: {getattr(hotel_restaurant_results, 'content', str(hotel_restaurant_results))}."
            )
            itinerary = llm.invoke(planning_prompt)

        st.subheader("🛫 Cheapest Flight Options")
        if cheapest_flights:
            cols = st.columns(len(cheapest_flights))
            for idx, flight in enumerate(cheapest_flights):
                with cols[idx]:
                    airline_logo = flight.get("airline_logo", "")
                    airline_name = flight.get("airline", "Unknown Airline")
                    price = flight.get("price", "Not Available")
                    total_duration = flight.get("total_duration", "N/A")
                    flights_info = flight.get("flights", [{}])
                    departure = flights_info[0].get("departure_airport", {})
                    arrival = flights_info[-1].get("arrival_airport", {})
                    airline_name = flights_info[0].get("airline", airline_name)
                    departure_time = format_datetime(departure.get("time", "N/A"))
                    arrival_time = format_datetime(arrival.get("time", "N/A"))
                    booking_link = "#"
                    st.markdown(
                        f"""
                        <div style="
                            border: 3px solid #ddd; 
                            border-radius: 10px; 
                            padding: 15px; 
                            text-align: center;
                            box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.1);
                            background-color: #FFB6C1;
                            margin-bottom: 20px;
                        ">
                            <img src="{airline_logo}" width="100" alt="Flight Logo" />
                            <h3 style="margin: 10px 0;">{airline_name}</h3>
                            <p><strong>Departure:</strong> {departure_time}</p>
                            <p><strong>Arrival:</strong> {arrival_time}</p>
                            <p><strong>Duration:</strong> {total_duration} min</p>
                            <h2 style="color: #008000;">💰 {price}</h2>
                            <a href="{booking_link}" target="_blank" style="
                                display: inline-block;
                                padding: 10px 20px;
                                font-size: 16px;
                                font-weight: bold;
                                color: #fff;
                                background-color: #007bff;
                                text-decoration: none;
                                border-radius: 5px;
                                margin-top: 10px;
                            ">🔗 Book Now</a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.warning("⚠️ No flight data available.")

        st.subheader("🏨 Hotels & Restaurants")
        # Always display plain text only
        hotel_text = getattr(hotel_restaurant_results, 'content', str(hotel_restaurant_results))
        if isinstance(hotel_text, (list, dict)):
            hotel_text = json.dumps(hotel_text, indent=2)
        st.write(hotel_text if hotel_text else "No hotel and restaurant data available.")

        st.subheader("🗺️ Your Personalized Itinerary")
        itinerary_text = getattr(itinerary, 'content', str(itinerary))
        if isinstance(itinerary_text, (list, dict)):
            itinerary_text = json.dumps(itinerary_text, indent=2)
        st.write(itinerary_text if itinerary_text else "No itinerary generated. Please check your inputs and try again.")

        st.success("✅ Travel plan generated successfully!")
        st.download_button(
            label="📥 Download Itinerary",
            data=itinerary_text if isinstance(itinerary_text, str) else str(itinerary_text),
            file_name=f"itinerary_{destination}_{departure_date}.txt",
            mime="text/plain"
        )
       

if __name__ == "__main__":
    try:
        travelplanner()
    except Exception as e:
        st.error(f"An error occurred: {e}")
