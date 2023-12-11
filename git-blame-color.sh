#!/usr/bin/env bash
set -euo pipefail

SAVED_PWD=$PWD

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

. "$DIR/venv/bin/activate"

# Only call `less` if command succeeded
result=$(python "$DIR/git_blame_colored_pygments.py" "$@") && echo "$result" | less
