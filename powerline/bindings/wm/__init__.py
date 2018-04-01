# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import requires_segment_info
from powerline.bindings.wm.awesome import AwesomeThread


DEFAULT_UPDATE_INTERVAL = 0.5


conn = None


def i3_subscribe(conn, event, callback):
	'''Subscribe to i3 workspace event

	:param conn:
		Connection returned by :py:func:`get_i3_connection`.
	:param str event:
		Event to subscribe to, e.g. ``'workspace'``.
	:param func callback:
		Function to run on event.
	'''
	try:
		import i3
	except ImportError:
		pass
	else:
		conn.Subscription(callback, event)
		return

	conn.on(event, callback)

	from threading import Thread

	class I3Thread(Thread):
		daemon = True

		def __init__(self, conn):
			super(I3Thread, self).__init__()
			self.__conn = conn

		def run(self):
			self.__conn.main()

	thread = I3Thread(conn=conn)

	thread.start()


def get_i3_connection():
	'''Return a valid, cached i3 Connection instance
	'''
	global conn
	if not conn:
		import i3ipc
		conn = i3ipc.Connection()
	try:
		conn.get_tree()
	except BrokenPipeError:
		import i3ipc
		conn = i3ipc.Connection()
	return conn

def get_randr_outputs():
	'''Return all randr outputs as a list.

	Outputs are represented by a dictionary with at least the ``name``, ``width``,
	``height``, ``primary``, ``x`` and ``y`` keys.
	'''

	from Xlib import X, display
	from Xlib.ext import randr

	d = display.Display()
	s = d.screen()
	window = s.root.create_window(0, 0, 1, 1, 1, s.root_depth)
	outputs = randr.get_screen_resources(window).outputs

	primary = randr.get_output_primary(window).output

	outputs = [(o, randr.get_output_info(window, o, 0)) for o in outputs]
	outputs = [{
	    'name': o[1].name,
	    'crtc': randr.get_crtc_info(window, o[1].crtc, 0) if not o[1].connection else None,
	    'primary': ' primary' if o[0] == primary else None, # space intended for bw comp
	    'status': ['on', 'off'][o[1].connection],
	} for o in outputs] # only return connectad outputs

	outputs = [{
	    'name': o['name'],
	    'primary': o['primary'],
	    'x': o['crtc'].x if o['crtc'] else None,
	    'y': o['crtc'].y if o['crtc'] else None,
	    'height': o['crtc'].height if o['crtc'] else None,
	    'width': o['crtc'].width if o['crtc'] else None,
	    'crtc': o['crtc'],
	    'status': o['status']
	} for o in outputs]

	return outputs


def get_connected_randr_outputs(pl):
	'''Iterate over randr outputs

	Outputs are represented by a dictionary with at least the ``name``, ``width``,
	``height``, ``primary``, ``x`` and ``y`` keys.
	'''
	try:
		for o in get_randr_outputs():
			if o['status'] == 'on':
				yield o

	except ImportError:
		import re
		from powerline.lib.shell import run_cmd

		XRANDR_OUTPUT_RE = re.compile(r'^(?P<name>[0-9A-Za-z-]+) connected(?P<primary> primary)? (?P<width>\d+)x(?P<height>\d+)\+(?P<x>\d+)\+(?P<y>\d+)', re.MULTILINE)

		return (match.groupdict() for match in XRANDR_OUTPUT_RE.finditer(
		    run_cmd(pl, ['xrandr', '-q'])
		))

def get_connected_xrandr_outputs(pl):
	'''Iterate over xrandr outputs (deprecated, use ``get_connected_randr_outputs``)

	Outputs are represented by a dictionary with ``name``, ``width``,
	``height``, ``primary``, ``x`` and ``y`` keys.
	'''

	return get_connected_randr_outputs(pl)

wm_threads = {
	'awesome': AwesomeThread,
}
