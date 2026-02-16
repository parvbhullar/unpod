#!/usr/bin/env python3
"""
Generate a new Django SECRET_KEY
Usage: python generate_secret_key.py
"""

from django.core.management.utils import get_random_secret_key

if __name__ == "__main__":
    secret_key = get_random_secret_key()
    print("\n" + "="*60)
    print("NEW DJANGO SECRET KEY GENERATED")
    print("="*60)
    print(f"\n{secret_key}\n")
    print("="*60)
    print("\nAdd this to your .env file as:")
    print(f"DJANGO_SECRET_KEY={secret_key}")
    print("="*60 + "\n")
