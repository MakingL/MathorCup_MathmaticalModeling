# -*- coding: utf-8 -*-

import datetime

class CLStation(object):

    def __init__(self):
        super(CLStation, self).__init__()
        #id
        self.m_stationId = int()
        #站外人数
        self.m_passengerOuter = list()
        #站内人数
        self.m_passengerInner = list()
        #本站限流强度
        self.m_limitingRate = float()
        #上次到达的人数
        self.m_lastArrival = int()
        pass
    

class CLTrain(object):

    def __init__(self):
        super(CLTrain, self).__init__()
        #列车编号
        self.m_id = str()
        #车上乘客
        self.m_passenger = list()
        #列车时刻表
        self.m_timeToStationList = list() 
        pass


class CLPassenger(object):

    def __init__(self):
        super(CLPassenger, self).__init__()
        #出发车站
        self.m_startStation = int()
        #目的车站
        self.m_endStation = int()
        #到站时间
        self.m_toStationTime = datetime.datetime.now()
        #进站时间
        self.m_inStationTime = datetime.datetime.now()
        #上车时间
        self.m_inTrainTime = datetime.datetime.now()
        #下车时间
        self.m_outTrainTime = datetime.datetime.now()
        pass