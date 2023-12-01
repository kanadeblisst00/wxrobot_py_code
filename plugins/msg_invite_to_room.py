import xml.etree.ElementTree as ET 
from . import MsgPluginTemplate, DealMsgThread, ChatMsgStruct, MsgType
from . import settings, NotConfigured


class AutoInviteToRoom(MsgPluginTemplate):
    def __init__(self, wxfunction, dtObj:DealMsgThread) -> None:
        super().__init__(wxfunction, dtObj)
        if not getattr(settings, "INVITE_TO_ROOM_KEYWORDS", None):
            raise NotConfigured
        print(f"插件[{self._name(__file__)}]加载成功")
        self.keywords = getattr(settings, "INVITE_TO_ROOM_KEYWORDS")
        
    def deal_msg(self, msg_struct:ChatMsgStruct):
        text = ""
        wxid = None
        if msg_struct.msg_type == MsgType.ADDFRIEND:
            xml = msg_struct.content
            root = ET.fromstring(xml) 
            datas = dict(root.items())
            text = datas["content"]
            wxid = datas["fromusername"]
        elif msg_struct.msg_type == MsgType.TEXT:
            content = msg_struct.content
            if "@chatroom" not in msg_struct.sender:
                text = content
                wxid = msg_struct.sender
        roomid = self.match_keyword(text)
        if roomid and wxid:
            
            self.invite_member(roomid, wxid)
    
    def match_keyword(self, s:str):
        if not s:
            return
        for keyword, room_name in self.keywords.items():
            if keyword in s:
                roomid = self.get_roomid_by_name(room_name)
                print(f"匹配到关键词({keyword})，群名称: {room_name}, 群id: {roomid}")
                return roomid
    
    def get_roomid_by_name(self, name:str):
        if not name:
            return
        for contact in self.dtObj.contact_list:
            if contact.get('备注') == name or contact.get("昵称") == name:
                return contact["wxid"]
    
    def invite_member(self, roomid, wxid):
        room_member_count = self.wxfunction.GetChatRoomMembers(roomid).count("^G") + 1
        if room_member_count < 35:
            # 邀请群成员，无需对方同意
            self.wxfunction.AddChatRoomMembers(roomid, wxid)
        else:
            # 发送群成员邀请
            self.wxfunction.InviteChatRoomMembers(roomid, wxid)

