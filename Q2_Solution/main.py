# -*- coding: utf-8 -*-
# @Time    : 2019/6/3 22:47
# @Author  : MLee
# @File    : main.py
import logging

from Solution.Solution2 import Solution2

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        filename='./logs/solution_main.log',
                        format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filemode='w+')

    # 禁止日志输出
    # logging.disable(logging.INFO)
    # logging.disable(logging.ERROR)

    solution = Solution2()
    # 导入数据
    solution.load_data()
    logging.info("load data done")

    sampled_user_list = solution.sample_user_batch(user_sample_freq=100)

    # 统计用户出行线路长度及线路流量
    passed_user_set = solution.get_user_path_len_and_route_traffic(sampled_user_list)
    sampled_user_list = list(set(sampled_user_list) - passed_user_set)

    logging.info("passed user size: {} planing user list size: {}".format(len(passed_user_set),
                                                                          len(sampled_user_list)))    # passed_user_set = solution.get_user_path_len_and_route_traffic(sampled_user_list)
    sampled_user_list = list(set(sampled_user_list) - passed_user_set)

    logging.info("passed user size: {} planing user list size: {}".format(len(passed_user_set),
                                                                          len(sampled_user_list)))
    # 为乘客规划线路，并统计规划后的客流量
    solution.plan_user_path(sampled_user_list)

    logging.info("Everything is Done")
