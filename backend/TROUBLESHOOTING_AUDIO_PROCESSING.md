# Troubleshooting Audio Processing Issues

## Audio Processing Taking Too Long or Hanging

### Problem
Audio files taking >2 minutes to process or completely hanging during processing.

### Root Cause
The Phase 2 Forced Alignment feature uses Whisper for word-level timestamps, which is computationally expensive for longer audio files.

### Quick Fix (Disable Alignment Temporarily)

1. Run the disable script:
   ```bash
   cd backend
   python disable_alignment.py
   ```

2. Restart your server:
   ```bash
   # Stop current server (Ctrl+C)
   # Then restart
   uvicorn app.main:app --reload
   ```

### Configuration Options

Add these to your `.env` file for fine-grained control:

```env
# Disable alignment completely (fastest processing)
ENABLE_ALIGNMENT=false

# Or configure alignment timeouts
ENABLE_ALIGNMENT=true
ALIGNMENT_TIMEOUT_SECONDS=60        # Max time for alignment (seconds)
ALIGNMENT_MAX_DURATION_SECONDS=120  # Skip alignment for files longer than this (seconds)
```

### Performance Comparison

| Setting | ~30s Audio | ~2min Audio | ~5min Audio | Notes |
|---------|------------|-------------|-------------|-------|
| `ENABLE_ALIGNMENT=false` | ~15s | ~25s | ~45s | Fastest, uses Deepgram timestamps only |
| `ENABLE_ALIGNMENT=true` (default) | ~45s | ~90s | ~180s+ | Slower but more precise timestamps |
| Long files auto-skip | ~45s | ~45s | ~45s | Skips alignment for files >3min |

### Advanced Troubleshooting

1. **Check GPU Memory** (if using CUDA):
   ```bash
   nvidia-smi  # Check GPU memory usage
   ```

2. **Monitor Logs**:
   - Look for "Starting alignment for X.Xs audio file"
   - "Alignment timed out after Xs"
   - "Forced alignment completed with X segments"

3. **Test with Small Files First**:
   - Upload 10-30 second audio files to verify basic functionality
   - Gradually test with longer files

### When to Re-enable Alignment

Re-enable alignment when you need:
- Precise word-level timestamps for advanced analysis
- Better alignment between transcription and sentiment analysis
- Improved accuracy for compliance checking

### Alternative Solutions

For production deployments:
1. **Batch Processing**: Process audio files asynchronously in background jobs
2. **Queue System**: Use Redis/Celery for queuing long-running tasks
3. **Scaling**: Deploy alignment service as separate microservice
4. **Caching**: Cache alignment results for frequently processed files

### Phase 4 Optimizations (Future)

The final Phase 4 implementation will include:
- Hybrid Gemini processing (Flash for fast eval, Pro for complex cases)
- Batch inference systems
- Enterprise-grade scaling optimizations
