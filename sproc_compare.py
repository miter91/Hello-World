#!/usr/bin/env python3
"""
Stored Procedure Comparison Tool
Compares stored procedures between two database exports
"""

import re
import sys
import os
import difflib
from datetime import datetime
from collections import defaultdict

def parse_stored_procedures(filepath):
    """
    Parse stored procedures from export file
    Returns dict with procedure names as keys and their definitions as values
    """
    procedures = {}
    
    # Try different encodings
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    content = None
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except:
            continue
    
    if content is None:
        print(f"Error: Could not read file {filepath}")
        return procedures
    
    # Split by procedure blocks
    pattern = r'=== STORED PROCEDURE START ===(.*?)=== STORED PROCEDURE END ==='
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        block = match.group(1)
        
        # Extract metadata
        database = re.search(r'Database:\s*([^\n\r]+)', block)
        schema = re.search(r'Schema:\s*([^\n\r]+)', block)
        name = re.search(r'Name:\s*([^\n\r]+)', block)
        
        # Extract definition
        def_pattern = r'--- DEFINITION START ---(.*?)--- DEFINITION END ---'
        definition = re.search(def_pattern, block, re.DOTALL)
        
        if database and schema and name and definition:
            proc_name = f"{database.group(1).strip()}.{schema.group(1).strip()}.{name.group(1).strip()}"
            proc_def = definition.group(1).strip()
            procedures[proc_name] = proc_def
    
    return procedures

def normalize_for_comparison(text):
    """Normalize SQL text for comparison - remove extra whitespace, comments"""
    # Remove single line comments
    text = re.sub(r'--[^\n]*', '', text)
    # Remove multi-line comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Normalize whitespace
    text = ' '.join(text.split())
    # Convert to lowercase for comparison
    text = text.lower()
    return text

def compare_procedures(source_file, target_file, output_dir='results'):
    """Main comparison function"""
    print(f"\nComparing stored procedures...")
    print(f"Source: {source_file}")
    print(f"Target: {target_file}")
    print("-" * 80)
    
    # Parse both files
    source_procs = parse_stored_procedures(source_file)
    target_procs = parse_stored_procedures(target_file)
    
    print(f"\nFound {len(source_procs)} procedures in source")
    print(f"Found {len(target_procs)} procedures in target")
    
    # Get sets of procedure names
    source_names = set(source_procs.keys())
    target_names = set(target_procs.keys())
    
    # Find differences
    only_in_source = source_names - target_names
    only_in_target = target_names - source_names
    in_both = source_names & target_names
    
    # Check for code differences
    code_differences = {}
    for proc_name in in_both:
        source_normalized = normalize_for_comparison(source_procs[proc_name])
        target_normalized = normalize_for_comparison(target_procs[proc_name])
        
        if source_normalized != target_normalized:
            # Get line-by-line diff
            source_lines = source_procs[proc_name].splitlines()
            target_lines = target_procs[proc_name].splitlines()
            diff = list(difflib.unified_diff(
                source_lines, 
                target_lines,
                fromfile='Source',
                tofile='Target',
                lineterm=''
            ))
            code_differences[proc_name] = diff
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write summary report
    summary_file = os.path.join(output_dir, f'comparison_summary_{timestamp}.txt')
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("STORED PROCEDURE COMPARISON SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source file: {os.path.basename(source_file)}\n")
        f.write(f"Target file: {os.path.basename(target_file)}\n\n")
        
        f.write("STATISTICS:\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total procedures in source: {len(source_procs)}\n")
        f.write(f"Total procedures in target: {len(target_procs)}\n")
        f.write(f"Missing in target: {len(only_in_source)}\n")
        f.write(f"Extra in target: {len(only_in_target)}\n")
        f.write(f"Code differences: {len(code_differences)}\n\n")
        
        # Missing procedures (only in source)
        if only_in_source:
            f.write(f"MISSING IN TARGET ({len(only_in_source)} procedures):\n")
            f.write("-" * 80 + "\n")
            for proc in sorted(only_in_source):
                f.write(f"  {proc}\n")
            f.write("\n")
        
        # Extra procedures (only in target)
        if only_in_target:
            f.write(f"EXTRA IN TARGET ({len(only_in_target)} procedures):\n")
            f.write("-" * 80 + "\n")
            for proc in sorted(only_in_target):
                f.write(f"  {proc}\n")
            f.write("\n")
        
        # Procedures with code differences
        if code_differences:
            f.write(f"PROCEDURES WITH CODE DIFFERENCES ({len(code_differences)} procedures):\n")
            f.write("-" * 80 + "\n")
            for proc in sorted(code_differences.keys()):
                f.write(f"  {proc}\n")
            f.write("\n")
    
    # Write detailed differences if any
    if code_differences:
        diff_file = os.path.join(output_dir, f'code_differences_{timestamp}.txt')
        with open(diff_file, 'w', encoding='utf-8') as f:
            f.write("DETAILED CODE DIFFERENCES\n")
            f.write("=" * 80 + "\n\n")
            
            for proc_name in sorted(code_differences.keys()):
                f.write(f"PROCEDURE: {proc_name}\n")
                f.write("-" * 80 + "\n")
                f.write('\n'.join(code_differences[proc_name]))
                f.write("\n\n" + "=" * 80 + "\n\n")
    
    # Print summary to console
    print("\nSUMMARY:")
    print("-" * 40)
    print(f"Missing in target: {len(only_in_source)}")
    if only_in_source:
        for proc in sorted(only_in_source)[:5]:  # Show first 5
            print(f"  - {proc}")
        if len(only_in_source) > 5:
            print(f"  ... and {len(only_in_source) - 5} more")
    
    print(f"\nExtra in target: {len(only_in_target)}")
    print(f"Code differences: {len(code_differences)}")
    
    print(f"\nReports saved in '{output_dir}' folder:")
    print(f"  - {os.path.basename(summary_file)}")
    if code_differences:
        print(f"  - {os.path.basename(diff_file)}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python sproc_compare.py <source_file> <target_file>")
        print("Example: python sproc_compare.py VISTA_STAGING_StoredProcs_20250701.txt VISTA_STAGING_StoredProcs_M&G_20250701.txt")
        sys.exit(1)
    
    source_file = sys.argv[1]
    target_file = sys.argv[2]
    
    if not os.path.exists(source_file):
        print(f"Error: Source file '{source_file}' not found")
        sys.exit(1)
    
    if not os.path.exists(target_file):
        print(f"Error: Target file '{target_file}' not found")
        sys.exit(1)
    
    compare_procedures(source_file, target_file)

if __name__ == "__main__":
    main()
