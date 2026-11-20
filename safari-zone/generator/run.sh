#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -p test_generator.py -v
safari_destination="${1:-../Shirokai-Safari}"
.venv/bin/python generate.py --output "$safari_destination"
.venv/bin/python validate.py "$safari_destination"
.venv/bin/python check_routes.py "$safari_destination"
.venv/bin/python check_natural.py "$safari_destination"
.venv/bin/python check_supports.py "$safari_destination"
.venv/bin/python check_design.py "$safari_destination"
.venv/bin/python render_preview.py "$safari_destination"
.venv/bin/python test_restore_integration.py "$safari_destination"
mkdir -p "$safari_destination/generator" "$safari_destination/biomes/biome_restore"
cp ./*.py requirements.txt run.sh README_TEMPLATE.md "$safari_destination/generator/"
cp restore_biomes.py "$safari_destination/biomes/biome_restore/"
cp README_TEMPLATE.md "$safari_destination/README.md"
rm -f "$safari_destination/terrain.work" "$safari_destination/surface.work.npy" "$safari_destination/reachable.work.npy"
