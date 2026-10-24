#!/usr/bin/env python3
"""Run checks that do not need a game archive or GPU."""
import ast,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for path in ROOT.rglob('*.py'):
    if any(p in {'.git','.local','out','build','build-native','__pycache__'} for p in path.relative_to(ROOT).parts):continue
    ast.parse(path.read_text(),filename=str(path))
for port in sorted((ROOT/'ports').iterdir()):
    info=json.loads((port/'config/media.json').read_text())
    assert len(info['sha256'])==64 and (port/'LICENSE').is_file()
    if (port/'tests').is_dir():
        subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=port,check=True)
print('Python sources, port metadata, and available importer/launcher tests passed')
