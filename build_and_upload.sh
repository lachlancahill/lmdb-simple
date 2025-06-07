#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f pip_token.txt ]]; then
  echo "Error: pip_token.txt not found. Please create pip_token.txt containing your PyPI API token." >&2
  exit 1
fi

PYPI_TOKEN=$(<pip_token.txt)

python setup.py sdist bdist_wheel
	twine upload --username __token__ --password "${PYPI_TOKEN}" dist/*
	rm -rf build dist