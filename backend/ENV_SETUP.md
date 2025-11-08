# Environment Variables Setup Guide

## GCP Credentials in .env File

Instead of using a JSON file for GCP credentials, you can put them directly in your `.env` file.

### Required .env Variables

```env
# Database
DATABASE_URL=postgresql://user:password@ep-yellow-firefly-123456.us-east-1.postgres.vercel.app/neon_db

# GCP
GCP_PROJECT_ID=ai-qa-system
GCP_BUCKET_NAME=ai_qa_recording
GCP_CLIENT_EMAIL=ai-qa-backend@ai-qa-system.iam.gserviceaccount.com
GCP_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCw90LpYoG4QfBD\nXwkOk5Eo5EEFNiJZS1ajISjwf1VF9C6P7/0t0TS4YEMAVfadQk5SYOuEcuOrwqp0\n8xBta6CJQqI7eF5SEeLNuRdhxSQHl06Uch5ShSL0H5MxqRASiDHVQPp3nDBINyP6\nIQFuTv4q2UukPHQjuRlRcVhb0caDz6TfxT7Rk8eBSKvZWHvyAJWVnMI5NJEejtYQ\nLQUvrhAw/A8s+QENf0QFqH3TIQk1tz10KLaZZSKJD2SszBPSKGGCmEcv42WjPzX3\nKGSrUMPm+vJQ5qTHEhUYWPLDrjmKELN0dtd0xfYvqBESc3dH++UaEb7Pki+pElsh\nPPFH0NaTAgMBAAECggEABeLbkTguKk3w/IM7OO9Obia4XJIPV2xfC30zMFuT5Ta4\n+NmrLZUv3t3tLJiMexOYHZiHDOy3u3eBW616N9ANaie7pWrWwiC15mgfhtby9+Rl\nuk7wJeVWC/qYVuljFScVMZ0XXXp9WHR7+xdMl0tJnCcpI1fZD9F8olOhlyj83rPp\nuod4yTqbMDa86KP3Z+RWhk0GiSFHfzEsv3sH/qNjMped2Uc1AqS7sfTExvT1339v\nTSEmZTxrhkLaJhHzx8AEsX5sZR68Cb+z6Ytmeh+H9z6FD3Zjhs8lDaLdprHzSTqk\nulW5+yz/nXLC7jTJd2CRVMdUgqtliSBr1ToDqrfpvQKBgQDfp6e76hOvSOU0YK5b\n7pTtjCw8aDHdxCrtzNvIef7Dt7bQrb+jGWEF1taIKlx0M7Cxvhjauteft8dzE6B1\nuLE+XTJuYRjF00VNWD+c7yPsRcSswy+qVJCEubIqKsabgR12sXgxo1/7fznY+79s\nnLqLuCWbUss34ejXDBcFnV7r3QKBgQDKjwtXOx+5gt6HIxEHHfRRDU8i0EIc+fVZ\n7Nro+N48FS5oxWynXWkaK8w1sgtZG8XDvkBBslUHo/xQMCx+nORfWRFYz4jICXzK\ngDBo7AqEuSDiKlB4xZsUjRpEQ3pHZyj/Sl6NdKKN1zBoQ33BDvTjYVJVvY+STu/W\nRw5cJmGdLwKBgDjOlrYOIG3XMBB7tg23rbAgeGPnezL+zoCUFgb3pZQEp7SdTR2a\nJqCbDuaLC+yf7HNY+2sjJf11an16MLl17d8PQO30T5x/qwyYK6AqxY8PsYLIGOVE\nkWiE2hIHx2ZcByXMseC5xHlWuVS5rMdjj6ZJYZPwFZneEYv9kCNm82MpAoGAdYN5\nW9kkNZbUDOhuJ4fcRu2GvLa/tFnbWplMAx7mp0rOiuAGgi5yHEnOhlRNuxuep0oH\ns1WHeRBNACSCm83fu+VLaA+21f6TFFQ8QZK3I3rXtf5Ag2B48PpPg8z18tjJcxot\nMrm42LtADS0ils9biVLb1nxL/+ClydWdYh6uQOcCgYEAqfIlE8v6KT6Mf6yTPwhP\njujuMrFzle3b+B7cQMxtN7FZThrcSgfIYDTWKrb7zUXFw1DxsgtHhtaC5Kq8MfgB\nDUj/8IlircRh/yn7vjUo5WKSu7lNkzfjlaPfo5XMjRlcVeo0wc+a4q/CSCbkO8gQ\nq+KSi3STrn6lF7KmDLEaHWs=\n-----END PRIVATE KEY-----"

# Authentication
JWT_SECRET=your-super-secret-key-change-this-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# External APIs
DEEPGRAM_API_KEY=your-deepgram-key
ASSEMBLYAI_API_KEY=your-assemblyai-key
GEMINI_API_KEY=your-gemini-key
# OR
CLAUDE_API_KEY=your-claude-key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourcompany.com

# Server
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Important Notes:

1. **GCP_PRIVATE_KEY**: The private key must be in quotes and use `\n` for newlines (the code will convert them automatically)
2. **GCP_CLIENT_EMAIL**: Use the exact client_email from your service account
3. **GCP_PROJECT_ID**: Your GCP project ID
4. **GCP_BUCKET_NAME**: The name of your Cloud Storage bucket

### Your Specific Values:

Based on your GCP credentials:

```env
GCP_PROJECT_ID=ai-qa-system
GCP_BUCKET_NAME=ai_qa_recording
GCP_CLIENT_EMAIL=ai-qa-backend@ai-qa-system.iam.gserviceaccount.com
GCP_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCw90LpYoG4QfBD\nXwkOk5Eo5EEFNiJZS1ajISjwf1VF9C6P7/0t0TS4YEMAVfadQk5SYOuEcuOrwqp0\n8xBta6CJQqI7eF5SEeLNuRdhxSQHl06Uch5ShSL0H5MxqRASiDHVQPp3nDBINyP6\nIQFuTv4q2UukPHQjuRlRcVhb0caDz6TfxT7Rk8eBSKvZWHvyAJWVnMI5NJEejtYQ\nLQUvrhAw/A8s+QENf0QFqH3TIQk1tz10KLaZZSKJD2SszBPSKGGCmEcv42WjPzX3\nKGSrUMPm+vJQ5qTHEhUYWPLDrjmKELN0dtd0xfYvqBESc3dH++UaEb7Pki+pElsh\nPPFH0NaTAgMBAAECggEABeLbkTguKk3w/IM7OO9Obia4XJIPV2xfC30zMFuT5Ta4\n+NmrLZUv3t3tLJiMexOYHZiHDOy3u3eBW616N9ANaie7pWrWwiC15mgfhtby9+Rl\nuk7wJeVWC/qYVuljFScVMZ0XXXp9WHR7+xdMl0tJnCcpI1fZD9F8olOhlyj83rPp\nuod4yTqbMDa86KP3Z+RWhk0GiSFHfzEsv3sH/qNjMped2Uc1AqS7sfTExvT1339v\nTSEmZTxrhkLaJhHzx8AEsX5sZR68Cb+z6Ytmeh+H9z6FD3Zjhs8lDaLdprHzSTqk\nulW5+yz/nXLC7jTJd2CRVMdUgqtliSBr1ToDqrfpvQKBgQDfp6e76hOvSOU0YK5b\n7pTtjCw8aDHdxCrtzNvIef7Dt7bQrb+jGWEF1taIKlx0M7Cxvhjauteft8dzE6B1\nuLE+XTJuYRjF00VNWD+c7yPsRcSswy+qVJCEubIqKsabgR12sXgxo1/7fznY+79s\nnLqLuCWbUss34ejXDBcFnV7r3QKBgQDKjwtXOx+5gt6HIxEHHfRRDU8i0EIc+fVZ\n7Nro+N48FS5oxWynXWkaK8w1sgtZG8XDvkBBslUHo/xQMCx+nORfWRFYz4jICXzK\ngDBo7AqEuSDiKlB4xZsUjRpEQ3pHZyj/Sl6NdKKN1zBoQ33BDvTjYVJVvY+STu/W\nRw5cJmGdLwKBgDjOlrYOIG3XMBB7tg23rbAgeGPnezL+zoCUFgb3pZQEp7SdTR2a\nJqCbDuaLC+yf7HNY+2sjJf11an16MLl17d8PQO30T5x/qwyYK6AqxY8PsYLIGOVE\nkWiE2hIHx2ZcByXMseC5xHlWuVS5rMdjj6ZJYZPwFZneEYv9kCNm82MpAoGAdYN5\nW9kkNZbUDOhuJ4fcRu2GvLa/tFnbWplMAx7mp0rOiuAGgi5yHEnOhlRNuxuep0oH\ns1WHeRBNACSCm83fu+VLaA+21f6TFFQ8QZK3I3rXtf5Ag2B48PpPg8z18tjJcxot\nMrm42LtADS0ils9biVLb1nxL/+ClydWdYh6uQOcCgYEAqfIlE8v6KT6Mf6yTPwhP\njujuMrFzle3b+B7cQMxtN7FZThrcSgfIYDTWKrb7zUXFw1DxsgtHhtaC5Kq8MfgB\nDUj/8IlircRh/yn7vjUo5WKSu7lNkzfjlaPfo5XMjRlcVeo0wc+a4q/CSCbkO8gQ\nq+KSi3STrn6lF7KmDLEaHWs=\n-----END PRIVATE KEY-----"
```

Make sure to:
- Keep the private key in quotes
- Use `\n` for line breaks (not actual newlines)
- Replace the other placeholder values with your actual credentials

