# -*- coding: utf-8 -*-
# @File    : GraphConf.py


class Road(object):
    """docstring for Road"""

    def __init__(self, road_conf):
        super(Road, self).__init__()
        self.road_id, self.road_len, self.start_id, self.end_id = road_conf
        self.weight = self.road_len
        # self.weight = 2


class Graph(object):
    """docstring for Graph"""

    def __init__(self, graph_dict=None):
        super(Graph, self).__init__()
        self.vertex_set = set()
        self.edge_set = set()
        self.edge_dict = dict()
        self.adjacent_edge_dict = dict(dict())
        self.graph_dict = graph_dict if graph_dict is not None else dict(set())
        self.graph_adjacent_dict = dict(dict())
        self.total_chanel = 0
        self.total_speed = 0

        self.min_weight = 0x3f3f3f3f
        self.max_weight = 0
        self.total_weight = 0

    def add_edge(self, start_id, edge_id, edge):
        """
        新增边操作；更新图的联接表，更新顶点集、边集
        :param start_id:
        :param edge_id:
        :param edge:
        :return:
        """
        # 联接表
        if start_id not in self.graph_dict:
            self.graph_dict[start_id] = set()
        self.graph_dict[start_id].add(edge)

        # 边集
        self.edge_set.add(edge_id)
        self.edge_dict[edge_id] = edge

        # 邻接矩阵
        end_id = edge.end_id
        if start_id not in self.graph_adjacent_dict:
            self.graph_adjacent_dict[start_id] = dict()
        self.graph_adjacent_dict[start_id][end_id] = edge

        # 顶点和边 id 的邻接关系
        if start_id not in self.adjacent_edge_dict:
            self.adjacent_edge_dict[start_id] = dict()
        self.adjacent_edge_dict[start_id][end_id] = edge_id


        # 顶点集
        self.add_vertex(start_id)
        self.add_vertex(edge.end_id)

        self.min_weight = min(edge.weight, self.min_weight)
        self.max_weight = max(edge.weight, self.max_weight)
        self.total_weight += edge.weight

    def get_average_weight(self):
        return self.total_weight / self.get_edge_count()

    def get_neighbors(self, current_id):
        neighbors = dict()
        for edge in self.graph_dict[current_id]:
            neighbors[edge.road_id] = edge

        return neighbors

    def add_vertex(self, node_id):
        self.vertex_set.add(node_id)

    def get_vertex_count(self):
        return len(self.vertex_set)

    def get_vertex_list(self):
        return list(self.vertex_set)

    def get_edge_count(self):
        return len(self.edge_set)

    def update_edge_weight(self, edge_id, new_weight):
        self.edge_dict[edge_id].weight = new_weight

    def change_edge_weight(self, edge_id, weight_delta):
        """
        更改边上的权值
        :param edge_id: 边的 id
        :param weight_delta: 权值变化值，可正可负
        :return:
        """
        change_before = self.edge_dict[edge_id].weight
        self.edge_dict[edge_id].weight += weight_delta
        return change_before, self.edge_dict[edge_id].weight

    def change_edge_travel_times(self, edge_id, times_delta):
        self.edge_dict[edge_id].traveled_times += times_delta

    def decay_edge_weight(self, edge_id, decay_ratio):
        self.edge_dict[edge_id].weight *= decay_ratio

    def get_edge_traveled_times(self, edge_id):
        return self.edge_dict[edge_id].traveled_times

    def get_average_chanel(self):
        return self.total_chanel / self.get_edge_count()

    def get_vertex_degree(self, vertex_id):
        return len(self.graph_dict[vertex_id])

    def get_edge_obj(self, start, end):
        start_adjacent = self.graph_adjacent_dict.get(start, None)
        if start_adjacent is None:
            return None

        return start_adjacent.get(end, None)

    def get_edge_form_id(self, edge_id):
        return self.edge_dict.get(edge_id, None)

    def get_adjacent_edge_id(self, start_vertex, end_vertex):
        edge_id = self.adjacent_edge_dict[start_vertex][end_vertex]

        # 反向边是以 “_b” 符号连接的
        edge_id = edge_id.replace("_b", "")
        return edge_id

    def get_graph_dict(self):
        """
        返回图的联接表
        :return:
        """
        return self.graph_dict

    def get_edge_dict(self):
        return self.edge_dict

    def get_adjacent_edge_dict(self):
        return self.adjacent_edge_dict

    def get_average_road_speed(self):
        return self.total_speed / self.get_edge_count()

    def get_edge_weight(self, edge_id):
        return self.edge_dict[edge_id].weight
