from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys
import re

from powerline.lib.shell import run_cmd

# XXX Warning: module name must not be equal to the segment name as long as this
# segment is imported into powerline.segments.common module.

show_original=False
capacity_full_design=-1
base_dir = '/sys/class/power_supply'

def _file_exists(path, arg):
    return os.path.exists(path.format(arg))

def _get_batteries(file_names):
    import functools
    batteries = []
    for linux_bat in os.listdir('/sys/class/power_supply'):
        if linux_bat.startswith('BAT'):
            pos = [functools.reduce(lambda x, y: x and y, a, True) for a in
                    [[_file_exists(base_dir + '/{0}/' + b, linux_bat) for b in file_names[i]]
                    for i in range(0, len(file_names))]]
            for i in range(0, len(pos)):
                if pos[i]:
                    batteries += [(linux_bat, i)]
                    break
    return batteries

def _get_paths(file_names, batteries, battery):
    return [(base_dir + '/BAT' + str(battery) + '/' + fn)
            for fn in file_names[
                [bat[1] for bat in batteries
                    if bat[0] == ('BAT' + str(battery))][0]]]

def _read(file_names):
    res = []
    for p in file_names:
        with open(p, 'r') as f:
            res += [f.readline().split()[0]]
    return res

def _get_battery(pl):
    if os.path.isdir(base_dir):
        file_names = [['charge_now', 'charge_full', 'charge_full_design'],
                ['energy_now', 'energy_full', 'energy_full_design']]
        batteries = _get_batteries(file_names)

        def _get_capacity(pl, battery):
            current = 0
            full = 1

            paths = _get_paths(file_names, batteries, battery)
            vals = _read(paths)

            current = int(float(vals[0]))
            if not show_original:
                full = int(float(vals[1]))
            elif capacity_full_design == -1:
                full = int(float(vals[2]))
            else:
                full = capacity_full_design
            return (current * 100/full)

        return _get_capacity
    else:
        pl.debug('Not using /sys/class/power_supply: no directory')

    raise NotImplementedError

def _get_battery_status(pl):
    if os.path.isdir(base_dir):
        status_paths = [['status']]
        batteries = _get_batteries(status_paths)

        def _get_status(pl, battery):
            path = _get_paths(status_paths, batteries, battery)
            stat = _read(path)[0]
            if stat == 'Unknown':
                stat = ''
            return stat
        return _get_status
    else:
        pl.debug('Not using /sys/class/power_supply: no directory')

    raise NotImplementedError

def _get_battery_rem_time(pl, battery):
    if os.path.isdir(base_dir):
        rem_time_paths = [['energy_now', 'energy_full', 'power_now', 'status'],
                ['charge_now', 'charge_full', 'current_now', 'status']]
        batteries = _get_batteries(rem_time_paths)

        def _get_rem_time(pl, battery):
            paths = _get_paths(rem_time_paths, batteries, battery)
            vals = _read(paths)
            if vals[2] == '0' or vals[3] == 'Unknown':
                return 0

            curr = int(float(vals[2]))
            charge = int(vals[0])
            full = int(vals[1])
            if vals[3] == 'Charging':
                return (full - charge) / curr
            elif vals[3] == 'Discharging':
                return charge / curr
            else:
                return 0
        return _get_rem_time
    else:
        pl.debug('Not using /sys/class/power_supply: no directory')

    raise NotImplementedError

def _get_capacity(pl, battery):
    global _get_capacity

    def _failing_get_capacity(pl, battery):
        raise NotImplementedError

    try:
        _get_capacity = _get_battery(pl)
    except NotImplementedError:
        _get_capacity = _failing_get_capacity
    except Exception as e:
        pl.exception('Exception while obtaining battery capacity getter: {0}', str(e))
        _get_capacity = _failing_get_capacity
    return _get_capacity(pl, battery)

def _get_status(pl, battery):
    global _get_status

    def _failing_get_status(pl, battery):
        raise NotImplementedError

    try:
        _get_status = _get_battery_status(pl)
    except NotImplementedError:
        _get_status = _failing_get_status
    except Exception as e:
        pl.exception('Exception while obtaining battery capacity getter: {0}', str(e))
        _get_status = _failing_get_status
    return _get_status(pl, battery)

def _get_rem_time(pl, battery):
    global _get_rem_time

    def _failing_get_rem_time(pl, battery):
        raise NotImplementedError

    try:
        _get_rem_time = _get_battery_rem_time(pl, battery)
    except NotImplementedError:
        _get_rem_time = _failing_get_rem_time
    except Exception as e:
        pl.exception('Exception while obtaining battery capacity getter: {0}', str(e))
        _get_rem_time = _failing_get_rem_time
    return _get_rem_time(pl, battery)

def battery(pl, format='{capacity:3.0%}', steps=5, gamify=False, full_heart='O', half_heart='O', empty_heart='O', bat=0, original_health=False, full_design=-1, online=None, offline=None):
    '''Return battery charge status.

        :param str format:
                Percent format in case gamify is False.
        :param int steps:
                Number of discrete steps to show between 0% and 100% capacity if gamify
                is True.
        :param bool gamify:
                Measure in hearts (♥) instead of percentages. For full hearts
                ``battery:full`` highlighting group is preferred, for empty hearts there
                is ``battery:empty``.
        :param str full_heart:
                Heart displayed for “full” part of battery.
        :param str empty_heart:
                Heart displayed for “used” part of battery. It is also displayed using
                another gradient level and highlighting group, so it is OK for it to be
                the same as full_heart as long as necessary highlighting groups are
                defined.
        :param int bat:
                Specifies the battery to display information for.
        :param bool original_health:
                Use the original battery health ase base value. (Experimental)

        ``battery_gradient`` and ``battery`` groups are used in any case, first is
        preferred.

        Highlight groups used: ``battery:full`` or ``battery_gradient`` (gradient) or ``battery``, ``battery:empty`` or ``battery_gradient`` (gradient) or ``battery``.
        '''
    try:
        global show_original
        global capacity_full_design
        show_original = original_health
        capacity_full_design = full_design

        capacity = min(100, _get_capacity(pl, bat))

    except NotImplementedError:
        pl.info('Unable to get battery capacity.')
        return None

    status = ''
    if gamify or ('status' in format):
        try:
            status = _get_status(pl, bat)
        except NotImplementedError:
            pl.info('Unable to get battery status.')
            if 'status' in format:
                return None
        if not gamify and status == '':
            return None

    rem_time = 0
    if 'rem_time' in format:
        try:
            rem_time = _get_rem_time(pl, bat)
        except NotImplementedError:
            pl.info('Unable to get remaining time.')
            return None
        except OSError:
            pl.info('Your BIOS is screwed.')
            return None
        if rem_time == 0 or status == 'Full':
            return None

    rem_sec = int(rem_time * 3600)
    rem_hours = int(rem_sec / 3600)
    rem_sec -= rem_hours * 3600
    rem_minutes = int(rem_sec / 60)

    ret = []
    if gamify:
        denom = int(steps)
        numer = int(denom * capacity / 100 + 0.5)
        hnumer = 0
        if capacity < 100 and (denom * capacity / 100)%1 < 0.5:
            hnumer = 1
        ret.append({
            'contents': full_heart * numer,
            'draw_inner_divider': False,
            'highlight_groups': ['battery:full', 'battery_gradient', 'battery'],
            # Using zero as “nothing to worry about”: it is least alert color.
            'gradient_level': 0,
            })
        ret.append({
            'contents': half_heart * hnumer,
            'draw_inner_divider': False,
            'highlight_groups': ['battery:full', 'battery_gradient', 'battery'],
            # Using zero as “nothing to worry about”: it is least alert color.
            'gradient_level': 50,
            })
        ret.append({
            'contents': empty_heart * (denom - numer - hnumer),
            'draw_inner_divider': False,
            'highlight_groups': ['battery:empty', 'battery_gradient', 'battery'],
            # Using a hundred as it is most alert color.
            'gradient_level': 100,
            })
        if status == 'Charging':
            ret.append({
                'contents': online,
                'draw_inner_divider': False,
                'highlight_groups': ['battery_online', 'battery_gradient', 'battery'],
                'gradient_level': 0,
            })
        elif status == 'Discharging':
            ret.append({
                'contents': offline,
                'draw_inner_divider': False,
                'highlight_groups': ['battery_offline', 'battery_gradient', 'battery'],
                'gradient_level': 0,
            })
        return ret
    else:
        ret.append({
            'contents': format.format(capacity=(capacity / 100.0), status=status, rem_time_hours=rem_hours, rem_time_minutes=rem_minutes),
            'highlight_groups': ['battery_gradient', 'battery'],
            # Gradients are “least alert – most alert” by default, capacity has
            # the opposite semantics.
            'gradient_level': 100 - capacity,
            })
        return ret
