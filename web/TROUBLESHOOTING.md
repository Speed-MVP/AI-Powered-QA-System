# TypeScript Project Troubleshooting Guide

## Common Issues and Solutions

### 1. Missing Type Definitions

If you see errors like:
- `Cannot find module '@types/node'`
- `Cannot find name 'process'`

**Solution:**
```bash
npm install --save-dev @types/node
```

### 2. Path Alias Issues

If you see errors like:
- `Cannot find module '@/components/Layout'`
- `Module not found: @/lib/supabase`

**Solution:**
Check that `tsconfig.json` and `vite.config.ts` have matching path aliases:
- `tsconfig.json` should have `"@/*": ["./src/*"]`
- `vite.config.ts` should resolve `@` to `./src`

### 3. Environment Variables Not Found

If you see:
- `VITE_SUPABASE_URL is not defined`

**Solution:**
Create a `.env` file in the `web` directory:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 4. Type Errors After Installation

**Solution:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Or on Windows:
rmdir /s node_modules
del package-lock.json
npm install
```

### 5. Vite HMR Not Working

**Solution:**
```bash
# Clear Vite cache
rm -rf node_modules/.vite

# Or on Windows:
rmdir /s node_modules\.vite
```

### 6. TypeScript Strict Mode Issues

If you see strict mode errors, you can temporarily disable them in `tsconfig.json`:
```json
{
  "compilerOptions": {
    "strict": false,
    "noUnusedLocals": false,
    "noUnusedParameters": false
  }
}
```

## Verification Steps

1. **Check TypeScript compilation:**
   ```bash
   npx tsc --noEmit
   ```

2. **Check for linting errors:**
   ```bash
   npm run build
   ```

3. **Verify dependencies:**
   ```bash
   npm list --depth=0
   ```

## Current Project Status

✅ TypeScript compilation: **PASSING**
✅ No linting errors: **PASSING**
✅ Dependencies installed: **PASSING**

## If Issues Persist

1. Delete `node_modules` and `package-lock.json`
2. Run `npm install` fresh
3. Check Node.js version (should be 18+)
4. Clear npm cache: `npm cache clean --force`

