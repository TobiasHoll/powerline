from __future__ import (unicode_literals, division, absolute_import, print_function)
from powerline.lib.threaded import ThreadedSegment
from powerline.segments import with_docstring
from powerline.theme import requires_segment_info
from os import path
from subprocess import check_call, check_output, run
from glob import glob

MODES = ['locked', 'auto']
@requires_segment_info
class ScreenRotationSegment(ThreadedSegment):

    interval = 1

    current_state = 0

    # output to manage
    initial_output = None
    output = None
    touch_output = None

    # Input devices to manage
    devices = None

    # Basedir for accelerometer
    basedir = None

    # Scale of the accelerometer
    scale = 1.0

    # Input devices to be mapped to the specified output
    mapped_inputs = []
    # Touchpads to be enabled/disabled
    touchpads = []

    STATES = []
    g = 8
    # Gravity triggers (rotation -> value)
    triggers = {'normal': -g, 'inverted': g, 'left': g, 'right': -g}
    checks = { }
    touchpad_state = {'normal': 'enable', 'inverted': 'disable',
            'left': 'disable', 'right': 'disable'}

    accel_x = None
    accel_y = None

    # Disable this segment if it runs in a bar on the wrong output
    mode = 1

    last_oneshot = 0
    bar_needs_resize = None

    rotation_hook = None

    def set_state(self, output, states=['normal', 'inverted', 'left', 'right'],
            gravity_triggers=None, mapped_inputs=[], touchpads=[], touchpad_states=None,
            rotation_hook=None, **kwargs):
        self.initial_output = output
        self.output = output
        self.touch_output = output

        self.rotation_hook = rotation_hook

        for basedir in glob('/sys/bus/iio/devices/iio:device*'):
            if 'accel' in open(path.join(basedir, 'name')).read():
                self.basedir = basedir
                break
        else:
            # No accels found, throw an error
            pass

        self.devices = check_output(['xinput', '--list', '--name-only']).splitlines()
        self.scale = float(open(path.join(self.basedir, 'in_accel_scale')).read())

        if gravity_triggers:
            self.triggers = gravity_triggers
        if touchpad_states:
            self.touchpad_states = touchpad_states

        self.mapped_inputs = mapped_inputs
        self.touchpads = touchpads

        self.current_state = 0
        self.STATES = states

        self.accel_x = open(path.join(basedir, 'in_accel_x_raw'))
        self.accel_y = open(path.join(basedir, 'in_accel_y_raw'))

        self.checks = {
            'normal':   lambda x, y: y < self.triggers['normal'],
            'inverted': lambda x, y: y > self.triggers['inverted'],
            'left':     lambda x, y: x > self.triggers['left'],
            'right':    lambda x, y: x < self.triggers['right']
        }

        self.rotate(self.current_state)
        self.update_touchpad(self.current_state)
        super(ScreenRotationSegment, self).set_state(**kwargs)

    def rotate(self, state):
        check_call(['xrandr', '--output', self.output, '--rotate', self.STATES[state]])

        if (self.STATES[self.current_state] in ['left', 'right']) != (self.STATES[state] in ['left', 'right']):
            self.bar_needs_resize = self.output
            if self.rotation_hook:
                run(self.rotation_hook, shell=True)

        needs_map = [i.decode('utf-8') for i in self.devices if len([j for j in self.mapped_inputs
            if j in i.decode('utf-8')])]

        ids = [check_output(['xinput', '--list', '--id-only', i]).splitlines()[0].decode()
                for i in needs_map]
        for i in ids:
            check_call(['xinput', '--map-to-output', i, self.touch_output])

    def update_touchpad(self, state):
        needs_map = [i.decode('utf-8') for i in self.devices if len([j for j in self.touchpads
            if j in i.decode('utf-8')])]

        for dev in needs_map:
            check_call(['xinput', self.touchpad_state[self.STATES[state]], dev])

    def read_accel(self, f):
        f.seek(0)
        return float(f.read()) * self.scale

    def update(self, *args, **kwargs):
        if self.mode == 0:
            return -1

        x = self.read_accel(self.accel_x)
        y = self.read_accel(self.accel_y)

        for i in range(len(self.STATES)):
            if i == self.current_state:
                continue
            if self.checks[self.STATES[i]](x, y):
                self.rotate(i)
                self.current_state = i
                self.update_touchpad(self.current_state)


        return self.current_state

    def render(self, data, segment_info, show_on_all_outputs=True, name='rotation',
            format='{icon}', icons={'left':'l', 'right':'r', 'normal':'n', 'inverted':'i',
                'locked':'l', 'auto':'a'}, **kwargs):

        channel_name = 'randr.srot'
        channel_value = None
        if 'payloads' in segment_info and channel_name in segment_info['payloads']:
            channel_value = segment_info['payloads'][channel_name]

        if self.bar_needs_resize:
            scrn = self.bar_needs_resize
            self.bar_needs_resize = None
            if segment_info['output'] == scrn:
                segment_info['restart'](scrn)


        # A user wants to map devices to a different screen
        if channel_value and channel_value == 'capture_input' and 'output' in segment_info:
            self.touch_output = segment_info['output']
            self.rotate(self.current_state)
        # A user wants to rotate a different screen
        if channel_value and channel_value == 'capture' and 'output' in segment_info:
            self.output = segment_info['output']
            self.touch_output = segment_info['output']
            self.mode = 1
            self.rotate(self.current_state)
        # A user wants to toggle auto rotation
        if channel_value and not isinstance(channel_value, str) and len(channel_value) == 2 and channel_value[0] == 'toggle_rot' and 'output' in segment_info and self.output == segment_info['output'] and channel_value[1] > self.last_oneshot:
            self.last_oneshot = channel_value[1]
            self.mode = 1 - self.mode
            self.rotate(self.current_state)


        if 'output' in segment_info and segment_info['output'] != self.initial_output:
            self.mode = 0
            if not show_on_all_outputs:
                return None

        if name == 'rotation':
            return [{
                'contents': format.format(rotation=self.STATES[self.current_state],
                    mode=MODES[self.mode], icon=icons[self.STATES[self.current_state]]),
                'payload_name': channel_name,
                'highlight_groups': ['srot:' + self.STATES[data], 'srot:rotation', 'srot']
            }]

        if name == 'mode':
            return [{
                'contents': format.format(rotation=self.STATES[self.current_state],
                    mode=MODES[self.mode], icon=icons[MODES[self.mode]]),
                'payload_name': channel_name,
                'highlight_groups': ['srot:' + MODES[self.mode], 'srot:mode', 'srot']
            }]

        return None


srot = with_docstring(ScreenRotationSegment(),
''' Manage screen rotation and optionally display some information.

Requires ``xinput`` and ``xrandr`` and an accelerometer.
''')
