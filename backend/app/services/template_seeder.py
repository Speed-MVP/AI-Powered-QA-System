"""
Service to seed default Standard QA Template for new companies.
Creates a pre-configured template with criteria, rubric levels, and generated rules.
"""

import logging
from sqlalchemy.orm import Session
from app.models.policy_template import PolicyTemplate
from app.models.evaluation_criteria import EvaluationCriteria
from app.models.evaluation_rubric_level import EvaluationRubricLevel
from app.services.policy_rule_builder import PolicyRuleBuilder
from decimal import Decimal
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


def seed_default_template(company_id: str, user_id: str, db: Session) -> PolicyTemplate:
    """
    Create the default Standard QA Template for a new company.
    
    Args:
        company_id: The company ID to create the template for
        user_id: The user ID who will be marked as approving the rules
        db: Database session
        
    Returns:
        The created PolicyTemplate with criteria and rules
    """
    # Check if default template already exists
    existing_template = db.query(PolicyTemplate).filter(
        PolicyTemplate.company_id == company_id,
        PolicyTemplate.template_name == "Standard QA Template"
    ).first()
    
    if existing_template:
        logger.info(f"Default template already exists for company {company_id}")
        return existing_template
    
    # Create the template
    template = PolicyTemplate(
        id=str(uuid.uuid4()),
        company_id=company_id,
        template_name="Standard QA Template",
        description="Standard quality assurance evaluation template for call center interactions. This template evaluates agent performance across compliance, empathy, and resolution metrics.",
        is_active=True,
        enable_structured_rules=True  # Will be set to True after rules are generated, but set it initially too
    )
    db.add(template)
    db.flush()
    
    # Define default criteria (5 standard QA criteria)
    criteria_definitions = [
        {
            "category_name": "Compliance",
            "weight": Decimal("30.00"),
            "passing_score": 90,
            "evaluation_prompt": "Evaluate if the agent followed all compliance guidelines including required disclosures, identity verification, and regulatory requirements. Score higher if all compliance protocols were met.",
            "rubric_levels": [
                {
                    "level_name": "Excellent",
                    "level_order": 1,
                    "min_score": 90,
                    "max_score": 100,
                    "description": "All compliance requirements met perfectly. Required disclosures provided clearly, identity verified properly, all regulatory protocols followed without exception.",
                    "examples": "Agent clearly stated required disclosures, verified customer identity using approved methods, followed all regulatory guidelines."
                },
                {
                    "level_name": "Good",
                    "level_order": 2,
                    "min_score": 75,
                    "max_score": 89,
                    "description": "Most compliance requirements met. Minor omissions or unclear delivery of required information.",
                    "examples": "Agent provided most disclosures but may have missed one minor requirement or delivered it unclearly."
                },
                {
                    "level_name": "Average",
                    "level_order": 3,
                    "min_score": 60,
                    "max_score": 74,
                    "description": "Some compliance requirements met but significant gaps exist. Missing important disclosures or verification steps.",
                    "examples": "Agent missed some required disclosures or did not properly verify customer identity."
                },
                {
                    "level_name": "Poor",
                    "level_order": 4,
                    "min_score": 0,
                    "max_score": 59,
                    "description": "Major compliance violations. Missing critical disclosures, improper verification, or regulatory violations.",
                    "examples": "Agent failed to provide required disclosures, did not verify identity, or violated regulatory requirements."
                }
            ]
        },
        {
            "category_name": "Communication Skills",
            "weight": Decimal("25.00"),
            "passing_score": 75,
            "evaluation_prompt": "Evaluate the agent's communication effectiveness including professional greeting, clear explanations, active listening, appropriate tone, and ability to convey information in a clear and jargon-free manner. Assess if the agent asked probing questions to understand the issue and maintained a professional demeanor throughout.",
            "rubric_levels": [
                {
                    "level_name": "Excellent",
                    "level_order": 1,
                    "min_score": 85,
                    "max_score": 100,
                    "description": "Exceptional communication throughout. Professional greeting, clear and concise explanations, excellent active listening, appropriate tone, and information conveyed in easily understandable terms. Agent asked effective probing questions.",
                    "examples": "Agent greeted professionally, explained solutions clearly without jargon, listened attentively, asked clarifying questions, and maintained appropriate tone throughout."
                },
                {
                    "level_name": "Good",
                    "level_order": 2,
                    "min_score": 70,
                    "max_score": 84,
                    "description": "Good communication skills demonstrated. Professional greeting, mostly clear explanations, good listening, though some areas could be improved in clarity or tone consistency.",
                    "examples": "Agent greeted well and communicated clearly most of the time, but may have used some technical terms or could have asked more probing questions."
                },
                {
                    "level_name": "Average",
                    "level_order": 3,
                    "min_score": 55,
                    "max_score": 69,
                    "description": "Adequate communication but with notable gaps. Greeting may have been rushed, explanations unclear at times, limited active listening, or inconsistent tone.",
                    "examples": "Agent communicated but explanations were sometimes unclear, used technical jargon, or showed limited active listening skills."
                },
                {
                    "level_name": "Poor",
                    "level_order": 4,
                    "min_score": 0,
                    "max_score": 54,
                    "description": "Poor communication skills. Unprofessional greeting, unclear or confusing explanations, lack of active listening, inappropriate tone, or excessive use of jargon.",
                    "examples": "Agent failed to greet properly, explanations were confusing, did not listen to customer, used inappropriate tone, or relied heavily on technical jargon."
                }
            ]
        },
        {
            "category_name": "Empathy",
            "weight": Decimal("20.00"),
            "passing_score": 70,
            "evaluation_prompt": "Assess how well the agent acknowledged customer emotions and concerns. Look for empathetic language, active listening indicators, and appropriate responses to customer frustration.",
            "rubric_levels": [
                {
                    "level_name": "Excellent",
                    "level_order": 1,
                    "min_score": 85,
                    "max_score": 100,
                    "description": "Exceptional empathy demonstrated. Agent clearly acknowledged customer emotions, used empathetic language throughout, showed genuine concern, and validated customer feelings effectively.",
                    "examples": "Agent said 'I understand how frustrating this must be for you' and actively listened to customer concerns with appropriate responses."
                },
                {
                    "level_name": "Good",
                    "level_order": 2,
                    "min_score": 70,
                    "max_score": 84,
                    "description": "Good empathy shown. Agent acknowledged emotions and used some empathetic language, though could be more consistent or deeper.",
                    "examples": "Agent acknowledged customer frustration and used some empathetic phrases, but could have been more consistent."
                },
                {
                    "level_name": "Average",
                    "level_order": 3,
                    "min_score": 55,
                    "max_score": 69,
                    "description": "Limited empathy demonstrated. Agent may have acknowledged emotions briefly but lacked consistent empathetic responses or appropriate language.",
                    "examples": "Agent showed minimal empathy, mostly focused on solving the problem without acknowledging customer emotions."
                },
                {
                    "level_name": "Poor",
                    "level_order": 4,
                    "min_score": 0,
                    "max_score": 54,
                    "description": "Little to no empathy shown. Agent ignored customer emotions, used dismissive language, or made customer feel unheard.",
                    "examples": "Agent dismissed customer concerns, showed no understanding of customer emotions, or used inappropriate language."
                }
            ]
        },
        {
            "category_name": "Problem-Solving",
            "weight": Decimal("15.00"),
            "passing_score": 75,
            "evaluation_prompt": "Evaluate the agent's problem-solving abilities including accurate issue identification, logical troubleshooting approach, effective solution implementation, and appropriate escalation when needed. Assess if the agent followed structured steps to resolve the problem.",
            "rubric_levels": [
                {
                    "level_name": "Excellent",
                    "level_order": 1,
                    "min_score": 85,
                    "max_score": 100,
                    "description": "Exceptional problem-solving skills. Accurately identified root cause, followed logical troubleshooting steps, implemented effective solution, and escalated appropriately when needed.",
                    "examples": "Agent quickly identified the issue, followed systematic troubleshooting, provided effective solution, and escalated to higher tier when appropriate."
                },
                {
                    "level_name": "Good",
                    "level_order": 2,
                    "min_score": 70,
                    "max_score": 84,
                    "description": "Good problem-solving demonstrated. Mostly accurate issue identification, followed reasonable troubleshooting steps, though approach could have been more systematic or solution more effective.",
                    "examples": "Agent identified the issue and worked toward solution, but troubleshooting could have been more structured or solution could have been more comprehensive."
                },
                {
                    "level_name": "Average",
                    "level_order": 3,
                    "min_score": 55,
                    "max_score": 69,
                    "description": "Adequate problem-solving but with gaps. Issue identification may have been incomplete, troubleshooting approach was somewhat scattered, or solution was only partially effective.",
                    "examples": "Agent attempted to solve the problem but missed some key aspects, troubleshooting was not systematic, or solution was incomplete."
                },
                {
                    "level_name": "Poor",
                    "level_order": 4,
                    "min_score": 0,
                    "max_score": 54,
                    "description": "Poor problem-solving skills. Failed to identify root cause, no clear troubleshooting approach, ineffective solutions, or inappropriate escalation decisions.",
                    "examples": "Agent misunderstood the issue, had no clear troubleshooting approach, provided ineffective solutions, or failed to escalate when needed."
                }
            ]
        },
        {
            "category_name": "Resolution",
            "weight": Decimal("10.00"),
            "passing_score": 80,
            "evaluation_prompt": "Determine if the customer's issue was successfully resolved. Check for customer confirmation of satisfaction, clear action plans, and follow-up commitments.",
            "rubric_levels": [
                {
                    "level_name": "Excellent",
                    "level_order": 1,
                    "min_score": 85,
                    "max_score": 100,
                    "description": "Issue fully resolved. Customer confirmed satisfaction, clear action plan provided, appropriate follow-up scheduled, and customer expressed appreciation.",
                    "examples": "Customer confirmed the issue is resolved, agent provided clear next steps, and customer thanked the agent."
                },
                {
                    "level_name": "Good",
                    "level_order": 2,
                    "min_score": 70,
                    "max_score": 84,
                    "description": "Issue mostly resolved. Customer seems satisfied, action plan provided, though follow-up may be unclear or customer satisfaction not explicitly confirmed.",
                    "examples": "Agent provided solution and customer seemed satisfied, but explicit confirmation or follow-up details were missing."
                },
                {
                    "level_name": "Average",
                    "level_order": 3,
                    "min_score": 55,
                    "max_score": 69,
                    "description": "Partial resolution. Some progress made but issue not fully resolved, or customer satisfaction uncertain.",
                    "examples": "Agent attempted to resolve issue but solution was incomplete or customer satisfaction was unclear."
                },
                {
                    "level_name": "Poor",
                    "level_order": 4,
                    "min_score": 0,
                    "max_score": 54,
                    "description": "Issue not resolved. Customer problem remains, no clear action plan, or customer explicitly expressed dissatisfaction.",
                    "examples": "Issue was not resolved, customer remained frustrated, or no clear solution was provided."
                }
            ]
        }
    ]
    
    # Create criteria and rubric levels
    for criteria_def in criteria_definitions:
        criterion = EvaluationCriteria(
            id=str(uuid.uuid4()),
            policy_template_id=template.id,
            category_name=criteria_def["category_name"],
            weight=criteria_def["weight"],
            passing_score=criteria_def["passing_score"],
            evaluation_prompt=criteria_def["evaluation_prompt"]
        )
        db.add(criterion)
        db.flush()
        
        # Create rubric levels for this criterion
        for level_def in criteria_def["rubric_levels"]:
            rubric_level = EvaluationRubricLevel(
                id=str(uuid.uuid4()),
                criteria_id=criterion.id,
                level_name=level_def["level_name"],
                level_order=level_def["level_order"],
                min_score=level_def["min_score"],
                max_score=level_def["max_score"],
                description=level_def["description"],
                examples=level_def.get("examples")
            )
            db.add(rubric_level)
    
    db.flush()
    
    # Generate policy rules automatically
    try:
        from sqlalchemy.orm import joinedload
        
        # Reload template with criteria and rubric levels
        template_with_data = db.query(PolicyTemplate).options(
            joinedload(PolicyTemplate.evaluation_criteria).joinedload(EvaluationCriteria.rubric_levels)
        ).filter(PolicyTemplate.id == template.id).first()
        
        if template_with_data:
            # Extract policy text
            policy_parts = []
            if template_with_data.description:
                policy_parts.append(template_with_data.description)
            for criterion in template_with_data.evaluation_criteria:
                if criterion.evaluation_prompt:
                    policy_parts.append(f"{criterion.category_name}: {criterion.evaluation_prompt}")
            policy_text = "\n\n".join(policy_parts)
            
            # Extract rubric levels
            rubric_levels = {}
            for criterion in template_with_data.evaluation_criteria:
                rubric_levels[criterion.category_name] = []
                for level in criterion.rubric_levels:
                    rubric_levels[criterion.category_name].append({
                        "level_name": level.level_name,
                        "min_score": level.min_score,
                        "max_score": level.max_score,
                        "description": level.description
                    })
            
            if policy_text:
                # Generate rules automatically (skip clarification step)
                builder = PolicyRuleBuilder()
                validated_rules, metadata = builder.generate_structured_rules(
                    policy_text=policy_text,
                    clarification_answers={},  # Empty - auto-generate without clarifications
                    rubric_levels=rubric_levels
                )
                
                # Convert to dict for storage
                rules_dict = {
                    "version": 1,
                    "rules": {
                        category: [rule.dict() for rule in rules]
                        for category, rules in validated_rules.rules.items()
                    },
                    "metadata": validated_rules.metadata
                }
                
                # Save rules to template
                template.policy_rules = rules_dict
                template.policy_rules_version = 1
                template.rules_generated_at = datetime.utcnow()
                template.rules_approved_by_user_id = user_id
                template.rules_generation_method = "ai"
                template.enable_structured_rules = True
                
                logger.info(f"Generated rules for default template {template.id}")
            else:
                logger.warning(f"No policy text available for default template {template.id}")
    except Exception as e:
        logger.error(f"Failed to generate rules for default template {template.id}: {e}", exc_info=True)
        # Continue without rules - template will still be created
    
    db.commit()
    db.refresh(template)
    
    logger.info(f"Created default Standard QA Template for company {company_id}")
    return template

