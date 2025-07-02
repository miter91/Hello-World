#!/usr/bin/env python3
"""
Simple Stored Procedure Comparison Tool
Just compares two files and shows the differences clearly
"""

import sys
import os
import re
from datetime import datetime

def extract_procedures(filename):
    """Extract procedures from file into a dictionary"""
    procedures = {}
    
    # Read file with proper encoding
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except:
        with open(filename, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Find each procedure block
    current_proc = None
    current_def = []
    in_definition = False
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Start of new procedure
        if line == '=== STORED PROCEDURE START ===':
            current_proc = {}
            current_def = []
            in_definition = False
            
        # Extract database
        elif line.startswith('Database:'):
            current_proc['database'] = line.replace('Database:', '').strip()
            
        # Extract schema
        elif line.startswith('Schema:'):
            current_proc['schema'] = line.replace('Schema:', '').strip()
            
        # Extract name
        elif line.startswith('Name:'):
            current_proc['name'] = line.replace('Name:', '').strip()
            
        # Start of definition
        elif line == '--- DEFINITION START ---':
            in_definition = True
            
        # End of definition
        elif line == '--- DEFINITION END ---':
            in_definition = False
            
        # End of procedure
        elif line == '=== STORED PROCEDURE END ===':
            if current_proc and 'name' in current_proc:
                # Create full name
                full_name = f"{current_proc.get('database', 'Unknown')}.{current_proc.get('schema', 'Unknown')}.{current_proc.get('name', 'Unknown')}"
                # Store definition
                procedures[full_name] = '\n'.join(current_def)
            current_proc = None
            current_def = []
            
        # Collect definition lines
        elif in_definition:
            current_def.append(line)
    
    return procedures

def normalize_sql(sql_text):
    """Normalize SQL for comparison - remove comments and extra spaces"""
    # Remove single-line comments
    sql_text = re.sub(r'--.*$', '', sql_text, flags=re.MULTILINE)
    # Remove multi-line comments
    sql_text = re.sub(r'/\*.*?\*/', '', sql_text, flags=re.DOTALL)
    # Normalize whitespace
    sql_text = ' '.join(sql_text.split())
    # Convert to lowercase
    return sql_text.lower().strip()

def compare_files(file1, file2):
    """Compare two procedure files and return differences"""
    print(f"\nExtracting procedures from files...")
    
    procs1 = extract_procedures(file1)
    procs2 = extract_procedures(file2)
    
    print(f"Source file: {len(procs1)} procedures found")
    print(f"Target file: {len(procs2)} procedures found")
    
    # Get sets of procedure names
    names1 = set(procs1.keys())
    names2 = set(procs2.keys())
    
    # Calculate differences
    only_in_source = names1 - names2  # Missing in target
    only_in_target = names2 - names1  # Extra in target
    in_both = names1 & names2         # Common procedures
    
    # Find procedures with different code
    different_code = []
    for proc_name in in_both:
        norm1 = normalize_sql(procs1[proc_name])
        norm2 = normalize_sql(procs2[proc_name])
        if norm1 != norm2:
            different_code.append(proc_name)
    
    return {
        'source_count': len(procs1),
        'target_count': len(procs2),
        'only_in_source': sorted(list(only_in_source)),
        'only_in_target': sorted(list(only_in_target)),
        'different_code': sorted(different_code),
        'procedures': {
            'source': procs1,
            'target': procs2
        }
    }

def generate_report(results, output_dir='results'):
    """Generate comparison report"""
    # Create results directory
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_dir, f'comparison_report_{timestamp}.txt')
    
    with open(report_file, 'w') as f:
        f.write("STORED PROCEDURE COMPARISON REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary
        f.write("SUMMARY\n")
        f.write("-" * 30 + "\n")
        f.write(f"Procedures in source: {results['source_count']}\n")
        f.write(f"Procedures in target: {results['target_count']}\n")
        f.write(f"Missing in target:    {len(results['only_in_source'])}\n")
        f.write(f"Extra in target:      {len(results['only_in_target'])}\n")
        f.write(f"Different code:       {len(results['different_code'])}\n\n")
        
        # Missing procedures
        if results['only_in_source']:
            f.write(f"\nMISSING IN TARGET ({len(results['only_in_source'])} procedures)\n")
            f.write("-" * 70 + "\n")
            for proc in results['only_in_source']:
                f.write(f"{proc}\n")
        
        # Extra procedures
        if results['only_in_target']:
            f.write(f"\nEXTRA IN TARGET ({len(results['only_in_target'])} procedures)\n")
            f.write("-" * 70 + "\n")
            for proc in results['only_in_target']:
                f.write(f"{proc}\n")
        
        # Different code
        if results['different_code']:
            f.write(f"\nDIFFERENT CODE ({len(results['different_code'])} procedures)\n")
            f.write("-" * 70 + "\n")
            for proc in results['different_code']:
                f.write(f"{proc}\n")
    
    # If there are code differences, create detailed diff file
    if results['different_code']:
        diff_file = os.path.join(output_dir, f'code_differences_{timestamp}.txt')
        with open(diff_file, 'w') as f:
            f.write("DETAILED CODE DIFFERENCES\n")
            f.write("=" * 70 + "\n\n")
            
            for proc in results['different_code']:
                f.write(f"PROCEDURE: {proc}\n")
                f.write("-" * 70 + "\n")
                f.write("\n--- SOURCE VERSION ---\n")
                f.write(results['procedures']['source'][proc])
                f.write("\n\n--- TARGET VERSION ---\n")
                f.write(results['procedures']['target'][proc])
                f.write("\n\n" + "=" * 70 + "\n\n")
    
    return report_file

def main():
    if len(sys.argv) != 3:
        print("\nUsage: python simple_compare.py <source_file> <target_file>")
        print("Example: python simple_compare.py VISTA_STAGING_StoredProcs_20250701.txt VISTA_STAGING_StoredProcs_M&G_20250701.txt")
        sys.exit(1)
    
    source_file = sys.argv[1]
    target_file = sys.argv[2]
    
    # Check files exist
    if not os.path.exists(source_file):
        print(f"Error: Cannot find source file: {source_file}")
        sys.exit(1)
        
    if not os.path.exists(target_file):
        print(f"Error: Cannot find target file: {target_file}")
        sys.exit(1)
    
    # Run comparison
    results = compare_files(source_file, target_file)
    
    # Generate report
    report_file = generate_report(results)
    
    # Print summary to console
    print("\n" + "=" * 50)
    print("RESULTS:")
    print("=" * 50)
    print(f"Missing in target: {len(results['only_in_source'])}")
    if results['only_in_source']:
        for i, proc in enumerate(results['only_in_source'][:5]):
            print(f"  - {proc}")
        if len(results['only_in_source']) > 5:
            print(f"  ... and {len(results['only_in_source']) - 5} more")
    
    print(f"\nExtra in target: {len(results['only_in_target'])}")
    if results['only_in_target']:
        for i, proc in enumerate(results['only_in_target'][:5]):
            print(f"  - {proc}")
        if len(results['only_in_target']) > 5:
            print(f"  ... and {len(results['only_in_target']) - 5} more")
    
    print(f"\nDifferent code: {len(results['different_code'])}")
    
    print(f"\nFull report saved to: {report_file}")

if __name__ == "__main__":
    main()
