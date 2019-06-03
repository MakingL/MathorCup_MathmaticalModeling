# -*- coding: utf-8 -*-
# @Time    : 2019/4/11 20:44
# @File    : Solution2A.py
import logging
from datetime import datetime

from RouteInfo.Route import Route
from UserInfo.User import User


class Solution2A(object):
    """
    docstring for Solution2A
    @已知用户出行数据: 进地铁站刷卡站点，进站时间，出站站点，出站时间
    @已知地铁运行时间表及地铁线路表，站点之间的距离
    @ 还原乘客出行的真实线路信息： 何时何地搭乘何辆列车
    @ 统计用户出行的长度及线路的客流量
    """

    def __init__(self,
                 user_data_path="../data/data1_O2D.txt",
                 node_data_path="../data/data2_nodeInfo.txt",
                 train_data_path="../data/data3_trainInfo.txt",
                 road_distance_data_path="../data/data2_distance_between_two_station.txt",
                 answer_file_path="../data/answer_2A.txt",
                 user_path_len_file_path="../data/user_path_len.txt",
                 route_traffic_file_path="../data/route_traffic.txt",
                 passed_user_file_path="../data/passed_user_2A.txt",
                 route_data_path="../data/data2_routeInfo.txt"):
        super(Solution2A, self).__init__()

        self.user_data_path = user_data_path
        self.route_data_path = route_data_path
        self.node_data_path = node_data_path
        self.train_data_path = train_data_path
        self.answer_file_path = answer_file_path
        self.user_path_len_file_path = user_path_len_file_path
        self.route_traffic_file_path = route_traffic_file_path
        self.road_distance_data_path = road_distance_data_path
        self.passed_user_file_path = passed_user_file_path

        logging.info("user_data_path: {}".format(self.user_data_path))
        logging.info("route_data_path: {}".format(self.route_data_path))
        logging.info("node_data_path: {}".format(self.node_data_path))
        logging.info("train_data_path: {}".format(self.train_data_path))
        logging.info("answer_file_path: {}".format(self.answer_file_path))
        logging.info("user_path_len_file_path: {}".format(self.user_path_len_file_path))
        logging.info("route_traffic_file_path: {}".format(self.route_traffic_file_path))
        logging.info("road_distance_data_path: {}".format(self.road_distance_data_path))
        logging.info("passed_user_file_path: {}".format(self.passed_user_file_path))

        # 用户 ID 到用户信息对象映射
        self.user_dict = dict()
        self.user_list = list()

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

        # 打开结果文件，清空文件
        self.user_path_len_file = open(self.user_path_len_file_path, "w+", encoding="UTF-8")
        self.route_traffic_file = open(self.route_traffic_file_path, "w+", encoding="UTF-8")
        self.passed_user_file = open(self.passed_user_file_path, "w+", encoding="UTF-8")
        self.answer_file = open(self.answer_file_path, "w+", encoding="UTF-8")

        # 车站之间的距离
        self.road_distance_dict = dict(dict())

        # 线路上的客流量信息
        self.route_traffic_info = dict()

        # 统计数据特征的 用户采样率: 1/user_sample_freq
        self.user_sample_freq = 10000
        # 用户出行线路长度数据的缓冲区大小
        self.len_data_buff_size = max(50, self.user_sample_freq / 1000)
        self.user_path_len_buff = list()

        self.sampled_user_set = set()

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
                if not self.is_valid_user_data(start_node_id, dst_node_id, start_time, end_time):
                    self.passed_user_file.write("{}\n".format(line))
                    continue

                new_user = User(user_id, start_node_id, dst_node_id, start_time, end_time)
                self.user_dict[user_id] = new_user
                self.user_list.append(new_user)

        # 用户 buffer 预排序
        self.pre_process_user()

    def pre_process_user(self):
        """
        用户数据预排序: 按照进站时刻升序排列
        :return:
        """
        self.user_list.sort(key=lambda x: x.start_time, reverse=False)

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

    def load_data(self):
        self.load_route_info()
        self.load_road_distance()
        self.load_user_data()

        train_count_total = 0
        node_total = 0
        node_train_number_total = 0
        total_transfer_node = 0
        for route in self.route_dict.values():
            train_count_total += len(route.get_train_info_dict())
            node_total += len(route.get_node_train())
            node_train_number_total += route.get_total_train_number()
            total_transfer_node += route.get_transfer_node_number()

        logging.info("train count is: {}".format(train_count_total))
        logging.info("user count is: {}".format(len(self.user_dict)))
        logging.info("node count is: {}".format(node_total))
        logging.info("node train number count is: {}".format(node_train_number_total))
        logging.info("average node train number count is: {}".format(node_train_number_total / node_total))
        logging.info("transfer node count is: {}".format(total_transfer_node))

    def verify_distance_data(self):
        """
        验证距离数据的有效性
        :return:
        """
        missing_road_pair_set = set(tuple())
        for route in self.route_dict.values():
            train_info = route.get_train_info_dict()
            for train_number in train_info.keys():
                train_node_sequence = route.get_train_node_sequence(train_number)
                last_node_id = None
                for node_id, _, _ in train_node_sequence:
                    if last_node_id is not None:
                        if last_node_id not in self.road_distance_dict or \
                                node_id not in self.road_distance_dict[last_node_id]:
                            missing_road_pair_set.add((last_node_id, node_id))

                    last_node_id = node_id
        return missing_road_pair_set

    def parse_hms_time(self, time_str):
        """
        将字符串的时间信息转换为 datetime 对象
        :param time_str: 时间的字符串信息
        :return:
        """
        hour_s, minute_s, second_s = time_str.split(":")
        return datetime(1900, 1, 1, int(hour_s), int(minute_s), int(second_s))

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

    def get_invalid_user_set(self):
        invalid_user_set = set()
        for user_id in self.user_dict:
            user = self.user_dict[user_id]
            start_node_id, end_node_id = user.get_node_info()
            start_time, end_time = user.get_time_info()

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

    def get_user_path(self, user_id):
        """
        还原用户出行的真实路线
        :param user_id: 用户 id
        :return: 用户出行的真实线路信息，不能还原则返回 None
        """
        # logging.info("start find user: {} path".format(user_id))

        # 清除所有线路上的搜索痕迹
        for route in self.route_dict.values():
            route.clear_route_visit_status()

        user = self.user_dict[user_id]
        # 用户出行信息
        start_node_id, end_node_id = user.get_node_info()
        start_time, end_time = user.get_time_info()

        # logging.info(
        #     "user: {} start node: {} start time: {} and end node: {} end time: {}".format(user_id,
        #                                                                                   start_node_id,
        #                                                                                   start_time,
        #                                                                                   end_node_id, end_time))
        if not self.is_valid_user_data(start_node_id, end_node_id, start_time, end_time):
            logging.error("user: {} data is invalid".format(user_id))
            return None

        # 求出用户的路线图
        path_info = self.get_path_info(start_node_id, start_time, end_node_id, end_time)
        if path_info is None or len(path_info) == 0:
            logging.error("user {} hasn't path info: {}".format(user_id, path_info))
            return None

        return path_info

    def get_path_info(self, start_node_id, start_time, end_node_id, end_time):
        """
        还原出行线路信息，从 @start_node_id 到 @end_node_id 的出行线路
        :param start_node_id: 进站点
        :param start_time: 进站时间
        :param end_node_id: 出站点
        :param end_time: 出站时间
        :return: 线路信息，不能还原则为 None
        """
        if start_time >= end_time:
            # logging.info("start_time {} is greater than end_time: {}".format(start_time, end_time))
            return None
        if start_node_id == end_node_id:
            # 递归过程中可能会生成起点等于终点状态
            # logging.warning("start_node_id: {} is equal to end_node_id: {}".format(start_node_id, end_node_id))
            return []

        # 终点所属的线路
        _, route_id = self.node_info_dict[end_node_id]
        route = self.route_dict[route_id]

        # 起点和终点在同一线路上
        if route.has_node(start_node_id):

            # 寻找同时包含起点和终点的车次
            node_train_info_dict = route.get_node_train()
            train_info_dict = route.get_train_info_dict()
            for train_number, train_arrival_time, _ in node_train_info_dict[end_node_id]:
                if start_time > train_arrival_time > end_time:
                    continue
                if start_node_id not in train_info_dict[train_number]:
                    continue

                start_node_arrival_time, start_node_dispatch_time = train_info_dict[train_number][start_node_id]
                if start_node_arrival_time > train_arrival_time:
                    continue

                if start_time < start_node_dispatch_time < end_time:
                    # 找到两个顶点在同一车次的列车车次
                    # 先返回路径的大概信息，最后再重构有效路径的详细信息
                    user_path_list = [(start_node_id, end_node_id, train_number)]
                    return user_path_list

            # 同一线路上的换乘,换乘不同的车次
            for train_number, train_arrival_time, _ in node_train_info_dict[end_node_id]:
                if start_time > train_arrival_time > end_time:
                    continue

                left_node, right_node = route.get_train_points_info(train_number)

                if left_node is not None:
                    left_arrival_time = route.get_train_node_arrival_time(train_number, left_node)

                    if not route.is_visited(left_node) and train_arrival_time >= left_arrival_time > start_time:
                        route.set_visited(left_node)
                        solution_path = self.get_path_info(start_node_id, start_time,
                                                           left_node, left_arrival_time)

                        if solution_path is not None:
                            solution_path.append((left_node, end_node_id, train_number))
                            return solution_path
                        else:
                            route.reset_visited(left_node)

                if right_node is None:
                    continue

                right_arrival_time = route.get_train_node_arrival_time(train_number, right_node)
                if not route.is_visited(right_node) and train_arrival_time >= right_arrival_time > start_time:
                    route.set_visited(right_node)
                    solution_path = self.get_path_info(start_node_id, start_time,
                                                       right_node, right_arrival_time)

                    if solution_path is not None:
                        solution_path.append((right_node, end_node_id, train_number))
                        return solution_path
                    else:
                        route.reset_visited(right_node)

        # 获得该路线上的换乘节点信息
        transfer_dict = route.get_transfer_info()
        if transfer_dict is None or len(transfer_dict) == 0:
            # 无换乘站点
            return None

        # 终止点自身为换乘点
        if not route.is_visited(end_node_id):   # 排除递归的情况
            end_node_transfer = transfer_dict.get(end_node_id, None)
            if end_node_transfer is not None:
                for transfer_node_id in end_node_transfer:
                    _, transfer_before_route_id = self.node_info_dict[transfer_node_id]
                    transfer_before_route = self.route_dict[transfer_before_route_id]
                    # 该节点已被搜索过
                    if transfer_before_route.is_visited(transfer_node_id):
                        continue

                    # 将该换乘点置为已被访问过
                    route.set_visited(end_node_id)
                    transfer_before_route.set_visited(transfer_node_id)
                    solution_path = self.get_path_info(start_node_id, start_time,
                                                       transfer_node_id, end_time)

                    # 如果有解
                    if solution_path is not None:
                        return solution_path
                    else:
                        route.reset_visited(end_node_id)
                        transfer_before_route.reset_visited(transfer_node_id)

        # 找出经过终止点，且到达终止点的时间最贴近终止时间的前 k 个点
        nearest_train = route.get_node_k_nearest_train(end_node_id, end_time, 50)

        for train_number_possible in nearest_train:
            end_node_arrival_time, _ = route.get_node_time_in_train(end_node_id, train_number_possible)

            # 递归搜索符合条件的换乘点
            for transfer_node_id in transfer_dict:
                # 该换乘点已被搜索过
                if transfer_node_id == end_node_id or  route.is_visited(transfer_node_id):
                    continue

                # 换乘点在该车次中
                if route.node_in_the_train(transfer_node_id, train_number_possible):

                    arrival_time, dispatch_time = route.get_node_time_in_train(transfer_node_id,
                                                                               train_number_possible)
                    # 换乘点发车时刻不符合条件
                    if (arrival_time > end_node_arrival_time or
                            dispatch_time <= start_time or
                            arrival_time >= end_time or
                            arrival_time <= start_time):
                        continue

                    # 搜索所有换乘后的路线
                    transfer_before_set = route.get_after_transfer_node_id(transfer_node_id)
                    if transfer_before_set is None or len(transfer_before_set) == 0:
                        continue

                    # 将该换乘点置为已被访问过
                    route.set_visited(transfer_node_id)

                    # 对所有换乘后的节点
                    for transfer_before_node_id in transfer_before_set:
                        _, transfer_before_route_id = self.node_info_dict[transfer_before_node_id]
                        transfer_before_route = self.route_dict[transfer_before_route_id]
                        # 该节点已被搜索过
                        if transfer_before_route.is_visited(transfer_before_node_id):
                            continue

                        # 将该节点置为已被搜索过
                        transfer_before_route.set_visited(transfer_before_node_id)

                        solution_path = self.get_path_info(start_node_id, start_time,
                                                           transfer_before_node_id, arrival_time)

                        # 如果有解
                        if solution_path is not None:
                            solution_path.append((transfer_node_id, end_node_id, train_number_possible))
                            return solution_path
                        else:
                            route.reset_visited(transfer_node_id)
                            transfer_before_route.reset_visited(transfer_before_node_id)

        return None

    def rebuild_path(self, path_info_list):
        """
        根据出行线路信息还原站点名字表示的线路信息
        :param path_info_list: 用户出行的线路信息序列
        :return:
        """
        answer_path = list()

        last_end_node_name = None
        for path_info in path_info_list:
            start_node_id, end_node_id, train_number = path_info
            start_node_name, _ = self.node_info_dict[start_node_id]
            end_node_name, _ = self.node_info_dict[end_node_id]

            route_id = self.train_route_dict[train_number]
            route = self.route_dict[route_id]
            train_dispatch_time_at_start_node = route.get_train_node_dispatch_time(train_number, start_node_id)

            route_name = self.route_id_2_name_dict[route_id]

            if last_end_node_name is None:
                answer_path.append((None, None, None, start_node_name))
            else:
                if last_end_node_name != start_node_name:
                    logging.error("Transfer node is wrong: node {} cannot transfer to node {}".format(
                        last_end_node_name, start_node_id))
                    logging.error("Answer is wrong")
                    return []

            last_end_node_name = end_node_name
            answer_path.append((train_dispatch_time_at_start_node, route_name, train_number, end_node_name))

        return answer_path

    def get_and_save_user_path(self, user_id):
        """
        还原用户出行线路并保存到文件
        :param user_id: 用户id
        :return:
        """
        user = self.user_dict[user_id]
        # 用户出行信息
        start_time, end_time = user.get_time_info()

        path_info = self.get_user_path(user_id)

        if path_info is None:
            logging.error("Cannot get path information for user: {}".format(user_id))
            print("Cannot get path information for user: {}".format(user_id))
            return None
        # 重构用户出行路线
        user_path = self.rebuild_path(path_info)
        # logging.info("got user {} path: {}".format(user_id, user_path))

        # 输出结果到文件
        self.save_user_path_info(user_id, user_path, start_time, end_time)

    def get_path_len(self, path_info_list, update_route_traffic=False):
        """
        根据出行的线路信息，求出行长度信息
        :param path_info_list: 出行的线路信息
        :param update_route_traffic: 是否同时统计线路上的客流量
        :return: 出行总长度
        """
        total_path_length = 0

        last_end_node_name = None
        if path_info_list is None:
            return None

        for path_info in path_info_list:
            start_node_id, end_node_id, train_number = path_info

            start_node_name, _ = self.node_info_dict[start_node_id]
            end_node_name, _ = self.node_info_dict[end_node_id]

            # 确保换乘节点是正确的
            if last_end_node_name is not None and last_end_node_name != start_node_name:
                logging.error("Transfer node is wrong: node {} cannot transfer to node {}".format(
                    last_end_node_name, start_node_name))
                # raise RuntimeError("Answer is Wrong")
                logging.error("Answer is wrong")
                return None

            route_id = self.train_route_dict[train_number]
            route = self.route_dict[route_id]

            if update_route_traffic:
                # 该路线上的客流量加1
                route.traffic_value += 1

            # 活动该车次（列车）的顶点顺序序列
            train_node_sequence = route.get_train_node_sequence(train_number)

            # 找出两个换乘站点间的详细中间站点
            path_node_tag = False
            last_node_id = None
            for node_id, arrival_time, dispatch_time in train_node_sequence:
                if path_node_tag:
                    # 累加行程距离
                    total_path_length += self.road_distance_dict[last_node_id][node_id]

                if node_id == start_node_id:
                    path_node_tag = True

                last_node_id = node_id

                if node_id == end_node_id:
                    break

            last_end_node_name = end_node_name

        return total_path_length

    def get_and_save_user_path_len(self, user_id_list, update_route_traffic=False):
        """
        对 user_id_list 集合中中的用户，获得并保存用户出行的长度
        :param user_id_list: 用户 id 集合
        :param update_route_traffic: 是否同时统计线路客流量
        :return:
        """
        passed_user_set = set()

        # 求用户行程长度数据
        for user_id in user_id_list:
            path_info = self.get_user_path(user_id)
            if path_info is None:
                logging.warning("passed user: {} path length,  path information: {}".format(user_id, path_info))
                passed_user_set.add(user_id)
                continue

            user_path_length = self.get_path_len(path_info, update_route_traffic)
            if user_path_length is None:
                logging.warning("passed user: {} path length".format(user_id))
                continue
            # self.user_path_len_info[user_id] = user_path_length

            self.save_user_path_len(user_id, user_path_length)

        logging.warning("passed user number: {0}  percent: {1:.2f}%".format(len(passed_user_set),
                                                                            len(passed_user_set) /
                                                                            len(user_id_list) * 100))
        # 清空缓存
        self.save_user_path_len(None, None)

    def sample_user_batch(self, user_sample_freq=None):
        """
        对用户按出行时间段进行均匀采样
        :return:
        """
        self.sampled_user_set.clear()

        if user_sample_freq is None:
            user_sample_freq = self.user_sample_freq

        user_index = 0
        while user_index <= len(self.user_list):
            self.sampled_user_set.add(self.user_list[user_index].user_id)
            user_index += user_sample_freq

        return self.sampled_user_set

    def update_route_traffic(self, path_info_list):
        """
        对 path_info_list 出行线路上线路，更新客流量
        :param path_info_list: 用户的出行路线信息
        :return:
        """
        for path_info in path_info_list:
            _, _, train_number = path_info

            route_id = self.train_route_dict[train_number]
            route = self.route_dict[route_id]

            # 该路线上的客流量加1
            route.traffic_value += 1

    def get_and_save_route_traffic(self, user_sample_freq=None):
        """
        获得并保存线路客流量
        :param user_sample_freq: 用户采样率
        :return:
        """
        # 只采样一部分用户进行统计
        for user_id in self.sample_user_batch(user_sample_freq):
            path_list = self.get_user_path(user_id)
            if path_list is None:
                logging.warning("passed user: {} path len， path information: {}".format(user_id, path_list))
                continue

            self.update_route_traffic(path_list)

        self.route_traffic_file.write("# total sampled user number: {} \n".format(len(self.sampled_user_set)))
        self.save_route_traffic()

    def save_route_traffic(self):
        """
        统计并保存各线路上的客流量
        :return:
        """
        # 求所有线路流量
        for route_id, route in self.route_dict.items():
            self.route_traffic_info[route_id] = route.traffic_value
            self.route_traffic_file.write("route_id: {} traffic: {}\n".format(route_id, route.traffic_value))

    def get_user_path_len_and_route_traffic(self, user_sample_freq=None):
        """
        获得并保存用户出行长度及线路客流量
        :param user_sample_freq:  用户采样率
        :return:
        """
        # 只采样一部分用户进行统计
        sampled_user = self.sample_user_batch(user_sample_freq)
        logging.info("Start get user path len and route traffic. sampled user size: {}".format(
                len(sampled_user)))
        self.get_and_save_user_path_len(sampled_user, update_route_traffic=True)

        # 保存各线路的客流量
        self.save_route_traffic()

    def save_user_path_info(self, user_id, user_path_list, start_time, end_time):
        """
        保存用户出行的路线信息
        :param user_id: 用户 id
        :param user_path_list: 乘客出行线路信息
        :param start_time: 进站时间点
        :param end_time: 出站时间点
        :return:
        """
        start_time_str = start_time.strftime("%H:%M:%S")
        end_time_str = end_time.strftime("%H:%M:%S")
        with open(self.answer_file_path, "a+", encoding="UTF-8") as answer_file:
            answer_file.write("user: {},  start time: {}, ".format(user_id, start_time_str))

            for path_info in user_path_list:
                hitchhiking_time, route_name, train_id, node_name = path_info
                if hitchhiking_time is None:
                    answer_file.write("{}, ".format(node_name))
                    continue
                hitchhiking_time_str = hitchhiking_time.strftime("%H:%M:%S")
                answer_file.write("{}, {}, {}, {}, ".format(hitchhiking_time_str, route_name, train_id, node_name))

            answer_file.write(" end time: {}\n".format(end_time_str))

    def save_user_path_len(self, user_id, path_len):
        """
        保存乘客出行线路长度
        :param user_id:
        :param path_len:
        :return:
        """
        if user_id:
            self.user_path_len_buff.append((user_id, path_len))

        if not user_id or len(self.user_path_len_buff) >= self.len_data_buff_size:
            data_str = ""
            for user_id, path_len in self.user_path_len_buff:
                data_str += "user: {} path_len: {}\n".format(user_id, path_len)
            self.user_path_len_file.write(data_str)
            self.user_path_len_buff.clear()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        filename='./logs/solution_2A.log',
                        format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filemode='w+')

    # 禁止日志输出
    # logging.disable(logging.INFO)
    # logging.disable(logging.ERROR)

    # 构建问题求解对象
    solution = Solution2A()
    # 导入数据
    solution.load_data()
    logging.info("load data done")

    # ===== 2-A 答案求解======
    user_list = ["2", "7", "19", "31", "41", "71",
                 "83", "89", "101", "113", "2845", "124801",
                 "140610", "164834", "193196", "223919",
                 "275403", "286898", "314976", "315621"
                 ]
    # @TODO: 45 号用户的行程数据推导不出：
    #   45,12,37,10:49:00,11:05:06
    #   查地图：
    #       12,复兴门,1
    #       37,积水潭,2
    #   地图给的乘车路线:
    #       【乘车方案】复兴门－积水潭：2号线（复兴门－积水潭，4站），预计时间约12分钟，票价3元。
    #   行车数据并无相关的线路
    # user_list = ["45"]
    # logging.info("user id list is: {}".format(user_list))
    #
    for userId in user_list:
        # 求解每个用户的路径数据
        solution.get_and_save_user_path(userId)
    # ===== 2-A =======

    # 统计用户出行线路长度及线路流量，
    # solution.get_user_path_len_and_route_traffic()

    logging.info("Everything is Done")
