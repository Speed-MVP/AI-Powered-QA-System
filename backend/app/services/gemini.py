from app.config import settings
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.evaluation_criteria import EvaluationCriteria
from app.models.evaluation import Evaluation
from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Gemini service will not work.")

try:
    from app.services.rag import RAGService
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger.warning("RAG service not available. Policy context will not be retrieved.")

from app.models.human_review import HumanReview, ReviewStatus
from app.models.transcript import Transcript
from app.models.category_score import CategoryScore


class GeminiService:
    def __init__(self):
        if not GEMINI_AVAILABLE:
            raise Exception("google-generativeai package not installed")

        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)

            # List available models first to find correct names (optional, for debugging)
            try:
                available_models = self.list_available_models()
                logger.info(f"Available Gemini models: {available_models}")
            except Exception as e:
                logger.debug(f"Could not list available models (non-critical): {e}")

            # Use gemini-2.5-flash-lite for cost efficiency (cheaper than 2.5-pro)
            try:
                self.pro_model = genai.GenerativeModel('gemini-2.5-flash-lite')
                logger.info("Gemini model initialized successfully with gemini-2.5-flash-lite")
            except Exception as e:
                logger.warning(f"Failed to initialize gemini-2.5-flash-lite: {e}, trying gemini-2.5-flash")
                try:
                    self.pro_model = genai.GenerativeModel('gemini-2.5-flash')
                    logger.info("Gemini model initialized successfully with gemini-2.5-flash")
                except Exception as e2:
                    logger.warning(f"Failed to initialize gemini-2.5-flash: {e2}, trying gemini-flash-latest")
                    try:
                        self.pro_model = genai.GenerativeModel('gemini-flash-latest')
                        logger.info("Gemini model initialized successfully with gemini-flash-latest")
                    except Exception as e3:
                        raise Exception(f"No Gemini model available: {e3}")

            # Use same model for Flash (cost-optimized Flash model)
            self.flash_model = self.pro_model
            logger.info("Using cost-optimized Flash model for all evaluations")

            self.api_key = settings.gemini_api_key
        else:
            self.flash_model = None
            self.pro_model = None
            self.api_key = None

    def list_available_models(self):
        """List available Gemini models for debugging"""
        try:
            models = genai.list_models()
            gemini_models = [model.name for model in models if 'gemini' in model.name.lower()]
            logger.info(f"Available Gemini models: {gemini_models}")
            return gemini_models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def evaluate(self, transcript_text: str, policy_template_id: str, sentiment_analysis: Optional[List[Dict[str, Any]]] = None, rule_results: Optional[Dict[str, Any]] = None, use_hybrid: Optional[bool] = None) -> Dict[str, Any]:
        """
        Evaluate transcript using Gemini LLM with hybrid Flash/Pro deployment.
        Phase 4: Use Flash for fast evaluation, Pro for complex cases.
        Defaults to Pro model if Flash is not available.
        """
        if not self.pro_model:
            raise Exception("Gemini API key not configured")

        # Use configuration setting if not explicitly specified
        if use_hybrid is None:
            use_hybrid = settings.gemini_use_hybrid

        # Always calculate complexity score (needed for metadata even if forcing Pro)
        complexity_score = self._assess_call_complexity(transcript_text, sentiment_analysis, rule_results)

        # Use Flash model for cost efficiency
        if settings.gemini_force_pro:
            model = self.pro_model
            model_name = "Flash model (cost-optimized)"
            logger.info(f"Using Gemini Flash (forced by configuration, complexity: {complexity_score:.2f})")
        else:
            # Phase 4: Choose model based on complexity
            if use_hybrid and complexity_score <= 0.7 and self.flash_model != self.pro_model:
                # Use Flash for simple/routine cases (~70% of calls) - only if Flash is available
                model = self.flash_model
                model_name = "Flash model (cost-optimized)"
                logger.info(f"Using Gemini Flash for evaluation (complexity: {complexity_score:.2f})")
            else:
                # Use Flash for all cases (cost-optimized)
                model = self.pro_model
                model_name = "Flash model (cost-optimized)"
                logger.info(f"Using Gemini Flash for evaluation (complexity: {complexity_score:.2f})")

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

            # COST OPTIMIZATION: Conditionally enable expensive RAG retrieval
            rag_results = None
            if settings.enable_expensive_features and RAG_AVAILABLE:
                try:
                    rag_service = RAGService()
                    rag_results = rag_service.retrieve_relevant_policies(
                        transcript_text=transcript_text,
                        evaluation_criteria=criteria,
                        top_k=3  # Get top 3 most relevant policies
                    )
                    logger.info(f"RAG retrieval completed: {len(rag_results.get('retrieved_policies', []))} policies retrieved using {rag_results.get('method', 'unknown')} method")
                except Exception as e:
                    logger.warning(f"RAG retrieval failed, continuing without policy context: {e}")
                    rag_results = None
            else:
                logger.debug("RAG disabled for cost optimization or service not available")

            # COST OPTIMIZATION: Conditionally enable expensive human review examples
            human_review_examples = []
            if settings.enable_expensive_features:
                human_review_examples = self._retrieve_similar_human_reviews(
                    transcript_text=transcript_text,
                    policy_template_id=policy_template_id,
                    db=db,
                    max_examples=3  # Limit to 3 examples to keep prompt size manageable
                )

            # Build prompt with retrieved policy context, human review examples, and rule engine results
            prompt = self._build_prompt(transcript_text, criteria, sentiment_analysis, rag_results, rule_results, human_review_examples)

            # Phase 4: Call selected model (Flash or Pro)
            if model is None:
                raise Exception("Model not initialized - cannot generate content")
            
            # COST OPTIMIZATION: Enforce deterministic settings with token limits
            generation_config = genai.types.GenerationConfig(
                temperature=0.0,  # Deterministic
                top_p=1.0,        # No sampling randomness
                top_k=None,       # Use default
                candidate_count=1, # Single response
                max_output_tokens=2048,  # COST CONTROL: Limit output tokens
            )

            try:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}")
                raise Exception(f"Failed to generate content from Gemini API: {e}")

            # Parse response
            if not response or not hasattr(response, 'text') or not response.text:
                raise Exception("Empty or invalid response from Gemini API")

            response_text = response.text

            # COST OPTIMIZATION: Store compressed metadata only (not full prompt/response)
            # Use hash for reproducibility verification without storing expensive content
            prompt_hash = hash(prompt) % 1000000
            response_summary = response_text[:500] + "..." if len(response_text) > 500 else response_text
            tokens_used = len(prompt.split()) + len(response_text.split())  # Rough estimate

            raw_llm_response = {
                "model": model_name,
                "timestamp": datetime.utcnow().isoformat(),
                "temperature": generation_config.temperature,
                "top_p": generation_config.top_p,
                "response_length": len(response_text),
                "prompt_hash": prompt_hash,
                "response_summary": response_summary,  # Limited preview for debugging
                "tokens_used": tokens_used,
                "cost_estimate": tokens_used * 0.000002  # Rough Gemini cost estimate ($0.002 per 1000 tokens)
            }

            # COST MONITORING: Log token usage and alert if over threshold
            logger.info(f"Token usage: {tokens_used} tokens, estimated cost: ${raw_llm_response['cost_estimate']:.6f}")

            if raw_llm_response['cost_estimate'] > settings.token_cost_threshold:
                logger.warning(f"High-cost evaluation detected: ${raw_llm_response['cost_estimate']:.6f} exceeds threshold of ${settings.token_cost_threshold:.6f}")
            
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
            
            # Ensure evaluation is a dictionary
            if not isinstance(evaluation, dict):
                logger.error(f"Evaluation is not a dictionary: {type(evaluation)}")
                evaluation = self._parse_fallback_response(response_text, criteria)
            
            # Ensure required fields exist
            if "category_scores" not in evaluation:
                logger.warning("Evaluation missing category_scores, using fallback")
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
            
            # Phase 4: Add hybrid deployment metadata
            evaluation["model_used"] = model_name
            evaluation["complexity_score"] = complexity_score
            # Determine cost tier based on actual model name (Flash model is standard/cost-efficient)
            evaluation["cost_tier"] = "standard"  # Flash model is cost-optimized

            # MVP Evaluation Improvements: Return both parsed evaluation and raw response
            return {
                "evaluation": evaluation,
                "raw_llm_response": raw_llm_response
            }

        finally:
            db.close()
    
    def _retrieve_similar_human_reviews(
        self,
        transcript_text: str,
        policy_template_id: str,
        db: Session,
        max_examples: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar past human-reviewed evaluations for in-context learning.
        Uses keyword-based similarity to find similar transcripts.
        
        Args:
            transcript_text: Current transcript text
            policy_template_id: Policy template ID
            db: Database session
            max_examples: Maximum number of examples to retrieve
            
        Returns:
            List of human review examples with transcript snippets, AI scores, and human scores
        """
        try:
            # Get completed human reviews for the same policy template
            human_reviews = db.query(HumanReview).join(
                Evaluation, HumanReview.evaluation_id == Evaluation.id
            ).filter(
                Evaluation.policy_template_id == policy_template_id,
                HumanReview.review_status == ReviewStatus.completed,
                HumanReview.human_overall_score.isnot(None)  # Only reviews with human scores
            ).order_by(
                HumanReview.updated_at.desc()  # Most recent first
            ).limit(20).all()  # Get more candidates, then filter by similarity
            
            if not human_reviews:
                logger.debug("No human-reviewed evaluations found for in-context learning")
                return []
            
            # Extract keywords from current transcript for similarity matching
            import re
            if RAG_AVAILABLE:
                try:
                    rag_service = RAGService()
                    current_keywords = rag_service._extract_keywords(transcript_text[:3000])
                except Exception:
                    # Fallback to simple keyword extraction
                    words = re.findall(r'\b\w+\b', transcript_text.lower()[:3000])
                    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
                    current_keywords = set([w for w in words if len(w) > 3 and w not in stop_words])[:30]
            else:
                # Simple keyword extraction
                words = re.findall(r'\b\w+\b', transcript_text.lower()[:3000])
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
                current_keywords = set([w for w in words if len(w) > 3 and w not in stop_words])[:30]
            
            # Score each human review by similarity
            scored_reviews = []
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
            
            for review in human_reviews:
                # Get transcript for this review
                evaluation = db.query(Evaluation).filter(Evaluation.id == review.evaluation_id).first()
                if not evaluation:
                    continue
                
                transcript = db.query(Transcript).filter(Transcript.recording_id == evaluation.recording_id).first()
                if not transcript or not transcript.transcript_text:
                    continue
                
                # Extract keywords from past transcript
                past_transcript = transcript.transcript_text[:3000]  # Limit length
                if RAG_AVAILABLE:
                    try:
                        rag_service = RAGService()
                        past_keywords = rag_service._extract_keywords(past_transcript)
                    except Exception:
                        words = re.findall(r'\b\w+\b', past_transcript.lower())
                        past_keywords = set([w for w in words if len(w) > 3 and w not in stop_words])[:30]
                else:
                    words = re.findall(r'\b\w+\b', past_transcript.lower())
                    past_keywords = set([w for w in words if len(w) > 3 and w not in stop_words])[:30]
                
                # Calculate Jaccard similarity
                intersection = len(current_keywords.intersection(past_keywords))
                union = len(current_keywords.union(past_keywords))
                similarity = intersection / union if union > 0 else 0.0
                
                # Get AI category scores
                ai_category_scores = {}
                ai_scores = db.query(CategoryScore).filter(CategoryScore.evaluation_id == evaluation.id).all()
                for score in ai_scores:
                    ai_category_scores[score.category_name] = score.score
                
                # Get human category scores
                human_category_scores = review.human_category_scores or {}
                
                # Calculate score difference (higher difference = more informative example)
                score_difference = abs(evaluation.overall_score - (review.human_overall_score or evaluation.overall_score))
                
                scored_reviews.append({
                    "review": review,
                    "evaluation": evaluation,
                    "transcript": transcript,
                    "similarity": similarity,
                    "score_difference": score_difference,
                    "ai_category_scores": ai_category_scores,
                    "human_category_scores": human_category_scores,
                    "ai_overall_score": evaluation.overall_score,
                    "human_overall_score": review.human_overall_score
                })
            
            # Sort by similarity (descending) and score difference (descending) - prefer similar but informative examples
            scored_reviews.sort(key=lambda x: (x["similarity"], x["score_difference"]), reverse=True)
            
            # Get top examples (filter by minimum similarity threshold)
            min_similarity = 0.1  # At least 10% keyword overlap
            top_examples = [ex for ex in scored_reviews if ex["similarity"] >= min_similarity][:max_examples]
            
            # If we don't have enough examples with similarity, just take the most recent ones
            if len(top_examples) < max_examples:
                top_examples = scored_reviews[:max_examples]
            
            # Format examples
            examples = []
            for example in top_examples:
                transcript_snippet = example["transcript"].transcript_text[:1000]  # First 1000 chars
                
                # Format category scores comparison
                category_comparison = []
                all_categories = set(list(example["ai_category_scores"].keys()) + list(example["human_category_scores"].keys()))
                for category in sorted(all_categories):
                    ai_score = example["ai_category_scores"].get(category, "N/A")
                    human_score = example["human_category_scores"].get(category, "N/A")
                    if ai_score != human_score:
                        category_comparison.append(f"  - {category}: AI={ai_score}, Human={human_score} (CORRECTED)")
                    else:
                        category_comparison.append(f"  - {category}: AI={ai_score}, Human={human_score}")
                
                examples.append({
                    "transcript_snippet": transcript_snippet,
                    "ai_overall_score": example["ai_overall_score"],
                    "human_overall_score": example["human_overall_score"],
                    "category_comparison": "\n".join(category_comparison) if category_comparison else "No category scores available",
                    "ai_feedback": example["review"].ai_recommendation or "No feedback",
                    "similarity": example["similarity"]
                })
            
            logger.info(f"Retrieved {len(examples)} human review examples for in-context learning")
            return examples
            
        except Exception as e:
            logger.warning(f"Failed to retrieve human review examples: {e}")
            return []
    
    def _build_prompt(self, transcript: str, criteria: list, sentiment_analysis: Optional[List[Dict[str, Any]]] = None, rag_results: Optional[Dict[str, Any]] = None, rule_results: Optional[Dict[str, Any]] = None, human_review_examples: Optional[List[Dict[str, Any]]] = None) -> str:
        """Build LLM prompt with rubric-based evaluation - COST OPTIMIZED"""

        # COST OPTIMIZATION: Token budget management
        MAX_PROMPT_TOKENS = 4000  # Conservative limit for cost control
        current_tokens = 0

        def estimate_tokens(text: str) -> int:
            """Rough token estimation (1 token ≈ 4 chars)"""
            return len(text) // 4

        # Compress transcript if too long
        if estimate_tokens(transcript) > 1500:  # Leave room for other content
            transcript = transcript[:6000] + "...[truncated for efficiency]"
            logger.info("Transcript compressed for token efficiency")
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

        # Phase 1: Add RAG-retrieved policy context
        policy_context = ""
        if rag_results and rag_results.get("retrieved_policies"):
            policy_context = "\n\nRELEVANT POLICY CONTEXT (Use this context to better understand the evaluation criteria):\n"
            for i, policy in enumerate(rag_results["retrieved_policies"], 1):
                similarity_score = rag_results.get("similarity_scores", [])
                score = similarity_score[i-1] if i-1 < len(similarity_score) else 0.0
                policy_context += f"\n{i}. {policy['category_name']} (Relevance: {score:.2%}):\n"
                policy_context += f"   {policy['evaluation_prompt']}\n"
                policy_context += f"   Weight: {policy['weight']}%, Passing Score: {policy['passing_score']}/100\n"
            policy_context += "\nNOTE: Use the above policy context to provide more context-aware evaluations. "
            policy_context += "The relevance scores indicate how closely each policy matches the call content.\n"

        # Phase 2: Add rule engine violations (CRITICAL - these are confirmed violations)
        rule_violations_text = ""
        human_examples_text = ""
        if rule_results and rule_results.get("violations"):
            rule_violations_text = "\n\nCRITICAL RULE VIOLATIONS DETECTED (These are confirmed policy breaches - match to appropriate lower rubric levels):\n"
            for i, violation in enumerate(rule_results["violations"], 1):
                rule_violations_text += f"VIOLATION {i}: {violation['rule_name']} ({violation['category']} - {violation['severity'].upper()})\n"
                rule_violations_text += f"  Description: {violation['description']}\n"
                rule_violations_text += f"  Evidence: {'; '.join(violation['evidence'])}\n"
                rule_violations_text += f"  IMPACT: This violation should result in matching to a lower rubric level in the {violation['category']} category.\n\n"

            rule_violations_text += "REMINDER: Rule violations are DETERMINISTIC and CONFIRMED. Match performance to lower rubric levels that reflect these violations.\n"

            # COST OPTIMIZATION: Skip expensive human examples for token efficiency
            # Temporarily disable human examples to save tokens - can be re-enabled when needed
            # if human_review_examples and len(human_review_examples) > 0:
            human_examples_text = "\n\nLEARNING FROM PAST HUMAN EVALUATIONS (Use these examples to understand how humans evaluate calls):\n"
            human_examples_text += "These are real examples of how human reviewers evaluated similar calls. Use them to guide your evaluation.\n\n"
            
            if human_review_examples:
                for i, example in enumerate(human_review_examples, 1):
                    human_examples_text += f"EXAMPLE {i} (Similarity: {example['similarity']:.1%}):\n"
                    human_examples_text += f"TRANSCRIPT SNIPPET:\n{example['transcript_snippet'][:800]}...\n\n"
                    human_examples_text += f"AI EVALUATION:\n  Overall Score: {example['ai_overall_score']}/100\n"
                    human_examples_text += f"  Category Scores:\n{example['category_comparison']}\n\n"
                    human_examples_text += f"HUMAN EVALUATION (GROUND TRUTH):\n  Overall Score: {example['human_overall_score']}/100\n"
                    human_examples_text += f"  Category Scores:\n{example['category_comparison']}\n"
                    if example.get('ai_feedback') and example['ai_feedback'] != "No feedback":
                        human_examples_text += f"  Human Feedback on AI: {example['ai_feedback']}\n"
                    human_examples_text += "\nLESSON: Compare the AI and Human evaluations above. Notice where the AI was correct and where it needed correction. "
                    human_examples_text += "Use these insights to improve your evaluation of the current call.\n\n"
            
            human_examples_text += "IMPORTANT: Use these examples to learn how humans evaluate calls, but remember that each call is unique. "
            human_examples_text += "Don't blindly copy scores - instead, understand the reasoning behind human evaluations and apply similar reasoning to the current call.\n"

        prompt = f"""You are a FAIR, UNBIASED, and BALANCED quality assurance evaluator. Your job is to evaluate customer service calls with realistic expectations, acknowledging that perfect performance is rare and that tone/emotion detection has limitations. Be HONEST but REALISTIC in your assessments.

{policy_context}{rule_violations_text}{human_examples_text}

ALLOWED CATEGORIES (YOU MUST USE ONLY THESE):
{criteria_list_bullet}

YOU CANNOT CREATE NEW CATEGORIES. YOU CANNOT USE CATEGORY NAMES THAT ARE NOT IN THE LIST ABOVE.

EVALUATION GUIDELINES:
1. BE FAIR AND REALISTIC: Evaluate based on what was actually said and done. Don't penalize for minor imperfections or natural voice variations.
2. ACKNOWLEDGE LIMITATIONS: Voice sentiment analysis is not perfect. Some people naturally have different voice characteristics. Only flag clear and obvious tone issues.
3. BE CONSTRUCTIVE: Provide clear feedback, but don't be overly harsh for minor issues.
4. RUBRIC-BASED SCORING: Match performance to the appropriate rubric level. Each rubric level has a score range - assign a score within that range based on where the performance falls.
5. MATCH TO APPROPRIATE LEVEL: If there are issues, match to a lower rubric level that reflects those issues. Don't deduct points - instead, match to the rubric level that best describes the performance.
6. GIVE BENEFIT OF DOUBT: When tone/emotion detection is uncertain, err on the side of leniency rather than assuming the worst.

IMPORTANT: DETECTING TONE AND EMOTION (WITH REALISTIC EXPECTATIONS)
Analyze the AGENT's delivery, but acknowledge that voice sentiment analysis has limitations. Be lenient unless there are CLEAR and OBVIOUS issues:

1. NATURAL VOICE VARIATIONS ARE NORMAL:
   - Some people naturally have monotone voices (this is NOT a violation)
   - Some people naturally sound more intense (this is NOT a violation)
   - Some people naturally sound calmer (this is NOT a violation)
   - Only flag tone issues if they are CLEARLY inappropriate for the context

2. HOW TO EVALUATE TONE (BE LENIENT):
   - Compare AGENT's voice sentiment with their text content, but give benefit of doubt
   - If agent says "I understand your frustration" but voice tone is NEUTRAL → This is ACCEPTABLE (not everyone shows emotion in their voice)
   - If agent says "Let me help you with that" but voice tone is slightly stressed → This is ACCEPTABLE (agents can be busy)
   - Only flag tone mismatches if they are CLEARLY sarcastic, dismissive, or unprofessional
   - Minor variations in tone are NORMAL and should NOT result in lower rubric levels

3. ACCOUNTING FOR NATURAL VOICE CHARACTERISTICS (CRITICAL):
   - ALWAYS consider that voice characteristics vary naturally between people
   - Look for CLEAR DEVIATIONS from baseline, not minor variations
   - If agent's voice is consistently intense even when saying calm things → This is their natural voice (NOT a violation)
   - If agent's voice is consistently calm even when saying empathetic things → This is their natural voice (NOT a violation)
   - Only flag issues if there's a CLEAR pattern of inappropriate tone (e.g., consistently sarcastic when saying positive things)
   - Voice baseline information is provided in sentiment analysis data - USE IT to understand natural variations

4. WHEN TO FLAG TONE ISSUES (ONLY CLEAR CASES):
   - CLEARLY sarcastic tone when saying positive things
   - CLEARLY dismissive or condescending tone
   - CLEARLY frustrated or angry tone when customer is upset
   - OBVIOUS eye-roll tone or sighing (if detectable)
   - If uncertain → DON'T flag it. Err on the side of leniency.

CUSTOMER TONE ANALYSIS (VOICE-BASED + TEXT-BASED):
- PRIMARY METHOD: Use voice-based sentiment analysis when available (analyzes pitch, intensity, speaking rate, prosody)
- SECONDARY METHOD: Analyze text content for emotional indicators (words, phrases, language patterns)
- COMBINE BOTH: Voice characteristics provide accurate emotion detection; text provides context and validation
- Track emotional journey: How did the customer's emotion change from early to middle to late in the call?
- Evaluate how well the agent handled the customer's emotional state
- If customer was frustrated and agent made it worse → MAJOR VIOLATION

AGENT TONE ANALYSIS (BE REALISTIC AND LENIENT):
- Analyze agent's voice sentiment throughout the call, but acknowledge limitations
- Only flag CLEAR and OBVIOUS tone mismatches, not minor variations
- Consider that natural voice characteristics vary - don't match to lower rubric levels for normal variations
- Only flag disengaged/sarcastic/dismissive behavior if it's CLEARLY evident
- Compare agent's voice sentiment with what they're saying, but give benefit of doubt
- Remember: Right words + Slightly different tone = ACCEPTABLE (not everyone shows emotion the same way)
- Only flag as "disingenuous" if there's CLEAR evidence of insincerity

SCORING METHOD (RUBRIC-BASED EVALUATION):
- Use the RUBRIC LEVELS defined for each category above to determine the exact score
- Match the agent's performance to the appropriate rubric level based on the description
- DO NOT apply penalties or deduct points - instead, match performance to the correct rubric level
- If agent says right words with slightly different tone → This is ACCEPTABLE, match to appropriate rubric level normally
- If there are CLEAR tone mismatches or violations → Match to a LOWER rubric level that reflects the issue
- Delivery matters - consider it when determining which rubric level matches the performance
- Don't match to lower rubric levels for natural voice variations - match to rubric level based on actual performance quality
- Assign a score within the matched level's range (min_score to max_score)
- Be precise: If performance is at the top of a level, use the higher end of the range. If at the bottom, use the lower end
- If no rubric levels are defined for a category, use the default levels shown above

HOW VIOLATIONS AFFECT RUBRIC MATCHING:
- Tone mismatches (ONLY CLEAR CASES): Match to a rubric level that reflects the issue (e.g., if minor mismatch, use "Good" instead of "Excellent")
- Disingenuous behavior (ONLY CLEAR CASES): Match to a lower rubric level (e.g., "Average" or "Poor" depending on severity)
- Poor delivery (ONLY CLEAR CASES): Match to a rubric level that reflects delivery quality
- Policy violations: Match to a lower rubric level appropriate for the violation severity
- Unprofessional behavior: Match to a rubric level that reflects the unprofessionalism level
- Multiple violations: Match to the lowest appropriate rubric level that encompasses all issues
- The rubric level descriptions already account for violations - match performance to the level that best describes it

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
  "agent_tone": {{
    "primary_characteristics": "professional|dismissive|empathetic|sarcastic|frustrated|bored|engaged|disengaged",
    "tone_mismatches": [
      {{
        "segment": "early|middle|late",
        "text": "What agent said",
        "voice_sentiment": "negative|neutral|positive",
        "text_sentiment": "positive|empathetic|professional",
        "mismatch_type": "sarcasm|dismissiveness|insincerity|frustration|boredom",
        "description": "Agent said empathetic words but voice showed no empathy",
        "severity": "critical|major|minor"
      }}
    ],
    "disingenuous_behavior_detected": true,
    "keyword_gaming_detected": false,
    "overall_delivery_quality": "excellent|good|average|poor|unacceptable"
  }},
  "violations": [
    {{
      "category_name": "Exact category name from criteria above",
      "type": "violation_type (e.g., 'tone_mismatch', 'disingenuous_behavior', 'poor_delivery')",
      "description": "Clear, direct description of violation. Be specific about tone mismatches and disingenuous behavior.",
      "severity": "critical|major|minor",
      "evidence": "Specific quote and voice sentiment mismatch"
    }}
  ]
}}

IMPORTANT INSTRUCTIONS - APPLY REALISTICALLY:
1. TONE ANALYSIS (BE LENIENT):
   - Analyze agent's tone, but acknowledge that voice sentiment analysis has limitations
   - Compare voice sentiment with text content, but give benefit of doubt
   - Only flag CLEAR and OBVIOUS tone mismatches as violations
   - Don't penalize for natural voice variations
   - If agent says right thing with slightly different tone → This is ACCEPTABLE (not a violation)
   - Only flag as violation if tone is CLEARLY inappropriate (sarcastic, dismissive, unprofessional)
   - Include tone analysis in "agent_tone" section, but be realistic about limitations

2. DETECTING KEYWORD GAMING:
   - Look for agents who say compliance keywords but with poor delivery
   - Flag instances where agent uses scripted responses inappropriately
   - Detect sarcasm, dismissiveness, boredom in agent's voice
   - Match agents who "check the boxes" but show poor attitude to lower rubric levels
   - Set "keyword_gaming_detected" to true if agent uses keywords without proper delivery

3. NATURAL VOICE CHARACTERISTICS:
   - Account for speakers who naturally sound more intense
   - Look for RELATIVE changes in tone, not absolute values
   - Focus on tone DEVIATIONS, not baseline characteristics
   - If agent's voice is consistently intense, that's their natural voice (not a violation)
   - But if agent's tone changes inappropriately, that's a violation
   - Use voice baseline information to distinguish natural characteristics from actual emotions

4. AGENT TONE EVALUATION:
   - Evaluate agent's tone throughout the entire call
   - Detect patterns: Is agent consistently disengaged? Sarcastic? Dismissive?
   - Flag tone mismatches in the "agent_tone" section with specific examples
   - Include tone violations in the "violations" array
   - Set "disingenuous_behavior_detected" to true if agent shows insincere behavior

5. CATEGORY RESTRICTIONS:
   - You MUST ONLY evaluate and score these EXACT categories: {criteria_list_text}
   - DO NOT create, invent, or add any categories that are not in this list
   - DO NOT use generic category names like "Compliance", "Empathy", "Resolution", "Communication" unless they EXACTLY match a category name from the list above
   - You MUST provide a score for EVERY SINGLE category in the list above - no exceptions
   - If a category seems unrelated, score it based on how well the agent met that category's requirements (read the evaluation_prompt for each category)
   - The category_scores object in your JSON response MUST contain EXACTLY these categories and NO OTHERS

6. CATEGORY NAME MATCHING:
   - Category names must match EXACTLY (case-sensitive, character-for-character)
   - For violations, the "category_name" field MUST be one of the exact category names from the list above
   - If you're unsure about a category name, use the EXACT name as shown in the criteria list

7. SCORING REQUIREMENTS (RUBRIC-BASED):
   - Match the agent's performance to the RUBRIC LEVELS defined for each category
   - If performance matches "Excellent" level description, score in that range
   - If performance matches "Poor" or "Unacceptable" level, score in that range
   - BE HARSH: If the agent shows poor attitude, lacks professionalism, or violates policies, match them to the appropriate LOW level
   - MULTIPLE VIOLATIONS = LOW LEVELS: Don't average out violations. Each violation should place the agent in a lower rubric level
   - NO EXCUSES: Technical issues resolved poorly still deserve low rubric levels
   - BE SPECIFIC: In feedback, cite exact examples from the transcript and reference which rubric level the performance matches
   - Include tone mismatch violations in scoring

8. JSON STRUCTURE:
   - The "category_scores" object MUST contain EXACTLY these categories: {criteria_list_text}
   - Each category MUST have a "score" (0-100) and "feedback" field
   - Do NOT include any categories that are not in the list above
   - Violations can reference any of the categories from the list above
   - Include "agent_tone" section with tone mismatch analysis

Remember: Delivery matters as much as content. An agent who says the right words with the wrong tone is FAILING. An agent who uses keywords but shows poor attitude is VIOLATING policy. Be critical, be strict, be honest. ONLY use the categories provided above."""
        
        return prompt

    def _assess_call_complexity(self, transcript: str, sentiment_analysis: Optional[List[Dict[str, Any]]] = None, rule_results: Optional[Dict[str, Any]] = None) -> float:
        """
        Phase 4: Assess call complexity to determine Flash vs Pro routing.
        Returns 0.0-1.0 complexity score (higher = more complex).
        """
        complexity = 0.0

        # Length complexity (longer calls tend to be more complex)
        word_count = len(transcript.split())
        if word_count > 500:
            complexity += 0.3
        elif word_count > 200:
            complexity += 0.2
        elif word_count > 100:
            complexity += 0.1

        # Sentiment complexity (emotional calls are more complex)
        if sentiment_analysis and isinstance(sentiment_analysis, list):
            negative_segments = 0
            for s in sentiment_analysis:
                if not isinstance(s, dict):
                    continue  # Skip invalid sentiment entries

                # Handle both Deepgram sentiment format and other formats
                sentiment_obj = s.get("sentiment", {})
                sentiment_value = None

                # Deepgram format: sentiment object has direct properties
                if isinstance(sentiment_obj, dict):
                    sentiment_value = sentiment_obj.get("sentiment")
                else:
                    # Fallback for other formats
                    sentiment_value = sentiment_obj

                if sentiment_value == "negative":
                    negative_segments += 1

            total_segments = len(sentiment_analysis)
            if total_segments > 0:
                negative_ratio = negative_segments / total_segments
                complexity += negative_ratio * 0.4  # Up to 0.4 for highly emotional calls

        # Rule violations complexity (calls with violations are more complex)
        if rule_results and rule_results.get("violations"):
            violation_count = len(rule_results["violations"])
            if violation_count > 3:
                complexity += 0.3  # Major violations
            elif violation_count > 1:
                complexity += 0.2  # Some violations
            elif violation_count > 0:
                complexity += 0.1  # Minor violations

        # Topic complexity (certain topics are inherently complex)
        complex_topics = ["refund", "complaint", "escalation", "threat", "legal", "fraud", "crisis"]
        transcript_lower = transcript.lower()
        topic_matches = sum(1 for topic in complex_topics if topic in transcript_lower)
        complexity += min(topic_matches * 0.1, 0.2)  # Up to 0.2 for complex topics

        return min(complexity, 1.0)  # Cap at 1.0

    def _format_sentiment_analysis(self, sentiment_analysis: List[Dict[str, Any]]) -> str:
        """Format sentiment analysis data for prompt - NOW INCLUDES AGENT SENTIMENT"""
        if not sentiment_analysis:
            return "VOICE-BASED SENTIMENT ANALYSIS: Not available (using text-based analysis only)"
        
        # Group by speaker (BOTH caller and agent)
        caller_sentiments = [s for s in sentiment_analysis if s.get("speaker") == "caller"]
        agent_sentiments = [s for s in sentiment_analysis if s.get("speaker") == "agent"]
        
        formatted = "VOICE-BASED SENTIMENT ANALYSIS (from audio characteristics - pitch, intensity, speaking rate, prosody):\n"
        formatted += "These sentiment scores are derived from voice characteristics, not text content.\n"
        formatted += "CRITICAL: Compare voice tone with text content to detect disingenuous behavior.\n\n"
        
        # Format caller sentiments
        if caller_sentiments:
            formatted += "CALLER SENTIMENT ANALYSIS:\n"
            for idx, sentiment in enumerate(caller_sentiments[:15]):  # Increased limit
                sentiment_score = sentiment.get("sentiment", {})
                start_time = sentiment.get("start", 0)
                text = sentiment.get("text", "")[:150]  # Increased limit
                
                formatted += f"  Segment {idx + 1} (Time: {start_time:.1f}s):\n"
                formatted += f"    Voice Sentiment: {sentiment_score}\n"
                formatted += f"    Text: \"{text}...\"\n\n"
            
            if len(caller_sentiments) > 15:
                formatted += f"  ... and {len(caller_sentiments) - 15} more caller segments\n\n"
        else:
            formatted += "CALLER SENTIMENT ANALYSIS: No caller sentiment data available.\n\n"
        
        # Format agent sentiments (NEW - CRITICAL FOR DETECTING DISINGENUOUS BEHAVIOR)
        if agent_sentiments:
            formatted += "AGENT SENTIMENT ANALYSIS (CRITICAL FOR DETECTING DISINGENUOUS BEHAVIOR):\n"
            formatted += "Analyze agent's voice tone vs. text content to detect:\n"
            formatted += "- Sarcasm: Positive words with negative/neutral tone\n"
            formatted += "- Dismissiveness: Helpful words with flat/disinterested tone\n"
            formatted += "- Frustration: Professional words with stressed/angry tone\n"
            formatted += "- Insincerity: Empathetic words with neutral/bored tone\n"
            formatted += "- Keyword Gaming: Compliance keywords with inappropriate delivery\n\n"
            
            for idx, sentiment in enumerate(agent_sentiments[:15]):
                sentiment_score = sentiment.get("sentiment", {})
                start_time = sentiment.get("start", 0)
                text = sentiment.get("text", "")[:150]
                
                formatted += f"  Segment {idx + 1} (Time: {start_time:.1f}s):\n"
                formatted += f"    Voice Sentiment: {sentiment_score}\n"
                formatted += f"    Text: \"{text}...\"\n"
                formatted += f"    TONE ANALYSIS REQUIRED:\n"
                formatted += f"      - Does the voice tone match the text sentiment?\n"
                formatted += f"      - Is the agent saying the right words but with wrong tone?\n"
                formatted += f"      - Is there a mismatch indicating disingenuous behavior?\n"
                formatted += f"      - Is the agent using keywords but showing poor attitude?\n\n"
            
            if len(agent_sentiments) > 15:
                formatted += f"  ... and {len(agent_sentiments) - 15} more agent segments\n\n"
        else:
            formatted += "AGENT SENTIMENT ANALYSIS: No agent sentiment data available (cannot detect tone mismatches).\n\n"
        
        formatted += "\nCRITICAL INSTRUCTIONS FOR TONE ANALYSIS:\n"
        formatted += "1. Compare voice sentiment with text content for BOTH caller and agent\n"
        formatted += "2. Detect mismatches: Right words + Wrong tone = Disingenuous behavior\n"
        formatted += "3. Account for natural voice characteristics (some voices naturally sound more intense)\n"
        formatted += "4. Look for patterns: If agent consistently has tone mismatches, flag as problematic\n"
        formatted += "5. Agent saying keywords with inappropriate tone is a VIOLATION\n"
        formatted += "6. Focus on RELATIVE changes in tone, not absolute voice characteristics\n"
        formatted += "7. Flag tone mismatches in the 'agent_tone' section with specific examples\n"
        
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
    
    def call_llm(
        self,
        prompt: str,
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_tokens: int = 2048,
        model: Optional[str] = None,
        seed: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generic LLM call method for deterministic evaluations.
        
        Args:
            prompt: The prompt text to send to the LLM
            temperature: Sampling temperature (0.0 for deterministic)
            top_p: Nucleus sampling parameter
            max_tokens: Maximum tokens in response
            model: Model name (defaults to flash_model)
            seed: Optional seed for deterministic generation
            
        Returns:
            Dictionary with 'response', 'model', 'tokens_used', etc.
        """
        if not self.flash_model:
            raise Exception("Gemini API key not configured")
        
        # Use specified model or default to flash_model
        model_instance = self.flash_model
        
        # Build generation config
        generation_config_kwargs = {
            "temperature": temperature,
            "top_p": top_p,
            "candidate_count": 1,
            "max_output_tokens": max_tokens,
        }
        
        # Add seed if provided (for deterministic generation)
        seed_used = False
        if seed is not None:
            try:
                # Convert seed string to integer if possible
                seed_int = hash(seed) % (2**31)  # Convert to 32-bit signed int
                generation_config_kwargs["seed"] = seed_int
                seed_used = True
            except Exception as e:
                logger.warning(f"Could not set seed: {e}")
        
        # Try to create GenerationConfig with seed, fallback without if not supported
        try:
            generation_config = genai.types.GenerationConfig(**generation_config_kwargs)
        except TypeError as e:
            if "seed" in str(e) and seed_used:
                # Seed parameter not supported in this version, retry without it
                logger.warning(f"GenerationConfig does not support 'seed' parameter in this version. Falling back without seed. Error: {e}")
                generation_config_kwargs.pop("seed", None)
                generation_config = genai.types.GenerationConfig(**generation_config_kwargs)
                seed_used = False
            else:
                # Some other error, re-raise it
                raise
        
        try:
            response = model_instance.generate_content(
                prompt,
                generation_config=generation_config
            )
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise Exception(f"Failed to generate content from Gemini API: {e}")
        
        # Parse response
        if not response or not hasattr(response, 'text') or not response.text:
            raise Exception("Empty or invalid response from Gemini API")
        
        response_text = response.text
        
        # Estimate tokens (rough approximation)
        tokens_used = len(prompt.split()) + len(response_text.split())
        
        model_name = model or "gemini-2.5-flash-lite"
        
        return {
            "response": response_text,
            "model": model_name,
            "tokens_used": tokens_used,
            "temperature": temperature,
            "top_p": top_p,
            "seed": seed if seed_used else None
        }

