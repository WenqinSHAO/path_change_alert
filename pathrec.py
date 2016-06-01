from ripe.atlas.cousteau import AtlasResultsRequest
from ripe.atlas.sagan import TracerouteResult
from multiprocessing import Process
from pathpattern import PathPattern
from util import sagan_ip_path
from copy import deepcopy
from collections import deque
import time
from util import learn_pattern, SUBLEN, trace_formatter


class PathRec(Process):
    """A class for path pattern learning and change detection.

    If a query is provided when initiating the obj,
    hist path records are queried to construct the major path patterns.
    The process reads from a queue the streaming results and then:
    1/ update the path pattern structure;
    2/ detect path pattern change.

    Attributes:
        pattern (dict) : {hash_code of pattern: {'obj': PathPattern(), 'count': XX}}
            the data structure that maintains complete (longer than 16) path pattern and its counts
        mes_queue (multiprocessing.Queue): a queue from which streaming results are red
        report_queue (multiprocessing.Queue): a queue to which changes are reported
        cur_pattern (pathpattern.PathPattern): the current path pattern before the arrival of new measurement results
        cur_pattern_match (boolean) : if the current pattern partially match ones in self.pattern
        last.three (collections.deque) : max=3, a fixed size FIFO list containing
            last three streaming results in json form
    """
    def __init__(self, mes_queue, report_queue, query={}):
        """
        Args:
            mes_queue (multiprocessing.Queue): a queue from which streaming results are red
            report_queue (multiprocessing.Queue): a queue to which changes are reported
            query (dict): query to fetch historical measurement records;
                see http://ripe-atlas-cousteau.readthedocs.io/en/latest/use.html#results
        """
        if query:
            is_success, res = AtlasResultsRequest(**query).create()
            if is_success:
                self.pattern = learn_pattern(res)
        else:
            self.pattern = []
        self.mes_queue = mes_queue
        self.report_queue = report_queue
        self.cur_pattern = PathPattern(**{})
        self.cur_pattern_match = False
        self.last_three = deque([], 3)
        super(PathRec, self).__init__()

    def run(self):
        """what should be doing when the process is started:
            1/ get stream results from the mes_queue
            2/ report changes to the report_queue
        """
        while True:
            if self.mes_queue.empty():
                time.sleep(1)
            else:
                mes = self.mes_queue.get()
                if mes != 'STOP':
                    self.last_three.append(mes)
                    self.detect(mes)
                else:
                    print '{0} received end signal.'.format(self.name)
                    self.report_queue.put('STOP')
                    return

    def detect(self, mes):
        """The function that updates path pattern structure and detects pattern change upon a new coming measurement.

        Args:
            mes (dict): one single json format traceroute object fetched from the queue
        """
        trace_sagan = TracerouteResult(mes)
        new_p = {trace_sagan.paris_id: sagan_ip_path(trace_sagan)}
        if self.cur_pattern.is_complete:
            new_pptn = PathPattern(new_p)
            if self.cur_pattern.fit_partial(new_pptn):
                # the new coming path fit with current pattern, thus no change
                if self.cur_pattern.hash_code not in self.pattern.keys():  # how a new pattern begin to exist
                    self.pattern[self.cur_pattern.hash_code]['count'] = SUBLEN
                self.pattern[self.cur_pattern.hash_code]['count'] += 1  # increment the counter of an existing pattern
            else:
                # the new coming path doesn't fit with current path, change
                self.report_queue.put(mes)  # report a change
                self.cur_pattern = new_pptn
                self.cur_pattern_match = self.match_existing_pptn(new_pptn)
        else:
            if self.cur_pattern_match:
                # current pattern partially matches at least one complete pattern
                new_pptn = deepcopy(self.cur_pattern)
                new_pptn.update(new_p)
                if self.match_existing_pptn(new_pptn):
                    # after updating with the new coming path,
                    # if the current path continuous to match at least one existing complete pattern, no change happens
                    self.cur_pattern = new_pptn
                else:
                    # after update, no longer match, change!
                    self.cur_pattern = PathPattern(new_p)
                    self.cur_pattern_match = self.match_existing_pptn(self.cur_pattern)
                    self.report_queue.put(mes)  # report a change
            else:
                # current pattern matches no complete one
                if len(self.last_three) >= 3:
                    res_sagan = trace_formatter(self.last_three)
                    l3_p = {}
                    for rec in res_sagan:
                        test_p[rec.paris_id] = sagan_ip_path(rec)
                    l3_pptn = PathPattern(**l3_p)
                    if self.match_existing_pptn(l3_pptn):
                        # if last three path matches one complete pattern,
                        # the first one of the three is marked as change
                        self.report_queue.put(self.last_three[0])  # report a change
                        self.cur_pattern = l3_pptn
                        self.cur_pattern_match = True
                    else:
                        # updating the current pattern that matches on one"""
                        self.cur_pattern.update(**new_p)
        return

    def match_existing_pptn(self, pptn):
        """Given a path pattern, verify if it matches to at least one known complete pattern

        Args:
            pptn (pathpattern.PathPattern): a path pattern

        Returns:
            flag (boolean) : true if matches at least one, false otherwise
        """
        flag = False
        for key in self.pattern.keys():
            if self.pattern[key]['obj'].fit_partial(pptn):
                flag = True
                break
        return flag





