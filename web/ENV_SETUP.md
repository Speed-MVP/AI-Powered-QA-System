# Environment Variables Setup

Create a `.env` file in the `web` directory with the following content:

```env
# Supabase Configuration
VITE_SUPABASE_URL=https://wbusunnmiwhztkbedllf.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndidXN1bm5taXdoenRrYmVkbGxmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI1Mzc0MTQsImV4cCI6MjA3ODExMzQxNH0.Ka7BSX5BdtrA_yQYgjV8tQ6JkJWpWYx7r23dRINnkrI

# API Keys (Optional for now - will be used in Edge Functions)
# VITE_DEEPGRAM_API_KEY=your-deepgram-api-key
# VITE_ASSEMBLYAI_API_KEY=your-assemblyai-api-key
# VITE_GEMINI_API_KEY=your-gemini-api-key
# VITE_CLAUDE_API_KEY=your-claude-api-key
```

## Instructions

1. Create a file named `.env` in the `web` directory
2. Copy the content above into the file
3. Uncomment and add API keys when you're ready to use them (for Edge Functions)

## Note

The Supabase URL and Anon Key are already configured above. These are public keys and safe to use in the frontend.

