#!/bin/bash
set -euo pipefail
sed 's|/bigstore|https://console.developers.google.com/m/cloudstorage/b|g' "$1" | sed 's|-output/|-output/o/|g'
