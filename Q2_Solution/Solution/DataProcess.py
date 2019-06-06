# -*- coding: utf-8 -*-
# @Time    : 2019/6/4 20:53
# @Author  : MLee
# @File    : DataProcess.py
from datetime import datetime

from RouteInfo.Route import Route
from UserInfo.User import User


class DataProcess(object):
    """
    docstring for DataProcess
    数据清洗
    """

    def __init__(self,
                 user_data_path="../data/data1_O2D.txt",
                 node_data_path="../data/data2_nodeInfo.txt",
                 train_data_path="../data/data3_trainInfo.txt",
                 road_distance_data_path="../data/data2_distance_between_two_station.txt",
                 user_path_len_file_path="../data/user_path_len.txt",
                 route_data_path="../data/data2_routeInfo.txt"
                 ):
        super(DataProcess, self).__init__()
        self.user_data_path = user_data_path
        self.route_data_path = route_data_path
        self.node_data_path = node_data_path
        self.train_data_path = train_data_path
        self.user_path_len_file_path = user_path_len_file_path
        self.road_distance_data_path = road_distance_data_path

        # 用户 ID 到用户信息对象映射
        self.user_dict = dict()

        # route ID 到 线路信息对象的映射
        self.route_dict = dict()
        self.route_id_2_name_dict = dict()

        # 节点 id 到其信息的映射
        self.node_info_dict = dict(tuple())
        self.node_set = set()

        # 节点名字到车站 id  集合的映射，找出相同站点的节点 id 集合
        self.node_name_2_id_set = dict(set())

        # 车次号到所属线路的映射
        self.train_route_dict = dict()

        # 车站之间的距离
        self.road_distance_dict = dict(dict())

    def parse_hms_time(self, time_str):
        """
        将字符串的时间信息转换为 datetime 对象
        :param time_str: 时间的字符串信息
        :return:
        """
        hour_s, minute_s, second_s = time_str.split(":")
        return datetime(1900, 1, 1, int(hour_s), int(minute_s), int(second_s))

    def load_user_data(self):
        with open(self.user_data_path, "r", encoding="UTF-8") as user_file:
            for line in user_file:
                line = line.strip(" \n")
                if line.startswith("#"):
                    continue

                data = line.replace(" ", "").replace("\t", "")
                data_info = data.split(",")

                if len(data_info) != 5 or not data_info[0].isnumeric():
                    continue

                user_id, start_node_id, dst_node_id, start_time_str, end_time_str = data_info

                start_time = self.parse_hms_time(start_time_str)
                end_time = self.parse_hms_time(end_time_str)

                # 过滤掉异常的用户数据
                # if not self.is_valid_user_data(start_node_id, dst_node_id, start_time, end_time):
                #     self.passed_user_file.write("{}\n".format(line))
                #     continue

                new_user = User(user_id, start_node_id, dst_node_id, start_time, end_time)
                self.user_dict[user_id] = new_user

    def load_route_info(self):
        """
        导入地铁线路表
        :return:
        """

        # 导入地图线路信息
        with open(self.node_data_path, "r", encoding="UTF-8") as node_file:
            for line in node_file:
                # 车站编号,车站名,所属线路
                line = line.strip(" \n")
                if line.startswith("#"):
                    continue

                data = line.replace(" ", "").replace("\t", "")
                data_info = data.split(",")

                if len(data_info) != 3 or not data_info[0].isnumeric():
                    continue

                node_id, node_name, route_id = data_info

                if route_id not in self.route_dict:
                    new_route = Route()
                    self.route_dict[route_id] = new_route

                self.route_dict[route_id].add_node(node_id)

                self.node_info_dict[node_id] = (node_name, route_id)

                # 地图上的顶点集
                self.node_set.add(node_id)

                if node_name not in self.node_name_2_id_set:
                    self.node_name_2_id_set[node_name] = set()
                self.node_name_2_id_set[node_name].add((node_id, route_id))

        # 添加换乘信息
        for transfer_node_set in self.node_name_2_id_set.values():
            for node_id, route_id in transfer_node_set:
                for transfer_node_id, transfer_route_id in transfer_node_set:
                    if transfer_node_id == node_id:
                        continue

                    # 添加换乘节点信息
                    self.route_dict[route_id].add_transfer_node(node_id, transfer_node_id)

        # 读取线路信息
        with open(self.route_data_path, "r", encoding="UTF-8") as route_file:
            for line in route_file:
                # 线路编号,线路名称
                line = line.strip(" \n")
                if line.startswith("#"):
                    continue

                data = line.replace(" ", "").replace("\t", "")
                data_info = data.split(",")

                if len(data_info) != 2 or not data_info[0].isnumeric():
                    continue

                route_id, route_name = data_info

                self.route_id_2_name_dict[route_id] = route_name

        # 导入列车运行信息
        with open(self.train_data_path, "r", encoding="UTF-8") as train_file:
            for line in train_file:
                # 线路编号,车次号,车站编号,到达时刻,发车时刻
                line = line.strip(" \n")
                if line.startswith("#"):
                    continue

                data = line.replace(" ", "").replace("\t", "")
                data_info = data.split(",")

                if len(data_info) != 5 or not data_info[0].isnumeric():
                    continue

                route_id, train_number, node_id, arrival_time_str, dispatch_time_str = data_info
                arrival_time = self.parse_hms_time(arrival_time_str)
                dispatch_time = self.parse_hms_time(dispatch_time_str)

                if train_number not in self.train_route_dict:
                    self.train_route_dict[train_number] = route_id

                # 添加车次信息
                self.route_dict[route_id].add_train_number_info(train_number, node_id,
                                                                arrival_time, dispatch_time)

        for route in self.route_dict.values():
            # 对所有线路上的车次信息进行降序排序
            route.preprocess_train_info()

    def load_road_distance(self):
        """
        导入站点之间的线路数据
        :return:
        """
        with open(self.road_distance_data_path, "r", encoding="UTF-8") as road_distance_file:
            for line in road_distance_file:
                line = line.strip(" \n")
                if line.startswith("#"):
                    continue
                data = line.replace(" ", "").replace("\t", "")
                data_info = data.split(",")

                if len(data_info) != 3 or not data_info[0].isnumeric():
                    continue

                start_node_id, end_node_id, distance = data_info
                if start_node_id not in self.road_distance_dict:
                    self.road_distance_dict[start_node_id] = dict()
                if end_node_id not in self.road_distance_dict:
                    self.road_distance_dict[end_node_id] = dict()
                self.road_distance_dict[start_node_id][end_node_id] = int(distance)
                self.road_distance_dict[end_node_id][start_node_id] = int(distance)

    def is_valid_user_data(self, start_node_id, dst_node_id, start_time, end_time):
        """
        是否为合理的用户数据，要求用户进站和出站应该是不同站点，
        进站时间及出站时间符合因果序
        以及进站及出站的站点应该真实存在
        :param start_node_id: 进站点的 id
        :param dst_node_id: 出站点的 id
        :param start_time: 进站时刻
        :param end_time: 出站时可
        :return:
        """
        # 进站点和出站点相同
        if start_node_id == dst_node_id:
            return False

        # 非法的节点信息
        if start_node_id not in self.node_set or dst_node_id not in self.node_set:
            return False

        # 不合理的时间因果序
        if start_time >= end_time:
            return False
        return True

    def verify_distance_data(self):
        """
        验证距离数据的有效性，确保数据是完整的
        :return:
        """
        missing_road_pair_set = set(tuple())
        for route in self.route_dict.values():
            for train_number in route.train_number_dict.keys():
                train_node_sequence = route.train_node_list_dict[train_number]
                last_node_id = None
                for node_id, _, _ in train_node_sequence:
                    if last_node_id is not None:
                        if last_node_id not in self.road_distance_dict or \
                                node_id not in self.road_distance_dict[last_node_id]:
                            missing_road_pair_set.add((last_node_id, node_id))

                    last_node_id = node_id

        print("Distance data missing: {}".format(missing_road_pair_set))
        return missing_road_pair_set

    def get_invalid_user_set(self):
        if len(self.user_dict) == 0:
            self.load_user_data()

        invalid_user_set = set()
        for user_id in self.user_dict:
            user = self.user_dict[user_id]
            start_node_id, end_node_id = user.start_node_id, user.end_node_id
            start_time, end_time = user.start_time, user.end_time

            if not self.is_valid_user_data(start_node_id, end_node_id, start_time, end_time):
                invalid_user_set.add(user_id)

        return invalid_user_set

    def get_invalid_train_set(self):
        invalid_train = set()
        for route in self.route_dict.values():
            train_dict = route.get_train_info_dict()
            for train_number in train_dict:
                for node in train_dict[train_number]:
                    arrival_time, dispatch_time = train_dict[train_number][node]

                    if arrival_time >= dispatch_time:
                        invalid_train.add(train_number)
                        continue

            return invalid_train
