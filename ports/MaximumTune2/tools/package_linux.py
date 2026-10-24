#!/usr/bin/env python3
"""Create a portable Linux archive from the current source and local executable."""
import hashlib,json,os,re,shutil,subprocess,tarfile,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def snapshot_source(stage):
    # Release the source that actually produced this binary, including local
    # renderer corrections. Never package game data, build caches or signing keys.
    directories={'android','cmake','config','localization','patches','sdk','src','tests','tools','docs'}
    excluded={'.git','.local','.gradle','build','build-native','out','dist','generated','hdd',
              '__pycache__','jniLibs','third_party','node_modules','assets','libs'}
    suffixes={'.pyc','.xbe','.iso','.bin','.cue','.chd','.zip','.7z','.data','.pic','.fatx',
              '.key','.apk','.keystore','.jks','.so','.a','.o','.exe'}
    files=[]
    for source in ROOT.iterdir():
        if source.is_file() and (source.suffix in {'.md','.txt','.sh'} or source.name in {'.gitignore','LICENSE','CMakePresets.json','UPSTREAM.json'}):
            files.append(source)
        elif source.is_dir() and source.name in directories:
            for current, dirs, names in os.walk(source,followlinks=False):
                dirs[:]=[name for name in dirs if name not in excluded and not name.startswith('build-')]
                for name in names:
                    path=Path(current)/name
                    if path.is_symlink() or path.suffix.lower() in suffixes or name.startswith('.env'):continue
                    files.append(path)
    manifest={}
    for source in sorted(files):
        relative=source.relative_to(ROOT)
        destination=stage/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,destination)
        manifest[str(relative)]=hashlib.sha256(source.read_bytes()).hexdigest()
    (stage/'source-sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()

def main():
    info=json.loads((ROOT/'config/media.json').read_text());target=Path(info['binary']).name
    binary=ROOT/info['binary']
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    revision=revision.stdout.strip() if revision.returncode==0 else None
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='linux-release-',dir=ROOT/'.local') as temp:
        stage=Path(temp)/(target+'-Linux-x86_64');stage.mkdir()
        source_digest=snapshot_source(stage)
        install=stage/Path(info['binary']).parent;install.mkdir(parents=True,exist_ok=True)
        shutil.copy2(binary,install/target)
        subprocess.run(['strip','--strip-unneeded',str(install/target)],check=True)
        libs={}
        def dependencies(path):
            text=subprocess.check_output(['ldd',str(path)],text=True)
            for line in text.splitlines():
                match=re.match(r'\s*(\S+) => (/\S+)',line)
                if match:libs[match.group(1)]=Path(match.group(2))
        dependencies(binary)
        dxc=binary.parent/'libdxcompiler.so'
        if dxc.is_file():shutil.copy2(dxc.resolve(),install/'libdxcompiler.so');dependencies(dxc)
        # Keep the system Vulkan loader and GPU drivers. Bundle SDL and the C++ runtime.
        for name,path in libs.items():
            if name.startswith(('libSDL3.so','libstdc++.so','libgcc_s.so')):shutil.copy2(path.resolve(),install/name)
        local=stage/'.local';local.mkdir(exist_ok=True)
        (local/'setup-image.sha256').write_text(info['sha256']+'\n')
        start=stage/'Start.sh';start.write_text('#!/bin/sh\nset -eu\ncd "$(dirname "$0")"\nexport LD_LIBRARY_PATH="$PWD/'+str(Path(info['binary']).parent)+':${LD_LIBRARY_PATH:-}"\nexec ./run.sh "$@"\n');start.chmod(0o755)
        manifest={'title':info['title'],'commit':revision,'source':'working-tree snapshot','source_sha256':source_digest,'status':info['summary'],'architecture':'x86_64','game_files_included':False,'source_archive':info['archive'],'executable_sha256':hashlib.sha256((install/target).read_bytes()).hexdigest()}
        versions=[]
        for path in install.iterdir():
            if not path.is_file():continue
            symbols=subprocess.check_output(['readelf','--version-info',str(path)],text=True,stderr=subprocess.DEVNULL)
            versions += [tuple(map(int,v.split('.'))) for v in re.findall(r'GLIBC_([0-9.]+)',symbols)]
        manifest['minimum_glibc']='.'.join(map(str,max(versions))) if versions else 'unknown'
        (stage/'release.json').write_text(json.dumps(manifest,indent=2)+'\n')
        output=dist/(stage.name+'.tar.gz')
        with tarfile.open(output,'w:gz') as tar:tar.add(stage,arcname=stage.name)
        print(output);print(json.dumps(manifest))
if __name__=='__main__':main()
