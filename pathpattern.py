
class PathPattern(object):
    def __init__(self, **kwargs):
        self.pid2path = kwargs
        self.ordered_path = self.__get_path_ordered()
        self.ordered_pid = self.__get_pid_ordered()
        self.hash_code = self.__calc_hash()


    def update(self, **kwargs):
        for pid, path in kwargs.iteritems():
            self.pid2path[pid] = path
        self.ordered_path = self.__get_path_ordered()
        self.ordered_pid = self.__get_pid_ordered()
        self.hash_code = self.__calc_hash()

    def __calc_hash(self):
        return hash(self.ordered_path)

    def __get_path_ordered(self):
        return sorted(self.pid2path.items(), key=lambda s: s[0])

    def __get_pid_ordered(self):
        return sorted(self.pid2path.keys())

    def is_complete(self):
        return self.ordered_pid == range(16)

    def identical_full(self, pptn):
        return self.hash_code == pptn.hash_code

    def fit_partial(self, pptn):
        """test if all the paths in pptn fit with the local one"""
        flag = True
        for tup in pptn.ordered_path:
            if tup not in self.ordered_path:
                flag = False
                break
        return flag




