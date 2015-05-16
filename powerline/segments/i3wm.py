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


def workspaces(pl, strip=0):
	'''Return list of used workspaces

	:param int strip:
		Specifies how many characters from the front of each workspace name should
		be stripped (e.g. to remove workspace numbers). Defaults to zero.

	Highlight groups used: ``workspace``, ``w_visible``, ``w_focused``, ``w_urgent``
	'''
	global conn
	if not conn: conn = i3ipc.Connection()

	return [{
		'contents': w['name'][min(len(w['name']),strip):],
		'highlight_groups': calcgrp(w)
	} for w in conn.get_workspaces()]

@requires_segment_info
def mode(pl, segment_info, default=None):
	'''Returns current i3 mode

	:param str default:
		Specifies the name to be displayed instead of "default".
		By default the segment is left out in the default mode.

	Highligh groups used: ``mode``
	'''
	mode = segment_info['mode']
	if not mode or mode == 'default':
		return default
	return mode
