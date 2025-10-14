from __future__ import annotations

from datetime import datetime
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select, func, and_, between
from .models import Trip
from .algorithms import TopKFrequent, MedianCalculator, AnomalyDetector


api_bp = Blueprint("api", __name__)


def _get_session():
	return current_app.session_factory()


@api_bp.get("/trips")
def list_trips():
	session = _get_session()
	try:
		query = select(Trip)
		# Optional filters: start, end (ISO), min_fare, max_fare, hour
		start = request.args.get("start")
		end = request.args.get("end")
		min_fare = request.args.get("min_fare", type=float)
		max_fare = request.args.get("max_fare", type=float)
		hour = request.args.get("hour", type=int)

		conds = []
		if start:
			try:
				start_dt = datetime.fromisoformat(start)
				conds.append(Trip.pickup_datetime >= start_dt)
			except Exception:
				pass
		if end:
			try:
				end_dt = datetime.fromisoformat(end)
				conds.append(Trip.pickup_datetime <= end_dt)
			except Exception:
				pass
		if min_fare is not None and max_fare is not None:
			conds.append(between(Trip.fare_amount, min_fare, max_fare))
		elif min_fare is not None:
			conds.append(Trip.fare_amount >= min_fare)
		elif max_fare is not None:
			conds.append(Trip.fare_amount <= max_fare)
		if hour is not None:
			conds.append(Trip.pickup_hour == hour)

		if conds:
			query = query.where(and_(*conds))

		query = query.limit(200)
		rows = session.execute(query).scalars().all()
		result = [
			{
				"id": r.id,
				"pickup_datetime": r.pickup_datetime.isoformat(),
				"dropoff_datetime": r.dropoff_datetime.isoformat(),
				"distance_km": r.distance_km,
				"fare_amount": r.fare_amount,
				"tip_amount": r.tip_amount,
				"trip_speed_kmh": r.trip_speed_kmh,
				"fare_per_km": r.fare_per_km,
			}
			for r in rows
		]
		return jsonify(result)
	finally:
		session.close()


@api_bp.get("/kpis")
def kpis():
	session = _get_session()
	try:
		# Apply same filters as trips endpoint
		conds = []
		start = request.args.get("start")
		end = request.args.get("end")
		min_fare = request.args.get("min_fare", type=float)
		max_fare = request.args.get("max_fare", type=float)
		hour = request.args.get("hour", type=int)

		if start:
			try:
				start_dt = datetime.fromisoformat(start)
				conds.append(Trip.pickup_datetime >= start_dt)
			except Exception:
				pass
		if end:
			try:
				end_dt = datetime.fromisoformat(end)
				conds.append(Trip.pickup_datetime <= end_dt)
			except Exception:
				pass
		if min_fare is not None and max_fare is not None:
			conds.append(between(Trip.fare_amount, min_fare, max_fare))
		elif min_fare is not None:
			conds.append(Trip.fare_amount >= min_fare)
		elif max_fare is not None:
			conds.append(Trip.fare_amount <= max_fare)
		if hour is not None:
			conds.append(Trip.pickup_hour == hour)

		q = select(
			func.count(Trip.id),
			func.avg(Trip.trip_speed_kmh),
			func.avg(Trip.fare_per_km),
			func.min(Trip.pickup_datetime),
			func.max(Trip.pickup_datetime),
		)
		if conds:
			q = q.where(and_(*conds))
		
		count_, avg_speed, avg_fpk, min_time, max_time = session.execute(q).one()
		return jsonify({
			"trip_count": int(count_ or 0),
			"avg_speed_kmh": float(avg_speed or 0),
			"avg_fare_per_km": float(avg_fpk or 0),
			"date_range": {
				"start": min_time.isoformat() if min_time else None,
				"end": max_time.isoformat() if max_time else None,
			}
		})
	finally:
		session.close()


@api_bp.get("/speed_by_hour")
def speed_by_hour():
	session = _get_session()
	try:
		q = select(Trip.pickup_hour, func.avg(Trip.trip_speed_kmh)).group_by(Trip.pickup_hour).order_by(Trip.pickup_hour)
		rows = session.execute(q).all()
		return jsonify([{ "hour": int(h), "avg_speed_kmh": float(s or 0)} for h, s in rows])
	finally:
		session.close()


# Custom Top-K frequent pickup hour buckets without heapq/Counter
@api_bp.get("/topk_hours")
def topk_hours():
	k = request.args.get("k", default=5, type=int)
	session = _get_session()
	try:
		# Stream counts from DB as (hour, count) then apply manual min-heap
		rows = session.execute(select(Trip.pickup_hour, func.count()).group_by(Trip.pickup_hour)).all()
		pairs = [(int(h), int(c)) for h, c in rows]

		# Manual min-heap implementation
		class MinHeap:
			def __init__(self):
				self.a = []  # list of (count, hour)
			def _parent(self, i): return (i - 1) // 2
			def _left(self, i): return 2 * i + 1
			def _right(self, i): return 2 * i + 2
			def _swap(self, i, j): self.a[i], self.a[j] = self.a[j], self.a[i]
			def push(self, item):
				self.a.append(item)
				i = len(self.a) - 1
				while i > 0 and self.a[self._parent(i)][0] > self.a[i][0]:
					p = self._parent(i)
					self._swap(i, p)
					i = p
			def pop(self):
				if not self.a: return None
				self._swap(0, len(self.a) - 1)
				minv = self.a.pop()
				i = 0
				while True:
					l, r = self._left(i), self._right(i)
					small = i
					if l < len(self.a) and self.a[l][0] < self.a[small][0]: small = l
					if r < len(self.a) and self.a[r][0] < self.a[small][0]: small = r
					if small == i: break
					self._swap(i, small)
					i = small
				return minv
			def top(self):
				return self.a[0] if self.a else None
			def __len__(self): return len(self.a)

		heap = MinHeap()
		for hour, cnt in pairs:
			item = (cnt, hour)
			if len(heap) < k:
				heap.push(item)
			else:
				top = heap.top()
				if top and cnt > top[0]:
					heap.pop()
					heap.push(item)

		# Extract heap contents sorted desc by count
		res = []
		while len(heap) > 0:
			cnt, hour = heap.pop()
			res.append({"hour": hour, "count": cnt})
		res.reverse()
		return jsonify(res)
	finally:
		session.close()


@api_bp.get("/fare_by_weekday")
def fare_by_weekday():
	session = _get_session()
	try:
		q = select(Trip.pickup_weekday, func.avg(Trip.fare_per_km)).group_by(Trip.pickup_weekday).order_by(Trip.pickup_weekday)
		rows = session.execute(q).all()
		weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
		return jsonify([{ "weekday": weekdays[int(w)], "avg_fare_per_km": float(f or 0)} for w, f in rows])
	finally:
		session.close()


@api_bp.get("/top_pickup_zones")
def top_pickup_zones():
	session = _get_session()
	try:
		k = int(request.args.get("k", 10))
		
		# Get all pickup coordinates
		q = select(Trip.pickup_lat, Trip.pickup_lng)
		rows = session.execute(q).all()
		
		# Round coordinates to create zones (0.01 degree ≈ 1km)
		zones = {}
		for lat, lng in rows:
			zone_key = (round(lat, 2), round(lng, 2))
			zones[zone_key] = zones.get(zone_key, 0) + 1
		
		# Use custom Top-K algorithm
		topk = TopKFrequent(k)
		for zone, count in zones.items():
			topk.add(zone, count)
		
		result = []
		for zone, count in topk.get_top_k():
			result.append({
				"lat": zone[0],
				"lng": zone[1],
				"count": count
			})
		
		return jsonify(result)
	finally:
		session.close()


@api_bp.get("/median_speed_by_hour")
def median_speed_by_hour():
	session = _get_session()
	try:
		hour = int(request.args.get("hour", 0))
		
		# Get all speeds for the hour
		q = select(Trip.trip_speed_kmh).where(Trip.pickup_hour == hour)
		rows = session.execute(q).all()
		speeds = [float(row[0]) for row in rows]
		
		# Use custom median calculator
		median_calc = MedianCalculator()
		for speed in speeds:
			median_calc.add(speed)
		
		median_speed = median_calc.get_median()
		
		return jsonify({
			"hour": hour,
			"median_speed_kmh": median_speed,
			"sample_count": len(speeds)
		})
	finally:
		session.close()


@api_bp.get("/anomaly_detection")
def anomaly_detection():
	session = _get_session()
	try:
		# Get recent trips for anomaly detection
		q = select(Trip.trip_speed_kmh, Trip.fare_per_km, Trip.distance_km).order_by(Trip.pickup_datetime.desc()).limit(1000)
		rows = session.execute(q).all()
		
		if not rows:
			return jsonify({"anomalies": [], "threshold": 0})
		
		# Calculate rolling statistics for anomaly detection
		speeds = [float(row[0]) for row in rows]
		fares = [float(row[1]) for row in rows]
		distances = [float(row[2]) for row in rows]
		
		# Simple z-score based anomaly detection
		def calculate_z_scores(data):
			if len(data) < 2:
				return [0] * len(data)
			mean = sum(data) / len(data)
			variance = sum((x - mean) ** 2 for x in data) / (len(data) - 1)
			std_dev = variance ** 0.5
			if std_dev == 0:
				return [0] * len(data)
			return [(x - mean) / std_dev for x in data]
		
		speed_z = calculate_z_scores(speeds)
		fare_z = calculate_z_scores(fares)
		distance_z = calculate_z_scores(distances)
		
		# Find anomalies (z-score > 2.5)
		anomalies = []
		for i, (speed, fare, dist) in enumerate(rows):
			if abs(speed_z[i]) > 2.5 or abs(fare_z[i]) > 2.5 or abs(distance_z[i]) > 2.5:
				anomalies.append({
					"index": i,
					"speed_kmh": float(speed),
					"fare_per_km": float(fare),
					"distance_km": float(dist),
					"speed_z_score": speed_z[i],
					"fare_z_score": fare_z[i],
					"distance_z_score": distance_z[i]
				})
		
		return jsonify({
			"anomalies": anomalies[:50],  # Limit to 50 most recent anomalies
			"threshold": 2.5,
			"total_checked": len(rows)
		})
	finally:
		session.close()


