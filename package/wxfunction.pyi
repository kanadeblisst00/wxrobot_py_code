from typing import Union, List


def GetUsers() -> List[dict]: ...

def GetContactList() -> List[list]: ...

def popFromMsgQueue() -> Union[str, None]: ...

def getMsgQueueSize() -> int: ...

def SendTextMsg(wxid:str, text:str) -> int: ...

def SendXmlMsg(wxid:str, xml:str, dtype:int) -> int: ...

def SendEmotionMsg(wxid:str, path:str) -> int: ...

def SendCardMsg(wxid:str, xml:str) -> int: ...

def SendPatMsg(roomid:str, wxid:str) -> int: ...

def SendImageMsg(wxid:str, path:str) -> int: ...

def SendFileMsg(wxid:str, path:str) -> int: ...

def SendAppMsg(wxid:str, gappid:str) -> int: ...

def ForwardMessage(wxid:str, localid:int) -> int: ...

def EditRemark(wxid:str, remark:str) -> int: ...

def GetChatRoomMembers(roomid:str) -> str: ...

def GetChatRoomMemberNickname(roomid:str, wxid:str) -> str: ...

def DelChatRoomMembers(roomid:str, wxid:str) -> int: ...

def SetChatRoomAnnouncement(roomid:str, content:str) -> int: ...

def SetChatRoomName(roomid:str, name:str) -> int: ...

def SetChatRoomMyNickname(roomid:str, name:str) -> int: ...

def AddChatRoomMembers(roomid:str, wxid:str) -> int: ...

def DownloadFileFromCdn(content:str, file_path:str) -> int: ...

def AddFriendByV3V4(v3:str, v4:str, addType:int) -> int: ...

def AddFriendByWxidOrV3(wxid:str, message:str, addType:int) -> int: ...

def ExecuteSql(dbname:str, sql:str) -> str: ...

def CheckFriendStatus(wxid:str) -> dict: ...

def SearchFriend(phone:str) -> dict: ...

def DownloadImageFromCdnByLocalid(localid:int,dbindex:int, file_path:str) -> int: ...

def DownloadFileFromCdnByLocalid(localid:int,dbindex:int, file_path:str) -> int: ...

def DownloadVideoFromCdnByLocalid(localid:int,dbindex:int, file_path:str) -> int: ...

def getVoiceByMsgid(msgid:str) -> str: ...

def RecvTransfer(wxid:str, transferid:str, transcationid:str) -> int: ...

def getMsgByMsgid(msgid:str) -> dict: ...

def getMaxDbindex() -> int: ...