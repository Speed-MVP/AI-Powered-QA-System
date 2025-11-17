"""
Phase 2: Policy Rule Builder - LLM-powered Policy Rule Generation Service
Converts human-written policy text into structured, deterministic policy_rules JSON.
"""

import json
import hashlib
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict

from app.services.gemini import GeminiService
from app.schemas.policy_rules import (
    validate_policy_rules,
    validate_rule,
    detect_conflicting_rules,
    PolicyRulesSchema,
    PolicyRule
)
from app.config import settings

logger = logging.getLogger(__name__)


class PolicyRuleBuilder:
    """
    Service for converting human-written policy text into structured policy rules using LLM.

    Handles:
    - Prompt building and LLM calls
    - Response parsing and validation
    - Clarification question handling
    - Deterministic rule generation
    """

    def __init__(self):
        self.gemini = GeminiService() if settings.gemini_api_key else None
        self.prompt_template = self._load_prompt_template()
        self.analysis_prompt_template = self._load_analysis_prompt_template()
        self.clarification_prompt_template = self._load_clarification_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the LLM prompt template for rule generation."""
        return """You are a Policy Rule Extractor for a call center QA system. Your task is to convert human-written policy descriptions into structured, machine-executable rules.

INPUT:
{input_data}

OUTPUT FORMAT:
You must respond with valid JSON only, following this exact schema. ALL RULES MUST INCLUDE ALL REQUIRED FIELDS:

{
  "policy_rules": {
    "CategoryName": [
      {
        "id": "snake_case_rule_id",
        "type": "boolean|numeric|phrase|list|conditional|multi_step|tone_based|resolution",
        "category": "CategoryName",  // REQUIRED: Must match the category key
        "severity": "critical|major|minor",  // REQUIRED: Severity if rule fails
        "description": "human readable description",  // REQUIRED
        "enabled": true,  // Optional, defaults to true
        "critical": false,  // Optional, defaults to false
        
        // For boolean rules:
        "required": true/false,  // REQUIRED for boolean: true if behavior required, false if forbidden
        "value": true/false,  // Optional: same as required for boolean rules
        
        // For numeric rules:
        "comparator": "le|lt|eq|ge|gt",  // REQUIRED for numeric
        "value": 15.0,  // REQUIRED for numeric: threshold value
        "unit": "seconds",  // Optional, defaults to "seconds"
        "measurement_field": "greeting_time",  // REQUIRED for numeric: what to measure
        
        // For phrase rules:
        "required": true/false,  // REQUIRED for phrase: true if phrases required, false if forbidden
        "phrases": ["phrase1", "phrase2"],  // REQUIRED for phrase: list of phrases
        "case_sensitive": false,  // Optional
        "fuzzy_match": false,  // Optional
        
        // For list rules:
        "required_items": ["item1", "item2"],  // REQUIRED for list
        "min_required": 1,  // Optional
        "all_required": false,  // Optional
        
        // For conditional rules:
        "condition": {{"field": "caller_sentiment", "operator": "le", "value": -0.4}},  // REQUIRED
        "then_rule": {{"type": "boolean", "required": true}},  // REQUIRED
        
        // For multi_step rules:
        "steps": [{{"description": "step1", "evidence_patterns": ["pattern1"]}}],  // REQUIRED
        "strict_order": true,  // Optional
        "allow_gaps": false,  // Optional
        
        // For tone_based rules:
        "check_agent_tone": true,  // Optional
        "check_caller_tone": false,  // Optional
        "baseline_comparison": true,  // Optional
        "mismatch_threshold": 0.5,  // Optional
        
        // For resolution rules:
        "must_resolve": true,  // Optional
        "resolution_markers": ["resolved", "fixed"],  // Optional
        "must_document_next_steps": false,  // Optional
        "next_steps_markers": ["next steps", "follow up"]  // Optional
      }
    ]
  },
  "clarifications": [
    {
      "id": "q1",
      "question": "Clarification question for ambiguous parts?"
    }
  ]
}

RULE TYPES:
- boolean: true/false rules (e.g., "agent must identify themselves")
- numeric: rules with numeric thresholds and comparators (e.g., "respond within 10 seconds")
- phrase: rules checking for required/forbidden phrases
- list: rules checking against allowed values
- conditional: if-then logic rules
- multi_step: ordered checklist rules
- tone_based: sentiment/tone analysis rules
- resolution: issue resolution detection rules

EXAMPLES:

Input: "Agent must greet customer within 15 seconds and identify themselves"
Output:
{
  "policy_rules": {
    "Communication Skills": [
      {
        "id": "greet_within_seconds",
        "type": "numeric",
        "category": "Communication Skills",
        "severity": "major",
        "description": "Agent must greet within 15 seconds",
        "comparator": "le",
        "value": 15.0,
        "unit": "seconds",
        "measurement_field": "greeting_time"
      },
      {
        "id": "identify_self",
        "type": "boolean",
        "category": "Communication Skills",
        "severity": "major",
        "description": "Agent must identify themselves",
        "required": true
      }
    ]
  },
  "clarifications": []
}

Input: "Show empathy when customer is frustrated"
Output:
{
  "policy_rules": {
    "Empathy": [
      {
        "id": "requires_apology_if_negative_sentiment",
        "type": "boolean",
        "category": "Empathy",
        "severity": "major",
        "description": "Agent must show empathy when customer sentiment is negative",
        "required": true
      }
    ]
  },
  "clarifications": [
    {"id": "q1", "question": "What specific empathy keywords or actions should be required?"}
  ]
}

GUIDELINES:
1. Use snake_case for all rule IDs
2. CRITICAL: You MUST use ONLY the exact category names provided in the rubric_levels input. Do NOT create new category names.
3. If rubric_levels are provided, use those EXACT category names as keys in policy_rules (case-sensitive, character-for-character match).
4. If no rubric_levels are provided, use standard categories: Compliance, Communication Skills, Empathy, Problem-Solving, Resolution
5. Be specific and actionable in rule descriptions
6. Include clarifications for ambiguous terms like "quickly", "short time", "angry customer"
7. Prefer concrete numeric values over vague terms
8. Do not hallucinate rule IDs - stick to common QA patterns
9. Output valid JSON only - no additional text or formatting

CATEGORY NAME REQUIREMENTS:
- The category name in the JSON key MUST match EXACTLY one of the category names from rubric_levels
- The "category" field inside each rule MUST also match that exact category name
- Do NOT use variations like "Resolve" (use "Resolution"), "Start to End" (use appropriate category from rubric_levels), etc.
- If you see category names in the policy text, map them to the exact names from rubric_levels

Now process the input:"""

    def generate_policy_rules(
        self,
        policy_text: str,
        rubric_levels: Optional[Dict[str, Any]] = None,
        examples: Optional[str] = None,
        user_answers: Optional[Dict[str, str]] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate policy rules from human-written text using LLM.

        Args:
            policy_text: The human-written policy description
            rubric_levels: Optional rubric metadata from policy template
            examples: Optional example call transcripts
            user_answers: Optional answers to previous clarification questions

        Returns:
            Tuple of (llm_response, metadata) where:
            - llm_response: Parsed LLM response with policy_rules and clarifications
            - metadata: LLM call metadata (tokens, latency, etc.)
        """
        # Build input data for LLM
        input_data = {
            "policy_text": policy_text,
            "rubric_levels": rubric_levels or {},
            "examples": examples or "",
            "user_answers": user_answers or {}
        }

        # Build prompt
        prompt = self._build_prompt(input_data)

        # Call LLM with deterministic settings
        start_time = time.time()
        try:
            llm_response = self.gemini.call_llm(
                prompt=prompt,
                temperature=0.0,  # Deterministic
                top_p=1.0,        # No nucleus sampling
                max_tokens=2000,
                model="gemini-2.0-flash-exp"  # Use fast model for cost efficiency
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Parse and validate response
            parsed_response = self._parse_llm_response(llm_response["response"])

            # Add metadata
            metadata = {
                "llm_model": llm_response.get("model", "unknown"),
                "llm_tokens_used": llm_response.get("tokens_used"),
                "llm_latency_ms": latency_ms,
                "llm_prompt_hash": self._hash_prompt(prompt),
                "raw_response": llm_response["response"]
            }

            # Log metrics for monitoring
            logger.info(
                f"PolicyRuleBuilder: Generated rules for {len(llm_response.get('policy_rules', {}))} categories, "
                f"{len(llm_response.get('clarifications', []))} clarifications, "
                f"latency={latency_ms}ms, tokens={llm_response.get('tokens_used', 0)}"
            )

            return parsed_response, metadata

        except Exception as e:
            logger.error(f"LLM call failed in PolicyRuleBuilder: {e}")
            raise

    def _build_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build the complete prompt for LLM."""
        input_json = json.dumps(input_data, indent=2)
        return self.prompt_template.replace("{input_data}", input_json)

    def _parse_llm_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Parse LLM response and validate structure.

        Args:
            raw_response: Raw text response from LLM

        Returns:
            Parsed response with policy_rules and clarifications

        Raises:
            ValueError: If response cannot be parsed or validated
        """
        try:
            # Clean the response (remove markdown formatting if present)
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            parsed = json.loads(cleaned_response)

            # Validate structure
            if not isinstance(parsed, dict):
                raise ValueError("Response must be a JSON object")

            if "policy_rules" not in parsed:
                raise ValueError("Response must contain 'policy_rules' key")

            if "clarifications" not in parsed:
                parsed["clarifications"] = []

            # Validate clarifications format
            if not isinstance(parsed["clarifications"], list):
                raise ValueError("'clarifications' must be a list")

            for i, clarification in enumerate(parsed["clarifications"]):
                if not isinstance(clarification, dict) or "id" not in clarification or "question" not in clarification:
                    raise ValueError(f"Clarification {i} must have 'id' and 'question' fields")

            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {raw_response[:500]}...")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
    
    def _post_process_rules(self, rules_dict: Dict[str, Any], valid_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Post-process LLM-generated rules to add missing required fields with defaults.
        
        Args:
            rules_dict: Raw rules dictionary from LLM
            valid_categories: List of valid category names from the template (optional)
            
        Returns:
            Processed rules dictionary with all required fields
        """
        # Map invalid category names to valid ones
        category_mapping = {
            "Resolve": "Resolution",
            "Start to End": "Communication Skills",  # Default mapping
            "Professional": "Professionalism",
            "Compliance Skills": "Compliance",
            "Problem Solving": "Problem-Solving",
            "ProblemSolving": "Problem-Solving",
        }
        
        # If valid categories provided, try to match invalid names to valid ones
        if valid_categories:
            # Add fuzzy matching for common variations
            for invalid_name in ["Resolve", "Resolving", "Resolved"]:
                if "Resolution" in valid_categories:
                    category_mapping[invalid_name] = "Resolution"
            for invalid_name in ["Start to End", "Start-to-End", "Call Flow"]:
                if "Communication Skills" in valid_categories:
                    category_mapping[invalid_name] = "Communication Skills"
                elif "Professionalism" in valid_categories:
                    category_mapping[invalid_name] = "Professionalism"
        
        processed = {}
        
        for category_name, rules_list in rules_dict.items():
            # Map invalid category names to valid ones
            mapped_category = category_mapping.get(category_name, category_name)
            
            # If we have valid categories and the mapped category is still invalid, try to find a match
            if valid_categories and mapped_category not in valid_categories:
                # Try fuzzy matching: find category that contains words from the invalid name
                invalid_words = set(category_name.lower().split())
                for valid_cat in valid_categories:
                    valid_words = set(valid_cat.lower().split())
                    if invalid_words.intersection(valid_words):
                        mapped_category = valid_cat
                        break
                # If still no match, use first valid category as fallback
                if mapped_category not in valid_categories and valid_categories:
                    mapped_category = valid_categories[0]
            
            if mapped_category not in processed:
                processed[mapped_category] = []
            
            for rule in rules_list:
                if not isinstance(rule, dict):
                    continue
                
                # Add required base fields if missing
                if "category" not in rule:
                    rule["category"] = mapped_category
                else:
                    # Also map the category field inside the rule
                    rule_category = category_mapping.get(rule["category"], rule["category"])
                    if valid_categories and rule_category not in valid_categories:
                        # Try fuzzy matching
                        invalid_words = set(rule["category"].lower().split())
                        for valid_cat in valid_categories:
                            valid_words = set(valid_cat.lower().split())
                            if invalid_words.intersection(valid_words):
                                rule_category = valid_cat
                                break
                        if rule_category not in valid_categories and valid_categories:
                            rule_category = valid_categories[0]
                    rule["category"] = rule_category
                
                if "severity" not in rule:
                    # Default severity based on rule type or description
                    rule["severity"] = "major"  # Default to major
                
                if "enabled" not in rule:
                    rule["enabled"] = True
                
                if "critical" not in rule:
                    rule["critical"] = False
                
                # Add type-specific required fields
                rule_type = rule.get("type", "").lower()
                
                if rule_type == "boolean":
                    if "required" not in rule:
                        # Try to infer from description or value
                        if "value" in rule:
                            rule["required"] = bool(rule["value"])
                        else:
                            # Default: if description says "must" or "should", it's required
                            desc = rule.get("description", "").lower()
                            rule["required"] = "must" in desc or "should" in desc or "required" in desc
                    if "evidence_patterns" not in rule:
                        rule["evidence_patterns"] = []
                
                elif rule_type == "numeric":
                    if "comparator" not in rule:
                        rule["comparator"] = "le"  # Default to less than or equal
                    if "unit" not in rule:
                        rule["unit"] = "seconds"
                    if "measurement_field" not in rule:
                        # Try to infer from id or description
                        rule_id = rule.get("id", "").lower()
                        if "time" in rule_id or "duration" in rule_id:
                            rule["measurement_field"] = "duration"
                        elif "count" in rule_id:
                            rule["measurement_field"] = "count"
                        else:
                            rule["measurement_field"] = "value"
                
                elif rule_type == "phrase":
                    if "required" not in rule:
                        rule["required"] = True  # Default to required phrases
                    if "phrases" not in rule:
                        rule["phrases"] = []
                    if "case_sensitive" not in rule:
                        rule["case_sensitive"] = False
                    if "fuzzy_match" not in rule:
                        rule["fuzzy_match"] = False
                
                elif rule_type == "list":
                    if "required_items" not in rule:
                        rule["required_items"] = []
                    if "min_required" not in rule:
                        rule["min_required"] = 1
                    if "all_required" not in rule:
                        rule["all_required"] = False
                
                elif rule_type == "conditional":
                    if "condition" not in rule:
                        rule["condition"] = {}
                    if "then_rule" not in rule:
                        rule["then_rule"] = {}
                
                elif rule_type == "multi_step":
                    if "steps" not in rule:
                        rule["steps"] = []
                    if "strict_order" not in rule:
                        rule["strict_order"] = True
                    if "allow_gaps" not in rule:
                        rule["allow_gaps"] = False
                
                elif rule_type == "tone_based":
                    if "check_agent_tone" not in rule:
                        rule["check_agent_tone"] = True
                    if "check_caller_tone" not in rule:
                        rule["check_caller_tone"] = False
                    if "baseline_comparison" not in rule:
                        rule["baseline_comparison"] = True
                    if "mismatch_threshold" not in rule:
                        rule["mismatch_threshold"] = 0.5
                
                elif rule_type == "resolution":
                    if "must_resolve" not in rule:
                        rule["must_resolve"] = True
                    if "resolution_markers" not in rule:
                        rule["resolution_markers"] = []
                    if "must_document_next_steps" not in rule:
                        rule["must_document_next_steps"] = False
                    if "next_steps_markers" not in rule:
                        rule["next_steps_markers"] = []
                
                processed[mapped_category].append(rule)
        
        return processed

    def validate_generated_rules(self, generated_rules: Dict[str, Any]) -> Tuple[bool, Optional[PolicyRulesSchema], List[str]]:
        """
        Validate generated policy rules using the PolicyRulesSchema validator.

        Args:
            generated_rules: The policy_rules portion from LLM response

        Returns:
            Tuple of (is_valid, normalized_rules, error_messages)
        """
        try:
            # Convert to the format expected by schema
            rules_json = {
                "version": 1,
                "rules": generated_rules,
                "metadata": {}
            }

            # Validate using schema
            normalized = validate_policy_rules(rules_json)

            return True, normalized, []

        except Exception as e:
            logger.warning(f"Generated rules validation failed: {e}")
            return False, None, [str(e)]

    def _hash_prompt(self, prompt: str) -> str:
        """Generate SHA-256 hash of prompt for reproducibility tracking."""
        return hashlib.sha256(prompt.encode('utf-8')).hexdigest()

    def extract_policy_text_from_template(self, policy_template: Dict[str, Any]) -> str:
        """
        Extract human-readable policy text from policy template data.

        Args:
            policy_template: Policy template with criteria and rubric levels

        Returns:
            Concatenated policy text description
        """
        policy_parts = []

        # Add template description
        if policy_template.get("description"):
            policy_parts.append(f"Policy Description: {policy_template['description']}")

        # Add criteria descriptions
        for criterion in policy_template.get("criteria", []):
            if criterion.get("evaluation_prompt"):
                policy_parts.append(f"{criterion['category_name']}: {criterion['evaluation_prompt']}")

        return "\n\n".join(policy_parts)

    def extract_rubric_levels(self, policy_template: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract rubric level information from policy template.

        Args:
            policy_template: Policy template with criteria and rubric levels

        Returns:
            Dict mapping category names to list of rubric levels
        """
        rubric_data = {}

        for criterion in policy_template.get("criteria", []):
            category_name = criterion["category_name"]
            rubric_data[category_name] = []

            for level in criterion.get("rubric_levels", []):
                rubric_data[category_name].append({
                    "level_name": level["level_name"],
                    "min_score": level["min_score"],
                    "max_score": level["max_score"],
                    "description": level["description"]
                })

        return rubric_data
    
    def analyze_policy_text(
        self,
        policy_text: str,
        rubric_levels: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Stage 1: Analyze policy text and identify vague statements, missing details, and ambiguities.
        
        Args:
            policy_text: Human-written policy text
            rubric_levels: Optional rubric level information
            
        Returns:
            Dictionary with analysis results including vague_statements, missing_details, ambiguous_terms
        """
        if not self.gemini:
            raise Exception("Gemini API key not configured")
        
        input_data = {
            "policy_text": policy_text,
            "rubric_levels": rubric_levels or {}
        }
        
        prompt = self.analysis_prompt_template.replace(
            "{input_data}",
            json.dumps(input_data, indent=2)
        )
        
        try:
            llm_response = self.gemini.call_llm(
                prompt=prompt,
                temperature=0.0,
                top_p=1.0,
                max_tokens=2000,
                model="gemini-2.0-flash-exp"
            )
            
            # Parse response
            cleaned_response = llm_response["response"].strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            parsed = json.loads(cleaned_response)
            
            return {
                "vague_statements": parsed.get("vague_statements", []),
                "missing_details": parsed.get("missing_details", []),
                "ambiguous_terms": parsed.get("ambiguous_terms", []),
                "analysis_summary": parsed.get("analysis_summary", "")
            }
            
        except Exception as e:
            logger.error(f"Policy analysis failed: {e}")
            raise
    
    def generate_clarifying_questions(
        self,
        policy_text: str,
        analysis_results: Dict[str, Any],
        rubric_levels: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Stage 2: Generate clarifying questions for ambiguous policies.
        
        Args:
            policy_text: Original policy text
            analysis_results: Results from analyze_policy_text
            rubric_levels: Optional rubric level information
            
        Returns:
            List of clarification questions with id and question fields
        """
        if not self.gemini:
            raise Exception("Gemini API key not configured")
        
        input_data = {
            "policy_text": policy_text,
            "vague_statements": analysis_results.get("vague_statements", []),
            "missing_details": analysis_results.get("missing_details", []),
            "ambiguous_terms": analysis_results.get("ambiguous_terms", []),
            "rubric_levels": rubric_levels or {}
        }
        
        prompt = self.clarification_prompt_template.replace(
            "{input_data}",
            json.dumps(input_data, indent=2)
        )
        
        try:
            llm_response = self.gemini.call_llm(
                prompt=prompt,
                temperature=0.0,
                top_p=1.0,
                max_tokens=2000,
                model="gemini-2.0-flash-exp"
            )
            
            # Parse response
            cleaned_response = llm_response["response"].strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            parsed = json.loads(cleaned_response)
            
            clarifications = parsed.get("clarifications", [])
            
            # Validate format
            for i, clarification in enumerate(clarifications):
                if not isinstance(clarification, dict) or "id" not in clarification or "question" not in clarification:
                    raise ValueError(f"Clarification {i} must have 'id' and 'question' fields")
            
            return clarifications
            
        except Exception as e:
            logger.error(f"Clarification generation failed: {e}")
            raise
    
    def generate_structured_rules(
        self,
        policy_text: str,
        clarification_answers: Dict[str, str],
        rubric_levels: Optional[Dict[str, Any]] = None
    ) -> Tuple[PolicyRulesSchema, Dict[str, Any]]:
        """
        Stage 4: Generate structured rules from policy text + clarification answers.
        
        Args:
            policy_text: Original policy text
            clarification_answers: Dictionary mapping question IDs to answers
            rubric_levels: Optional rubric level information
            
        Returns:
            Tuple of (validated PolicyRulesSchema, metadata)
        """
        if not self.gemini:
            raise Exception("Gemini API key not configured")
        
        input_data = {
            "policy_text": policy_text,
            "clarification_answers": clarification_answers,
            "rubric_levels": rubric_levels or {}
        }
        
        prompt = self._build_prompt(input_data)
        
        start_time = time.time()
        try:
            llm_response = self.gemini.call_llm(
                prompt=prompt,
                temperature=0.0,
                top_p=1.0,
                max_tokens=3000,
                model="gemini-2.0-flash-exp"
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Parse response
            parsed_response = self._parse_llm_response(llm_response["response"])
            
            # Extract valid category names from rubric_levels
            valid_categories = list(rubric_levels.keys()) if rubric_levels else None
            
            # Post-process rules to add missing required fields and map category names
            processed_rules = self._post_process_rules(
                parsed_response.get("policy_rules", {}),
                valid_categories=valid_categories
            )
            
            # Validate against schema
            rules_dict = {
                "version": 1,
                "rules": processed_rules,
                "metadata": {}
            }
            
            validated_rules = validate_policy_rules(rules_dict)
            
            # Check for conflicts
            conflicts = detect_conflicting_rules(validated_rules.rules)
            
            metadata = {
                "llm_model": llm_response.get("model", "unknown"),
                "llm_tokens_used": llm_response.get("tokens_used"),
                "llm_latency_ms": latency_ms,
                "llm_prompt_hash": self._hash_prompt(prompt),
                "conflicts_detected": conflicts,
                "raw_response": llm_response["response"]
            }
            
            logger.info(
                f"PolicyRuleBuilder: Generated {sum(len(rules) for rules in validated_rules.rules.values())} rules, "
                f"{len(conflicts)} conflicts, latency={latency_ms}ms"
            )
            
            return validated_rules, metadata
            
        except Exception as e:
            logger.error(f"Rule generation failed: {e}")
            raise
    
    def validate_rules(self, rules: PolicyRulesSchema) -> Tuple[bool, List[str]]:
        """
        Validate rules against schema.
        
        Args:
            rules: PolicyRulesSchema object to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            # Schema validation is done by Pydantic - rules object is already validated
            # Just check for conflicts
            conflicts = detect_conflicting_rules(rules.rules)
            if conflicts:
                return False, [c.get("description", "Rule conflict detected") for c in conflicts]
            return True, []
        except Exception as e:
            return False, [str(e)]
    
    def detect_conflicts(self, rules: PolicyRulesSchema) -> List[Dict[str, Any]]:
        """
        Detect conflicting rules.
        
        Args:
            rules: PolicyRulesSchema object
            
        Returns:
            List of conflict descriptions
        """
        return detect_conflicting_rules(rules.rules)
    
    def _load_analysis_prompt_template(self) -> str:
        """Load prompt template for policy analysis."""
        return """You are a Policy Analyst. Analyze the provided policy text and identify vague statements, missing details, and ambiguous terms.

INPUT:
{input_data}

OUTPUT FORMAT (JSON only):
{{
  "vague_statements": ["list of vague statements"],
  "missing_details": ["list of missing details"],
  "ambiguous_terms": ["list of ambiguous terms"],
  "analysis_summary": "brief summary of analysis"
}}

GUIDELINES:
- Identify statements that lack specificity (e.g., "respond quickly", "show empathy")
- Find missing thresholds, timeframes, or concrete requirements
- Flag terms that could be interpreted multiple ways
- Focus on what would prevent deterministic rule creation

Now analyze the input:"""
    
    def _load_clarification_prompt_template(self) -> str:
        """Load prompt template for clarification question generation."""
        return """You are a Policy Clarification Generator. Generate specific clarifying questions for vague or ambiguous policy statements.

INPUT:
{input_data}

OUTPUT FORMAT (JSON only):
{{
  "clarifications": [
    {{
      "id": "q1",
      "question": "Specific question about ambiguous term"
    }}
  ]
}}

GUIDELINES:
- Generate questions that will lead to concrete, quantifiable answers
- Focus on thresholds, timeframes, specific phrases, and measurable criteria
- Each question should eliminate ambiguity
- Use clear, direct language

Now generate clarifying questions:"""
