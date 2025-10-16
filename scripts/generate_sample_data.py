#!/usr/bin/env python3
"""
Sample data generator for NYC Taxi Dashboard testing.
Generates realistic taxi trip data with proper distributions and patterns.
"""

import os
import random
import pandas as pd
from datetime import datetime, timedelta
import math

# NYC bounds (Manhattan + parts of other boroughs)
NYC_BOUNDS = {
    "lat_min": 40.4774,
    "lat_max": 40.9176,
    "lng_min": -74.2591,
    "lng_max": -73.7004,
}

# Popular pickup/dropoff zones in NYC
POPULAR_ZONES = [
    (40.7589, -73.9851),  # Times Square
    (40.7505, -73.9934),  # Penn Station
    (40.7614, -73.9776),  # Central Park
    (40.7505, -73.9934),  # Grand Central
    (40.6892, -74.0445),  # Statue of Liberty area
    (40.7061, -74.0087),  # Wall Street
    (40.7282, -73.7949),  # JFK Airport area
    (40.6413, -73.7781),  # LaGuardia Airport area
    (40.6892, -74.0445),  # Battery Park
    (40.7505, -73.9934),  # Port Authority
]

# Rush hour patterns (higher probability during these hours)
RUSH_HOURS = [7, 8, 9, 16, 17, 18, 19]

# Weekend vs weekday patterns
WEEKEND_HOURS = [0, 1, 2, 3, 4, 5, 6, 22, 23]  # More activity late night/early morning

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers."""
    R = 6371.0088  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def generate_coordinates():
    """Generate realistic pickup/dropoff coordinates."""
    # 70% chance to use popular zones
    if random.random() < 0.7:
        pickup = random.choice(POPULAR_ZONES)
        # Dropoff within reasonable distance
        lat_offset = random.uniform(-0.05, 0.05)
        lng_offset = random.uniform(-0.05, 0.05)
        dropoff = (
            max(NYC_BOUNDS["lat_min"], min(NYC_BOUNDS["lat_max"], pickup[0] + lat_offset)),
            max(NYC_BOUNDS["lng_min"], min(NYC_BOUNDS["lng_max"], pickup[1] + lng_offset))
        )
    else:
        # Random coordinates within NYC bounds
        pickup = (
            random.uniform(NYC_BOUNDS["lat_min"], NYC_BOUNDS["lat_max"]),
            random.uniform(NYC_BOUNDS["lng_min"], NYC_BOUNDS["lng_max"])
        )
        dropoff = (
            random.uniform(NYC_BOUNDS["lat_min"], NYC_BOUNDS["lat_max"]),
            random.uniform(NYC_BOUNDS["lng_min"], NYC_BOUNDS["lng_max"])
        )
    
    return pickup, dropoff

def generate_trip_datetime(base_date, is_weekend=False):
    """Generate realistic trip datetime."""
    # Choose hour based on patterns
    if is_weekend:
        # Weekend: more activity in late night/early morning
        hour = random.choices(
            list(range(24)),
            weights=[2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2],
            k=1
        )[0]
    else:
        # Weekday: rush hour patterns
        if random.random() < 0.4:  # 40% chance of rush hour
            hour = random.choice(RUSH_HOURS)
        else:
            hour = random.randint(0, 23)
    
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    pickup_time = base_date.replace(hour=hour, minute=minute, second=second)
    
    # Trip duration: 5-60 minutes, with some very long trips
    duration_minutes = random.choices(
        [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 90, 120],
        weights=[10, 15, 15, 15, 10, 10, 8, 6, 4, 3, 2, 1, 1],
        k=1
    )[0]
    
    dropoff_time = pickup_time + timedelta(minutes=duration_minutes)
    
    return pickup_time, dropoff_time

def generate_fare_data(distance_km, duration_minutes, is_weekend=False, is_rush_hour=False):
    """Generate realistic fare data."""
    # Base fare
    base_fare = 2.50
    
    # Distance fare (per km)
    distance_fare = distance_km * 1.50
    
    # Time fare (per minute when stopped)
    time_fare = duration_minutes * 0.50 * random.uniform(0.1, 0.3)  # Some idle time
    
    # Weekend/rush hour surcharge
    surcharge = 0
    if is_weekend:
        surcharge += 1.00
    if is_rush_hour:
        surcharge += 0.50
    
    # Add some randomness
    fare_amount = base_fare + distance_fare + time_fare + surcharge
    fare_amount *= random.uniform(0.8, 1.2)  # ±20% variation
    
    # Tip (0-30% of fare)
    tip_amount = fare_amount * random.uniform(0, 0.3)
    
    return round(fare_amount, 2), round(tip_amount, 2)

def generate_sample_data(num_trips=10000, start_date=None):
    """Generate sample taxi trip data."""
    if start_date is None:
        start_date = datetime(2024, 1, 1)
    
    trips = []
    
    for i in range(num_trips):
        # Generate date (spread over 3 months)
        trip_date = start_date + timedelta(days=random.randint(0, 90))
        is_weekend = trip_date.weekday() >= 5
        
        # Generate coordinates
        pickup_coords, dropoff_coords = generate_coordinates()
        pickup_lat, pickup_lng = pickup_coords
        dropoff_lat, dropoff_lng = dropoff_coords
        
        # Calculate distance
        distance_km = haversine_distance(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
        
        # Skip very short or very long trips
        if distance_km < 0.1 or distance_km > 50:
            continue
    
        # Generate datetime
        pickup_time, dropoff_time = generate_trip_datetime(trip_date, is_weekend)
        duration_minutes = (dropoff_time - pickup_time).total_seconds() / 60
        
        # Check if rush hour
        is_rush_hour = pickup_time.hour in RUSH_HOURS
        
        # Generate fare data
        fare_amount, tip_amount = generate_fare_data(distance_km, duration_minutes, is_weekend, is_rush_hour)
        
        # Calculate derived features
        trip_speed_kmh = (distance_km / duration_minutes) * 60 if duration_minutes > 0 else 0
        fare_per_km = fare_amount / distance_km if distance_km > 0 else 0
        
        # Skip unrealistic speeds
        if trip_speed_kmh > 120 or trip_speed_kmh < 1:
            continue
        
        trip = {
            'tpep_pickup_datetime': pickup_time.strftime('%Y-%m-%d %H:%M:%S'),
            'tpep_dropoff_datetime': dropoff_time.strftime('%Y-%m-%d %H:%M:%S'),
            'pickup_latitude': pickup_lat,
            'pickup_longitude': pickup_lng,
            'dropoff_latitude': dropoff_lat,
            'dropoff_longitude': dropoff_lng,
            'passenger_count': random.choices([1, 2, 3, 4, 5, 6], weights=[40, 30, 15, 10, 3, 2])[0],
            'fare_amount': fare_amount,
            'tip_amount': tip_amount,
        }
        
        trips.append(trip)
    
    return pd.DataFrame(trips)

def main():
    """Generate sample data and save to CSV."""
    print("Generating sample NYC taxi data...")
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Generate data
    df = generate_sample_data(num_trips=15000)
    
    # Save to CSV
    output_path = "data/train.csv"
    df.to_csv(output_path, index=False)
    
    print(f"Generated {len(df)} trips")
    print(f"Data saved to {output_path}")
    print(f"Date range: {df['tpep_pickup_datetime'].min()} to {df['tpep_pickup_datetime'].max()}")
    print(f"Fare range: ${df['fare_amount'].min():.2f} to ${df['fare_amount'].max():.2f}")
    print(f"Distance range: {df.apply(lambda x: haversine_distance(x['pickup_latitude'], x['pickup_longitude'], x['dropoff_latitude'], x['dropoff_longitude']), axis=1).min():.2f} to {df.apply(lambda x: haversine_distance(x['pickup_latitude'], x['pickup_longitude'], x['dropoff_latitude'], x['dropoff_longitude']), axis=1).max():.2f} km")

if __name__ == "__main__":
    main()
