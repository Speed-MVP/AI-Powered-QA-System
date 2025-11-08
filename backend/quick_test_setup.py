#!/usr/bin/env python3
"""Quick test setup - creates company, user, and template"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.policy_template import PolicyTemplate
from app.models.evaluation_criteria import EvaluationCriteria
from app.models.evaluation_rubric_level import EvaluationRubricLevel
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    # Workaround for bcrypt 5.0.0 compatibility
    try:
        return pwd_context.hash(password)
    except ValueError as e:
        # Fallback: use bcrypt directly if passlib fails
        import bcrypt
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
import uuid

db = SessionLocal()

try:
    # 1. Create or get company
    company = db.query(Company).filter(Company.company_name == "Test Company").first()
    if not company:
        company = Company(
            id=str(uuid.uuid4()),
            company_name="Test Company",
            industry="Technology"
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        print(f"✅ Company created: {company.company_name} (ID: {company.id})")
    else:
        print(f"✅ Company exists: {company.company_name} (ID: {company.id})")
    
    # 2. Create or get user
    user = db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            company_id=company.id,
            email="test@example.com",
            password_hash=get_password_hash("test123"),
            full_name="Test User",
            role=UserRole.admin,
            is_active=True
        )
        db.add(user)
        db.commit()
        print(f"✅ User created: {user.email}")
    else:
        print(f"✅ User exists: {user.email}")
        # Update company_id in case it changed
        if user.company_id != company.id:
            user.company_id = company.id
            db.commit()
    
    # 3. Create or get template
    template = db.query(PolicyTemplate).filter(
        PolicyTemplate.company_id == company.id,
        PolicyTemplate.template_name == "Test QA Template"
    ).first()
    
    if not template:
        template = PolicyTemplate(
            id=str(uuid.uuid4()),
            company_id=company.id,
            template_name="Test QA Template",
            description="Template for testing evaluation",
            is_active=True
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        print(f"✅ Template created: {template.template_name} (ID: {template.id})")
    else:
        # Make sure it's active
        if not template.is_active:
            template.is_active = True
            db.commit()
        print(f"✅ Template exists: {template.template_name} (ID: {template.id})")
    
    # 4. Check existing criteria
    existing_criteria = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.policy_template_id == template.id
    ).all()
    
    # Check if criteria need rubric levels
    criteria_need_rubrics = []
    for crit in existing_criteria:
        existing_levels = db.query(EvaluationRubricLevel).filter(
            EvaluationRubricLevel.criteria_id == crit.id
        ).all()
        if len(existing_levels) == 0:
            criteria_need_rubrics.append(crit)
    
    if len(existing_criteria) == 0:
        # Create criteria
        criteria_data = [
            {
                "category_name": "Compliance",
                "weight": 40.0,
                "passing_score": 90,
                "evaluation_prompt": "Evaluate if the agent followed compliance guidelines including required disclosures and regulatory requirements. Score higher if all compliance protocols were met."
            },
            {
                "category_name": "Empathy",
                "weight": 30.0,
                "passing_score": 70,
                "evaluation_prompt": "Assess how well the agent acknowledged customer emotions and concerns. Look for empathetic language, active listening indicators, and appropriate responses to customer frustration."
            },
            {
                "category_name": "Resolution",
                "weight": 30.0,
                "passing_score": 80,
                "evaluation_prompt": "Determine if the customer's issue was successfully resolved. Check for customer confirmation of satisfaction, clear action plans, and follow-up commitments."
            }
        ]
        
        for crit_data in criteria_data:
            criteria = EvaluationCriteria(
                id=str(uuid.uuid4()),
                policy_template_id=template.id,
                category_name=crit_data["category_name"],
                weight=crit_data["weight"],
                passing_score=crit_data["passing_score"],
                evaluation_prompt=crit_data["evaluation_prompt"]
            )
            db.add(criteria)
            db.flush()  # Flush to get the criteria ID
            
            # Create rubric levels for this criteria
            if crit_data["category_name"] == "Compliance":
                rubric_levels = [
                    {
                        "level_name": "Excellent",
                        "level_order": 1,
                        "min_score": 90,
                        "max_score": 100,
                        "description": "All compliance protocols followed perfectly. Required disclosures made clearly. Regulatory requirements met. No violations.",
                        "examples": "Agent verified customer identity, provided all required disclosures, followed script exactly, documented everything properly."
                    },
                    {
                        "level_name": "Good",
                        "level_order": 2,
                        "min_score": 75,
                        "max_score": 89,
                        "description": "Most compliance requirements met. Minor omissions or unclear disclosures. Generally compliant with minor issues.",
                        "examples": "Agent verified identity but missed one disclosure, or provided disclosure but not clearly enough."
                    },
                    {
                        "level_name": "Average",
                        "level_order": 3,
                        "min_score": 60,
                        "max_score": 74,
                        "description": "Some compliance requirements missed. Important disclosures omitted or unclear. Moderate compliance issues.",
                        "examples": "Agent skipped identity verification, missed multiple disclosures, or failed to document properly."
                    },
                    {
                        "level_name": "Poor",
                        "level_order": 4,
                        "min_score": 40,
                        "max_score": 59,
                        "description": "Major compliance violations. Critical disclosures missing. Regulatory requirements not met. Significant risk.",
                        "examples": "No identity verification, no disclosures provided, accessing account without permission, violating privacy rules."
                    },
                    {
                        "level_name": "Unacceptable",
                        "level_order": 5,
                        "min_score": 0,
                        "max_score": 39,
                        "description": "Severe compliance failures. Multiple critical violations. Legal or regulatory risk. Complete non-compliance.",
                        "examples": "Sharing confidential information, violating data protection laws, unauthorized account access, fraud indicators."
                    }
                ]
            elif crit_data["category_name"] == "Empathy":
                rubric_levels = [
                    {
                        "level_name": "Excellent",
                        "level_order": 1,
                        "min_score": 90,
                        "max_score": 100,
                        "description": "Exceptional empathy demonstrated. Actively listened, acknowledged emotions, showed genuine care. Used empathetic language throughout.",
                        "examples": "Agent said 'I understand how frustrating this must be', validated customer feelings, showed patience, used warm tone."
                    },
                    {
                        "level_name": "Good",
                        "level_order": 2,
                        "min_score": 75,
                        "max_score": 89,
                        "description": "Good empathy shown. Acknowledged customer concerns. Generally empathetic but could be more consistent.",
                        "examples": "Agent acknowledged frustration but didn't fully validate, showed some empathy but tone was neutral."
                    },
                    {
                        "level_name": "Average",
                        "level_order": 3,
                        "min_score": 60,
                        "max_score": 74,
                        "description": "Limited empathy. Minimal acknowledgment of emotions. Functional but not empathetic.",
                        "examples": "Agent focused on solving problem but ignored emotional state, no acknowledgment of frustration."
                    },
                    {
                        "level_name": "Poor",
                        "level_order": 4,
                        "min_score": 40,
                        "max_score": 59,
                        "description": "No empathy shown. Dismissive of customer emotions. Rude or unprofessional tone. Customer feelings ignored.",
                        "examples": "Agent was dismissive, said 'that's not my problem', showed no concern for customer's situation, rude tone."
                    },
                    {
                        "level_name": "Unacceptable",
                        "level_order": 5,
                        "min_score": 0,
                        "max_score": 39,
                        "description": "Completely unempathetic. Hostile or aggressive. Blamed customer. Severe unprofessional behavior.",
                        "examples": "Agent blamed customer, was hostile, raised voice, insulted customer, showed contempt."
                    }
                ]
            elif crit_data["category_name"] == "Resolution":
                rubric_levels = [
                    {
                        "level_name": "Excellent",
                        "level_order": 1,
                        "min_score": 90,
                        "max_score": 100,
                        "description": "Issue completely resolved. Customer confirmed satisfaction. Clear action plan provided. Follow-up committed.",
                        "examples": "Customer said 'thank you, that solved it', issue fully fixed, agent confirmed resolution, offered follow-up."
                    },
                    {
                        "level_name": "Good",
                        "level_order": 2,
                        "min_score": 75,
                        "max_score": 89,
                        "description": "Issue resolved but with minor gaps. Customer mostly satisfied. Some follow-up needed.",
                        "examples": "Issue mostly resolved, customer seemed satisfied but didn't explicitly confirm, minor follow-up needed."
                    },
                    {
                        "level_name": "Average",
                        "level_order": 3,
                        "min_score": 60,
                        "max_score": 74,
                        "description": "Partial resolution. Issue partially addressed. Customer uncertain. Incomplete solution.",
                        "examples": "Issue partially fixed, customer unsure if it's resolved, no clear confirmation, solution incomplete."
                    },
                    {
                        "level_name": "Poor",
                        "level_order": 4,
                        "min_score": 40,
                        "max_score": 59,
                        "description": "Issue not resolved. Customer dissatisfied. No clear solution. Problem persists.",
                        "examples": "Issue not fixed, customer still has problem, no solution provided, customer frustrated."
                    },
                    {
                        "level_name": "Unacceptable",
                        "level_order": 5,
                        "min_score": 0,
                        "max_score": 39,
                        "description": "Complete failure to resolve. Issue worsened. Customer extremely dissatisfied. No attempt to solve.",
                        "examples": "Issue made worse, agent gave up, no solution attempted, customer left without help."
                    }
                ]
            else:
                # Default rubric for other categories
                rubric_levels = [
                    {
                        "level_name": "Excellent",
                        "level_order": 1,
                        "min_score": 90,
                        "max_score": 100,
                        "description": "Exceeds all expectations. Perfect execution. Exceptional performance.",
                        "examples": None
                    },
                    {
                        "level_name": "Good",
                        "level_order": 2,
                        "min_score": 75,
                        "max_score": 89,
                        "description": "Meets all requirements. Minor room for improvement.",
                        "examples": None
                    },
                    {
                        "level_name": "Average",
                        "level_order": 3,
                        "min_score": 60,
                        "max_score": 74,
                        "description": "Meets basic requirements but has noticeable issues.",
                        "examples": None
                    },
                    {
                        "level_name": "Poor",
                        "level_order": 4,
                        "min_score": 40,
                        "max_score": 59,
                        "description": "Significant problems. Major issues. Fails to meet key requirements.",
                        "examples": None
                    },
                    {
                        "level_name": "Unacceptable",
                        "level_order": 5,
                        "min_score": 0,
                        "max_score": 39,
                        "description": "Complete failure. Severe violations. Unprofessional behavior.",
                        "examples": None
                    }
                ]
            
            # Create rubric levels
            for level_data in rubric_levels:
                rubric_level = EvaluationRubricLevel(
                    id=str(uuid.uuid4()),
                    criteria_id=criteria.id,
                    level_name=level_data["level_name"],
                    level_order=level_data["level_order"],
                    min_score=level_data["min_score"],
                    max_score=level_data["max_score"],
                    description=level_data["description"],
                    examples=level_data.get("examples")
                )
                db.add(rubric_level)
        
        db.commit()
        print(f"✅ Criteria created: {len(criteria_data)} categories with rubric levels added")
    else:
        print(f"✅ Criteria exists: {len(existing_criteria)} categories")
        
        # Add rubric levels to existing criteria that don't have them
        if len(criteria_need_rubrics) > 0:
            print(f"📝 Adding rubric levels to {len(criteria_need_rubrics)} existing criteria...")
            for crit in criteria_need_rubrics:
                # Use same rubric logic as above
                if crit.category_name == "Compliance":
                    rubric_levels = [
                        {
                            "level_name": "Excellent",
                            "level_order": 1,
                            "min_score": 90,
                            "max_score": 100,
                            "description": "All compliance protocols followed perfectly. Required disclosures made clearly. Regulatory requirements met. No violations.",
                            "examples": "Agent verified customer identity, provided all required disclosures, followed script exactly, documented everything properly."
                        },
                        {
                            "level_name": "Good",
                            "level_order": 2,
                            "min_score": 75,
                            "max_score": 89,
                            "description": "Most compliance requirements met. Minor omissions or unclear disclosures. Generally compliant with minor issues.",
                            "examples": "Agent verified identity but missed one disclosure, or provided disclosure but not clearly enough."
                        },
                        {
                            "level_name": "Average",
                            "level_order": 3,
                            "min_score": 60,
                            "max_score": 74,
                            "description": "Some compliance requirements missed. Important disclosures omitted or unclear. Moderate compliance issues.",
                            "examples": "Agent skipped identity verification, missed multiple disclosures, or failed to document properly."
                        },
                        {
                            "level_name": "Poor",
                            "level_order": 4,
                            "min_score": 40,
                            "max_score": 59,
                            "description": "Major compliance violations. Critical disclosures missing. Regulatory requirements not met. Significant risk.",
                            "examples": "No identity verification, no disclosures provided, accessing account without permission, violating privacy rules."
                        },
                        {
                            "level_name": "Unacceptable",
                            "level_order": 5,
                            "min_score": 0,
                            "max_score": 39,
                            "description": "Severe compliance failures. Multiple critical violations. Legal or regulatory risk. Complete non-compliance.",
                            "examples": "Sharing confidential information, violating data protection laws, unauthorized account access, fraud indicators."
                        }
                    ]
                elif crit.category_name == "Empathy":
                    rubric_levels = [
                        {
                            "level_name": "Excellent",
                            "level_order": 1,
                            "min_score": 90,
                            "max_score": 100,
                            "description": "Exceptional empathy demonstrated. Actively listened, acknowledged emotions, showed genuine care. Used empathetic language throughout.",
                            "examples": "Agent said 'I understand how frustrating this must be', validated customer feelings, showed patience, used warm tone."
                        },
                        {
                            "level_name": "Good",
                            "level_order": 2,
                            "min_score": 75,
                            "max_score": 89,
                            "description": "Good empathy shown. Acknowledged customer concerns. Generally empathetic but could be more consistent.",
                            "examples": "Agent acknowledged frustration but didn't fully validate, showed some empathy but tone was neutral."
                        },
                        {
                            "level_name": "Average",
                            "level_order": 3,
                            "min_score": 60,
                            "max_score": 74,
                            "description": "Limited empathy. Minimal acknowledgment of emotions. Functional but not empathetic.",
                            "examples": "Agent focused on solving problem but ignored emotional state, no acknowledgment of frustration."
                        },
                        {
                            "level_name": "Poor",
                            "level_order": 4,
                            "min_score": 40,
                            "max_score": 59,
                            "description": "No empathy shown. Dismissive of customer emotions. Rude or unprofessional tone. Customer feelings ignored.",
                            "examples": "Agent was dismissive, said 'that's not my problem', showed no concern for customer's situation, rude tone."
                        },
                        {
                            "level_name": "Unacceptable",
                            "level_order": 5,
                            "min_score": 0,
                            "max_score": 39,
                            "description": "Completely unempathetic. Hostile or aggressive. Blamed customer. Severe unprofessional behavior.",
                            "examples": "Agent blamed customer, was hostile, raised voice, insulted customer, showed contempt."
                        }
                    ]
                elif crit.category_name == "Resolution":
                    rubric_levels = [
                        {
                            "level_name": "Excellent",
                            "level_order": 1,
                            "min_score": 90,
                            "max_score": 100,
                            "description": "Issue completely resolved. Customer confirmed satisfaction. Clear action plan provided. Follow-up committed.",
                            "examples": "Customer said 'thank you, that solved it', issue fully fixed, agent confirmed resolution, offered follow-up."
                        },
                        {
                            "level_name": "Good",
                            "level_order": 2,
                            "min_score": 75,
                            "max_score": 89,
                            "description": "Issue resolved but with minor gaps. Customer mostly satisfied. Some follow-up needed.",
                            "examples": "Issue mostly resolved, customer seemed satisfied but didn't explicitly confirm, minor follow-up needed."
                        },
                        {
                            "level_name": "Average",
                            "level_order": 3,
                            "min_score": 60,
                            "max_score": 74,
                            "description": "Partial resolution. Issue partially addressed. Customer uncertain. Incomplete solution.",
                            "examples": "Issue partially fixed, customer unsure if it's resolved, no clear confirmation, solution incomplete."
                        },
                        {
                            "level_name": "Poor",
                            "level_order": 4,
                            "min_score": 40,
                            "max_score": 59,
                            "description": "Issue not resolved. Customer dissatisfied. No clear solution. Problem persists.",
                            "examples": "Issue not fixed, customer still has problem, no solution provided, customer frustrated."
                        },
                        {
                            "level_name": "Unacceptable",
                            "level_order": 5,
                            "min_score": 0,
                            "max_score": 39,
                            "description": "Complete failure to resolve. Issue worsened. Customer extremely dissatisfied. No attempt to solve.",
                            "examples": "Issue made worse, agent gave up, no solution attempted, customer left without help."
                        }
                    ]
                else:
                    # Default rubric for other categories
                    rubric_levels = [
                        {
                            "level_name": "Excellent",
                            "level_order": 1,
                            "min_score": 90,
                            "max_score": 100,
                            "description": "Exceeds all expectations. Perfect execution. Exceptional performance.",
                            "examples": None
                        },
                        {
                            "level_name": "Good",
                            "level_order": 2,
                            "min_score": 75,
                            "max_score": 89,
                            "description": "Meets all requirements. Minor room for improvement.",
                            "examples": None
                        },
                        {
                            "level_name": "Average",
                            "level_order": 3,
                            "min_score": 60,
                            "max_score": 74,
                            "description": "Meets basic requirements but has noticeable issues.",
                            "examples": None
                        },
                        {
                            "level_name": "Poor",
                            "level_order": 4,
                            "min_score": 40,
                            "max_score": 59,
                            "description": "Significant problems. Major issues. Fails to meet key requirements.",
                            "examples": None
                        },
                        {
                            "level_name": "Unacceptable",
                            "level_order": 5,
                            "min_score": 0,
                            "max_score": 39,
                            "description": "Complete failure. Severe violations. Unprofessional behavior.",
                            "examples": None
                        }
                    ]
                
                # Create rubric levels
                for level_data in rubric_levels:
                    rubric_level = EvaluationRubricLevel(
                        id=str(uuid.uuid4()),
                        criteria_id=crit.id,
                        level_name=level_data["level_name"],
                        level_order=level_data["level_order"],
                        min_score=level_data["min_score"],
                        max_score=level_data["max_score"],
                        description=level_data["description"],
                        examples=level_data.get("examples")
                    )
                    db.add(rubric_level)
            
            db.commit()
            print(f"✅ Added rubric levels to {len(criteria_need_rubrics)} criteria")
    
    print("\n" + "="*50)
    print("✅ TEST SETUP COMPLETE!")
    print("="*50)
    print(f"\n📝 Login Credentials:")
    print(f"   Email: test@example.com")
    print(f"   Password: test123")
    print(f"\n🏢 Company ID: {company.id}")
    print(f"👤 User ID: {user.id}")
    print(f"📋 Template ID: {template.id}")
    print(f"📊 Active Template: {template.template_name}")
    print(f"\n🚀 Ready to test! Login and upload a file.")
    print(f"   The file will be evaluated using: {template.template_name}")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

