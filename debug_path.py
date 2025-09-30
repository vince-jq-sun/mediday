#!/usr/bin/env python
"""Debug script to check path levels"""
from pathlib import Path

# Simulate the translation file path
translation_file = Path("temp/awake_where_you_are_english/1-2_foundational_meditation_sample-1/translations/1-2_foundational_meditation_sample-1_translations.json")

print(f"Translation file: {translation_file}")
print(f"Parent (1): {translation_file.parent}")  # translations/
print(f"Parent (2): {translation_file.parent.parent}")  # episode/
print(f"Parent (3): {translation_file.parent.parent.parent}")  # collection/
print(f"Parent (4): {translation_file.parent.parent.parent.parent}")  # temp/

print("\n--- What we want ---")
print(f"Collection should be: awake_where_you_are_english")
print(f"Episode should be: 1-2_foundational_meditation_sample-1")

print("\n--- Current code (3 parents) ---")
temp_dir_3 = translation_file.parent.parent.parent
print(f"temp_dir = {temp_dir_3}")
print(f"temp_dir.name = {temp_dir_3.name}")

# Try to list collections
if temp_dir_3.exists():
    collections = [item.name for item in temp_dir_3.iterdir() if item.is_dir()]
    print(f"Collections found: {collections}")
else:
    print("temp_dir doesn't exist")

print("\n--- Should be (for temp directory) ---")
# The temp_dir should point to 'temp/'
# From translations file, we need:
# parent(1) = translations/ -> parent(2) = episode/ -> parent(3) = collection/ -> that's wrong!
# We're currently at collection level, not temp level

print("\n--- Analysis ---")
print("Path structure: temp/{collection}/{episode}/translations/{file}")
print("From file.parent:")
print("  .parent(1) = translations/")
print("  .parent(2) = episode/")
print("  .parent(3) = collection/  <- WRONG! We're scanning episodes here")
print("  We SHOULD scan temp/ which contains collections")
print("\nThe issue: temp_dir should point to 'temp/', not 'collection/'")
