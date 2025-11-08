import aiohttp
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AssemblyAIService:
    def __init__(self):
        self.api_key = settings.assemblyai_api_key
        self.base_url = "https://api.assemblyai.com/v2"
    
    async def diarize(self, file_url: str):
        """Diarize audio file (separate agent from customer)"""
        if not self.api_key:
            logger.warning("AssemblyAI API key not set, skipping diarization")
            return None
        
        headers = {
            "authorization": self.api_key,
            "content-type": "application/json"
        }
        
        # Submit transcription with speaker diarization
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/transcript",
                json={
                    "audio_url": file_url,
                    "speaker_labels": True
                },
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"AssemblyAI error: {response.status} - {error_text}")
                
                transcript_data = await response.json()
                transcript_id = transcript_data.get("id")
                
                # Poll for completion
                while True:
                    async with session.get(
                        f"{self.base_url}/transcript/{transcript_id}",
                        headers=headers
                    ) as status_response:
                        status_data = await status_response.json()
                        status = status_data.get("status")
                        
                        if status == "completed":
                            # Extract speaker segments
                            utterances = status_data.get("utterances", [])
                            diarized_segments = []
                            
                            for utterance in utterances:
                                speaker = utterance.get("speaker", "A")
                                start = utterance.get("start", 0)
                                end = utterance.get("end", 0)
                                text = utterance.get("text", "")
                                
                                diarized_segments.append({
                                    "speaker": speaker,
                                    "text": text,
                                    "start": start,
                                    "end": end
                                })
                            
                            return {
                                "diarized_segments": diarized_segments,
                                "transcript": status_data.get("text", "")
                            }
                        
                        elif status == "error":
                            raise Exception(f"AssemblyAI transcription failed: {status_data.get('error')}")
                        
                        # Wait before polling again
                        import asyncio
                        await asyncio.sleep(2)

