# -*- coding: utf-8 -*-

import sys
import gc
import numpy
import datetime
import math

from CLStation_CLTrain_CLPassenger_8t import CLStation, CLTrain, CLPassenger

class CLSimulator(object):

    def __init__(self, dataPath_passenger, dataPath_timeTable,):
        super(CLSimulator, self).__init__()
        self.dataPath_timeTable = dataPath_timeTable
        self.dataPath = dataPath_passenger
        self.timeTableList = list()
        self.passengerList = list()
        self.passengerListForResult = list()
        self.trainList = list()
        #全局时间 时间的范围确定
        self.simulatorTime = datetime.datetime.strptime("2019-4-13:7:00:00", "%Y-%m-%d:%H:%M:%S")
        #下车概率(转移概率)
        self.getOffP = numpy.zeros([14,14])
        #模拟人数
        self.simulatorPassenger = list()
        #车站列表
        self.stationList = list()
        #到达强度
        self.arrivalRate_Day = list()
        self.arrivalRate_Station = numpy.zeros([14])
        #每10分钟到达人数(处理时候会与到达强度相乘 1700最合实际)
        self.arrivalPassengerNumPerT = 1700
        #全局限流强度(各个车站) 24-37 14个站点 1表示限流emmm
        self.limitingRate = 0.5
        #self.limitingRateList_Station = [1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        self.limitingRateList_Station = [0,0,0,0,0,0,0,0,0,0,0,0,0,1]
        self.limiting()
        self.initStation()
        #结果
        #站外等待时间
        self.waitTimeOuterStation = 0
        #站内等待时间
        self.waitTimeInnerStation = 0
        #车上时间
        self.waitTimeInTrain = 0
        #经过系统模拟的人数
        self.simulatorPassengerCount = 0
        pass
    
    def perprocess(self):
        #--获取八通线列车信息--
        with open(self.dataPath_timeTable, 'r') as datafile:
            for line in datafile:
                line = line.strip("\n")
                if line == "" or line.startswith("#"):
                    continue
                data = line.replace(" ","").replace("\t","")
                #线路编号,车次号,车站编号,到达时刻,发车时刻
                line_id, train_id, station_id, train_endTime, train_startTime = data.split(",")
                timeTable = {'line_id': line_id, 'train_id':train_id, 'station_id': station_id, 'train_startTime': train_startTime,  'train_endTime': train_endTime}
                self.timeTableList.append(timeTable)
        print("时刻表数:{}".format(len(self.timeTableList)))
        #筛选出八通线的所有列车
        for timeTable in self.timeTableList:
            #7:00:00之后的车
            if datetime.datetime.strptime("2019-4-13:" + timeTable['train_startTime'], "%Y-%m-%d:%H:%M:%S") <= datetime.datetime.strptime("2019-4-13:7:00:00", "%Y-%m-%d:%H:%M:%S"):
                continue
            if timeTable['line_id'] == '3':
                forCount = 0
                for train in self.trainList:
                    if train.m_id == timeTable['train_id']:
                        self.trainList.remove(train)
                        timeToStation = {'station_id': timeTable['station_id'], 'time': "2019-4-13:" + timeTable['train_startTime']}
                        train.m_timeToStationList.append(timeToStation)
                        self.trainList.append(train)
                        forCount += 1
                if forCount == 0:
                    obj_train = CLTrain()
                    obj_train.m_id = timeTable['train_id']
                    timeToStation = {'station_id': timeTable['station_id'], 'time': "2019-4-13:" + timeTable['train_startTime']}
                    obj_train.m_timeToStationList.append(timeToStation)
                    self.trainList.append(obj_train)
        print('八通线列车数量:{}'.format(len(self.trainList)))

        #释放无用信息
        del self.timeTableList
        gc.collect()

        #--读取乘客信息--
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
        print('总人数:{}'.format(len(self.passengerList)))
        #筛选出在八通线上或下车的乘客
        passengerListIn8T = list()
        for passenger in self.passengerList:
            if int(passenger['origin']) in range(24,37) or int(passenger['destination']) in range(24,37):
                passengerListIn8T.append(passenger)
        self.passengerList = passengerListIn8T
        print('经过八通线的人数:{}'.format(len(self.passengerList)))

        #--计算乘客转移概率--
        passengerNum = 0
        for passenger in self.passengerList:
            #r
            if int(passenger['origin']) in range(24,37):
                #l
                if int(passenger['destination']) in range(24,37):
                    self.getOffP[int(passenger['origin'])-24][int(passenger['destination'])-24] += 1
                    passengerNum += 1
                else:
                    #终点在别的线路，设为25-四惠东
                    self.getOffP[int(passenger['origin'])-24][12] += 1
                    passengerNum += 1
            else:
                #起点在别的线路，设为25-四惠东
                self.getOffP[13][int(passenger['destination'])-24] += 1
                passengerNum += 1
        #转化为概率
        for i in range(0,14):
            for j in range(0,14):
                self.getOffP[i][j] = round(float(self.getOffP[i][j]) / passengerNum, 5)
        print("转移矩阵:{}".format(self.getOffP))

        #--计算全天乘客到达强度--
        x_period = [0 for n in range(24)]
        passengerCount = 0
        for passenger in self.passengerList:
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
                passengerCount += 1
            else:
                for i in range(int(startTime_H), (int(startTime_H)+duration)):
                    x_period[i] += 1
                    passengerCount += 1
        print("出行时段:{}".format(x_period))


        for i in range(0,24):
            x_period[i] /= passengerCount
        self.arrivalRate_Day = x_period
        print("全天达到强度:{}".format(self.arrivalRate_Day))

        #--计算每个站点同一时段的到达率--
        passengerNum = 0
        for passenger in self.passengerList:
            if int(passenger['origin']) in range(24,37):
                self.arrivalRate_Station[int(passenger['origin'])-24] += 1
                passengerNum += 1
            else:
                self.arrivalRate_Station[13] += 1
                passengerNum += 1
        print("各站达到人数:{}".format(self.arrivalRate_Station))
        #归一化
        for i in range(0,14):
            self.arrivalRate_Station[i] /= passengerNum
        print("各站达到强度:{}".format(self.arrivalRate_Station))
        print("初始化准备数据-->完成")
        pass
        
    #---=-=-=-=---#
    def start(self):
        '''
        时间 += 1s
            判断是否是10分钟
                是的话更新限流人数(放人进车站)
        判断是否有车到站
            如果有车到站的话：上下车人数变动 -> 调用车站里的方法
            如果车到达终点(时间list走到最后): 标记到达终点站从self.train中删除
        '''
        self.perprocess()
        self.initPassenger()
        timeCount = 0
        while True:
            #时间步进
            self.simulatorTime += datetime.timedelta(seconds = 1)
            #print("当前时间:{}".format(self.simulatorTime))
            timeCount += 1
            nowTime = self.simulatorTime
            #判断是否已经到23:59:59
            if self.simulatorTime == datetime.datetime.strptime("2019-4-13:23:59:00", "%Y-%m-%d:%H:%M:%S"):
                #进入结果统计
                self.printResult()
                break

            #判断这一秒的情况是否是10分钟
            if timeCount == 600:
                timeCount = 0
                for station in self.stationList:
                    #print("调用乘客进站方法")
                    self.passengerInStation(nowTime)

            #判断这一秒的情况有没有列车到站
            for train in self.trainList:
                for timeToStation in train.m_timeToStationList:
                    if datetime.datetime.strptime(timeToStation['time'], "%Y-%m-%d:%H:%M:%S") == nowTime:
                        #列车进站，乘客上下车
                        for station in self.stationList:
                            if station.m_stationId == int(timeToStation['station_id']):
                                #乘客上下车
                                self.passengerTransTrain(nowTime, train, station)     

    #初始化限流强度
    def limiting(self):
        for i in range(0,14):
            #如果限流
            if self.limitingRateList_Station[i] == 0:
                self.limitingRateList_Station[i] = self.limitingRate
            else:
                self.limitingRateList_Station[i] = 0
        print("初始化限流强度-->完成")
        pass
            
    
    #初始化站点信息(可以通过m_limitingRate修改限流强度)
    def initStation(self):
        for i in range(0,14):
            obj_station = CLStation()
            obj_station.m_stationId = i + 24
            self.stationList.append(obj_station)
        print("初始化站点信息-->完成")
        pass

    #初始化7:00之前到达的乘客
    def initPassenger(self):
        #5，6两个小时到达的总人数
        arrivalPassengerNum = self.arrivalPassengerNumPerT * 12 * (self.arrivalRate_Day[5] + self.arrivalRate_Day[6])
        #使用到达率算出各个站到达的人数
        for i in range(0,len(self.stationList)):
            epassenger = math.ceil(self.arrivalRate_Station[i] * arrivalPassengerNum)
            for j in range(0,epassenger+1):
                obj_passenger = CLPassenger()
                obj_passenger.m_toStationTime = datetime.datetime.strptime("2019-4-13:6:30:00", "%Y-%m-%d:%H:%M:%S")
                #设置出发站点
                obj_passenger.m_startStation = self.stationList[i].m_stationId
                self.stationList[i].m_passengerOuter.append(obj_passenger)
                self.stationList[i].m_lastArrival = epassenger

        #对站外乘客设置目的站点
        for station in self.stationList:
            passengerNum = len(station.m_passengerOuter)
            #算出各个目的点的人数
            passengerNumList = list()
            for i in range(0,14):
                PassengerForThisStation = math.ceil(passengerNum * self.getOffP[station.m_stationId - 24][i])
                passengerNumList.append(PassengerForThisStation)
            #对本站站外人数设置目的
            for index in range(0,len(passengerNumList)):
                rangeL = 0
                rangeR = 0
                if index != 0:
                    rangeL = passengerNumList[index-1]
                rangeR = rangeL + passengerNumList[index] + 1
                for j in range(rangeL,rangeR):
                    station.m_passengerOuter[j].m_endStation = index + 24
        print("初始运营时间段外到站的乘客-->完成")
        pass

    #限流的话放人进站
    def passengerInStation(self,nowTime):
        #现有乘客进站 -- 按照限流强度
        for station in self.stationList:
            inPassengerNum = math.ceil(station.m_lastArrival * (1-self.limitingRateList_Station[station.m_stationId-24]))
            for passenger in station.m_passengerOuter:
                inPassengerNum -= 1
                if inPassengerNum > 0:
                    station.m_passengerOuter.remove(passenger)
                    passenger.m_inStationTime = nowTime
                    station.m_passengerInner.append(passenger)
                    #print("站内乘客举例:{}".format(passenger.m_inStationTime))
        #--new新的乘客到达，开始等候--
        #时段计算
        strnowTime = nowTime.strftime('%Y:%m:%d:%H:%M:%S')
        _,_,_,time_H,_,_ = strnowTime.split(":")
        arrivalPassengerNum = math.floor(self.arrivalPassengerNumPerT * self.arrivalRate_Day[int(time_H)])
        #print(arrivalPassengerNum)
        if(arrivalPassengerNum <= 0):
            self.printResult()
        #使用到达率算出各个站到达的人数
        for i in range(0,len(self.stationList)):
            epassenger = math.ceil(self.arrivalRate_Station[i] * arrivalPassengerNum)
            for j in range(0,epassenger+1):
                obj_passenger = CLPassenger()
                obj_passenger.m_toStationTime = nowTime
                #设置出发站点
                obj_passenger.m_startStation = self.stationList[i].m_stationId
                self.stationList[i].m_passengerOuter.append(obj_passenger)
                self.stationList[i].m_lastArrival = epassenger
        #对站外乘客设置目的站点
        for station in self.stationList:
            passengerNum = len(station.m_passengerOuter)
            #算出各个目的点的人数
            passengerNumList = list()
            for i in range(0,14):
                PassengerForThisStation = passengerNum * self.getOffP[station.m_stationId - 24][i]
                passengerNumList.append(PassengerForThisStation)
            #对本站站外人数设置目的
            for index in range(0,len(passengerNumList)):
                rangeL = 0
                if index != 0:
                    rangeL = int(passengerNumList[index-1])
                else:
                    rangeL = 0

                rangeR = rangeL + int(passengerNumList[index])
                for j in range(rangeL,rangeR):
                    station.m_passengerOuter[j].m_endStation = index + 24
                    #print("index+24={}".format(index + 24))
        pass

    #车辆到站时候人数变动
    def passengerTransTrain(self, nowTime, train, station):
        #先下
        #print("列车容量:{}".format(1428-len(train.m_passenger)))
        if len(train.m_passenger) > 0:
            for passengerInTrain in train.m_passenger:
                if passengerInTrain.m_endStation == station.m_stationId:
                    train.m_passenger.remove(passengerInTrain)
                    passengerInTrain.m_outTrainTime = nowTime
                    #self.passengerListForResult.append(passengerInTrain)
                    self.getResult(passengerInTrain)
                    self.simulatorPassengerCount += 1 
                    print("下车乘客:{}".format(passengerInTrain.m_outTrainTime)) 
        #后上
        vacancy = 1428 - len(train.m_passenger)
        for passenger in station.m_passengerInner:
            if vacancy == 0:
                break
            station.m_passengerInner.remove(passenger)
            passenger.m_inTrainTime = nowTime
            train.m_passenger.append(passenger)
            vacancy -= 1
            #print("上车乘客举例:{}".format(passenger.m_inTrainTime))
        pass

    #计算结果
    def getResult(self, passenger):

        toStationTime = passenger.m_toStationTime
        inStationTime = passenger.m_inStationTime 
        inTrainTime = passenger.m_inTrainTime
        outTrainTime = passenger.m_outTrainTime

        self.waitTimeOuterStation = (inStationTime - toStationTime).seconds + self.waitTimeOuterStation
        self.waitTimeInnerStation += (inTrainTime - inStationTime).seconds
        self.waitTimeInTrain += (outTrainTime - inTrainTime).seconds

        del passenger
        gc.collect()
        pass
    
    def printResult(self):

        print("站外等待时间:{}".format(self.waitTimeOuterStation / 60))
        print("站内等待时间:{}".format(self.waitTimeInnerStation / 60))
        print("车上时间:{}".format(self.waitTimeInTrain / 60))

        print("站外等待时间(平均):{}".format(self.waitTimeOuterStation / self.simulatorPassengerCount / 60))
        print("站内等待时间(平均):{}".format(self.waitTimeInnerStation / self.simulatorPassengerCount / 60))
        print("车上时间(平均):{}".format(self.waitTimeInTrain / self.simulatorPassengerCount / 60))

        print("总等待时间:{}".format(self.waitTimeOuterStation + self.waitTimeInnerStation + self.waitTimeInTrain))
        print("总平均等待时间:{}".format((self.waitTimeOuterStation + self.waitTimeInnerStation + self.waitTimeInTrain)/self.simulatorPassengerCount/60))


if __name__ == "__main__":
    data_path_passenger = sys.argv[1]
    data_path_timeTable = sys.argv[2]
    obj_Simulator = CLSimulator(data_path_passenger, data_path_timeTable) 
    obj_Simulator.start()