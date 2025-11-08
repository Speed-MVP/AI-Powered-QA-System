import aiohttp
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class DeepgramService:
    def __init__(self):
        self.api_key = settings.deepgram_api_key
        self.base_url = "https://api.deepgram.com/v1/listen"
    
    async def transcribe(self, file_url: str):
        """Transcribe audio with diarization"""
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
        
        async with aiohttp.ClientSession() as session:
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
                
                # Map speaker numbers to labels (caller/agent)
                # First speaker is typically the caller, second is the agent
                speaker_map = {}
                speaker_labels = ["caller", "agent"]  # Default labels
                
                # Determine which speaker speaks first (usually the caller)
                if utterances:
                    first_speaker = utterances[0].get("speaker", 0)
                    # Count total speaking time per speaker to determine roles
                    speaker_times = {}
                    for utterance in utterances:
                        speaker = utterance.get("speaker", 0)
                        duration = utterance.get("end", 0) - utterance.get("start", 0)
                        speaker_times[speaker] = speaker_times.get(speaker, 0) + duration
                    
                    # The speaker who speaks first is typically the caller
                    # If there are multiple speakers, label them accordingly
                    speakers = sorted(set(utterance.get("speaker", 0) for utterance in utterances))
                    for idx, speaker_num in enumerate(speakers):
                        if speaker_num == first_speaker:
                            speaker_map[speaker_num] = "caller"
                        else:
                            # Additional speakers are agents
                            speaker_map[speaker_num] = f"agent" if idx == 1 else f"agent_{idx}"
                
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
                # Deepgram provides sentiment scores per utterance when sentiment: true
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
                
                return {
                    "transcript": transcript,
                    "diarized_segments": diarized_segments,
                    "confidence": confidence,
                    "sentiment_analysis": sentiment_data  # Voice-based sentiment per utterance
                }

