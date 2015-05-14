# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import i3
import os

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

current_mode = 'default'

def workspaces(pl):
	'''Return workspace list

	Highlight groups used: ``workspace``, ``w_visible``, ``w_focused``, ``w_urgent``
	'''
	if os.path.exists( '/tmp/i3_bindings_mode' ):
	    f = open('/tmp/i3_bindings_mode', 'r')
	    current_mode = f.readline()
	    f.close()
	else:
	    current_mode = 'default'

	if current_mode == 'default':
	    return [{
		'contents': w['name'],
		'highlight_groups': calcgrp(w)
	    } for w in i3.get_workspaces()]
	else:
	    return [{
		'contents': current_mode,
		'highlight_groups':['w_urgent', 'workspace']}] + [{
		'contents': w['name'],
		'highlight_groups': calcgrp(w)
	    } for w in i3.get_workspaces() if w['focused'] ]
