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

mode = 'default'

def workspaces(pl, enable_workspace=False):
	'''Return list of used workspaces

	:param bool enable_workspace:
		Specifies whether to integrate the current non-default wonkspace

	Highlight groups used: ``workspace``, ``w_visible``, ``w_focused``, ``w_urgent``
	'''
	
	global conn
	if not conn: conn = i3ipc.Connection()

	if mode == 'default' or not mode:
	    return [{
		'contents': w['name'],
		'highlight_groups': calcgrp(w)
	    } for w in conn.get_workspaces()]
	else:
	    return [{
		'contents': mode,
		'highlight_groups':['w_urgent', 'workspace']}] + [{
		'contents': w['name'],
		'highlight_groups': calcgrp(w)
	    } for w in conn.get_workspaces() if w['focused'] ]

@requires_segment_info
def mode(pl, segment_info, default=None, disable_output=False):
	'''Returns current i3 mode

	:param str default:
		Specifies the name to be displayed instead of "default".
		By default the segment is left out in the default mode.

	:param bool disable_output:
		Specifies whether to disable the output.

	Highligh groups used: ``mode``
	'''
	mode = segment_info['mode']
	if disable_output:
		return None

	if not mode or mode == 'default':
		return default
	return mode
