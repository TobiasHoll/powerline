Powerline
=========

[![Build Status](https://travis-ci.org/PH111P/powerline.svg?branch=develop)](https://travis-ci.org/PH111P/powerline)

This is a fork of Kim Silkebækken's (kim.silkebaekken+vim@gmail.com) powerline
(https://github.com/powerline/powerline).

**Powerline is a statusline plugin for vim, and provides statuslines and
prompts for several other applications, including zsh, bash, tmux, IPython,
Awesome, i3 and Qtile. However, this fork is designed to be used in particular
as a replacement for i3's i3bar.**

Features
--------

For general features, consult the documentation of the original powerline. These are
the features that were added in this fork.

* List all workspaces, _and icons of applications currently running on a workspace (using FontAwesome)_
* More multi-monitor options for the workspace segment.
* Enhanced battery segment, having the same features as the i3bar one. Further, this segment
  now works with multiple batteries.
* Enhanced wifi segment to match i3bar's.
* Added a volume segment.
* Added GPMDP support in the player segment.
* Click support (see documentation below)

Changes requiring documentation
-------------------------------

This fork extends the files used by the powerline to configure the color scheme in varios ways:
* `attrs` is now optional, i.e., it can be omitted
* `click` is a new optional field to configure the behavior of a highlight group on a click.
 Where `click` is a drictionary mapping the values `left`, `right`, `middle`, `scroll up` or `scroll down`
 to a string to be executed by a shell. (Currently only the lemonbar binding supports this and only if it is run
 with the `--clicks` flag.)
 Further, the string to be executed may contain a placeholder for the segment's content. This placeholder uses python's
 `string.format` syntax.
* The colors in `fg` and `bg` can be specified directly through hex values using `0x` as a prefix (`0xRRGGBB` or `0xAARRGGBB`). These hex values will be translated back into xterm color indices whenever possible.

####Examples
A configuration to let the workspace segment act like the i3bar's (The substring hack is only required due to the way icons  for programs running on a workspace are implemented. Without using these icons, a simple `{0}` would suffice.):

      "workspace": { "fg": "0xe4e4e4", "bg": "0x0087af", "click": { "left": "i3-msg workspace {0:.2}", "right": "i3-msg move to workspace {0:.2}" } },
      "w_urgent": { "bg": "0x0087af", "fg": "0xffaf00", "click": { "left": "i3-msg workspace {0:.2}", "right": "i3-msg move to workspace {0:.2}" } },

A handy configuration of the volume segment:

      "volume_gradient": { "fg": "green_yellow_red", "bg": "0x005f87", "click": { "scroll up": "pactl set-sink-volume 0 +1%", "scroll down": "pactl set-sink-volume 0 -1%"} },

Note that the `lemonbar` allows for only a fixed number of clickable areas, which has to be specified as an argument (via `-a`).

Installation
------------

Let's start with the hard way.

The following Arch Linux packages should be installed:

* i3 or i3-gaps
* powerline-fonts-git
* lemonbar-xft-git
* ttf-font-awesome
* wpa_actiond (wifi segment)
* wireless_tools (wifi segment)
* python-iwlib (wifi segment)
* i3ipc-python-git (workspace segment)
* python-pyalsaaudio (volume segment)

If you have successfully installed all the previous packages, installing this fork becomes as easy
as

      pip install powerline-status-i3

or

      yaourt -S powerline-i3-git


To actually _use_ the powerline in your i3 setup, replace the following lines in your `.config/i3/config`

      bar {
          status_command i3status
      }

with this line (you may want to adjust the height and the font size):

      exec --no-startup-id powerline-lemonbar --i3 --clicks --height 16 -- -a 40 -b -f "DejaVu Sans Mono for Powerline-10" -f "FontAwesome-10"
