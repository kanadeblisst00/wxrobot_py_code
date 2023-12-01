import os
from abc import ABC, abstractmethod


class PluginTemplate(ABC):
    def __init__(self, wxfunction) -> None:
        self.wxfunction = wxfunction

    @abstractmethod
    def run(self):
        pass

    def start(self):
        self.run()

    def join(self):
        '''关闭资源'''
    
    def _name(self, file):
        return os.path.basename(file)[:-3]


class MsgPluginTemplate(ABC):
    def __init__(self, wxfunction, dtObj) -> None:
        '''dtObj: 是deal_msg.py里的DealMsgThread实例化的对象'''
        self.wxfunction = wxfunction
        self.dtObj = dtObj
    
    @abstractmethod
    def deal_msg(self, msg_struct):
        pass

    def _name(self, file):
        return os.path.basename(file)[:-3]