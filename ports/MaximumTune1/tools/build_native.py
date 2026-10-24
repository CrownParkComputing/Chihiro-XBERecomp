#!/usr/bin/env python3
"""Build the standalone experimental SDL3/Vulkan port."""
import argparse, hashlib, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--jobs', type=int, default=3)
    p.add_argument('--generate-only', action='store_true')
    p.add_argument('--deps-source', type=Path)
    p.add_argument('--dxc-source', type=Path)
    a = p.parse_args()
    profile = json.loads((ROOT / 'config/media.json').read_text())
    image = ROOT / 'assets' / profile['executable']
    if hashlib.sha256(image.read_bytes()).hexdigest() != profile['sha256']:
        p.error('Unsupported game executable')
    out = ROOT / 'out/native'
    out.mkdir(parents=True, exist_ok=True)
    if not (out / 'assets').exists():
        (out / 'assets').symlink_to(ROOT / 'assets', target_is_directory=True)
    cmd = ['cmake', '-S', str(ROOT), '-B', str(out), '-G', 'Ninja',
           '-DCMAKE_C_COMPILER=clang', '-DCMAKE_CXX_COMPILER=clang++',
           '-DCMAKE_BUILD_TYPE=RelWithDebInfo', '-DCMAKE_CXX_FLAGS=-march=x86-64-v2']
    if a.deps_source:
        for dep in ['zydis', 'tomlplusplus', 'imgui', 'sdl3', 'vma']:
            cmd.append('-DFETCHCONTENT_SOURCE_DIR_' + dep.upper() + '=' + str(a.deps_source.resolve() / (dep + '-src')))
    if a.dxc_source:
        cmd.append('-DFETCHCONTENT_SOURCE_DIR_DXC=' + str(a.dxc_source.resolve()))
    subprocess.run(cmd, cwd=ROOT, check=True)
    subprocess.run(['cmake', '--build', str(out), '--target',
        'recompile_MaximumTune1' if a.generate_only else 'MaximumTune1', '--parallel', str(max(1, a.jobs))], cwd=ROOT, check=True)
if __name__ == '__main__': main()
