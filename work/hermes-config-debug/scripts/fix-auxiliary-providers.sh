#!/bin/bash
# Fix all auxiliary providers: set from 'auto' to the given provider.
# Usage: bash fix-auxiliary-providers.sh [provider]
# Default provider: deepseek

PROVIDER="${1:-deepseek}"

TASKS=(
    vision
    web_extract
    compression
    skills_hub
    approval
    mcp
    title_generation
    tts_audio_tags
    triage_specifier
    kanban_decomposer
    profile_describer
    curator
    monitor
    session_search
)

echo "Setting all auxiliary providers to: $PROVIDER"
for task in "${TASKS[@]}"; do
    hermes config set "auxiliary.${task}.provider" "$PROVIDER"
done

echo ""
echo "Verification:"
REMAINING=$(grep -c 'provider: auto' ~/.hermes/config.yaml || echo 0)
echo "  auto providers remaining: $REMAINING"
echo ""
echo "Done. Run '/reset' in your Hermes session for changes to take effect."
