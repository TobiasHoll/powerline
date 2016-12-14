Powerline
=========

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
* Click support

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
