# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from threading import Thread

from powerline.theme import requires_segment_info
from powerline.segments import Segment, with_docstring


conn = None
try:
    import i3ipc
except ImportError:
    import i3 as conn


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

def workspaces(pl, include_only=None, separate_outputs=False):
	'''Return list of used workspaces

	:param include_only:
		Specifies the workspace types that should be returned.
		Use ``None`` to include all types.

	:param separate_outputs:
		Specifies whether the workspaces shall be grouped after the
		outputs they are visible on if there are at least 2 active outputs

	Highlight groups used: ``workspace``, ``w_visible``, ``w_focused``, ``w_urgent``, ``output``
	'''
	
	global conn
	if not conn: conn = i3ipc.Connection()
	r1 = [o['name'] for o in conn.get_outputs() if o['active']]
	
	if not separate_outputs or len(r1) <= 1:
	    return [{
		'contents': w['name'],
		'highlight_groups': calcgrp(w)
	    } for w in conn.get_workspaces() if not include_only 
		or 'focused' in include_only and w['focused'] 
		or 'visible' in include_only and w['visible'] 
		or 'urgent' in include_only and w['urgent'] 
		or 'normal' in include_only and not (w['focused'] or w['visible'] or w['urgent']) ]
	else:
	    r2 = []
	    for n in r1:
		    r2 += [{
			'contents': n,
			'highlight_groups': ['output']
		    }] + [{
			'contents': w['name'],
			'highlight_groups': calcgrp(w)
		    } for w in conn.get_workspaces() if w['output'] == n and 
			(not include_only or 'focused' in include_only and w['focused'] 
			or 'visible' in include_only and w['visible']
			or 'urgent' in include_only and w['urgent']
			or 'normal' in include_only and not (w['focused'] or w['visible'] or w['urgent']))]
	    return r2
@requires_segment_info
def mode(pl, segment_info, names={"default":None}):
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
