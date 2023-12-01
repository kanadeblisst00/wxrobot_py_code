import os
import re
import time
import xml.etree.ElementTree as ET 
from . import MsgPluginTemplate, ChatMsgStruct, MsgType, XmlMsgType, DealMsgThread 
from . import get_wxid_from_contact_list
from . import settings, NotConfigured


class MonitorKeywords(MsgPluginTemplate):
    '''监控群消息，如果触发关键词，则调用remind_me方法, 下面的例子是给小号发送预警提示'''
    def __init__(self, wxfunction, dtObj:DealMsgThread) -> None:
        '''dtObj: 是deal_msg.py里的DealMsgThread实例化的对象'''
        super().__init__(wxfunction, dtObj)
        self.dtObj = dtObj
        self.keyword_filepath = getattr(settings, "DEFAULT_MONITOR_KEYWORDS_FILEPATH", None)
        self.re_keyword_filepath = getattr(settings, "RE_MONITOR_KEYWORDS_FILEPATH", None)
        if not getattr(settings, "IS_MONITOR_KEYWORDS", None) :
            raise NotConfigured
        if not self.keyword_filepath and not self.re_keyword_filepath:
            raise NotConfigured
        remind_msg_wxh = getattr(settings, "SEND_REMIND_WXH", None)
        self.send_remind_wxid = get_wxid_from_contact_list(self.dtObj.contact_list, wxh=remind_msg_wxh)
        self.mode = getattr(settings, "MONITOR_KEYWORDS_MODE")
        self.keywords, self.re_keywords = self.load_keywords()
        print(f"插件[{self._name(__file__)}]加载成功")
        self.is_reply_friends = getattr(settings, "IS_MONITOR_KEYWORDS")
    
    def load_keywords(self):
        '''加载关键词'''
        keyword_filepath = self.keyword_filepath
        re_keyword_filepath = self.re_keyword_filepath
        if keyword_filepath and os.path.exists(keyword_filepath):
            with open(keyword_filepath, encoding='utf-8') as f:
                keywords = [i.strip() for i in f.readlines() if i.strip()]
        else:
            keywords = []
        if re_keyword_filepath and os.path.exists(re_keyword_filepath):
            with open(re_keyword_filepath, encoding='utf-8') as f:
                re_keywords = [i.strip() for i in f.readlines() if i.strip()]
        else:
            re_keywords = []
        return keywords, re_keywords

    def deal_msg(self, msg_struct:ChatMsgStruct):
        '''处理消息的函数'''
        if "@chatroom" not in msg_struct.sender:
            return 
        if msg_struct.timestamp < int(time.time())-2*60*60:
            return 
        text = self.get_text_content(msg_struct)
        if not text:
            return 
        keyword = self.is_contain_keyword(text, msg_struct)
        self.remind_me(keyword, text, msg_struct)

    def remind_me(self, keyword, text, msg_struct:ChatMsgStruct):
        '''触发关键词的预警函数'''
        if not keyword:
            return
        sender = msg_struct.sender
        sender_name = self.dtObj.get_sender_name(sender)
        sender_str = f"{sender_name}[{sender}]"
        msg = f'''*************触发监控预警*************\r\n关键词: {keyword}\r\n发送人[群]: {sender_str}\r\n'''
        room_nickname = msg_struct.room_nickname
        room_sender = msg_struct.room_sender
        if room_nickname:
            msg += f"群成员: {room_nickname}[{room_sender}]\r\n"
        msg += f"消息内容: {text}"
        # 根据微信号查找好友，然后给这个好友发送预警消息
        if self.send_remind_wxid:
             self.wxfunction.SendTextMsg(self.send_remind_wxid, msg)

    def is_contain_keyword(self, text:str, msg_struct:ChatMsgStruct):
        '''判断是否包含关键词'''
        for keyword in self.keywords:
            if self.default_match_rule(keyword, text):
                return keyword
        for keyword in self.re_keywords:
            if re.match(keyword, text):
                return keyword
    
    def default_match_rule(self, rule, text):
        '''默认规则匹配'''
        eval_str = ""
        word = ""
        for c in rule:
            if c in ("(", ")","+","|"):
                if word:
                    expression = f'"{word[1:]}" not in text' if word.startswith("-") else f'"{word}" in text'
                    eval_str += expression
                    word = ""
                if c == "(" or c == ")":
                    eval_str += c
                elif c == "|":
                    eval_str += " or "
                elif c == "+":
                    eval_str += " and "
            else:
                word += c
        if word:
            expression = f'"{word[1:]}" not in text' if word.startswith("-") else f'"{word}" in text'
            eval_str += expression
        #print(eval_str)
        return eval(eval_str)

    def get_text_content(self, msg_struct:ChatMsgStruct):
        '''获取消息文本内容，忽略其他类型消息'''
        content = None
        
        if msg_struct.msg_type == MsgType.TEXT:
            content = msg_struct.content
        elif msg_struct.msg_type == MsgType.XML: # 判断引用消息
            root = ET.fromstring(msg_struct.content) 
            _type = int(root.find('.//type').text)
            if _type == XmlMsgType.REFERENCE_MSG:
                content = root.find('.//appmsg/title').text
        return content