import os
import time
import random
from . import MsgPluginTemplate, DealMsgThread, ChatMsgStruct, MsgType
from . import NotConfigured
from . import settings

name = os.path.basename(__file__)[:-3]

class AutoReply(MsgPluginTemplate):
    def __init__(self, wxfunction, dtObj:DealMsgThread) -> None:
        super().__init__(wxfunction, dtObj)
        words_filepath = getattr(settings, "AUTO_REPLY_MSG_FILEPATH", None)
        if not getattr(settings, "AUTO_REPLY_FRIEND", None) or words_filepath:
            raise NotConfigured
        self.words = self.load_words(words_filepath)
        print(f"插件[{self._name(__file__)}]加载成功")
        self.reply_friends = getattr(settings, "AUTO_REPLY_FRIEND")
    
    def load_words(self, words_filepath:str):
        '''加载关键词'''
        if not os.path.exists(words_filepath):
            return []
        with open(words_filepath, encoding='utf-8') as f:
            words = [i.strip() for i in f.readlines() if i.strip()]
        return words

    def deal_msg(self, msg_struct:ChatMsgStruct):
        if msg_struct.is_self_msg or msg_struct.msg_type in (MsgType.NOTICE, MsgType.SYSMSG):
            return
        # 15分钟前的消息不回复
        if msg_struct.timestamp < int(time.time())-15*60:
            return 
        if self.is_target_friend(msg_struct):
            self.send_reply(msg_struct)
    
    def send_reply(self, msg_struct:ChatMsgStruct):
        '''从auto_reply.txt文件里随机发送一条回复消息'''
        sender = msg_struct.sender
        reply_msg = random.choice(self.words)
        self.wxfunction.SendTextMsg(sender, reply_msg)
    
    def is_target_friend(self, msg_struct:ChatMsgStruct):
        '''判断是不是配置文件中的好友发送的消息'''
        sender = msg_struct.sender
        sender_wxh = self.dtObj.contacts_wxh.get(sender)
        if sender_wxh in self.reply_friends:
            return True