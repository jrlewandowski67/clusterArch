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
rm -rf build/clusterArch dist/clusterArch.app
python -m PyInstaller --noconfirm --clean --windowed --name clusterArch \
  --paths . --collect-all Bio --collect-all PyQt5 \
  --hidden-import main --hidden-import gui --hidden-import clusterToolsParser \
  --add-data 'htmlvis:htmlvis' --add-data 'testHMM.fasta:.' \
  --add-data 'macDeps:macDeps' --add-data 'clusterTools:clusterTools' macos/launcher.py
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
