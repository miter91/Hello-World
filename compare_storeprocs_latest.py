#!/usr/bin/env python3
"""
Stored Procedure Comparison Tool - Fixed for case sensitivity
"""

import sys
import os
from datetime import datetime
import re

def parse_stored_procedures(filename):
    """Parse stored procedures from file"""
    procedures = {}
    
    # Read file
    with open(filename, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # Split by the procedure marker
    parts = content.split('=== STORED PROCEDURE START ===')
    
    for part in parts[1:]:  # Skip first empty part
        if '=== STORED PROCEDURE END ===' not in part:
            continue
        
        # Get just the procedure section
        proc_section = part.split('=== STORED PROCEDURE END ===')[0]
        
        # Extract metadata using regex
        database_match = re.search(r'Database:\s*(\S+)', proc_section)
        schema_match = re.search(r'Schema:\s*(\S+)', proc_section)
        name_match = re.search(r'Name:\s*(\S+)', proc_section)
        
        # Extract definition
        def_start = proc_section.find('--- DEFINITION START ---')
        def_end = proc_section.find('--- DEFINITION END ---')
        
        if database_match and schema_match and name_match and def_start != -1 and def_end != -1:
            database = database_match.group(1)
            schema = schema_match.group(1)
            name = name_match.group(1)
            
            # Extract definition between markers
            definition = proc_section[def_start + len('--- DEFINITION START ---'):def_end].strip()
            
            # Create key with LOWERCASE for case-insensitive comparison
            key = f"{database}.{schema}.{name}".lower()
            
            # Store with original names for display
            procedures[key] = {
                'full_name': f"{database}.{schema}.{name}",
                'definition': definition
            }
    
    return procedures

def normalize_for_comparison(text):
    """Normalize SQL for comparison"""
    # Remove comments
    text = re.sub(r'--[^\n]*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Normalize whitespace
    text = ' '.join(text.split())
    # Convert to lowercase
    return text.lower()

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 compare.py source_file target_file")
        sys.exit(1)
    
    source_file = sys.argv[1]
    target_file = sys.argv[2]
    
    # Check files exist
    if not os.path.exists(source_file):
        print(f"Error: Source file not found: {source_file}")
        sys.exit(1)
    
    if not os.path.exists(target_file):
        print(f"Error: Target file not found: {target_file}")
        sys.exit(1)
    
    print(f"\nComparing stored procedures...")
    print(f"Source: {source_file}")
    print(f"Target: {target_file}")
    print("-" * 70)
    
    # Parse files
    source_procs = parse_stored_procedures(source_file)
    target_procs = parse_stored_procedures(target_file)
    
    print(f"\nFound {len(source_procs)} procedures in source")
    print(f"Found {len(target_procs)} procedures in target")
    
    # Calculate differences using lowercase keys
    source_keys = set(source_procs.keys())
    target_keys = set(target_procs.keys())
    
    missing_in_target = source_keys - target_keys
    extra_in_target = target_keys - source_keys
    common = source_keys & target_keys
    
    # Find code differences
    different_code = []
    for proc_key in common:
        source_norm = normalize_for_comparison(source_procs[proc_key]['definition'])
        target_norm = normalize_for_comparison(target_procs[proc_key]['definition'])
        if source_norm != target_norm:
            different_code.append(proc_key)
    
    # Create results directory
    os.makedirs('results', exist_ok=True)
    
    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"results/comparison_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write("STORED PROCEDURE COMPARISON REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: {os.path.basename(source_file)}\n")
        f.write(f"Target: {os.path.basename(target_file)}\n\n")
        
        f.write("SUMMARY\n")
        f.write("-" * 30 + "\n")
        f.write(f"Procedures in source: {len(source_procs)}\n")
        f.write(f"Procedures in target: {len(target_procs)}\n")
        f.write(f"Missing in target:    {len(missing_in_target)}\n")
        f.write(f"Extra in target:      {len(extra_in_target)}\n")
        f.write(f"Different code:       {len(different_code)}\n\n")
        
        # List missing procedures (use original names for display)
        if missing_in_target:
            f.write(f"MISSING IN TARGET ({len(missing_in_target)} procedures)\n")
            f.write("-" * 70 + "\n")
            for proc_key in sorted(missing_in_target):
                f.write(f"{source_procs[proc_key]['full_name']}\n")
            f.write("\n")
        
        # List extra procedures
        if extra_in_target:
            f.write(f"EXTRA IN TARGET ({len(extra_in_target)} procedures)\n")
            f.write("-" * 70 + "\n")
            for proc_key in sorted(extra_in_target):
                f.write(f"{target_procs[proc_key]['full_name']}\n")
            f.write("\n")
        
        # List procedures with different code
        if different_code:
            f.write(f"PROCEDURES WITH DIFFERENT CODE ({len(different_code)} procedures)\n")
            f.write("-" * 70 + "\n")
            for proc_key in sorted(different_code):
                # Show name from source file
                f.write(f"{source_procs[proc_key]['full_name']}\n")
    
    # Create detailed differences file
    if different_code:
        diff_file = f"results/code_differences_{timestamp}.txt"
        with open(diff_file, 'w') as f:
            f.write("DETAILED CODE DIFFERENCES\n")
            f.write("=" * 70 + "\n\n")
            
            for proc_key in sorted(different_code):
                f.write(f"\nPROCEDURE: {source_procs[proc_key]['full_name']}\n")
                f.write("-" * 70 + "\n")
                f.write("\n--- SOURCE VERSION ---\n")
                f.write(source_procs[proc_key]['definition'])
                f.write("\n\n--- TARGET VERSION ---\n")
                f.write(target_procs[proc_key]['definition'])
                f.write("\n" + "=" * 70 + "\n")
    
    # Print console summary
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("-" * 70)
    print(f"Missing in target: {len(missing_in_target)}")
    if missing_in_target:
        for proc_key in list(missing_in_target)[:5]:
            print(f"  - {source_procs[proc_key]['full_name']}")
        if len(missing_in_target) > 5:
            print(f"  ... and {len(missing_in_target) - 5} more")
    
    print(f"\nExtra in target: {len(extra_in_target)}")
    if extra_in_target:
        for proc_key in list(extra_in_target)[:5]:
            print(f"  - {target_procs[proc_key]['full_name']}")
        if len(extra_in_target) > 5:
            print(f"  ... and {len(extra_in_target) - 5} more")
    
    print(f"\nDifferent code: {len(different_code)}")
    
    print(f"\nReports saved to 'results' folder")

if __name__ == "__main__":
    main()
