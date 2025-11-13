# Complete Evaluation Process Documentation

## Overview

This document provides a comprehensive explanation of how audio recordings are processed and evaluated in the AI-Powered QA System. The system uses advanced voice analysis, context-based speaker identification, and AI-powered evaluation to detect not just what agents say, but how they say it.

---

## Table of Contents

1. [Complete Process Flow](#complete-process-flow)
2. [Step 1: Audio Transcription & Speaker Diarization](#step-1-audio-transcription--speaker-diarization)
3. [Step 2: Context-Based Speaker Identification](#step-2-context-based-speaker-identification)
4. [Step 3: Voice-Based Sentiment Analysis](#step-3-voice-based-sentiment-analysis)
5. [Step 4: Voice Baseline Calculation](#step-4-voice-baseline-calculation)
6. [Step 5: LLM Evaluation with Tone Analysis](#step-5-llm-evaluation-with-tone-analysis)
7. [Step 6: Scoring & Violation Detection](#step-6-scoring--violation-detection)
8. [Key Features](#key-features)
9. [Technical Details](#technical-details)

---

## Complete Process Flow

```
1. Audio File Upload
   ↓
2. Deepgram Transcription
   ├─ Transcribe audio to text
   ├─ Separate speakers (diarization)
   ├─ Extract voice-based sentiment (pitch, intensity, rate, prosody)
   └─ Generate speaker segments with timestamps
   ↓
3. Context-Based Speaker Identification
   ├─ Analyze conversation patterns
   ├─ Identify agent vs caller based on content (not just order)
   └─ Map speakers to roles (caller/agent)
   ↓
4. Voice Baseline Calculation
   ├─ Calculate baseline voice characteristics per speaker
   ├─ Account for natural voice characteristics
   └─ Distinguish natural voice from emotional responses
   ↓
5. Save Transcript to Database
   ├─ Full transcript text
   ├─ Diarized segments with speaker labels
   ├─ Sentiment analysis (BOTH caller and agent)
   └─ Voice baselines
   ↓
6. Gemini LLM Evaluation
   ├─ Receive transcript text
   ├─ Receive voice-based sentiment (caller + agent)
   ├─ Receive voice baselines
   ├─ Analyze tone mismatches
   ├─ Detect disingenuous behavior
   ├─ Detect keyword gaming
   └─ Evaluate against policy criteria
   ↓
7. Scoring & Violation Detection
   ├─ Calculate category scores
   ├─ Detect policy violations
   ├─ Flag tone mismatches
   └─ Generate feedback
   ↓
8. Save Evaluation Results
   └─ Store scores, violations, and analysis
```

---

## Step 1: Audio Transcription & Speaker Diarization

### Technology: Deepgram API

**Configuration:**
- Model: `nova-2`
- Features enabled:
  - `diarize: true` - Separates speakers by voice characteristics
  - `punctuate: true` - Adds punctuation
  - `utterances: true` - Returns segmented utterances
  - `sentiment: true` - Analyzes voice-based sentiment

**Process:**
1. Audio file is sent to Deepgram API
2. Deepgram analyzes audio characteristics:
   - **Pitch**: Frequency of voice (high/low)
   - **Intensity/Volume**: Loudness of speech
   - **Speaking Rate**: Speed of speech
   - **Prosody**: Intonation patterns, stress, rhythm
   - **Spectral Features**: Voice timbre, frequency patterns

3. Deepgram returns:
   - Full transcript text
   - Segmented utterances with timestamps
   - Speaker IDs (0, 1, 2, etc.) based on voice characteristics
   - Sentiment scores per utterance (positive/negative/neutral)
   - Confidence scores

**Output Example:**
```json
{
  "transcript": "Hello, thank you for calling...",
  "utterances": [
    {
      "speaker": 0,
      "transcript": "Hello, thank you for calling ABC Company.",
      "start": 0.0,
      "end": 3.5,
      "sentiment": {"sentiment": "positive", "score": 0.85}
    },
    {
      "speaker": 1,
      "transcript": "Hi, I need help with my account.",
      "start": 3.5,
      "end": 7.2,
      "sentiment": {"sentiment": "neutral", "score": 0.60}
    }
  ]
}
```

---

## Step 2: Context-Based Speaker Identification

### Problem with Previous Approach

**Old Method:** Assumed first speaker = caller, second speaker = agent
- **Issue:** Not always accurate (agent might answer first, caller might have greeting)
- **Problem:** Could mislabel speakers, leading to incorrect sentiment analysis

### New Method: Context-Based Identification

**How It Works:**
1. Analyzes conversation patterns in each speaker's utterances
2. Uses keyword/phrase matching to identify roles
3. Considers utterance length and structure
4. Falls back to order if no clear pattern

**Agent Indicators:**
- Greetings: "Thank you for calling", "How can I help", "My name is"
- Scripted phrases: "I understand", "I apologize", "Let me help you"
- Questions about account: "Can I have your account number", "What's your name"
- Closing phrases: "Is there anything else", "Have a great day"
- Professional language: "I'll help you with that", "Absolutely", "Certainly"

**Caller Indicators:**
- Asking for help: "I need help with", "I have a problem", "Can you help me"
- Stating issues: "My account is", "I'm having trouble", "It's not working"
- Expressing emotions: "I'm frustrated", "This is unacceptable", "I'm angry"
- Request language: "I want to", "I'd like to", "Help me", "Fix this"

**Scoring System:**
1. Each speaker's utterances are analyzed for agent vs caller indicators
2. Scores are calculated: `agent_score` vs `caller_score`
3. Higher score determines role
4. Tie-breaker: Analyzes average utterance length (agents typically have longer, structured responses)

**Example:**
```
Speaker 0 utterances:
- "Thank you for calling ABC Company"
- "How can I help you today?"
- "I understand your frustration"
- Agent score: 3, Caller score: 0 → Identified as "agent"

Speaker 1 utterances:
- "I need help with my account"
- "I'm having trouble logging in"
- "Can you fix this?"
- Agent score: 0, Caller score: 3 → Identified as "caller"
```

**Benefits:**
- More accurate speaker identification
- Works even if agent answers first
- Handles complex call scenarios
- Reduces mislabeling errors

---

## Step 3: Voice-Based Sentiment Analysis

### What It Analyzes

**Voice Characteristics (from Deepgram):**
1. **Pitch Variations**
   - High pitch = stress, anger, frustration
   - Low pitch = calm, sadness, disappointment
   - Normal pitch = neutral, professional

2. **Intensity/Volume**
   - High volume = frustration, anger, urgency
   - Low volume = disappointment, resignation, calm
   - Normal volume = professional, engaged

3. **Speaking Rate**
   - Fast rate = urgency, anger, frustration
   - Slow rate = thoughtfulness, confusion, calm
   - Normal rate = professional, engaged

4. **Prosody (Intonation Patterns)**
   - Varied prosody = engagement, interest
   - Flat prosody = boredom, disinterest
   - Stressed prosody = emphasis, emotion

### Sentiment Scores

**Deepgram provides sentiment per utterance:**
- **Positive**: Satisfaction, happiness, engagement
- **Negative**: Anger, frustration, disappointment
- **Neutral**: Calm, professional, neutral

**Example:**
```json
{
  "speaker": "caller",
  "sentiment": {"sentiment": "negative", "score": 0.75},
  "text": "This is unacceptable!",
  "start": 45.2,
  "end": 48.5
}
```

### Capturing Both Caller and Agent Sentiment

**Previous Limitation:** Only analyzed caller sentiment
**New Feature:** Analyzes BOTH caller and agent sentiment

**Why This Matters:**
- Detects agent's emotional state
- Identifies tone mismatches (right words, wrong tone)
- Catches disingenuous behavior
- Flags keyword gaming (saying right things with poor delivery)

**Data Structure:**
```json
{
  "sentiment_analysis": [
    {
      "speaker": "caller",
      "sentiment": {"sentiment": "negative", "score": 0.80},
      "text": "I'm really frustrated with this",
      "start": 10.5,
      "end": 13.2
    },
    {
      "speaker": "agent",
      "sentiment": {"sentiment": "neutral", "score": 0.50},
      "text": "I understand your frustration",
      "start": 13.5,
      "end": 16.8
    }
  ]
}
```

---

## Step 4: Voice Baseline Calculation

### Problem: Natural Voice Characteristics

**Issue:** Some people naturally have:
- More intense voices (higher pitch/volume baseline)
- Calmer voices (lower pitch/volume baseline)
- Aggressive-sounding voices (even when calm)
- Soft voices (even when frustrated)

**Problem:** If we only look at absolute values, we might:
- Flag someone with a naturally intense voice as always angry
- Miss someone with a naturally calm voice who is actually frustrated
- Misinterpret natural voice characteristics as emotions

### Solution: Voice Baseline Calculation

**How It Works:**
1. Calculate baseline sentiment ratios for each speaker
2. Determine what's "normal" for that speaker
3. Look for DEVIATIONS from baseline, not absolute values
4. Focus on RELATIVE changes, not absolute characteristics

**Calculation:**
```python
For each speaker:
  - Count positive sentiments: positive_count
  - Count negative sentiments: negative_count
  - Count neutral sentiments: neutral_count
  - Total segments: total
  
  Baseline ratios:
    - baseline_positive_ratio = positive_count / total
    - baseline_negative_ratio = negative_count / total
    - baseline_neutral_ratio = neutral_count / total
```

**Example:**
```
Agent's voice baseline:
  - Positive: 20% (low - agent rarely sounds positive)
  - Negative: 60% (high - agent naturally sounds more intense)
  - Neutral: 20%

Interpretation:
  - If agent says something with negative sentiment, but it's within their 60% baseline → Natural voice
  - If agent says something with negative sentiment, but it's MUCH higher than 60% → Actual frustration
  - If agent says something with positive sentiment, but it's way above 20% → Genuine engagement
```

**Benefits:**
- Accounts for natural voice characteristics
- Reduces false positives (flagging natural voice as emotion)
- More accurate emotion detection
- Better tone mismatch detection

---

## Step 5: LLM Evaluation with Tone Analysis

### Technology: Google Gemini 2.0 Flash

### Input Data

**What Gemini Receives:**
1. **Transcript Text**: Full conversation transcript
2. **Diarized Segments**: Speaker-labeled segments with timestamps
3. **Voice-Based Sentiment**: Sentiment scores for BOTH caller and agent
4. **Voice Baselines**: Baseline characteristics for each speaker
5. **Policy Criteria**: Company-specific evaluation criteria
6. **Rubric Levels**: Scoring rubrics for each category

### Enhanced Prompting

**Key Instructions to Gemini:**

1. **Tone Analysis (Most Important)**
   - Analyze agent's tone, not just their words
   - Compare voice sentiment with text content for EVERY agent utterance
   - Flag tone mismatches as VIOLATIONS
   - Penalize disingenuous behavior heavily

2. **Detecting Disingenuous Behavior**
   - Right keywords + Wrong tone = VIOLATION
   - Scripted responses + Poor delivery = VIOLATION
   - Compliance keywords + Sarcastic tone = VIOLATION
   - Empathetic words + No empathy in voice = VIOLATION

3. **Natural Voice Characteristics**
   - Account for speakers who naturally sound more intense
   - Look for RELATIVE changes in tone, not absolute values
   - Focus on tone DEVIATIONS, not baseline characteristics
   - If agent's voice is consistently intense, that's their natural voice (not a violation)
   - But if agent's tone changes inappropriately, that's a violation

4. **Agent Tone Evaluation**
   - Evaluate agent's tone throughout the entire call
   - Detect patterns: Is agent consistently disengaged? Sarcastic? Dismissive?
   - Flag tone mismatches with specific examples
   - Include tone violations in the violations array

### Tone Mismatch Detection

**How It Works:**
1. For each agent utterance, compare:
   - **Text Content**: What the agent said
   - **Voice Sentiment**: How the agent said it (from Deepgram)

2. Detect mismatches:
   - **Sarcasm**: Positive words with negative/neutral tone
   - **Dismissiveness**: Helpful words with flat/disinterested tone
   - **Frustration**: Professional words with stressed/angry tone
   - **Insincerity**: Empathetic words with neutral/bored tone
   - **Keyword Gaming**: Compliance keywords with inappropriate delivery

3. Flag violations:
   - Tone mismatches are flagged as violations
   - Penalties applied: -15 to -25 points
   - Disingenuous behavior: -20 to -30 points
   - Poor delivery: -10 to -20 points

**Example Detection:**
```
Agent says: "I understand your frustration" (empathetic text)
Agent's voice: Neutral sentiment, score 0.50 (no emotion)
→ MISMATCH DETECTED: Insincerity
→ VIOLATION: "Agent said empathetic words but voice showed no empathy"
→ PENALTY: -20 points for Empathy category
```

### Keyword Gaming Detection

**What It Detects:**
- Agents who say compliance keywords but with poor delivery
- Agents who use scripted responses inappropriately
- Agents who "check the boxes" but show poor attitude
- Agents who technically follow protocol but show unprofessional behavior

**Example:**
```
Agent says: "I apologize for the inconvenience" (compliance keyword)
Agent's voice: Negative sentiment, frustrated tone
→ KEYWORD GAMING DETECTED
→ VIOLATION: "Agent used compliance keyword but showed frustration in delivery"
→ PENALTY: -25 points for Professionalism category
```

### Evaluation Output

**JSON Structure:**
```json
{
  "category_scores": {
    "Empathy": {
      "score": 65,
      "feedback": "Agent said empathetic words but voice showed no empathy. Tone mismatch detected at 13.5s: 'I understand your frustration' was said with neutral tone."
    },
    "Professionalism": {
      "score": 70,
      "feedback": "Agent used compliance keywords but showed frustration in delivery. Keyword gaming detected."
    }
  },
  "customer_tone": {
    "primary_emotion": "frustrated",
    "confidence": 0.85,
    "emotional_journey": [
      {
        "segment": "early",
        "emotion": "frustrated",
        "intensity": "high",
        "evidence": "Customer said 'This is unacceptable' with high negative sentiment"
      }
    ]
  },
  "agent_tone": {
    "primary_characteristics": "dismissive",
    "tone_mismatches": [
      {
        "segment": "middle",
        "text": "I understand your frustration",
        "voice_sentiment": "neutral",
        "text_sentiment": "empathetic",
        "mismatch_type": "insincerity",
        "description": "Agent said empathetic words but voice showed no empathy",
        "severity": "major"
      }
    ],
    "disingenuous_behavior_detected": true,
    "keyword_gaming_detected": true,
    "overall_delivery_quality": "poor"
  },
  "violations": [
    {
      "category_name": "Empathy",
      "type": "tone_mismatch",
      "description": "Agent said empathetic words but voice showed no empathy. Insincere delivery detected.",
      "severity": "major",
      "evidence": "Segment at 13.5s: 'I understand your frustration' said with neutral tone (score: 0.50)"
    }
  ]
}
```

---

## Step 6: Scoring & Violation Detection

### Scoring Method

**Rubric-Based Scoring:**
1. Each category has rubric levels (Excellent, Good, Average, Poor, Unacceptable)
2. Agent's performance is matched to the appropriate rubric level
3. Score is assigned within the level's range
4. Tone mismatches and disingenuous behavior lower the score

**Penalty System:**
- Tone mismatches: -15 to -25 points
- Disingenuous behavior: -20 to -30 points
- Poor delivery: -10 to -20 points
- Policy violations: -20 to -30 points
- Unprofessional behavior: -15 to -25 points
- Multiple violations: Penalties compound (scores can go below 40)

### Violation Detection

**Types of Violations:**
1. **Tone Mismatch**: Right words, wrong tone
2. **Disingenuous Behavior**: Insincere delivery
3. **Keyword Gaming**: Using keywords without proper delivery
4. **Poor Delivery**: Rushed, monotone, dismissive
5. **Policy Violations**: Not following company policies
6. **Unprofessional Behavior**: Unprofessional attitude or language

**Severity Levels:**
- **Critical**: Major policy violation, severe tone mismatch
- **Major**: Significant issue, repeated tone mismatches
- **Minor**: Minor issue, occasional tone mismatch

---

## Key Features

### 1. Context-Based Speaker Identification
- Analyzes conversation patterns, not just order
- More accurate speaker labeling
- Handles complex call scenarios

### 2. Voice Baseline Calculation
- Accounts for natural voice characteristics
- Distinguishes natural voice from emotions
- Reduces false positives

### 3. Agent Sentiment Analysis
- Analyzes BOTH caller and agent sentiment
- Detects agent's emotional state
- Identifies tone mismatches

### 4. Tone Mismatch Detection
- Compares voice sentiment with text content
- Flags disingenuous behavior
- Detects keyword gaming

### 5. Enhanced LLM Evaluation
- Gemini analyzes tone, not just words
- Detects patterns of disengagement
- Flags insincere behavior

### 6. Comprehensive Violation Detection
- Tone mismatches
- Disingenuous behavior
- Keyword gaming
- Poor delivery
- Policy violations

---

## Technical Details

### Deepgram API Configuration

```python
params = {
    "model": "nova-2",
    "diarize": "true",
    "punctuate": "true",
    "utterances": "true",
    "sentiment": "true",
    "topics": "false",
    "intents": "false"
}
```

### Speaker Identification Algorithm

```python
def _identify_speakers_by_context(utterances):
    # 1. Analyze each speaker's utterances for indicators
    # 2. Score each speaker (agent_score vs caller_score)
    # 3. Determine role based on higher score
    # 4. Tie-breaker: Analyze utterance length/structure
    # 5. Ensure at least one caller and one agent
    return speaker_map
```

### Voice Baseline Calculation

```python
def _calculate_voice_baselines(sentiment_data, speaker_map):
    # 1. Group sentiments by speaker
    # 2. Calculate sentiment ratios (positive/negative/neutral)
    # 3. Store baseline characteristics
    # 4. Return baselines for LLM analysis
    return baselines
```

### Gemini Prompt Structure

1. **Evaluation Guidelines**: Strict, unbiased, critical evaluation
2. **Tone Analysis Instructions**: How to detect tone mismatches
3. **Natural Voice Characteristics**: How to account for baselines
4. **Agent Tone Evaluation**: How to analyze agent's tone
5. **Violation Detection**: How to flag violations
6. **Scoring Guidelines**: How to assign scores and penalties

---

## Summary

The evaluation process now:

1. **Identifies speakers accurately** using context-based analysis
2. **Analyzes both caller and agent sentiment** for comprehensive tone analysis
3. **Accounts for natural voice characteristics** using baseline calculations
4. **Detects tone mismatches** by comparing voice sentiment with text content
5. **Flags disingenuous behavior** including keyword gaming and insincere delivery
6. **Provides comprehensive feedback** with specific examples and evidence

This ensures that agents are evaluated not just on what they say, but on how they say it, preventing "gaming the system" through keyword usage without proper delivery.

---

## References

- Deepgram API Documentation: https://developers.deepgram.com/
- Google Gemini API Documentation: https://ai.google.dev/
- Voice-Based Sentiment Analysis: Analyzes pitch, intensity, speaking rate, prosody
- Speaker Diarization: Voice-based speaker separation
- Tone Analysis: Comparison of voice sentiment with text content










