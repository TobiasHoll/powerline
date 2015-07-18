# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)
from datetime import (datetime, timedelta)
import os

def _dtfa( a ):
	return datetime(a[0], a[1], a[2], a[3], a[4])
def _int( lst ):
	return [int(a) for a in lst]

def _calc_td( a ):
	return (datetime(a[0].year+a[2][0], a[0].month, a[0].day, a[0].hour, a[0].minute) - a[0]) + timedelta(a[2][1], 3600 * a[2][2] + 60 * a[2][3])
def _concat( a ):
	result = a[0]
	for i in range(1,len(a)):
		result += ' ' + a[i]
	return result

#Auto-increment counters
def _rewrite_str( s ):
	ln = s.split()
	ln = [a if a[ 0 ] != '#' else '#' + str( 1 + int(a[1:]) ) for a in ln]
	return _concat(ln)
#Remove Locations
def _simplify( s ):
	ln = s.split()
	ln = [a for a in ln if a[0] != '@']
	return _concat(ln)

def appoint(pl, count=1, time_before={"0":0, "1":30}, file_path=os.path.expanduser('~') + '/.appointlist'):
	'''Return the next ``count`` appoints

	:param int count:
		Number of appoints that shall be shown
	:param time_before:
		Time in minutes before the appoint to start alerting

	Highlight groups used: ``appoint``, ``appoint_urgent``.
	'''
	#Don't do anything if the appointlist is locked
	if os.path.exists(file_path + '.lock'):
		return None

	#Read appoints data from appointlist
	if os.path.exists(file_path):
		f = open(file_path, 'r')
	else:
		return None

	lines = [ln.split() for ln in f.readlines() if ln != '\n' and ln[0] != '#']
	f.close()

	appoints = [(_dtfa(_int(lines[4*i])), _dtfa(_int(lines[4*i+1])), _int(lines[4*i+2]), _concat(lines[4*i+3])) for i in range(0, int(len(lines)/4))]
	#seperate the appoints after their priority
	appoints = [((a[0], a[1], [a[2][i] for i in range(0,4)], a[3]), a[2][4]) for a in appoints]
	appoints = {prio: [a[0] for a in appoints if a[1] == prio] for prio in range(0, max([0]+[b[1] for b in appoints])+1)}

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

		far_away = {prio:far_away[prio]+[a for a in appoints[prio] if now < a[0]-timedelta(0,time_before[prio]*60)] for prio in keys}
		upcoming = {prio:upcoming[prio]+[a for a in appoints[prio] if a[0]>now and now>a[0]-timedelta(0,time_before[prio]*60)] for prio in keys}
		current = {prio:current[prio]+[a for a in appoints[prio] if a[0] < now and now < a[1]] for prio in keys}
		past = {prio:[a for a in appoints[prio] if a[1] < now and a[2] != [0,0,0,0]] for prio in keys}
	
		appoints = {prio:[(a[0]+_calc_td(a),a[1]+_calc_td(a),a[2],_rewrite_str(a[3])) for a in past[prio]] for prio in past.keys()}
		appoints = {prio:appoints[prio] for prio in appoints.keys() if appoints[prio] != []}

	keys = [k for k in keys]
	keys.sort()
	keys.reverse()
	result = []
	for k in keys:
		result += [{
		    'contents': _simplify(a[3]),
		    'highlight_groups': ['appoint_urgent']
		} for a in upcoming[k]]
	for k in keys:
		result += [{
		    'contents': _simplify(a[3]),
		    'highlight_groups': ['appoint']
		} for a in current[k]]

	#Write the changed appoints
	f = open(file_path, 'w')
	f.write( "# List of appoints\n"\
		 "#\n"\
		 "# Line 1: Start date\n"\
		 "# Line 2: End date\n"\
		 "# Line 3: Next repitition and priority\n"\
		 "# Line 4: Subject\n"\
		 "#\n"\
		 "# Empty Lines and lines starting with a # will be ignored\n"\
		 "# Any line that gets ignored once will be deleted; excluding this paragraph.\n"\
		 "# Any part of the subject starting with a # will be incremented on every event.\n")
	
	appoints = {prio:current[prio]+upcoming[prio]+far_away[prio] for prio in keys}
	for k in keys:
		for ap in appoints[k]:
			f.write('\n')
			f.write(ap[0].strftime('%Y %m %d %H %M\n'))
			f.write(ap[1].strftime('%Y %m %d %H %M\n'))
			f.write(str(ap[2][0])+' '+str(ap[2][1])+' '+str(ap[2][2])+' '+str(ap[2][3])+' '+str(k)+'\n')
			f.write(ap[3]+'\n')
	f.close()

	if result != []:
		return [result[i] for i in range(0,min(len(result),count))]
	return None
