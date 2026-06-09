#!/usr/bin/env fish

# Volume Monitor — https://github.com/Tech127x/volume-monitor
# Copyright (c) 2025 Tech127x
# Setup Fish shell integration for Volume Monitor
# Run this after installation to set up aliases, completions, and prompt

set -l GREEN (set_color green)
set -l YELLOW (set_color yellow)
set -l BLUE (set_color blue)
set -l NC (set_color normal)

echo "$BLUE======================================$NC"
echo "$BLUE  Volume Monitor Fish Integration$NC"
echo "$BLUE======================================$NC"
echo ""

# Check if fish is the current shell
if not test "$SHELL" = "/usr/bin/fish" -o "$SHELL" = "/bin/fish"
    echo "$YELLOW Warning: Current shell is not fish. This setup is for fish shell.$NC"
    echo "Run: fish setup-fish-integration.fish"
    exit 1
end

set -l FISH_CONFIG "$HOME/.config/fish/config.fish"
set -l FISH_COMPLETIONS "$HOME/.config/fish/completions"
set -l FISH_FUNCTIONS "$HOME/.config/fish/functions"

# Create directories
mkdir -p $FISH_COMPLETIONS $FISH_FUNCTIONS

echo "$YELLOWSetting up Fish completions...$NC"

# Generate and install completions
if command -v volume-monitor >/dev/null 2>&1
    volume-monitor --generate-completions
    echo "  $GREEN✓$NC Completions installed"
else
    echo "  $RED✗$NC volume-monitor not found in PATH"
    echo "    Run: pipx ensurepath"
    echo "    Then: fish_add_path ~/.local/bin"
end

echo ""
echo "$YELLOWSetting up aliases...$NC"

# Add aliases to fish config if not already present
if not grep -q "# Volume Monitor aliases" $FISH_CONFIG 2>/dev/null
    echo "" >> $FISH_CONFIG
    echo "# Volume Monitor aliases" >> $FISH_CONFIG
    echo "alias vm='volume-monitor'" >> $FISH_CONFIG
    echo "alias vms='volume-monitor --status'" >> $FISH_CONFIG
    echo "alias vml='volume-monitor --list-devices'" >> $FISH_CONFIG
    echo "alias vmt='volume-monitor --toggle'" >> $FISH_CONFIG
    echo "alias vmc='volume-monitor --configure'" >> $FISH_CONFIG
    echo "alias vma='volume-monitor --list-streams'" >> $FISH_CONFIG
    echo "" >> $FISH_CONFIG
    echo "  $GREEN✓$NC Aliases added to config.fish"
else
    echo "  $GREEN✓$NC Aliases already configured"
end

echo ""
echo "$YELLOWDo you want to add audio device info to your fish prompt?$NC"
echo "This will show the current audio device and volume in your prompt."
echo ""

read -P "Add prompt integration? (y/N): " -l add_prompt

if test "$add_prompt" = "y" -o "$add_prompt" = "Y"
    # Backup existing prompt if any
    if test -f "$FISH_FUNCTIONS/fish_prompt.fish"
        cp "$FISH_FUNCTIONS/fish_prompt.fish" "$FISH_FUNCTIONS/fish_prompt.fish.bak"
        echo "  Backed up existing prompt to fish_prompt.fish.bak"
    end
    
    # Find the prompt integration file
    set -l prompt_file (dirname (status filename))/fish_prompt_integration.fish
    
    if test -f "$prompt_file"
        cp "$prompt_file" "$FISH_FUNCTIONS/fish_prompt.fish"
        echo "  $GREEN✓$NC Prompt integration installed"
    else
        echo "  $YELLOW!$NC Prompt integration file not found"
        echo "    Create your own at: $FISH_FUNCTIONS/fish_prompt.fish"
    end
else
    echo "  Skipped prompt integration"
end

echo ""
echo "$YELLOWAdding pipx to PATH if needed...$NC"

# Ensure pipx path is available
if not contains "$HOME/.local/bin" $PATH
    fish_add_path "$HOME/.local/bin"
    echo "  $GREEN✓$NC Added ~/.local/bin to PATH"
else
    echo "  $GREEN✓$NC PATH already configured"
end

echo ""
echo "$GREEN======================================$NC"
echo "$GREEN  Fish Integration Complete!$NC"
echo "$GREEN======================================$NC"
echo ""
echo "$BLUE Reload your shell:$NC"
echo "  exec fish"
echo ""
echo "$BLUE Available aliases:$NC"
echo "  vm    = volume-monitor"
echo "  vms   = volume-monitor --status"
echo "  vml   = volume-monitor --list-devices"
echo "  vmt   = volume-monitor --toggle"
echo "  vmc   = volume-monitor --configure"
echo "  vma   = volume-monitor --list-streams"
echo ""
echo "$BLUE Try tab completion:$NC"
echo "  volume-monitor --[TAB]"
echo "  vm --[TAB]"
echo ""