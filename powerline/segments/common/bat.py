from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys
import re

from powerline.lib.shell import run_cmd

# XXX Warning: module name must not be equal to the segment name as long as this
# segment is imported into powerline.segments.common module.

show_original=False
capacity_full_design=-1

def _get_battery(pl):
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
                    global capacity_full_design
                    with open(cap_path, 'r') as f:
                        current = int(float(f.readline().split()[0]))
                        if not show_original:
                            with open(cap_path1, 'r') as f:
                                full = int(float(f.readline().split()[0]))
                        elif capacity_full_design == -1:
                            with open(cap_path2, 'r') as f:
                                full = int(float(f.readline().split()[0]))
                        else:
                            full = capacity_full_design
                        return (current * 100/full)

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

def _get_battery_rem_time(pl):
    if os.path.isdir('/sys/class/power_supply'):
        linux_bat_fmt = '/sys/class/power_supply/{0}/current_now'
        for linux_bat in os.listdir('/sys/class/power_supply'):
            cap_path = linux_bat_fmt.format(linux_bat)
            if linux_bat.startswith('BAT') and os.path.exists(cap_path):
                pl.debug('Using /sys/class/power_supply with battery {0}', linux_bat)
                def _get_rem_time(pl):
                    curr = 0
                    charge = 0
                    full = 0
                    stat = ''
                    with open(cap_path, 'r') as f:
                        curr = int(f.readline().split()[0])
                        if curr == 0:
                            return 0
                    with open('/sys/class/power_supply/' + linux_bat + '/charge_now', 'r') as f:
                        charge = int(f.readline().split()[0])
                    with open('/sys/class/power_supply/' + linux_bat + '/charge_full', 'r') as f:
                        full = int(f.readline().split()[0])
                    with open('/sys/class/power_supply/' + linux_bat + '/status', 'r') as f:
                        stat = (f.readline().split()[0])
                        if stat == 'Charging':
                            return (full - charge) / curr
                        else:
                            return charge / curr
                return _get_rem_time
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

def _get_rem_time(pl):
    global _get_rem_time

    def _failing_get_rem_time(pl):
        raise NotImplementedError

    try:
        _get_rem_time = _get_battery_rem_time(pl)
    except NotImplementedError:
        _get_rem_time = _failing_get_rem_time
    except Exception as e:
        pl.exception('Exception while obtaining battery capacity getter: {0}', str(e))
        _get_rem_time = _failing_get_rem_time
    return _get_rem_time(pl)

def battery(pl, format='{capacity:3.0%}', steps=5, gamify=False, full_heart='O', empty_heart='O', original_health=False, full_design=-1, online=None, offline=None):
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
        global capacity_full_design
        show_original = original_health
        capacity_full_design = full_design

        capacity = _get_capacity(pl)
    except NotImplementedError:
        pl.info('Unable to get battery capacity.')
        return None

    status = ''
    if 'status' in format:
        try:
            status = _get_status(pl)
        except NotImplementedError:
            pl.info('Unable to get battery status.')
            if 'status' in format:
                return None
        if status == '':
            return None

    rem_time = 0
    if 'rem_time' in format:
        try:
            rem_time = _get_rem_time(pl)
        except NotImplementedError:
            pl.info('Unable to get remaining time.')
            return None
        except OSError:
            pl.info('Your BIOS is screwed.')
            return None
        if rem_time == 0:
            return None

    rem_sec = int(rem_time * 3600)
    rem_hours = int(rem_sec / 3600)
    rem_sec -= rem_hours * 3600
    rem_minutes = int(rem_sec / 60)

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
            'contents': format.format(capacity=(capacity / 100.0), status=status, rem_time_hours=rem_hours, rem_time_minutes=rem_minutes),
            'highlight_groups': ['battery_gradient', 'battery'],
            # Gradients are “least alert – most alert” by default, capacity has
            # the opposite semantics.
            'gradient_level': 100 - capacity,
            })
        return ret
