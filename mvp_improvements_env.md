# MVP Evaluation Improvements - Environment Variables

## New Environment Variables Added

### Cost Optimization Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_EXPENSIVE_FEATURES` | boolean | `false` | Controls expensive AI features like RAG retrieval and human review examples. Set to `true` when budget allows for enhanced evaluation quality. |
| `MAX_TOKENS_PER_EVALUATION` | integer | `4000` | Maximum token budget per evaluation. Limits prompt + response length to control costs. Recommended: 4000 for cost-efficiency, 6000+ for quality. |
| `TOKEN_COST_THRESHOLD` | float | `0.01` | Cost threshold in USD for evaluation alerts. Triggers warning logs when individual evaluations exceed this amount (e.g., `0.01` = $0.01 per evaluation). |

### Usage Examples

```bash
# Cost-optimized MVP settings (recommended for startups)
ENABLE_EXPENSIVE_FEATURES=false
MAX_TOKENS_PER_EVALUATION=4000
TOKEN_COST_THRESHOLD=0.01

# Full-featured production settings (higher cost)
ENABLE_EXPENSIVE_FEATURES=true
MAX_TOKENS_PER_EVALUATION=6000
TOKEN_COST_THRESHOLD=0.05
```

### Cost Impact

- **Basic mode** (`ENABLE_EXPENSIVE_FEATURES=false`): ~$0.003-0.005 per evaluation
- **Full features** (`ENABLE_EXPENSIVE_FEATURES=true`): ~$0.01-0.02 per evaluation
- **Token limits** prevent runaway costs from long transcripts
- **Cost threshold** alerts help monitor budget usage
