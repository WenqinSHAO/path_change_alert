from collections import Counter
from ripe.atlas.sagan import TracerouteResult
from pathpattern import PathPattern
SUBLEN = 16  # assume that 16 is the pid period
TRACE_INTV = 1800  # the built-in traceroute interval is 30min


def sagan_ip_path(trace):
    """given an sagan traceroute measurement obj,
    return a list of IP hop, each hop contain only one IP address"""
    single_path = []
    full_path = trace.ip_path
    for hops in full_path:
        single_path.append(Counter(hops).most_common(1))
    return single_path


def trace_formatter(res_json):
    """given a json object containing multiple traceroute measurements,
    return a list of sagan traceroute obj"""
    res_list = []
    for rec in res_json:
        rec_sagan = TracerouteResult(rec)
        res_list.append(rec_sagan)
    return res_list


def polish(path_list):
    """given a list of such tuple (pid, path, timestamp),
    pad the list where pid is not continuous"""
    prev = 0
    cur = 1
    while cur < len(path_list):
        prev_path_tup = path_list[prev]
        cur_path_tup = path_list[cur]
        pid_step = cur_path_tup[0] - prev_path_tup[0]
        if pid_step == 1 or pid_step == (1-SUBLEN):
            pass
        else:
            """something missing between prev and cur"""
            filling = ((prev_path_tup[0]+1) % SUBLEN,
                       [],
                       prev_path_tup[2]+TRACE_INTV)
            path_list.insert(prev+1, filling)
        prev += 1
        cur += 1
    return path_list


def path_seg(path_list):
    """given a list of of paths whose corresponding pids are continuous,
    segment the list so that no pid within the seg take different paths"""
    tLen = len(path_list)
    seg_bg = [0]  # stores the beginning index of each segment
    begin = 0
    while True:
        chk = begin + SUBLEN  # chk is the current checkpoint
        if chk >= tLen:
            break
        while chk < tLen:
            if path_list[chk] == path_list[chk-SUBLEN]:
                chk += 1
            else:
                break
        if chk < tLen:
            seg_bg.append(chk) # from chk begins a new segment
            begin = chk
        else:
            break
    # adjust the beginning of segment so that the segment length is maximized
    seg_bg.append(tLen)  # to ease the calculate of segment length
    for i in range(len(seg_bg))[1:-1]:
        left_len = seg_bg[i] - seg_bg[i-1]
        right_len = seg_bg[i+1] - seg_bg[i]
        max_len = max(left_len, right_len)
        chk = seg_bg[i] - 1  # verify if the beginning point can be moved leftward to increase max_len
        if (chk + SUBLEN) < tLen:
            while chk >= 0:
                if path_list[chk] == path_list[chk+SUBLEN]:
                    new_left = chk - seg_bg[i-1]
                    new_right = seg_bg[i+1] - chk
                    new_max = max(new_left, new_right)
                    if new_max > max_len:
                        seg_bg[i] = chk
                        chk -= 1
                    else:
                        break
                else:
                    break

    return seg_bg  # the the last index in the return list is outside the path_list idx range


def learn_pattern(mes):
    """given a historical records in json format, learn pattern and their counts"""
    res_sagan = trace_formatter(mes)
    path_list = []
    pattern_dict = {}  # {hash_code of pattern: {'obj': PathPattern(), 'count': XX}}
    for trace in res_sagan:
        pid = trace.paris_id
        tstp = trace.end_time_timestamp
        path = sagan_ip_path(trace)
        path_list.append((pid, path, tstp))
    # when there is missing pid, fill the hole
    path_list = polish(path_list)
    pure_path = [i[1] for i in path_list]
    # segment path_list
    seg_bg = path_seg(pure_path)
    seg = zip(seg_bg[:-1], seg_bg[1:])
    # for segment longer than 16, accumulate its total pid
    for (bg, ed) in seg:
        p = path_list[bg:ed]
        if len(p) > SUBLEN:
            p_dict = dict((pid, path) for (pid, path, tstp) in p)
            p_pattern = PathPattern(**p_dict)
            if p_pattern.hash_code not in pattern_dict.keys():
                pattern_dict[p_pattern.hash_code] = {'obj': p_pattern,
                                                     'count': len(p)}
            else:
                pattern_dict[p_pattern.hash_code]['count'] += len(p)
    return pattern_dict


def trace_formatter_old(res_json):
    """Given a json object containing multiple traceroute measurements,
    reture a list of dictionary.
    The order of elements is the same as the json obj.
    Each element of the list, a dictionary, correspond to one measurement."""
    # suppose there is only one unique tuple of msm and prb id in json obj
    res_list = []
    for rec in res_json:
        rec_dict = {'endtime': rec['endtime'],
                    'paris_id': rec['paris_id']}
        path=[]
        if 'result' in rec.keys() and rec['result']:
            for hop in rec['result']:
                if not 'result' in hop.keys():
                    path.append('*')
                else:
                    hop_s = set()
                    for trail in hop['result']:
                        if 'from' in trail.keys():
                            if trail['from'] != '*':
                                hop_s.add(trail['from'])
                    if hop_s: # only valid IP in hop_s
                        if len(hop_s) > 1:
                            print "ALERT: different hops observed in one trace meas."
                            pp.pprint(rec)
                        # in the case more than one possible hop are observed, an arbitray one is considered
                        # TODO: handle multiple different IPs in one hop
                        path.append(hop_s.pop())
                    else:
                        path.append('*')
        rec_dict['ip_path'] = path
        res_list.append(rec_dict)
    return res_list


