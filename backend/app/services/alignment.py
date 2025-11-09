"""
Forced Alignment Service for Precise Word-Level Timestamps
Phase 2: Accuracy & Intelligence Expansion
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import torch
from faster_whisper import WhisperModel
import io
import aiohttp
from app.config import settings

logger = logging.getLogger(__name__)


class AlignmentService:
    """
    Service for forced alignment to get precise word-level timestamps.
    Phase 2: Eliminates tone mismatch errors caused by misaligned sentiment.
    """

    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Alignment service initialized with device: {self.device}")

    async def align_transcript(
        self,
        audio_url: str,
        deepgram_transcript: str,
        deepgram_segments: List[Dict[str, Any]],
        timeout_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform forced alignment to get precise word-level timestamps.
        Uses faster-whisper with alignment for better precision than Deepgram alone.
        Includes timeout handling for long audio files.
        """
        # Use configured timeout or default
        if timeout_seconds is None:
            timeout_seconds = settings.alignment_timeout_seconds

        # Check if alignment is enabled
        if not settings.enable_alignment:
            logger.info("Alignment disabled in configuration, using Deepgram timestamps")
            return self._fallback_to_deepgram(deepgram_segments)

        try:
            # Check audio duration from Deepgram segments to decide alignment strategy
            total_duration = 0
            if deepgram_segments:
                # Get the end time of the last segment
                last_segment = max(deepgram_segments, key=lambda x: x.get('end', 0))
                total_duration = last_segment.get('end', 0)

            logger.info(f"Starting alignment for {total_duration:.1f}s audio file")

            # For very long audio files, skip word-level alignment
            if total_duration > settings.alignment_max_duration_seconds:
                logger.info(f"Audio too long ({total_duration:.1f}s > {settings.alignment_max_duration_seconds}s), skipping word-level alignment")
                return self._fallback_to_deepgram(deepgram_segments)

            # Download audio file with timeout
            download_task = self._download_audio(audio_url)
            audio_data = await asyncio.wait_for(download_task, timeout=30)  # 30 second download timeout
            if not audio_data:
                logger.warning("Could not download audio for alignment, using Deepgram timestamps")
                return self._fallback_to_deepgram(deepgram_segments)

            # Load model on first use (lazy loading)
            if self.model is None:
                logger.info("Loading Whisper model for alignment...")
                self.model = WhisperModel("base", device=self.device, compute_type="int8")
                logger.info("Whisper model loaded successfully")

            # Create alignment task with timeout
            async def perform_alignment():
                logger.info("Starting transcription with word-level timestamps...")
                segments, info = self.model.transcribe(
                    io.BytesIO(audio_data),
                    language="en",
                    vad_filter=True,
                    vad_parameters=dict(threshold=0.5, min_speech_duration_ms=250),
                    word_timestamps=True,  # Enable word-level timestamps
                    initial_prompt=deepgram_transcript[:200]  # Use Deepgram transcript as hint
                )
                logger.info("Transcription completed, processing segments...")
                return segments, info

            # Run alignment with timeout
            try:
                segments, info = await asyncio.wait_for(perform_alignment(), timeout=timeout_seconds)
                logger.info(f"Alignment completed with {len(list(segments))} segments")
            except asyncio.TimeoutError:
                logger.warning(f"Alignment timed out after {timeout_seconds}s, using Deepgram timestamps")
                return self._fallback_to_deepgram(deepgram_segments)

            # Extract aligned segments
            aligned_segments = []
            word_count = 0
            for segment in segments:
                for word in segment.words or []:
                    aligned_segments.append({
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "confidence": getattr(word, 'probability', 0.8)
                    })
                    word_count += 1

            logger.info(f"Extracted {word_count} words from alignment")

            # Merge with Deepgram speaker diarization
            enhanced_segments = self._merge_with_diarization(
                aligned_segments,
                deepgram_segments
            )

            return {
                "aligned_segments": enhanced_segments,
                "alignment_confidence": info.language_probability if hasattr(info, 'language_probability') else 0.8,
                "method": "faster_whisper_alignment",
                "word_count": word_count
            }

        except Exception as e:
            logger.error(f"Alignment failed: {e}, falling back to Deepgram timestamps")
            return self._fallback_to_deepgram(deepgram_segments)

    async def _download_audio(self, audio_url: str) -> Optional[bytes]:
        """Download audio file from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"Failed to download audio: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return None

    def _merge_with_diarization(
        self,
        aligned_words: List[Dict[str, Any]],
        deepgram_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge word-level alignment with speaker diarization from Deepgram.
        This gives us precise word timestamps with speaker identification.
        """
        enhanced_segments = []

        # Group Deepgram segments by speaker
        speaker_segments = {}
        for dg_segment in deepgram_segments:
            speaker = dg_segment.get("speaker", "unknown")
            if speaker not in speaker_segments:
                speaker_segments[speaker] = []
            speaker_segments[speaker].append(dg_segment)

        # For each word, find which speaker segment it belongs to
        for word_info in aligned_words:
            word_start = word_info["start"]
            word_end = word_info["end"]
            word_text = word_info["word"]

            # Find overlapping speaker segment
            best_speaker = "unknown"
            best_overlap = 0

            for speaker, segments in speaker_segments.items():
                for segment in segments:
                    seg_start = segment.get("start", 0)
                    seg_end = segment.get("end", 0)

                    # Calculate overlap
                    overlap_start = max(word_start, seg_start)
                    overlap_end = min(word_end, seg_end)
                    overlap_duration = max(0, overlap_end - overlap_start)

                    if overlap_duration > best_overlap:
                        best_overlap = overlap_duration
                        best_speaker = speaker

            enhanced_segments.append({
                "word": word_text,
                "start": word_start,
                "end": word_end,
                "speaker": best_speaker,
                "confidence": word_info.get("confidence", 0.8),
                "source": "aligned"
            })

        # Merge consecutive words from same speaker into utterances
        merged_utterances = self._merge_words_to_utterances(enhanced_segments)

        return merged_utterances

    def _merge_words_to_utterances(self, word_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge consecutive words from the same speaker into utterance segments.
        This provides better alignment with Deepgram's utterance-based sentiment.
        """
        if not word_segments:
            return []

        utterances = []
        current_utterance = {
            "speaker": word_segments[0]["speaker"],
            "words": [word_segments[0]],
            "start": word_segments[0]["start"],
            "end": word_segments[0]["end"],
            "text": word_segments[0]["word"]
        }

        for word in word_segments[1:]:
            # If same speaker and close in time (less than 0.5s gap), merge
            if (word["speaker"] == current_utterance["speaker"] and
                word["start"] - current_utterance["end"] < 0.5):

                current_utterance["words"].append(word)
                current_utterance["end"] = word["end"]
                current_utterance["text"] += " " + word["word"]
            else:
                # Finalize current utterance
                utterances.append({
                    "speaker": current_utterance["speaker"],
                    "text": current_utterance["text"],
                    "start": current_utterance["start"],
                    "end": current_utterance["end"],
                    "word_count": len(current_utterance["words"]),
                    "avg_confidence": np.mean([w["confidence"] for w in current_utterance["words"]])
                })

                # Start new utterance
                current_utterance = {
                    "speaker": word["speaker"],
                    "words": [word],
                    "start": word["start"],
                    "end": word["end"],
                    "text": word["word"]
                }

        # Add final utterance
        if current_utterance["words"]:
            utterances.append({
                "speaker": current_utterance["speaker"],
                "text": current_utterance["text"],
                "start": current_utterance["start"],
                "end": current_utterance["end"],
                "word_count": len(current_utterance["words"]),
                "avg_confidence": np.mean([w["confidence"] for w in current_utterance["words"]])
            })

        return utterances

    def _fallback_to_deepgram(self, deepgram_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback to Deepgram segments when alignment fails"""
        return {
            "aligned_segments": deepgram_segments,
            "alignment_confidence": 0.5,
            "method": "deepgram_fallback",
            "note": "Forced alignment failed, using Deepgram timestamps"
        }
