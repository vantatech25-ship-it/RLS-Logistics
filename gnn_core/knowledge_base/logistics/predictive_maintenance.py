"""Predictive Maintenance Module
IoT sensor-based equipment failure prediction
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math


class EquipmentType(Enum):
    TRUCK = "truck"
    REFRIGERATED_UNIT = "refrigerated_unit"
    CONVEYOR = "conveyor"
    FORKLIFT = "forklift"
    WAREHOUSE_SENSOR = "warehouse_sensor"


class HealthStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


class FailureMode(Enum):
    NONE = "none"
    BEARING_WEAR = "bearing_wear"
    COOLANT_LEAK = "coolant_leak"
    ENGINE_OVERHEAT = "engine_overheat"
    ELECTRICAL_FAULT = "electrical_fault"
    BRAKE_WEAR = "brake_wear"
    TIRE_DEGRADATION = "tire_degradation"
    SENSOR_MALFUNCTION = "sensor_malfunction"


@dataclass
class SensorReading:
    timestamp: datetime
    temperature: float
    vibration: float
    pressure: float
    rpm: float
    voltage: Optional[float] = None
    humidity: Optional[float] = None
    fuel_level: Optional[float] = None


@dataclass
class Equipment:
    equipment_id: str
    name: str
    equipment_type: EquipmentType
    manufacturer: str
    model: str
    installation_date: datetime
    last_maintenance: datetime
    operating_hours: int
    location: str
    sensors: List[str]


@dataclass
class MaintenanceRecord:
    record_id: str
    equipment_id: str
    maintenance_type: str
    description: str
    performed_by: str
    cost: float
    parts_replaced: List[str]
    performed_at: datetime
    next_scheduled: Optional[datetime] = None


@dataclass
class HealthPrediction:
    equipment_id: str
    health_score: float
    status: HealthStatus
    predicted_failure_date: Optional[datetime]
    remaining_useful_life_hours: int
    confidence: float
    failure_probability_30d: float
    failure_probability_90d: float
    recommended_actions: List[str]
    critical_components: List[str]
    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class AnomalyAlert:
    alert_id: str
    equipment_id: str
    sensor_type: str
    anomaly_type: str
    severity: str
    current_value: float
    threshold_value: float
    deviation_percentage: float
    message: str
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False


class PredictiveMaintenance:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.equipment: Dict[str, Equipment] = {}
        self.sensor_history: Dict[str, List[SensorReading]] = {}
        self.maintenance_records: Dict[str, List[MaintenanceRecord]] = {}
        self.alerts: List[AnomalyAlert] = []

    def _default_config(self) -> Dict:
        return {
            "vibration_threshold_normal": 2.0,
            "vibration_threshold_warning": 4.0,
            "temperature_threshold_normal": 85.0,
            "temperature_threshold_warning": 95.0,
            "pressure_threshold_min": 30.0,
            "pressure_threshold_max": 80.0,
            "failure_prediction_window_days": 30,
            "sensor_reading_interval_minutes": 15,
            "anomaly_detection_sensitivity": 0.85,
        }

    def register_equipment(self, equipment: Equipment) -> bool:
        self.equipment[equipment.equipment_id] = equipment
        if equipment.equipment_id not in self.sensor_history:
            self.sensor_history[equipment.equipment_id] = []
        if equipment.equipment_id not in self.maintenance_records:
            self.maintenance_records[equipment.equipment_id] = []
        return True

    def add_sensor_reading(self, equipment_id: str, reading: SensorReading) -> bool:
        if equipment_id not in self.sensor_history:
            self.sensor_history[equipment_id] = []
        self.sensor_history[equipment_id].append(reading)
        if len(self.sensor_history[equipment_id]) > 10000:
            self.sensor_history[equipment_id] = self.sensor_history[equipment_id][-5000:]
        self._check_for_anomalies(equipment_id, reading)
        return True

    def simulate_sensor_reading(self, equipment_id: str) -> SensorReading:
        cfg = self.config
        equipment = self.equipment.get(equipment_id)
        base_vibration = 1.5 if equipment else 1.5
        base_temp = 75.0 if equipment else 75.0
        base_pressure = 50.0 if equipment else 50.0
        health_factor = random.uniform(0.8, 1.2)
        reading = SensorReading(
            timestamp=datetime.now(),
            temperature=base_temp * health_factor + random.uniform(-5, 10),
            vibration=base_vibration * health_factor + random.uniform(-0.5, 1.5),
            pressure=base_pressure + random.uniform(-10, 10),
            rpm=3000 + random.uniform(-500, 500),
            voltage=24.0 + random.uniform(-2, 2),
            humidity=random.uniform(30, 70),
            fuel_level=random.uniform(0.2, 1.0) if equipment and equipment.equipment_type == EquipmentType.TRUCK else None,
        )
        self.add_sensor_reading(equipment_id, reading)
        return reading

    def _calculate_vibration_score(self, readings: List[SensorReading]) -> float:
        if not readings:
            return 100.0
        avg_vibration = sum(r.vibration for r in readings[-10:]) / min(10, len(readings))
        cfg = self.config
        if avg_vibration <= cfg["vibration_threshold_normal"]:
            return 100.0
        elif avg_vibration <= cfg["vibration_threshold_warning"]:
            return 80.0 - (avg_vibration - cfg["vibration_threshold_normal"]) * 10
        else:
            return max(0, 60 - (avg_vibration - cfg["vibration_threshold_warning"]) * 15)

    def _calculate_temperature_score(self, readings: List[SensorReading]) -> float:
        if not readings:
            return 100.0
        avg_temp = sum(r.temperature for r in readings[-10:]) / min(10, len(readings))
        cfg = self.config
        if avg_temp <= cfg["temperature_threshold_normal"]:
            return 100.0
        elif avg_temp <= cfg["temperature_threshold_warning"]:
            return 80.0 - (avg_temp - cfg["temperature_threshold_normal"]) * 5
        else:
            return max(0, 60 - (avg_temp - cfg["temperature_threshold_warning"]) * 10)

    def _calculate_pressure_score(self, readings: List[SensorReading]) -> float:
        if not readings:
            return 100.0
        recent = readings[-10:]
        out_of_range = sum(
            1 for r in recent if r.pressure < self.config["pressure_threshold_min"] or r.pressure > self.config["pressure_threshold_max"]
        )
        deviation_ratio = out_of_range / len(recent)
        return max(0, 100 - deviation_ratio * 50)

    def _identify_failure_mode(self, readings: List[SensorReading]) -> Tuple[FailureMode, float]:
        if len(readings) < 5:
            return FailureMode.NONE, 0.0
        recent = readings[-10:]
        avg_temp = sum(r.temperature for r in recent) / len(recent)
        avg_vibration = sum(r.vibration for r in recent) / len(recent)
        if avg_temp > 100 and avg_vibration > 3.5:
            return FailureMode.ENGINE_OVERHEAT, 0.85
        elif avg_vibration > 4.0:
            return FailureMode.BEARING_WEAR, 0.75
        elif any(r.temperature < 30 for r in recent):
            return FailureMode.COOLANT_LEAK, 0.65
        elif any(abs(r.voltage - 24) > 3 for r in recent if r.voltage):
            return FailureMode.ELECTRICAL_FAULT, 0.70
        return FailureMode.NONE, 0.0

    def predict_health(self, equipment_id: str) -> HealthPrediction:
        if equipment_id not in self.equipment:
            return HealthPrediction(equipment_id, 0, HealthStatus.FAILED, datetime.now(), 0, 0, 1.0, 1.0, ["Equipment not found"], [], datetime.now())
        equipment = self.equipment[equipment_id]
        readings = self.sensor_history.get(equipment_id, [])
        vibration_score = self._calculate_vibration_score(readings)
        temp_score = self._calculate_temperature_score(readings)
        pressure_score = self._calculate_pressure_score(readings)
        overall_score = (vibration_score * 0.35 + temp_score * 0.35 + pressure_score * 0.30)
        if overall_score >= 90:
            status = HealthStatus.EXCELLENT
        elif overall_score >= 75:
            status = HealthStatus.GOOD
        elif overall_score >= 60:
            status = HealthStatus.FAIR
        elif overall_score >= 40:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.CRITICAL
        failure_mode, failure_confidence = self._identify_failure_mode(readings)
        hours_per_day = 8
        if status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
            remaining_hours = int(overall_score * 10)
            failure_30d_prob = max(0.1, 1 - (overall_score / 100))
        else:
            remaining_hours = int(overall_score * 20)
            failure_30d_prob = max(0.01, (100 - overall_score) / 200)
        failure_90d_prob = min(0.99, failure_30d_prob * 2.5)
        predicted_failure = None
        if remaining_hours < 200:
            predicted_failure = datetime.now() + timedelta(hours=remaining_hours / hours_per_day)
        recommended = []
        if status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
            recommended.append("Schedule maintenance within 48 hours")
            if failure_mode != FailureMode.NONE:
                recommended.append(f"Inspect for {failure_mode.value} - confidence: {failure_confidence:.0%}")
        if temp_score < 70:
            recommended.append("Check cooling system and thermal management")
        if vibration_score < 70:
            recommended.append("Inspect bearings and rotating components")
        critical_components = []
        if temp_score < 80:
            critical_components.append("Cooling System")
        if vibration_score < 80:
            critical_components.append("Bearings")
        if pressure_score < 80:
            critical_components.append("Hydraulic System")
        return HealthPrediction(
            equipment_id=equipment_id,
            health_score=overall_score,
            status=status,
            predicted_failure_date=predicted_failure,
            remaining_useful_life_hours=remaining_hours,
            confidence=failure_confidence,
            failure_probability_30d=failure_30d_prob,
            failure_probability_90d=failure_90d_prob,
            recommended_actions=recommended if recommended else ["Continue monitoring"],
            critical_components=critical_components,
        )

    def _check_for_anomalies(self, equipment_id: str, reading: SensorReading):
        cfg = self.config
        alerts = []
        if reading.temperature > cfg["temperature_threshold_warning"]:
            severity = "critical" if reading.temperature > 100 else "warning"
            alerts.append(AnomalyAlert(
                alert_id=f"AL-{equipment_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                equipment_id=equipment_id,
                sensor_type="temperature",
                anomaly_type="high_temperature",
                severity=severity,
                current_value=reading.temperature,
                threshold_value=cfg["temperature_threshold_warning"],
                deviation_percentage=((reading.temperature - cfg["temperature_threshold_warning"]) / cfg["temperature_threshold_warning"]) * 100,
                message=f"Temperature exceeded threshold: {reading.temperature:.1f}°C",
            ))
        if reading.vibration > cfg["vibration_threshold_warning"]:
            severity = "critical" if reading.vibration > 5.0 else "warning"
            alerts.append(AnomalyAlert(
                alert_id=f"AL-{equipment_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                equipment_id=equipment_id,
                sensor_type="vibration",
                anomaly_type="excessive_vibration",
                severity=severity,
                current_value=reading.vibration,
                threshold_value=cfg["vibration_threshold_warning"],
                deviation_percentage=((reading.vibration - cfg["vibration_threshold_warning"]) / cfg["vibration_threshold_warning"]) * 100,
                message=f"Excessive vibration detected: {reading.vibration:.2f}g",
            ))
        if reading.pressure < cfg["pressure_threshold_min"] or reading.pressure > cfg["pressure_threshold_max"]:
            threshold = cfg["pressure_threshold_min"] if reading.pressure < cfg["pressure_threshold_min"] else cfg["pressure_threshold_max"]
            alerts.append(AnomalyAlert(
                alert_id=f"AL-{equipment_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                equipment_id=equipment_id,
                sensor_type="pressure",
                anomaly_type="pressure_out_of_range",
                severity="warning",
                current_value=reading.pressure,
                threshold_value=threshold,
                deviation_percentage=abs((reading.pressure - threshold) / threshold) * 100,
                message=f"Pressure out of range: {reading.pressure:.1f} PSI",
            ))
        self.alerts.extend(alerts)

    def get_active_alerts(self, equipment_id: Optional[str] = None, severity: Optional[str] = None) -> List[AnomalyAlert]:
        filtered = [a for a in self.alerts if not a.acknowledged]
        if equipment_id:
            filtered = [a for a in filtered if a.equipment_id == equipment_id]
        if severity:
            filtered = [a for a in filtered if a.severity == severity]
        return sorted(filtered, key=lambda x: (x.severity == "warning", x.created_at), reverse=True)

    def acknowledge_alert(self, alert_id: str) -> bool:
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_fleet_health_summary(self) -> Dict:
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_equipment": len(self.equipment),
            "health_distribution": {
                "excellent": 0,
                "good": 0,
                "fair": 0,
                "warning": 0,
                "critical": 0,
            },
            "active_alerts": 0,
            "critical_alerts": 0,
            "equipment_at_risk": [],
            "maintenance_due_soon": [],
        }
        for eq_id in self.equipment:
            prediction = self.predict_health(eq_id)
            summary["health_distribution"][prediction.status.value] += 1
            if prediction.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                summary["equipment_at_risk"].append({
                    "equipment_id": eq_id,
                    "health_score": prediction.health_score,
                    "status": prediction.status.value,
                    "recommended_actions": prediction.recommended_actions,
                })
        alerts = self.get_active_alerts()
        summary["active_alerts"] = len(alerts)
        summary["critical_alerts"] = len([a for a in alerts if a.severity == "critical"])
        return summary

    def schedule_maintenance(self, equipment_id: str, maintenance_type: str, description: str, performed_by: str, cost: float, parts_replaced: List[str]) -> MaintenanceRecord:
        record = MaintenanceRecord(
            record_id=f"MR-{equipment_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            equipment_id=equipment_id,
            maintenance_type=maintenance_type,
            description=description,
            performed_by=performed_by,
            cost=cost,
            parts_replaced=parts_replaced,
            performed_at=datetime.now(),
            next_scheduled=datetime.now() + timedelta(days=90),
        )
        self.maintenance_records[equipment_id].append(record)
        if equipment_id in self.equipment:
            self.equipment[equipment_id].last_maintenance = datetime.now()
        return record
