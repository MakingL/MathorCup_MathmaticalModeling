# 源代码运行说明

## 介绍

本代码主要用来解决第二题的问题。使用 `python3` 版本解释器

## 文件结构说明

第二题求解的主要代码在 get_solution_2.py 中实现，其他文件夹为问题求解的辅助 python 包

- main.py 为求解问题的主要代码文件
- AStar 文件夹为所实现的 A*  算法包
- Floyd 文件夹为所实现的 Floyd 算法包
- Graph 文件夹为所实现的有向赋权图模型
- RouteInfo 文件夹地铁线路信息类
- UserInfo 文件夹乘客信息类
- Solution 文件夹为解决问题所用的类
- data 给的附件中的数据及程序输出保存的目录
- logs 为代码运行生成的日志文件数据

## 运行代码

- 运行环境

    `python3.6`

- 运行命令

    python main.py

执行该命令，即可运行该脚本，计算第二题的结果

## 程序输出

若代码被正确执行，第二题的结果将保存在 data 目录下的 answer_2A.txt 及 answer_2B.txt 文件下。
