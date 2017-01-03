from __future__ import (unicode_literals, division, absolute_import, print_function)

import re

from powerline.theme import requires_segment_info
from powerline.bindings.wm import get_i3_connection


WORKSPACE_REGEX = re.compile(r'^[0-9]+: ?')


def workspace_groups(w):
    group = []
    if w['focused']:
        group.append('workspace:focused')
    if w['urgent']:
        group.append('workspace:urgent')
    if w['visible']:
        group.append('workspace:visible')
    group.append('workspace')
    return group

def format_name(name, strip=False):
    if strip:
        return WORKSPACE_REGEX.sub('', name, count=1)
    return name

WS_ICONS = {}

def get_icon(w, separator, icons, show_multiple_icons):
    if 'dummy' in w:
        return ""

    ws_containers = {w_con.name : w_con for w_con in get_i3_connection().get_tree().workspaces()}
    wins = [win for win in ws_containers[w['name']].leaves() if win.parent.scratchpad_state == 'none']
    if len(wins) == 0:
        return ""

    result = ""
    cnt = 0
    for key in icons:
        if any(key == win.window_class for win in wins):
            result += separator + icons[key]
            cnt += 1
    if not show_multiple_icons and cnt > 1:
        if 'multiple' in icons:
            return separator + icons['multiple']
        else:
            return ""
    return result

def get_next_ws(ws, outputs):
    names = [w['name'] for w in ws]
    for i in range(1, 100):
        if not str(i) in names:
            return [{
                'name': str(i),
                'urgent': False,
                'focused': False,
                'visible': False,
                'dummy': True,
                'output': o} for o in outputs]
    return []

@requires_segment_info
def workspaces(pl, segment_info, only_show=None, output=None, strip=0, separator=" ", icons=WS_ICONS, show_multiple_icons=True, show_dummy_workspace=False):
    '''Return list of used workspaces
        :param list only_show:
                Specifies which workspaces to show. Valid entries are ``"visible"``,
                ``"urgent"`` and ``"focused"``. If omitted or ``null`` all workspaces
                are shown.
        :param str output:
                May be set to the name of an X output. If specified, only workspaces
                on that output are shown. Overrides automatic output detection by
                the lemonbar renderer and bindings.
                Use "__all__" to show workspaces on all outputs.
        :param int strip:
                Specifies how many characters from the front of each workspace name
                should be stripped (e.g. to remove workspace numbers). Defaults to zero.
        :param string separator:
                Specifies a string to be inserted between the workspace name and program icons
                and between program icons.
        :param dict icons:
                A dictionary mapping window classes to strings to be used as an icon for that
                window class.
        :param boolean show_multiple_icons:
                If this is set to False, instead of displying multiple icons per workspace,
                the icon "multiple" will be used.
        :param boolean show_dummy_workspace:
                If this is set to True, this segment will alway display an additional, non-existing
                workspace. This workspace will be handled as if it was a non-urgent and non-focused
                regular workspace, i.e., click events will work as with normal workspaces.
        Highlight groups used: ``workspace`` or ``workspace:visible``, ``workspace`` or ``workspace:focused``, ``workspace`` or ``workspace:urgent`` or ``output``.
        '''

    if not output == "__all__":
        output = output or segment_info.get('output')
    else:
        output = None
    if output:
        output = [output]
    else:
        output = [o['name'] for o in get_i3_connection().get_outputs() if o['active']]

    def sort_ws(ws):
        import re
        def natural_key(ws):
            str = ws['name']
            return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', str)]
        return sorted(ws, key=natural_key) + (get_next_ws(ws, output) if show_dummy_workspace else [])

    if len(output) <= 1:
        return [{
            'contents': w['name'][min(len(w['name']), strip):] + get_icon(w, separator, icons, show_multiple_icons),
            'highlight_groups': workspace_groups(w)
            } for w in sort_ws(get_i3_connection().get_workspaces())
            if (not only_show or any(w[typ] for typ in only_show))
            and w['output'] == output[0]
            ]
    else:
        res = []
        for n in output:
            res += [{'contents': n, 'highlight_groups': ['output']}]
            res += [{'contents': w['name'][min(len(w['name']), strip):] + get_icon(w, separator, icons, show_multiple_icons),
                'highlight_groups': workspace_groups(w)} for w in sort_ws(get_i3_connection().get_workspaces())
                if (not only_show or any(w[typ] for typ in only_show))
                and w['output'] == n
                ]
        return res

@requires_segment_info
def mode(pl, segment_info, names={'default': None}):
    '''Returns current i3 mode
        :param str default:
            Specifies the name to be displayed instead of "default".
                By default the segment is left out in the default mode.
        Highligh groups used: ``mode``
        '''

    current_mode = segment_info['mode']

    if current_mode in names:
        return names[current_mode]
    return current_mode

def scratchpad_groups(w):
    group = []
    if w.urgent:
        group.append('scratchpad:urgent')
    if w.nodes[0].focused:
        group.append('scratchpad:focused')
    if w.workspace().name != '__i3_scratch':
        group.append('scratchpad:visible')
    group.append('scratchpad')
    return group


SCRATCHPAD_ICONS = {
        'fresh': 'O',
        'changed': 'X',
        }


def scratchpad(pl, icons=SCRATCHPAD_ICONS):
    '''Returns the windows currently on the scratchpad
        :param dict icons:
            Specifies the strings to show for the different scratchpad window states. Must
                contain the keys ``fresh`` and ``changed``.
        Highlight groups used: ``scratchpad`` or ``scratchpad:visible``, ``scratchpad`` or ``scratchpad:focused``, ``scratchpad`` or ``scratchpad:urgent``.
        '''

    return [{'contents': icons.get(w.scratchpad_state, icons['changed']),
        'highlight_groups': scratchpad_groups(w)
        } for w in get_i3_connection().get_tree().descendents()
        if w.scratchpad_state != 'none']

def active_window(pl, cutoff=100):
        '''
        Returns the title of the currently active window
            :param int cutoff:
                Maximum title length. If the title is longer, the window_class is used instead.
        Highlight groups used: ``active_window_title``.
        '''

        focused = get_i3_connection().get_tree().find_focused()

        cont = focused.name
        if len(cont) > cutoff:
            cont = focused.window_class

        return [{'contents': cont, 'highlight_groups': ['active_window_title']}] if focused.name != focused.workspace().name else []
