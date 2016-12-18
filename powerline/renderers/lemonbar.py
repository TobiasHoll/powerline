# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.renderer import Renderer
from powerline.theme import Theme
from powerline.colorscheme import ATTR_UNDERLINE


class LemonbarRenderer(Renderer):
	'''lemonbar (formerly bar/bar ain't recursive) renderer


	See documentation of `lemonbar <https://github.com/LemonBoy/bar>`_ and :ref:`the usage instructions <lemonbar-usage>`
	'''

	character_translations = Renderer.character_translations.copy()
	character_translations[ord('%')] = '%%{}'

	@staticmethod
	def hlstyle(*args, **kwargs):
		# We don’t need to explicitly reset attributes, so skip those calls
		return ''

	def hl(self, contents, fg=None, bg=None, attrs=None, click=None):
		button_map = { 'left': 1, 'middle': 2, 'right': 3, 'scroll up': 4, 'scroll down': 5 }

		text = ''
		click_count = 0

		if click is not None:
			for key in click:
				if not key in button_map:
					continue
				str = click[key].format(contents).strip()
				text += '%{{A{1}:{0}:}}'.format(str, button_map[key])
				click_count += 1

		if fg is not None:
			if fg is not False and fg[1] is not False:
				if fg[1] <= 0xFFFFFF:
					text += '%{{F#ff{0:06x}}}'.format(fg[1])
				else:
					text += '%{{F#{0:08x}}}'.format(fg[1])

		if bg is not None:
			if bg is not False and bg[1] is not False:
				if bg[1] <= 0xFFFFFF:
					text += '%{{B#ff{0:06x}}}'.format(bg[1])
				else:
					text += '%{{B#{0:08x}}}'.format(bg[1])

		if attrs and attrs & ATTR_UNDERLINE:
			text += '%{+u}'

		return text + contents + '%{F-B--u}' + ('%{A}' * click_count)

	def render(self, *args, **kwargs):
		return '%{{r}}{1}%{{l}}{0}'.format(
			super(LemonbarRenderer, self).render(side='left', segment_info={'output': kwargs.get('matcher_info')}, *args, **kwargs),
			super(LemonbarRenderer, self).render(side='right', segment_info={'output': kwargs.get('matcher_info')}, *args, **kwargs),
		)

	def get_theme(self, matcher_info):
		if not matcher_info or matcher_info not in self.local_themes:
			return self.theme
		match = self.local_themes[matcher_info]

		try:
			return match['theme']
		except KeyError:
			match['theme'] = Theme(
				theme_config=match['config'],
				main_theme_config=self.theme_config,
				**self.theme_kwargs
			)
			return match['theme']


renderer = LemonbarRenderer
