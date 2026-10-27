"""Bundle Homebrew dylib dependencies of BLAST/HMMER tools without basename collisions."""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

bindir, app = (Path(arg).resolve() for arg in sys.argv[1:3])
libdir = bindir.parent / 'lib'
libdir.mkdir(parents=True, exist_ok=True)
seen = {}  # source install-name -> bundled destination
occupied = {p.name for p in libdir.iterdir() if p.is_file()}


def deps(path):
    output = subprocess.check_output(['otool', '-L', str(path)], text=True)
    return [line.strip().split(' (compatibility')[0]
            for line in output.splitlines()[1:] if ' (compatibility' in line]


def collect(path):
    for dep in deps(path):
        if not dep.startswith(('/opt/homebrew/', '/usr/local/')):
            continue
        source = Path(dep)
        if not source.is_file():
            raise RuntimeError(f'Missing Homebrew dependency: {dep} (required by {path})')
        if dep not in seen:
            name = source.name
            if name in occupied:
                digest = hashlib.sha256(dep.encode()).hexdigest()[:12]
                name = f'{source.stem}-{digest}{source.suffix}'
                if name in occupied:
                    raise RuntimeError(f'Unexpected library name collision: {name}')
            occupied.add(name)
            target = libdir / name
            seen[dep] = target  # mark before recursion, for cyclic dependencies
            target.write_bytes(source.read_bytes())
            subprocess.check_call(['chmod', 'u+w', str(target)])
            subprocess.check_call(['install_name_tool', '-id', '@rpath/' + name, str(target)])
            collect(target)
        target = seen[dep]
        relative = os.path.relpath(target, path.parent)
        subprocess.check_call(['install_name_tool', '-change', dep,
                               '@loader_path/' + relative, str(path)])


for binary in sorted(bindir.iterdir()):
    if binary.is_file():
        collect(binary)
print(f'Bundled {len(seen)} Homebrew library references')
