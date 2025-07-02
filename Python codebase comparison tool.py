#!/usr/bin/env python3
"""
Python Code Comparison Tool
Compares Python scripts between two environments (yours vs client's)
"""

import os
import difflib
import hashlib
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Set
import json
import re


class PythonFileComparer:
    """Main class for comparing Python files"""
    
    def __init__(self):
        self.source_files: Dict[str, dict] = {}
        self.target_files: Dict[str, dict] = {}
        
    def normalize_code(self, code: str) -> str:
        """Normalize Python code for comparison"""
        # Remove comments but preserve docstrings
        lines = code.split('\n')
        normalized_lines = []
        in_docstring = False
        docstring_char = None
        
        for line in lines:
            # Handle docstrings
            if '"""' in line or "'''" in line:
                if not in_docstring:
                    in_docstring = True
                    docstring_char = '"""' if '"""' in line else "'''"
                elif docstring_char in line:
                    in_docstring = False
                    docstring_char = None
            
            # Remove inline comments if not in docstring
            if not in_docstring and '#' in line:
                # Find the comment position (not inside strings)
                comment_pos = -1
                in_string = False
                string_char = None
                for i, char in enumerate(line):
                    if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                        if not in_string:
                            in_string = True
                            string_char = char
                        elif char == string_char:
                            in_string = False
                    elif char == '#' and not in_string:
                        comment_pos = i
                        break
                
                if comment_pos >= 0:
                    line = line[:comment_pos].rstrip()
            
            # Remove trailing whitespace
            line = line.rstrip()
            
            # Skip empty lines
            if line or in_docstring:
                normalized_lines.append(line)
        
        return '\n'.join(normalized_lines)
    
    def get_file_hash(self, content: str) -> str:
        """Get hash of normalized content"""
        normalized = self.normalize_code(content)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def read_python_file(self, filepath: str) -> dict:
        """Read a Python file and extract information"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract basic metadata
            imports = []
            functions = []
            classes = []
            
            # Simple parsing for structure
            lines = content.split('\n')
            for line in lines:
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    imports.append(line.strip())
                elif line.strip().startswith('def '):
                    match = re.match(r'def\s+(\w+)\s*\(', line)
                    if match:
                        functions.append(match.group(1))
                elif line.strip().startswith('class '):
                    match = re.match(r'class\s+(\w+)\s*[\(:]', line)
                    if match:
                        classes.append(match.group(1))
            
            return {
                'content': content,
                'normalized_content': self.normalize_code(content),
                'hash': self.get_file_hash(content),
                'imports': imports,
                'functions': functions,
                'classes': classes,
                'lines': len(lines),
                'size': len(content)
            }
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return None
    
    def compare_directories(self, source_dir: str, target_dir: str, file_pattern: str = "*.py") -> None:
        """Compare Python files in two directories"""
        import glob
        
        # Get all Python files in source directory
        source_pattern = os.path.join(source_dir, file_pattern)
        source_files = glob.glob(source_pattern)
        
        print(f"Found {len(source_files)} Python files in source directory")
        
        for filepath in source_files:
            filename = os.path.basename(filepath)
            file_data = self.read_python_file(filepath)
            if file_data:
                self.source_files[filename] = file_data
        
        # Get all Python files in target directory
        target_pattern = os.path.join(target_dir, file_pattern)
        target_files = glob.glob(target_pattern)
        
        print(f"Found {len(target_files)} Python files in target directory")
        
        for filepath in target_files:
            filename = os.path.basename(filepath)
            file_data = self.read_python_file(filepath)
            if file_data:
                self.target_files[filename] = file_data
    
    def compare_specific_files(self, file_pairs: List[Tuple[str, str]]) -> None:
        """Compare specific file pairs"""
        for source_path, target_path in file_pairs:
            source_name = os.path.basename(source_path)
            target_name = os.path.basename(target_path)
            
            source_data = self.read_python_file(source_path)
            target_data = self.read_python_file(target_path)
            
            if source_data and target_data:
                # Use source filename as key for both for comparison
                self.source_files[source_name] = source_data
                self.target_files[source_name] = target_data
    
    def get_comparison_results(self) -> Tuple[Set[str], Set[str], Dict[str, dict]]:
        """Get comparison results"""
        source_names = set(self.source_files.keys())
        target_names = set(self.target_files.keys())
        
        # Files only in source
        only_in_source = source_names - target_names
        
        # Files only in target
        only_in_target = target_names - source_names
        
        # Files in both but different
        different_files = {}
        common_files = source_names & target_names
        
        for filename in common_files:
            source_file = self.source_files[filename]
            target_file = self.target_files[filename]
            
            if source_file['hash'] != target_file['hash']:
                # Get detailed diff
                source_lines = source_file['content'].splitlines()
                target_lines = target_file['content'].splitlines()
                
                diff = list(difflib.unified_diff(
                    source_lines, target_lines,
                    fromfile=f'Source/{filename}',
                    tofile=f'Target/{filename}',
                    lineterm=''
                ))
                
                # Analyze changes
                changes_summary = {
                    'diff': diff,
                    'source_lines': source_file['lines'],
                    'target_lines': target_file['lines'],
                    'imports_changed': source_file['imports'] != target_file['imports'],
                    'functions_changed': source_file['functions'] != target_file['functions'],
                    'classes_changed': source_file['classes'] != target_file['classes'],
                    'size_difference': target_file['size'] - source_file['size']
                }
                
                different_files[filename] = changes_summary
                
        return only_in_source, only_in_target, different_files
    
    def generate_report(self, output_dir: str = ".") -> None:
        """Generate comparison reports"""
        only_in_source, only_in_target, different_files = self.get_comparison_results()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(output_dir, exist_ok=True)
        
        # Summary report
        summary_file = os.path.join(output_dir, f"python_comparison_summary_{timestamp}.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("PYTHON CODE COMPARISON SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"Total files in source: {len(self.source_files)}\n")
            f.write(f"Total files in target: {len(self.target_files)}\n")
            f.write(f"Files only in source: {len(only_in_source)}\n")
            f.write(f"Files only in target: {len(only_in_target)}\n")
            f.write(f"Files with differences: {len(different_files)}\n\n")
            
            # List files only in source
            if only_in_source:
                f.write("FILES ONLY IN SOURCE (Missing in Target):\n")
                f.write("-" * 80 + "\n")
                for filename in sorted(only_in_source):
                    f.write(f"  - {filename}\n")
                f.write("\n")
            
            # List files only in target
            if only_in_target:
                f.write("FILES ONLY IN TARGET (Not in Source):\n")
                f.write("-" * 80 + "\n")
                for filename in sorted(only_in_target):
                    f.write(f"  - {filename}\n")
                f.write("\n")
            
            # List files with differences
            if different_files:
                f.write("FILES WITH DIFFERENCES:\n")
                f.write("-" * 80 + "\n")
                for filename in sorted(different_files.keys()):
                    changes = different_files[filename]
                    f.write(f"\n  - {filename}\n")
                    f.write(f"    Source lines: {changes['source_lines']}, ")
                    f.write(f"Target lines: {changes['target_lines']}\n")
                    f.write(f"    Size difference: {changes['size_difference']:+d} bytes\n")
                    
                    if changes['imports_changed']:
                        f.write("    ⚠ Imports have changed\n")
                    if changes['functions_changed']:
                        f.write("    ⚠ Functions have changed\n")
                    if changes['classes_changed']:
                        f.write("    ⚠ Classes have changed\n")
        
        # Detailed differences report
        if different_files:
            diff_file = os.path.join(output_dir, f"python_detailed_differences_{timestamp}.txt")
            with open(diff_file, 'w', encoding='utf-8') as f:
                f.write("DETAILED PYTHON CODE DIFFERENCES\n")
                f.write("=" * 80 + "\n\n")
                
                for filename in sorted(different_files.keys()):
                    f.write(f"\nFILE: {filename}\n")
                    f.write("-" * 80 + "\n")
                    f.write('\n'.join(different_files[filename]['diff']))
                    f.write("\n\n")
        
        # JSON report
        json_file = os.path.join(output_dir, f"python_comparison_results_{timestamp}.json")
        results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "source_total": len(self.source_files),
                "target_total": len(self.target_files),
                "only_in_source": len(only_in_source),
                "only_in_target": len(only_in_target),
                "different": len(different_files)
            },
            "only_in_source": sorted(list(only_in_source)),
            "only_in_target": sorted(list(only_in_target)),
            "different": sorted(list(different_files.keys())),
            "file_details": {
                filename: {
                    "imports_changed": changes['imports_changed'],
                    "functions_changed": changes['functions_changed'],
                    "classes_changed": changes['classes_changed'],
                    "size_difference": changes['size_difference']
                } for filename, changes in different_files.items()
            }
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nReports generated:")
        print(f"  - Summary: {summary_file}")
        if different_files:
            print(f"  - Detailed differences: {diff_file}")
        print(f"  - JSON results: {json_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Compare Python scripts between two environments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare specific files
  python compare_python.py -f source/api.py:target/api.py source/db.py:target/db.py
  
  # Compare all Python files in directories
  python compare_python.py -d source_folder target_folder
  
  # Compare with custom output directory
  python compare_python.py -f file1.py:file2.py -o results
        """
    )
    
    parser.add_argument('-f', '--files', nargs='+', 
                        help='File pairs to compare (format: source:target)')
    parser.add_argument('-d', '--directories', nargs=2,
                        help='Compare all Python files in two directories')
    parser.add_argument('-o', '--output', default='.',
                        help='Output directory for reports (default: current directory)')
    
    args = parser.parse_args()
    
    if not args.files and not args.directories:
        parser.error('Either --files or --directories must be specified')
    
    comparer = PythonFileComparer()
    
    if args.files:
        # Parse file pairs
        file_pairs = []
        for pair in args.files:
            if ':' not in pair:
                print(f"Error: Invalid file pair format '{pair}'. Use source:target")
                return
            source, target = pair.split(':', 1)
            if not os.path.exists(source):
                print(f"Error: Source file '{source}' not found")
                return
            if not os.path.exists(target):
                print(f"Error: Target file '{target}' not found")
                return
            file_pairs.append((source, target))
        
        print(f"Comparing {len(file_pairs)} file pairs...")
        comparer.compare_specific_files(file_pairs)
    
    elif args.directories:
        source_dir, target_dir = args.directories
        if not os.path.isdir(source_dir):
            print(f"Error: Source directory '{source_dir}' not found")
            return
        if not os.path.isdir(target_dir):
            print(f"Error: Target directory '{target_dir}' not found")
            return
        
        print(f"Comparing Python files in directories...")
        comparer.compare_directories(source_dir, target_dir)
    
    comparer.generate_report(args.output)
    print("\nComparison complete!")


if __name__ == "__main__":
    main()
