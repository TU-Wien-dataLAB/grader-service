#!/usr/bin/env bash
set -euo pipefail

# Start the labextension watcher (tsc -w + jupyter labextension watch) in the
# background. It rebuilds lib/ and grader_labextension/labextension/ on save so
# that a browser refresh picks up TypeScript changes.
(
    cd /opt/grader-labextension
    jlpm watch >/tmp/grader-labextension-watch.log 2>&1
) &

# Hand off to the original JupyterHub spawn command (jupyter-labhub ...).
exec "$@"
