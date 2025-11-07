# Supabase Setup Instructions

## Prerequisites

1. Create a Supabase account at https://supabase.com
2. Create a new project (or use the provided project URL)

## Required Setup Steps

### 1. Create Storage Bucket

1. Go to your Supabase project dashboard
2. Navigate to **Storage** in the sidebar
3. Click **New bucket**
4. Name it: `recordings`
5. Make it **Public** (or configure RLS policies if you prefer private)
6. Click **Create bucket**

### 2. Set Up Database Tables

You need to create the database tables. See `DEVELOPMENT.md` for migration files, or run:

```sql
-- Create recordings table (simplified version for now)
CREATE TABLE IF NOT EXISTS recordings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID,
  uploaded_by_user_id UUID,
  file_name VARCHAR(255) NOT NULL,
  file_url TEXT NOT NULL,
  duration_seconds INTEGER,
  status VARCHAR(50) DEFAULT 'queued',
  uploaded_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP,
  policy_template_id UUID
);

-- Enable RLS (Row Level Security)
ALTER TABLE recordings ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows all operations for now (you'll restrict this later with auth)
CREATE POLICY "Allow all for now" ON recordings
  FOR ALL
  USING (true)
  WITH CHECK (true);
```

### 3. Environment Variables

Create a `.env` file in the `web` directory:

```env
VITE_SUPABASE_URL=https://wbusunnmiwhztkbedllf.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndidXN1bm5taXdoenRrYmVkbGxmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI1Mzc0MTQsImV4cCI6MjA3ODExMzQxNH0.Ka7BSX5BdtrA_yQYgjV8tQ6JkJWpWYx7r23dRINnkrI
```

## Testing the Upload

1. Start the dev server: `npm run dev`
2. Navigate to http://localhost:5173/upload
3. Try uploading a test audio file
4. Check the Supabase dashboard to verify:
   - File appears in Storage → recordings bucket
   - Record appears in Table Editor → recordings table

## Troubleshooting

### "Bucket not found" error
- Make sure you created the `recordings` bucket in Storage
- Check that the bucket name matches exactly (case-sensitive)

### "Table does not exist" error
- Run the SQL migration above in the Supabase SQL Editor
- Or follow the full migration files in `DEVELOPMENT.md`

### Upload fails silently
- Check browser console for errors
- Check Supabase logs in the dashboard
- Verify your API keys are correct in `.env`

