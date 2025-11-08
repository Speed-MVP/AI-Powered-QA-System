# Company ID for Testing - Explained

## Quick Answer

**You don't need to worry about company_id!** It's automatically handled when you:
1. Create a test user (which gets a company_id)
2. Login with that user
3. Upload files (uses your user's company_id automatically)

---

## How Company ID Works

### The Flow:

```
1. Create Test Company
   ↓
   Company ID: "abc-123-def-456" (auto-generated UUID)
   
2. Create Test User
   ↓
   User.company_id = "abc-123-def-456" (linked to company)
   
3. User Logs In
   ↓
   JWT token contains user_id
   Backend gets user → finds user.company_id
   
4. Upload File
   ↓
   Recording.company_id = current_user.company_id (automatic!)
   
5. Process Recording
   ↓
   Backend finds template where:
   template.company_id = recording.company_id
   (Uses YOUR company's template!)
```

---

## For Testing: Quick Setup

### Step 1: Run Setup Script

```bash
cd backend
python quick_test_setup.py
```

This creates:
- ✅ Test Company (auto-generated ID)
- ✅ Test User (email: `test@example.com`, password: `test123`)
- ✅ Test Template (with 3 criteria)
- ✅ All linked together automatically!

### Step 2: Login

Go to `/sign-in` and login with:
- Email: `test@example.com`
- Password: `test123`

### Step 3: Upload File

Go to `/test` and upload a file. The system automatically:
- Uses your user's company_id
- Finds your company's active template
- Evaluates using your template's criteria

---

## What Gets Created

### Company:
```json
{
  "id": "abc-123-def-456",  // ← This is the company_id
  "company_name": "Test Company",
  "industry": "Technology"
}
```

### User:
```json
{
  "id": "user-123",
  "company_id": "abc-123-def-456",  // ← Links to company
  "email": "test@example.com",
  "role": "admin"
}
```

### Template:
```json
{
  "id": "template-123",
  "company_id": "abc-123-def-456",  // ← Links to company
  "template_name": "Test QA Template",
  "is_active": true
}
```

### Recording (when you upload):
```json
{
  "id": "recording-123",
  "company_id": "abc-123-def-456",  // ← Auto-set from user!
  "file_name": "test.mp3",
  "status": "queued"
}
```

---

## Important Points

1. **Company ID is Auto-Generated**: You don't need to know or set it manually
2. **Users Belong to Companies**: Each user has a `company_id` (required)
3. **Templates are Company-Specific**: Templates belong to a company
4. **Recordings Use User's Company**: When you upload, it uses your user's company_id
5. **Templates are Isolated**: Each company only sees their own templates

---

## Testing Without Real Company

The system is designed for multi-tenant use (multiple companies), but for testing:

1. **Create a test company** (any name - "Test Company")
2. **Create a test user** (linked to that company)
3. **Create templates** (they'll be linked to that company)
4. **Login and test** (everything uses that company automatically)

**No real company needed!** Just use "Test Company" for all testing.

---

## Common Questions

### Q: Do I need to know the company_id?
**A:** No! It's handled automatically. When you login, the backend knows your company_id.

### Q: Can I use multiple companies for testing?
**A:** Yes! Create multiple companies and users. Each user's uploads will use their company's templates.

### Q: What if I don't have a template?
**A:** The setup script creates one automatically. Or create one via the Policy Templates page.

### Q: What if I get "No active policy template found"?
**A:** Make sure:
1. You're logged in
2. A template exists for your company
3. The template is set to `is_active = true`

---

## Summary

**For testing:**
1. Run `python backend/quick_test_setup.py`
2. Login with `test@example.com` / `test123`
3. Upload a file
4. Everything works automatically!

**Company ID is handled behind the scenes** - you don't need to worry about it! 🎉

