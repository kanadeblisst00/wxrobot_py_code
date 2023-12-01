import os
from threading import Timer
from . import PluginTemplate
from . import NotConfigured
from . import settings
from . import get_wxid_from_contact_list

name = os.path.basename(__file__)[:-3]


class SendMsg(PluginTemplate):
    def __init__(self, wxfunction) -> None:
        super().__init__(wxfunction)
        if not getattr(settings, "ENABLE_AUTO_SEND_MSG", None):
            raise NotConfigured
        print(f"插件[{self._name(__file__)}]加载成功")
        self.contact_list = list(wxfunction.GetContactList())
    
    def run(self):
        self.send(5 * 60)

    def send(self, interval, is_first=True):
        '''每隔interval秒发一次消息'''
        # 如果不这样判断，他会在运行时立马发送一次消息
        if not is_first:
            # 通过微信号查找对应的wxid，也可以通过备注和昵称查找
            wxid = get_wxid_from_contact_list(self.contact_list, wxh="kanadeblisst")
            # 给该好友发送测试消息
            self.wxfunction.SendTextMsg(wxid, "测试消息！")
        # 创建定时器，间隔interval秒后再发一次消息
        timer = Timer(interval, self.send, args=(interval, False))
        timer.start()
        