# Volume Monitor - Volume monitor for Bitfocus Companion
# Created by Tech127x (https://github.com/tech127x)
# Repository: https://github.com/tech127x/volume-monitor
# Fish Prompt Integration for Volume Monitor
# Add this to your fish_prompt or fish_right_prompt function
# Location: ~/.config/fish/functions/fish_prompt.fish

function fish_prompt --description 'Custom prompt with audio device info'
    # Save the return status
    set -l last_status $status
    
    # Get current audio device
    set -l audio_device ""
    if command -v wpctl >/dev/null 2>&1
        set -l wpctl_output (wpctl status 2>/dev/null)
        if test $status -eq 0
            # Extract default sink info
            set audio_device (echo $wpctl_output | \\
                grep -A 50 "Sinks:" | \\
                grep "^*" | \\
                string match -rg '\d+\.\s+(.+?)\s+\[' | \\
                string trim)
            
            # Get volume if available
            set -l volume_info (wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null)
            if test $status -eq 0
                set -l vol (echo $volume_info | string match -rg 'Volume: (\d+\.\d+)')
                if test -n "$vol"
                    set -l vol_pct (math "round($vol * 100)")
                    set audio_device "$audio_device [$vol_pct%]"
                end
            end
        end
    end
    
    # Build prompt
    set -l prompt ""
    
    # Add audio device if available
    if test -n "$audio_device"
        set prompt "$prompt🔊 $audio_device "
    end
    
    # Add directory
    set prompt "$prompt"(set_color blue)(prompt_pwd)(set_color normal)
    
    # Add git info if in a repo
    if command -v fish_git_prompt >/dev/null 2>&1
        set prompt "$prompt"(fish_git_prompt)
    end
    
    # Add prompt symbol
    if test $last_status -eq 0
        set prompt "$prompt\n> "
    else
        set prompt "$prompt\n"(set_color red)"> "(set_color normal)
    end
    
    echo -n $prompt
end