"""
Transcript Normalization Pipeline
MVP Evaluation Improvements - Phase 2
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class TranscriptNormalizer:
    """
    Preprocessing pipeline to normalize raw transcripts before LLM evaluation.
    Cleans text, removes noise, fixes punctuation, and optimizes for long conversations.
    """

    def __init__(self):
        # Configurable normalization settings
        self.max_call_duration = 1200  # 20 minutes in seconds
        self.keep_segments = 60  # Keep first and last 60 seconds
        self.rule_event_buffer = 30  # Keep 30 seconds around rule-triggered events

        # Fillers and noise patterns to remove
        self.filler_patterns = [
            r'\b(uh|um|uhh|umm|you know)\b',
            r'\b(like|so|well|okay|alright)\b',
            r'\b(hmm|huh|oh|ah)\b'
        ]

        # Noise patterns to normalize
        self.noise_patterns = [
            r'\[noise\]',
            r'\[inaudible\]',
            r'\[unclear\]',
            r'\[crosstalk\]',
            r'\[background noise\]'
        ]

        # Punctuation and formatting improvements
        self.punctuation_rules = [
            (r'(\w+)\s*\?', r'\1?'),  # Fix spacing before question marks
            (r'(\w+)\s*\!', r'\1!'),  # Fix spacing before exclamation marks
            (r'(\w+)\s*\.', r'\1.'),  # Fix spacing before periods
            (r'(\w+)\s*,', r'\1,'),   # Fix spacing before commas
        ]

    def normalize_transcript(
        self,
        raw_transcript: str,
        diarized_segments: Optional[List[Dict[str, Any]]] = None,
        rule_results: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Main normalization pipeline.

        Args:
            raw_transcript: Raw transcript text
            diarized_segments: List of diarized segments with speaker, text, timestamps
            rule_results: Optional rule engine results to preserve important segments

        Returns:
            Tuple of (normalized_text, processed_segments, metadata)
        """
        if diarized_segments is None:
            diarized_segments = [{
                "speaker": "agent",
                "text": raw_transcript,
                "start": 0.0,
                "end": float(len(raw_transcript.split())) or 0.0,
                "confidence": 1.0
            }]

        logger.info(f"Starting transcript normalization - segments: {len(diarized_segments)}")

        # Step 1: Clean individual segments
        cleaned_segments = self._clean_segments(diarized_segments)

        # Step 2: Merge consecutive segments by same speaker
        merged_segments = self._merge_consecutive_speaker_segments(cleaned_segments)

        # Step 3: Handle long calls - trim if necessary
        if self._should_trim_call(merged_segments):
            trimmed_segments = self._trim_long_call(merged_segments, rule_results)
            trim_metadata = {"trimmed": True, "original_segments": len(merged_segments)}
        else:
            trimmed_segments = merged_segments
            trim_metadata = {"trimmed": False}

        # Step 4: Reconstruct normalized transcript text
        normalized_text = self._reconstruct_transcript_text(trimmed_segments)

        # Step 5: Compute quality metrics
        quality_metrics = self._compute_quality_metrics(raw_transcript, normalized_text, trimmed_segments)

        metadata = {
            **trim_metadata,
            "quality_metrics": quality_metrics,
            "processing_steps": [
                "cleaned_filler_words",
                "normalized_noise",
                "merged_consecutive_segments",
                "trimmed_long_calls",
                "fixed_punctuation"
            ],
            "normalized_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Transcript normalization complete - original: {len(raw_transcript)} chars, normalized: {len(normalized_text)} chars")

        return normalized_text, trimmed_segments, metadata

    def _clean_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Step 1: Clean individual segments - remove fillers, normalize noise."""
        cleaned = []

        for segment in segments:
            cleaned_segment = segment.copy()
            text = segment.get("text", "")

            # Remove filler words
            for pattern in self.filler_patterns:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)

            # Normalize noise patterns
            for pattern in self.noise_patterns:
                text = re.sub(pattern, '{noise}', text, flags=re.IGNORECASE)

            # Fix punctuation spacing
            for pattern, replacement in self.punctuation_rules:
                text = re.sub(pattern, replacement, text)

            # Clean up extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()

            # Skip empty segments after cleaning
            if text:
                cleaned_segment["text"] = text
                cleaned_segment["original_text"] = segment.get("text", "")  # Keep original for reference
                cleaned.append(cleaned_segment)

        return cleaned

    def _merge_consecutive_speaker_segments(self, segments: List[Dict[str, Any]], gap_threshold: float = 1.5) -> List[Dict[str, Any]]:
        """Step 2: Merge consecutive segments by the same speaker within time gap."""
        if not segments:
            return segments

        merged = []
        current_segment = segments[0].copy()

        for next_segment in segments[1:]:
            # Check if same speaker and within gap threshold
            if (current_segment.get("speaker") == next_segment.get("speaker") and
                next_segment.get("start", 0) - current_segment.get("end", 0) <= gap_threshold):

                # Merge segments
                current_segment["text"] += " " + next_segment.get("text", "")
                current_segment["end"] = next_segment.get("end", current_segment.get("end", 0))
                current_segment["confidence"] = min(
                    current_segment.get("confidence", 1.0),
                    next_segment.get("confidence", 1.0)
                )  # Use lowest confidence
            else:
                # Add current segment and start new one
                merged.append(current_segment)
                current_segment = next_segment.copy()

        # Add the last segment
        merged.append(current_segment)

        logger.debug(f"Merged segments: {len(segments)} -> {len(merged)}")
        return merged

    def _should_trim_call(self, segments: List[Dict[str, Any]]) -> bool:
        """Check if call is too long and should be trimmed."""
        if not segments:
            return False

        total_duration = segments[-1].get("end", 0) - segments[0].get("start", 0)
        return total_duration > self.max_call_duration

    def _trim_long_call(self, segments: List[Dict[str, Any]], rule_results: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Step 3: Trim long calls while preserving important segments."""
        if not segments:
            return segments

        # Identify key segments to preserve
        key_time_ranges = []

        # Always keep beginning and end
        total_duration = segments[-1].get("end", 0) - segments[0].get("start", 0)
        key_time_ranges.append((0, self.keep_segments))  # First 60 seconds
        key_time_ranges.append((total_duration - self.keep_segments, total_duration))  # Last 60 seconds

        # Keep segments around rule-triggered events
        if rule_results:
            for rule_name, rule_data in rule_results.items():
                if rule_data.get("hit") and rule_data.get("evidence"):
                    for evidence in rule_data["evidence"]:
                        if isinstance(evidence, dict) and "start" in evidence:
                            event_time = evidence["start"]
                            start_time = max(0, event_time - self.rule_event_buffer)
                            end_time = event_time + self.rule_event_buffer
                            key_time_ranges.append((start_time, end_time))

        # Merge overlapping ranges
        merged_ranges = self._merge_time_ranges(key_time_ranges)

        # Filter segments to keep only those in key ranges
        trimmed_segments = []
        for segment in segments:
            segment_start = segment.get("start", 0)
            segment_end = segment.get("end", 0)

            # Check if segment overlaps with any key range
            keep_segment = False
            for range_start, range_end in merged_ranges:
                if segment_start < range_end and segment_end > range_start:
                    keep_segment = True
                    break

            if keep_segment:
                trimmed_segments.append(segment)

        logger.info(f"Trimmed long call: {len(segments)} -> {len(trimmed_segments)} segments")
        return trimmed_segments

    def _merge_time_ranges(self, ranges: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Merge overlapping time ranges."""
        if not ranges:
            return []

        # Sort by start time
        sorted_ranges = sorted(ranges, key=lambda x: x[0])
        merged = [sorted_ranges[0]]

        for start, end in sorted_ranges[1:]:
            last_start, last_end = merged[-1]

            if start <= last_end:
                # Overlapping, merge
                merged[-1] = (last_start, max(last_end, end))
            else:
                # No overlap, add new range
                merged.append((start, end))

        return merged

    def _reconstruct_transcript_text(self, segments: List[Dict[str, Any]]) -> str:
        """Step 4: Reconstruct normalized transcript text from processed segments."""
        if not segments:
            return ""

        transcript_parts = []

        for i, segment in enumerate(segments):
            speaker = segment.get("speaker", "Unknown")
            text = segment.get("text", "")

            # Format: "Agent: Hello there. Customer: Yes, I need help."
            if speaker.lower() == "agent":
                speaker_label = "Agent"
            elif speaker.lower() == "customer":
                speaker_label = "Customer"
            else:
                speaker_label = speaker.title()

            transcript_parts.append(f"{speaker_label}: {text}")

        return " ".join(transcript_parts)

    def _compute_quality_metrics(self, original_text: str, normalized_text: str, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Step 5: Compute quality metrics for the normalized transcript."""
        metrics = {
            "original_length": len(original_text),
            "normalized_length": len(normalized_text),
            "compression_ratio": len(normalized_text) / len(original_text) if original_text else 1.0,
            "segment_count": len(segments),
            "speaker_changes": self._count_speaker_changes(segments),
            "avg_segment_length": sum(len(s.get("text", "")) for s in segments) / len(segments) if segments else 0,
            "avg_confidence": sum(s.get("confidence", 1.0) for s in segments) / len(segments) if segments else 1.0
        }

        return metrics

    def _count_speaker_changes(self, segments: List[Dict[str, Any]]) -> int:
        """Count how many times speakers change in the transcript."""
        if len(segments) < 2:
            return 0

        changes = 0
        current_speaker = segments[0].get("speaker")

        for segment in segments[1:]:
            if segment.get("speaker") != current_speaker:
                changes += 1
                current_speaker = segment.get("speaker")

        return changes
