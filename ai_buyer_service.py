import math
import os
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# API CONFIGURATION
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ---------------------------------------------------------------------------
# 1. DATA COLLECTION & MOCK DATABASE
# ---------------------------------------------------------------------------
RAW_BUYERS_DATA = [
    {
        "id": 1,
        "name": "Sahyadri Agro Traders",
        "crop": "Tomato",
        "min_qty": 50,
        "max_qty": 500,
        "district": "Nashik",
        "contact": "+91-9822001122"
    },
    {
        "id": 2,
        "name": "Maha Krishi Co.",
        "crop": "Onion",
        "min_qty": 100,
        "max_qty": 2000,
        "district": "Pune",
        "contact": "+91-9822003344"
    },
    {
        "id": 3,
        "name": "Greenfield Exports",
        "crop": "Tomato",
        "min_qty": 200,
        "max_qty": 1000,
        "district": "Nashik",
        "contact": "+91-9822005566"
    },
    {
        "id": 4,
        "name": "Vidarbha Cotton & Grain",
        "crop": "Soybean",
        "min_qty": 20,
        "max_qty": 300,
        "district": "Nagpur",
        "contact": "+91-9822007788"
    }
]

DISTRICT_COORDINATES = {
    "nashik": (19.9975, 73.7898),
    "pune": (18.5204, 73.8567),
    "nagpur": (21.1458, 79.0882),
    "mumbai": (19.0760, 72.8777)
}


# ---------------------------------------------------------------------------
# 2. DATA CLEANING & HELPER FUNCTIONS
# ---------------------------------------------------------------------------
def clean_buyer_record(buyer: dict) -> dict:
    cleaned = buyer.copy()
    cleaned["name"] = buyer["name"].strip()
    cleaned["crop"] = buyer["crop"].strip().title()
    cleaned["district"] = buyer["district"].strip().title()
    return cleaned


def clean_buyers_database(raw_list: list[dict]) -> list[dict]:
    return [clean_buyer_record(b) for b in raw_list]


BUYERS_DATABASE = clean_buyers_database(RAW_BUYERS_DATA)


def calculate_haversine_distance(coord1: tuple, coord2: tuple) -> float:
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371.0

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ---------------------------------------------------------------------------
# 3. FILTER BUYERS
# ---------------------------------------------------------------------------
def filter_buyers(crop: str, quantity: float, district: str) -> list[dict]:
    clean_crop = crop.strip().title()
    clean_district = district.strip().title()
    filtered = []

    farmer_coords = DISTRICT_COORDINATES.get(clean_district.lower())

    for buyer in BUYERS_DATABASE:
        crop_match = buyer["crop"] == clean_crop
        district_match = buyer["district"] == clean_district
        qty_match = buyer["min_qty"] <= quantity <= buyer["max_qty"]

        if crop_match and district_match and qty_match:
            b_data = buyer.copy()
            buyer_coords = DISTRICT_COORDINATES.get(buyer["district"].lower())

            if farmer_coords and buyer_coords:
                b_data["distance_km"] = round(calculate_haversine_distance(farmer_coords, buyer_coords), 2)
            else:
                b_data["distance_km"] = 0.0

            filtered.append(b_data)

    return filtered


# ---------------------------------------------------------------------------
# 4. DUAL AI ADVISORY (GEMINI API WITH OFFLINE FALLBACK)
# ---------------------------------------------------------------------------
def ask_gemini_advisory(user_prompt: str, market_data: dict) -> str:
    """
    Calls the live Gemini API using the official Google GenAI SDK.
    Gracefully falls back to the deterministic local rule engine if offline or on error.
    """
    # 1. Attempt call with Gemini API
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            system_instruction = (
                "You are an expert Indian agricultural market advisor for smallholder farmers. "
                "Analyze the provided APMC market data and the farmer's question. "
                "Provide clear, practical, supportive selling advice in under 4 sentences. "
                "Crucial: Always respond in the EXACT language used by the farmer (Marathi, Hindi, or English)."
            )

            prompt_content = f"Market Ground Truth Data:\n{market_data}\n\nFarmer Query:\n{user_prompt}"

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3
                )
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[Gemini API Notice: Falling back to local engine due to: {e}]")

    # 2. Local Fallback Rule Engine
    crop = market_data.get("crop", "Produce")
    district = market_data.get("district", "your district")
    trend = market_data.get("trend_status", "Stable")
    price = market_data.get("current_modal_price_per_quintal", 0)
    avg_price = market_data.get("7_day_average_price", 0)

    is_marathi = any(w in user_prompt for w in ["विकू", "भाव", "कधी", "थांबू", "कांदा", "टोमॅटो"])
    is_hindi = any(w in user_prompt.lower() for w in ["bechu", "bhaav", "kya", "kab", "mandi", "daam"])

    if trend == "Upward":
        if is_marathi:
            return f"{district} बाजारात {crop} चा सध्याचा दर ₹{price}/क्विंटल आहे आणि बाजार तेजीत आहे. पुढील १-२ दिवस थांबू शकता."
        elif is_hindi:
            return f"{district} मंडी में {crop} का भाव ₹{price}/क्विंटल पर बढ़ रहा है. आप 1-2 दिन रुक कर बेहतर दाम पा सकते हैं."
        else:
            return f"In {district}, the price of {crop} is currently ₹{price}/quintal, trending upward compared to the 7-day average of ₹{avg_price}. Demand is strong; you may hold for 24-48 hours."
    else:
        if is_marathi:
            return f"{district} बाजारात {crop} चा दर घसरला आहे. नुकसान टाळण्यासाठी ताबडतोब विक्री करा."
        elif is_hindi:
            return f"{district} मंडी में {crop} का भाव गिर रहा है. तुरंत नजदीकी सत्यापित खरीदारों को बेचने की सलाह दी जाती है."
        else:
            return f"In {district}, the current modal price for {crop} is ₹{price}/quintal, below the 7-day average. We recommend selling immediately to verified local buyers."