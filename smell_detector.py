# smell_detector.py
import ast
from collections import defaultdict

class SmellDetector(ast.NodeVisitor):
    def __init__(self):
        self.findings = defaultdict(list)
    
    def visit_FunctionDef(self, node):
        if len(node.args.args) > 7:
            self.findings[node.lineno].append("Demasiados parámetros (>7)")
        self.generic_visit(node)

def analyze_file(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read())
    detector = SmellDetector()
    detector.visit(tree)
    return detector.findings
