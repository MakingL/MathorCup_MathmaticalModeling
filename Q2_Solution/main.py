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
    # ************   2-A   ******************
    # 2-A 的解答保存在文件： data/user_path_answer_2A.txt 中
    solution = Solution2(answer_2A_file_path="./data/user_path_answer_2A.txt",)
    # 导入数据
    solution.load_data()
    logging.info("load data done")

    user_list = ["2", "7", "19", "31", "41", "71",
                 "83", "89", "101", "113", "2845", "124801",
                 "140610", "164834", "193196", "223919",
                 "275403", "286898", "314976", "315621"]
    logging.info("user id list is: {}".format(user_list))

    for userId in user_list:
        # 求解每个用户的路径数据
        solution.get_and_save_user_path(userId)
    # ************ 2-A END ******************

    # ************ 2-B **************
    # 2-B 的运行结果保存在文件： data/planed_user_path.txt 中
    solution = Solution2()
    # 导入数据
    solution.load_data()
    logging.info("load data done")

    # 按比例 user_sample_freq=100:1 采样数据，若采用所有数据，一般电脑下程序需要跑几天
    sampled_user_list = solution.sample_user_batch(user_sample_freq=100)

    # 统计用户出行线路长度及线路流量
    passed_user_set = solution.get_user_path_len_and_route_traffic(sampled_user_list)
    sampled_user_list = list(set(sampled_user_list) - passed_user_set)

    logging.info("passed user size: {} planing user list size: {}".format(len(passed_user_set),
                                                                          len(sampled_user_list)))
    sampled_user_list = list(set(sampled_user_list) - passed_user_set)

    logging.info("passed user size: {} planing user list size: {}".format(len(passed_user_set),
                                                                          len(sampled_user_list)))
    # 为乘客规划线路，并统计规划后的客流量
    solution.plan_user_path(sampled_user_list)
    # ************ 2-B END **************

    logging.info("Everything is Done")
