import os
import ast
import json
import argparse

def extract_strings(node):
    strings = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.Str):
            strings.append(child.s)
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            strings.append(child.value)
        strings.extend(extract_strings(child))
    return strings

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            tree = ast.parse(file.read())
            return extract_strings(tree)
        except SyntaxError:
            print(f"Syntax error in file: {file_path}")
            return []

def process_directory(directory):
    all_strings = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)
                if relative_path.startswith('build') or relative_path.startswith('dist'):
                    continue
                strings = process_file(file_path)
                if strings:
                    all_strings[relative_path] = strings
    return all_strings

def save_to_json(strings, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(strings, f, ensure_ascii=False, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Extract strings from Python files in a directory")
    parser.add_argument("directory", help="Directory to scan for Python files")
    parser.add_argument("-o", "--output", default="extracted_strings.json", help="Output JSON file name")
    args = parser.parse_args()

    all_strings = process_directory(args.directory)
    save_to_json(all_strings, args.output)
    print(f"Extracted strings have been saved to {args.output}")

if __name__ == "__main__":
    main()