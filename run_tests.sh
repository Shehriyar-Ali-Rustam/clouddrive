#!/usr/bin/env bash
# ------------------------------------------------------------
#  CloudDrive — run the test suite
#  (env -u PYTHONPATH isolates pytest from any system ROS plugins)
# ------------------------------------------------------------
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest "$@"
