#!/usr/bin/env python3
"""Merge cross-device tick messages (ntfy topic <topic>-st, last ~12h) into the durable state file.
Same rule as the page: newest timestamp per path wins; equal time -> a real value beats a tombstone.
Used by the GitHub Action in the Pages repo (every ~15 min) and by tests. Writes only when something changed.
usage: st_merge.py STATE_FILE [--topic T | --feed NDJSON] [--add JSON_FILE]   (exit 0; prints 'changed' or 'same')"""
import json, sys, urllib.request, argparse
def merge(P, R):
    ch = False
    for k, b in (R or {}).items():
        if not isinstance(b, list) or len(b) != 2 or not isinstance(b[1], (int, float)): continue
        a = P.get(k)
        if a is None or b[1] > a[1] or (b[1] == a[1] and a[0] is None and b[0] is not None):
            if a != b: ch = True
            P[k] = [b[0], b[1]]
    return ch
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('state'); ap.add_argument('--topic'); ap.add_argument('--feed'); ap.add_argument('--add')
    a = ap.parse_args()
    try: st = json.load(open(a.state))
    except Exception: st = {'v': 1, 'p': {}}
    P = st.setdefault('p', {}); ch = False
    lines = []
    if a.feed: lines = open(a.feed).read().splitlines()
    elif a.topic:
        with urllib.request.urlopen(f'https://ntfy.sh/{a.topic}-st/json?poll=1&since=all', timeout=30) as r: lines = r.read().decode().splitlines()
    for l in lines:
        try:
            m = json.loads(l)
            if m.get('event') == 'message': ch = merge(P, json.loads(m['message']).get('c')) or ch
        except Exception: pass
    if a.add: ch = merge(P, json.load(open(a.add))) or ch
    if ch:
        st['p'] = dict(sorted(P.items()))
        open(a.state, 'w').write(json.dumps(st, separators=(',', ':')) + '\n')
    print('changed' if ch else 'same')
if __name__ == '__main__': main()
