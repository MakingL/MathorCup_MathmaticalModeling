# -*- coding: utf-8 -*-
# @Time    : 2019/4/11 20:44
# @Author  : MLee
# @File    : get_solution_2_A.py
import logging
from datetime import datetime

from RoadInfo.Road import Route
from UserInfo.User import User


class Solution2A(object):
    """docstring for Solution2A"""

    def __init__(self, user_data_path="./data/附件 1 线网乘客O-D数据.txt",
                 node_data_path="./data/附件 2 线网基础信息表-1 基础数据-车站表.txt",
                 train_data_path="./data/附件 3 列车运行图数据.txt",
                 answer_file_path="./data/answer.txt",
                 route_data_path="./data/附件 2 线网基础信息表-2 基础数据-线路表.txt"):
        super(Solution2A, self).__init__()
        self.user_data_path = user_data_path
        self.route_data_path = route_data_path
        self.node_data_path = node_data_path
        self.train_data_path = train_data_path
        self.answer_file_path = answer_file_path

        # 用户 ID 到用户信息对象映射
        self.user_dict = dict()

        self.route_dict = dict()
        self.route_id_2_name_dict = dict()

        # 节点 id 到其信息的映射
        self.node_info_dict = dict(tuple())

        # 节点名字到车站 id  集合的映射，找出相同站点的节点 id 集合
        self.node_name_2_id_set = dict(set())

    def load_user_data(self):
        with open(self.user_data_path, "r") as user_file:
            for line in user_file:
                line = line.strip(" \n")
                data = line.replace(" ", "").replace("\t", "")
                data_info = data.split(",")

                if len(data_info) != 5 or not data_info[0].isnumeric():
                    continue

                user_id, start_node_id, dst_node_id, start_time_str, end_time_str = data_info

                start_time = self.parse_hms_time(start_time_str)
                end_time = self.parse_hms_time(end_time_str)

                new_user = User(start_node_id, dst_node_id, start_time, end_time)
                self.user_dict[user_id] = new_user

    def load_route_info(self):

        # 导入地图线路信息
        with open(self.node_data_path, "r") as node_file:
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
        with open(self.route_data_path, "r") as route_file:
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
        with open(self.train_data_path, "r") as train_file:
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

                # 添加车次信息
                self.route_dict[route_id].add_train_number_info(train_number, node_id,
                                                                arrival_time, dispatch_time)

        for route in self.route_dict.values():
            # 对所有线路上的车次信息进行降序排序
            route.sort_train_info()

    def load_data(self):
        self.load_user_data()
        self.load_route_info()
        logging.info("node name to (node id,route id) set is: {}".format(self.node_name_2_id_set))
        for route in self.route_dict.values():
            logging.info("transfer node: {}".format(route.get_transfer_info()))
            logging.info("train count is: {}".format(len(route.get_train_info_dict())))
        logging.info("user count is: {}".format(len(self.user_dict)))

    def parse_hms_time(self, time_str):
        # end_time = datetime.strptime(end_time_str, "%H:%M:%S")
        # 号称下面这种解析方法在格式已知的情况下比上面的方法快7倍
        hour_s, minute_s, second_s = time_str.split(":")
        return datetime(1900, 1, 1, int(hour_s), int(minute_s), int(second_s))

    def get_user_path(self, user_id):
        logging.info("start find user: {} path".format(user_id))
        if len(self.user_dict) == 0:
            self.load_data()

        user = self.user_dict[user_id]
        # 用户出行信息
        start_node_id, end_node_id = user.get_node_info()
        start_time, end_time = user.get_time_info()

        # 求出用户的路线图
        path_info = self.get_path_info(start_node_id, start_time, end_node_id, end_time)
        if path_info is None or len(path_info) == 0:
            logging.info("user {} hasn't path info: {}".format(user_id, path_info))
            print("Got empty user path")
            raise RuntimeError("Got empty user path")

        # 重构用户出行路线
        user_path = self.rebuild_path(path_info)
        logging.info("got user {} path: {}".format(user_id, user_path))
        # 输出结果
        self.output_answer(user_id, user_path, start_time, end_time)

    def get_path_info(self, start_node_id, start_time, end_node_id, end_time):
        # 终点所属的线路
        _, route_id = self.node_info_dict[end_node_id]
        route = self.route_dict[route_id]
        # route.set_visited()
        logging.info("start search route: {}".format(route_id))

        # 起点和终点在同一线路上
        if route.has_node(start_node_id):
            # 起点和终点有同一车次的车
            train_number = route.in_same_train(end_node_id, end_time, start_node_id, start_time)
            logging.info("start node and end node in same train: {}".format(train_number))

            # 具有符合条件的车次
            if train_number is not None:
                # 先返回路径的大概信息，最后再重构有效路径的详细信息
                user_path_list = [(start_node_id, end_node_id, train_number)]
                return user_path_list

        # 获得该路线上的换乘节点信息
        transfer_dict = route.get_transfer_info()
        if len(transfer_dict) == 0:
            # 无换乘站点
            return None

        # 有换乘
        for transfer_node_id in transfer_dict:
            logging.info("start search transfer node: {}".format(transfer_node_id))
            # 获得换乘节点的车次信息
            node_train_info = route.get_node_train_info(transfer_node_id)
            if node_train_info is None:
                continue

            # 对换乘点的所有车次
            for train_number, arrival_time, dispatch_time in node_train_info:
                # 换乘点发车时刻不符合条件
                if dispatch_time > end_time or arrival_time <= start_time:
                    continue

                # 终点不在该车次
                if not route.node_in_the_train(end_node_id, train_number):
                    continue

                # 该车次的终点到达时刻大于结束时间
                if route.get_train_node_arrival_time(train_number, end_node_id) > end_time:
                    continue

                # 搜索所有换乘后的路线
                transfer_before_set = route.get_after_transfer_node_id(transfer_node_id)
                if len(transfer_before_set) == 0:
                    continue

                # 将该换乘点置为已被访问过
                route.set_visited(transfer_node_id)

                # 对所有换乘前的节点
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
                        solution_path.append((transfer_before_node_id, transfer_node_id, None))
                        return solution_path.append((transfer_node_id, end_node_id, train_number))
                    else:
                        route.reset_visited(transfer_node_id)
                        transfer_before_route.reset_visited(transfer_before_node_id)

        return None

    def rebuild_path(self, path_info_list):
        answer_path = list()

        last_path = None
        last_end_node_name = None
        for path_info in path_info_list:
            start_node_id, end_node_id, train_number = path_info
            start_node_name, _ = self.node_info_dict[start_node_id]
            end_node_name, _ = self.node_info_dict[end_node_id]

            if last_end_node_name is None:
                answer_path.append((start_node_name, None))
            else:
                if last_end_node_name != start_node_name:
                    print("Transfer node is wrong: node {} cannot transfer to node {}".format(
                        last_path[1], start_node_id))
                    raise RuntimeError("Answer is Wrong")

            last_path = path_info
            last_end_node_name = end_node_name
            answer_path.append((end_node_name, train_number))

        return answer_path

    def output_answer(self, user_id, user_path, start_time, end_time):
        logging.info("start write user: {} answer".format(user_id))
        with open(self.answer_file_path, "a+") as answer_file:
            answer_file.write("{}, ".format(user_id))
            for index in range(user_path):
                if index == 0:
                    start_time_str = datetime.strptime("%H:%M:%S", start_time)
                    answer_file.write("{}, {}, ".format(user_path[index][0], start_time_str))
                else:
                    answer_file.write("{}, {}, ".format(user_path[index][1], user_path[index][0]))

            end_time_str = datetime.strptime("%H:%M:%S", end_time)
            answer_file.write("{}\n".format(end_time_str))


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG,
                        filename='./logs/solution.log',
                        format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filemode='w+')

    solution = Solution2A()
    solution.load_data()

    logging.info("load data done")

    # user_list = ["2", "7", "19", "31", "41", "71",
    #              "83", "89", "101", "113", "2845", "124801",
    #              "140610", "164834", "193196", "223919",
    #              "275403", "286898", "314976", "315621"]
    user_list = ["18"]

    logging.info("user id list is: {}".format(user_list))

    for userId in user_list:
        solution.get_user_path(userId)
