from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info


conn = None


def calcgrp(w):
    group = []
    if w['focused']:
        group.append('w_focused')
    if w['urgent']:
        group.append('w_urgent')
    if w['visible']:
        group.append('w_visible')
    group.append('workspace')
    return group

@requires_segment_info
def workspaces(pl, segment_info, only_show=None, output=None, strip=0):
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

        Highlight groups used: ``workspace`` or ``w_visible``, ``workspace`` or ``w_focused``, ``workspace`` or ``w_urgent``.
        '''

    global conn
    if not conn:
        try:
            import i3ipc
        except ImportError:
            import i3 as conn
        else:
            conn = i3ipc.Connection()

    if not output == "__all__":
        output = output or segment_info.get('output')
    else:
        output = None
    if output:
        output = [output]
    else:
        output = [o['name'] for o in conn.get_outputs() if o['active']]
    if len(output) <= 1:
        return [{
            'contents': w['name'][min(len(w['name']), strip):],
            'highlight_groups': calcgrp(w)
            } for w in conn.get_workspaces()
            if (not only_show or any(w[typ] for typ in only_show))
            and w['output'] == output[0]
            ]
    else:
        res = []
        for n in output:
            res += [{ 'contents': n, 'highlight_groups': ['output']}]
            res += [{'contents': w['name'][min(len(w['name']), strip):],
                'highlight_groups': calcgrp(w)} for w in conn.get_workspaces()
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
