# -*- coding: utf-8 -*-
# @File    : AStar.py
from collections import deque


class AStar:
    def __init__(self, graph, floyd, gama=1):
        self.graph = graph
        self.floyd = floyd
        self.gama = gama
        assert 0 <= self.gama <= 1, print("A star argument: gama should in [0, 1]: {}".format(self.gama))

    def distBetween(self, edge):
        """
        计算当前节点移动到邻居节点的代价
        :param edge: 当前节点与邻接节点的边
        :return: 代价值
        """
        return edge.weight

    def heuristicEstimate(self, start, goal):
        """
        计算启发函数值 h(n)
        :param start: 起始节点
        :param goal: 目标节点
        :return: h(n)
        """
        return self.floyd.get_dist(start, goal)

    def neighborNodes(self, current):
        """
        获得当前节点的邻居节点 字典 道路ID: 道路对象的字典
        :param current: 当前节点的 ID
        :return:
        """
        return self.graph.get_neighbors(current)

    def reconstructPath(self, cameFrom, goal):
        """
            重新建立路径完整信息
            :param cameFrom: 节点的父节点集合
            :param goal: 目标节点
            :return: 包含源节点 ID 到目标节点 ID 的路径
        """
        path = deque()
        node = goal
        path.appendleft(node)
        while node in cameFrom:
            node = cameFrom[node]
            path.appendleft(node)
        return path

    def getLowest(self, openSet, fScore):
        """
        获得 Open Set 中最低代价值得节点
        :param openSet:
        :param fScore:
        :return:
        """
        lowest = float("inf")
        lowestNode = None
        for node in openSet:
            if fScore[node] < lowest:
                lowest = fScore[node]
                lowestNode = node
        return lowestNode

    def aStar(self, start, goal):
        """
        A star 找 start 到 goal 节点的路径
        :param start:
        :param goal:
        :return:
        """

        cameFrom = {}
        # start = "164"
        # openSet = set(start)
        openSet = set()
        openSet.add(start)
        closedSet = set()
        gScore = {}
        fScore = {}
        gScore[start] = 0

        fScore[start] = self.gama * gScore[start] + (1 - self.gama) * self.heuristicEstimate(start, goal)
        while len(openSet) != 0:
            current = self.getLowest(openSet, fScore)
            if current == goal:
                return self.reconstructPath(cameFrom, goal), gScore[goal]

            openSet.remove(current)
            closedSet.add(current)

            for edge_id, edge in self.neighborNodes(current).items():
                adjacent_id = edge.end_id

                tentative_gScore = gScore[current] + self.distBetween(edge)
                if adjacent_id in closedSet and tentative_gScore >= gScore[adjacent_id]:
                    continue

                if adjacent_id not in closedSet or tentative_gScore < gScore[adjacent_id]:
                    cameFrom[adjacent_id] = current
                    gScore[adjacent_id] = tentative_gScore
                    fScore[adjacent_id] = self.gama * gScore[adjacent_id] + (1 - self.gama) * self.heuristicEstimate(
                        adjacent_id, goal)

                    if adjacent_id not in openSet:
                        openSet.add(adjacent_id)
        return 0
