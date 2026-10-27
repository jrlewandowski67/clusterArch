"""Static sanity checks; does not replace functional macOS testing."""
import subprocess
import sys
from pathlib import Path
app = Path(sys.argv[1])
assert (app / 'Contents' / 'MacOS').is_dir()
for tool in ('blastp', 'makeblastdb', 'hmmsearch', 'hmmbuild'):
    paths = list(app.rglob('bin/' + tool))
    assert paths, f'Missing executable: {tool}'
    for p in paths:
        output = subprocess.check_output(['file', str(p)], text=True)
        assert 'arm64' in output, f'Not ARM64: {p}: {output}'
print('Bundle structure and essential ARM64 tools verified')
