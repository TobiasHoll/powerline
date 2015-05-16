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

def workspaces(pl, include_only=None):
	'''Return list of used workspaces

	:param include_only:
		Specifies the workspace types that should be returned.
		Use ``None`` to include all types.

	Highlight groups used: ``workspace``, ``w_visible``, ``w_focused``, ``w_urgent``
	'''
	
	global conn
	if not conn: conn = i3ipc.Connection()
	
	return [{
	    'contents': w['name'],
	    'highlight_groups': calcgrp(w)
	} for w in conn.get_workspaces() if not include_only 
		or 'focused' in include_only and w['focused'] 
		or 'visible' in include_only and w['visible'] 
		or 'urgent' in include_only and w['urgent'] 
		or 'normal' in include_only and not (w['focused'] or w['visible'] or w['urgent']) ]

@requires_segment_info
def mode(pl, segment_info, default=None):
	'''Returns current i3 mode

	:param str default:
		Specifies the name to be displayed instead of "default".
		By default the segment is left out in the default mode.

	Highligh groups used: ``mode``
	'''

	current_mode = segment_info['mode']

	if not current_mode or current_mode == 'default':
		return default
	return current_mode
