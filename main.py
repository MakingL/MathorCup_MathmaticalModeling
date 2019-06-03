# -*- coding: utf-8 -*-
# @Time    : 2019/6/3 22:47
# @Author  : MLee
# @File    : main.py
import logging

from Solution.Solution2A import Solution2A
from Solution.Solution2B import Solution2B

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        filename='./logs/solution_main.log',
                        format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filemode='w+')

    # 禁止日志输出
    # logging.disable(logging.INFO)
    # logging.disable(logging.ERROR)

    # ===== 2-A 答案求解======
    # 构建问题求解对象
    solution_2A = Solution2A()
    # 导入数据
    solution_2A.load_data()
    logging.info("2A load data done")

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
        solution_2A.get_and_save_user_path(userId)

    # ===============
    # 统计用户出行线路长度及线路流量，
    # solution_2A.get_user_path_len_and_route_traffic()
    # ===== 2-A =======


    # ============ 2-B ============
    solution_2B = Solution2B()
    solution_2B.load_data()
    logging.info("2B load data done")
    solution_2B.build_graph()

    solution_2B.plan_all_user_path()
    # ============ 2-B ============

    logging.info("Everything is Done")
