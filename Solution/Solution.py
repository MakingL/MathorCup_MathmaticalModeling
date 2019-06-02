# -*- coding: utf-8 -*-
# @Time    : 2019/4/11 20:44
import logging
from datetime import datetime, timedelta

from AStar.AStar import AStar
from Floyd.Floyd import Floyd
from Graph.GraphConf import Graph, Road
from RouteInfo.Route import Route
from UserInfo.User import User


class Solution(object):
    """docstring for Solution2A"""

    def __init__(self,
                 # user_data_path="./data/data1_userData.txt",
                 user_data_path="../data/data1_O2D.txt",
                 node_data_path="../data/data2_nodeInfo.txt",
                 train_data_path="../data/data3_trainInfo.txt",
                 road_distance_data_path="../data/data2_distance_between_two_station.txt",
                 answer_file_path="../data/answer_2B.txt",
                 user_path_len_file_path="../data/user_path_len.txt",
                 route_traffic_file_path="../data/route_traffic.txt",
                 passed_user_file_path="../data/passed_user_2B.txt",
                 route_data_path="../data/data2_routeInfo.txt"):
        super(Solution, self).__init__()
        self.user_path_buff = list()
        self.gama = 0.5
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
        self.pending_usr_list = list()

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
        open(self.answer_file_path, "w+", encoding="UTF-8")
        open(self.user_path_len_file_path, "w+", encoding="UTF-8")
        open(self.route_traffic_file_path, "w+", encoding="UTF-8")
        self.passed_user_file = open(self.passed_user_file_path, "w+", encoding="UTF-8")
        self.answer_file = open(self.answer_file_path, "w+", encoding="UTF-8")

        # 路的权值
        self.road_distance_dict = dict(dict())

        # 线路流量是否统计过
        self.traffic_counted_flag = False

        self.user_path_len_info = dict()
        self.route_traffic_info = dict()

        # 地图对象
        self.graph = Graph()

        # Floyd 算法对象
        self.Floyd = None

        # 权值更新的列表
        self.weight_update_list = list()

        # 权值衰减公式中的参数 a
        self.alpha = 1 / 6

        # 调度的时间段
        self.schedule_T = timedelta(hours=0, minutes=10, seconds=0)
        self.earliest_user_start_time = self.parse_hms_time("23:59:59")

        self.omega = 1428

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

                if start_time < self.earliest_user_start_time:
                    self.earliest_user_start_time = start_time

                new_user = User(user_id, start_node_id, dst_node_id, start_time, end_time)
                self.user_dict[user_id] = new_user
                self.pending_usr_list.append(new_user)

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

    def plan_all_user_path(self):
        # 预处理
        self.pre_process_user()

        # batch_Schedule_time_len = self.schedule_T
        current_time = self.earliest_user_start_time

        user_count = 0
        while self.has_pending_user():
            user_plan_batch = self.get_plan_user_batch(current_time)

            # ****** 衰减图边上的权值 ******
            self.update_decay_graph_weight()

            weight_update_dict = dict()
            weight_update_dict.clear()
            print("get user batch size: {}".format(len(user_plan_batch)))
            for user in user_plan_batch:
                plan_path, shortest_len = self.get_a_star_path(self.graph, user.start_node_id, user.end_node_id)
                if plan_path is None:
                    return -2

                # user.plan_path_list = plan_path
                self.save_planed_user_path(user, plan_path, shortest_len)

                # 更新权值
                self.update_graph_weight(list(plan_path), weight_update_dict)

            #     user_count += 1
            #     print(user_count)
            #
            #
            # if user_count >=101:
            #     break

            for road_id in weight_update_dict:
                weight_update_dict[road_id]["times"] /= len(user_plan_batch)

            # 当前时间片的道路权值更新信息保存到列表
            self.weight_update_list.append(weight_update_dict)

            # 时间片增加
            current_time += self.schedule_T

        # 清空缓存
        self.save_planed_user_path(None, None, None)

    def build_graph(self):
        for start_node_id in self.road_distance_dict:
            for end_node_id in self.road_distance_dict[start_node_id]:
                # 正向边
                road_id = self.get_edge_id(start_node_id, end_node_id)
                road_len = self.road_distance_dict[start_node_id][end_node_id]
                road_conf = road_id, road_len, start_node_id, end_node_id

                new_road = Road(road_conf)
                self.graph.add_edge(start_node_id, road_id, new_road)

                # 添加反向边
                # road_id = self.get_edge_id(end_node_id, start_node_id)
                # road_conf = road_id, road_len, end_node_id, start_node_id
                #
                # new_road = Road(road_conf)
                # self.graph.add_edge(end_node_id, road_id, new_road)

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

    def pre_process_user(self):
        self.pending_usr_list.sort(key=lambda x: x.start_time, reverse=False)

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
        hour_s, minute_s, second_s = time_str.split(":")
        return datetime(1900, 1, 1, int(hour_s), int(minute_s), int(second_s))

    def is_valid_user_data(self, start_node_id, dst_node_id, start_time, end_time):
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

    def has_pending_user(self):
        return len(self.pending_usr_list) != 0

    def get_plan_user_batch(self, current_time):
        user_set = set()

        for user in self.pending_usr_list:
            if user.start_time <= current_time:
                user_set.add(user)

        for user in user_set:
            self.pending_usr_list.remove(user)

        return user_set

    def get_a_star_path(self, graph, start_node_id, end_node_id):
        aStarSchedule = AStar(graph, self.Floyd, self.gama)
        return aStarSchedule.aStar(start_node_id, end_node_id)

    def update_graph_weight(self, plan_path_list, weight_update_dict):

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
            # weight_update_delta = self.graph.get_edge_weight_delta(road_id, car_speed)
            weight_update_dict[road_id]["weight"] += weight_delta
            weight_update_dict[road_id]["times"] += 1

            # 更新道路上的权值
            self.graph.change_edge_weight(road_id, weight_delta)
            last_node_id = node_id

    def update_decay_graph_weight(self):
        """
        道路权值衰减
        :return:
        """
        for w_update in self.weight_update_list:
            for road_id in w_update:
                w_u = w_update[road_id]["weight"]
                if w_u <= 1e-5:
                    w_update[road_id]["weight"] = 0
                    continue

                # print('w_update[road_id]["times"]: {}'.format(w_update[road_id]["times"]))
                beta = self.alpha * w_update[road_id]["times"]
                # print("beta - 1: {}".format(beta - 1))

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

    def get_edge_id(self, start_node_id, end_node_id):
        if start_node_id == end_node_id:
            raise RuntimeError("start_node_id: {} == end_node_id: {}".format(start_node_id, end_node_id))
        road_id = "{}_{}".format(start_node_id, end_node_id)
        return road_id

    def save_planed_user_path(self, user, plan_path, path_len):
        if user:
            self.user_path_buff.append((user, plan_path))

        if not user or len(self.user_path_buff) >= 100:
            for user, plan_path in self.user_path_buff:
                self.answer_file.write("user {} path: {} len: {}\n".format(user.user_id, ", ".join(plan_path), path_len))

            self.user_path_buff.clear()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        filename='../logs/solution_2B.log',
                        format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filemode='w+')

    # logging.disable(logging.INFO)
    # logging.disable(logging.ERROR)

    solution = Solution()
    solution.load_data()
    logging.info("load data done")
    solution.build_graph()

    solution.plan_all_user_path()

    logging.info("Everything is Done")
