# Testing Setup Guide

## Quick Test Setup (No Real Company Needed)

For testing, you need to create a test company and user. Here's how:

---

## Step 1: Run Database Migrations

Make sure your database is set up:

```bash
cd backend
alembic upgrade head
```

---

## Step 2: Create Test Company and User

### Option A: Using the Admin Script (Interactive)

```bash
cd backend
python -m app.scripts.create_admin
```

When prompted:
- **Company name**: Press Enter (uses "Default Company") or type "Test Company"
- **Email**: `test@example.com`
- **Password**: `test123` (or any password you want)
- **Full name**: Press Enter (uses "Admin User") or type "Test User"

This will:
1. ✅ Create a test company (if it doesn't exist)
2. ✅ Create a test user with admin role
3. ✅ Link user to the company
4. ✅ Print the company ID

### Option B: Using Python Directly (Quick)

Create a file `backend/create_test_user.py`:

```python
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.company import Company
from app.routes.auth import get_password_hash
import uuid

db = SessionLocal()

# Create test company
company = Company(
    id=str(uuid.uuid4()),
    company_name="Test Company",
    industry="Technology"
)
db.add(company)
db.commit()
db.refresh(company)
print(f"✅ Company created: {company.company_name} (ID: {company.id})")

# Create test user
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
print(f"✅ Company ID: {company.id}")
print(f"✅ User ID: {user.id}")
print(f"\n📝 Login credentials:")
print(f"   Email: test@example.com")
print(f"   Password: test123")

db.close()
```

Run it:
```bash
cd backend
python create_test_user.py
```

---

## Step 3: Login via API

### Using curl:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "..."
}
```

### Using the Frontend:
1. Go to `/sign-in` (if implemented)
2. Or use the Test page - it will prompt for login
3. The API client stores the token automatically

---

## Step 4: Create a Policy Template

Once logged in, create a template:

```bash
curl -X POST http://localhost:8000/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "template_name": "Test QA Template",
    "description": "Template for testing",
    "is_active": true,
    "criteria": [
      {
        "category_name": "Compliance",
        "weight": 40.0,
        "passing_score": 90,
        "evaluation_prompt": "Evaluate if the agent followed compliance guidelines."
      },
      {
        "category_name": "Empathy",
        "weight": 30.0,
        "passing_score": 70,
        "evaluation_prompt": "Assess the agent'\''s empathy and emotional intelligence."
      },
      {
        "category_name": "Resolution",
        "weight": 30.0,
        "passing_score": 80,
        "evaluation_prompt": "Determine if the customer'\''s issue was resolved."
      }
    ]
  }'
```

Or use the Policy Templates page in the UI (after logging in).

---

## Step 5: Upload and Test

1. **Login** (frontend or API)
2. **Create template** (Policy Templates page or API)
3. **Set template as active** (Policy Templates page)
4. **Upload file** (Test page)
5. **Check results** (should use your template!)

---

## What Happens Behind the Scenes

### Company ID Flow:
1. **User logs in** → JWT token contains user_id
2. **Backend gets user** → `current_user.company_id` is used
3. **Recording created** → Uses `current_user.company_id`
4. **Template lookup** → Finds template where `company_id = current_user.company_id`
5. **Evaluation** → Uses template for that company

### For Testing:
- **Company ID**: Auto-generated UUID when company is created
- **User**: Linked to company via `company_id` foreign key
- **Templates**: Linked to company via `company_id`
- **Recordings**: Linked to company via `company_id`

---

## Quick Test Script

Save this as `backend/quick_test_setup.py`:

```python
#!/usr/bin/env python3
"""Quick test setup - creates company, user, and template"""
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.policy_template import PolicyTemplate
from app.models.evaluation_criteria import EvaluationCriteria
from app.routes.auth import get_password_hash
import uuid

db = SessionLocal()

try:
    # 1. Create company
    company = Company(
        id=str(uuid.uuid4()),
        company_name="Test Company",
        industry="Technology"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    print(f"✅ Company: {company.company_name} (ID: {company.id})")
    
    # 2. Create user
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
    print(f"✅ User: {user.email}")
    
    # 3. Create template
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
    print(f"✅ Template: {template.template_name} (ID: {template.id})")
    
    # 4. Create criteria
    criteria_data = [
        {
            "category_name": "Compliance",
            "weight": 40.0,
            "passing_score": 90,
            "evaluation_prompt": "Evaluate if the agent followed compliance guidelines including required disclosures and regulatory requirements."
        },
        {
            "category_name": "Empathy",
            "weight": 30.0,
            "passing_score": 70,
            "evaluation_prompt": "Assess how well the agent acknowledged customer emotions and concerns. Look for empathetic language."
        },
        {
            "category_name": "Resolution",
            "weight": 30.0,
            "passing_score": 80,
            "evaluation_prompt": "Determine if the customer's issue was successfully resolved. Check for customer confirmation."
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
    
    db.commit()
    print(f"✅ Criteria: {len(criteria_data)} categories added")
    
    print("\n" + "="*50)
    print("✅ TEST SETUP COMPLETE!")
    print("="*50)
    print(f"\n📝 Login Credentials:")
    print(f"   Email: test@example.com")
    print(f"   Password: test123")
    print(f"\n🏢 Company ID: {company.id}")
    print(f"👤 User ID: {user.id}")
    print(f"📋 Template ID: {template.id}")
    print(f"\n🚀 Ready to test! Upload a file and it will use this template.")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    db.rollback()
finally:
    db.close()
```

Run it:
```bash
cd backend
python quick_test_setup.py
```

---

## Troubleshooting

### "No active policy template found"
- **Solution**: Create a template and set it as active
- Check: `SELECT * FROM policy_templates WHERE company_id = 'YOUR_COMPANY_ID' AND is_active = true;`

### "Invalid email or password"
- **Solution**: Make sure user exists and password is correct
- Check: `SELECT * FROM users WHERE email = 'test@example.com';`

### "User is inactive"
- **Solution**: Set `is_active = true` for the user
- Check: `UPDATE users SET is_active = true WHERE email = 'test@example.com';`

---

## Summary

**For testing, you need:**
1. ✅ One test company (any name)
2. ✅ One test user (linked to company)
3. ✅ One active template (linked to company)
4. ✅ Login with test user
5. ✅ Upload file → Uses your template!

**Company ID is automatically handled** - you don't need to know it, just make sure you're logged in!

