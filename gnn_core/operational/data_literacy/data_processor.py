"""Data Literacy and Processing Module
Data cleaning, preparation, and analysis for model accuracy
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import re


class DataType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"


class DataQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class DataField:
    field_name: str
    data_type: DataType
    nullable: bool
    unique: bool
    sample_values: List[Any] = field(default_factory=list)
    null_count: int = 0
    total_count: int = 0

    @property
    def null_percentage(self) -> float:
        return (self.null_count / self.total_count * 100) if self.total_count > 0 else 0


@dataclass
class DatasetProfile:
    dataset_id: str
    name: str
    row_count: int
    column_count: int
    fields: List[DataField]
    quality_score: float
    quality_issues: List[str]
    recommendations: List[str]
    created_at: datetime


@dataclass
class Transformation:
    transformation_id: str
    name: str
    input_field: str
    output_field: str
    transformation_type: str
    parameters: Dict
    applied_at: Optional[datetime] = None


class DataProcessor:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.datasets: Dict[str, List[Dict]] = {}
        self.profiles: Dict[str, DatasetProfile] = {}
        self.transformations: List[Transformation] = []

    def _default_config(self) -> Dict:
        return {
            "max_null_percentage": 20.0,
            "min_unique_ratio": 0.01,
            "sample_size": 1000,
            "auto_clean_enabled": True,
        }

    def load_dataset(self, name: str, data: List[Dict]) -> str:
        dataset_id = f"DS-{uuid.uuid4().hex[:8].upper()}"
        self.datasets[dataset_id] = data
        self.profiles[dataset_id] = self._profile_dataset(dataset_id, name, data)
        return dataset_id

    def _detect_data_type(self, value: Any) -> DataType:
        if value is None:
            return DataType.STRING
        if isinstance(value, bool):
            return DataType.BOOLEAN
        if isinstance(value, int):
            return DataType.INTEGER
        if isinstance(value, float):
            return DataType.FLOAT
        if isinstance(value, datetime):
            return DataType.DATETIME
        if isinstance(value, (dict, list)):
            return DataType.JSON
        return DataType.STRING

    def _profile_dataset(self, dataset_id: str, name: str, data: List[Dict]) -> DatasetProfile:
        if not data:
            return DatasetProfile(dataset_id, name, 0, 0, [], 0, ["Empty dataset"], [], datetime.now())
        row_count = len(data)
        column_names = set()
        for row in data:
            column_names.update(row.keys())
        column_count = len(column_names)
        fields = []
        quality_issues = []
        recommendations = []
        for col in column_names:
            values = [row.get(col) for row in data]
            non_null = [v for v in values if v is not None]
            unique_values = set(non_null)
            field_profile = DataField(
                field_name=col,
                data_type=self._detect_data_type(non_null[0] if non_null else None),
                nullable=any(v is None for v in values),
                unique=len(unique_values) > row_count * 0.9,
                sample_values=non_null[:10],
                null_count=len(values) - len(non_null),
                total_count=len(values),
            )
            fields.append(field_profile)
            if field_profile.null_percentage > self.config["max_null_percentage"]:
                quality_issues.append(f"Field '{col}' has {field_profile.null_percentage:.1f}% null values")
                recommendations.append(f"Consider imputing or removing '{col}' due to high null rate")
            if field_profile.unique and field_profile.null_percentage < 1:
                quality_issues.append(f"Field '{col}' has {len(unique_values)} unique values (potential identifier)")
        quality_score = max(0, 100 - len(quality_issues) * 10 - sum(f.null_percentage for f in fields) / 10)
        return DatasetProfile(
            dataset_id=dataset_id,
            name=name,
            row_count=row_count,
            column_count=column_count,
            fields=fields,
            quality_score=quality_score,
            quality_issues=quality_issues,
            recommendations=recommendations,
            created_at=datetime.now(),
        )

    def clean_data(self, dataset_id: str, strategy: str = "auto") -> List[Dict]:
        if dataset_id not in self.datasets:
            return []
        data = self.datasets[dataset_id]
        profile = self.profiles.get(dataset_id)
        cleaned = []
        for row in data:
            new_row = {}
            for key, value in row.items():
                if value is None:
                    new_row[key] = None
                elif isinstance(value, str):
                    new_row[key] = value.strip()
                    if new_row[key] == "":
                        new_row[key] = None
                else:
                    new_row[key] = value
            cleaned.append(new_row)
        if profile and strategy == "auto":
            for field_profile in profile.fields:
                if field_profile.null_percentage > self.config["max_null_percentage"]:
                    col = field_profile.field_name
                    if field_profile.data_type in [DataType.INTEGER, DataType.FLOAT]:
                        non_null = [r.get(col) for r in cleaned if r.get(col) is not None]
                        if non_null:
                            fill_value = sum(non_null) / len(non_null)
                            for row in cleaned:
                                if row.get(col) is None:
                                    row[col] = fill_value
        return cleaned

    def transform_field(self, dataset_id: str, input_field: str, output_field: str, transformation_type: str, parameters: Optional[Dict] = None) -> bool:
        if dataset_id not in self.datasets:
            return False
        params = parameters or {}
        transformation = Transformation(
            transformation_id=f"TR-{uuid.uuid4().hex[:8].upper()}",
            name=f"{transformation_type} on {input_field}",
            input_field=input_field,
            output_field=output_field,
            transformation_type=transformation_type,
            parameters=params,
            applied_at=datetime.now(),
        )
        self.transformations.append(transformation)
        for row in self.datasets[dataset_id]:
            value = row.get(input_field)
            if transformation_type == "uppercase":
                row[output_field] = str(value).upper() if value else None
            elif transformation_type == "lowercase":
                row[output_field] = str(value).lower() if value else None
            elif transformation_type == "remove_whitespace":
                row[output_field] = re.sub(r'\s+', ' ', str(value)).strip() if value else None
            elif transformation_type == "extract_numbers":
                numbers = re.findall(r'\d+\.?\d*', str(value)) if value else []
                row[output_field] = float(numbers[0]) if numbers else None
            elif transformation_type == "parse_date":
                try:
                    row[output_field] = datetime.strptime(str(value), params.get("format", "%Y-%m-%d")).isoformat() if value else None
                except:
                    row[output_field] = None
            elif transformation_type == "categorize":
                bins = params.get("bins", [])
                for i, threshold in enumerate(bins):
                    if isinstance(value, (int, float)) and value < threshold:
                        row[output_field] = params.get("labels", ["A", "B", "C"])[i] if i < len(params.get("labels", ["A", "B", "C"])) else "Unknown"
                        break
                else:
                    row[output_field] = params.get("labels", ["A", "B", "C"])[-1] if params.get("labels") else "Unknown"
            elif transformation_type == "one_hot":
                categories = params.get("categories", [])
                for cat in categories:
                    row[f"{output_field}_{cat}"] = 1 if value == cat else 0
        return True

    def aggregate_data(self, dataset_id: str, group_by: str, aggregations: Dict[str, str]) -> List[Dict]:
        if dataset_id not in self.datasets:
            return []
        data = self.datasets[dataset_id]
        groups: Dict[Any, List[Dict]] = {}
        for row in data:
            key = row.get(group_by)
            if key not in groups:
                groups[key] = []
            groups[key].append(row)
        results = []
        for key, group_rows in groups.items():
            result = {group_by: key}
            for field_name, agg_func in aggregations.items():
                values = [r.get(field_name) for r in group_rows if r.get(field_name) is not None]
                if agg_func == "sum":
                    result[f"{field_name}_sum"] = sum(values)
                elif agg_func == "avg" or agg_func == "mean":
                    result[f"{field_name}_avg"] = sum(values) / len(values) if values else None
                elif agg_func == "count":
                    result[f"{field_name}_count"] = len(values)
                elif agg_func == "min":
                    result[f"{field_name}_min"] = min(values) if values else None
                elif agg_func == "max":
                    result[f"{field_name}_max"] = max(values) if values else None
            results.append(result)
        return results

    def join_datasets(self, dataset_id_1: str, dataset_id_2: str, join_key: str, join_type: str = "inner") -> List[Dict]:
        if dataset_id_1 not in self.datasets or dataset_id_2 not in self.datasets:
            return []
        data1 = self.datasets[dataset_id_1]
        data2 = self.datasets[dataset_id_2]
        joined = []
        if join_type == "inner":
            for row1 in data1:
                for row2 in data2:
                    if row1.get(join_key) == row2.get(join_key):
                        merged = {**row1, **{f"{k}_2": v for k, v in row2.items() if k != join_key}}
                        joined.append(merged)
        elif join_type == "left":
            for row1 in data1:
                matched = False
                for row2 in data2:
                    if row1.get(join_key) == row2.get(join_key):
                        merged = {**row1, **{f"{k}_2": v for k, v in row2.items() if k != join_key}}
                        joined.append(merged)
                        matched = True
                if not matched:
                    joined.append(row1)
        return joined

    def get_summary_statistics(self, dataset_id: str, field_name: str) -> Dict:
        if dataset_id not in self.datasets:
            return {}
        data = self.datasets[dataset_id]
        values = [row.get(field_name) for row in data if row.get(field_name) is not None and isinstance(row.get(field_name), (int, float))]
        if not values:
            return {"count": 0, "error": "No numeric values found"}
        import statistics
        return {
            "field": field_name,
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "q1": statistics.quantiles(values, n=4)[0] if len(values) >= 4 else None,
            "q3": statistics.quantiles(values, n=4)[2] if len(values) >= 4 else None,
        }

    def export_to_json(self, dataset_id: str) -> str:
        if dataset_id not in self.datasets:
            return "{}"
        return json.dumps(self.datasets[dataset_id], indent=2, default=str)

    def get_data_quality_report(self, dataset_id: str) -> Dict:
        if dataset_id not in self.profiles:
            return {"error": "Dataset not found"}
        profile = self.profiles[dataset_id]
        return {
            "dataset_id": dataset_id,
            "name": profile.name,
            "quality_score": f"{profile.quality_score:.1f}%",
            "quality_grade": DataQuality.EXCELLENT.value if profile.quality_score >= 90 else DataQuality.GOOD.value if profile.quality_score >= 70 else DataQuality.FAIR.value if profile.quality_score >= 50 else DataQuality.POOR.value,
            "row_count": profile.row_count,
            "column_count": profile.column_count,
            "issues": profile.quality_issues,
            "recommendations": profile.recommendations,
            "field_summary": [
                {
                    "field": f.field_name,
                    "type": f.data_type.value,
                    "null_pct": f"{f.null_percentage:.1f}%",
                    "unique_values": len(set(f.sample_values)),
                }
                for f in profile.fields
            ],
        }
