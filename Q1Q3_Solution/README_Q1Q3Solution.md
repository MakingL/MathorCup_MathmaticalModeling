# 问题1解答
-----

# 问题3解答
-----

# 说明
------

## 环境说明
- 代码使用 Visual Studio Code(1.32.3) 编写
- 所有代码使用 python3 编写
- 可在 macOS 或 Linux 环境下运行

## 代码文件说明
- CLDataPreprocessor.py
    用于预处理数据，生成合法数据存入新的文件
    ```
    运行命令：
        python3 py/dataPreprocessor.py data/data1_O:D_ov.txt data/data3_time_table.txt data/data1_O:D.txt
    ```

- CLDataDistribution.py
    用于**问题1**求解数据分布
    ```
    运行命令：
        python3 py/dataDistribution.py data/data1_O:D.txt  
    ```

- CLSimulator_8t.py
    模拟器代码，用于**问题3**模型模拟，生成模拟用时
    ```
    运行命令：
        python3 py/CLSimulator_8t.py data/data1_O:D.txt data/data3_time_table.txt
    ```
- CLStation_CLTrain_CLPassenger_8t.py
    用于问题3模拟器的一些辅助类的定义，处理全部放在 CLSimulator 类中

## 数据文件说明
- data1_O:D_ov.txt -------------------------------- 原始乘客出行信息
- data1_O:D.txt ----------------------------------- 预处理后的乘客出行信息
- data2.1_station.txt ------------------------------ 车站编号
- data2.2_line.txt --------------------------------- 线路编号
- data2.3_distance_between_two_station.txt ------ 站间距离信息
- data3_time_table ------------------------------- 列车时刻表