"""
Dependency Analysis Script
Traces imports from entry points to identify active, deprecated, and orphaned files
"""

import ast
import os
from pathlib import Path
from typing import Dict, Set, List
import json

class DependencyAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.all_files: Set[str] = set()
        self.imports_map: Dict[str, Set[str]] = {}
        self.imported_by: Dict[str, Set[str]] = {}
        
    def discover_files(self, directories: List[str]):
        """Discover all Python files in specified directories"""
        for directory in directories:
            dir_path = self.root_dir / directory
            if dir_path.exists():
                for py_file in dir_path.rglob("*.py"):
                    rel_path = py_file.relative_to(self.root_dir)
                    self.all_files.add(str(rel_path))
                    
    def extract_imports(self, file_path: str) -> Set[str]:
        """Extract all imports from a Python file"""
        imports = set()
        try:
            with open(self.root_dir / file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
                        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return imports
    
    def build_dependency_graph(self):
        """Build complete dependency graph"""
        for file_path in self.all_files:
            imports = self.extract_imports(file_path)
            self.imports_map[file_path] = imports
            
            # Map imports to actual files
            for imp in imports:
                # Convert import to file path
                possible_paths = [
                    f"{imp.replace('.', os.sep)}.py",
                    f"{imp.replace('.', os.sep)}/__init__.py"
                ]
                
                for poss_path in possible_paths:
                    if poss_path in self.all_files:
                        if poss_path not in self.imported_by:
                            self.imported_by[poss_path] = set()
                        self.imported_by[poss_path].add(file_path)
                        
    def trace_from_entry_points(self, entry_points: List[str]) -> Set[str]:
        """Trace all files reachable from entry points"""
        visited = set()
        to_visit = list(entry_points)
        
        while to_visit:
            current = to_visit.pop(0)
            if current in visited or current not in self.all_files:
                continue
                
            visited.add(current)
            
            # Add all imports of this file
            for imp in self.imports_map.get(current, set()):
                possible_paths = [
                    f"{imp.replace('.', os.sep)}.py",
                    f"{imp.replace('.', os.sep)}/__init__.py"
                ]
                for poss_path in possible_paths:
                    if poss_path in self.all_files and poss_path not in visited:
                        to_visit.append(poss_path)
                        
        return visited
    
    def find_orphans(self, active_files: Set[str]) -> Set[str]:
        """Find files not imported by any active file"""
        return self.all_files - active_files
    
    def analyze(self, entry_points: List[str]) -> Dict:
        """Run complete analysis"""
        self.discover_files(['api', 'agents'])
        self.build_dependency_graph()
        
        active_files = self.trace_from_entry_points(entry_points)
        orphan_files = self.find_orphans(active_files)
        
        # Categorize files
        results = {
            'total_files': len(self.all_files),
            'active_files': sorted(list(active_files)),
            'orphan_files': sorted(list(orphan_files)),
            'imports_map': {k: list(v) for k, v in self.imports_map.items()},
            'imported_by': {k: list(v) for k, v in self.imported_by.items()}
        }
        
        return results

if __name__ == "__main__":
    analyzer = DependencyAnalyzer(os.getcwd())
    
    entry_points = [
        "api/main.py",
        "agents/core/graph_agent.py",
        "agents/core/multi_agent_orchestrator.py",
        "api/services/chat_service.py"
    ]
    
    results = analyzer.analyze(entry_points)
    
    print(json.dumps(results, indent=2, ensure_ascii=False))
