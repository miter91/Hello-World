#!/usr/bin/env python3
"""
Fixed Stored Procedure Comparison Tool
This actually works and shows only the differences!
"""

import re
import os
from datetime import datetime

def parse_procedures_from_file(filepath):
    """Parse stored procedures from export file and return a dictionary"""
    procedures = {}
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # Split by procedure blocks
    proc_pattern = r'=== STORED PROCEDURE START ===(.*?)=== STORED PROCEDURE END ==='
    matches = re.findall(proc_pattern, content, re.DOTALL)
    
    for match in matches:
        # Extract the procedure details
        db_match = re.search(r'Database:\s*([^\n]+)', match)
        schema_match = re.search(r'Schema:\s*([^\n]+)', match)
        name_match = re.search(r'Name:\s*([^\n]+)', match)
        
        # Extract definition
        def_match = re.search(r'--- DEFINITION START ---(.*?)--- DEFINITION END ---', match, re.DOTALL)
        
        if db_match and schema_match and name_match and def_match:
            db = db_match.group(1).strip()
            schema = schema_match.group(1).strip()
            name = name_match.group(1).strip()
            definition = def_match.group(1).strip()
            
            # Create unique key
            key = f"{db}.{schema}.{name}"
            
            # Normalize definition for comparison (remove extra spaces, lowercase)
            normalized_def = ' '.join(definition.lower().split())
            
            procedures[key] = {
                'definition': definition,
                'normalized': normalized_def
            }
    
    return procedures

def compare_procedures(source_file, target_file):
    """Compare procedures between two files"""
    print("Parsing source file...")
    source_procs = parse_procedures_from_file(source_file)
    print(f"Found {len(source_procs)} procedures in source\n")
    
    print("Parsing target file...")
    target_procs = parse_procedures_from_file(target_file)
    print(f"Found {len(target_procs)} procedures in target\n")
    
    # Get procedure names as sets
    source_names = set(source_procs.keys())
    target_names = set(target_procs.keys())
    
    # Calculate differences
    only_in_source = source_names - target_names
    only_in_target = target_names - source_names
    in_both = source_names & target_names
    
    # Check for code differences in common procedures
    different_code = []
    for proc_name in in_both:
        if source_procs[proc_name]['normalized'] != target_procs[proc_name]['normalized']:
            different_code.append(proc_name)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create results directory
    os.makedirs('results', exist_ok=True)
    
    # Write summary report
    summary_file = f'results/comparison_summary_{timestamp}.txt'
    with open(summary_file, 'w') as f:
        f.write("STORED PROCEDURE COMPARISON SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"Total procedures in source: {len(source_procs)}\n")
        f.write(f"Total procedures in target: {len(target_procs)}\n")
        f.write(f"Procedures only in source: {len(only_in_source)}\n")
        f.write(f"Procedures only in target: {len(only_in_target)}\n")
        f.write(f"Procedures with differences: {len(different_code)}\n\n")
        
        # Missing in target (only in source)
        if only_in_source:
            f.write(f"PROCEDURES ONLY IN SOURCE (Missing in Target): {len(only_in_source)}\n")
            f.write("-" * 80 + "\n")
            for proc in sorted(only_in_source):
                f.write(f"  - {proc}\n")
            f.write("\n")
        else:
            f.write("PROCEDURES ONLY IN SOURCE (Missing in Target): None\n\n")
        
        # Extra in target (only in target)
        if only_in_target:
            f.write(f"PROCEDURES ONLY IN TARGET (Not in Source): {len(only_in_target)}\n")
            f.write("-" * 80 + "\n")
            for proc in sorted(only_in_target):
                f.write(f"  - {proc}\n")
            f.write("\n")
        else:
            f.write("PROCEDURES ONLY IN TARGET (Not in Source): None\n\n")
        
        # Different code
        if different_code:
            f.write(f"PROCEDURES WITH DIFFERENT CODE: {len(different_code)}\n")
            f.write("-" * 80 + "\n")
            for proc in sorted(different_code):
                f.write(f"  - {proc}\n")
            f.write("\n")
        else:
            f.write("PROCEDURES WITH DIFFERENT CODE: None\n\n")
        
        # Action summary
        f.write("=" * 80 + "\n")
        f.write("ACTION REQUIRED:\n")
        f.write("-" * 80 + "\n")
        if only_in_source:
            f.write(f"⚠️  Deploy {len(only_in_source)} missing procedures to target\n")
        if only_in_target:
            f.write(f"❓ Review {len(only_in_target)} extra procedures in target\n")
        if different_code:
            f.write(f"🔄 Review {len(different_code)} procedures with code changes\n")
        if not only_in_source and not only_in_target and not different_code:
            f.write("✅ All procedures match perfectly!\n")
    
    # Write detailed differences if any exist
    if different_code:
        diff_file = f'results/detailed_differences_{timestamp}.txt'
        with open(diff_file, 'w') as f:
            f.write("DETAILED PROCEDURE DIFFERENCES\n")
            f.write("=" * 80 + "\n\n")
            
            for proc_name in sorted(different_code):
                f.write(f"PROCEDURE: {proc_name}\n")
                f.write("-" * 80 + "\n")
                f.write("SOURCE VERSION:\n")
                f.write(source_procs[proc_name]['definition'])
                f.write("\n\nTARGET VERSION:\n")
                f.write(target_procs[proc_name]['definition'])
                f.write("\n\n" + "=" * 80 + "\n\n")
    
    print(f"\nResults saved to:")
    print(f"  - {summary_file}")
    if different_code:
        print(f"  - {diff_file}")
    
    # Quick summary to console
    print(f"\nQUICK SUMMARY:")
    print(f"  Missing in target: {len(only_in_source)}")
    if only_in_source:
        for proc in sorted(only_in_source):
            print(f"    - {proc}")
    print(f"  Extra in target: {len(only_in_target)}")
    print(f"  Different code: {len(different_code)}")

if __name__ == "__main__":
    # Replace with your actual file names
    source_file = "VISTA_STAGING_Stored_Procs_2025_07_01.txt"
    target_file = "VISTA_STAGING_Stored_Procs_Test_2025_07_01.txt"
    
    compare_procedures(source_file, target_file)
