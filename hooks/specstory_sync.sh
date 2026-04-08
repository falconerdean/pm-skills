#!/bin/bash
# Sync current session to SpecStory on session stop.
# Runs silently in background to avoid blocking.
export PATH="$HOME/.local/bin:$PATH"
if command -v specstory &>/dev/null; then
    specstory sync claude --silent 2>/dev/null &
fi
exit 0
