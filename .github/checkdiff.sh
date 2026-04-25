#!/bin/sh
set -e

if ! git diff-index --quiet HEAD --; then
    echo 'Uncommitted changes detected:'
    git diff-index HEAD --
    exit 1
fi
