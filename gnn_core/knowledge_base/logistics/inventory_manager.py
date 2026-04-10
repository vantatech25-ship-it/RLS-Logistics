"""Predictive Inventory Management Module
Machine learning-based demand forecasting and automated replenishment
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class ReorderLevel(Enum):
    CRITICAL = "critical"
    LOW = "low"
    ADEQUATE = "adequate"
    OPTIMAL = "optimal"
    OVERSTOCKED = "overstocked"


@dataclass
class Product:
    sku: str
    name: str
    category: str
    unit_cost: float
    unit_price: float
    reorder_point: int
    reorder_quantity: int
    lead_time_days: int
    safety_stock: int
    current_stock: int = 0
    max_stock: int = 1000


@dataclass
class DemandForecast:
    product_sku: str
    predicted_demand: float
    confidence: float
    forecast_period_days: int
    trend: str
    seasonality_factor: float
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReplenishmentOrder:
    order_id: str
    product_sku: str
    quantity: int
    estimated_cost: float
    expected_delivery: datetime
    priority: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StockoutRisk:
    product_sku: str
    risk_level: str
    days_until_stockout: int
    recommended_action: str
    confidence_score: float


class InventoryManager:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.products: Dict[str, Product] = {}
        self.demand_history: Dict[str, List[int]] = {}
        self.forecast_cache: Dict[str, DemandForecast] = {}

    def _default_config(self) -> Dict:
        return {
            "forecast_horizon_days": 30,
            "confidence_threshold": 0.80,
            "critical_stockout_threshold_days": 3,
            "low_stock_threshold_days": 7,
            "seasonality_weight": 0.2,
            "trend_weight": 0.3,
            "demand_variability_weight": 0.5,
        }

    def add_product(self, product: Product) -> bool:
        self.products[product.sku] = product
        if product.sku not in self.demand_history:
            self.demand_history[product.sku] = []
        return True

    def record_demand(self, sku: str, quantity: int, date: Optional[datetime] = None) -> bool:
        if sku not in self.demand_history:
            self.demand_history[sku] = []
        self.demand_history[sku].append(quantity)
        if len(self.demand_history[sku]) > 365:
            self.demand_history[sku] = self.demand_history[sku][-365:]
        if sku in self.products:
            self.products[sku].current_stock = max(0, self.products[sku].current_stock - quantity)
        return True

    def simulate_demand_history(self, sku: str, days: int = 90) -> List[int]:
        if sku not in self.products:
            return []
        product = self.products[sku]
        base_demand = max(1, product.reorder_quantity // 7)
        history = []
        for day in range(days):
            weekday_factor = 1.2 if (datetime.now() - timedelta(days=days - day)).weekday() < 5 else 0.8
            seasonal_factor = 1.0 + 0.2 * (day % 30) / 30
            random_factor = random.uniform(0.7, 1.3)
            demand = int(base_demand * weekday_factor * seasonal_factor * random_factor)
            history.append(max(0, demand))
        self.demand_history[sku] = history
        return history

    def calculate_moving_average(self, sku: str, window: int = 7) -> float:
        if sku not in self.demand_history or not self.demand_history[sku]:
            return 0.0
        history = self.demand_history[sku][-window:]
        return sum(history) / len(history) if history else 0.0

    def detect_trend(self, sku: str) -> Tuple[str, float]:
        if sku not in self.demand_history or len(self.demand_history[sku]) < 14:
            return "stable", 0.0
        recent = self.demand_history[sku][-7:]
        previous = self.demand_history[sku][-14:-7]
        recent_avg = sum(recent) / len(recent)
        previous_avg = sum(previous) / len(previous) if previous else 1
        trend_ratio = recent_avg / previous_avg if previous_avg > 0 else 1.0
        if trend_ratio > 1.15:
            return "increasing", min(1.0, (trend_ratio - 1) * 2)
        elif trend_ratio < 0.85:
            return "decreasing", min(1.0, (1 - trend_ratio) * 2)
        return "stable", 0.0

    def calculate_seasonality(self, sku: str) -> float:
        if sku not in self.demand_history or len(self.demand_history[sku]) < 30:
            return 1.0
        recent_demand = sum(self.demand_history[sku][-7:])
        avg_demand = self.calculate_moving_average(sku, 30)
        return recent_demand / (avg_demand * 7) if avg_demand > 0 else 1.0

    def calculate_demand_variability(self, sku: str) -> float:
        if sku not in self.demand_history or len(self.demand_history[sku]) < 7:
            return 0.0
        history = self.demand_history[sku][-30:]
        if not history:
            return 0.0
        mean = sum(history) / len(history)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std_dev = variance ** 0.5
        cv = std_dev / mean if mean > 0 else 0
        return min(1.0, cv)

    def forecast_demand(self, sku: str) -> DemandForecast:
        if sku in self.forecast_cache:
            cache_age = datetime.now() - self.forecast_cache[sku].generated_at
            if cache_age < timedelta(hours=1):
                return self.forecast_cache[sku]
        if sku not in self.products:
            return DemandForecast(sku, 0, 0, 0, "unknown", 0)
        cfg = self.config
        base_demand = self.calculate_moving_average(sku, 14)
        trend, trend_factor = self.detect_trend(sku)
        seasonality = self.calculate_seasonality(sku)
        variability = self.calculate_demand_variability(sku)
        confidence = 1 - (cfg["seasonality_weight"] * abs(seasonality - 1) + cfg["demand_variability_weight"] * variability)
        confidence = max(0.5, min(0.99, confidence))
        trend_multiplier = 1 + trend_factor if trend == "increasing" else 1 - trend_factor
        predicted = base_demand * trend_multiplier * seasonality
        forecast = DemandForecast(
            product_sku=sku,
            predicted_demand=max(0, predicted * cfg["forecast_horizon_days"]),
            confidence=confidence,
            forecast_period_days=cfg["forecast_horizon_days"],
            trend=trend,
            seasonality_factor=seasonality,
        )
        self.forecast_cache[sku] = forecast
        return forecast

    def calculate_reorder_point(self, sku: str) -> int:
        if sku not in self.products:
            return 0
        product = self.products[sku]
        avg_daily_demand = self.calculate_moving_average(sku, 14)
        safety_stock = product.safety_stock
        reorder_point = int(avg_daily_demand * product.lead_time_days + safety_stock)
        return reorder_point

    def assess_reorder_level(self, sku: str) -> ReorderLevel:
        if sku not in self.products:
            return ReorderLevel.CRITICAL
        product = self.products[sku]
        forecast = self.forecast_demand(sku)
        avg_daily = forecast.predicted_demand / forecast.forecast_period_days if forecast.forecast_period_days > 0 else 1
        days_of_stock = product.current_stock / avg_daily if avg_daily > 0 else float('inf')
        if days_of_stock <= self.config["critical_stockout_threshold_days"]:
            return ReorderLevel.CRITICAL
        elif days_of_stock <= self.config["low_stock_threshold_days"]:
            return ReorderLevel.LOW
        elif product.current_stock >= product.max_stock * 0.9:
            return ReorderLevel.OVERSTOCKED
        elif product.current_stock >= product.reorder_point * 1.5:
            return ReorderLevel.OPTIMAL
        return ReorderLevel.ADEQUATE

    def generate_replenishment_order(self, sku: str, quantity: Optional[int] = None) -> Optional[ReplenishmentOrder]:
        if sku not in self.products:
            return None
        product = self.products[sku]
        reorder_level = self.assess_reorder_level(sku)
        if reorder_level not in [ReorderLevel.CRITICAL, ReorderLevel.LOW]:
            return None
        order_qty = quantity or product.reorder_quantity
        estimated_cost = order_qty * product.unit_cost
        expected_delivery = datetime.now() + timedelta(days=product.lead_time_days)
        priority = "urgent" if reorder_level == ReorderLevel.CRITICAL else "normal"
        order = ReplenishmentOrder(
            order_id=f"PO-{sku}-{datetime.now().strftime('%Y%m%d%H%M')}",
            product_sku=sku,
            quantity=order_qty,
            estimated_cost=estimated_cost,
            expected_delivery=expected_delivery,
            priority=priority,
        )
        product.current_stock += order_qty
        return order

    def analyze_stockout_risk(self, sku: str) -> StockoutRisk:
        if sku not in self.products:
            return StockoutRisk(sku, "unknown", 0, "Product not found", 0)
        product = self.products[sku]
        forecast = self.forecast_demand(sku)
        avg_daily_demand = forecast.predicted_demand / forecast.forecast_period_days if forecast.forecast_period_days > 0 else 1
        days_until_stockout = int(product.current_stock / avg_daily_demand) if avg_daily_demand > 0 else 999
        if days_until_stockout <= 3:
            risk_level = "critical"
            action = "Immediate reorder required - risk of stockout"
        elif days_until_stockout <= 7:
            risk_level = "high"
            action = "Reorder within 24 hours recommended"
        elif days_until_stockout <= 14:
            risk_level = "medium"
            action = "Plan reorder within this week"
        else:
            risk_level = "low"
            action = "Stock levels adequate"
        confidence = forecast.confidence * 0.8
        return StockoutRisk(
            product_sku=sku,
            risk_level=risk_level,
            days_until_stockout=days_until_stockout,
            recommended_action=action,
            confidence_score=confidence,
        )

    def get_inventory_status(self) -> Dict:
        status = {
            "timestamp": datetime.now().isoformat(),
            "total_products": len(self.products),
            "products_at_risk": 0,
            "products_critical": 0,
            "products_optimal": 0,
            "total_stock_value": 0,
            "reorder_recommendations": [],
        }
        for sku, product in self.products.items():
            stock_value = product.current_stock * product.unit_cost
            status["total_stock_value"] += stock_value
            reorder_level = self.assess_reorder_level(sku)
            if reorder_level in [ReorderLevel.CRITICAL, ReorderLevel.LOW]:
                status["products_at_risk"] += 1
            if reorder_level == ReorderLevel.CRITICAL:
                status["products_critical"] += 1
            if reorder_level == ReorderLevel.OPTIMAL:
                status["products_optimal"] += 1
            order = self.generate_replenishment_order(sku)
            if order:
                status["reorder_recommendations"].append(order)
        return status

    def batch_forecast(self, skus: Optional[List[str]] = None) -> List[DemandForecast]:
        target_skus = skus or list(self.products.keys())
        return [self.forecast_demand(sku) for sku in target_skus if sku in self.products]

    def auto_replenishment_scan(self) -> List[ReplenishmentOrder]:
        orders = []
        for sku in self.products:
            order = self.generate_replenishment_order(sku)
            if order:
                orders.append(order)
        return sorted(orders, key=lambda x: (0 if x.priority == "urgent" else 1, x.created_at))
