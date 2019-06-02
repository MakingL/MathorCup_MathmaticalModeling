# -*- coding: utf-8 -*-
# @Time    : 2019/4/11 20:44
# @File    : get_solution_2.py
import logging
from datetime import datetime

from RouteInfo.Route import Route
from UserInfo.User import User


class Solution2A(object):
    """docstring for Solution2A"""

    def __init__(self,
                 # user_data_path="./data/data1_userData.txt",
                 user_data_path="./data/data1_O2D.txt",
                 node_data_path="./data/data2_nodeInfo.txt",
                 train_data_path="./data/data3_trainInfo.txt",
                 road_distance_data_path="./data/data2_distance_between_two_station.txt",
                 answer_file_path="./data/answer_2A.txt",
                 user_path_len_file_path="./data/user_path_len.txt",
                 route_traffic_file_path="./data/route_traffic.txt",
                 passed_user_file_path="./data/passed_user_2A.txt",
                 route_data_path="./data/data2_routeInfo.txt"):
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

        # route ID 到 线路信息对象的映射
        self.route_dict = dict()
        self.route_id_2_name_dict = dict()

        # 节点 id 到其信息的映射
        self.node_info_dict = dict(tuple())

        # 节点名字到车站 id  集合的映射，找出相同站点的节点 id 集合
        self.node_name_2_id_set = dict(set())

        # 车次号到所属线路的映射
        self.train_route_dict = dict()

        # 打开结果文件，清空文件
        open(self.answer_file_path, "w+", encoding="UTF-8")
        open(self.user_path_len_file_path, "w+", encoding="UTF-8")
        open(self.route_traffic_file_path, "w+", encoding="UTF-8")
        open(self.passed_user_file_path, "w+", encoding="UTF-8")

        self.road_distance_dict = dict(dict())

        # 线路流量是否统计过
        self.traffic_counted_flag = False

        self.user_path_len_info = dict()
        self.route_traffic_info = dict()

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

                new_user = User(user_id, start_node_id, dst_node_id, start_time, end_time)
                self.user_dict[user_id] = new_user

    def load_route_info(self):

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
        hour_s, minute_s, second_s = time_str.split(":")
        return datetime(1900, 1, 1, int(hour_s), int(minute_s), int(second_s))

    def is_valid_user_data(self, start_node_id, dst_node_id, start_time, end_time):
        if start_node_id == dst_node_id:
            return False
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
        logging.info("start find user: {} path".format(user_id))

        # 清除所有线路上的搜索痕迹
        for route in self.route_dict.values():
            route.clear_route_visit_status()

        user = self.user_dict[user_id]
        # 用户出行信息
        start_node_id, end_node_id = user.get_node_info()
        start_time, end_time = user.get_time_info()

        logging.info(
            "user: {} start node: {} start time: {} and end node: {} end time: {}".format(user_id,
                                                                                          start_node_id,
                                                                                          start_time,
                                                                                          end_node_id, end_time))
        if not self.is_valid_user_data(start_node_id, end_node_id, start_time, end_time):
            logging.error("user: {} data is invalid".format(user_id))
            # print("user: {} data is invalid".format(user_id))
            return None

        # 求出用户的路线图
        path_info = self.get_path_info(start_node_id, start_time, end_node_id, end_time)
        if path_info is None or len(path_info) == 0:
            logging.error("user {} hasn't path info: {}".format(user_id, path_info))
            # print("user: {} empty user path: {}".format(user_id, path_info))
            # raise RuntimeError("Got empty user path")
            return None

        return path_info

    def get_path_info(self, start_node_id, start_time, end_node_id, end_time):
        if start_time >= end_time:
            logging.info("start_time {} is greater than end_time: {}".format(start_time, end_time))
            return None
        if start_node_id == end_node_id:
            logging.warning("start_node_id: {} is equal to end_node_id: {}".format(start_node_id, end_node_id))
            # 递归过程中可能会生成起点等于终点状态
            return []

        # 终点所属的线路
        _, route_id = self.node_info_dict[end_node_id]
        route = self.route_dict[route_id]
        # logging.info("start search route: {}".format(route_id))

        # 起点和终点在同一线路上
        if route.has_node(start_node_id):

            # logging.info("start node: {} and end node: {} in same route".format(start_node_id, end_node_id))

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

                    logging.info(
                        "train_number: {} at start node: {} dispatch time: {}".format(train_number, start_node_id,
                                                                                      train_info_dict[train_number][
                                                                                          start_node_id][1]))
                    logging.info("got result in same route and train: {}".format(user_path_list))
                    return user_path_list

            # logging.info("start node: {} and end node: {} has no same **train**".format(start_node_id, end_node_id))

            for train_number, train_arrival_time, _ in node_train_info_dict[end_node_id]:
                if train_arrival_time > end_time:
                    continue

                left_node, right_node = route.get_train_points_info(train_number)
                # logging.info("get left node: {} and right node: {}".format(left_node, right_node))

                if left_node is not None:
                    left_arrival_time = route.get_train_node_arrival_time(train_number, left_node)

                    if not route.is_visited(left_node) and end_time > left_arrival_time > start_time:
                        route.set_visited(left_node)
                        # logging.info("try left node: {}".format(left_node))
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
                if not route.is_visited(right_node) and end_time > right_arrival_time > start_time:
                    route.set_visited(right_node)
                    # logging.info("try right node: {}".format(right_node))
                    solution_path = self.get_path_info(start_node_id, start_time,
                                                       right_node, right_arrival_time)

                    if solution_path is not None:
                        solution_path.append((right_node, end_node_id, train_number))
                        return solution_path
                    else:
                        route.reset_visited(right_node)

        # 获得该路线上的换乘节点信息
        transfer_dict = route.get_transfer_info()
        if len(transfer_dict) == 0:
            logging.info("route {} has no transfer node".format(route_id))
            # 无换乘站点
            return None

        # 找出经过终止点，且到达终止点的时间最贴近终止时间的前 k 个点
        nearest_train = route.get_node_k_nearest_train(end_node_id, end_time, 50)

        for train_number_possible in nearest_train:
            end_node_arrival_time, _ = route.get_node_time_in_train(end_node_id, train_number_possible)

            # 递归搜索符合条件的换乘点
            for transfer_node_id in transfer_dict:
                # 该换乘点已被搜索过
                if route.is_visited(transfer_node_id):
                    continue

                # 换乘点在该车次中
                if route.node_in_the_train(transfer_node_id, train_number_possible):

                    arrival_time, dispatch_time = route.get_node_time_in_train(transfer_node_id, train_number_possible)
                    # 换乘点发车时刻不符合条件
                    if arrival_time > end_node_arrival_time or dispatch_time <= start_time \
                            or arrival_time >= end_time \
                            or arrival_time <= start_time:
                        continue

                    # 搜索所有换乘后的路线
                    transfer_before_set = route.get_after_transfer_node_id(transfer_node_id)
                    if len(transfer_before_set) == 0:
                        # logging.warning("transfer node: {} in route {} has no transfer node".format(transfer_node_id,
                        #                                                                             route_id))
                        continue

                    # logging.info("Got possible transfer node: {}".format(transfer_node_id))
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
                    # raise RuntimeError("Answer is Wrong")
                    logging.error("Answer is wrong")
                    return []

            last_end_node_name = end_node_name
            answer_path.append((train_dispatch_time_at_start_node, route_name, train_number, end_node_name))

        return answer_path

    def get_and_save_user_path(self, user_id):
        user = self.user_dict[user_id]
        # 用户出行信息
        start_time, end_time = user.get_time_info()

        path_info = self.get_user_path(user_id)

        # 重构用户出行路线
        user_path = self.rebuild_path(path_info)
        logging.info("got user {} path: {}".format(user_id, user_path))

        # 输出结果到文件
        self.save_user_path_info(user_id, user_path, start_time, end_time)

    def get_path_len_and_change_route_traffic(self, path_info_list):
        # user_path = list()
        total_path_length = 0

        last_end_node_name = None
        logging.info("path_info_list: {}".format(path_info_list))
        if path_info_list is None:
            return None
        for path_info in path_info_list:
            start_node_id, end_node_id, train_number = path_info

            start_node_name, _ = self.node_info_dict[start_node_id]
            end_node_name, _ = self.node_info_dict[end_node_id]

            # 确保换乘节点是正确的
            if last_end_node_name is not None and last_end_node_name != start_node_name:
                logging.error("Transfer node is wrong: node {} cannot transfer to node {}".format(
                    last_end_node_name, start_node_id))
                # raise RuntimeError("Answer is Wrong")
                logging.error("Answer is wrong")
                return None

            route_id = self.train_route_dict[train_number]
            route = self.route_dict[route_id]

            # 该路线上的客流量加1
            route.increase_traffic_value(1)

            # 活动该车次（列车）的顶点顺序序列
            train_node_sequence = route.get_train_node_sequence(train_number)

            # 找出两个换乘站点间的详细中间站点
            path_node_tag = False
            last_node_id = None
            for node_id, arrival_time, dispatch_time in train_node_sequence:
                if path_node_tag:
                    # user_path.append(node_id)
                    # 累加行程距离
                    # print("last_node_id: {} node_id: {}".format(last_node_id, node_id))
                    total_path_length += self.road_distance_dict[last_node_id][node_id]

                if node_id == start_node_id:
                    # user_path.append(node_id)
                    path_node_tag = True

                last_node_id = node_id

                if node_id == end_node_id:
                    break

            last_end_node_name = end_node_name

        self.traffic_counted_flag = True
        return total_path_length

    def get_and_save_all_user_path_len(self):
        computed_user_number = 0

        passed_user_set = set()
        user_path_data_list = list()
        # 求用户行程长度数据
        with open(self.user_path_len_file_path, "w+", encoding="UTF-8") as answer_file:
            for user_id in self.user_dict.keys():
                path_info = self.get_user_path(user_id)
                if path_info is None:
                    logging.warning("passed user: {} path length,  path information: {}".format(user_id, path_info))
                    # print("passed user: {} path length,  path information: {}".format(user_id, path_info))
                    passed_user_set.add(user_id)
                    continue
                user_path_length = self.get_path_len_and_change_route_traffic(path_info)
                if user_path_length is None:
                    continue
                self.user_path_len_info[user_id] = user_path_length

                user_path_data_list.append((user_id, user_path_length))
                if len(user_path_data_list) >= 500:
                    for usr_id, path_len in user_path_data_list:
                        answer_file.write("user id: {} path length: {}\n".format(usr_id, path_len))
                    user_path_data_list.clear()

                computed_user_number += 1
                if computed_user_number % 100 == 0:
                    print("got {} user path length".format(computed_user_number))

            logging.warning("passed user number: {} percent: {}% set: {}".format(len(passed_user_set),
                                                                                 len(passed_user_set) / len(
                                                                                     self.user_dict) * 100,
                                                                                 passed_user_set))

    def sample_user_batch(self):
        """
        对用户进行均匀采样
        :return:
        """
        self.sampled_user_set.clear()
        sample_size = 100

        user_index = 0
        for user_id in self.user_dict.keys():
            if user_index % sample_size == 0:
                self.sampled_user_set.add(user_id)
            user_index += 1

        return self.sampled_user_set

    def get_and_save_all_route_traffic(self):
        # 只采样一部分用户进行统计
        self.sample_user_batch()
        print("start get user path. user batch size: {}".format(len(self.sampled_user_set)))
        for user_id in self.sampled_user_set:
            path_info = self.get_user_path(user_id)
            if path_info is None:
                logging.warning("passed user: {} path len， path information: {}".format(user_id, path_info))
                continue
            self.get_path_len_and_change_route_traffic(path_info)
        print("get user path finished. user batch size: {}".format(len(self.sampled_user_set)))

        with open(self.route_traffic_file_path, "w+", encoding="UTF-8") as answer_file:
            answer_file.write("# total sampled user number: {} \n".format(len(self.sampled_user_set)))
            # 求所有线路流量
            for route_id, route in self.route_dict.items():
                route_traffic = route.get_traffic_value()
                self.route_traffic_info[route_id] = route_traffic
                answer_file.write("route id: {} route traffic: {}\n".format(route_id, route_traffic))

    def save_user_path_info(self, user_id, user_path_list, start_time, end_time):
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
    # user_list = ["2", "7", "19", "31", "41", "71",
    #              "83", "89", "101", "113", "2845", "124801",
    #              "140610", "164834", "193196", "223919",
    #              "275403", "286898", "314976", "315621"
    #              ]
    user_list = ["45"]
    logging.info("user id list is: {}".format(user_list))

    for userId in user_list:
        # 求解每个用户的路径数据
        solution.get_and_save_user_path(userId)
    # ===== 2-A =======

    logging.info("Everything is Done")
