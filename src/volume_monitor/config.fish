# Volume Monitor - Volume monitor for Bitfocus Companion
# Created by Tech127x (https://github.com/tech127x)
# Repository: https://github.com/tech127x/volume-monitor
# Volume Monitor Fish Shell Configuration
# Add to ~/.config/fish/config.fish or source from there

# Add pipx bin directory to PATH (if not already there)
if not contains "$HOME/.local/bin" $PATH
    fish_add_path "$HOME/.local/bin"
end

# Aliases for common commands
alias vm='volume-monitor'
alias vms='volume-monitor --status'
alias vml='volume-monitor --list-devices'
alias vmt='volume-monitor --toggle'
alias vmc='volume-monitor --configure'
alias vma='volume-monitor --list-streams'

# Fish completions for volume-monitor
function __fish_volume_monitor_needs_command
    set -l cmd (commandline -opc)
    if test (count $cmd) -eq 1
        return 0
    end
    return 1
end

# Complete commands
complete -c volume-monitor -f

# Main options
complete -c volume-monitor -s s -l start -d 'Start monitor in background'
complete -c volume-monitor -s f -l start-foreground -d 'Start monitor in foreground'
complete -c volume-monitor -s k -l stop -d 'Stop running monitor'
complete -c volume-monitor -s r -l restart -d 'Restart the monitor'
complete -c volume-monitor -s S -l status -d 'Check if monitor is running'
complete -c volume-monitor -s d -l debug -d 'Enable verbose debug logging'
complete -c volume-monitor -s c -l configure -d 'Run configuration wizard'
complete -c volume-monitor -s t -l toggle -d 'Toggle audio output device'
complete -c volume-monitor -s l -l list-devices -d 'List audio output devices'
complete -c volume-monitor -l list-streams -d 'List per-app audio streams'
complete -c volume-monitor -s h -l help -d 'Show help message'

# Device management
complete -c volume-monitor -s i -l include -d 'Add device to toggle list' -x
complete -c volume-monitor -s x -l exclude -d 'Remove device from toggle list' -x
complete -c volume-monitor -s R -l reset-devices -d 'Clear device filter list'