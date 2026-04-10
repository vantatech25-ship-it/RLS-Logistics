"""Document Processing Module (OCR & NLP)
Automated extraction and validation from Bills of Lading, Invoices, Customs Declarations
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class DocumentType(Enum):
    BILL_OF_LADING = "bill_of_lading"
    INVOICE = "invoice"
    CUSTOMS_DECLARATION = "customs_declaration"
    PACKING_LIST = "packing_list"
    DELIVERY_NOTE = "delivery_note"
    UNKNOWN = "unknown"


class ValidationStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    PARTIAL = "partial"
    PENDING_REVIEW = "pending_review"


@dataclass
class ExtractedField:
    field_name: str
    value: str
    confidence: float
    location: Optional[Dict] = None


@dataclass
class DocumentMetadata:
    document_type: DocumentType
    document_number: str
    issue_date: Optional[datetime]
    parties: Dict[str, str]
    total_value: Optional[float]
    currency: str
    page_count: int
    extracted_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessedDocument:
    document_id: str
    metadata: DocumentMetadata
    extracted_fields: List[ExtractedField]
    validation_status: ValidationStatus
    validation_errors: List[str]
    raw_text: str
    confidence_score: float
    requires_human_review: bool


class DocumentProcessor:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.document_templates = self._load_templates()

    def _default_config(self) -> Dict:
        return {
            "min_confidence_threshold": 0.75,
            "require_human_review_below": 0.60,
            "supported_languages": ["en", "es", "fr", "de", "zh"],
            "auto_correction_enabled": True,
            "field_validation_rules": self._default_validation_rules(),
        }

    def _default_validation_rules(self) -> Dict:
        return {
            "invoice_number": {"pattern": r"^(INV|INVOICE)?[\s-]?\d{6,12}$", "required": True},
            "date": {"pattern": r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", "required": True},
            "total_amount": {"pattern": r"[\$€£]?\s?[\d,]+\.?\d{0,2}", "required": True},
            "tax_id": {"pattern": r"[\d]{8,15}", "required": False},
        }

    def _load_templates(self) -> Dict:
        return {
            DocumentType.BILL_OF_LADING: {
                "required_fields": ["shipper", "consignee", "vessel", "port_of_loading", "port_of_discharge", "container_numbers", "description"],
                "optional_fields": ["freight_charges", "insurance", "notify_party"],
                "patterns": {
                    "container": r"[A-Z]{4}\d{7}",
                    "bill_number": r"[A-Z]{3}\d{10}",
                },
            },
            DocumentType.INVOICE: {
                "required_fields": ["invoice_number", "date", "seller", "buyer", "line_items", "total_amount", "currency"],
                "optional_fields": ["tax_id", "payment_terms", "due_date", "discount"],
                "patterns": {
                    "invoice": r"INV[\s-]?\d{6,}",
                    "amount": r"(TOTAL|AMOUNT DUE)[\s:]*[$€£]?\s?[\d,]+\.?\d{0,2}",
                },
            },
            DocumentType.CUSTOMS_DECLARATION: {
                "required_fields": ["declaration_number", "importer", "country_of_origin", "hs_codes", "values", "port_of_entry"],
                "optional_fields": ["duty_rate", "duty_amount", "broker", "bond_number"],
                "patterns": {
                    "hs_code": r"\d{4}\.\d{2}(?:\.\d{2})?",
                    "declaration": r"CD\d{10,}",
                },
            },
        }

    def detect_document_type(self, text: str) -> Tuple[DocumentType, float]:
        text_lower = text.lower()
        type_scores = {
            DocumentType.BILL_OF_LADING: 0,
            DocumentType.INVOICE: 0,
            DocumentType.CUSTOMS_DECLARATION: 0,
            DocumentType.PACKING_LIST: 0,
            DocumentType.DELIVERY_NOTE: 0,
        }
        bill_of_lading_keywords = ["bill of lading", "shipper", "consignee", "vessel", "port of loading", "container", "shipment"]
        invoice_keywords = ["invoice", "billing", "payment terms", "amount due", "line items", "seller", "buyer"]
        customs_keywords = ["customs", "declaration", "hs code", "tariff", "duty", "import", "country of origin"]
        packing_keywords = ["packing list", "packages", "gross weight", "net weight", "dimensions"]
        delivery_keywords = ["delivery note", "delivered", "received by", "signed"]
        for kw in bill_of_lading_keywords:
            if kw in text_lower:
                type_scores[DocumentType.BILL_OF_LADING] += 1
        for kw in invoice_keywords:
            if kw in text_lower:
                type_scores[DocumentType.INVOICE] += 1
        for kw in customs_keywords:
            if kw in text_lower:
                type_scores[DocumentType.CUSTOMS_DECLARATION] += 1
        for kw in packing_keywords:
            if kw in text_lower:
                type_scores[DocumentType.PACKING_LIST] += 1
        for kw in delivery_keywords:
            if kw in text_lower:
                type_scores[DocumentType.DELIVERY_NOTE] += 1
        max_score = max(type_scores.values()) if type_scores else 0
        detected_type = max(type_scores, key=type_scores.get)
        confidence = max_score / max(len(bill_of_lading_keywords), 1) if max_score > 0 else 0.3
        return detected_type, confidence

    def extract_invoice_data(self, text: str) -> Dict:
        extracted = {"invoice_number": None, "date": None, "seller": None, "buyer": None, "line_items": [], "total_amount": None, "currency": "USD", "tax_id": None}
        invoice_match = re.search(r"(?:INVOICE|INV)[\s#:-]?(\d{6,12})", text, re.IGNORECASE)
        if invoice_match:
            extracted["invoice_number"] = invoice_match.group(1)
            extracted["invoice_number"] = ExtractedField("invoice_number", invoice_match.group(1), 0.95)
        date_match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text)
        if date_match:
            extracted["date"] = date_match.group(1)
        amount_pattern = r"(?:TOTAL|AMOUNT\s*DUE|GRAND\s*TOTAL)[\s:]*[$€£]?\s*([\d,]+\.?\d{0,2})"
        amount_match = re.search(amount_pattern, text, re.IGNORECASE)
        if amount_match:
            extracted["total_amount"] = float(amount_match.group(1).replace(",", ""))
        seller_match = re.search(r"(?:FROM|SELLER|VENDOR)[\s:]+([^\n]+)", text, re.IGNORECASE)
        if seller_match:
            extracted["seller"] = seller_match.group(1).strip()
        buyer_match = re.search(r"(?:TO|BUYER|CUSTOMER|BILL\s*TO)[\s:]+([^\n]+)", text, re.IGNORECASE)
        if buyer_match:
            extracted["buyer"] = buyer_match.group(1).strip()
        return extracted

    def extract_bill_of_lading_data(self, text: str) -> Dict:
        extracted = {"bill_number": None, "shipper": None, "consignee": None, "vessel": None, "port_of_loading": None, "port_of_discharge": None, "container_numbers": [], "description": None}
        bol_pattern = r"([A-Z]{3}\d{10})"
        bol_match = re.search(bol_pattern, text)
        if bol_match:
            extracted["bill_number"] = bol_match.group(1)
        container_pattern = r"[A-Z]{4}\d{7}"
        containers = re.findall(container_pattern, text)
        extracted["container_numbers"] = containers
        shipper_match = re.search(r"(?:SHIPPER|FROM)[\s:]+([^\n]+)", text, re.IGNORECASE)
        if shipper_match:
            extracted["shipper"] = shipper_match.group(1).strip()
        consignee_match = re.search(r"(?:CONSIGNEE|TO)[\s:]+([^\n]+)", text, re.IGNORECASE)
        if consignee_match:
            extracted["consignee"] = consignee_match.group(1).strip()
        vessel_match = re.search(r"(?:VESSEL|VESSEL\s*NAME)[\s:]+([^\n]+)", text, re.IGNORECASE)
        if vessel_match:
            extracted["vessel"] = vessel_match.group(1).strip()
        return extracted

    def extract_customs_data(self, text: str) -> Dict:
        extracted = {"declaration_number": None, "importer": None, "country_of_origin": None, "hs_codes": [], "values": {}, "port_of_entry": None}
        decl_pattern = r"(?:DECLARATION|CD)[\s#:-]?(\d{10,})"
        decl_match = re.search(decl_pattern, text, re.IGNORECASE)
        if decl_match:
            extracted["declaration_number"] = decl_match.group(1)
        hs_pattern = r"\b(\d{4}\.\d{2}(?:\.\d{2})?)\b"
        hs_codes = re.findall(hs_pattern, text)
        extracted["hs_codes"] = hs_codes
        country_match = re.search(r"(?:COUNTRY\s*OF\s*ORIGIN|ORIGIN)[\s:]+([^\n]+)", text, re.IGNORECASE)
        if country_match:
            extracted["country_of_origin"] = country_match.group(1).strip()
        return extracted

    def extract_fields(self, text: str, document_type: DocumentType) -> Tuple[List[ExtractedField], Dict]:
        if document_type == DocumentType.INVOICE:
            data = self.extract_invoice_data(text)
        elif document_type == DocumentType.BILL_OF_LADING:
            data = self.extract_bill_of_lading_data(text)
        elif document_type == DocumentType.CUSTOMS_DECLARATION:
            data = self.extract_customs_data(text)
        else:
            data = {}
        fields = []
        for key, value in data.items():
            if value is not None:
                confidence = 0.80 if isinstance(value, (str, float, int)) else 0.75
                fields.append(ExtractedField(key, str(value), confidence))
        return fields, data

    def validate_document(self, document_type: DocumentType, extracted_data: Dict) -> Tuple[ValidationStatus, List[str]]:
        errors = []
        template = self.document_templates.get(document_type)
        if not template:
            return ValidationStatus.PENDING_REVIEW, ["Unknown document type - requires manual review"]
        required = template.get("required_fields", [])
        for field in required:
            if field not in extracted_data or not extracted_data[field]:
                errors.append(f"Missing required field: {field}")
        missing_count = len(errors)
        total_fields = len(required)
        if missing_count == 0:
            status = ValidationStatus.VALID
        elif missing_count <= total_fields * 0.3:
            status = ValidationStatus.PARTIAL
        else:
            status = ValidationStatus.INVALID
        return status, errors

    def process_document(self, text: str, document_id: Optional[str] = None) -> ProcessedDocument:
        doc_id = document_id or f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        detected_type, type_confidence = self.detect_document_type(text)
        extracted_fields, raw_data = self.extract_fields(text, detected_type)
        validation_status, validation_errors = self.validate_document(detected_type, raw_data)
        confidence_score = sum(f.confidence for f in extracted_fields) / len(extracted_fields) if extracted_fields else 0.5
        overall_confidence = (confidence_score * 0.6 + type_confidence * 0.4)
        requires_review = overall_confidence < self.config["require_human_review_below"] or validation_status == ValidationStatus.INVALID
        if validation_status == ValidationStatus.PARTIAL:
            requires_review = True
        metadata = DocumentMetadata(
            document_type=detected_type,
            document_number=raw_data.get("invoice_number") or raw_data.get("bill_number") or raw_data.get("declaration_number") or doc_id,
            issue_date=None,
            parties={"seller": raw_data.get("seller"), "buyer": raw_data.get("buyer"), "shipper": raw_data.get("shipper"), "consignee": raw_data.get("consignee")},
            total_value=raw_data.get("total_amount"),
            currency=raw_data.get("currency", "USD"),
            page_count=1,
        )
        return ProcessedDocument(
            document_id=doc_id,
            metadata=metadata,
            extracted_fields=extracted_fields,
            validation_status=validation_status,
            validation_errors=validation_errors,
            raw_text=text[:5000],
            confidence_score=overall_confidence,
            requires_human_review=requires_review,
        )

    def compare_documents(self, doc1_id: str, doc2_id: str, known_docs: Dict[str, ProcessedDocument]) -> Dict:
        if doc1_id not in known_docs or doc2_id not in known_docs:
            return {"error": "One or both documents not found"}
        d1, d2 = known_docs[doc1_id], known_docs[doc2_id]
        comparison = {
            "document_1": doc1_id,
            "document_2": doc2_id,
            "same_type": d1.metadata.document_type == d2.metadata.document_type,
            "type_match_confidence": 1.0 if d1.metadata.document_type == d2.metadata.document_type else 0.0,
            "value_difference": None,
            "matching_fields": [],
            "differing_fields": [],
        }
        if d1.metadata.total_value and d2.metadata.total_value:
            comparison["value_difference"] = abs(d1.metadata.total_value - d2.metadata.total_value)
        field_names_1 = {f.field_name for f in d1.extracted_fields}
        field_names_2 = {f.field_name for f in d2.extracted_fields}
        comparison["matching_fields"] = list(field_names_1 & field_names_2)
        comparison["differing_fields"] = list(field_names_1 ^ field_names_2)
        return comparison
