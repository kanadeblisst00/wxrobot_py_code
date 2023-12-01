import os
import time


EXE_PATH = os.path.abspath('..')
PY_CODE_PATH = os.path.abspath(os.path.dirname(__file__)) 


# [deal_msg.py]
# 保存图片、文件、视频的路径。当前目录是main.py所在目录。..是指上级目录，也就是exe所在目录
FILE_SAVE_PATH = os.path.join(EXE_PATH, "WECHAT_FILES")
# 设置是否保存到FILE_SAVE_PATH，文件始终会主动下载到Wechat files目录下
IS_SAVE_FILE = False
# 是否单独保存图片，表情包和语音默认就是下载，没有提供设置
IS_SAVE_IMAGE = True
# 自动同意好友请求
AUTO_AGREE_FRIEND_REQ = True
# 自动接收转账
AUTO_RECV_TRANSFER = True

# [msg_save_to_postgre.py]
# 保存到postgre数据库配置
POSTGRE_DB = {
    "user" : "kanadeblisst",
    "password" :"123456",
    "host" : "127.0.0.1",
    "port" : "1234",
    "database": "wechat",
    "db_table": "wechat_msg"
}

# [send_msg_timing.py]
# 启动send_msg_timing插件每隔一段时间发送消息
# 请按照需求修改send_msg_timing
ENABLE_AUTO_SEND_MSG = False

# [msg_auto_reply.py]
# 触发自动回复的好友微信号列表
AUTO_REPLY_FRIEND = []
# 自动回复的文件路径，每行一句话
AUTO_REPLY_MSG_FILEPATH = os.path.join(PY_CODE_PATH, "file", "auto_reply.txt")

# [msg_monitor_keyword.py]
# 是否开启关键词监控
IS_MONITOR_KEYWORDS = True
# 同时支持两种。监控关键词模式，有默认default和正则re
MONITOR_KEYWORDS_MODE = "default"
# 默认支持三种语法
DEFAULT_MONITOR_KEYWORDS_FILEPATH = os.path.join(PY_CODE_PATH, "file", "monitor_keyword.txt")
# 正则
RE_MONITOR_KEYWORDS_FILEPATH = os.path.join(PY_CODE_PATH, "file", "re_monitor_keyword.txt")
# 当出现关键词时，给该好友发送预警消息
SEND_REMIND_WXH = "kanadeblisst"


# [check_friend.py]
# 是否开启好友检测
IS_CHECK_FRIEND = False


# [msg_save_to_sqlite.py]
# sqlite数据库路径
# SQLITE_DB = {
#     "database": os.path.join(EXE_PATH, "msg0.db"),
#     "timeout": 5,
#     "db_table": "MSG"
# }

# [msg_invite_to_room.py]
# 自动根据好友请求的关键词邀请进群
INVITE_TO_ROOM_KEYWORDS = {
    # keyword: 群名称
    "进群": "Python自动化交流"
}

#[save_history_msg.py]
# 读取的信息需要运行的插件
RUN_PLUGINS_SETTINGS = ("POSTGRE_DB", )
# 从数据库查询之前到现在的消息, 
SAVE_HISTORY_MSG_TIMESTAMP = int(time.time()) - 60*60*2
# SAVE_HISTORY_MSG_TIMESTAMP = int(time.mktime(time.strptime("2020-11-30 00:00:00", "%Y-%m-%d %H:%M:%S")))
