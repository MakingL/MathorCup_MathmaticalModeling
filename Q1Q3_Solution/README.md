# 问题1解答
&emsp; 问题1要求分析基于以上数据的乘客出行特征，包括出行时段分布、出行距离分布、 出行时长分布。

&emsp; 首先使用 CLDayaPreprocessor.py 进行数据预处理。删除以下异常数据：
- 出发站点与到达站点相同的乘客
- 进站时间晚于出站时间的乘客
- 乘车时间超出地铁发车时间的乘客

&emsp; 然后使用 CLDataDistribution.py 统计出行分布，包括：
- 出行时段分布
- 出行时长分布
- 出发站或到达站在八通线的乘客出行时段分布
- 出发站或到达站在八通线的乘客出行时长分布

# 问题3解答
&emsp; 问题3要求分析在考虑限流的措施下，分析八通线的服务水平情况。

&emsp; 建立模型如下：
- 将服务水平体现为乘客出行总的用时，包括：在车站等待进站时间，在站台等车时间，在列车上时间。
- 使用限流措施改变的是在车站等待进站时间和在站台等车时间。
- 限流措施具体表现为限流强度，即在单位时间内，在站外等待人数与总到达人数的比值。
- 在站外等车时间可由限流强度与乘客到达车站的强度求得。
- 在站台等车时间则由列车发车间隔以及站台内等车的人数决定。

# 代码说明
## 环境说明
- 代码使用 Visual Studio Code(1.32.3) 编写
- 所有代码使用 python3 编写
- 可在 python3.7 环境下运行

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
