class PathPattern(object):
    """Class for path pattern.

    Attributes:
        pid2path (dict): {pid(int): path(list of strings)};
            dictionary mapping paris id to the IP path that it takes
        ordered_path (list): a list of tuples (pid, path) ordered by pid
        ordered_pid (list): ordered pids
        hash_code (int): hash value of ordered_path
        is_complete (boolean): tells if the path pattern contains all the 16 paris id

    """
    def __init__(self, dict):
        """

        Args:
             dict: supposed to be a dictionary {pid(int): path(list of strings)}
        """
        self.pid2path = dict
        self.ordered_path = self.__get_path_ordered()
        self.ordered_pid = self.__get_pid_ordered()
        self.hash_code = self.__calc_hash()
        self.is_complete = self.__is_complete()

    def update(self, dict):
        """Update the path pattern with given pid path pairs.

        Args:
            dict: supposed to be a dictionary {pid(int): path(list of strings)}

        """
        for pid, path in dict.iteritems():
            self.pid2path[pid] = path
        self.ordered_path = self.__get_path_ordered()
        self.ordered_pid = self.__get_pid_ordered()
        self.hash_code = self.__calc_hash()
        self.is_complete = self.__is_complete()

    def __calc_hash(self):
        """calculate the hash code for the path pattern"""
        return hash(str(self.ordered_path))

    def __get_path_ordered(self):
        """form ordered paths"""
        return sorted(self.pid2path.items(), key=lambda s: s[0])

    def __get_pid_ordered(self):
        """form ordered pid list"""
        return sorted(self.pid2path.keys())

    def __is_complete(self):
        """verify if the paris ids contained in the path pattern is complete"""
        return self.ordered_pid == range(16)

    def identical_full(self, pptn):
        """verify if given path pattern is equal to the local one.

        Args:
            pptn (PathPattern): the one that is compared to the local one

        """
        return self.hash_code == pptn.hash_code

    def fit_partial(self, pptn):
        """Test if all the paths in given path pattern fit with the local one.

        Args:
            pptn (PathPattern): the one that is compared to the local one

        """
        flag = True
        for tup in pptn.ordered_path:
            if tup not in self.ordered_path:
                flag = False
                break
        return flag




