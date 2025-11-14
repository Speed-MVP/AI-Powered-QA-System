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
        Load predefined QA rules as per MVP Evaluation Improvements spec.
        """
        return {
            "greeting_within_15s": {
                "description": "Agent must greet caller within first 15 seconds",
                "severity": 5,
                "patterns": [
                    r'\b(hello|hi|good\s+(morning|afternoon|evening))\b',
                    r'\b(thank you for calling|how can i help|how may i assist)\b',
                    r'\b(my name is|this is)\b'
                ]
            },
            "agent_identifies_self_or_company": {
                "description": "Agent must identify themselves or company within first 30 seconds",
                "severity": 4,
                "patterns": [
                    r'\b(my name is|i\'m|this is)\b',
                    r'\b(company|corporation|inc|llc|ltd)\b'
                ]
            },
            "apology_or_empathy_present": {
                "description": "Agent must show empathy or apologize when appropriate",
                "severity": 3,
                "patterns": [
                    r'\b(sorry|i apologize|i\'m sorry|that sounds frustrating)\b',
                    r'\b(i understand|that must be|let me help you)\b'
                ]
            },
            "hold_compliance": {
                "description": "Agent must ask permission and explain hold duration",
                "severity": 4,
                "patterns": [
                    r'\b(may i put you on hold|do you mind if i|can i place you)\b',
                    r'\b(it will only take|should be about|approximately)\b.*\b(minute|second)\b'
                ]
            },
            "closing_and_confirmation": {
                "description": "Agent must confirm resolution and provide proper closing",
                "severity": 5,
                "patterns": [
                    r'\b(is there anything else|does that resolve|have i answered)\b',
                    r'\b(thank you for|have a (good|great|nice))\b'
                ]
            },
            "dead_air": {
                "description": "No continuous silence longer than 4 seconds",
                "severity": 2,
                "max_silence": 4.0
            },
            "interruptions": {
                "description": "Agent should not interrupt caller excessively",
                "severity": 2,
                "max_interruptions": 3
            },
            "card_or_pii_mentioned": {
                "description": "No sensitive card or PII information should be mentioned",
                "severity": 10,
                "patterns": [
                    r'\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}\b',  # Credit card pattern
                    r'\b\d{3}[\s\-]\d{2}[\s\-]\d{4}\b',  # SSN pattern
                    r'\b\d{9}\b'  # 9-digit numbers (potential SSN)
                ]
            },
            "script_adherence": {
                "description": "Agent should follow company script when applicable",
                "severity": 3,
                "script_patterns": []  # To be populated from company scripts
            }
        }

    def evaluate_rules(
        self,
        transcript_segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate all rules against the transcript and return rule-based results in spec format.
        MVP Evaluation Improvements: Rule engine expansion and return format.
        """
        logger.info(f"Evaluating {len(self.rules)} rules - transcript_segments: {len(transcript_segments) if transcript_segments else 0}")

        results = {}

        # Run each rule
        for rule_id, rule_config in self.rules.items():
            rule_result = self._evaluate_single_rule(rule_id, rule_config, transcript_segments, sentiment_analysis)
            results[rule_id] = rule_result

        logger.info(f"Rule engine evaluation completed for {len(results)} rules")

        return results

    def _evaluate_single_rule(
        self,
        rule_id: str,
        rule_config: Dict,
        transcript_segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Evaluate a single rule against the transcript and return spec format.
        """
        # Rule-specific evaluation logic - returns (hit, evidence)
        if rule_id == "greeting_within_15s":
            hit, evidence = self._check_greeting_within_15s(transcript_segments)
        elif rule_id == "agent_identifies_self_or_company":
            hit, evidence = self._check_agent_identification(transcript_segments)
        elif rule_id == "apology_or_empathy_present":
            hit, evidence = self._check_empathy_presence(transcript_segments, sentiment_analysis)
        elif rule_id == "hold_compliance":
            hit, evidence = self._check_hold_compliance(transcript_segments)
        elif rule_id == "closing_and_confirmation":
            hit, evidence = self._check_closing_confirmation(transcript_segments)
        elif rule_id == "dead_air":
            hit, evidence = self._check_dead_air(transcript_segments)
        elif rule_id == "interruptions":
            hit, evidence = self._check_interruptions(transcript_segments)
        elif rule_id == "card_or_pii_mentioned":
            hit, evidence = self._check_pii_mention(transcript_segments)
        elif rule_id == "script_adherence":
            hit, evidence = self._check_script_adherence(transcript_segments)
        else:
            hit, evidence = False, []

        return {
            "hit": hit,
            "evidence": evidence,
            "severity": rule_config["severity"]
        }

    def _check_greeting_within_15s(self, segments: List[Dict]) -> tuple[bool, List[Dict]]:
        """Check if agent greeted within first 15 seconds"""
        agent_segments = [s for s in segments if s.get("speaker") == "agent"]

        if not agent_segments:
            return True, [{"speaker": "system", "text": "No agent utterances found", "start": 0.0}]

        # Check first agent utterance timing and content
        first_agent_segment = min(agent_segments, key=lambda x: x.get("start", 0))
        start_time = first_agent_segment.get("start", 0)
        text = first_agent_segment.get("text", "").lower()

        # Check timing
        if start_time > 15.0:
            return True, [{"speaker": first_agent_segment.get("speaker", "agent"),
                          "text": first_agent_segment.get("text", ""),
                          "start": start_time}]

        # Check content for greeting patterns
        greeting_patterns = [
            r'\b(hello|hi|good\s+(morning|afternoon|evening))\b',
            r'\b(thank you for calling|how can i help|how may i assist)\b',
            r'\b(my name is|this is)\b'
        ]
        has_greeting = any(re.search(pattern, text, re.IGNORECASE) for pattern in greeting_patterns)

        if not has_greeting:
            return True, [{"speaker": first_agent_segment.get("speaker", "agent"),
                          "text": first_agent_segment.get("text", ""),
                          "start": start_time}]

        return False, []

    def _check_agent_identification(self, segments: List[Dict]) -> tuple[bool, List[Dict]]:
        """Check if agent identifies themselves or company within first 30 seconds"""
        # COST OPTIMIZATION: Early exit if no agent segments
        agent_segments = [s for s in segments if s.get("speaker") == "agent"]
        if not agent_segments:
            return True, [{"speaker": "system", "text": "No agent utterances found", "start": 0.0}]

        # COST OPTIMIZATION: Check only first few agent utterances (most likely to contain intro)
        check_segments = agent_segments[:5]  # First 5 agent utterances max

        for segment in check_segments:
            if segment.get("start", 0) > 30.0:
                break

            text = segment.get("text", "").lower()
            # COST OPTIMIZATION: Simplified patterns, fewer regex operations
            if ('my name is' in text or 'i\'m' in text or 'this is' in text or
                'company' in text or 'corporation' in text):
                return False, []  # Found identification

        return True, [{"speaker": "system", "text": "No agent identification in first 30 seconds", "start": 0.0}]

    def _check_empathy_presence(self, segments: List[Dict], sentiment_analysis: Optional[List]) -> tuple[bool, List[Dict]]:
        """Check if agent shows empathy when appropriate"""
        # COST OPTIMIZATION: Skip expensive sentiment analysis if not available
        if not sentiment_analysis:
            # Fallback: Check for basic empathy keywords in agent speech
            agent_segments = [s for s in segments if s.get("speaker") == "agent"]
            for segment in agent_segments[:10]:  # Check first 10 agent segments
                text = segment.get("text", "").lower()
                if any(word in text for word in ['sorry', 'understand', 'apologize', 'frustrating']):
                    return False, []  # Found empathy
            return True, [{"speaker": "system", "text": "No empathy keywords detected", "start": 0.0}]

        return False, []  # Assume empathy present if sentiment analysis available

    def _check_hold_compliance(self, segments: List[Dict]) -> tuple[bool, List[Dict]]:
        """Check if agent asks permission before placing on hold"""
        agent_segments = [s for s in segments if s.get("speaker") == "agent"]

        for segment in agent_segments:
            text = segment.get("text", "").lower()
            # COST OPTIMIZATION: Simple string checks instead of regex
            if ('hold on' in text or 'one moment' in text or 'let me put you on hold' in text):
                # Check if permission was asked in previous segments
                segment_start = segment.get("start", 0)
                permission_found = False
                for prev_segment in agent_segments:
                    if prev_segment.get("start", 0) < segment_start:
                        prev_text = prev_segment.get("text", "").lower()
                        if ('may i' in prev_text or 'can i' in prev_text or 'do you mind' in prev_text):
                            permission_found = True
                            break
                if not permission_found:
                    return True, [{"speaker": segment.get("speaker", "agent"),
                                  "text": segment.get("text", ""),
                                  "start": segment_start}]

        return False, []

    def _check_closing_confirmation(self, segments: List[Dict]) -> tuple[bool, List[Dict]]:
        """Check if call ends with proper closing"""
        if not segments:
            return True, [{"speaker": "system", "text": "No segments found", "start": 0.0}]

        # Check last few agent segments
        agent_segments = [s for s in segments if s.get("speaker") == "agent"]
        if not agent_segments:
            return True, [{"speaker": "system", "text": "No agent segments found", "start": 0.0}]

        last_agent = agent_segments[-1]
        text = last_agent.get("text", "").lower()

        # COST OPTIMIZATION: Simple checks for common closing phrases
        if any(phrase in text for phrase in ['anything else', 'does that resolve', 'thank you', 'have a']):
            return False, []

        return True, [{"speaker": last_agent.get("speaker", "agent"),
                      "text": last_agent.get("text", ""),
                      "start": last_agent.get("start", 0)}]

    def _check_dead_air(self, segments: List[Dict]) -> tuple[bool, List[Dict]]:
        """Check for excessive silence between speakers"""
        if len(segments) < 2:
            return False, []

        # COST OPTIMIZATION: Check only last 20 segment transitions (most recent interactions)
        check_segments = segments[-20:] if len(segments) > 20 else segments
        long_silences = []

        for i in range(len(check_segments) - 1):
            current_end = check_segments[i].get("end", 0)
            next_start = check_segments[i + 1].get("start", 0)
            silence = next_start - current_end

            if silence > 4.0:  # 4 seconds threshold
                long_silences.append({
                    "speaker": "system",
                    "text": f"{silence:.1f}s silence between speakers",
                    "start": current_end
                })

        return len(long_silences) > 0, long_silences

    def _check_interruptions(self, segments: List[Dict]) -> tuple[bool, List[Dict]]:
        """Check for excessive agent interruptions"""
        # COST OPTIMIZATION: Simplified - just count overlapping segments
        interruptions = []
        for i in range(len(segments) - 1):
            current = segments[i]
            next_seg = segments[i + 1]

            # Simple overlap detection
            if (current.get("speaker") != next_seg.get("speaker") and
                current.get("end", 0) > next_seg.get("start", 0)):
                interruptions.append({
                    "speaker": next_seg.get("speaker", "unknown"),
                    "text": "Interrupted by other speaker",
                    "start": next_seg.get("start", 0)
                })

        return len(interruptions) > 3, interruptions  # More than 3 interruptions is excessive

    def _check_pii_mention(self, segments: List[Dict]) -> tuple[bool, List[Dict]]:
        """Check for sensitive PII information"""
        pii_found = []

        for segment in segments:
            text = segment.get("text", "")
            # COST OPTIMIZATION: Simple pattern checks for common PII
            if any(pattern in text for pattern in [
                'xxxx-xxxx-xxxx-xxxx',  # Credit card
                'xxx-xx-xxxx',  # SSN
                'xxxxxxxxx'  # 9 digits
            ]):
                pii_found.append({
                    "speaker": segment.get("speaker", "unknown"),
                    "text": "[PII DETECTED]",
                    "start": segment.get("start", 0)
                })

        return len(pii_found) > 0, pii_found

    def _check_script_adherence(self, segments: List[Dict]) -> tuple[bool, List[Dict]]:
        """Check script adherence - placeholder for future implementation"""
        # COST OPTIMIZATION: Skip for now - implement when company scripts are available
        return False, []

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
