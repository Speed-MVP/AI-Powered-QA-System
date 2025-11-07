# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### 1. Install Dependencies
```bash
cd web
npm install
```

### 2. Create `.env` File
Create a file named `.env` in the `web` directory:

```env
VITE_SUPABASE_URL=https://wbusunnmiwhztkbedllf.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndidXN1bm5taXdoenRrYmVkbGxmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI1Mzc0MTQsImV4cCI6MjA3ODExMzQxNH0.Ka7BSX5BdtrA_yQYgjV8tQ6JkJWpWYx7r23dRINnkrI
```

### 3. Set Up Supabase (One-Time Setup)

#### Create Storage Bucket
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to **Storage** → **New bucket**
4. Name: `recordings`
5. Make it **Public**
6. Click **Create**

#### Create Database Table
1. Go to **SQL Editor** in Supabase dashboard
2. Run this SQL:

```sql
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

ALTER TABLE recordings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for now" ON recordings
  FOR ALL
  USING (true)
  WITH CHECK (true);
```

### 4. Start Development Server
```bash
npm run dev
```

### 5. Test Upload
1. Open http://localhost:5173/upload
2. Drag and drop an audio file (MP3, WAV, etc.)
3. Watch it upload! ✅

## 🎨 Features

- ✅ **Upload Page** - Fully functional file upload
- ✅ **Theme Toggle** - Light/Dark/System themes
- ✅ **Modern UI** - Supabase.com-inspired design
- ✅ **Responsive** - Works on all devices
- 🚧 **Other Pages** - UI placeholders (to be implemented)

## 📁 Project Structure

```
web/
├── src/
│   ├── pages/Upload.tsx    ← Priority: Fully functional
│   ├── components/Layout.tsx
│   ├── lib/supabase.ts
│   └── store/themeStore.ts
├── .env                    ← Create this file
└── package.json
```

## 🔧 Troubleshooting

**"Bucket not found" error?**
→ Create the `recordings` bucket in Supabase Storage

**"Table does not exist" error?**
→ Run the SQL migration above

**Upload not working?**
→ Check browser console and Supabase logs

## 📚 Next Steps

1. Set up authentication (when ready)
2. Implement Edge Functions for processing
3. Build out Dashboard and Results pages
4. Add real-time updates

## 📖 More Info

- See `README.md` for detailed documentation
- See `SUPABASE_SETUP.md` for Supabase configuration
- See `DEVELOPMENT.md` for development guidelines

