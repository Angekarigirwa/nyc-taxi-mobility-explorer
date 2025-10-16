# NYC Taxi Mobility Explorer

A comprehensive data analysis dashboard for NYC taxi data with custom algorithms and interactive visualizations.

## Features

### Backend (Flask + SQLite)
- **Data Cleaning**: Robust cleaning pipeline with outlier detection and validation
- **Custom Algorithms**: 
  - Top-K frequent elements using custom min-heap implementation
  - Median calculator using two-heap approach
  - Anomaly detection with rolling z-score statistics
- **RESTful API**: Filtered queries, aggregations, and real-time KPIs
- **Database**: Normalized schema with derived features

### Frontend (Vanilla JS + Chart.js)
- **Interactive Dashboard**: Real-time KPIs and multiple chart types
- **Advanced Filtering**: Date range, fare range, hour selection
- **Visualizations**: Speed by hour, fare by weekday, pickup zones, anomaly detection
- **Responsive Design**: Modern UI with clean styling

### Custom Algorithms (No External Libraries)
1. **TopKFrequent**: Min-heap based top-K algorithm for finding most frequent pickup zones
2. **MedianCalculator**: Two-heap approach for streaming median calculation
3. **AnomalyDetector**: Rolling statistics for real-time anomaly detection

## Prerequisites
- Python 3.10+
- Modern web browser

## Quick Start

### 1. Setup Environment
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
```

### 2. Prepare Data
Place your NYC taxi CSV at `data/train.csv` or set the `RAW_CSV` environment variable:
```bash
# Example with environment variable
$env:RAW_CSV="path/to/your/taxi_data.csv"
```

### 3. Clean and Ingest Data
```bash
.\.venv\Scripts\python scripts/clean_ingest.py
```
This will:
- Clean the raw data (remove outliers, validate coordinates, etc.)
- Create derived features (speed, fare per km, rush hour flags)
- Log excluded records to `logs/cleaning_log.jsonl`
- Load data into SQLite database

### 4. Start the API Server
```bash
.\.venv\Scripts\python run.py
```
Server runs on `http://localhost:5000`

### 5. Open Dashboard
Open `frontend/index.html` in your browser. For CORS issues, use a local server:
```bash
# Python simple server
cd frontend
python -m http.server 8000
# Then visit http://localhost:8000
```

## API Endpoints

### Core Data
- `GET /api/trips` - List trips with filtering
- `GET /api/kpis` - Key performance indicators
- `GET /api/speed_by_hour` - Average speed by hour
- `GET /api/fare_by_weekday` - Average fare per km by weekday

### Custom Algorithms
- `GET /api/topk_hours` - Top-K most frequent pickup hours
- `GET /api/top_pickup_zones` - Top-K pickup zones using custom algorithm
- `GET /api/median_speed_by_hour` - Median speed for specific hour
- `GET /api/anomaly_detection` - Anomaly detection results

### Query Parameters
- `start`, `end` - Date range (ISO format)
- `min_fare`, `max_fare` - Fare range
- `hour` - Specific hour (0-23)
- `k` - Number of top results (for top-K endpoints)

## Data Schema

### Trips Table
- **Core**: pickup_datetime, dropoff_datetime, coordinates, passenger_count
- **Financial**: fare_amount, tip_amount, distance_km
- **Derived Features**:
  - `trip_speed_kmh` - Calculated speed
  - `fare_per_km` - Fare efficiency metric
  - `pickup_hour` - Hour of day (0-23)
  - `pickup_weekday` - Day of week (0-6)
  - `is_rush_hour` - Rush hour flag (0/1)

## Custom Algorithm Details

### TopKFrequent Class
- **Purpose**: Find most frequent elements without using Counter or heapq
- **Implementation**: Custom min-heap with O(k) space complexity
- **Time Complexity**: O(n log k) for n elements, top k results
- **Usage**: Pickup zone frequency analysis

### MedianCalculator Class
- **Purpose**: Calculate median of streaming data
- **Implementation**: Two-heap approach (max-heap + min-heap)
- **Space Complexity**: O(n) for n elements
- **Time Complexity**: O(log n) per insertion
- **Usage**: Median speed calculations

### AnomalyDetector Class
- **Purpose**: Detect outliers in real-time data streams
- **Implementation**: Rolling z-score with online statistics
- **Threshold**: Configurable z-score threshold (default: 2.5)
- **Usage**: Identify unusual trip patterns

## Project Structure
```
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # SQLAlchemy models
│   ├── api.py              # REST API endpoints
│   ├── db.py               # Database utilities
│   └── algorithms.py       # Custom algorithm implementations
├── scripts/
│   └── clean_ingest.py     # Data cleaning and ingestion
├── frontend/
│   ├── index.html          # Dashboard HTML
│   ├── styles.css          # Styling
│   └── app.js             # Frontend logic
├── data/                   # Data directory
├── logs/                   # Log files
├── requirements.txt        # Python dependencies
└── run.py                 # Application entry point
```
## 5-Minute Video Outline

### 1. System Overview (1 min)
- Architecture: Flask backend + SQLite + vanilla JS frontend
- Data flow: CSV → cleaning → database → API → dashboard
- Key features: custom algorithms, real-time filtering, anomaly detection

### 2. Custom Algorithms Demo (2 mins)
- Show Top-K algorithm finding most frequent pickup zones
- Demonstrate median calculator with streaming data
- Display anomaly detection identifying unusual trips
- Explain time/space complexity analysis

### 3. Dashboard Walkthrough (2 mins)
- Interactive filtering (date range, fare range, hour selection)
- Multiple chart types (line, bar, scatter plots)
- Real-time KPI updates
- Anomaly detection results display

### Technical Choices:
- **Flask**: Lightweight, flexible web framework
- **SQLite**: Embedded database, no setup required
- **Vanilla JS**: No framework dependencies, fast loading
- **Custom algorithms**: Demonstrates understanding of data structures
- **Chart.js**: Industry-standard visualization library

## Troubleshooting

### CORS Issues
If the frontend can't connect to the API, serve it through a local server:
```bash
cd frontend
python -m http.server 8000
```

### Data Loading Issues
Check the cleaning log at `logs/cleaning_log.jsonl` for excluded records and reasons.

### Database Issues
Delete `data/taxi.db` and re-run the ingestion script to start fresh.

## Performance Notes
- Custom algorithms handle up to 100K+ records efficiently
- Database queries are indexed for fast filtering
- Frontend uses Chart.js for smooth animations
- Memory usage optimized with streaming algorithms
