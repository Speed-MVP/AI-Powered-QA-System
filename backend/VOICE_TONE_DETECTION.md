# Voice-Based Tone Detection

## Overview

This document explains how tone detection works in the AI-Powered QA System, specifically focusing on voice-based analysis vs text-based analysis.

## Current Implementation

### 1. Speaker Diarization (Voice-Based) ✅

**YES - Deepgram uses voice-based speaker diarization.**

- **How it works**: Deepgram analyzes voice characteristics (pitch, spectral features, timbre, frequency patterns) to distinguish between different speakers
- **Not text-based**: Speaker separation is NOT based on text content or diacritics - it's purely audio analysis
- **Configuration**: `diarize: "true"` parameter in Deepgram API
- **Result**: Each utterance is labeled with a speaker ID (0, 1, etc.) based on voice characteristics

### 2. Tone Detection (Hybrid: Voice + Text) ✅

**NEW: Now uses voice-based sentiment analysis + text-based analysis**

#### Voice-Based Analysis (Primary Method)
- **Source**: Deepgram's sentiment analysis (`sentiment: "true"` parameter)
- **What it analyzes**: Audio characteristics including:
  - **Pitch variations**: High pitch = stress/anger, Low pitch = calm/sad
  - **Intensity/Volume**: High volume = frustration/anger, Low volume = disappointment
  - **Speaking rate**: Fast = urgency/anger, Slow = thoughtfulness/confusion
  - **Prosody**: Intonation patterns, stress, rhythm
- **Accuracy**: More accurate for detecting true emotions (voice doesn't lie)
- **Output**: Sentiment scores per utterance from Deepgram

#### Text-Based Analysis (Secondary/Validation Method)
- **Source**: Gemini LLM analyzing transcript text
- **What it analyzes**: Words, phrases, language patterns
- **Purpose**: Provides context and validates voice-based analysis
- **Fallback**: Used when voice-based analysis is not available

#### Combined Approach
1. **Primary**: Use voice-based sentiment from Deepgram (analyzes audio characteristics)
2. **Validate**: Cross-reference with text analysis for consistency
3. **Determine**: Final emotion based on both voice and text signals

## Deepgram Configuration

```python
params = {
    "model": "nova-2",
    "diarize": "true",        # Voice-based speaker separation
    "punctuate": "true",
    "utterances": "true",
    "sentiment": "true",      # Voice-based sentiment analysis
    "topics": "false",
    "intents": "false"
}
```

## Data Flow

```
1. Audio File Upload
   ↓
2. Deepgram Transcription
   ├─ Transcribes audio to text
   ├─ Separates speakers by voice (diarization)
   └─ Analyzes sentiment from voice (sentiment analysis)
   ↓
3. Save Transcript
   ├─ transcript_text: Full text
   ├─ diarized_segments: Speaker-separated utterances
   └─ sentiment_analysis: Voice-based sentiment scores
   ↓
4. Gemini Evaluation
   ├─ Receives transcript text
   ├─ Receives voice-based sentiment analysis
   ├─ Combines voice + text analysis
   └─ Determines customer tone/emotion
   ↓
5. Save Evaluation
   └─ customer_tone: Final emotion determination
```

## Voice Characteristics → Emotions Mapping

| Voice Characteristic | Pattern | Emotion Indication |
|---------------------|---------|-------------------|
| **Pitch** | High | Stress, Anger, Frustration |
| **Pitch** | Low | Calm, Sadness, Disappointment |
| **Intensity** | High | Frustration, Anger, Urgency |
| **Intensity** | Low | Disappointment, Resignation |
| **Speaking Rate** | Fast | Urgency, Anger, Frustration |
| **Speaking Rate** | Slow | Thoughtfulness, Confusion, Calm |
| **Prosody** | Varied | Engagement, Interest |
| **Prosody** | Flat | Boredom, Disinterest |

## Sentiment Scores

Deepgram provides sentiment scores per utterance:
- **Positive**: Satisfaction, Happiness
- **Negative**: Anger, Frustration, Disappointment
- **Neutral**: Calm, Neutral

These scores are combined with intensity and speaking rate to determine specific emotions.

## Example

**Customer says**: "This is unacceptable!" (text)
- **Voice analysis**: High pitch + High intensity + Fast rate = **Anger/Frustration**
- **Text analysis**: "unacceptable" = Negative sentiment
- **Combined**: **Angry/Frustrated** (confirmed by both voice and text)

## Benefits of Voice-Based Analysis

1. **Accuracy**: Voice characteristics don't lie - can detect emotions even when words are neutral
2. **Early Detection**: Can identify frustration before customer explicitly states it
3. **Context**: Provides emotional context that text alone cannot capture
4. **Validation**: Cross-references with text to ensure accurate emotion detection

## Limitations

1. **Audio Quality**: Requires clear audio for accurate analysis
2. **Language**: Some languages may have different prosodic patterns
3. **Cultural Differences**: Voice patterns may vary by culture
4. **Background Noise**: Can affect sentiment analysis accuracy

## Future Enhancements

1. **Real-time Analysis**: Analyze tone during live calls
2. **Advanced Metrics**: Add more voice characteristics (jitter, shimmer, etc.)
3. **Emotion Timeline**: Track emotion changes throughout the call in real-time
4. **Agent Coaching**: Provide real-time feedback to agents based on customer tone

## References

- Deepgram API Documentation: https://developers.deepgram.com/
- Speaker Diarization: Voice-based speaker separation
- Sentiment Analysis: Voice-based emotion detection
- Prosody: Intonation, stress, and rhythm in speech

