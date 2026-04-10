"""Multimodal Route & Rate Optimization Module
Analyzes real-time data to recommend optimal routes and competitive rates
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class TrafficCondition(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HEAVY = "heavy"
    GRIDLOCK = "gridlock"


class WeatherCondition(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    STORMY = "stormy"
    FOGGY = "foggy"


@dataclass
class Location:
    lat: float
    lng: float
    address: str = ""


@dataclass
class RouteSegment:
    origin: Location
    destination: Location
    distance_km: float
    estimated_time_hours: float
    traffic: TrafficCondition
    weather: WeatherCondition
    toll_cost: float = 0.0


@dataclass
class Carrier:
    id: str
    name: str
    rating: float
    on_time_percentage: float
    base_rate_per_km: float
    capabilities: List[str]


@dataclass
class RouteOption:
    route_id: str
    segments: List[RouteSegment]
    total_distance_km: float
    total_time_hours: float
    total_cost: float
    carrier: Carrier
    score: float


@dataclass
class RateQuote:
    quote_id: str
    carrier: Carrier
    origin: Location
    destination: Location
    cargo_type: str
    weight_kg: float
    volume_m3: float
    rate_per_kg: float
    total_cost: float
    estimated_delivery: datetime
    validity_hours: int = 24
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class RouteOptimizer:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.carriers = self._load_carriers()
        self.route_cache = {}

    def _default_config(self) -> Dict:
        return {
            "max_route_time_hours": 48,
            "max_cost_factor": 1.5,
            "traffic_weight": 0.25,
            "weather_weight": 0.20,
            "cost_weight": 0.30,
            "carrier_rating_weight": 0.25,
            "cache_ttl_seconds": 300,
        }

    def _load_carriers(self) -> List[Carrier]:
        return [
            Carrier("C001", "Swift Logistics", 4.5, 95.2, 2.50, ["express", " refrigerated"]),
            Carrier("C002", "EcoTrans", 4.2, 92.8, 2.20, ["standard", "eco-friendly"]),
            Carrier("C003", "FastFreight", 4.8, 98.5, 3.10, ["express", "priority"]),
            Carrier("C004", "GlobalCargo", 4.0, 89.5, 1.90, ["standard", "international"]),
            Carrier("C005", "ColdChain Pro", 4.6, 96.1, 3.50, ["refrigerated", "pharma"]),
        ]

    def get_traffic_data(self, location: Location) -> TrafficCondition:
        traffic_levels = list(TrafficCondition)
        weights = [0.3, 0.4, 0.2, 0.1]
        return random.choices(traffic_levels, weights=weights)[0]

    def get_weather_data(self, location: Location) -> WeatherCondition:
        weather_conditions = list(WeatherCondition)
        weights = [0.4, 0.3, 0.15, 0.05, 0.1]
        return random.choices(weather_conditions, weights=weights)[0]

    def calculate_distance(self, origin: Location, destination: Location) -> float:
        lat_diff = abs(destination.lat - origin.lat)
        lng_diff = abs(destination.lng - origin.lng)
        return ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111

    def estimate_time_based_on_conditions(
        self, distance_km: float, traffic: TrafficCondition, weather: WeatherCondition
    ) -> float:
        base_speed = 60
        traffic_factors = {
            TrafficCondition.LOW: 1.0,
            TrafficCondition.MODERATE: 0.85,
            TrafficCondition.HEAVY: 0.60,
            TrafficCondition.GRIDLOCK: 0.30,
        }
        weather_factors = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.CLOUDY: 0.95,
            WeatherCondition.RAINY: 0.80,
            WeatherCondition.STORMY: 0.50,
            WeatherCondition.FOGGY: 0.70,
        }
        effective_speed = base_speed * traffic_factors[traffic] * weather_factors[weather]
        return distance_km / effective_speed

    def calculate_segment_cost(
        self, distance_km: float, carrier: Carrier, weather: WeatherCondition
    ) -> float:
        base_cost = distance_km * carrier.base_rate_per_km
        weather_surcharge = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.CLOUDY: 1.0,
            WeatherCondition.RAINY: 1.15,
            WeatherCondition.STORMY: 1.30,
            WeatherCondition.FOGGY: 1.10,
        }
        return base_cost * weather_surcharge[weather]

    def score_route(self, route: RouteOption) -> float:
        cfg = self.config
        time_score = 1 - (route.total_time_hours / cfg["max_route_time_hours"])
        cost_score = 1 / (1 + route.total_cost / 10000)
        carrier_score = route.carrier.rating / 5.0
        on_time_score = route.carrier.on_time_percentage / 100
        traffic_penalty = sum(
            0.1 for seg in route.segments if seg.traffic in [TrafficCondition.HEAVY, TrafficCondition.GRIDLOCK]
        )
        weather_penalty = sum(
            0.15 for seg in route.segments if seg.weather in [WeatherCondition.STORMY, WeatherCondition.FOGGY]
        )
        score = (
            cfg["traffic_weight"] * time_score
            + cfg["cost_weight"] * cost_score
            + cfg["carrier_rating_weight"] * (carrier_score * 0.5 + on_time_score * 0.5)
            - traffic_penalty
            - weather_penalty
        )
        return max(0, min(1, score))

    def optimize_route(
        self,
        origin: Location,
        destination: Location,
        cargo_type: str = "standard",
        prefer_fast: bool = False,
        prefer_cheap: bool = False,
    ) -> List[RouteOption]:
        cache_key = f"{origin.lat},{origin.lng}-{destination.lat},{destination.lng}"
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]

        num_segments = random.randint(1, 3)
        segments = []
        current = origin
        total_distance = self.calculate_distance(origin, destination)

        for i in range(num_segments + 1):
            ratio = (i + 1) / (num_segments + 1)
            segment_dest = Location(
                lat=origin.lat + (destination.lat - origin.lat) * ratio,
                lng=origin.lng + (destination.lng - origin.lng) * ratio,
                address=f"Waypoint {i+1}",
            )
            distance = self.calculate_distance(current, segment_dest)
            traffic = self.get_traffic_data(segment_dest)
            weather = self.get_weather_data(segment_dest)
            time = self.estimate_time_based_on_conditions(distance, traffic, weather)
            segments.append(
                RouteSegment(
                    origin=current,
                    destination=segment_dest,
                    distance_km=distance,
                    estimated_time_hours=time,
                    traffic=traffic,
                    weather=weather,
                    toll_cost=random.uniform(10, 50),
                )
            )
            current = segment_dest

        routes = []
        for carrier in self.carriers:
            if cargo_type not in carrier.capabilities and cargo_type != "standard":
                continue
            total_time = sum(s.estimated_time_hours for s in segments)
            segment_costs = [self.calculate_segment_cost(s.distance_km, carrier, s.weather) for s in segments]
            total_cost = sum(segment_costs) + sum(s.toll_cost for s in segments)

            route = RouteOption(
                route_id=f"RT-{carrier.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                segments=segments,
                total_distance_km=total_distance,
                total_time_hours=total_time,
                total_cost=total_cost,
                carrier=carrier,
                score=0.0,
            )
            route.score = self.score_route(route)
            routes.append(route)

        routes.sort(key=lambda x: x.score, reverse=True)

        if prefer_fast:
            routes.sort(key=lambda x: x.total_time_hours)
        elif prefer_cheap:
            routes.sort(key=lambda x: x.total_cost)

        self.route_cache[cache_key] = routes[:5]
        return routes[:5]

    def get_rate_quote(
        self,
        origin: Location,
        destination: Location,
        cargo_type: str,
        weight_kg: float,
        volume_m3: float,
        carrier_id: Optional[str] = None,
    ) -> List[RateQuote]:
        carrier = None
        if carrier_id:
            carrier = next((c for c in self.carriers if c.id == carrier_id), None)
        carriers_to_quote = [carrier] if carrier else self.carriers

        distance = self.calculate_distance(origin, destination)
        quotes = []

        for c in carriers_to_quote:
            weight_charge = weight_kg * c.base_rate_per_km
            volume_charge = volume_m3 * c.base_rate_per_km * 100
            chargeable = max(weight_charge, volume_charge)
            total_cost = chargeable * (1 + random.uniform(0.05, 0.15))

            base_time_hours = distance / 60
            delivery_buffer = random.uniform(4, 24)
            estimated_delivery = datetime.now() + timedelta(hours=base_time_hours + delivery_buffer)

            quotes.append(
                RateQuote(
                    quote_id=f"QT-{c.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    carrier=c,
                    origin=origin,
                    destination=destination,
                    cargo_type=cargo_type,
                    weight_kg=weight_kg,
                    volume_m3=volume_m3,
                    rate_per_kg=total_cost / weight_kg,
                    total_cost=total_cost,
                    estimated_delivery=estimated_delivery,
                )
            )

        return sorted(quotes, key=lambda x: x.total_cost)

    def analyze_route_alternatives(
        self, origin: Location, destination: Location, cargo_type: str = "standard"
    ) -> Dict:
        routes = self.optimize_route(origin, destination, cargo_type)
        return {
            "optimal_route": routes[0] if routes else None,
            "alternative_routes": routes[1:4],
            "analysis_timestamp": datetime.now().isoformat(),
            "route_count": len(routes),
            "summary": {
                "fastest_route": min(routes, key=lambda x: x.total_time_hours).route_id if routes else None,
                "cheapest_route": min(routes, key=lambda x: x.total_cost).route_id if routes else None,
                "best_rated_carrier": max(routes, key=lambda x: x.carrier.rating).carrier.name if routes else None,
            },
        }
