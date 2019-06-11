# -*- coding: utf-8 -*-
# @Time    : 2019/4/11 21:34
# @Author  : MLee
# @File    : Route.py


class Route(object):
    """docstring for Route"""

    def __init__(self, arg=None):
        super(Route, self).__init__()
        self.arg = arg

        # 线路上的顶点集
        self.node_set = set()

        # 换乘站点信息 --- 该站点所换乘后的顶点及线路信息
        self.transfer_node_dict = dict(set())

        # 该线路上出现的车次信息
        # 车次号对应的信息
        self.train_number_dict = dict(dict())

        # 车次对应的节点时间信息列表
        # 将车次对应的节点信息存储到列表，方便排序和顺序找出相邻节点
        self.train_node_list_dict = dict(list())

        # 顶点上的车次信息
        self.node_train_info_dict = dict(list(tuple()))

        # 一个车次的两个端点
        self.train_points_dict = dict(tuple())

        # 被访问过的顶点信息
        self.node_visited_dict = dict()

        self.traffic_value = 0

    def clear_route_visit_status(self):
        self.node_visited_dict.clear()

    def clear_route_traffic(self):
        self.traffic_value = 0

    def add_node(self, node_id):
        self.node_set.add(node_id)

    def add_transfer_node(self, node_id, transfer_node_id):
        if node_id not in self.transfer_node_dict:
            self.transfer_node_dict[node_id] = set()

        self.transfer_node_dict[node_id].add(transfer_node_id)
        self.node_visited_dict[node_id] = False

    def has_node(self, node):
        return node in self.node_set

    def add_train_number_info(self, train_number, node_id, arrival_time, dispatch_time):
        if train_number not in self.train_number_dict:
            self.train_number_dict[train_number] = dict()
        self.train_number_dict[train_number][node_id] = (arrival_time, dispatch_time)

        if train_number not in self.train_node_list_dict:
            # 将车次对应的节点信息存储到列表，方便排序和顺序找出相邻节点
            self.train_node_list_dict[train_number] = list()
        self.train_node_list_dict[train_number].append((node_id, arrival_time, dispatch_time))

        # 节点的发车信息表
        if node_id not in self.node_train_info_dict:
            self.node_train_info_dict[node_id] = list()
        self.node_train_info_dict[node_id].append((train_number, arrival_time, dispatch_time))

    def preprocess_train_info(self):
        # 找出每个车次的两端的顶点
        for train_number in self.train_number_dict.keys():
            if train_number not in self.train_points_dict:
                self.train_points_dict[train_number] = dict()

            left_point = None
            right_point = None
            min_time = None
            max_time = None
            for node_id in self.train_number_dict[train_number]:
                if min_time is None:
                    min_time = self.train_number_dict[train_number][node_id][0]
                    left_point = node_id
                if max_time is None:
                    max_time = self.train_number_dict[train_number][node_id][0]
                    right_point = node_id

                if self.train_number_dict[train_number][node_id][0] < min_time:
                    left_point = node_id
                    min_time = self.train_number_dict[train_number][node_id][0]
                elif self.train_number_dict[train_number][node_id][0] > max_time:
                    right_point = node_id
                    max_time = self.train_number_dict[train_number][node_id][0]
            self.train_points_dict[train_number] = (left_point, right_point)

        for train_number in self.train_node_list_dict.keys():
            # 到达时间和出发时间作为键对车次的节点进行 升序 排序
            self.train_node_list_dict[train_number].sort(key=lambda x: (x[1], x[2]), reverse=False)

        for node_id in self.node_train_info_dict.keys():
            # 到达时间和出发时间作为键对节点的车次进行 降序 排序
            self.node_train_info_dict[node_id].sort(key=lambda x: (x[1], x[2]), reverse=True)

    def get_train_node_sequence(self, train_number):
        return self.train_node_list_dict[train_number]

    def get_train_points_info(self, train_number):
        return self.train_points_dict[train_number]

    def get_node_k_nearest_train(self, node_id, date_time, k):
        result = list()
        for train_number, train_arrival_time, _ in self.node_train_info_dict[node_id]:
            if train_arrival_time <= date_time:
                result.append(train_number)
                if len(result) >= k:
                    return result
        return result

    def get_train_node_earliest_arrival_time(self, start_node_id, start_time, end_node_id):
        """
        获得符合 start_node -> end_node 最早的列车中， end_node 的到达时间
        :param start_node_id: 起始点
        :param start_time: start_node 的时间
        :param end_node_id: 终止点
        :return: 终止点的到达时间
        """
        for train_number, arrival_time, dispatch_time in self.node_train_info_dict[start_node_id]:
            # 可能在该节点等一段时间
            if arrival_time <= start_time < dispatch_time:
                if end_node_id in self.train_number_dict[train_number]:
                    end_node_arrival_time, _ = self.train_number_dict[train_number][end_node_id]
                    if arrival_time >= end_node_arrival_time:
                        continue
                    return end_node_arrival_time

        node_train_list = list(reversed(self.node_train_info_dict[start_node_id]))
        for train_number, arrival_time, dispatch_time in node_train_list:
            if end_node_id in self.train_number_dict[train_number]:
                end_node_arrival_time, _ = self.train_number_dict[train_number][end_node_id]
                if start_time >= dispatch_time or arrival_time >= end_node_arrival_time :
                    continue
                return end_node_arrival_time

        return None

    def node_in_the_train(self, node_id, train_number):
        return node_id in self.train_number_dict[train_number]

    def get_node_train_info(self, node_id):
        return self.node_train_info_dict.get(node_id, None)

    def get_train_node_arrival_time(self, train_number, node_id):
        if node_id not in self.train_number_dict[train_number]:
            return None

        return self.train_number_dict[train_number][node_id][0]

    def get_time_info_in_train(self, node_id, train_number):
        if node_id not in self.train_number_dict[train_number]:
            return None

        return self.train_number_dict[train_number][node_id]

    def get_train_info_dict(self):
        return self.train_number_dict

    def set_visited(self, node_id):
        self.node_visited_dict[node_id] = True

    def reset_visited(self, node_id):
        self.node_visited_dict[node_id] = False

    def is_visited(self, node_id):
        if node_id not in self.node_visited_dict:
            self.node_visited_dict[node_id] = False
        return self.node_visited_dict[node_id]

    def get_node_train(self):
        return self.node_train_info_dict

    def get_total_train_number(self):
        total_train_number = 0
        for train_list in self.node_train_info_dict.values():
            total_train_number += len(train_list)
        return total_train_number

    def get_transfer_node_number(self):
        return len(self.transfer_node_dict)

    def get_train_node_dispatch_time(self, train_number, node_id):
        return self.train_number_dict[train_number][node_id][1]
