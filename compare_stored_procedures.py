#!/usr/bin/env python3
"""
Stored Procedure Comparison Tool
Compares stored procedures between two SQL Server database exports
"""

import re
import difflib
import argparse
import os
from datetime import datetime
from typing import Dict, List, Tuple, Set
import json
import hashlib


class StoredProcedure:
    """Class to represent a stored procedure"""
    def __init__(self, database: str, schema: str, name: str, definition: str, 
                 create_date: str = "", modify_date: str = ""):
        self.database = database
        self.schema = schema
        self.name = name
        self.definition = definition
        self.create_date = create_date
        self.modify_date = modify_date
        self.full_name = f"{database}.{schema}.{name}"
        
    def get_normalized_definition(self) -> str:
        """Normalize the definition for comparison"""
        # Remove extra whitespace, normalize line endings
        normalized = re.sub(r'\s+', ' ', self.definition)
        # Remove comments
        normalized = re.sub(r'--[^\n]*', '', normalized)
        normalized = re.sub(r'/\*.*?\*/', '', normalized, flags=re.DOTALL)
        # Convert to lowercase for comparison
        normalized = normalized.lower().strip()
        return normalized
    
    def get_definition_hash(self) -> str:
        """Get hash of normalized definition"""
        return hashlib.md5(self.get_normalized_definition().encode()).hexdigest()


class StoredProcedureComparer:
    """Main class for comparing stored procedures"""
    
    def __init__(self):
        self.source_procs: Dict[str, StoredProcedure] = {}
        self.target_procs: Dict[str, StoredProcedure] = {}
        
    def parse_file(self, filepath: str) -> Dict[str, StoredProcedure]:
        """Parse the SQL export file and extract stored procedures"""
        procedures = {}
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # Pattern to match stored procedure blocks
        pattern = r'=== STORED PROCEDURE START ===(.*?)=== STORED PROCEDURE END ==='
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            proc_content = match.group(1)
            
            # Extract metadata
            database = self._extract_value(proc_content, 'Database:')
            schema = self._extract_value(proc_content, 'Schema:')
            name = self._extract_value(proc_content, 'Name:')
            create_date = self._extract_value(proc_content, 'CreateDate:')
            modify_date = self._extract_value(proc_content, 'ModifyDate:')
            
            # Extract definition
            def_pattern = r'--- DEFINITION START ---(.*?)--- DEFINITION END ---'
            def_match = re.search(def_pattern, proc_content, re.DOTALL)
            definition = def_match.group(1).strip() if def_match else ""
            
            if database and schema and name and definition:
                proc = StoredProcedure(database, schema, name, definition, create_date, modify_date)
                procedures[proc.full_name] = proc
                
        return procedures
    
    def _extract_value(self, content: str, label: str) -> str:
        """Extract value after a label"""
        pattern = rf'{label}\s*([^\n\r]+)'
        match = re.search(pattern, content)
        return match.group(1).strip() if match else ""
    
    def compare_files(self, source_file: str, target_file: str) -> None:
        """Compare two stored procedure export files"""
        print(f"Parsing source file: {source_file}")
        self.source_procs = self.parse_file(source_file)
        print(f"Found {len(self.source_procs)} stored procedures in source")
        
        print(f"\nParsing target file: {target_file}")
        self.target_procs = self.parse_file(target_file)
        print(f"Found {len(self.target_procs)} stored procedures in target")
        
    def get_comparison_results(self) -> Tuple[Set[str], Set[str], Dict[str, List[str]]]:
        """Get comparison results"""
        source_names = set(self.source_procs.keys())
        target_names = set(self.target_procs.keys())
        
        # Procedures only in source
        only_in_source = source_names - target_names
        
        # Procedures only in target
        only_in_target = target_names - source_names
        
        # Procedures in both but different
        different_procs = {}
        common_procs = source_names & target_names
        
        for proc_name in common_procs:
            source_proc = self.source_procs[proc_name]
            target_proc = self.target_procs[proc_name]
            
            if source_proc.get_definition_hash() != target_proc.get_definition_hash():
                # Get detailed diff
                source_lines = source_proc.definition.splitlines()
                target_lines = target_proc.definition.splitlines()
                diff = list(difflib.unified_diff(source_lines, target_lines, 
                                               fromfile='Source', tofile='Target', lineterm=''))
                different_procs[proc_name] = diff
                
        return only_in_source, only_in_target, different_procs
    
    def generate_report(self, output_dir: str = ".") -> None:
        """Generate detailed comparison report"""
        only_in_source, only_in_target, different_procs = self.get_comparison_results()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Summary report
        summary_file = os.path.join(output_dir, f"comparison_summary_{timestamp}.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("STORED PROCEDURE COMPARISON SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"Total procedures in source: {len(self.source_procs)}\n")
            f.write(f"Total procedures in target: {len(self.target_procs)}\n")
            f.write(f"Procedures only in source: {len(only_in_source)}\n")
            f.write(f"Procedures only in target: {len(only_in_target)}\n")
            f.write(f"Procedures with differences: {len(different_procs)}\n\n")
            
            # List procedures only in source
            if only_in_source:
                f.write("PROCEDURES ONLY IN SOURCE (Missing in Target):\n")
                f.write("-" * 80 + "\n")
                for proc_name in sorted(only_in_source):
                    f.write(f"  - {proc_name}\n")
                f.write("\n")
            
            # List procedures only in target
            if only_in_target:
                f.write("PROCEDURES ONLY IN TARGET (Not in Source):\n")
                f.write("-" * 80 + "\n")
                for proc_name in sorted(only_in_target):
                    f.write(f"  - {proc_name}\n")
                f.write("\n")
            
            # List procedures with differences
            if different_procs:
                f.write("PROCEDURES WITH DIFFERENCES:\n")
                f.write("-" * 80 + "\n")
                for proc_name in sorted(different_procs.keys()):
                    f.write(f"  - {proc_name}\n")
        
        # Detailed differences report
        if different_procs:
            diff_file = os.path.join(output_dir, f"detailed_differences_{timestamp}.txt")
            with open(diff_file, 'w', encoding='utf-8') as f:
                f.write("DETAILED PROCEDURE DIFFERENCES\n")
                f.write("=" * 80 + "\n\n")
                
                for proc_name in sorted(different_procs.keys()):
                    f.write(f"\nPROCEDURE: {proc_name}\n")
                    f.write("-" * 80 + "\n")
                    f.write('\n'.join(different_procs[proc_name]))
                    f.write("\n\n")
        
        # JSON report for programmatic processing
        json_file = os.path.join(output_dir, f"comparison_results_{timestamp}.json")
        results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "source_total": len(self.source_procs),
                "target_total": len(self.target_procs),
                "only_in_source": len(only_in_source),
                "only_in_target": len(only_in_target),
                "different": len(different_procs)
            },
            "only_in_source": sorted(list(only_in_source)),
            "only_in_target": sorted(list(only_in_target)),
            "different": sorted(list(different_procs.keys()))
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nReports generated:")
        print(f"  - Summary: {summary_file}")
        if different_procs:
            print(f"  - Detailed differences: {diff_file}")
        print(f"  - JSON results: {json_file}")


def main():
    parser = argparse.ArgumentParser(description='Compare stored procedures between SQL Server database exports')
    parser.add_argument('source', help='Source database export file (your side)')
    parser.add_argument('target', help='Target database export file (client side)')
    parser.add_argument('-o', '--output', default='.', help='Output directory for reports (default: current directory)')
    
    args = parser.parse_args()
    
    # Validate input files
    if not os.path.exists(args.source):
        print(f"Error: Source file '{args.source}' not found")
        return
    
    if not os.path.exists(args.target):
        print(f"Error: Target file '{args.target}' not found")
        return
    
    # Run comparison
    comparer = StoredProcedureComparer()
    comparer.compare_files(args.source, args.target)
    comparer.generate_report(args.output)
    
    print("\nComparison complete!")


if __name__ == "__main__":
    main()
