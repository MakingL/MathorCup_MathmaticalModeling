# -*- coding: utf-8 -*-
# @Time    : 2019/4/11 21:21
# @Author  : MLee
# @File    : User.py


class User(object):
    """docstring for User"""

    def __init__(self, start_node_id, end_node_id, start_time, end_time):
        super(User, self).__init__()

        self.start_node_id = start_node_id
        self.end_node_id = end_node_id
        self.start_time = start_time
        self.end_time = end_time

    def get_node_info(self):
        return self.start_node_id, self.end_node_id

    def get_time_info(self):
        return self.start_time, self.end_time


