# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import subprocess

def generic_shell(pl, command):
	'''Execute the given command in a shell and return its result

	:param str command:
		The command to execute.

	Highlight groups used: ``generic_shell``.

	Click values supplied: ``contents`` (string)
	'''

	shell = subprocess.Popen(['/bin/sh'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	shell.stdin.write((command + '\n').encode('utf-8'));
	shell.stdin.flush();
	shell.stdin.close();

	contents = shell.stdout.read().decode().strip('\n ')

	return [{
		'contents': contents,
		'highlight_groups': ['generic_shell'],
		'click_values': {'contents': contents}
	}]
