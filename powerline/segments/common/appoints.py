from __future__ import (unicode_literals, division, absolute_import, print_function)
from datetime import (datetime, timedelta, timezone)
from powerline.lib.threaded import ThreadedSegment
from powerline.segments import with_docstring
import os

class GoogleCalendarSegment(ThreadedSegment):
    interval = 300
    service = None
    dev_key = None

    def set_state(self, developer_key, credentials=os.path.expanduser('~') + '/.config/powerline/gcalendar_credentials', range=1, **kwargs):
        self.dev_key = developer_key
        self.cred_path = credentials
        self.range = range

        if not self.service:
            import httplib2

            from apiclient.discovery import build
            from oauth2client.file import Storage

            # If the Credentials don't exist or are invalid, run through the native client
            # flow. The Storage object will ensure that if successful the good
            # Credentials will get written back to a file.
            if not os.path.exists(credentials):
                super(GoogleCalendarSegment, self).set_state(**kwargs)
                self.invalid = True
                return None

            storage = Storage(credentials)
            credentials = storage.get()
            if credentials is None or credentials.invalid == True:
                super(GoogleCalendarSegment, self).set_state(**kwargs)
                self.invalid = True
                return None

            # Create an httplib2.Http object to handle our HTTP requests and authorize it
            # with our good Credentials.
            http = httplib2.Http()
            http = credentials.authorize(http)

            self.service = build(serviceName='calendar', version='v3', http=http, developerKey=developer_key)

        self.invalid = False
        super(GoogleCalendarSegment, self).set_state(**kwargs)

    def get_remind(self, dict):
        mx = 0
        for d in dict:
            mx = max(mx, d['minutes'])
        return mx

    def update(self, *args, **kwargs):
        if self.invalid:
            if self.dev_key:
                self.set_state(self.dev_key, self.cred_path, self.range, **kwargs)
            if self.invalid:
                return None

        # Get the list of all calendars
        calendars = self.service.calendarList().list().execute()['items']

        # Get the next count events from every calendar
        result = [self.service.events().list(
            calendarId=id,
            orderBy='startTime',
            singleEvents=True,
            timeMin=datetime.now(timezone.utc).isoformat(),
            timeMax=(datetime.now(timezone.utc) + timedelta(self.range)).isoformat()
        ).execute() for id in [c['id'] for c in calendars]]

        result = [(c['items'], self.get_remind(c['defaultReminders'])) for c in result]
        return sum([[(e,r) for e in c] for c, r in result], []) or []

    def render(self, events, format='{summary}{time}', time_format=' (%H:%M)', count=3, show_count=False, hide_times=[" (00:00)"], **kwargs):
        if events is None:
            return [{
                'contents': 'No valid credentials',
                'highlight_groups': ['appoint:error', 'appoint:urgent', 'appoint']
            }]
        segments = []
        if show_count and len(events) > 0:
            segments += [{
                'contents': str(len(events)),
                'highlight_groups': ['appoint:count', 'appoint']
            }]

        # Sort all events
        def remove_at(string, pos):
            return string[:pos] + string[pos+1:]

        events = [(
            datetime.strptime(ev['start']['date']+'+0000', "%Y-%m-%d%z") if 'date' in ev['start'] else datetime.strptime(remove_at(ev['start']['dateTime'],-3), "%Y-%m-%dT%H:%M:%S%z"),
            ev['summary'],
            ev['location'] if 'location' in ev else '(???)',
            timedelta(minutes=self.get_remind(ev['reminders']['overrides']), seconds=self.interval) if 'reminders' in ev and 'overrides' in ev['reminders'] else timedelta(minutes=bf)
        ) for ev, bf in events]

        events = sorted([(dt - bf, sm, lc, bf) for dt, sm, lc, bf in events])

        if count != 0:
            events = events[:count]

        # check if these events are relevant
        now = datetime.now(timezone.utc)
        return [{
            'contents': format.format(time="" if (dt + bf).strftime(time_format) in hide_times else (dt + bf).strftime(time_format), summary=sm, location=lc),
            'highlight_groups': ['appoint:urgent', 'appoint'] if now < dt + bf else ['appoint'],
            'draw_inner_divider': True
        } for dt, sm, lc, bf in events if dt <= now] + segments

gcalendar = with_docstring(GoogleCalendarSegment(),
'''Return the next ``count`` appoints found in your Google Calendar.

:param string format:
    The format to use when displaying events. Valid fields are time, summary and location.
:param string time_format:
    The format to use when displaying times and dates.
:param int count:
    Number of appoints that shall be shown
:param bool show_count:
    Add an additional segment containing the number of events in the specified range.
:param list hide_times:
    Times (using time_format) not to be displayed as start times.
:param string credentials:
    A path to a file containing credentials to access the Google Calendar API.
:param string developer_key:
    Your Google dev key.
:param int range:
    Number of days into the future to check. No more than 250 events will be displayed in any case.

Highlight groups used: ``appoint``, ``appoint:urgent``, ``appoint:count``.
''')


def appoint(pl, count=1, time_before={"0":0, "1":30}, file_path=os.path.expanduser('~') + '/.appointlist'):
    '''Return the next ``count`` appoints

    :param int count:
        Number of appoints that shall be shown
    :param time_before:
        Time in minutes before the appoint to start alerting

    Highlight groups used: ``appoint``, ``appoint:urgent``.
    '''

    from appoints import (appoint, special, io)
    appoints = io.read_appoints(file_path)
    if appoints == None:
        return None

    appoints = {prio: [ap for ap in appoints if ap.prio == prio]
            for prio in range(0, max([0]+[b.prio for b in appoints])+1)}

    if appoints == None or len(appoints) == 0:
        return None

    now = datetime.now()

    #split into upcoming, current, past events, and events in the far future
    far_away = {prio:[] for prio in appoints.keys()}
    upcoming = {prio:[] for prio in appoints.keys()}
    current = {prio:[] for prio in appoints.keys()}

    time_before = {int(a):int(time_before[a]) for a in time_before}

    lst = 0
    for i in range(0, 1+max(appoints.keys())):
        if i in time_before:
            lst = time_before[i]
        else:
            time_before[i] = lst

    keys = appoints.keys()
    while len(appoints) != 0:
        for i in keys:
            if not i in appoints:
                appoints[i] = []
        far_away = {prio:far_away[prio]+[a for a in appoints[prio]
            if a.is_future(now)
            and not a.is_near(now,timedelta(0,time_before[prio]*60))]
            for prio in keys}
        upcoming = {prio:upcoming[prio]+[a for a in appoints[prio]
            if a.is_near(now,timedelta(0,time_before[prio]*60))]
            for prio in keys}
        current = {prio:current[prio]+[a for a in appoints[prio]
            if a.is_present(now)]
            for prio in keys}
        past = {prio:[a for a in appoints[prio]
            if a.is_past(now)]
            for prio in keys}

        appoints = {prio:[a.evolve() for a in past[prio]
            if a.evolve() != None]
            for prio in past.keys()}
        appoints = {prio:appoints[prio] for prio in appoints.keys()
                if appoints[prio] != []}

    keys = [k for k in keys]
    keys.sort()
    keys.reverse()
    result = []
    def prepend_space(str):
        if str == '':
            return ''
        return ' ' + str
    for k in keys:
        result += [{
            'contents': a.text+prepend_space(a.spec.print()),
            'highlight_groups': ['appoint:urgent']
            } for a in upcoming[k]]
    for k in keys:
        result += [{
            'contents': a.text+prepend_space(a.spec.print()),
            'highlight_groups': ['appoint']
            } for a in current[k]]

    #Write the changed appoints

    tw = []
    for k in keys:
        tw += current[k]
        tw += upcoming[k]
        tw += far_away[k]

    io.write_appoints(tw, file_path)

    if result != []:
        return [result[i] for i in range(0,min(len(result),count))]
    return None
