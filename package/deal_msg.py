#-*- coding: utf-8 -*-
import os
import stat
import json
import time
import shutil
import requests
import traceback
from typing import Callable, List
from types import ModuleType
from threading import Thread, Event
import xml.etree.ElementTree as ET 
from .wxstruct import MsgType, ChatMsgStruct, XmlMsgType, SysMsgType
from .WechatImageDecoder import WechatImageDecoder

import inspect
from importlib import import_module
from abc import ABC, ABCMeta
from threading import Thread
from .plugin_class import PluginTemplate, MsgPluginTemplate


class NotConfigured(Exception):
    pass

def get_classes_from_module(module):
    is_abstract = lambda cls: ABC in cls.__bases__ or ABCMeta in cls.__bases__
    # 优先选择PluginTemplate的子类
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and not is_abstract(obj) and (issubclass(obj, PluginTemplate) or issubclass(obj, MsgPluginTemplate)):
            return obj
        
    for name, obj in inspect.getmembers(module):
        if obj == DealMsgThread:
            continue
        if inspect.isclass(obj) and not is_abstract(obj) and issubclass(obj, Thread):
            return obj


def load_plugins():
    plugins_path = "plugins"
    msg_plugins = []
    gen_plugins = []
    for file in os.listdir(plugins_path):
        # 以_开头或者不是py结尾的脚本不执行
        if file.startswith('_') or not file.endswith('.py'):
            continue
        plugin_name = file[:-3]
        try:
            plugin_module = import_module(f"{plugins_path}.{plugin_name}")
        except Exception as e:
            print(f"{plugin_name} import error: {e}")
            continue
        plugin_class = get_classes_from_module(plugin_module)
        if not plugin_class:
            continue
        if plugin_name.startswith('msg'):
            msg_plugins.append(plugin_class)
        else:
            gen_plugins.append(plugin_class)
    return msg_plugins, gen_plugins


IMAGE_DIR = "IMAGE"
VIDEO_DIR = "VIDEO"
VOICE_DIR = "VOICE"
FILE_DIR = "FILE"
EMOTION_DIR = "EMOTION"
UNKNOW_XMLTYPE = "unknow_xml"


def wait(timeout:int, func:Callable, *args, interval = 10):
    '''timeout: 毫秒'''
    while timeout > 0:
        ret = func(*args)
        if ret:
            return ret
        timeout -= interval
        time.sleep(interval/1000)


class DealMsgThread(Thread):
    def __init__(self, wxfunction:ModuleType,  event:Event, **kwargs):
        super().__init__()
        self.wxfunction = wxfunction
        self.event = event
        self.settings = kwargs
        
        self.wxid = wxfunction.getSelfWxid()
        self.img_decode = WechatImageDecoder()
        
        self.contact_list = list(self.wxfunction.GetContactList())
        self.contacts_wxh = {i["wxid"]:i.get('微信号') for i in self.contact_list}
        self._room_nicknames = {}
        self._friend_nicknames = {}
        
        self.wx_file_path = wxfunction.getWeChatFilePath().strip('\\').rsplit('\\', 1)[0] + '\\'
        # 需放到最后运行，因为要等待其他成员初始化完成
        msg_plugins = kwargs.get("msg_plugins", [])
        self.plugin_objs = self.init_plugins_instance(msg_plugins)

    def run(self):
        while self.event.is_set():
            msg = self.wxfunction.popFromMsgQueue()
            if not msg:
                time.sleep(0.5)
                continue
            msg_data = json.loads(msg)
            self.get_room_sender_nickname(msg_data)
            msg_data["sender_nickname"] = self.get_sender_name(msg_data["sender"])
            msg_struct = ChatMsgStruct(**msg_data)
            if not msg_struct.localid and msg_struct.msgid:
                localid_data = dict(self.wxfunction.getLocalidByMsgid(str(msg_struct.msgid)))
                localid = localid_data.get("localid", "")
                if localid.isdigit():
                    msg_struct.localid = int(localid)
            if not msg_struct.msgid and msg_struct.localid:
                dbindex = self.wxfunction.getMaxDbindex()
                msg_struct.msgid = self.wxfunction.getMsgidByLocalid(msg_struct.localid, dbindex)
            self._deal_msg(msg_struct)
            self.run_in_plugins(msg_struct)
    
    def init_plugins_instance(self, msg_plugins:List[MsgPluginTemplate]) -> List[MsgPluginTemplate]:
        '''初始化所有消息处理的插件类'''
        plugin_objs = []
        for plugin_class in msg_plugins:
            try:
                obj = plugin_class(self.wxfunction, self)
            except NotConfigured:
                continue
            except:
                traceback.print_exc()
                continue
            plugin_objs.append(obj)
        return plugin_objs
    
    def run_in_plugins(self, msg_struct:ChatMsgStruct):
        '''运行所有插件的deal_msg方法'''
        for obj in self.plugin_objs:
            try:
                obj.deal_msg(msg_struct)
            except:
                traceback.print_exc()
    
    def get_room_sender_nickname(self, msg_data:dict):
        '''获取群成员昵称'''
        if not msg_data.get('room_sender'):
            msg_data["room_nickname"] = None
            return
        room_sender = msg_data["room_sender"]
        if self._room_nicknames.get(room_sender):
            room_nickname = self._room_nicknames[room_sender]
        else:
            room_nickname = self.wxfunction.GetChatRoomMemberNickname(msg_data["sender"], room_sender)
            if not room_nickname:
                json_info = self.wxfunction.GetUserInfoJsonByCache(room_sender)
                user_info = json.loads(json_info)
                room_nickname = user_info["nickname"]
            self._room_nicknames[room_sender] = room_nickname
        msg_data["room_nickname"] = room_nickname

    def get_sender_name(self, sender):
        sender_name = self._friend_nicknames.get(sender)
        if not sender_name:
            time.sleep(2)
            self.contact_list = list(self.wxfunction.GetContactList())
            self._friend_nicknames = {d["wxid"]:d.get('备注') or d.get("昵称") for d in self.contact_list}
            self._friend_nicknames["filehelper"] = "文件传输助手"
            sender_name = self._friend_nicknames.get(sender)
        if not sender_name:
            sender_name = sender
        return sender_name
    
    def _deal_img_msg(self, msg_struct:ChatMsgStruct):
        sender_name = msg_struct.sender_nickname
        room_nickname = msg_struct.room_nickname
        img_path = self.wx_file_path + msg_struct.file_path
        if room_nickname:
            print(f"收到图片消息, 群: {sender_name}[{msg_struct.sender}]，发送人: {room_nickname}[{msg_struct.room_sender}], 图片路径: ", img_path)
        else:
            print(f"收到图片消息, 发送人: {sender_name}[{msg_struct.sender}], 图片路径: ", img_path)
        
        wait(1000, lambda : os.path.exists(img_path))
        if not os.path.exists(img_path):
            print("图片未下载，开始主动下载")
            localid_data = dict(self.wxfunction.getLocalidByMsgid(str(msg_struct.msgid)))
            dbindex = int(localid_data.get("dbindex", self.wxfunction.getMaxDbindex()))
            self.wxfunction.DownloadImageFromCdnByLocalid(msg_struct.localid, dbindex)
        wait(10000, lambda : os.path.exists(img_path))
        if not os.path.exists(img_path):
            print("图片下载失败")
            return
        if self.settings.get("IS_SAVE_IMAGE"):
            print("下载成功，正在保存图片")
            save_path = f"{IMAGE_DIR}{os.sep}{sender_name}【{msg_struct.sender}】{os.sep}{msg_struct.msgid}.png"
            save_abspath = self.abspath(save_path)
            try:
                self.img_decode.decode_pc_dat(img_path, save_abspath)
            except:
                traceback.print_exc()

    def abspath(self, path):
        '''获取保存的路径，创建不存在的文件夹'''
        abs_path = os.path.join(self.settings["FILE_SAVE_PATH"], path)
        dir = os.path.dirname(abs_path)
        if not os.path.exists(dir):
            os.makedirs(dir, exist_ok=True)
        return os.path.abspath(abs_path)

    def copy_file(self, src, dst):
        '''复制文件'''
        src = os.path.abspath(src)
        dst = os.path.abspath(dst)
        if os.path.isdir(src):
            return
        if src[0] != dst[0]:
            shutil.copyfile(src, dst)
        else:
            # 如果在同一个分区的话，不拷贝文件。直接对文件做硬链接处理，避免空间浪费
            os.link(src, dst)
    
    def _deal_video_msg(self, msg_struct:ChatMsgStruct):
        sender_name = msg_struct.sender_nickname
        file_path = msg_struct.file_path
        if not file_path:
            file_path = msg_struct.thumb_path[:-4] + '.mp4'
        room_nickname = msg_struct.room_nickname
        path = self.wx_file_path + file_path
        if room_nickname:
            print(f"收到视频消息, 群: {sender_name}[{msg_struct.sender}]，发送人: {room_nickname}[{msg_struct.room_sender}], 视频路径: {path}")
        else:
            print(f"收到视频消息, 发送人: {sender_name}[{msg_struct.sender}], 视频路径: {path}")
        if msg_struct.is_self_msg:
            return
        wait(1000, lambda : os.path.exists(path))
        if not os.path.exists(path):
            print("视频未下载，开始主动下载")
            localid_data = dict(self.wxfunction.getLocalidByMsgid(str(msg_struct.msgid)))
            dbindex = int(localid_data.get("dbindex", self.wxfunction.getMaxDbindex()))
            self.wxfunction.DownloadVideoFromCdnByLocalid(msg_struct.localid, dbindex)
        wait(30000, lambda : os.path.exists(path))
        if not os.path.exists(path):
            print("视频下载失败")
            return
        if self.settings.get("IS_SAVE_FILE"):
            print("下载成功，正在保存视频")
            save_path = f"{VIDEO_DIR}{os.sep}{sender_name}【{msg_struct.sender}】{os.sep}{msg_struct.msgid}.mp4"
            save_abspath = self.abspath(save_path)
            self.copy_file(path, save_abspath)
    
    def _deal_file_msg(self, msg_struct:ChatMsgStruct):
        sender_name = msg_struct.sender_nickname
        file_path = msg_struct.file_path
        room_nickname = msg_struct.room_nickname
        path = self.wx_file_path + file_path
        if room_nickname:
            print(f"收到文件消息, 群: {sender_name}[{msg_struct.sender}]，发送人: {room_nickname}[{msg_struct.room_sender}], 文件路径: {path}")
        else:
            print(f"收到文件消息, 发送人: {sender_name}[{msg_struct.sender}], 文件路径: {path}")
        if msg_struct.is_self_msg:
            return
        wait(1000, lambda : os.path.exists(path))
        if not os.path.exists(path):
            print("文件未下载，开始主动下载")
            localid_data = dict(self.wxfunction.getLocalidByMsgid(str(msg_struct.msgid)))
            dbindex = int(localid_data.get("dbindex", self.wxfunction.getMaxDbindex()))
            self.wxfunction.DownloadFileFromCdnByLocalid(msg_struct.localid, dbindex)
        wait(30000, lambda : os.path.exists(path))
        if not os.path.exists(path):
            print("文件下载失败")
            return
        # 取消文件只读属性，因为微信会默认设置文件只读
        os.chmod(path, stat.S_IWRITE)
        if self.settings.get("IS_SAVE_FILE"):
            print("下载成功，正在保存文件")
            filename = os.path.basename(path)
            save_path = f"{FILE_DIR}{os.sep}{sender_name}【{msg_struct.sender}】{os.sep}{filename}"
            save_abspath = self.abspath(save_path)
            self.copy_file(path, save_abspath)
    
    def _deal_voice_msg(self, msg_struct:ChatMsgStruct):
        sender_name = msg_struct.sender_nickname
        room_nickname = msg_struct.room_nickname
        if room_nickname:
            print(f"收到语音消息, 群: {sender_name}[{msg_struct.sender}]，发送人: {room_nickname}[{msg_struct.room_sender}], msgid: {msg_struct.msgid}")
        else:
            print(f"收到语音消息, 发送人: {sender_name}[{msg_struct.sender}], msgid: {msg_struct.msgid}")
        if msg_struct.is_self_msg:
            return
        hexVoice = wait(5000, lambda : self.wxfunction.getVoiceByMsgid(str(msg_struct.msgid)), interval=200)
        if hexVoice:
            bytesVoice = bytes.fromhex(hexVoice)
            save_path = f"{VOICE_DIR}{os.sep}{sender_name}【{msg_struct.sender}】{os.sep}{msg_struct.msgid}.slik"
            save_abspath = self.abspath(save_path)
            with open(save_abspath, 'wb') as f:
                f.write(bytesVoice)
        else:
            print("语音保存失败！")
    
    def _deal_addfriend_msg(self, msg_struct:ChatMsgStruct):
        xml = msg_struct.content
        root = ET.fromstring(xml) 
        datas = dict(root.items())
        print(f"收到好友({datas['fromnickname']})请求。")
        # 只同意24个小时内的请求
        if self.settings["AUTO_AGREE_FRIEND_REQ"] and msg_struct.timestamp > int(time.time())-60*60*24:
            print("已开启自动同意好友请求，等待五秒后自动同意!")
            v3 = datas["encryptusername"]
            v4 = datas["ticket"]
            addType = datas["scene"]
            time.sleep(5)
            self.wxfunction.AddFriendByV3V4(v3, v4, addType)
    
    def _deal_card_msg(self, msg_struct:ChatMsgStruct):
        xml = msg_struct.content
        root = ET.fromstring(xml) 
        datas = dict(root.items())
        print("收到名片请求: ", datas)

    def _deal_emotion_msg(self, msg_struct:ChatMsgStruct):
        sender_name = msg_struct.sender_nickname
        room_nickname = msg_struct.room_nickname
        if room_nickname:
            print(f"收到表情消息, 群: {sender_name}[{msg_struct.sender}]，发送人: {room_nickname}[{msg_struct.room_sender}], 文件名: {msg_struct.file_path}")
        else:
            print(f"收到表情消息, 发送人: {sender_name}[{msg_struct.sender}], 文件名: {msg_struct.file_path}")
        if msg_struct.is_self_msg:
            return
        xml = msg_struct.content
        root = ET.fromstring(xml) 
        datas = dict(root.find('.//emoji').items())
        cdnurl = datas["cdnurl"].replace('&amp;', '&')
        filename = msg_struct.file_path
        if not filename:
            filename = msg_struct.msgid
        save_path = f"{EMOTION_DIR}{os.sep}{filename}.gif"
        save_abspath = self.abspath(save_path)
        with open(save_abspath, 'wb') as f:
            f.write(self.download_file(cdnurl))
    
    def _deal_location_msg(self, msg_struct:ChatMsgStruct):
        sender_name = msg_struct.sender_nickname
        xml = msg_struct.content
        
        root = ET.fromstring(xml) 
        datas = dict(root.find('.//location').items())
        room_nickname = msg_struct.room_nickname
        if room_nickname:
            print(f"收到位置消息, 群: {sender_name}[{msg_struct.sender}]，发送人: {room_nickname}[{msg_struct.room_sender}], 位置: {datas}")
        else:
            print(f"收到位置消息, 发送人: {sender_name}[{msg_struct.sender}], 位置: {datas}")
    
    def download_file(self, url, retry=0):
        if retry > 2:
            return
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=6)
        except:
            traceback.print_exc()
            time.sleep(2)
            return self.download_file(url, retry+1)
        return resp.content
    
    def _deal_notice_msg(self, msg_struct:ChatMsgStruct):
        sender_name = msg_struct.sender_nickname
        room_nickname = msg_struct.room_nickname
        if room_nickname:
            print(f"收到通知类消息, 群: {sender_name}[{msg_struct.sender}]，发送人: {room_nickname}[{msg_struct.room_sender}], 消息内容: {msg_struct.content}")
        else:
            print(f"收到通知类消息, 发送人: {sender_name}[{msg_struct.sender}], 消息内容: {msg_struct.content}")
    
    def _deal_text_msg(self, msg_struct:ChatMsgStruct):
        sender_name = msg_struct.sender_nickname
        room_nickname = msg_struct.room_nickname
        if room_nickname:
            print(f"收到文本消息, 群: {sender_name}[{msg_struct.sender}]，发送人: {room_nickname}[{msg_struct.room_sender}], 消息内容: {msg_struct.content}")
        else:
            print(f"收到文本消息, 发送人: {sender_name}[{msg_struct.sender}], 消息内容: {msg_struct.content}")
    
    def _deal_msg(self, msg_struct:ChatMsgStruct):
        msg_type = msg_struct.msg_type
        if msg_type == MsgType.TEXT:
            self._deal_text_msg(msg_struct)
        elif msg_type == MsgType.IMAGE:
            self._deal_img_msg(msg_struct)
        elif msg_type == MsgType.VIDEO:
            self._deal_video_msg(msg_struct)
        elif msg_type == MsgType.VOICE:
            self._deal_voice_msg(msg_struct)
        elif msg_type == MsgType.ADDFRIEND:
            self._deal_addfriend_msg(msg_struct)
        elif msg_type == MsgType.CARD:
            self._deal_card_msg(msg_struct)
        elif msg_type == MsgType.EMOTION:
            self._deal_emotion_msg(msg_struct)
        elif msg_type == MsgType.LOCATION:
            self._deal_location_msg(msg_struct)
        elif msg_type == MsgType.XML:
            self.parse_xml(msg_struct)
        elif msg_type == MsgType.VOIP:
            pass
        elif msg_type == MsgType.NOTICE:
            self._deal_notice_msg(msg_struct)
        elif msg_type == MsgType.SYSMSG:
            self._deal_sysmsg_msg(msg_struct)
        else:
            save_path = f"{UNKNOW_XMLTYPE}{os.sep}msg_{msg_type}.txt"
            save_abspath = self.abspath(save_path)
            with open(save_abspath, 'w', encoding='utf-8') as f:
                f.write(msg_struct.to_json())
            print("未知的消息类型，msg_type: ", msg_type, msg_struct.content)
    
    def _deal_refer_msg(self, msg_struct:ChatMsgStruct):
        sender_name = msg_struct.sender_nickname
        xml = msg_struct.content
        root = ET.fromstring(xml) 
        room_nickname = msg_struct.room_nickname
        content = root.find('.//appmsg/title').text
        refermsg = root.find('.//refermsg')
        refer_type = refermsg.find('.//type').text
        # fromusr = refermsg.find('.//fromusr').text
        # chatusr = refermsg.find('.//chatusr').text
        # displayname = refermsg.find('.//displayname').text
        if refer_type == "1":
            refer_content = refermsg.find('.//content').text
        else:
            refer_content = self.get_msg_type_text(refer_type)
        if room_nickname:
            print(f"收到引用回复消息, 群: {sender_name}[{msg_struct.sender}]，发送人: {room_nickname}[{msg_struct.room_sender}], 引用内容: {refer_content.strip()}, 消息内容: {content}")
        else:
            print(f"收到引用回复消息, 发送人: {sender_name}[{msg_struct.sender}], 引用内容: {refer_content} =》 消息内容: {content}")
    
    def parse_xml(self, msg_struct:ChatMsgStruct):
        sender_name = msg_struct.sender_nickname
        _type = self.get_xml_type(msg_struct.content)
        if _type == XmlMsgType.FILE: # 文件
            self._deal_file_msg(msg_struct)
        elif _type == XmlMsgType.BIZMSG: # 链接
            pass
        elif _type == XmlMsgType.SHARE_LOCATION:
            print(f'[{sender_name}]发起了位置共享')
        elif _type == XmlMsgType.MULTI_MSG:
            print("收到合并转发的聊天记录!")
        elif _type == XmlMsgType.STEP_RANK_MSG:
            print("收到微信运动步数信息!")
        elif _type == XmlMsgType.APPMSG:
            print("收到分享的小程序!")
        elif _type == XmlMsgType.REFERENCE_MSG:
            self._deal_refer_msg(msg_struct)
        elif _type == XmlMsgType.ROOM_ANNOUNCEMENT:
            print(f'{sender_name}[{msg_struct.sender}] 发送了一个群公告')
        elif _type == XmlMsgType.TRANSFER: # 转账
            self._deal_transfer_msg(msg_struct)
        else:
            print(f"收到未知的xml类型， type: {_type} !")
            save_path = f"{UNKNOW_XMLTYPE}{os.sep}xml_{_type}.txt"
            save_abspath = self.abspath(save_path)
            with open(save_abspath, 'w', encoding='utf-8') as f:
                f.write(msg_struct.to_json())

    def _deal_transfer_msg(self, msg_struct:ChatMsgStruct):
        sender_name = msg_struct.sender_nickname
        xml = msg_struct.content
        root = ET.fromstring(xml) 
        paysubtype = root.find('.//paysubtype').text
        amount = root.find('.//feedesc').text
        transcationid = root.find('.//transcationid').text
        transferid = root.find('.//transferid').text
        invalidtime = root.find('.//invalidtime').text
        begintransfertime = root.find('.//begintransfertime').text
        if paysubtype == 1:
            print(f"收到转账消息: 发送人: {sender_name}[{msg_struct.sender}], 金额: {amount}")
            if self.settings["AUTO_RECV_TRANSFER"] and msg_struct.timestamp > int(time.time())-60*60*24:
                time.sleep(5)
                self.wxfunction.RecvTransfer(msg_struct.sender, transferid, transcationid)
        else:
            print(f"接收转账消息: 发送人: {sender_name}[{msg_struct.sender}], 金额: {amount}")
    
    def get_msg_type_text(self, _type:str):
        if not _type:
            return ""
        for type_text in dir(MsgType):
            if type_text.startswith('__'):
                continue
            if str(getattr(MsgType, type_text, "")) == _type:
                return type_text

    def _deal_revoke_msg(self, msg_struct:ChatMsgStruct):
        root = ET.fromstring(msg_struct.content) 
        replacemsg = root.find('.//replacemsg').text
        newmsgid = root.find('.//newmsgid').text
        sender_name = msg_struct.sender_nickname
        room_nickname = msg_struct.room_nickname
        msg = self.wxfunction.getMsgByMsgid(str(newmsgid))
        msg = dict(msg) if msg else {}
        if msg.get("Type") == "1":
            content = msg.get("StrContent")
        else:
            content = self.get_msg_type_text(msg.get("Type"))
        if room_nickname:
            print(f"群: {sender_name}[{msg_struct.sender}]，{room_nickname}[{msg_struct.room_sender}] 撤回了一条消息, 消息内容: {content}")
        else:
            print(f"{sender_name}[{msg_struct.sender}] 撤回了一条消息, 消息内容: {content}")
        
    
    def _deal_sysmsg_msg(self, msg_struct:ChatMsgStruct):
        sender_name = msg_struct.sender_nickname
        xml = msg_struct.content
        root = ET.fromstring(xml) 
        _type = dict(root.items()).get('type')
        if _type == SysMsgType.revokemsg:
            self._deal_revoke_msg(msg_struct)
        elif _type == SysMsgType.bizlivenotify: # 公众号直播提醒
            pass
        elif _type == SysMsgType.secmsg: # 群消息相关的，没看出来是什么消息
            pass
        elif _type == SysMsgType.modtextstatus: # 个人消息相关的，没看出来是什么消息
            pass
        elif _type == SysMsgType.uploadfinishmsg: # 文件上传完成，比如某人给你发了个大文件。只有收到这个消息时才能下载。里面有消息msgid
            pass 
        elif _type == SysMsgType.gamecenter: # 游戏广告，没找到界面显示在哪
            pass
        elif _type == SysMsgType.pat: # 已经在通知类型消息处理了，这里就忽略了
            pass
        elif _type == SysMsgType.mmchatroombarannouncememt: # 群公告, 已经在xml消息里处理
            pass
        elif _type == SysMsgType.functionmsg: # 这个不知道, 感觉像微信内部的逻辑
            pass
        elif _type == SysMsgType.delchatroommember: # 群成员变动，删除或邀请
            pass
        else:
            print("收到系统类消息:", msg_struct.sender, msg_struct.content)
    
    def get_xml_type(self, xml):
        root = ET.fromstring(xml) 
        _type = root.find('.//type').text
        return int(_type)
