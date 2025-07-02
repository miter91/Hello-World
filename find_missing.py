#!/usr/bin/env python3
"""
SIMPLE script that ONLY shows missing stored procedures
Nothing fancy - just the missing procedure names
"""

import re

def get_procedure_names(filename):
    """Extract just the procedure names from file"""
    procedures = set()
    
    # Read file - try different encodings if needed
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except:
            with open(filename, 'r', encoding='latin-1') as f:
                content = f.read()
    
    # Find all procedures
    blocks = content.split('=== STORED PROCEDURE START ===')
    
    for block in blocks[1:]:  # Skip first empty block
        # Look for the procedure name
        lines = block.split('\n')
        for line in lines:
            if line.strip().startswith('Name:'):
                name = line.replace('Name:', '').strip()
                # Also get database and schema
                db = ''
                schema = ''
                for l in lines:
                    if l.strip().startswith('Database:'):
                        db = l.replace('Database:', '').strip()
                    if l.strip().startswith('Schema:'):
                        schema = l.replace('Schema:', '').strip()
                if db and schema and name:
                    full_name = f"{db}.{schema}.{name}"
                    procedures.add(full_name)
                break
    
    return procedures

# YOUR FILES
source_file = "VISTA_STAGING_Stored_Procs_2025_07_01.txt"
target_file = "VISTA_STAGING_Stored_Procs_Test_2025_07_01.txt"

print("Finding missing procedures...\n")

# Get procedures from both files
source_procs = get_procedure_names(source_file)
target_procs = get_procedure_names(target_file)

print(f"Source has: {len(source_procs)} procedures")
print(f"Target has: {len(target_procs)} procedures\n")

# Find missing
missing = source_procs - target_procs

print("=" * 60)
print(f"MISSING PROCEDURES (in source but NOT in target): {len(missing)}")
print("=" * 60)

if missing:
    for proc in sorted(missing):
        print(f"  - {proc}")
else:
    print("  None - all procedures exist in both!")

# Also check for extra
extra = target_procs - source_procs
if extra:
    print(f"\n\nEXTRA PROCEDURES (in target but NOT in source): {len(extra)}")
    print("=" * 60)
    for proc in sorted(extra):
        print(f"  - {proc}")

# Save to a simple text file
with open('MISSING_PROCEDURES.txt', 'w') as f:
    f.write(f"MISSING PROCEDURES: {len(missing)}\n")
    f.write("=" * 60 + "\n")
    if missing:
        for proc in sorted(missing):
            f.write(f"{proc}\n")
    else:
        f.write("None - all procedures exist in both!\n")

print(f"\n\nResults also saved to: MISSING_PROCEDURES.txt")
