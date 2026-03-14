#!/usr/bin/env python3
"""Patch dashboard.html: replace the JS block using line-based approach."""

HTML = r"c:\Users\MSI\OneDrive\Desktop\insight forge - Copy\templates\dashboard.html"
JS_FILE = r"c:\Users\MSI\OneDrive\Desktop\insight forge - Copy\new_js_block.js"

with open(HTML, encoding='utf-8') as f:
    lines = f.readlines()

# Find the line indices (0-indexed)
# Start: line containing "    <script>" followed by "lucide.createIcons();"
# End: the closing brace of buildCharts() (before updateHealthScore)

start_idx = None
end_idx   = None

for i, line in enumerate(lines):
    if start_idx is None and '<script>' in line and i+1 < len(lines) and 'lucide.createIcons' in lines[i+1]:
        start_idx = i
    # The buildCharts closing brace pattern: "        }" on its own line,
    # followed by an empty line and updateHealthScore function
    if start_idx is not None and end_idx is None:
        stripped = line.strip()
        if stripped == '}':
            # Check if next non-empty line contains updateHealthScore
            for j in range(i+1, min(i+5, len(lines))):
                if 'updateHealthScore' in lines[j] or 'Health Score Gauge' in lines[j]:
                    end_idx = i
                    break

if start_idx is None or end_idx is None:
    print(f"ERROR: could not find markers. start={start_idx}, end={end_idx}")
    for i, l in enumerate(lines[655:700], start=655):
        print(f"L{i+1}: {repr(l[:100])}")
    exit(1)

print(f"Replacing lines {start_idx+1} to {end_idx+1}")

with open(JS_FILE, encoding='utf-8') as f:
    new_js = f.read()

new_lines = lines[:start_idx] + [new_js] + lines[end_idx+1:]

with open(HTML, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"SUCCESS. Total lines: {len(new_lines)}")
