# -*- coding: utf-8 -*-

import sys
import math
import datetime
import seaborn as sns
import matplotlib.pyplot as plt

from collections import Counter

#import numpy as np

class CLDataDistributer(object):
    """
    用于计算：
    1.出行时段分布（24小时，对每个乘客的时间在时间段上计算）
    2.出行距离分布（）
    3.出行时长分布（差值）
    /拓展
    4.线路上的分布
    """
    
    def __init__(self, dataPath):
        super(CLDataDistributer, self).__init__()
        self.dataPath = dataPath
        self.passengerList = list()
        pass
    
    def getdataFromFile(self):
        with open(self.dataPath, 'r') as datafile:
            for line in datafile:
                line = line.strip("\n")
                if line == "" or line.startswith("#"):
                    continue
                data = line.replace(" ","").replace("\t","")
                #乘客编号,始发车站,目的地车站,进站刷卡时刻,出站刷卡时刻
                p_id, p_origin, p_destination, p_startTime, p_endTime = data.split(",")
                passenger = {'id': p_id, 'origin': p_origin, 'destination': p_destination, 'startTime': p_startTime, 'endTime': p_endTime}
                self.passengerList.append(passenger)
        print("参与计算乘客总数:{}".format(len(self.passengerList)))
        pass

    def distribute_period(self):
        x_period = [0 for n in range(24)]
        #x_period = list()
        for passenger in self.passengerList:
            startTime_H, _, _ = passenger['startTime'].split(":")
            startTimeStr = "2019-4-13" + ":" + passenger['startTime']
            endTimeStr = "2019-4-13" + ":" + passenger['endTime']
            startTime = datetime.datetime.strptime(startTimeStr, "%Y-%m-%d:%H:%M:%S")
            endTime = datetime.datetime.strptime(endTimeStr, "%Y-%m-%d:%H:%M:%S")
            duration = math.floor((endTime-startTime).seconds/3600)
            
            '''不合法的数据 --> 出站时间在进站时间之前
            if(int(startTime_H)+duration >= 24):
                print("id {}, startTime: {}, endTime: {}, startTime_H: {}, duration: {}".format(passenger['id'],
                passenger['startTime'], 
                passenger['endTime'],
                startTime_H,
                duration))
            '''
            
            if(int(startTime_H)+duration >= 24):
                continue
            if(duration == 0):
                x_period[int(startTime_H)] += 1
            else:
                for i in range(int(startTime_H), (int(startTime_H)+duration)):
                    x_period[i] += 1
            
            ''' sns绘制图使用
            if (duration == 0):
                x_period.append(int(startTime_H))
            else:
                for i in range(int(startTime_H), (int(startTime_H)+duration)):
                    x_period.append(i)
        sns.distplot(x_period, kde=True)
        plt.show()
        '''
        print("出行时段:{}".format(x_period))
        pass
    
    def distribute_duration(self):
        #出行时长
        durationList = list()
        for passenger in self.passengerList:
            startTimeStr = "2019-4-13" + ":" + passenger['startTime']
            endTimeStr = "2019-4-13" + ":" + passenger['endTime']
            startTime = datetime.datetime.strptime(startTimeStr, "%Y-%m-%d:%H:%M:%S")
            endTime = datetime.datetime.strptime(endTimeStr, "%Y-%m-%d:%H:%M:%S")
            durationList.append(math.ceil((endTime-startTime).seconds/3600))
        #list筛出相同的量
        x_duration = list()
        for duration in range(0,24):
            x_duration.append(durationList.count(duration))
        print("出行时长:{}".format(x_duration))
        pass

    #八通线 筛选出出发站或者结束站在八通线的乘客/计算各项分布
    def distribute_period_8tong(self):
        x_period = [0 for n in range(24)]
        #x_period = list()
        for passenger in self.passengerList:
            if(int(passenger['origin']) not in range(24,37) or int(passenger['destination']) not in range(24,37)):
                continue
            startTime_H, _, _ = passenger['startTime'].split(":")
            startTimeStr = "2019-4-13" + ":" + passenger['startTime']
            endTimeStr = "2019-4-13" + ":" + passenger['endTime']
            startTime = datetime.datetime.strptime(startTimeStr, "%Y-%m-%d:%H:%M:%S")
            endTime = datetime.datetime.strptime(endTimeStr, "%Y-%m-%d:%H:%M:%S")
            duration = math.floor((endTime-startTime).seconds/3600)
            
            if(int(startTime_H)+duration >= 24):
                continue
            if(duration == 0):
                x_period[int(startTime_H)] += 1
            else:
                for i in range(int(startTime_H), (int(startTime_H)+duration)):
                    x_period[i] += 1
        print("八通线出行时段:{}".format(x_period))
        pass

    def distribute_duration_8tong(self):
        #出行时长
        durationList = list()
        #line8Tong 24:36 车站数
        for passenger in self.passengerList:
            if(int(passenger['origin']) not in range(24,37) or int(passenger['destination']) not in range(24,37)):
                continue
            startTimeStr = "2019-4-13" + ":" + passenger['startTime']
            endTimeStr = "2019-4-13" + ":" + passenger['endTime']
            startTime = datetime.datetime.strptime(startTimeStr, "%Y-%m-%d:%H:%M:%S")
            endTime = datetime.datetime.strptime(endTimeStr, "%Y-%m-%d:%H:%M:%S")
            durationList.append(math.ceil((endTime-startTime).seconds/3600))
        #list筛出相同的量
        x_duration = list()
        for duration in range(0,24):
            x_duration.append(durationList.count(duration))
        print("八通线出行时长:{}".format(x_duration))
        pass


if __name__ == "__main__":
    data_path = sys.argv[1]
    obj_DataDistrict = CLDataDistributer(data_path)
    obj_DataDistrict.getdataFromFile()
    #obj_DataDistrict.distribute_period()
    #obj_DataDistrict.distribute_duration()
    obj_DataDistrict.distribute_duration_8tong()
    obj_DataDistrict.distribute_period_8tong()