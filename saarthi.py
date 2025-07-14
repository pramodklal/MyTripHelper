# --- Aviationstack Integration ---
def fetch_aviationstack_flights(source_iata, dest_iata, dep_date=None):
    """
    Fetch flight details from Aviationstack API for given source and destination IATA codes.
    dep_date: optional, format 'YYYY-MM-DD'.
    """
    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    if not api_key:
        st.warning("Aviationstack API key not found in environment variables. Set AVIATIONSTACK_API_KEY in your .env file.")
        return []
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": api_key,
        "dep_iata": source_iata,
        "arr_iata": dest_iata
    }
    if dep_date:
        params["flight_date"] = dep_date
    try:
        resp = requests.get(url, params=params, timeout=15)
        print('URL='+resp.url)
        print('Text='+resp.text)
        if resp.status_code != 200:
            st.warning(f"Aviationstack API error: {resp.status_code}")
            return []
        data = resp.json()
        flights = data.get("data", [])
        return flights
    except Exception as e:
        st.warning(f"Aviationstack API error: {e}")
        return []

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
    </style>
    """,
    unsafe_allow_html=True,
)

# Title and subtitle
st.markdown('<h1 class="title">✈️  my Travel Planner (AI Based)</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">my dream trip with AI having personalized recommendations for flights, hotels, and activities.</p>', unsafe_allow_html=True)


# User Inputs Section
st.markdown("## 🌐 Where are you going?")
st.markdown("<b>🛫 Enter Departure City OR IATA Code:</b>", unsafe_allow_html=True)
source = st.text_input("", "JFK")
st.markdown("<b>🛬 Enter Destination City OR IATA Code:</b>", unsafe_allow_html=True)
destination = st.text_input("", "ORD")

st.markdown("<b>🎭 Select Your Travel Theme:</b>", unsafe_allow_html=True)
travel_theme = st.selectbox(
    "",
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


import datetime as dt
st.markdown("## 📅 Plan Your Trip!!")
st.markdown("<b>🕒 Trip Duration (days):</b>", unsafe_allow_html=True)
num_days = st.slider("", 1, 15, 5)


# Departure and Return Date side by side
st.markdown("<b>Departure Date and Return Date:</b>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    departure_date = st.date_input("Departure Date", key="dep_date")
if isinstance(departure_date, tuple):
    dep_date = departure_date[0] if departure_date and departure_date[0] else None
else:
    dep_date = departure_date if departure_date else None
if dep_date is not None:
    try:
        return_date = dep_date + dt.timedelta(days=num_days)
    except Exception:
        return_date = dep_date
else:
    return_date = None
with col2:
    st.date_input("Return Date (auto-calculated) based on days chosen in Trip Duration ", value=return_date if return_date else dt.date.today(), disabled=True, key="ret_date")

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
from pydantic import SecretStr

llm = ChatGoogleGenerativeAI(
    api_key=SecretStr(GOOGLE_API_KEY),
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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(receiver_email, subject, body, sender_email, sender_password):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

def travelplanner():
    # --- Estimate Trip Expense Section ---
    # Simple mapping for demonstration; in production, use a reliable API or library
    country_currency = {
        "US": ("USD", "$"),
        "IN": ("INR", "₹"),
        "GB": ("GBP", "£"),
        "FR": ("EUR", "€"),
        "DE": ("EUR", "€"),
        "JP": ("JPY", "¥"),
        "AU": ("AUD", "$"),
        "CA": ("CAD", "$"),
        "SG": ("SGD", "$"),
        "AE": ("AED", "د.إ"),
        # Add more as needed
    }

    # Simple city-country mapping for demo (IATA and major city names)
    city_country = {
        # US
        "JFK": "US", "NYC": "US", "ORD": "US", "New York": "US", "Chicago": "US",
        # India
        "DEL": "IN", "BOM": "IN", "BLR": "IN", "MAA": "IN", "HYD": "IN", "CCU": "IN", "GOI": "IN", "PNQ": "IN", "COK": "IN", "AMD": "IN",
        "Delhi": "IN", "Mumbai": "IN", "Bangalore": "IN", "Chennai": "IN", "Hyderabad": "IN", "Kolkata": "IN", "Goa": "IN", "Pune": "IN", "Kochi": "IN", "Ahmedabad": "IN", "Kanpur": "IN",
        # UK/Europe/Other
        "LON": "GB", "London": "GB", "PAR": "FR", "Paris": "FR", "BER": "DE", "Berlin": "DE", "TYO": "JP", "Tokyo": "JP", "SYD": "AU", "Sydney": "AU", "TOR": "CA", "Toronto": "CA", "SIN": "SG", "Singapore": "SG", "DXB": "AE", "Dubai": "AE"
    }

    # Estimate cost per day based on budget and hotel rating
    base_cost = 100  # Default per day in USD
    if budget == "Economy":
        base_cost = 60
    elif budget == "Standard":
        base_cost = 120
    elif budget == "Luxury":
        base_cost = 250
    if hotel_rating == "4⭐":
        base_cost += 40
    elif hotel_rating == "5⭐":
        base_cost += 100
    # Add a multiplier for flight class
    if flight_class == "Business":
        base_cost *= 1.5
    elif flight_class == "First Class":
        base_cost *= 2.5

    # Estimate total cost
    total_cost_usd = base_cost * num_days

    # Get destination country and currency
    dest_input = destination.strip()
    dest_code = dest_input.upper()
    dest_name = dest_input.title()
    source_input = source.strip()
    source_code = source_input.upper()
    source_name = source_input.title()
    # Normalize for robust India detection
    india_codes = {"IN", "IND", "INDIA"}
    india_iata = {
        "DEL", "BOM", "BLR", "MAA", "HYD", "CCU", "GOI", "PNQ", "COK", "AMD", "LKO", "PAT", "JAI", "ATQ", "SXR", "IXC", "IXB", "TRV", "VNS", "BHO", "NAG", "RJA", "IXM", "IXE", "VTZ", "GAU", "DIB", "IMF", "IXA", "IXJ", "IXR", "IXU", "IDR", "RAJ", "UDR", "JLR", "JDH", "GWL", "STV", "TIR", "TCR", "IXZ", "IXG", "IXI", "IXL", "IXS", "IXT", "IXV", "IXW", "IXY", "JGB", "JRH", "JSA", "KNU", "KQH", "KUU", "LDA", "LGB", "LKO", "LUH", "MEE", "MYQ", "NDC", "NMB", "PAB", "PBD", "PGH", "PUT", "RPR", "RUP", "SAG", "SSE", "TEZ", "TNI", "TNS", "VGA", "VNS", "WGC"
    }
    india_cities = {
        # Major metros
        "Delhi", "Mumbai", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Goa", "Pune", "Kochi", "Ahmedabad", "Kanpur", "Lucknow", "Patna", "Jaipur", "Amritsar", "Srinagar", "Chandigarh", "Bagdogra", "Thiruvananthapuram", "Bhopal", "Nagpur", "Rajahmundry", "Madurai", "Mangalore", "Visakhapatnam", "Guwahati", "Dibrugarh", "Imphal", "Agartala", "Jammu", "Ranchi", "Aurangabad", "Indore", "Rajkot", "Udaipur", "Jabalpur", "Jodhpur", "Gwalior", "Surat", "Tuticorin", "Port Blair", "Belgaum", "Lilabari", "Leh", "Silchar", "Tezpur", "Vijayawada", "Mysore", "Nanded", "Nashik", "Porbandar", "Pantnagar", "Puttaparthi", "Raipur", "Rupsi", "Shirdi", "Solapur", "Tiruchirappalli", "Agra", "Madhubani", "Warangal",
        # Major religious cities
        "Varanasi", "Haridwar", "Rishikesh", "Ayodhya", "Mathura", "Vrindavan", "Tirupati", "Puri", "Dwarka", "Somnath", "Ujjain", "Nashik", "Shirdi", "Bodh Gaya", "Sarnath", "Amarnath", "Vaishno Devi", "Kedarnath", "Badrinath", "Gangotri", "Yamunotri", "Kanchipuram", "Madurai", "Rameswaram", "Kanyakumari", "Sabarimala", "Palani", "Guruvayur", "Pushkar", "Ajmer", "Pandharpur", "Trimbakeshwar", "Hampi", "Srisailam", "Chidambaram", "Kalahasti", "Tiruvannamalai", "Kanchipuram", "Kottayam", "Kollur", "Murudeshwar", "Gokarna", "Hemkund Sahib", "Patna Sahib", "Nanded Sahib", "Golden Temple", "Hazur Sahib", "Takht Sri Damdama Sahib", "Takht Sri Keshgarh Sahib", "Takht Sri Patna Sahib", "Takht Sri Hazur Sahib"
    }
    # Try both IATA code and city name for India
    dest_country_code = city_country.get(dest_code, city_country.get(dest_name, "US"))
    source_country_code = city_country.get(source_code, city_country.get(source_name, "US"))
    # For demo, use static conversion rates (in production, use a currency API)
    conversion_rates = {"USD": 1, "INR": 83, "GBP": 0.78, "EUR": 0.92, "JPY": 157, "AUD": 1.5, "CAD": 1.36, "SGD": 1.35, "AED": 3.67}

    # If destination is India by code, IATA, or city name, always show INR, else always show USD
    is_india = (
        dest_country_code == "IN" or
        dest_code in india_iata or
        dest_name in india_cities or
        dest_code in india_codes or
        dest_name in india_codes or
        dest_input.lower() == "india"
    )
    if is_india:
        currency_code = "INR"
        currency_symbol = "₹"
        rate = conversion_rates["INR"]
        total_cost_local = int(total_cost_usd * rate)
    else:
        currency_code = "USD"
        currency_symbol = "$"
        rate = 1
        total_cost_local = int(total_cost_usd)

    # (Moved to after itinerary)
    # --- Aviationstack Flight Results Section ---
    st.markdown("### ✈️ Aviationstack Flight Results (Free Tier Demo)")
    # Use the IATA codes from user input
    dep_code = source.strip().upper()
    arr_code = destination.strip().upper()
    # Optionally use departure date
    dep_date_str = None
    if dep_date:
        dep_date_str = dep_date.strftime('%Y-%m-%d')
    if st.button("🔍 Show Flights (Aviationstack)"):
        st.info(f"Fetching flights from {dep_code} to {arr_code} on {dep_date_str if dep_date_str else 'any date'}...")
        flights = fetch_aviationstack_flights(dep_code, arr_code, dep_date_str)
        if flights:
            for f in flights[:5]:  # Show up to 5 flights
                flight_num = f.get('flight', {}).get('iata', 'N/A')
                airline = f.get('airline', {}).get('name', 'N/A')
                dep_time = f.get('departure', {}).get('scheduled', 'N/A')
                arr_time = f.get('arrival', {}).get('scheduled', 'N/A')
                st.info(f"Flight: {flight_num} | Airline: {airline}\n\nDeparture: {dep_time} | Arrival: {arr_time}")
        else:
            st.warning("No flights found or API limit reached.")
    booking_options = ""

    # Email input for download/send
    user_email = st.text_input("📧 Enter your email to receive the itinerary (optional):", "", key="email_before_download")

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
        #else:
            #st.warning("⚠️ No flight data available.")

        st.subheader("🏨 Hotels & Restaurants")
        # Always display plain text only
        hotel_text = getattr(hotel_restaurant_results, 'content', str(hotel_restaurant_results))
        if isinstance(hotel_text, (list, dict)):
            hotel_text = json.dumps(hotel_text, indent=2)
        st.write(hotel_text if hotel_text else "No hotel and restaurant data available.")

        st.subheader("🗺️ Your Personalized Itinerary")
        itinerary_text = getattr(itinerary, 'content', str(itinerary))
        itinerary_text = getattr(itinerary, 'content', str(itinerary))
        if isinstance(itinerary_text, (list, dict)):
            itinerary_text = json.dumps(itinerary_text, indent=2)
        st.write(itinerary_text if itinerary_text else "No itinerary generated. Please check your inputs and try again.")
        # Store itinerary in session state for email sending

        # Prepare trip expense summary for download/email
        expense_text = f"\n\n---\n💸 Approximate Trip Expense: {currency_symbol}{total_cost_local:,} {currency_code} ({num_days} days, {budget} budget, {hotel_rating}, {flight_class})\n"
        itinerary_with_expense = (itinerary_text if isinstance(itinerary_text, str) else str(itinerary_text)) + expense_text
        st.session_state['itinerary_text'] = itinerary_with_expense

        # Show approximate trip expense at the bottom (UI)
        st.markdown(f"<div style='background:#e6f7ff;padding:10px;border-radius:10px;margin-bottom:10px;margin-top:18px;'><b>💸 Approximate Trip Expense:</b> <span style='font-size:22px;color:#007bff;font-weight:bold;'>{currency_symbol}{total_cost_local:,} {currency_code}</span> <br><span style='font-size:13px;color:#888;'>({num_days} days, {budget} budget, {hotel_rating}, {flight_class})</span></div>", unsafe_allow_html=True)

        st.success("✅ Travel plan generated successfully!")
        download_clicked = st.download_button(
            label="📥 Download my Itinerary",
            data=itinerary_with_expense,
            file_name=f"itinerary_{destination}_{departure_date}.txt",
            mime="text/plain"
        )

        # If email is provided and download is clicked, send the itinerary
        if download_clicked and user_email:
            sender_email = os.getenv("SENDER_EMAIL")
            sender_password = os.getenv("SENDER_EMAIL_PASSWORD")
            if not sender_email or not sender_password:
                st.error("Sender email credentials are not set in the environment.")
            else:
                with st.spinner("Sending itinerary to your email..."):
                    subject = f"Your Travel Itinerary for {destination}"
                    body = itinerary_with_expense
                    success, msg = send_email(user_email, subject, body, sender_email, sender_password)
                    if success:
                        st.success(f"✅ Itinerary sent to your email: {user_email}")
                    else:
                        st.error(f"Failed to send email: {msg}")
    # Email input and send button only shown after plan generation, handled above



if __name__ == "__main__":
    try:
        travelplanner()
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Footer
st.markdown(
    """
    <hr style='margin-top:40px;margin-bottom:10px;border:1px solid #eee;'>
    <div style='text-align:center; color:#888; font-size:16px; margin-bottom:20px;'>
        Made with ❤️ by Pramod Lal for my daughter who loves to travel during her ongoing summer vacation.
    </div>
    """,
    unsafe_allow_html=True
)