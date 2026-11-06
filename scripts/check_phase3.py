"""Check SUMO's model conflict matrix and fixed-time clearances."""
import xml.etree.ElementTree as ET


def check_network(root):
    if root.get('lefthand') != 'true':
        raise ValueError('network is not marked left-hand')
    logics = root.findall('tlLogic')
    if len(logics) != 1 or logics[0].get('type') != 'static':
        raise ValueError('expected one static traffic-light program')
    logic = logics[0]
    connections = [c for c in root.findall('connection') if c.get('tl') == logic.get('id')]
    if not connections:
        raise ValueError('traffic light has no controlled connections')
    indices = {int(c.get('linkIndex')) for c in connections}
    phases = logic.findall('phase')
    if not phases or len(phases) % 3 or indices != set(range(max(indices) + 1)):
        raise ValueError('unexpected links or phase sequence')
    width = len(indices)
    for i in range(0, len(phases), 3):
        green, yellow, red = phases[i:i+3]
        g, y, r = (p.get('state') for p in (green, yellow, red))
        if any(len(s) != width for s in (g, y, r)) or not set(g) <= set('Gr') or 'G' not in g:
            raise ValueError('invalid green state')
        if y != ''.join('y' if c == 'G' else 'r' for c in g) or float(yellow.get('duration')) < 4:
            raise ValueError('yellow clearance is missing or too short')
        if set(r) != {'r'} or float(red.get('duration')) < 2:
            raise ValueError('all-red clearance is missing or too short')
        if float(green.get('duration')) <= 0:
            raise ValueError('green duration must be positive')
    mapped = set()
    for junction in root.findall('junction'):
        lanes = junction.get('intLanes', '').split()
        requests = junction.findall('request')
        relevant = {lanes.index(c.get('via')): int(c.get('linkIndex')) for c in connections if c.get('via') in lanes}
        if not relevant:
            continue
        if len(requests) != len(lanes) or len(relevant) != len(lanes):
            raise ValueError('missing junction conflict information')
        mapped.update(relevant.values())
        for request in requests:
            i = int(request.get('index'))
            foes = request.get('foes')
            if i not in relevant or len(foes) != len(lanes):
                raise ValueError('invalid conflict matrix')
            for j, signal in relevant.items():
                if foes[-1-j] == '1':
                    for phase in phases[::3]:
                        state = phase.get('state')
                        if state[relevant[i]] == state[signal] == 'G':
                            raise ValueError('conflicting green movements')
    if mapped != indices:
        raise ValueError('not every signal was checked against a junction')


if __name__ == '__main__':
    check_network(ET.parse('sumo/sathorn.net.xml').getroot())
    print('PASS: left-hand network, model conflicts and yellow/all-red transitions')
