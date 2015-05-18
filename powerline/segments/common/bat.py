# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys
import re

from powerline.lib.shell import run_cmd


# XXX Warning: module name must not be equal to the segment name as long as this 
# segment is imported into powerline.segments.common module.

show_original=False

def _get_battery(pl):
	try:
		import dbus
	except ImportError:
		pl.debug('Not using DBUS+UPower as dbus is not available')
	else:
		try:
			bus = dbus.SystemBus()
		except Exception as e:
			pl.exception('Failed to connect to system bus: {0}', str(e))
		else:
			interface = 'org.freedesktop.UPower'
			try:
				up = bus.get_object(interface, '/org/freedesktop/UPower')
			except dbus.exceptions.DBusException as e:
				if getattr(e, '_dbus_error_name', '').endswith('ServiceUnknown'):
					pl.debug('Not using DBUS+UPower as UPower is not available via dbus')
				else:
					pl.exception('Failed to get UPower service with dbus: {0}', str(e))
			else:
				devinterface = 'org.freedesktop.DBus.Properties'
				devtype_name = interface + '.Device'
				for devpath in up.EnumerateDevices(dbus_interface=interface):
					dev = bus.get_object(interface, devpath)
					devget = lambda what: dev.Get(
						devtype_name,
						what,
						dbus_interface=devinterface
					)
					if int(devget('Type')) != 2:
						pl.debug('Not using DBUS+UPower with {0}: invalid type', devpath)
						continue
					if not bool(devget('IsPresent')):
						pl.debug('Not using DBUS+UPower with {0}: not present', devpath)
						continue
					if not bool(devget('PowerSupply')):
						pl.debug('Not using DBUS+UPower with {0}: not a power supply', devpath)
						continue
					pl.debug('Using DBUS+UPower with {0}', devpath)
					return lambda pl: float(
						dbus.Interface(dev, dbus_interface=devinterface).Get(
							devtype_name,
							'Percentage'
						)
					)
				pl.debug('Not using DBUS+UPower as no batteries were found')

	if os.path.isdir('/sys/class/power_supply'):
		linux_bat_fmt = '/sys/class/power_supply/{0}/charge_now'
		linux_bat_fmt1 = '/sys/class/power_supply/{0}/charge_full'
		linux_bat_fmt2 = '/sys/class/power_supply/{0}/charge_full_design'
		for linux_bat in os.listdir('/sys/class/power_supply'):
			cap_path = linux_bat_fmt.format(linux_bat)
			cap_path1 = linux_bat_fmt1.format(linux_bat)
			cap_path2 = linux_bat_fmt2.format(linux_bat)
			if linux_bat.startswith('BAT') and os.path.exists(cap_path) and os.path.exists(cap_path1) and os.path.exists(cap_path2):
				pl.debug('Using /sys/class/power_supply with battery {0}', linux_bat)

				def _get_capacity(pl):
					current = 0
					full = 1
					global show_original
					with open(cap_path, 'r') as f:
						current = int(float(f.readline().split()[0]))
					if not show_original:
						with open(cap_path1, 'r') as f:
							full = int(float(f.readline().split()[0]))
					else:
						with open(cap_path2, 'r') as f:
							full = int(float(f.readline().split()[0]))
					return int(current * 100/full)

				return _get_capacity
		pl.debug('Not using /sys/class/power_supply as no batteries were found')
	else:
		pl.debug('Not using /sys/class/power_supply: no directory')

	raise NotImplementedError

def _get_battery_status(pl):
	if os.path.isdir('/sys/class/power_supply'):
		linux_bat_fmt = '/sys/class/power_supply/{0}/status'
		for linux_bat in os.listdir('/sys/class/power_supply'):
			cap_path = linux_bat_fmt.format(linux_bat)
			if linux_bat.startswith('BAT') and os.path.exists(cap_path):
				pl.debug('Using /sys/class/power_supply with battery {0}', linux_bat)

				def _get_status(pl):
					stat = ''
					with open(cap_path, 'r') as f:
						stat = f.readline().split()[0]
					if stat == 'Unknown':
						stat = ''
					return stat
				return _get_status
		pl.debug('Not using /sys/class/power_supply as no batteries were found')
	else:
		pl.debug('Not using /sys/class/power_supply: no directory')

	raise NotImplementedError

def _get_capacity(pl):
	global _get_capacity
	global show_original

	def _failing_get_capacity(pl):
		raise NotImplementedError

	try:
		_get_capacity = _get_battery(pl)
	except NotImplementedError:
		_get_capacity = _failing_get_capacity
	except Exception as e:
		pl.exception('Exception while obtaining battery capacity getter: {0}', str(e))
		_get_capacity = _failing_get_capacity
	return _get_capacity(pl)

def _get_status(pl):
	global _get_status
	global show_original

	def _failing_get_status(pl):
		raise NotImplementedError

	try:
		_get_status = _get_battery_status(pl)
	except NotImplementedError:
		_get_status = _failing_get_status
	except Exception as e:
		pl.exception('Exception while obtaining battery capacity getter: {0}', str(e))
		_get_status = _failing_get_status
	return _get_status(pl)


def battery(pl, format='{capacity:3.0%}', steps=5, gamify=False, full_heart='O', empty_heart='O', original_health=False):
	'''Return battery charge status.

	:param str format:
		Percent format in case gamify is False.
	:param int steps:
		Number of discrete steps to show between 0% and 100% capacity if gamify
		is True.
	:param bool gamify:
		Measure in hearts (♥) instead of percentages. For full hearts 
		``battery_full`` highlighting group is preferred, for empty hearts there 
		is ``battery_empty``.
	:param str full_heart:
		Heart displayed for “full” part of battery.
	:param str empty_heart:
		Heart displayed for “used” part of battery. It is also displayed using
		another gradient level and highlighting group, so it is OK for it to be 
		the same as full_heart as long as necessary highlighting groups are 
		defined.
	:param bool original_health:
		Use the original battery health ase base value. (Experimental)

	``battery_gradient`` and ``battery`` groups are used in any case, first is 
	preferred.

	Highlight groups used: ``battery_full`` or ``battery_gradient`` (gradient) or ``battery``, ``battery_empty`` or ``battery_gradient`` (gradient) or ``battery``.
	'''
	try:
		global show_original
		show_original = original_health
		capacity = _get_capacity(pl)
	except NotImplementedError:
		pl.info('Unable to get battery capacity.')
		return None
	
	try:
		status = _get_status(pl)
	except NotImplementedError:
		pl.info('Unable to get battery status.')
		if 'status' in format:
			return None
	if 'status' in format and status == '':
		return None

	ret = []
	if gamify:
		denom = int(steps)
		numer = int(denom * capacity / 100)
		ret.append({
			'contents': full_heart * numer,
			'draw_inner_divider': False,
			'highlight_groups': ['battery_full', 'battery_gradient', 'battery'],
			# Using zero as “nothing to worry about”: it is least alert color.
			'gradient_level': 0,
		})
		ret.append({
			'contents': empty_heart * (denom - numer),
			'draw_inner_divider': False,
			'highlight_groups': ['battery_empty', 'battery_gradient', 'battery'],
			# Using a hundred as it is most alert color.
			'gradient_level': 100,
		})
	else:
		ret.append({
			'contents': format.format(capacity=(capacity / 100.0), status=status),
			'highlight_groups': ['battery_gradient', 'battery'],
			# Gradients are “least alert – most alert” by default, capacity has 
			# the opposite semantics.
			'gradient_level': 100 - capacity,
		})
	return ret
