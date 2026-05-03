"""
Test Gemini API connection and list available models
Run from testers directory: python test_gemini.py
"""
import sys
import os
# Add parent directory to path for accessing environment variables if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("Set GEMINI_API_KEY in your environment before running this test.")

genai.configure(api_key=api_key)

print("Available Gemini models that support generateContent:\n")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"  - {model.name}")
