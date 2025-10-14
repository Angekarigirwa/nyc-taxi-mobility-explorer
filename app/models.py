from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, Float, String, DateTime


class Base(DeclarativeBase):
	pass


class Vendor(Base):
	__tablename__ = "vendors"
	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	name: Mapped[str] = mapped_column(String(64), nullable=False)


class PaymentType(Base):
	__tablename__ = "payment_types"
	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	label: Mapped[str] = mapped_column(String(32), nullable=False)


class Trip(Base):
	__tablename__ = "trips"
	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	vendor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
	pickup_datetime: Mapped[str] = mapped_column(DateTime, index=True)
	dropoff_datetime: Mapped[str] = mapped_column(DateTime, index=True)
	pickup_lat: Mapped[float] = mapped_column(Float)
	pickup_lng: Mapped[float] = mapped_column(Float)
	dropoff_lat: Mapped[float] = mapped_column(Float)
	dropoff_lng: Mapped[float] = mapped_column(Float)
	passenger_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
	distance_km: Mapped[float] = mapped_column(Float)
	fare_amount: Mapped[float] = mapped_column(Float)
	tip_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
	payment_type_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

	# Derived features
	trip_duration_min: Mapped[float] = mapped_column(Float, index=True)
	trip_speed_kmh: Mapped[float] = mapped_column(Float, index=True)
	fare_per_km: Mapped[float] = mapped_column(Float, index=True)
	pickup_hour: Mapped[int] = mapped_column(Integer, index=True)
	pickup_weekday: Mapped[int] = mapped_column(Integer, index=True)
	is_rush_hour: Mapped[int] = mapped_column(Integer, index=True)  # 0/1


