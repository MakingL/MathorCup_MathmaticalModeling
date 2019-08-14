# -*- coding: utf-8 -*-
# @Time    : 2019/6/4 22:10
# @Author  : MLee
# @File    : Solution2.py
import logging
from datetime import datetime, timedelta

from AStar.AStar import AStar
from Floyd.Floyd import Floyd
from Graph.GraphConf import Graph, Road
from RouteInfo.Route import Route
from UserInfo.User import User


class Solution2(object):
    """
    Problem 2 的解答
    @已知用户出行数据: 进地铁站刷卡站点，进站时间，出站站点，出站时间
    @已知地铁运行时间表及地铁线路表，站点之间的距离
    @ 还原乘客出行的真实线路信息： 何时何地搭乘何辆列车
    @ 统计用户出行的长度及线路的客流量
    @对地铁线路进行有向赋权图建模
    @利用 A* 算法求用户出行的最短路，
    @同时通过用户出行量改变权值信息，避免线路过于拥塞
    """

    def __init__(self,
                 user_data_path="./data/data1_O2D.txt",
                 node_data_path="./data/data2_nodeInfo.txt",
                 train_data_path="./data/data3_trainInfo.txt",
                 road_distance_data_path="./data/data2_distance_between_two_station.txt",
                 answer_2A_file_path="./data/user_path_answer.txt",
                 user_planed_path_file_path="./data/planed_user_path.txt",
                 user_path_len_file_path="./data/user_path_len.txt",
                 route_traffic_file_path="./data/route_traffic.txt",
                 planed_route_traffic_file_path="./data/planed_route_traffic.txt",
                 passed_user_file_path="./data/passed_user.txt",
                 route_data_path="./data/data2_routeInfo.txt"):
        super(Solution2, self).__init__()
        self.user_data_path = user_data_path
        self.route_data_path = route_data_path
        self.node_data_path = node_data_path
        self.train_data_path = train_data_path
        self.answer_2A_file_path = answer_2A_file_path
        self.user_path_len_file_path = user_path_len_file_path
        self.route_traffic_file_path = route_traffic_file_path
        self.planed_route_traffic_file_path = planed_route_traffic_file_path
        self.road_distance_data_path = road_distance_data_path
        self.passed_user_file_path = passed_user_file_path
        self.user_planed_path_file_path = user_planed_path_file_path

        logging.info("user_data_path: {}".format(self.user_data_path))
        logging.info("route_data_path: {}".format(self.route_data_path))
        logging.info("node_data_path: {}".format(self.node_data_path))
        logging.info("train_data_path: {}".format(self.train_data_path))
        logging.info("answer_2A_file_path: {}".format(self.answer_2A_file_path))
        logging.info("planed_user_path: {}".format(self.user_planed_path_file_path))
        logging.info("user_path_len_file_path: {}".format(self.user_path_len_file_path))
        logging.info("route_traffic_file_path: {}".format(self.route_traffic_file_path))
        logging.info("planed_route_traffic_file_path: {}".format(self.planed_route_traffic_file_path))
        logging.info("road_distance_data_path: {}".format(self.road_distance_data_path))
        logging.info("passed_user_file_path: {}".format(self.passed_user_file_path))

        # 用户 ID 到用户信息对象映射
        self.user_dict = dict()
        self.user_list = list()

        # 正在规划路线的乘客集合
        self.planing_usr_list = list()
        self.planing_usr_index = 0

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
        self.planed_route_traffic_file = open(self.planed_route_traffic_file_path, "w+", encoding="UTF-8")
        self.passed_user_file = open(self.passed_user_file_path, "w+", encoding="UTF-8")
        self.answer_2A_file = open(self.answer_2A_file_path, "w+", encoding="UTF-8")
        self.user_planed_path_file = open(self.user_planed_path_file_path, "w+", encoding="UTF-8")

        # 车站之间的距离
        self.road_distance_dict = dict(dict())

        # 线路上的客流量信息
        self.route_traffic_info = dict()

        # 统计数据特征的 用户采样率: 1/user_sample_freq
        self.user_sample_freq = 10000
        # 用户出行线路长度数据的缓冲区大小
        self.len_data_buff_size = max(50, int(self.user_sample_freq / 1000))
        self.user_path_len_buff = list()

        self.path_info_data_buff = list()

        self.sampled_user_set = set()

        # 规划后的乘客路径
        self.planed_user_path_buff = list()
        self.planed_path_data_buff_size = 100

        # 地图对象
        self.graph = Graph()

        # Floyd 算法对象，用于近似 A* 算法中 h(n)
        self.Floyd = None

        # 权值更新的列表
        self.weight_update_list = list()

        # 调度的时间段
        self.schedule_T = timedelta(hours=0, minutes=10, seconds=0)
        self.earliest_user_start_time = self.parse_hms_time("23:59:59")

        # 权值衰减公式中的参数 a
        self.alpha = 1 / 6
        # 权值更新的参数
        self.omega = 1428
        # A* 算法中 g(n) 与 h(n) 的比重参数
        self.gama = 0.5

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

    def load_user_data(self):
        """
        导入乘客出行的历史数据
        :return:
        """
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
        导入地铁线路信息表
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
        导入地铁站点距离信息
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
        """导入数据"""
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

        # 建立图模型
        self.build_graph()

    def clear_routes_traffic(self):
        """
        清空道路上累计的流量
        :return:
        """
        for route in self.route_dict.values():
            # 清空道路的流量
            route.clear_route_traffic()

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
        transfer_dict = route.transfer_node_dict
        if transfer_dict is None or len(transfer_dict) == 0:
            # 无换乘站点
            return None

        # 终止点自身为换乘点
        if not route.is_visited(end_node_id):  # 排除递归的情况
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
            end_node_arrival_time, _ = route.get_time_info_in_train(end_node_id, train_number_possible)

            # 递归搜索符合条件的换乘点
            for transfer_node_id in transfer_dict:
                # 该换乘点已被搜索过
                if transfer_node_id == end_node_id or route.is_visited(transfer_node_id):
                    continue

                # 换乘点在该车次中
                if route.node_in_the_train(transfer_node_id, train_number_possible):

                    arrival_time, dispatch_time = route.get_time_info_in_train(transfer_node_id,
                                                                               train_number_possible)
                    # 换乘点发车时刻不符合条件
                    if (arrival_time > end_node_arrival_time or
                            dispatch_time <= start_time or
                            arrival_time >= end_time or
                            arrival_time <= start_time):
                        continue

                    # 搜索所有换乘后的路线
                    transfer_before_set = route.transfer_node_dict[transfer_node_id]
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

    def get_user_path(self, user_id):
        """
        还原用户出行的真实路线
        :param user_id: 用户 id
        :return: 用户出行的真实线路信息，不能还原则返回 None
        """

        # 清除所有线路上的搜索痕迹
        for route in self.route_dict.values():
            route.clear_route_visit_status()

        user = self.user_dict[user_id]
        # 用户出行信息
        start_node_id, end_node_id = user.get_node_info()
        start_time, end_time = user.get_time_info()

        if not self.is_valid_user_data(start_node_id, end_node_id, start_time, end_time):
            logging.error("user: {} data is invalid".format(user_id))
            return None

        # 求出用户的路线图
        path_info = self.get_path_info(start_node_id, start_time, end_node_id, end_time)
        if path_info is None or len(path_info) == 0:
            logging.error("user {} hasn't path info: {}".format(user_id, path_info))
            return None

        return path_info

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
            # print("Cannot get path information for user: {}".format(user_id))
            return None
        # 重构用户出行路线
        user_path = self.rebuild_path(path_info)

        # 输出结果到文件
        self.save_user_path_info(user_id, user_path, start_time, end_time)
        return path_info

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
            # path_info = self.get_user_path(user_id)
            path_info = self.get_and_save_user_path(user_id)
            if path_info is None:
                logging.warning("passed user: {} path length,  path information: {}".format(user_id, path_info))
                passed_user_set.add(user_id)
                continue

            user_path_length = self.get_path_len(path_info, update_route_traffic)
            if user_path_length is None:
                logging.warning("passed user: {} path length".format(user_id))
                continue

            self.save_user_path_len(user_id, user_path_length)

        logging.warning("passed user number: {0}  percent: {1:.2f}%".format(len(passed_user_set),
                                                                            len(passed_user_set) /
                                                                            len(user_id_list) * 100))
        # 清空缓存
        self.save_user_path_len(None, None)
        return passed_user_set

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

    def get_and_save_route_traffic(self, user_id_list):
        """
        获得并保存线路客流量
        :param user_id_list: 乘客集合
        :return:
        """
        # 只采样一部分用户进行统计
        for user_id in user_id_list:
            path_list = self.get_user_path(user_id)
            if path_list is None:
                logging.warning("passed user: {} path len， path information: {}".format(user_id, path_list))
                continue

            self.update_route_traffic(path_list)

        self.route_traffic_file.write("# total sampled user number: {} \n".format(len(self.sampled_user_set)))
        self.save_route_traffic()

    def save_route_traffic(self, route_traffic_file=None):
        """
        统计并保存各线路上的客流量
        :return:
        """
        if route_traffic_file is None:
            route_traffic_file = self.route_traffic_file
        # 求所有线路流量
        for route_id, route in self.route_dict.items():
            self.route_traffic_info[route_id] = route.traffic_value
            route_traffic_file.write("route_id: {} traffic: {}\n".format(route_id, route.traffic_value))

    def get_user_path_len_and_route_traffic(self, user_id_list):
        """
        获得并保存用户出行长度及线路客流量
        :param user_id_list:  乘客集合
        :return:
        """
        logging.info("Start get user path len and route traffic. User size: {}".format(
                len(user_id_list)))
        passed_user_set = self.get_and_save_user_path_len(user_id_list, update_route_traffic=True)

        # 保存各线路的客流量
        self.save_route_traffic()
        return passed_user_set

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
        self.answer_2A_file.write("user: {},  start_time: {}, ".format(user_id, start_time_str))

        for path_info in user_path_list:
            hitchhiking_time, route_name, train_id, node_name = path_info
            if hitchhiking_time is None:
                self.answer_2A_file.write("{}, ".format(node_name))
                continue
            hitchhiking_time_str = hitchhiking_time.strftime("%H:%M:%S")
            self.answer_2A_file.write("{}, {}, {}, {}, ".format(hitchhiking_time_str, route_name, train_id, node_name))

        self.answer_2A_file.write(" end_time: {}\n".format(end_time_str))

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

    def plan_user_path(self, user_id_list):
        """
        为所有用户规划出行线路
        :return:
        """
        self.planing_usr_list.clear()
        # 清空累计的客流量
        self.clear_routes_traffic()

        passed_user_list = list()

        # 添加到 buffer
        for user_id in user_id_list:
            user = self.user_dict[user_id]
            self.planing_usr_list.append(user)

        # 预处理，用户按照出行时间进行升序排列
        self.planing_usr_list.sort(key=lambda x: x.start_time, reverse=False)
        self.planing_usr_index = 0

        # 最早出行时间
        current_time = self.planing_usr_list[0].start_time

        while self.has_pending_user():
            user_plan_batch = self.get_planing_user_batch(current_time)

            # ****** 衰减图边上的权值 ******
            self.update_decay_graph_weight()

            weight_update_dict = dict()
            weight_update_dict.clear()
            for user in user_plan_batch:
                plan_path, _ = self.get_a_star_path(self.graph, user.start_node_id, user.end_node_id)
                if plan_path is None:
                    raise RuntimeError("Cannot plan path for user: {}, get None".format(user.user_id))

                # 求出规划后路径的行程长度
                path_len = self.get_planed_path_len(list(plan_path), update_route_traffic=True)
                # 时间消耗
                time_info = self.get_planed_path_time_info(list(plan_path), user.start_time)
                if time_info is None:
                    logging.warning("Cannot get train info for path: {} user: {}".format(list(plan_path),
                                                                                         user.user_id))
                    passed_user_list.append(user.user_id)
                    continue
                time_info_list, time_cost = time_info

                # 保存规划后的结果
                self.save_planed_user_path(user, plan_path, path_len, time_cost)

                # 更新权值
                self.update_graph_weight(list(plan_path), weight_update_dict)

            for road_id in weight_update_dict:
                weight_update_dict[road_id]["times"] /= len(user_plan_batch)

            # 当前时间片的道路权值更新信息保存到列表
            self.weight_update_list.append(weight_update_dict)

            # 时间片增加
            current_time += self.schedule_T

        self.save_route_traffic(self.planed_route_traffic_file)
        # 清空缓存
        self.save_planed_user_path(None, None, None, None)
        logging.info("User path planning passed: {}".format(passed_user_list))
        logging.info("User path planning passed {:.2f}% user".format(len(passed_user_list)/len(user_id_list)*100.0))

    def build_graph(self):
        """
        对地铁网路图进行有向赋权图建模，构建有向图
        :return:
        """
        for start_node_id in self.road_distance_dict:
            for end_node_id in self.road_distance_dict[start_node_id]:
                # 正向边
                road_id = self.get_edge_id(start_node_id, end_node_id)
                road_len = self.road_distance_dict[start_node_id][end_node_id]
                road_conf = road_id, road_len, start_node_id, end_node_id

                new_road = Road(road_conf)
                self.graph.add_edge(start_node_id, road_id, new_road)

        # 换乘节点的之间的距离设为 0
        for node_info in self.node_name_2_id_set.values():
            transfer_nodes = set()
            for node_id, route_id in node_info:
                transfer_nodes.add(node_id)

            transfer_nodes = list(transfer_nodes)
            for index, node_id in enumerate(transfer_nodes):
                for other_node_index in range(index + 1, len(transfer_nodes)):
                    road_len = 0
                    start_node_id = node_id
                    end_node_id = transfer_nodes[other_node_index]
                    # 正向边
                    road_id = self.get_edge_id(start_node_id, end_node_id)
                    road_conf = road_id, road_len, start_node_id, end_node_id

                    new_road = Road(road_conf)
                    self.graph.add_edge(start_node_id, road_id, new_road)

                    # 反向换乘边
                    road_id = self.get_edge_id(end_node_id, start_node_id)
                    road_conf = road_id, road_len, end_node_id, start_node_id

                    new_road = Road(road_conf)
                    self.graph.add_edge(end_node_id, road_id, new_road)

        # Floyd 求任意两点的最短距离，A* 算法用，预处理车辆排序也用
        self.Floyd = Floyd(self.graph)

    def has_pending_user(self):
        """
        是否存在待规划的用户数据
        :return:
        """
        return self.planing_usr_index < len(self.planing_usr_list)

    def get_planing_user_batch(self, current_time):
        """
        获得一个批次的待规划乘客
        :param current_time:
        :return:
        """
        user_set = set()

        if not self.has_pending_user():
            return user_set

        for index in range(self.planing_usr_index, len(self.planing_usr_list)):
            user = self.planing_usr_list[index]
            if user.start_time <= current_time:
                user_set.add(user)

                # planing_usr_list 已升序排列，符合要求的 user 一定是在前面的
                self.planing_usr_index += 1

        return user_set

    def get_a_star_path(self, graph, start_node_id, end_node_id):
        """
        A* 算法求起始站点到目的站点的最短路
        :param graph:
        :param start_node_id:
        :param end_node_id:
        :return:
        """
        a_star_schedule = AStar(graph, self.Floyd, self.gama)
        return a_star_schedule.aStar(start_node_id, end_node_id)

    def update_graph_weight(self, plan_path_list, weight_update_dict):
        """
        更新图上的边权值
        :param plan_path_list:
        :param weight_update_dict:
        :return:
        """

        last_node_id = None
        for node_id in plan_path_list:
            if last_node_id is None:
                last_node_id = node_id
                continue

            road_id = self.get_edge_id(last_node_id, node_id)
            road_weight = self.graph.get_edge_weight(road_id)
            weight_delta = road_weight / self.omega

            # 保存权值变化
            if road_id not in weight_update_dict:
                weight_update_dict[road_id] = dict()
                weight_update_dict[road_id]["weight"] = 0
                weight_update_dict[road_id]["times"] = 0

            # 计算权值变化量，并保存
            weight_update_dict[road_id]["weight"] += weight_delta
            weight_update_dict[road_id]["times"] += 1

            # 更新道路上的权值
            self.graph.change_edge_weight(road_id, weight_delta)
            last_node_id = node_id

    def update_decay_graph_weight(self):
        """
        图上的道路权值衰减
        :return:
        """
        for w_update in self.weight_update_list:
            for road_id in w_update:
                w_u = w_update[road_id]["weight"]
                if w_u <= 1e-5:
                    w_update[road_id]["weight"] = 0
                    continue

                beta = self.alpha * w_update[road_id]["times"]

                decayed_weight = (beta - 1) * w_u
                w_update[road_id]["weight"] *= beta
                change_before, after_decayed_weight = self.graph.change_edge_weight(road_id, decayed_weight)
                if after_decayed_weight < 0:
                    logging.error(
                            "road_id: {} change_before: {} decayed_weight: {}"
                            " after_decayed_weight: {}".format(road_id,
                                                               change_before,
                                                               decayed_weight,
                                                               after_decayed_weight))

    def get_planed_path_len(self, planed_path_list, update_route_traffic=False):
        """
        获取规划路径的行程长度
        :param planed_path_list: 规划后的路径列表
        :param update_route_traffic: 是否更新道路客流量
        :return: 行程长度
        """

        total_path_len = 0

        for index in range(0, len(planed_path_list) - 1):
            node_id = planed_path_list[index]
            next_node_id = planed_path_list[index + 1]

            node_name, _ = self.node_info_dict[node_id]
            next_node_name, _ = self.node_info_dict[next_node_id]
            if node_name == next_node_name:
                # 换乘节点
                road_len = 0

                if update_route_traffic:
                    # 该路线上的客流量加1
                    _, route_id = self.node_info_dict[node_id]
                    route = self.route_dict[route_id]
                    route.traffic_value += 1
            else:
                road_len = self.road_distance_dict[node_id][next_node_id]

            total_path_len += road_len

        if update_route_traffic:
            # 该路线上的客流量加1
            _, route_id = self.node_info_dict[planed_path_list[-1]]
            route = self.route_dict[route_id]
            route.traffic_value += 1

        return total_path_len

    def get_planed_path_time_info(self, planed_path_list, start_time):
        """
        获取规划后的路径的时间信息
        :param planed_path_list: 规划后的路径
        :param start_time: 出发时间
        :return: 各节点的到达时刻, 总花费时间
        """

        # 总耗时
        time_cost = timedelta(hours=0, minutes=0, seconds=0)

        node_index = 0
        current_time = start_time

        # 节点时间信息
        path_time_info_list = list()
        # 起始点的出发时间
        path_time_info_list.append((planed_path_list[0], current_time))

        while node_index < len(planed_path_list):
            current_node_id = planed_path_list[node_index]
            _, route_id = self.node_info_dict[current_node_id]
            route = self.route_dict[route_id]

            # 找出出行路线上的换乘节点
            transfer_node_index = None
            transfer_node_id = None
            for index in range(node_index, len(planed_path_list) - 1):
                node_id = planed_path_list[index]
                next_node_id = planed_path_list[index + 1]

                node_name, _ = self.node_info_dict[node_id]
                next_node_name, _ = self.node_info_dict[next_node_id]
                if node_name == next_node_name:
                    # 换乘节点
                    transfer_node_index = index
                    transfer_node_id = node_id
                    break

            if transfer_node_index is None:
                # 不存在换乘节点，直接令为终止节点
                transfer_node_index = len(planed_path_list) - 1
                transfer_node_id = planed_path_list[transfer_node_index]

            transfer_node_time = route.get_train_node_earliest_arrival_time(current_node_id,
                                                                            current_time, transfer_node_id)
            if transfer_node_time is None:
                logging.warning("Cannot get valid train for planed path. node: {} time: {}"
                                " transfer_node: {}".format(current_node_id, current_time,
                                                            transfer_node_id))
                return None

            # 换乘节点或者终点的到达时间
            path_time_info_list.append((transfer_node_id, transfer_node_time))

            # 计算当前列车上的耗时
            time_cost += transfer_node_time - current_time
            current_time = transfer_node_time
            # 当前节点直接跳到换乘后的节点
            node_index = transfer_node_index + 1

        return path_time_info_list, time_cost

    def get_edge_id(self, start_node_id, end_node_id):
        """
        根据起始点和终止点的 id 获得两点决定的边的id
        :param start_node_id:
        :param end_node_id:
        :return:
        """
        if start_node_id == end_node_id:
            raise RuntimeError("start_node_id: {} == end_node_id: {}".format(start_node_id, end_node_id))
        road_id = "{}_{}".format(start_node_id, end_node_id)
        return road_id

    def save_planed_user_path(self, user, plan_path, path_len, time_cost):
        """
        保存规划的用户出行信息
        :param user:
        :param plan_path:
        :param path_len:
        :param time_cost:
        :return:
        """
        if user:
            self.planed_user_path_buff.append((user, plan_path, path_len, time_cost))

        if not user or len(self.planed_user_path_buff) >= self.planed_path_data_buff_size:
            data_str = ""
            for user, plan_path, planed_path_len, time_cost in self.planed_user_path_buff:
                data_str += "user_id: {} planed_path: {} path_len: {} time_cost: {}\n".format(user.user_id,
                                                                                              ", ".join(plan_path),
                                                                                              planed_path_len,
                                                                                              time_cost)
            self.user_planed_path_file.write(data_str)

            self.planed_user_path_buff.clear()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        filename='../logs/solution_2.log',
                        format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filemode='w+')

    # 禁止日志输出
    # logging.disable(logging.INFO)
    # logging.disable(logging.ERROR)

    # 构建问题求解对象
    solution = Solution2(user_data_path="../data/data1_O2D.txt",
                         node_data_path="../data/data2_nodeInfo.txt",
                         train_data_path="../data/data3_trainInfo.txt",
                         road_distance_data_path="../data/data2_distance_between_two_station.txt",
                         answer_2A_file_path="../data/user_path_answer_2A.txt",
                         user_planed_path_file_path="../data/planed_user_path.txt",
                         user_path_len_file_path="../data/user_path_len.txt",
                         route_traffic_file_path="../data/route_traffic.txt",
                         planed_route_traffic_file_path="../data/planed_route_traffic.txt",
                         passed_user_file_path="../data/passed_user.txt",
                         route_data_path="../data/data2_routeInfo.txt")
    # 导入数据
    solution.load_data()
    logging.info("load data done")

    # ===== 2-A 答案求解======
    user_list = ["2", "7", "19", "31", "41", "71",
                 "83", "89", "101", "113", "2845", "124801",
                 "140610", "164834", "193196", "223919",
                 "275403", "286898", "314976", "315621"
                 ]
    # 45 号用户的行程数据推导不出：
    # -------------------------
    #   45,12,37,10:49:00,11:05:06
    #   查地图：
    #       12,复兴门,1
    #       37,积水潭,2
    #   地图给的乘车路线:
    #       【乘车方案】复兴门－积水潭：2号线（复兴门－积水潭，4站），预计时间约12分钟，票价3元。
    #   行车数据并无相关的线路
    # user_list = ["45"]
    # user_list = ["1910787"]
    # -------------------------
    logging.info("user id list is: {}".format(user_list))

    for userId in user_list:
        # 求解每个用户的路径数据
        solution.get_and_save_user_path(userId)
    # ===== 2-A END =======

    # ======= 2-B =========
    # 构建问题求解对象，更改 user_path_answer 文件，避免覆盖掉 user_path_answer_2A 中的结果
    solution = Solution2(user_data_path="../data/data1_O2D.txt",
                         node_data_path="../data/data2_nodeInfo.txt",
                         train_data_path="../data/data3_trainInfo.txt",
                         road_distance_data_path="../data/data2_distance_between_two_station.txt",
                         answer_2A_file_path="../data/user_path_answer.txt",
                         user_planed_path_file_path="../data/planed_user_path.txt",
                         user_path_len_file_path="../data/user_path_len.txt",
                         route_traffic_file_path="../data/route_traffic.txt",
                         planed_route_traffic_file_path="../data/planed_route_traffic.txt",
                         passed_user_file_path="../data/passed_user.txt",
                         route_data_path="../data/data2_routeInfo.txt")
    # 导入数据
    solution.load_data()
    logging.info("load data done")

    # 按比例 user_sample_freq= 1000000:1 采样用户数据，若采用所有数据，一般主机下需要跑几天
    sampled_user_list = solution.sample_user_batch(user_sample_freq=1000000)

    # 统计用户出行线路长度及线路流量
    passed_user_set = solution.get_user_path_len_and_route_traffic(sampled_user_list)
    sampled_user_list = list(set(sampled_user_list) - passed_user_set)
    logging.info("passed user size: {} planing user list size: {}".format(len(passed_user_set),
                                                                          len(sampled_user_list)))
    sampled_user_list = list(set(sampled_user_list) - passed_user_set)
    logging.info("passed user size: {} planing user list size: {}".format(len(passed_user_set),
                                                                          len(sampled_user_list)))
    # 为乘客规划线路, 并将规划结果保存到相应的文件 planed_user_path.txt 中
    solution.plan_user_path(sampled_user_list)
    # ======= 2-B END=========

    logging.info("Everything is Done")
