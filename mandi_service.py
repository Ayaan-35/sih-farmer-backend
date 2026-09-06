import os
# pyrefly: ignore[missing-import]
import numpy as np
import pandas as pd

def haversine_np(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371.0
    lat1, lon1 = np.radians(float(lat1)), np.radians(float(lon1))
    lat2, lon2 = np.radians(lat2.astype(float)), np.radians(lon2.astype(float))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return earth_radius_km * c

class MandiService:
    def __init__(self, csv_path: str):
        if not os.path.exists(csv_path):
            self.df = pd.DataFrame(columns=['date', 'crop', 'district', 'modal_price', 'latitude', 'longitude', 'mandi_name'])
            return
        self.df = pd.read_csv(csv_path)
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df['crop'] = self.df['crop'].astype(str).str.strip().str.lower()
        self.df['district'] = self.df['district'].astype(str).str.strip().str.lower()
        self.df['modal_price'] = pd.to_numeric(self.df['modal_price'], errors='coerce')
        self.df['latitude'] = pd.to_numeric(self.df['latitude'], errors='coerce')
        self.df['longitude'] = pd.to_numeric(self.df['longitude'], errors='coerce')
        self.df = self.df.dropna(subset=['latitude', 'longitude', 'modal_price'])

    def get_price_trends(self, crop: str, district: str) -> dict:
        query_crop = crop.strip().lower()
        query_district = district.strip().lower()
        filtered = self.df[(self.df['crop'] == query_crop) & (self.df['district'] == query_district)].sort_values('date')
        if filtered.empty:
            return {"error": f"No data found for crop '{crop}' in district '{district}'."}
        latest_record = filtered.iloc[-1]
        latest_date = latest_record['date']
        current_modal_price = latest_record['modal_price']
        seven_days_ago = latest_date - pd.Timedelta(days=7)
        seven_day_window = filtered[(filtered['date'] >= seven_days_ago) & (filtered['date'] <= latest_date)]
        seven_day_avg = seven_day_window['modal_price'].mean()
        return {
            "crop": crop.capitalize(),
            "district": district.capitalize(),
            "latest_date": latest_date.strftime("%Y-%m-%d"),
            "current_modal_price_per_quintal": round(float(current_modal_price), 2),
            "7_day_average_price": round(float(seven_day_avg), 2),
            "trend_status": "Upward" if current_modal_price >= seven_day_avg else "Downward",
        }

    def get_nearby_mandis(self, farmer_lat: float, farmer_lon: float, top_k: int = 3) -> list:
        if self.df.empty:
            return []
        mandis = self.df.groupby(['mandi_name', 'district'])[['latitude', 'longitude']].first().reset_index()
        mandis['distance_km'] = haversine_np(farmer_lat, farmer_lon, mandis['latitude'], mandis['longitude'])
        closest = mandis.sort_values('distance_km').head(top_k).reset_index(drop=True)
        closest['distance_km'] = closest['distance_km'].round(2)
        return closest[['mandi_name', 'district', 'latitude', 'longitude', 'distance_km']].to_dict(orient='records')
