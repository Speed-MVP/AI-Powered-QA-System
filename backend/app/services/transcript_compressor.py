"""
Transcript Compressor Service
Phase 4: Deterministic LLM Evaluator Integration

Compresses transcripts to extract only essential information for LLM evaluation:
- Key statements
- Conflict points
- Escalations
- Apologies
- Resolution summary
- Emotion transitions
- Tone mismatches
"""

from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


class TranscriptCompressor:
    """
    Compresses transcripts to essential information for deterministic LLM evaluation.
    """

    def compress_transcript(
        self,
        transcript_segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Compress transcript to key information.
        
        Args:
            transcript_segments: Diarized transcript segments
            sentiment_analysis: Optional sentiment analysis data
            
        Returns:
            Compressed transcript summary with:
            - key_statements: Important utterances
            - conflict_points: Where conflicts occurred
            - escalations: Escalation requests
            - apologies: Apology moments
            - resolution_summary: Resolution information
        """
        key_statements = self._extract_key_statements(transcript_segments)
        conflict_points = self._extract_conflict_points(transcript_segments, sentiment_analysis)
        escalations = self._extract_escalations(transcript_segments)
        apologies = self._extract_apologies(transcript_segments)
        resolution_summary = self._extract_resolution_summary(transcript_segments)
        
        return {
            "key_statements": key_statements,
            "conflict_points": conflict_points,
            "escalations": escalations,
            "apologies": apologies,
            "resolution_summary": resolution_summary,
            "total_segments": len(transcript_segments),
            "compressed_segments": len(key_statements) + len(conflict_points) + len(escalations) + len(apologies)
        }

    def summarize_emotion(
        self,
        sentiment_analysis: Optional[List[Dict[str, Any]]],
        transcript_segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Summarize customer emotion trajectory (start → middle → end).
        
        Args:
            sentiment_analysis: Sentiment analysis data
            transcript_segments: Transcript segments
            
        Returns:
            Emotion summary with start, middle, end states
        """
        if not sentiment_analysis:
            return {
                "start": "unknown",
                "middle": "unknown",
                "end": "unknown",
                "trajectory": "unknown"
            }
        
        # Find caller segments with sentiment
        caller_sentiments = []
        for sent in sentiment_analysis:
            if sent.get("speaker") == "caller":
                sentiment_obj = sent.get("sentiment", {})
                if isinstance(sentiment_obj, dict):
                    sentiment_value = sentiment_obj.get("sentiment", "neutral")
                else:
                    sentiment_value = sentiment_obj or "neutral"
                
                caller_sentiments.append({
                    "sentiment": sentiment_value,
                    "start": sent.get("start", 0),
                    "end": sent.get("end", 0)
                })
        
        if not caller_sentiments:
            return {
                "start": "neutral",
                "middle": "neutral",
                "end": "neutral",
                "trajectory": "stable"
            }
        
        # Sort by time
        caller_sentiments.sort(key=lambda x: x.get("start", 0))
        
        # Get start, middle, end
        total_segments = len(caller_sentiments)
        start_idx = 0
        middle_idx = total_segments // 2
        end_idx = total_segments - 1
        
        start_sentiment = caller_sentiments[start_idx].get("sentiment", "neutral")
        middle_sentiment = caller_sentiments[middle_idx].get("sentiment", "neutral")
        end_sentiment = caller_sentiments[end_idx].get("sentiment", "neutral")
        
        # Determine trajectory
        trajectory = "stable"
        if start_sentiment == "negative" and end_sentiment == "positive":
            trajectory = "improved"
        elif start_sentiment == "positive" and end_sentiment == "negative":
            trajectory = "worsened"
        elif start_sentiment == "negative" or middle_sentiment == "negative" or end_sentiment == "negative":
            trajectory = "negative"
        elif start_sentiment == "positive" or middle_sentiment == "positive" or end_sentiment == "positive":
            trajectory = "positive"
        
        return {
            "start": start_sentiment,
            "middle": middle_sentiment,
            "end": end_sentiment,
            "trajectory": trajectory
        }

    def extract_tone_mismatches(
        self,
        transcript_segments: List[Dict[str, Any]],
        sentiment_analysis: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Extract tone mismatch flags (pre-computed tone anomalies).
        
        Args:
            transcript_segments: Transcript segments
            sentiment_analysis: Sentiment analysis data
            
        Returns:
            Dictionary with tone mismatch flags:
            - mismatches: List of mismatch events
            - major_mismatches: Critical tone issues
            - minor_mismatches: Minor tone issues
        """
        mismatches = []
        major_mismatches = []
        minor_mismatches = []
        
        if not sentiment_analysis:
            return {
                "mismatches": [],
                "major_mismatches": [],
                "minor_mismatches": [],
                "has_mismatches": False
            }
        
        # Check for empathy phrases with neutral/negative tone
        empathy_phrases = [
            "i understand", "i'm sorry", "i apologize", "that sounds",
            "let me help", "i can help"
        ]
        
        for segment in transcript_segments:
            if segment.get("speaker") == "agent":
                text = segment.get("text", "").lower()
                
                # Check if agent used empathy phrase
                has_empathy_phrase = any(phrase in text for phrase in empathy_phrases)
                
                if has_empathy_phrase:
                    # Find corresponding sentiment
                    segment_start = segment.get("start", 0)
                    segment_end = segment.get("end", 0)
                    
                    for sent in sentiment_analysis:
                        if sent.get("speaker") == "agent":
                            sent_start = sent.get("start", 0)
                            sent_end = sent.get("end", 0)
                            
                            # Check if sentiment overlaps with segment
                            if (sent_start <= segment_end and sent_end >= segment_start):
                                sentiment_obj = sent.get("sentiment", {})
                                if isinstance(sentiment_obj, dict):
                                    sentiment_value = sentiment_obj.get("sentiment", "neutral")
                                else:
                                    sentiment_value = sentiment_obj or "neutral"
                                
                                # Check for mismatch
                                if sentiment_value == "negative" or sentiment_value == "neutral":
                                    mismatch = {
                                        "type": "insincerity",
                                        "segment_start": segment_start,
                                        "text": segment.get("text", ""),
                                        "sentiment": sentiment_value,
                                        "severity": "major" if sentiment_value == "negative" else "minor"
                                    }
                                    mismatches.append(mismatch)
                                    
                                    if sentiment_value == "negative":
                                        major_mismatches.append(mismatch)
                                    else:
                                        minor_mismatches.append(mismatch)
                                break
        
        return {
            "mismatches": mismatches,
            "major_mismatches": major_mismatches,
            "minor_mismatches": minor_mismatches,
            "has_mismatches": len(mismatches) > 0
        }

    def _extract_key_statements(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract key statements from transcript."""
        key_statements = []
        
        # Extract first agent statement (greeting)
        agent_segments = [s for s in segments if s.get("speaker") == "agent"]
        if agent_segments:
            first_agent = min(agent_segments, key=lambda x: x.get("start", 0))
            key_statements.append({
                "type": "greeting",
                "speaker": "agent",
                "text": first_agent.get("text", ""),
                "start": first_agent.get("start", 0)
            })
        
        # Extract last agent statement (closing)
        if agent_segments:
            last_agent = max(agent_segments, key=lambda x: x.get("end", 0))
            key_statements.append({
                "type": "closing",
                "speaker": "agent",
                "text": last_agent.get("text", ""),
                "start": last_agent.get("start", 0)
            })
        
        # Extract important keywords/phrases
        important_keywords = [
            "problem", "issue", "complaint", "refund", "cancel", "escalate",
            "supervisor", "manager", "resolve", "solution", "fixed"
        ]
        
        for segment in segments:
            text = segment.get("text", "").lower()
            if any(keyword in text for keyword in important_keywords):
                key_statements.append({
                    "type": "important",
                    "speaker": segment.get("speaker", "unknown"),
                    "text": segment.get("text", ""),
                    "start": segment.get("start", 0)
                })
        
        return key_statements[:20]  # Limit to 20 key statements

    def _extract_conflict_points(self, segments: List[Dict[str, Any]], sentiment_analysis: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Extract conflict points from transcript."""
        conflict_points = []
        
        # Look for negative sentiment segments
        if sentiment_analysis:
            for sent in sentiment_analysis:
                if sent.get("speaker") == "caller":
                    sentiment_obj = sent.get("sentiment", {})
                    if isinstance(sentiment_obj, dict):
                        sentiment_value = sentiment_obj.get("sentiment", "neutral")
                    else:
                        sentiment_value = sentiment_obj or "neutral"
                    
                    if sentiment_value == "negative":
                        conflict_points.append({
                            "start": sent.get("start", 0),
                            "end": sent.get("end", 0),
                            "severity": "high"
                        })
        
        # Look for conflict keywords
        conflict_keywords = ["no", "wrong", "unacceptable", "terrible", "awful", "horrible"]
        
        for segment in segments:
            if segment.get("speaker") == "caller":
                text = segment.get("text", "").lower()
                if any(keyword in text for keyword in conflict_keywords):
                    conflict_points.append({
                        "start": segment.get("start", 0),
                        "end": segment.get("end", 0),
                        "text": segment.get("text", ""),
                        "severity": "medium"
                    })
        
        return conflict_points[:10]  # Limit to 10 conflict points

    def _extract_escalations(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract escalation requests."""
        escalations = []
        
        escalation_keywords = [
            "supervisor", "manager", "escalate", "speak to", "higher", "complaint"
        ]
        
        for segment in segments:
            text = segment.get("text", "").lower()
            if any(keyword in text for keyword in escalation_keywords):
                escalations.append({
                    "speaker": segment.get("speaker", "unknown"),
                    "text": segment.get("text", ""),
                    "start": segment.get("start", 0)
                })
        
        return escalations

    def _extract_apologies(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract apology moments."""
        apologies = []
        
        apology_keywords = [
            "sorry", "apologize", "apology", "regret", "mistake", "error"
        ]
        
        for segment in segments:
            if segment.get("speaker") == "agent":
                text = segment.get("text", "").lower()
                if any(keyword in text for keyword in apology_keywords):
                    apologies.append({
                        "text": segment.get("text", ""),
                        "start": segment.get("start", 0)
                    })
        
        return apologies

    def _extract_resolution_summary(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract resolution summary."""
        resolution_keywords = [
            "resolved", "fixed", "solved", "taken care of", "handled", "completed"
        ]
        
        resolution_found = False
        resolution_text = ""
        
        # Check last few segments for resolution
        last_segments = segments[-10:] if len(segments) > 10 else segments
        
        for segment in reversed(last_segments):
            text = segment.get("text", "").lower()
            if any(keyword in text for keyword in resolution_keywords):
                resolution_found = True
                resolution_text = segment.get("text", "")
                break
        
        return {
            "resolved": resolution_found,
            "resolution_text": resolution_text,
            "confidence": 0.8 if resolution_found else 0.2
        }

