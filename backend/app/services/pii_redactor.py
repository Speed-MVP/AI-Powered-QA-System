"""
PII Redaction Service (up-leveled)
Multi-layer PII detection: regex + entropy + optional ML (Presidio),
with residual scans and configurable strictness per DATA_PRIVACY_AND_LLM_USAGE.md.
"""

import re
import math
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import SpacyNlpEngine
    _PRESIDIO_AVAILABLE = True
except Exception:
    _PRESIDIO_AVAILABLE = False


class PIIRedactor:
    """
    Redacts PII from transcripts using layered detectors:
    - Deterministic regex (fast)
    - Entropy-based detector for secrets/IDs
    - Optional ML NER via Presidio if available in environment
    """

    def __init__(self):
        # Compile regex patterns for common PII
        self.patterns = {
            "name": re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
            "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"),
            "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
            "account_number": re.compile(r"\b(?:account|acct|acc)[\s#:]*(\d{4,})\b", re.IGNORECASE),
            "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "address": re.compile(
                r"\b\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)\b",
                re.IGNORECASE,
            ),
            "order_id": re.compile(r"\b(?:order|ord|ref|reference)[\s#:]*([A-Z0-9]{6,})\b", re.IGNORECASE),
        }

        self.entropy_token_pattern = re.compile(r"[A-Za-z0-9=_\-\+/]{12,}")

        self.presidio_engine = None
        if _PRESIDIO_AVAILABLE:
            try:
                self.presidio_engine = AnalyzerEngine(
                    nlp_engine=SpacyNlpEngine(),
                    supported_languages=["en"],
                )
                logger.info("Presidio AnalyzerEngine initialized for PII detection.")
            except Exception as e:
                # Fail open to keep service operational; log for ops visibility
                logger.warning("Failed to initialize Presidio AnalyzerEngine, falling back to regex/entropy only: %s", e)
                self.presidio_engine = None

    def _default_config(self, overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        base = {
            "strict": False,  # raise on residual PII if True
            "residual_check": True,
            "enable_entropy": True,
            "entropy_threshold": 3.5,
            "min_entropy_length": 12,
            "enable_regex": True,
            "enable_ml": True,
            "ml_confidence": 0.35,
        }
        if overrides:
            base.update(overrides)
        if not self.presidio_engine:
            base["enable_ml"] = False
        return base

    def _calc_entropy(self, text: str) -> float:
        if not text:
            return 0.0
        freq = {}
        for ch in text:
            freq[ch] = freq.get(ch, 0) + 1
        length = len(text)
        return -sum((count / length) * math.log2(count / length) for count in freq.values())

    def _detect_entropy_spans(self, text: str, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not cfg.get("enable_entropy", True):
            return []
        spans = []
        for match in self.entropy_token_pattern.finditer(text):
            token = match.group(0)
            if len(token) < cfg.get("min_entropy_length", 12):
                continue
            ent = self._calc_entropy(token)
            if ent >= cfg.get("entropy_threshold", 3.5):
                spans.append({"start": match.start(), "end": match.end(), "label": "SECRET"})
        return spans

    def _detect_regex_spans(self, text: str, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not cfg.get("enable_regex", True):
            return []
        spans = []
        for label, pattern in self.patterns.items():
            for m in pattern.finditer(text):
                spans.append({"start": m.start(), "end": m.end(), "label": label.upper()})
        return spans

    def _detect_ml_spans(self, text: str, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not cfg.get("enable_ml", False) or not self.presidio_engine:
            return []
        spans = []
        try:
            results = self.presidio_engine.analyze(
                text=text,
                language="en",
                score_threshold=cfg.get("ml_confidence", 0.35),
            )
            for r in results:
                spans.append({"start": r.start, "end": r.end, "label": r.entity_type})
        except Exception as e:
            logger.warning("Presidio analyze failed, continuing without ML: %s", e)
        return spans

    def _merge_spans(self, spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Sort by start then end, merge overlaps preferring longer span
        spans_sorted = sorted(spans, key=lambda s: (s["start"], -(s["end"] - s["start"])))
        merged: List[Dict[str, Any]] = []
        for span in spans_sorted:
            if not merged:
                merged.append(span)
                continue
            last = merged[-1]
            if span["start"] <= last["end"]:
                # overlap; keep the longer span
                if (span["end"] - span["start"]) > (last["end"] - last["start"]):
                    merged[-1] = span
            else:
                merged.append(span)
        return merged

    def _apply_redactions(
        self,
        text: str,
        spans: List[Dict[str, Any]],
        token_map: Dict[str, str],
    ) -> Tuple[str, Dict[str, str]]:
        if not spans:
            return text, token_map
        spans = sorted(spans, key=lambda s: s["start"])
        redacted_parts = []
        cursor = 0
        for span in spans:
            redacted_parts.append(text[cursor:span["start"]])
            value = text[span["start"]:span["end"]]
            key = f"{span['label']}::{value}".lower()
            if key not in token_map:
                token_map[key] = f"{{{{{span['label']}_{len(token_map)+1}}}}}"
            redacted_parts.append(token_map[key])
            cursor = span["end"]
        redacted_parts.append(text[cursor:])
        return "".join(redacted_parts), token_map

    def _detect_all(self, text: str, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
        spans = []
        spans.extend(self._detect_regex_spans(text, cfg))
        spans.extend(self._detect_entropy_spans(text, cfg))
        spans.extend(self._detect_ml_spans(text, cfg))
        return self._merge_spans(spans)

    def _build_report(self, original: str, redacted: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
        residual_hits = []
        if cfg.get("residual_check", True):
            residual_hits = self._detect_all(redacted, cfg)
        return {
            "strict": cfg.get("strict", False),
            "residual_hits": residual_hits,
            "redacted": redacted != original,
            "detected_count": len(self._detect_all(original, cfg)),
        }

    def redact_text(
        self,
        text: str,
        config: Optional[Dict[str, Any]] = None,
        return_report: bool = False,
        token_map: Optional[Dict[str, str]] = None,
    ):
        """
        Redact PII from text string. Returns redacted text (and report if requested).
        Config keys:
            - strict: raise if residual PII remains after redaction
            - residual_check: run post-redaction scan
            - enable_regex, enable_ml, enable_entropy
            - entropy_threshold, min_entropy_length, ml_confidence
        """
        if text is None:
            return (text, {"residual_hits": []}) if return_report else text

        cfg = self._default_config(config)
        spans = self._detect_all(text, cfg)
        token_map = token_map or {}
        redacted_text, token_map = self._apply_redactions(text, spans, token_map)
        report = self._build_report(text, redacted_text, cfg)

        if cfg.get("strict", False) and report["residual_hits"]:
            raise ValueError("Residual PII detected after redaction; aborting to protect data.")

        if return_report:
            return redacted_text, report, token_map
        return redacted_text

    def redact_segments(
        self,
        segments: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
        return_report: bool = False,
    ):
        """
        Redact PII from transcript segments.
        Preserves speaker attribution/timestamps and applies consistent placeholders.
        """
        cfg = self._default_config(config)
        redacted_segments: List[Dict[str, Any]] = []
        token_map: Dict[str, str] = {}
        aggregate_report = {"residual_hits": [], "strict": cfg.get("strict", False)}

        for segment in segments or []:
            redacted_segment = segment.copy()
            text = segment.get("text", "")
            redacted_text, report, token_map = self.redact_text(
                text,
                config=cfg,
                return_report=True,
                token_map=token_map,
            )
            redacted_segment["text"] = redacted_text
            redacted_segments.append(redacted_segment)
            aggregate_report["residual_hits"].extend(report.get("residual_hits", []))

        # Deduplicate residual hits for reporting clarity
        if aggregate_report["residual_hits"]:
            unique = []
            seen = set()
            for hit in aggregate_report["residual_hits"]:
                sig = (hit["start"], hit["end"], hit["label"])
                if sig not in seen:
                    seen.add(sig)
                    unique.append(hit)
            aggregate_report["residual_hits"] = unique

        if cfg.get("strict", False) and aggregate_report["residual_hits"]:
            raise ValueError("Residual PII detected in segments after redaction; aborting to protect data.")

        if return_report:
            return redacted_segments, aggregate_report
        return redacted_segments

    def redact_transcript(
        self,
        transcript_text: str,
        segments: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Redact PII from both transcript text and segments.
        Returns (redacted_text, redacted_segments, report)
        """
        cfg = self._default_config(config)
        redacted_text, text_report, token_map = self.redact_text(
            transcript_text,
            config=cfg,
            return_report=True,
        )
        redacted_segments, seg_report = self.redact_segments(
            segments,
            config=cfg,
            return_report=True,
        )

        combined_report = {
            "strict": cfg.get("strict", False),
            "text_residual_hits": text_report.get("residual_hits", []),
            "segment_residual_hits": seg_report.get("residual_hits", []),
        }

        if cfg.get("strict", False) and (
            combined_report["text_residual_hits"] or combined_report["segment_residual_hits"]
        ):
            raise ValueError("Residual PII detected after redacting transcript and segments.")

        return redacted_text, redacted_segments, combined_report

