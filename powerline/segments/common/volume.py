# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import alsaaudio


def vol( pl, format='♪: {0}%', control='Master', id= 0 ):
	'''Return the current volume.

	Divider highlight group used: ``time:divider``.

	Highlight groups used: ``time`` or ``date``.
	'''

	avg = 0;

	res = alsaaudio.Mixer(control,id).getvolume();

	for a in res:
	    avg += a;

	return [{
		'contents':	    (format.format('--') if alsaaudio.Mixer(control,id).getmute()[0] == 1 else format.format( int(a / len( res )))),
		'highlight_groups': ['volume_gradient'],
		'divider_highlight_group': None,
		'gradient_level': int(a / len( res )),
	}]

