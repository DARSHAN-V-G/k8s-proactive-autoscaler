#!/usr/bin/env bash
# Wrapper alias for destroy_local.sh
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${DIR}/destroy_local.sh" "$@"
