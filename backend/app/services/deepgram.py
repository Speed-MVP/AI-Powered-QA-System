import aiohttp
from app.config import settings
import logging
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)


class DeepgramService:
    def __init__(self):
        self.api_key = settings.deepgram_api_key
        self.base_url = "https://api.deepgram.com/v1/listen"
        if not self.api_key:
            raise ValueError("Deepgram API key not configured")
        # Production-safe client timeout (connect + total)
        self._timeout = aiohttp.ClientTimeout(total=180, connect=15)
    
    async def transcribe(self, file_url: str):
        """Transcribe audio with diarization (alignment removed)"""
        logger.info("Transcription starting - alignment disabled/removed")

        if not file_url or not isinstance(file_url, str):
            raise ValueError("file_url is required for transcription")

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "model": "nova-2",
            "diarize": "true",
            "punctuate": "true",
            "utterances": "true",
            "sentiment": "true",  # Enable sentiment analysis (voice-based)
            "topics": "false",  # Can enable for topic detection if needed
            "intents": "false"  # Can enable for intent detection if needed
        }
        
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.post(
                self.base_url,
                json={"url": file_url},
                headers=headers,
                params=params
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Deepgram error: {response.status} - {error_text}")
                
                data = await response.json()
                
                # Extract transcript
                transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
                
                # Extract diarized segments (utterances)
                utterances = data.get("results", {}).get("utterances", [])
                diarized_segments = []
                
                # NEW: Context-based speaker identification
                # Instead of assuming first speaker = caller, analyze conversation patterns
                speaker_map = self._identify_speakers_by_context(utterances)
                
                for utterance in utterances:
                    speaker_num = utterance.get("speaker", 0)
                    speaker_label = speaker_map.get(speaker_num, "caller" if speaker_num == 0 else "agent")
                    start = utterance.get("start", 0)
                    end = utterance.get("end", 0)
                    text = utterance.get("transcript", "")
                    
                    diarized_segments.append({
                        "speaker": speaker_label,
                        "text": text,
                        "start": start,
                        "end": end
                    })
                
                # Extract confidence
                confidence = data["results"]["channels"][0].get("alternatives", [{}])[0].get("confidence", 0)

                # Extract sentiment analysis (voice-based tone detection)
                # NOW: Capture sentiment for BOTH caller and agent
                sentiment_data = []
                if "utterances" in data.get("results", {}):
                    for utterance in data["results"]["utterances"]:
                        sentiment_info = utterance.get("sentiment", None)
                        if sentiment_info:
                            speaker_num = utterance.get("speaker", 0)
                            speaker_label = speaker_map.get(speaker_num, "caller" if speaker_num == 0 else "agent")
                            sentiment_data.append({
                                "speaker": speaker_label,
                                "sentiment": sentiment_info,  # Deepgram's sentiment analysis
                                "start": utterance.get("start", 0),
                                "end": utterance.get("end", 0),
                                "text": utterance.get("transcript", "")
                            })
                
                # Phase 2: Calculate adaptive baseline voice characteristics per speaker (first 30s window)
                # This prevents mislabeling intense-sounding agents as angry
                voice_baselines = self._calculate_adaptive_voice_baselines(sentiment_data, speaker_map)
                
                return {
                    "transcript": transcript,
                    "diarized_segments": diarized_segments,
                    "confidence": confidence,
                    "sentiment_analysis": sentiment_data,  # BOTH caller and agent
                    "voice_baselines": voice_baselines  # NEW: Natural voice characteristics
                }
    
    def _identify_speakers_by_context(self, utterances: List[Dict]) -> Dict[int, str]:
        """
        Identify caller vs agent based on conversation context, not just order.
        Analyzes: greeting patterns, question patterns, scripted language, etc.
        """
        if not utterances:
            return {}
        
        # Agent indicators (typically):
        # - Greetings: "Thank you for calling", "How can I help", "My name is"
        # - Scripted phrases: "I understand", "I apologize", "Let me help you"
        # - Questions about account: "Can I have your account number", "What's your name"
        # - Closing phrases: "Is there anything else", "Have a great day"
        
        # Caller indicators (typically):
        # - Asking for help: "I need help with", "I have a problem", "Can you help me"
        # - Stating issues: "My account is", "I'm having trouble", "It's not working"
        # - Expressing emotions: "I'm frustrated", "This is unacceptable", "I'm angry"
        
        agent_indicators = [
            r'thank you for calling',
            r'how can i (help|assist)',
            r'my name is',
            r'i understand',
            r'i apologize',
            r'let me (help|assist|check)',
            r'can i have your (account|name|phone)',
            r'what\'s your (name|account|phone)',
            r'is there anything else',
            r'have a (great|wonderful|nice) (day|evening)',
            r'for calling',
            r'your account number',
            r'i\'ll (help|check|look into)',
            r'please (hold|wait)',
            r'one moment',
            r'may i (help|assist)',
            r'how may i (help|assist)',
            r'i\'d be happy to',
            r'absolutely',
            r'certainly',
        ]
        
        caller_indicators = [
            r'i need (help|assistance)',
            r'i have a (problem|issue)',
            r'can you (help|fix)',
            r'my account is',
            r'i\'m having (trouble|problems)',
            r'it\'s not working',
            r'i\'m (frustrated|angry|upset)',
            r'this is (unacceptable|ridiculous)',
            r'why (didn\'t|isn\'t)',
            r'when (will|can)',
            r'i want to',
            r'i\'d like to',
            r'help me',
            r'fix this',
            r'i called (because|to)',
            r'my (issue|problem) is',
        ]
        
        speaker_scores = {}
        
        # Analyze each speaker's utterances for indicators
        for utterance in utterances:
            speaker = utterance.get("speaker", 0)
            text = utterance.get("transcript", "").lower()
            
            if speaker not in speaker_scores:
                speaker_scores[speaker] = {"agent": 0, "caller": 0, "utterances": []}
            
            speaker_scores[speaker]["utterances"].append(text)
            
            # Check for agent indicators
            for pattern in agent_indicators:
                if re.search(pattern, text, re.IGNORECASE):
                    speaker_scores[speaker]["agent"] += 1
            
            # Check for caller indicators
            for pattern in caller_indicators:
                if re.search(pattern, text, re.IGNORECASE):
                    speaker_scores[speaker]["caller"] += 1
        
        # Determine roles based on scores
        speaker_map = {}
        for speaker, scores in speaker_scores.items():
            agent_score = scores["agent"]
            caller_score = scores["caller"]
            
            if agent_score > caller_score:
                speaker_map[speaker] = "agent"
            elif caller_score > agent_score:
                speaker_map[speaker] = "caller"
            else:
                # Tie-breaker: Analyze utterance characteristics
                utterances_list = scores["utterances"]
                avg_length = sum(len(u) for u in utterances_list) / max(len(utterances_list), 1)
                
                # Agents typically have longer, more structured utterances (scripted responses)
                # Callers typically have shorter, more emotional utterances
                if avg_length > 80:  # Longer average utterance = likely agent
                    speaker_map[speaker] = "agent"
                else:
                    # Check if first utterance is a greeting (agent) or question (caller)
                    if utterances_list:
                        first_utterance = utterances_list[0]
                        if any(ind in first_utterance for ind in ['thank you', 'calling', 'help you', 'name is']):
                            speaker_map[speaker] = "agent"
                        else:
                            speaker_map[speaker] = "caller"
                    else:
                        speaker_map[speaker] = "caller"
        
        # Ensure at least one caller and one agent
        if not any(v == "caller" for v in speaker_map.values()):
            # First speaker defaults to caller if no clear indication
            first_speaker = utterances[0].get("speaker", 0)
            speaker_map[first_speaker] = "caller"
        
        if not any(v == "agent" for v in speaker_map.values()):
            # Second speaker defaults to agent
            speakers = sorted(set(u.get("speaker", 0) for u in utterances))
            for speaker in speakers:
                if speaker not in speaker_map or speaker_map[speaker] != "caller":
                    speaker_map[speaker] = "agent"
                    break
        
        logger.info(f"Speaker identification: {speaker_map}")
        return speaker_map
    
    def _calculate_adaptive_voice_baselines(self, sentiment_data: List[Dict], speaker_map: Dict[int, str]) -> Dict[str, Dict]:
        """
        Phase 2: Calculate adaptive baseline voice characteristics per session (first 30s window).
        This prevents mislabeling intense-sounding agents as angry by establishing baselines
        from the beginning of the conversation when emotions are typically neutral.
        """
        baselines = {}

        for speaker_label in set(speaker_map.values()):
            # Get all sentiment data for this speaker
            speaker_sentiments = [s for s in sentiment_data if s.get("speaker") == speaker_label]

            if not speaker_sentiments:
                continue

            # Phase 2: Only use first 30 seconds of conversation for baseline
            # This captures natural voice characteristics before emotions escalate
            baseline_window_sentiments = []
            cumulative_time = 0.0
            max_baseline_time = 30.0  # 30 second window

            # Sort by start time to ensure chronological order
            speaker_sentiments.sort(key=lambda x: x.get("start", 0))

            for sent in speaker_sentiments:
                start_time = sent.get("start", 0)
                if start_time <= max_baseline_time:
                    baseline_window_sentiments.append(sent)
                else:
                    break  # Stop when we exceed the baseline window

            if not baseline_window_sentiments:
                # Fallback to first utterance if no utterances in first 30s
                baseline_window_sentiments = speaker_sentiments[:1]

            # Calculate baseline from the early conversation window
            sentiment_scores = []
            for sent in baseline_window_sentiments:
                sentiment_info = sent.get("sentiment", {})
                if isinstance(sentiment_info, dict):
                    sentiment_scores.append(sentiment_info)

            if sentiment_scores:
                # Determine baseline characteristics from early conversation
                positive_count = sum(1 for s in sentiment_scores if s.get("sentiment") == "positive")
                negative_count = sum(1 for s in sentiment_scores if s.get("sentiment") == "negative")
                neutral_count = sum(1 for s in sentiment_scores if s.get("sentiment") == "neutral")

                total = len(sentiment_scores)
                total_conversation_segments = len(speaker_sentiments)

                baselines[speaker_label] = {
                    "baseline_positive_ratio": positive_count / total if total > 0 else 0,
                    "baseline_negative_ratio": negative_count / total if total > 0 else 0,
                    "baseline_neutral_ratio": neutral_count / total if total > 0 else 0,
                    "baseline_window_seconds": max_baseline_time,
                    "baseline_segments_used": total,
                    "total_conversation_segments": total_conversation_segments,
                    "baseline_method": "adaptive_30s_window",
                    "note": "Phase 2: Adaptive baseline from first 30s prevents mislabeling intense-sounding agents as angry. Compare current sentiment against this early-conversation baseline to detect actual emotional changes."
                }

                logger.info(f"Adaptive baseline for {speaker_label}: {total} segments in first {max_baseline_time}s, "
                           f"negative_ratio={baselines[speaker_label]['baseline_negative_ratio']:.2f}")

        return baselines

