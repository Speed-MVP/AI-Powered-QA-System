from app.config import settings
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.evaluation_criteria import EvaluationCriteria
from typing import Dict, Any, Optional, List
import logging
import json

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Gemini service will not work.")


class GeminiService:
    def __init__(self):
        if not GEMINI_AVAILABLE:
            raise Exception("google-generativeai package not installed")
        
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            self.api_key = settings.gemini_api_key
        else:
            self.model = None
            self.api_key = None
    
    async def evaluate(self, transcript_text: str, policy_template_id: str, sentiment_analysis: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Evaluate transcript using Gemini LLM"""
        if not self.model:
            raise Exception("Gemini API key not configured")
        
        db = SessionLocal()
        try:
            # Get evaluation criteria for template
            # Load criteria with rubric levels
            from sqlalchemy.orm import joinedload
            criteria = db.query(EvaluationCriteria).options(
                joinedload(EvaluationCriteria.rubric_levels)
            ).filter(
                EvaluationCriteria.policy_template_id == policy_template_id
            ).all()
            
            if not criteria:
                raise Exception(f"No evaluation criteria found for template {policy_template_id}")
            
            # Build prompt
            prompt = self._build_prompt(transcript_text, criteria, sentiment_analysis)
            
            # Call Gemini
            response = self.model.generate_content(prompt)
            
            # Parse response
            response_text = response.text
            
            # Try to extract JSON from response
            try:
                # Look for JSON block in markdown format
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                evaluation = json.loads(response_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract structured data
                logger.warning("Failed to parse JSON response, attempting fallback parsing")
                evaluation = self._parse_fallback_response(response_text, criteria)
            
            # Log received categories for debugging
            received_categories = list(evaluation.get("category_scores", {}).keys())
            expected_categories = [c.category_name for c in criteria]
            logger.info(f"LLM evaluation completed. Expected categories: {expected_categories}, Received categories: {received_categories}")
            
            # Check for category mismatches
            missing_categories = set(expected_categories) - set(received_categories)
            extra_categories = set(received_categories) - set(expected_categories)
            
            if missing_categories:
                logger.warning(f"LLM did not provide scores for categories: {missing_categories}")
            if extra_categories:
                logger.warning(f"LLM provided scores for unexpected categories (will be filtered): {extra_categories}")
            
            return evaluation
        
        finally:
            db.close()
    
    def _build_prompt(self, transcript: str, criteria: list, sentiment_analysis: Optional[List[Dict[str, Any]]] = None) -> str:
        """Build LLM prompt with rubric-based evaluation"""
        criteria_text_parts = []
        
        for c in criteria:
            # Build rubric levels section
            rubric_section = ""
            if c.rubric_levels and len(c.rubric_levels) > 0:
                # Sort by level_order (1 = highest, 5 = lowest)
                sorted_levels = sorted(c.rubric_levels, key=lambda x: x.level_order)
                rubric_section = "\n  RUBRIC LEVELS (Use these to determine the score):\n"
                for level in sorted_levels:
                    examples_text = f"\n    Examples: {level.examples}" if level.examples else ""
                    rubric_section += f"    - {level.level_name} (Score: {level.min_score}-{level.max_score}): {level.description}{examples_text}\n"
            else:
                # Fallback to default levels if no rubric defined
                rubric_section = "\n  RUBRIC LEVELS (Default - use these to determine the score):\n"
                rubric_section += "    - Excellent (Score: 90-100): Exceeds all expectations, perfect execution\n"
                rubric_section += "    - Good (Score: 75-89): Meets all requirements, minor room for improvement\n"
                rubric_section += "    - Average (Score: 60-74): Meets basic requirements but has noticeable issues\n"
                rubric_section += "    - Poor (Score: 40-59): Significant problems, major policy violations\n"
                rubric_section += "    - Unacceptable (Score: 0-39): Complete failure, severe violations\n"
            
            criteria_text_parts.append(
                f"- {c.category_name} (Weight: {c.weight}%, Passing: {c.passing_score}/100)\n"
                f"  Evaluation Prompt: {c.evaluation_prompt}"
                f"{rubric_section}"
            )
        
        criteria_text = "\n\n".join(criteria_text_parts)
        
        # Build criteria list with names for reference (show with quotes for clarity)
        criteria_names = [c.category_name for c in criteria]
        criteria_list_text = ", ".join([f'"{name}"' for name in criteria_names])
        criteria_list_bullet = "\n".join([f"   - \"{name}\"" for name in criteria_names])
        
        prompt = f"""You are a STRICT, UNBIASED, and CRITICAL quality assurance evaluator. Your job is to evaluate customer service calls with ZERO tolerance for poor performance, unprofessional behavior, or policy violations. Be BRUTALLY HONEST and STRAIGHT TO THE POINT.

ALLOWED CATEGORIES (YOU MUST USE ONLY THESE):
{criteria_list_bullet}

YOU CANNOT CREATE NEW CATEGORIES. YOU CANNOT USE CATEGORY NAMES THAT ARE NOT IN THE LIST ABOVE.

EVALUATION GUIDELINES:
1. BE STRICT: Default to lower scores unless excellence is demonstrated. Mediocre performance deserves LOW scores.
2. NO BIAS: Do NOT be lenient or forgiving. Do NOT give benefit of the doubt. If something is wrong, score it LOW.
3. BE BLUNT: Don't sugarcoat feedback. State violations clearly and directly.
4. ZERO TOLERANCE: Any policy violation, unprofessional behavior, or lack of empathy should result in SIGNIFICANT score deductions.
5. PERFECTIONIST STANDARD: A score of 90+ requires EXCELLENCE. 80+ requires very good performance. 70+ is acceptable but not great. Below 70 is poor.
6. MULTIPLE VIOLATIONS = MULTIPLE PENALTIES: Each violation should result in substantial score reduction. Multiple violations compound the penalty.

CUSTOMER TONE ANALYSIS (VOICE-BASED + TEXT-BASED):
- PRIMARY METHOD: Use voice-based sentiment analysis when available (analyzes pitch, intensity, speaking rate, prosody)
- SECONDARY METHOD: Analyze text content for emotional indicators (words, phrases, language patterns)
- COMBINE BOTH: Voice characteristics provide accurate emotion detection; text provides context and validation

VOICE-BASED ANALYSIS (When available):
- Analyze sentiment scores from voice analysis (provided below)
- Voice characteristics indicate: pitch variations (high = stress/anger, low = calm/sad), intensity/volume (high = frustration, low = disappointment), speaking rate (fast = urgency/anger, slow = thoughtfulness/confusion)
- Match voice sentiment to emotions: positive sentiment + high intensity = satisfaction/happiness; negative sentiment + high intensity = anger/frustration; negative sentiment + low intensity = disappointment/sadness

TEXT-BASED ANALYSIS (Fallback/Validation):
- Identify emotional indicators in customer's words: frustrated, angry, satisfied, neutral, happy, disappointed, confused, calm
- Track emotional journey: How did the customer's emotion change from early to middle to late in the call?
- Provide evidence: Quote specific statements that indicate the emotion
- Assess intensity: high, medium, or low for each emotion

FINAL TONE DETERMINATION:
- PRIMARY: Use voice-based sentiment when available (more accurate for detecting true emotions)
- VALIDATE: Cross-reference with text analysis for consistency
- IDENTIFY: Primary emotion: frustrated, angry, satisfied, neutral, happy, disappointed, confused, calm
- This helps evaluate how well the agent handled the customer's emotional state

SCORING METHOD:
- Use the RUBRIC LEVELS defined for each category above to determine the exact score
- Match the agent's performance to the appropriate rubric level based on the description
- Assign a score within the level's range (min_score to max_score)
- Be precise: If performance is at the top of a level, use the higher end of the range. If at the bottom, use the lower end
- If no rubric levels are defined for a category, use the default levels shown above

PENALTY GUIDELINES (Apply based on relevant categories):
- Policy violations: Apply significant penalties (-20 to -30 points) based on the category
- Unprofessional behavior: Apply penalties (-15 to -25 points) based on relevant categories
- Multiple violations: Apply MULTIPLE penalties (scores can go below 40)
- Each violation should result in substantial score reduction for the relevant category

Evaluate this customer service call transcript based on the following criteria:

{criteria_text}

TRANSCRIPT:
{transcript}

{self._format_sentiment_analysis(sentiment_analysis) if sentiment_analysis else "VOICE-BASED SENTIMENT ANALYSIS: Not available (using text-based analysis only)"}

Provide evaluation in JSON format with the following structure:
{{
  "category_scores": {{
    "category_name": {{
      "score": 85,
      "feedback": "Blunt, direct feedback. State violations clearly. No sugarcoating."
    }}
  }},
  "resolution_detected": true,
  "resolution_confidence": 0.92,
  "customer_tone": {{
    "primary_emotion": "frustrated|angry|satisfied|neutral|happy|disappointed|confused|calm",
    "confidence": 0.85,
    "description": "Brief description of customer's emotional state throughout the call",
    "emotional_journey": [
      {{
        "segment": "early|middle|late",
        "emotion": "frustrated",
        "intensity": "high|medium|low",
        "evidence": "Specific quotes or behaviors that indicate this emotion"
      }}
    ]
  }},
  "violations": [
    {{
      "category_name": "Exact category name from criteria above",
      "type": "violation_type",
      "description": "Clear, direct description of violation. Be specific and harsh.",
      "severity": "critical|major|minor"
    }}
  ]
}}

CRITICAL INSTRUCTIONS - STRICTLY ENFORCE:
1. CATEGORY RESTRICTIONS (MOST IMPORTANT):
   - You MUST ONLY evaluate and score these EXACT categories: {criteria_list_text}
   - DO NOT create, invent, or add any categories that are not in this list
   - DO NOT use generic category names like "Compliance", "Empathy", "Resolution", "Communication" unless they EXACTLY match a category name from the list above
   - You MUST provide a score for EVERY SINGLE category in the list above - no exceptions
   - If a category seems unrelated, score it based on how well the agent met that category's requirements (read the evaluation_prompt for each category)
   - The category_scores object in your JSON response MUST contain EXACTLY these categories and NO OTHERS

2. CATEGORY NAME MATCHING:
   - Category names must match EXACTLY (case-sensitive, character-for-character)
   - For violations, the "category_name" field MUST be one of the exact category names from the list above
   - If you're unsure about a category name, use the EXACT name as shown in the criteria list

3. SCORING REQUIREMENTS (RUBRIC-BASED):
   - Match the agent's performance to the RUBRIC LEVELS defined for each category
   - If performance matches "Excellent" level description, score in that range
   - If performance matches "Poor" or "Unacceptable" level, score in that range
   - BE HARSH: If the agent shows poor attitude, lacks professionalism, or violates policies, match them to the appropriate LOW level
   - MULTIPLE VIOLATIONS = LOW LEVELS: Don't average out violations. Each violation should place the agent in a lower rubric level
   - NO EXCUSES: Technical issues resolved poorly still deserve low rubric levels
   - BE SPECIFIC: In feedback, cite exact examples from the transcript and reference which rubric level the performance matches

4. JSON STRUCTURE:
   - The "category_scores" object MUST contain EXACTLY these categories: {criteria_list_text}
   - Each category MUST have a "score" (0-100) and "feedback" field
   - Do NOT include any categories that are not in the list above
   - Violations can reference any of the categories from the list above

Remember: You are evaluating professional customer service. Substandard performance deserves substandard scores. Be critical, be strict, be honest. ONLY use the categories provided above."""
        
        return prompt
    
    def _format_sentiment_analysis(self, sentiment_analysis: List[Dict[str, Any]]) -> str:
        """Format sentiment analysis data for prompt"""
        if not sentiment_analysis:
            return "VOICE-BASED SENTIMENT ANALYSIS: Not available (using text-based analysis only)"
        
        # Group by speaker (customer)
        customer_sentiments = [s for s in sentiment_analysis if s.get("speaker") == "caller"]
        
        if not customer_sentiments:
            return "VOICE-BASED SENTIMENT ANALYSIS: No customer sentiment data available (using text-based analysis only)"
        
        formatted = "VOICE-BASED SENTIMENT ANALYSIS (from audio characteristics - pitch, intensity, speaking rate, prosody):\n"
        formatted += "These sentiment scores are derived from voice characteristics, not text content:\n\n"
        for idx, sentiment in enumerate(customer_sentiments[:20]):  # Limit to first 20 for prompt size
            sentiment_score = sentiment.get("sentiment", {})
            start_time = sentiment.get("start", 0)
            text = sentiment.get("text", "")[:100]  # Limit text length
            
            formatted += f"  Segment {idx + 1} (Time: {start_time:.1f}s):\n"
            formatted += f"    Voice Sentiment: {sentiment_score}\n"
            formatted += f"    Text: \"{text}...\"\n\n"
        
        if len(customer_sentiments) > 20:
            formatted += f"  ... and {len(customer_sentiments) - 20} more segments\n"
        
        formatted += "\nUSE THIS VOICE-BASED SENTIMENT AS PRIMARY INDICATOR FOR CUSTOMER TONE. Cross-reference with text for validation."
        
        return formatted
    
    def _parse_fallback_response(self, response_text: str, criteria: list) -> dict:
        """Fallback parser if JSON parsing fails"""
        # Simple fallback - create basic structure
        category_scores = {}
        for criterion in criteria:
            category_scores[criterion.category_name] = {
                "score": 75,  # Default score
                "feedback": "Evaluation completed"
            }
        
        return {
            "category_scores": category_scores,
            "resolution_detected": False,
            "resolution_confidence": 0.5,
            "violations": []
        }

