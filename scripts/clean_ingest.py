from __future__ import annotations

import os
import math
import json
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine


RAW_CSV = os.environ.get("RAW_CSV", "data/train.csv")
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/taxi.db")
LOG_FILE = os.environ.get("CLEAN_LOG", "logs/cleaning_log.jsonl")


NYC_BOUNDS = {
	"lat_min": 40.4774,
	"lat_max": 40.9176,
	"lng_min": -74.2591,
	"lng_max": -73.7004,
}


def within_nyc(lat: float, lng: float) -> bool:
	return (
		NYC_BOUNDS["lat_min"] <= lat <= NYC_BOUNDS["lat_max"]
		and NYC_BOUNDS["lng_min"] <= lng <= NYC_BOUNDS["lng_max"]
	)


def haversine_km(lat1, lon1, lat2, lon2) -> float:
	R = 6371.0088
	phi1, phi2 = math.radians(lat1), math.radians(lat2)
	dphi = math.radians(lat2 - lat1)
	dlam = math.radians(lon2 - lon1)
	a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
	return 2 * R * math.asin(math.sqrt(a))


def is_rush(hour: int) -> int:
	return 1 if hour in {7, 8, 9, 16, 17, 18} else 0


def log_exclusion(record: dict) -> None:
	os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
	with open(LOG_FILE, "a", encoding="utf-8") as f:
		f.write(json.dumps(record) + "\n")


def clean_and_ingest() -> None:
	if not os.path.exists(RAW_CSV):
		raise FileNotFoundError(f"Raw CSV not found at {RAW_CSV}")

	df = pd.read_csv(RAW_CSV)

	# Expected column names may vary by NYC taxi version; adapt mappings
	column_map = {
		"pickup_datetime": ["tpep_pickup_datetime", "lpep_pickup_datetime", "pickup_datetime"],
		"dropoff_datetime": ["tpep_dropoff_datetime", "lpep_dropoff_datetime", "dropoff_datetime"],
		"pickup_lat": ["pickup_latitude", "PULocationLat", "pickup_lat"],
		"pickup_lng": ["pickup_longitude", "PULocationLng", "pickup_lng"],
		"dropoff_lat": ["dropoff_latitude", "DOLocationLat", "dropoff_lat"],
		"dropoff_lng": ["dropoff_longitude", "DOLocationLng", "dropoff_lng"],
		"passenger_count": ["passenger_count"],
		"fare_amount": ["fare_amount"],
		"tip_amount": ["tip_amount"],
	}

	def resolve(col_key: str):
		for c in column_map[col_key]:
			if c in df.columns:
				return c
		return None

	# Rename to normalized columns when present
	renamed = {}
	for k in column_map:
		src = resolve(k)
		if src:
			renamed[src] = k
	if renamed:
		df = df.rename(columns=renamed)

	# Parse times
	for tcol in ["pickup_datetime", "dropoff_datetime"]:
		df[tcol] = pd.to_datetime(df[tcol], errors="coerce")

	# Filter invalid times
	valid_time = df["pickup_datetime"].notna() & df["dropoff_datetime"].notna()
	df = df[valid_time]

	# Geospatial sanity
	geo_mask = (
		df[["pickup_lat", "pickup_lng", "dropoff_lat", "dropoff_lng"]].notna().all(axis=1)
	)
	df = df[geo_mask]

	# NYC bounds and positive fares
	keep = []
	for idx, row in df.iterrows():
		if not within_nyc(row["pickup_lat"], row["pickup_lng"]):
			log_exclusion({"reason": "pickup_outside_nyc", "row": int(idx)})
			continue
		if not within_nyc(row["dropoff_lat"], row["dropoff_lng"]):
			log_exclusion({"reason": "dropoff_outside_nyc", "row": int(idx)})
			continue
		# Derived geometric distance
		d = haversine_km(row["pickup_lat"], row["pickup_lng"], row["dropoff_lat"], row["dropoff_lng"])
		minutes = (row["dropoff_datetime"] - row["pickup_datetime"]).total_seconds() / 60.0
		if minutes <= 0 or d <= 0:
			log_exclusion({"reason": "non_positive_duration_or_distance", "row": int(idx)})
			continue
		fare = float(row.get("fare_amount", 0) or 0)
		if fare <= 0:
			log_exclusion({"reason": "non_positive_fare", "row": int(idx)})
			continue
		# Compute features
		hour = int(row["pickup_datetime"].hour)
		keep.append({
			"pickup_datetime": row["pickup_datetime"],
			"dropoff_datetime": row["dropoff_datetime"],
			"pickup_lat": float(row["pickup_lat"]),
			"pickup_lng": float(row["pickup_lng"]),
			"dropoff_lat": float(row["dropoff_lat"]),
			"dropoff_lng": float(row["dropoff_lng"]),
			"passenger_count": int(row.get("passenger_count", 0) or 0),
			"distance_km": float(d),
			"fare_amount": float(fare),
			"tip_amount": float(row.get("tip_amount", 0) or 0),
			"trip_duration_min": float(minutes),
			"trip_speed_kmh": float((d / minutes) * 60.0),
			"fare_per_km": float(fare / d if d > 0 else 0),
			"pickup_hour": hour,
			"pickup_weekday": int(row["pickup_datetime"].weekday()),
			"is_rush_hour": is_rush(hour),
		})

	clean_df = pd.DataFrame(keep)

	# Remove extreme outliers using IQR on distance and fare_per_km
	def iqr_filter(series: pd.Series, k: float = 3.0):
		q1, q3 = series.quantile(0.25), series.quantile(0.75)
		iqr = q3 - q1
		low, high = q1 - k * iqr, q3 + k * iqr
		return (series >= low) & (series <= high)

	mask = iqr_filter(clean_df["distance_km"]) & iqr_filter(clean_df["fare_per_km"]) & iqr_filter(clean_df["trip_speed_kmh"]) 
	clean_df = clean_df[mask]

	# Ingest into DB
	engine = create_engine(DB_URL, future=True)
	clean_df.to_sql("trips", engine, if_exists="append", index=False)
	print(f"Ingested {len(clean_df)} rows into database at {DB_URL}")


if __name__ == "__main__":
	clean_and_ingest()


