# -*- coding: utf-8 -*-
# @File    : Floyd.py
from collections import deque


class Floyd(object):
    """Floyd-Warshall 最短路算法"""

    def __init__(self, graph):
        super(Floyd, self).__init__()
        self.graph = graph
        self.INF = float("inf")
        # self.INF = 0x3f3f3f3f
        self.dist = dict(dict())

        self.path_info = dict(dict())

        # 构建邻接矩阵，路的权值为 1
        for start_id in self.graph.vertex_set:
            if start_id not in self.dist:
                self.dist[start_id] = dict()

            for end_id in self.graph.vertex_set:
                if start_id == end_id:
                    self.dist[start_id][end_id] = 0
                    continue

                if start_id in self.graph.graph_adjacent_dict and \
                        end_id in self.graph.graph_adjacent_dict[start_id]:
                    # 邻接的节点
                    # self.dist[start_id][end_id] = 1
                    self.dist[start_id][end_id] = self.graph.graph_adjacent_dict[start_id][end_id].weight

                    # 初始化路径信息
                    if start_id not in self.path_info:
                        self.path_info[start_id] = dict()
                    self.path_info[start_id][end_id] = start_id

                else:
                    # 两点不邻接
                    self.dist[start_id][end_id] = self.INF

        # 利用 Floyd 算法求出任意两点间最短路长
        self.floyd_search()

    def floyd_search(self):
        """
        搜索任意两点间的最短路
        :return:
        """

        # 中介节点放在最外层循环
        for mid in self.graph.vertex_set:

            for start in self.graph.vertex_set:
                for end in self.graph.vertex_set:

                    if self.dist[start][mid] < self.INF and self.dist[mid][end] < self.INF:
                        if self.dist[start][end] > self.dist[start][mid] + self.dist[mid][end]:
                            self.dist[start][end] = self.dist[start][mid] + self.dist[mid][end]

                            # 保存路径中转信息
                            self.path_info[start][end] = self.path_info[mid][end]

    def reconstruct_path(self, came_from, start, goal):
        """
        重构最短路径
        :param came_from: 保存路径信息的容器
        :param start: 源点
        :param goal: 终点
        :return: 包含路径信息的队列
        """
        path = deque()
        path.clear()

        if start not in came_from or goal not in came_from[start]:
            return path

        node = goal
        path.appendleft(node)
        mid_node = came_from[start][goal]
        while mid_node != start:
            path.appendleft(mid_node)
            mid_node = came_from[start][mid_node]
        path.appendleft(mid_node)

        return path

    def get_dist(self, start_id, end_id):
        """
        获得最短路长度
        :param start_id: 源点
        :param end_id: 终点
        :return: 路长
        """
        return self.dist[start_id][end_id]

    def get_shortest_path(self, start_id, end_id):
        """
        获得两点间的最短路
        :param start_id:
        :param end_id:
        :return:
        """
        return self.reconstruct_path(self.path_info, start_id, end_id), self.dist[start_id][end_id]
