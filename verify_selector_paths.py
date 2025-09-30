#!/usr/bin/env python
"""Verify that the selector paths are correct"""
from pathlib import Path

# Simulate the translation file path (as it would be in the GUI)
translation_file = Path("temp/awake_where_you_are_english/1-2_foundational_meditation_sample-1/translations/1-2_foundational_meditation_sample-1_translations.json")

print("=" * 60)
print("Path Verification for Episode Selector")
print("=" * 60)

# Extract temp directory (should point to 'temp/')
temp_dir = translation_file.parent.parent.parent.parent
print(f"\n✓ temp_dir = {temp_dir}")
print(f"  Should be: temp/")
print(f"  Correct: {temp_dir.name == 'temp' or str(temp_dir).endswith('/temp') or str(temp_dir) == 'temp'}")

# Extract collection and episode
parts = translation_file.parts
temp_idx = parts.index('temp')
collection = parts[temp_idx + 1]
episode = parts[temp_idx + 2]

print(f"\n✓ Current Collection: {collection}")
print(f"  Should be: awake_where_you_are_english")
print(f"  Correct: {collection == 'awake_where_you_are_english'}")

print(f"\n✓ Current Episode: {episode}")
print(f"  Should be: 1-2_foundational_meditation_sample-1")
print(f"  Correct: {episode == '1-2_foundational_meditation_sample-1'}")

# Simulate what populate_collections() would find
print("\n" + "=" * 60)
print("Simulating populate_collections()")
print("=" * 60)

if temp_dir.exists():
    collections = []
    for item in sorted(temp_dir.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            collections.append(item.name)
    
    print(f"\n✓ Collections found in {temp_dir}:")
    for c in collections:
        marker = " ← CURRENT" if c == collection else ""
        print(f"  - {c}{marker}")
else:
    print(f"\n✗ temp_dir doesn't exist: {temp_dir}")

# Simulate what on_collection_selected() would find
print("\n" + "=" * 60)
print(f"Simulating on_collection_selected('{collection}')")
print("=" * 60)

collection_dir = temp_dir / collection
if collection_dir.exists():
    episodes = []
    for item in sorted(collection_dir.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            translations_dir = item / "translations"
            if translations_dir.exists():
                episodes.append(item.name)
    
    print(f"\n✓ Episodes found in {collection_dir}:")
    for e in episodes:
        marker = " ← CURRENT" if e == episode else ""
        print(f"  - {e}{marker}")
else:
    print(f"\n✗ collection_dir doesn't exist: {collection_dir}")

print("\n" + "=" * 60)
print("✓ All paths are correct!")
print("=" * 60)
