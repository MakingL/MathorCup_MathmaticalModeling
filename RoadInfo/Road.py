# -*- coding: utf-8 -*-
# @Time    : 2019/4/11 21:34
# @Author  : MLee
# @File    : Road.py


class Road(object):
    """docstring for Road"""

    def __init__(self, arg):
        super(Road, self).__init__()
        self.arg = arg


class Route(object):
    """docstring for Route"""

    def __init__(self, arg=None):
        super(Route, self).__init__()
        self.arg = arg

        self.node_set = set()

        # 换乘站点信息
        self.transfer_node_dict = dict(set())

        # 该线路上出现的车次信息
        self.train_number_dict = dict(dict())

        self.node_train_info_dict = dict(list())

        # self.has_visited = False
        self.transfer_visited_dict = dict()

    def add_node(self, node_id):
        self.node_set.add(node_id)

    def add_transfer_node(self, node_id, transfer_node_id):
        if node_id not in self.transfer_node_dict:
            self.transfer_node_dict[node_id] = set()

        self.transfer_node_dict[node_id].add(transfer_node_id)
        self.transfer_visited_dict[node_id] = False

    def with_both_node(self, node1, node2):
        return node1 in self.node_set and node2 in self.node_set

    def has_node(self, node):
        return node in self.node_set

    def add_train_number_info(self, train_number, node_id, arrival_time, dispatch_time):
        # if train_number not in self.train_number_dict:
        #     self.train_number_dict[train_number] = list()
        # # 将该车次的信息添加入列表，方便后面排序
        # self.train_number_dict[train_number].append((node_id, arrival_time, dispatch_time))

        if train_number not in self.train_number_dict:
            self.train_number_dict[train_number] = dict()
        self.train_number_dict[train_number][node_id] = (arrival_time, dispatch_time)

        # 节点的发车信息表
        if node_id not in self.node_train_info_dict:
            self.node_train_info_dict[node_id] = list()
        self.node_train_info_dict[node_id].append((train_number, arrival_time, dispatch_time))
        # if node_id not in self.node_train_info_dict:
        #     self.node_train_info_dict[node_id] = dict()
        # self.node_train_info_dict[node_id][train_number] = (arrival_time, dispatch_time)

    def sort_train_info(self):
        # for train_number in self.train_number_dict.keys():
        #     # 到达时间和出发时间作为键对节点进行 降序 排序
        #     self.train_number_dict[train_number].sort(key=lambda x: (x[1], x[2]), reverse=True)

        for node_id in self.node_train_info_dict.keys():
            # 到达时间和出发时间作为键对节点进行 降序 排序
            self.node_train_info_dict[node_id].sort(key=lambda x: (x[1], x[2]), reverse=True)

    def in_same_train(self, end_node_id, end_time, start_node_id, start_time):
        for train_number, train_arrival_time, _ in self.node_train_info_dict[end_node_id]:
            # 该车次到达终点的时刻要小于等于终止时刻
            if train_arrival_time > end_time:
                continue

            # 起始时刻要小于等于该车次的起始点发车时刻
            if start_node_id in self.train_number_dict[train_number] and \
                    start_time <= self.train_number_dict[train_number][start_node_id][1]:
                # 找到两个顶点在同一车次的列车车次
                return train_number

        return None

    def get_transfer_info(self):
        return self.transfer_node_dict

    def get_latest_arrival_time(self, transfer_node, end_time):
        for train_number, train_arrival_time, dispatch_time in self.node_train_info_dict[transfer_node].items():
            if train_arrival_time < end_time:
                return train_number, train_arrival_time

        return None

    def node_in_the_train(self, node_id, train_number):
        return node_id in self.train_number_dict[train_number]

    def get_node_train_info(self, node_id):
        return self.node_train_info_dict.get(node_id, None)

    def get_train_node_arrival_time(self, train_number, node_id):
        if node_id not in self.train_number_dict[train_number]:
            return None

        return self.train_number_dict[train_number][node_id][0]

    def get_after_transfer_node_id(self, transfer_node_id):
        return self.transfer_node_dict[transfer_node_id]

    def get_train_info_dict(self):
        return self.train_number_dict

    def set_visited(self, transfer_node_id):
        self.transfer_visited_dict[transfer_node_id] = True

    def reset_visited(self, transfer_node_id):
        self.transfer_visited_dict[transfer_node_id] = False

    def is_visited(self, transfer_node_id):
        return self.transfer_visited_dict[transfer_node_id]
