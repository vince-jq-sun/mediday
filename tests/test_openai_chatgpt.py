#!/usr/bin/env python3
"""
Simple test script to verify OpenAI ChatGPT API connectivity.
Tests GPT-4o-mini model with a simple "hello" message.
"""

import json
import os
import sys
from openai import OpenAI

def load_openai_config():
    """Load OpenAI API key from config file."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'openai.json')
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config.get('api')
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in config file {config_path}")
        return None
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_chatgpt():
    """Test ChatGPT API with a simple hello message."""
    # Load API key
    api_key = load_openai_config()
    if not api_key:
        print("Failed to load OpenAI API key")
        return False
    
    # Initialize OpenAI client
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return False
    
    # Test message
    test_message = "hello"
    
    try:
        print(f"Testing ChatGPT with message: '{test_message}'")
        print("Using model: gpt-4o-mini")
        print("-" * 50)
        
        # Make API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": test_message}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        # Extract and display response
        if response.choices:
            reply = response.choices[0].message.content
            print(f"ChatGPT Response: {reply}")
            print("-" * 50)
            print(f"✅ Success! API call completed successfully.")
            print(f"Model used: {response.model}")
            print(f"Tokens used: {response.usage.total_tokens}")
            return True
        else:
            print("❌ No response received from ChatGPT")
            return False
            
    except Exception as e:
        print(f"❌ Error calling ChatGPT API: {e}")
        return False

def main():
    """Main function to run the test."""
    print("OpenAI ChatGPT API Test")
    print("=" * 50)
    
    success = test_chatgpt()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed. Please check your API key and network connection.")
        sys.exit(1)

if __name__ == "__main__":
    main()
