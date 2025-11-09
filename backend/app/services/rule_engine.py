"""
Rule Engine Service for Explicit QA Policy Compliance Checking
Phase 2: Accuracy & Intelligence Expansion
"""

from typing import List, Dict, Any, Optional
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class RuleEngineService:
    """
    Phase 2: Rule Engine for explicit QA policy compliance checking.
    Runs deterministic rules before LLM evaluation to pre-score policy violations.
    """

    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Dict]:
        """
        Load predefined QA rules. In production, these could be configurable via database.
        """
        return {
            "greeting_within_15s": {
                "name": "Greeting within first 15 seconds",
                "category": "Professionalism",
                "severity": "major",
                "description": "Agent must greet caller within first 15 seconds",
                "time_window_start": 0,
                "time_window_end": 15,
                "required_patterns": [
                    r'\b(hello|hi|good\s+(morning|afternoon|evening))\b',
                    r'\b(thank you for calling|how can i help|how may i assist)\b',
                    r'\b(my name is|this is)\b'
                ]
            },
            "empathy_in_frustrated_segments": {
                "name": "Empathy keywords in frustrated caller segments",
                "category": "Empathy",
                "severity": "critical",
                "description": "Agent must use empathy keywords when caller shows frustration",
                "trigger_sentiment": "negative",
                "required_patterns": [
                    r'\b(i understand|i apologize|i\'m sorry|that sounds frustrating)\b',
                    r'\b(i can imagine|that must be|let me help you with that)\b',
                    r'\b(frustrating|unfortunate|annoying|i hear you|i feel you)\b'
                ]
            },
            "hold_without_permission": {
                "name": "Placing caller on hold without permission",
                "category": "Professionalism",
                "severity": "major",
                "description": "Agent must ask permission before placing caller on hold",
                "forbidden_patterns": [
                    r'\b(hold on|one moment|let me put you on hold)\b.*[^\?]*$'
                ],
                "required_before_forbidden": [
                    r'\b(may i|can i|do you mind if i)\b.*\bhold\b'
                ]
            },
            "closing_verification": {
                "name": "Proper call closing with verification",
                "category": "Resolution",
                "severity": "minor",
                "description": "Agent must verify resolution before closing call",
                "required_patterns": [
                    r'\b(is there anything else|does that resolve|have i answered)\b',
                    r'\b(thank you for|have a (good|great|nice))\b'
                ]
            },
            "no_dead_air": {
                "name": "No extended periods of silence",
                "category": "Communication",
                "severity": "minor",
                "description": "No gaps longer than 10 seconds between speakers",
                "max_silence_seconds": 10
            }
        }

    def evaluate_rules(
        self,
        transcript_segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate all rules against the transcript and return rule-based violations/scores.
        """
        logger.info(f"Evaluating rules - transcript_segments: {len(transcript_segments) if transcript_segments else 0}, sentiment_analysis: {type(sentiment_analysis)} len: {len(sentiment_analysis) if isinstance(sentiment_analysis, list) else 'N/A'}")

        violations = []
        rule_scores = {}

        # Run each rule
        for rule_id, rule_config in self.rules.items():
            rule_result = self._evaluate_single_rule(rule_id, rule_config, transcript_segments, sentiment_analysis)
            if rule_result["triggered"]:
                violations.append(rule_result)

                # Update rule scores for ensemble evaluation
                category = rule_config["category"]
                if category not in rule_scores:
                    rule_scores[category] = {"score": 100, "violations": []}

                # Apply penalty based on severity
                penalty = self._get_penalty_for_severity(rule_config["severity"])
                rule_scores[category]["score"] = max(0, rule_scores[category]["score"] - penalty)
                rule_scores[category]["violations"].append(rule_result)

        logger.info(f"Rule engine found {len(violations)} violations across {len(rule_scores)} categories")

        return {
            "violations": violations,
            "rule_scores": rule_scores,
            "total_violations": len(violations),
            "categories_affected": list(rule_scores.keys())
        }

    def _evaluate_single_rule(
        self,
        rule_id: str,
        rule_config: Dict,
        transcript_segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Evaluate a single rule against the transcript.
        """
        rule_result = {
            "rule_id": rule_id,
            "rule_name": rule_config["name"],
            "category": rule_config["category"],
            "severity": rule_config["severity"],
            "description": rule_config["description"],
            "triggered": False,
            "evidence": [],
            "timestamp": datetime.utcnow().isoformat()
        }

        # Rule-specific evaluation logic
        if rule_id == "greeting_within_15s":
            rule_result = self._check_greeting_rule(rule_result, rule_config, transcript_segments)
        elif rule_id == "empathy_in_frustrated_segments":
            rule_result = self._check_empathy_rule(rule_result, rule_config, transcript_segments, sentiment_analysis)
        elif rule_id == "hold_without_permission":
            rule_result = self._check_hold_rule(rule_result, rule_config, transcript_segments)
        elif rule_id == "closing_verification":
            rule_result = self._check_closing_rule(rule_result, rule_config, transcript_segments)
        elif rule_id == "no_dead_air":
            rule_result = self._check_silence_rule(rule_result, rule_config, transcript_segments)

        return rule_result

    def _check_greeting_rule(self, rule_result: Dict, rule_config: Dict, segments: List[Dict]) -> Dict:
        """Check if agent greeted within first 15 seconds"""
        agent_segments = [s for s in segments if s.get("speaker") == "agent"]

        if not agent_segments:
            rule_result["triggered"] = True
            rule_result["evidence"] = ["No agent utterances found"]
            return rule_result

        # Check first agent utterance timing and content
        first_agent_segment = min(agent_segments, key=lambda x: x.get("start", 0))
        start_time = first_agent_segment.get("start", 0)
        text = first_agent_segment.get("text", "").lower()

        # Check timing
        if start_time > rule_config["time_window_end"]:
            rule_result["triggered"] = True
            rule_result["evidence"] = [f"First agent utterance at {start_time:.1f}s (should be within {rule_config['time_window_end']}s)"]
            return rule_result

        # Check content for greeting patterns
        has_greeting = any(re.search(pattern, text, re.IGNORECASE) for pattern in rule_config["required_patterns"])

        if not has_greeting:
            rule_result["triggered"] = True
            rule_result["evidence"] = [f"First agent utterance lacks greeting: '{first_agent_segment.get('text', '')}'"]
            return rule_result

        return rule_result

    def _check_empathy_rule(self, rule_result: Dict, rule_config: Dict, segments: List[Dict], sentiment_analysis: Optional[List]) -> Dict:
        """Check if agent uses empathy keywords during frustrated caller segments"""
        if not sentiment_analysis or not isinstance(sentiment_analysis, list):
            return rule_result

        # Find frustrated caller segments
        frustrated_segments = []
        for sent in sentiment_analysis:
            if not isinstance(sent, dict):
                continue  # Skip invalid sentiment entries
            # Handle both Deepgram sentiment format and other formats
            sentiment_obj = sent.get("sentiment", {})
            sentiment_value = None

            # Deepgram format: sentiment object has direct properties
            if isinstance(sentiment_obj, dict):
                sentiment_value = sentiment_obj.get("sentiment")
            else:
                # Fallback for other formats
                sentiment_value = sentiment_obj

            if (sent.get("speaker") == "caller" and
                sentiment_value == "negative"):
                frustrated_segments.append(sent)

        if not frustrated_segments:
            return rule_result  # No frustrated segments to check

        # Check if agent responded with empathy in each frustrated segment
        empathy_missing = []
        for frustrated_seg in frustrated_segments:
            seg_end_time = frustrated_seg.get("end", 0)

            # Look for agent response within 10 seconds after frustrated segment
            agent_response_found = False
            for segment in segments:
                if (segment.get("speaker") == "agent" and
                    segment.get("start", 0) >= seg_end_time and
                    segment.get("start", 0) <= seg_end_time + 10):

                    text = segment.get("text", "").lower()
                    has_empathy = any(re.search(pattern, text, re.IGNORECASE)
                                    for pattern in rule_config["required_patterns"])

                    if has_empathy:
                        agent_response_found = True
                        break

            if not agent_response_found:
                empathy_missing.append(f"No empathy response to frustrated segment at {seg_end_time:.1f}s")

        if empathy_missing:
            rule_result["triggered"] = True
            rule_result["evidence"] = empathy_missing

        return rule_result

    def _check_hold_rule(self, rule_result: Dict, rule_config: Dict, segments: List[Dict]) -> Dict:
        """Check if agent asks permission before placing on hold"""
        for segment in segments:
            if segment.get("speaker") == "agent":
                text = segment.get("text", "").lower()

                # Check for forbidden hold patterns
                forbidden_found = any(re.search(pattern, text, re.IGNORECASE)
                                    for pattern in rule_config["forbidden_patterns"])

                if forbidden_found:
                    # Check if permission was asked before this segment
                    permission_asked = False
                    segment_start = segment.get("start", 0)

                    for prev_segment in segments:
                        if (prev_segment.get("speaker") == "agent" and
                            prev_segment.get("start", 0) < segment_start):

                            prev_text = prev_segment.get("text", "").lower()
                            permission_found = any(re.search(pattern, prev_text, re.IGNORECASE)
                                                 for pattern in rule_config["required_before_forbidden"])

                            if permission_found:
                                permission_asked = True
                                break

                    if not permission_asked:
                        rule_result["triggered"] = True
                        rule_result["evidence"] = [f"Hold without permission: '{segment.get('text', '')}'"]
                        break

        return rule_result

    def _check_closing_rule(self, rule_result: Dict, rule_config: Dict, segments: List[Dict]) -> Dict:
        """Check if call ends with proper closing verification"""
        if not segments:
            return rule_result

        # Check last few agent segments for closing patterns
        agent_segments = [s for s in segments if s.get("speaker") == "agent"]
        if not agent_segments:
            rule_result["triggered"] = True
            rule_result["evidence"] = ["No agent closing found"]
            return rule_result

        # Check last agent segment
        last_agent_segment = max(agent_segments, key=lambda x: x.get("end", 0))
        text = last_agent_segment.get("text", "").lower()

        has_closing = any(re.search(pattern, text, re.IGNORECASE)
                         for pattern in rule_config["required_patterns"])

        if not has_closing:
            rule_result["triggered"] = True
            rule_result["evidence"] = [f"Improper closing: '{last_agent_segment.get('text', '')}'"]

        return rule_result

    def _check_silence_rule(self, rule_result: Dict, rule_config: Dict, segments: List[Dict]) -> Dict:
        """Check for excessive silence between speakers"""
        if len(segments) < 2:
            return rule_result

        long_silences = []
        sorted_segments = sorted(segments, key=lambda x: x.get("start", 0))

        for i in range(len(sorted_segments) - 1):
            current_end = sorted_segments[i].get("end", 0)
            next_start = sorted_segments[i + 1].get("start", 0)
            silence_duration = next_start - current_end

            if silence_duration > rule_config["max_silence_seconds"]:
                long_silences.append(
                    f"{silence_duration:.1f}s silence between '{sorted_segments[i].get('speaker')}' "
                    f"and '{sorted_segments[i + 1].get('speaker')}' segments"
                )

        if long_silences:
            rule_result["triggered"] = True
            rule_result["evidence"] = long_silences

        return rule_result

    def _get_penalty_for_severity(self, severity: str) -> int:
        """Convert severity level to score penalty"""
        penalty_map = {
            "critical": 25,
            "major": 15,
            "minor": 5
        }
        return penalty_map.get(severity, 10)
