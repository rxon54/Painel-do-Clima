#!/usr/bin/env python3
"""
Test script for LLM integration with Langfuse OpenTelemetry observability.
This script validates that the LiteLLM + Langfuse setup is working correctly.
"""

import os
import sys
import yaml
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.generate_narratives import load_config, setup_llm_config, generate_llm_response

def test_llm_integration():
    """Test the LLM integration with a simple prompt."""
    print("🧪 Testing LLM integration with Langfuse OpenTelemetry observability...")
    
    # Load configuration
    try:
        config = load_config("../config.yaml")
        print(f"✅ Configuration loaded successfully")
        print(f"   Model: {config.get('llm', {}).get('model', 'Not set')}")
        print(f"   Observability enabled: {config.get('observability', {}).get('enabled', False)}")
        if config.get('observability', {}).get('enabled', False):
            host = config.get('observability', {}).get('host', 'https://cloud.langfuse.com')
            print(f"   Langfuse host: {host}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Setup LLM configuration
    try:
        setup_llm_config(config)
        print(f"✅ LLM configuration setup completed")
    except Exception as e:
        print(f"⚠️  LLM configuration setup completed with warnings: {e}")
        print(f"   LLM calls will proceed without observability tracing.")
    
    # Check environment variables
    api_keys_present = []
    if os.getenv('OPENAI_API_KEY'):
        api_keys_present.append('OpenAI')
    if os.getenv('ANTHROPIC_API_KEY'):
        api_keys_present.append('Anthropic')
    if os.getenv('GOOGLE_API_KEY'):
        api_keys_present.append('Google')
    
    if not api_keys_present:
        print("⚠️  No LLM API keys detected. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY")
        return False
    else:
        print(f"✅ API keys found for: {', '.join(api_keys_present)}")
    
    # Check Langfuse keys
    langfuse_keys = []
    if os.getenv('LANGFUSE_PUBLIC_KEY'):
        langfuse_keys.append('Public')
    if os.getenv('LANGFUSE_SECRET_KEY'):
        langfuse_keys.append('Secret')
    
    if langfuse_keys:
        print(f"✅ Langfuse keys found: {', '.join(langfuse_keys)}")
    else:
        print("⚠️  Langfuse keys not found. Observability will not be available.")
    
    # Test LLM call
    test_prompt = """
    Generate a JSON object with the following structure for testing purposes:
    {
        "title": "Test Response",
        "content": "This is a test of the LLM integration",
        "status": "success"
    }
    """
    
    print("\n🔄 Testing LLM call...")
    try:
        response = generate_llm_response(test_prompt, config, "test")
        if response:
            print(f"✅ LLM call successful!")
            print(f"   Response: {response}")
            return True
        else:
            print(f"❌ LLM call returned empty response")
            return False
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        
        # If the error is related to Langfuse compatibility, suggest a workaround
        if "sdk_integration" in str(e) or "langfuse" in str(e).lower():
            print("\n💡 This appears to be a Langfuse version compatibility issue.")
            print("   You can disable observability in config.yaml to proceed:")
            print("   observability: { enabled: false }")
            
        return False

if __name__ == "__main__":
    print("Painel do Clima - LLM Integration Test")
    print("=" * 50)
    
    success = test_llm_integration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! LLM integration is working correctly.")
        
        # Load config to show the correct dashboard URL
        try:
            config = load_config("../config.yaml")
            host = config.get('observability', {}).get('host', 'https://cloud.langfuse.com')
            print(f"\n📊 Check your Langfuse dashboard to see the traced LLM call:")
            print(f"   {host}")
        except:
            print("\n📊 Check your Langfuse dashboard to see the traced LLM call:")
            print("   https://cloud.langfuse.com (or your self-hosted instance)")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        print("\n💡 Common solutions:")
        print("   1. Set your LLM API key: export OPENAI_API_KEY='your-key'")
        print("   2. Set Langfuse keys: export LANGFUSE_PUBLIC_KEY='key' LANGFUSE_SECRET_KEY='key'")
        print("   3. Check config.yaml model format: 'openai/gpt-4o-mini'")
        sys.exit(1)
