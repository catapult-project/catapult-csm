#!/bin/bash
set -euo pipefail
sed 's|https://console.developers.google.com/m/cloudstorage/b|/bigstore|g' "$1" | sed 's|/o/|/|g'
