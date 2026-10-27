"""Copy Homebrew dylibs referenced by bundled tools and rewrite their install names."""
import re
import subprocess
import sys
from pathlib import Path

bindir, app = map(Path, sys.argv[1:3])
libdir = bindir.parent / 'lib'
libdir.mkdir(exist_ok=True)
seen = {}

def deps(path):
    out = subprocess.check_output(['otool', '-L', str(path)], text=True)
    return [line.strip().split(' (compatibility')[0] for line in out.splitlines()[1:] if ' (compatibility' in line]

def collect(path):
    for dep in deps(path):
        if dep.startswith(('/opt/homebrew/', '/usr/local/')):
            source = Path(dep)
            if not source.exists():
                raise RuntimeError(f'Missing library: {dep}')
            target = libdir / source.name
            if dep not in seen:
                if target.exists() and target.resolve() != source.resolve():
                    raise RuntimeError(f'Library filename collision: {target}')
                target.write_bytes(source.read_bytes())
                seen[dep] = target
                collect(target)
            subprocess.check_call(['install_name_tool', '-change', dep, '@loader_path/' + ('../lib/' if path.parent == bindir else '') + source.name, str(path)])

for binary in bindir.iterdir():
    if binary.is_file():
        collect(binary)
print('Copied', len(seen), 'Homebrew dynamic libraries')
