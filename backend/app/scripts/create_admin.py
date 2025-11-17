"""
Script to create admin user
Usage: python -m app.scripts.create_admin
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.company import Company
from app.routes.auth import get_password_hash
from app.services.template_seeder import seed_default_template
import uuid


def create_admin():
    """Create admin user and company"""
    db = SessionLocal()
    try:
        # Get or create company
        company_name = input("Enter company name (or press Enter for 'Default Company'): ").strip()
        if not company_name:
            company_name = "Default Company"
        
        company = db.query(Company).filter(Company.company_name == company_name).first()
        if not company:
            company = Company(
                id=str(uuid.uuid4()),
                company_name=company_name,
                industry="Technology"
            )
            db.add(company)
            db.commit()
            db.refresh(company)
            print(f"Created company: {company.company_name} (ID: {company.id})")
        else:
            print(f"Using existing company: {company.company_name} (ID: {company.id})")
        
        # Get user details
        email = input("Enter admin email: ").strip()
        if not email:
            print("Email is required")
            return
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User with email {email} already exists")
            return
        
        password = input("Enter admin password: ").strip()
        if not password:
            print("Password is required")
            return
        
        full_name = input("Enter admin full name (or press Enter for 'Admin User'): ").strip()
        if not full_name:
            full_name = "Admin User"
        
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            company_id=company.id,
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role=UserRole.admin,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Seed default Standard QA Template for the company
        try:
            seed_default_template(company.id, admin_user.id, db)
            print(f"✓ Default Standard QA Template created successfully with 5 pre-configured criteria!")
        except Exception as e:
            print(f"Warning: Failed to create default template: {e}")
            # Don't fail the entire process if template creation fails
        
        print(f"\nAdmin user created successfully!")
        print(f"Email: {email}")
        print(f"Company: {company.company_name}")
        print(f"Role: {admin_user.role.value}")
        
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()

