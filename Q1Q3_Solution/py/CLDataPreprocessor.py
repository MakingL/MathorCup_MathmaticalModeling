# -*- coding: utf-8 -*-

import datetime
import sys

class CLDataPerprocessor(object):

    def __init__(self, dataPath_passenger, dataPath_timeTable, dataPath_result):
        super(CLDataPerprocessor, self).__init__()
        self.dataPath_passenger = dataPath_passenger
        self.dataPath_timeTable = dataPath_timeTable
        self.dataPath_result = dataPath_result
        self.passengerList = list()
        self.timeTableList = list()
        pass

    def getdataFromFile(self):
        #读取时段内的乘客信息
        with open(self.dataPath_passenger, 'r') as datafile:
            for line in datafile:
                line = line.strip("\n")
                if line == "" or line.startswith("#"):
                    continue
                data = line.replace(" ","").replace("\t","")
                #乘客编号,始发车站,目的地车站,进站刷卡时刻,出站刷卡时刻
                p_id, p_origin, p_destination, p_startTime, p_endTime = data.split(",")
                passenger = {'id': p_id, 'origin': p_origin, 'destination': p_destination, 'startTime': p_startTime, 'endTime': p_endTime}
                self.passengerList.append(passenger)
        print("乘客数:{}".format(len(self.passengerList)))
        #读取时段内列车时刻表
        with open(self.dataPath_timeTable, 'r') as datafile:
            for line in datafile:
                line = line.strip("\n")
                if line == "" or line.startswith("#"):
                    continue
                data = line.replace(" ","").replace("\t","")
                #线路编号,车次号,车站编号,到达时刻,发车时刻
                _, _, station_id, _, train_startTime = data.split(",")
                timeTable = {'station_id': station_id, 'train_startTime': train_startTime}
                self.timeTableList.append(timeTable)
        print("时刻表数:{}".format(len(self.timeTableList)))
        self.Perprocess_passenger()
        pass

    def Perprocess_passenger(self):
        #将每个站点的最早发车时间和最晚发车时间存起来
        stationList = list()
        for timeTable in self.timeTableList:
            sstartTimeStr = "2019-4-13" + ":" + timeTable['train_startTime']
            sstartTime = datetime.datetime.strptime(sstartTimeStr, "%Y-%m-%d:%H:%M:%S")
            #计数器：用于判读是否有相同id的station
            forNum = 0
            for station in stationList:
                if (station['id'] == timeTable['station_id']):
                    forNum += 1
                    stationList.remove(station)
                    #newStation = {'id':,'est':,'lst':}
                    if(station['est'] > sstartTime):
                        station['est'] = sstartTime
                    if(station['lst'] < sstartTime):
                        station['lst'] = sstartTime
                    stationList.append(station)
            #元素为空或者没有匹配station的时候
            if (len(stationList) == 0 or forNum == 0): 
                station = {'id': timeTable['station_id'], 'est': sstartTime, 'lst': sstartTime}
                stationList.append(station)
                continue
        print("表内车站数:{}".format(len(stationList)))

        for passenger in self.passengerList:
            startTimeStr = "2019-4-13" + ":" + passenger['startTime']
            endTimeStr = "2019-4-13" + ":" + passenger['endTime']
            startTime = datetime.datetime.strptime(startTimeStr, "%Y-%m-%d:%H:%M:%S")
            endTime = datetime.datetime.strptime(endTimeStr, "%Y-%m-%d:%H:%M:%S")
            #出发站与到达站点相同的乘客 & 出站时间早于入站时间的乘客
            if (passenger['origin'] == passenger['destination'] or startTime >= endTime):
                self.passengerList.remove(passenger)
                continue
            #乘车超出地铁发车时间的乘客
            for station in stationList:
                if (passenger['origin'] == station['id'] and (startTime < station['est'] or startTime > station['lst'])):
                    self.passengerList.remove(passenger)
                    print(passenger)
            
        print("合法乘客数:{}".format(len(self.passengerList)))
        self.writeBackResult()
        pass

    def writeBackResult(self):
        with open(self.dataPath_result, "w+", encoding="UTF-8") as result_file:
            result_file.write("#乘客编号,始发车站,目的地车站,进站刷卡时刻,出站刷卡时刻\n")
            for passenger in self.passengerList:
                result_file.write("{},{},{},{},{} ".format(passenger['id'],
                passenger['origin'],
                passenger['destination'],
                passenger['startTime'],
                passenger['endTime']))
                result_file.write("\n")

    

if __name__ == "__main__":
    data_path_passenger = sys.argv[1]
    data_path_timeTable = sys.argv[2]
    data_path_result = sys.argv[3]
    obj_DataPerprocessor = CLDataPerprocessor(data_path_passenger, data_path_timeTable, data_path_result)
    obj_DataPerprocessor.getdataFromFile()
    