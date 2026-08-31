#!/usr/bin/env bash
# Claude Code Tool Hook: Reactive Error Remediation with doc-engine
# Triggered on PostToolExecution when Bash tool commands exit with non-zero status.

set -eo pipefail

payload="$(cat -)"
tool_name="$(echo "$payload" | jq -r '.tool_name // empty')"
exit_code="$(echo "$payload" | jq -r '.tool_result.exit_code // .exit_code // 0')"
output="$(echo "$payload" | jq -r '.tool_result.output // .output // empty')"
command="$(echo "$payload" | jq -r '.tool_input.command // .command // empty')"

# Only process non-zero exit codes from compiler/build tools
if [ "$exit_code" -ne 0 ] && [ -n "$output" ]; then
    cmd_lower="$(echo "$command" | tr '[:upper:]' '[:lower:]')"
    if [[ "$cmd_lower" =~ (zig|cargo|tsc|next|build|npm|pnpm|yarn|sqlx|psql) ]]; then
        # Check doc-engine binary
        if command -v doc-engine >/dev/null 2>&1; then
            # Extract common error patterns
            symbol=""
            lib=""
            if [[ "$cmd_lower" =~ zig ]]; then
                symbol="$(echo "$output" | grep -oP "(?<=no member named ')[^']+" | head -n 1 || true)"
                lib="zig"
            elif [[ "$cmd_lower" =~ cargo ]]; then
                symbol="$(echo "$output" | grep -oP "(?<=no method named \`)[^\`]+" | head -n 1 || true)"
                lib="rust"
            elif [[ "$cmd_lower" =~ (tsc|next|build) ]]; then
                symbol="$(echo "$output" | grep -oP "(?<=Property ')[^']+(?=' does not exist)" | head -n 1 || true)"
                lib="frontend"
            fi

            if [ -n "$symbol" ]; then
                search_res="$(doc-engine search "$symbol" --tier 1 --limit 1 ${lib:+--lib $lib} 2>/dev/null || true)"
                if [ -n "$search_res" ] && [ "$search_res" != "[]" ]; then
                    snippet="$(echo "$search_res" | jq -r '.[0].snippet // empty' | sed 's/<\/\?[ab]>//g' | head -n 8)"
                    doc_id="$(echo "$search_res" | jq -r '.[0].id // empty')"
                    
                    # Format output for Claude Code
                    jq --null-input \
                        --arg banner "💡 [doc-engine Auto-Remediation] Symbol: $symbol (ref: $doc_id)
$snippet

Run 'doc-engine get $doc_id' for the complete compilable template." \
                        '{"system_message": $banner}'
                    exit 0
                fi
            fi
        fi
    fi
fi

# Pass-through
echo "{}"
