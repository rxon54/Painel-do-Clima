# LLM Integration Update: OpenTelemetry Migration

## Summary of Changes

This update migrates the Painel do Clima LLM integration from the Langfuse Python SDK to Langfuse's OpenTelemetry integration for better observability and standard compliance.

## Key Changes Made

### 1. Updated `backend/generate_narratives.py`
- **Removed**: Direct Langfuse Python SDK imports (`from langfuse import observe, langfuse_context`)
- **Updated**: LLM configuration to use OpenTelemetry-based observability
- **Simplified**: Observability setup now handled automatically via LiteLLM callbacks
- **Added**: Metadata and tags to LLM calls for better tracing
- **Improved**: Error handling and null checking for LLM responses

### 2. Updated `config.yaml`
- **Fixed**: Model name from `openai/gpt-4.1` to `openai/gpt-4o-mini` (valid model)
- **Enabled**: Observability by default (`enabled: true`)
- **Added**: Comment indicating OpenTelemetry-based approach

### 3. Updated `requirements.txt`
- **Added**: OpenTelemetry dependencies for Langfuse integration:
  - `opentelemetry-api`
  - `opentelemetry-sdk`
  - `opentelemetry-instrumentation`

### 4. Updated Documentation
- **README.md**: Updated LLM setup instructions to mention OpenTelemetry integration
- **.github/copilot-instructions.md**: Updated debugging guidance for OpenTelemetry approach

### 5. Added Test Script
- **Created**: `backend/test_llm_integration.py` for validating the integration
- **Features**: Tests configuration loading, API key detection, and LLM calls
- **Validation**: Confirms OpenTelemetry observability is working

## Migration Benefits

### Before (Python SDK)
- Manual trace management with decorators
- Explicit context updates required
- More complex error handling
- Additional SDK-specific imports

### After (OpenTelemetry)
- Automatic trace creation via LiteLLM callbacks
- Standard OpenTelemetry compliance
- Simplified code with metadata/tags approach
- Better integration with observability ecosystem
- Future-proof for other observability providers

## How to Use

### 1. Set Environment Variables
```bash
# LLM Provider (choose one)
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"  # Alternative
export GOOGLE_API_KEY="your-key"     # Alternative

# Langfuse Observability (optional but recommended)
export LANGFUSE_PUBLIC_KEY="your-public-key"
export LANGFUSE_SECRET_KEY="your-secret-key"
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

### 2. Test the Integration
```bash
cd /home/rxon/projects/adaptabrasil
python backend/test_llm_integration.py
```

### 3. Generate Narratives
```bash
# Generate for a specific city
python backend/generate_narratives.py 5310 PR data/LLM data/LLM_processed
```

## Observability Features

### Automatic Tracing
- All LLM calls are automatically traced via OpenTelemetry
- Traces include metadata: component_type, model, temperature
- Failed calls are automatically logged with error details

### Langfuse Dashboard
- View all LLM calls, costs, and performance metrics
- Debug failed generations with full context
- Monitor token usage and response times
- Compare different models and prompts

## Configuration Options

### LLM Models (examples)
- `openai/gpt-4o-mini` (recommended for cost)
- `openai/gpt-4` (higher quality)
- `anthropic/claude-3-sonnet` (alternative provider)
- `gemini/gemini-1.5-pro` (Google's model)

### Observability Settings
```yaml
observability:
  enabled: true  # Enable/disable tracing
  project_name: "painel-do-clima"  # Langfuse project
  environment: "development"  # Environment tag
```

## Troubleshooting

### Common Issues
1. **Missing API Keys**: Set appropriate LLM provider keys
2. **Invalid Model Names**: Use format `provider/model-name`
3. **Langfuse Not Working**: Check public/secret keys are set
4. **JSON Parsing Errors**: Enable debug prints in `generate_llm_response()`

### Debug Steps
1. Run the test script: `python backend/test_llm_integration.py`
2. Check Langfuse dashboard for traces
3. Verify config.yaml model format
4. Enable debug prints in the code

## Next Steps

This migration provides a solid foundation for:
- Adding more LLM providers via LiteLLM
- Implementing advanced observability features
- Scaling to multiple concurrent narrative generations
- Adding custom metrics and alerts
- Integrating with other observability tools
