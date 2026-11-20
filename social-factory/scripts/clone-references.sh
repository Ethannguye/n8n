#!/usr/bin/env bash
# Optional upstream source checkout, kept OUTSIDE our application and never auto-executed.
set -euo pipefail
mkdir -p third_party
for repo in harry0703/MoneyPrinterTurbo tashfeenahmed/freellmapi gitroomhq/postiz-app getopenpost/openpost FerdiKT/postflare azeemkafridi/openpublish; do
  dest="third_party/${repo##*/}"
  if [[ -e "$dest" ]]; then echo "SKIP $dest"; continue; fi
  echo "Cloning upstream: $repo"
  git clone --depth 1 "https://github.com/$repo.git" "$dest"
done
echo "Clones are local only; review license/README before use."
