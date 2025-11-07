# AI-Powered QA System - Frontend

React + TypeScript + Vite frontend for the AI-Powered QA System.

## Features

- 🎨 **Supabase.com-inspired Design** - Modern, clean UI with dark/light theme support
- 📤 **File Upload** - Drag-and-drop audio/video file upload with progress tracking
- 🎯 **Theme Control** - Light, dark, and system theme modes
- 🚀 **Fast Development** - Vite for instant HMR and optimized builds
- 💾 **State Management** - Zustand for lightweight state management
- 🗄️ **Supabase Integration** - Real-time database and storage

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Supabase account and project

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
   - Create a `.env` file in the `web` directory
   - See `ENV_SETUP.md` for details

3. Set up Supabase:
   - See `SUPABASE_SETUP.md` for database and storage setup

4. Start development server:
```bash
npm run dev
```

5. Open http://localhost:5173

## Project Structure

```
web/
├── src/
│   ├── components/       # React components
│   │   └── Layout.tsx    # Main layout with navbar
│   ├── pages/            # Page components
│   │   ├── Upload.tsx    # Upload page (priority)
│   │   ├── Dashboard.tsx
│   │   ├── Results.tsx
│   │   └── ...
│   ├── lib/              # Utilities
│   │   └── supabase.ts   # Supabase client
│   ├── store/            # Zustand stores
│   │   └── themeStore.ts # Theme management
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── public/               # Static assets
├── tailwind.config.js    # Tailwind configuration
├── vite.config.ts        # Vite configuration
└── package.json
```

## Key Pages

### Upload Page (`/upload`)
- **Priority**: Fully functional
- Drag-and-drop file upload
- Progress tracking
- Error handling
- File list display

### Other Pages
- `/` - Home page
- `/dashboard` - Dashboard (placeholder)
- `/results` - Results viewer (placeholder)
- `/policy-templates` - Policy management (placeholder)
- `/pricing` - Pricing page (placeholder)
- `/features` - Features page (placeholder)
- `/sign-in` - Sign in (placeholder)

## Development

### Theme System
The app supports light, dark, and system themes. The theme preference is persisted in localStorage.

### Supabase Integration
- Storage: File uploads go to the `recordings` bucket
- Database: Recording metadata stored in the `recordings` table
- Real-time: Ready for real-time updates (to be implemented)

### Build for Production

```bash
npm run build
```

The build output will be in the `dist` directory.

## Environment Variables

Required:
- `VITE_SUPABASE_URL` - Your Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Your Supabase anon key

Optional (for future use):
- `VITE_DEEPGRAM_API_KEY`
- `VITE_ASSEMBLYAI_API_KEY`
- `VITE_GEMINI_API_KEY`
- `VITE_CLAUDE_API_KEY`

## Notes

- **No Auth Yet**: Authentication will be implemented later. The upload page uses temporary UUIDs for now.
- **Upload Page Priority**: The upload page is fully functional. Other pages are UI placeholders.
- **Storage Bucket**: Make sure to create the `recordings` bucket in Supabase Storage.
- **Database Tables**: Run migrations to create required tables (see `SUPABASE_SETUP.md`).

## Troubleshooting

See `SUPABASE_SETUP.md` for common setup issues and solutions.

