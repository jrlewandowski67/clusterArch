#!/usr/bin/env bash
set -euo pipefail
APP="${1:-dist/clusterArch.app}"
# Ad-hoc signing is appropriate for CI validation, NOT notarized public distribution.
# Sign nested Mach-O binaries and libraries first, then the outer bundle.
while IFS= read -r -d '' file; do
  if /usr/bin/file -b "$file" | grep -q 'Mach-O'; then
    /usr/bin/codesign --force --sign - "$file"
  fi
done < <(find "$APP/Contents" -type f -print0)
/usr/bin/codesign --force --deep --sign - "$APP"
/usr/bin/codesign --verify --deep --strict --verbose=2 "$APP"
