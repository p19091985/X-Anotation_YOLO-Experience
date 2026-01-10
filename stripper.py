import sys
import os
import ast

def remove_comments_and_docstrings(source_code):
    try:
        parsed = ast.parse(source_code)
    except SyntaxError:
        return source_code
    for node in ast.walk(parsed):
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)):
            continue
        if not len(node.body):
            continue
        if not isinstance(node.body[0], ast.Expr):
            continue
        if not hasattr(node.body[0], 'value') or not isinstance(node.body[0].value, ast.Str):
            continue
        node.body.pop(0)
    return ast.unparse(parsed)
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python stripper.py <file>')
        sys.exit(1)
    file_path = sys.argv[1]
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    clean_code = remove_comments_and_docstrings(content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(clean_code)