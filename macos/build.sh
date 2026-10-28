#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ "$(uname -s)" == Darwin && "$(uname -m)" == arm64 ]] || { echo 'Apple Silicon macOS required' >&2; exit 1; }
for path in main.py htmlvis macDeps; do [[ -e "$path" ]] || { echo "Missing upstream path: $path" >&2; exit 1; }; done
command -v brew >/dev/null || { echo 'Homebrew required on build machine' >&2; exit 1; }
for tool in blastp makeblastdb hmmsearch hmmbuild hmmpress; do command -v "$tool" >/dev/null || { echo "Build dependency missing: $tool" >&2; exit 1; }; done
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r macos/requirements-build.txt

# Install legacy scientific dependencies in the same
# virtual environment used by PyInstaller.
python -m pip install biopython sortedcontainers bx-python

# Verify dependencies before building.
python - <<'PY'
import sys
import Bio
import sortedcontainers
import bx
from clusterTools import clusterAnalysis

print("Python:", sys.executable)
print("Biopython:", Bio.__version__)
print("sortedcontainers:", sortedcontainers.__file__)
print("bx-python:", bx.__file__)
print("clusterAnalysis:", clusterAnalysis.__file__)
print("All required imports succeeded.")
PY
rm -rf build/clusterArch dist/clusterArch.app

python -m PyInstaller --noconfirm --clean --windowed --name clusterArch \
  --paths . \
  --collect-all Bio \
  --collect-all PyQt5 \
  --collect-all sortedcontainers \
  --collect-all bx \
  --collect-submodules clusterTools \
  --hidden-import main \
  --hidden-import gui \
  --hidden-import clusterToolsParser \
  --hidden-import clusterTools.clusterAnalysis \
  --hidden-import clusterTools.clusterDistance \
  --hidden-import clusterTools.clusterDomStrs \
  --hidden-import clusterTools.clusterGenbank \
  --hidden-import clusterTools.clusterGraphics \
  --hidden-import clusterTools.genbank_process \
  --add-data 'htmlvis:htmlvis' \
  --add-data 'testHMM.fasta:.' \
  --add-data 'macDeps:macDeps' \
  --add-data 'clusterTools:clusterTools' \
  macos/launcher.py

APP="dist/clusterArch.app"
RESOURCE="$APP/Contents/Frameworks"
# PyInstaller one-dir app stores collected data beneath Contents/Frameworks/_internal
if [[ -d "$APP/Contents/Frameworks/_internal" ]]; then RESOURCE="$APP/Contents/Frameworks/_internal"; fi
if [[ -d "$APP/Contents/Resources/_internal" ]]; then RESOURCE="$APP/Contents/Resources/_internal"; fi
mkdir -p "$RESOURCE/bin"
for tool in blastp blastn blastx tblastn tblastx makeblastdb blastdbcmd hmmsearch hmmscan hmmbuild hmmpress hmmalign hmmfetch; do
  path="$(command -v "$tool" || true)"
  [[ -n "$path" ]] && cp -L "$path" "$RESOURCE/bin/$tool"
done
# Collect dynamic library dependencies from Homebrew; reject any unresolved external links.
python3 macos/bundle_dylibs.py "$RESOURCE/bin" "$APP"
python3 macos/check_bundle.py "$APP"
bash macos/sign_bundle.sh "$APP"
mkdir -p dist
/usr/bin/ditto -c -k --sequesterRsrc --keepParent "$APP" dist/clusterArch-macos-arm64.zip
