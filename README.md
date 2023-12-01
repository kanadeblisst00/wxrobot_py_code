## 代码介绍

#### 简介
`wxrobot.exe`启动的时候会执行py_code目录下的main.py，类似于你在命令行使用`python main.py`，不同的是`wxrobot.exe`会导出一个库(wxfunction)接口给Python使用，这个库包含一些微信的功能，具体请看所有功能一栏。

执行main.py的时候会加载当前目录下的plugins目录里的py脚本作为插件运行，默认会忽略掉以_开头的脚本，已经内置了部分插件，你也可以根据需要写自己的插件。

插件脚本分为两类: 
1. 消息插件脚本，当收到消息时触发，文件名以msg开头的py文件
2. 其他插件脚本，执行main.py时就会运行

默认所有其他插件脚本都在同一个线程内运行，如果需要多线程，请在脚本里继承一下threading.Thread, 可以参考check_friend.py插件的写法

#### 已有插件
- 检测所有好友状态(拉黑、删除等): check_friend.py
- 定时发送消息: send_msg_timing.py
- 自动回复: msg_auto_reply.py
- 监控群消息，触发关键词预警: msg_monitor_keyword.py
- 推送消息到接口: msg_post_api.py
- 保存聊天记录到sqlite: msg_save_to_sqlite.py
- 保存聊天记录到postgresql: msg_save_to_postgre.py
- 加好友或关键词自动邀请进群: msg_invite_to_room.py
- 查询历史消息: save_history_msg.py
- 群机器人管理(待开发): msg_room_manager.py

另外一些功能没有写在插件里，而是集成到消息处理里面：
- 消息防撤回
- 自动下载文件、图片和视频
- 自动同意好友请求
- 自动接收转账
- 图片自动解密
- 自动保存表情并解密

#### 发消息例子
举个例子，如果想每隔五分钟发一次消息，代码可以参考`send_msg_timing.py`
```python
from threading import Timer

def sendmsg(interval):
    '''每隔interval秒给文件传输助手发一次消息, filehelper是文件传输助手的wxid'''
    wxfunction.SendTextMsg("filehelper", "测试消息！")
    timer = Timer(interval, sendmsg, args=(interval,))
    timer.start()

sendmsg(5*60)
```

SendTextMsg就是`wxrobot.exe`导出的发送文本消息的函数，第一个参数是wxid，这是微信内部使用的唯一id，每个微信号都有对应的wxid，可以通过获取好友列表来获取，第二个参数是发送的消息内容

#### 接收消息例子
收到的消息处理，比如你想收到某人的回复，然后给他发一个消息，就像对接机器人一样的操作方式, 代码可以参考`msg_auto_reply.py`，其中的主要函数如下
```python
def deal_msg(self, msg_struct:ChatMsgStruct):
    # 判断是否是自己发的或手机同步的消息
    # 判断消息是否是通知和系统类消息
    if msg_struct.is_self_msg or msg_struct.msg_type in (MsgType.NOTICE, MsgType.SYSMSG):
        return
    # 15分钟前的消息不回复
    if msg_struct.timestamp < int(time.time())-15*60:
        return 
    # 判断是否是配置的好友
    if self.is_target_friend(msg_struct):
        wxfunction.SendTextMsg(sender, "自动回复")
```
`msg_auto_reply.py`插件可以自定义回复的内容，在`auto_reply.txt`里配置，每行一个，发送时随机一个。

## 所有功能
#### 接收消息
- 好友消息
- 群消息
- 通知类消息(成员进群通知等)
- 公众号推送(可以用来监控公众号的发文)
- 公众号消息(公众号发送的消息)
- 好友请求
- 撤回提示消息
- 群公告
- 转账消息
- 收款消息(可以写一个自动发卡的)
- 关注的公众号直播提醒
- 大文件上传完成提示
- 更多消息自己发现
- 有遗漏的消息类型也可以提出来

#### 发消息
- 发送文本
- 发送群@消息
- 发送图片
- 发送文件
- 发送表情
- 发送名片
- 发送xml消息
- 发送拍一拍
- 发送小程序
- 转发消息
- 发送引用消息
- 撤回消息

#### 防撤回

程序会收到撤回消息提示，界面并不会显示

- 已内置(打开软件，默认开启，无法关闭)，

#### 群相关

- 获取群成员
- 获取群成员昵称
- 删除群成员
- 设置群公告
- 修改群名称
- 修改自己的群昵称
- 邀请好友进群
- 发送群邀请(群人数大于40)

#### 加好友

- 同意好友请求(案例Python代码可配置自动同意)
- 检测好友状态(正常、删除、拉黑等)
- 搜索好友(可通过手机号或微信号搜索)
- 添加好友

#### 转账收款

- 接收转账和退还转账（案例Python代码可配置自动接收）

#### 其他

- 修改好友备注
- 获取好友详细信息
- 获取好友列表
- 获取wxid的相关信息
- 获取语音转文字的结果(需开启自动语音转文字)

#### CDN下载

- 下载图片
- 下载视频
- 下载文件
- 下载语音
- 下载表情包

## 操作步骤

##### 准备工作
1. 安装给定版本(3.9.6.32)的微信到任意目录
2. 安装给定的python-3.8.10.exe到任意目录, 不懂的话，安装选项可以一直默认
3. 编辑配置文件，主要修改微信安装目录和Python安装目录
4. 打开wxrobot.exe软件，点击软件界面的-》帮助-》启动微信，登录即可(如果出现监听不到消息的情况，需要以管理员权限运行微信，在运行软件)

**提示1: Python版本并不需要是给定的3.8.10，更新的版本应该都能用，但必须是32位的Python**
**提示2: 不一定要使用软件启动微信，也可以自己点击快捷方式启动，但是软件和微信都需要以管理员方式运行，如果不是，会无法正常拦截消息**

打开软件之后，可以在文件传输助手发送消息测试下能不能正常拦截到。

## 函数介绍
#### getSelfWxid
函数原型: `def getSelfWxid() -> str: ...`
功能: 获取自己登录的微信的wxid

#### getWeChatFilePath
函数原型: `def getWeChatFilePath() -> str: ...`
功能: 获取微信文件的保存路径（微信设置文件管理里的微信文件的默认保存路径）

#### GetUsers
函数原型: `def GetUsers() -> List[dict]: ...`
功能: 获取当前已登录的wxid、微信号和昵称

#### GetContactList
函数原型: `def GetContactList() -> List[list]: ...`
功能: 获取好友和群列表

#### popFromMsgQueue
函数原型: `def popFromMsgQueue() -> Union[str, None]: ...`
功能: 从已接收到的消息队列里弹出一条消息，消息类型为json字符串

#### SendTextMsg
函数原型: `def SendTextMsg(wxid:str, text:str) -> int: ...`
功能: 发送文本消息
参数：
1. wxid: 对方的wxid
2. text: 发送的文本内容

#### SendXmlMsg
函数原型: `def SendXmlMsg(wxid:str, xml:str, dtype:int) -> int: ...`
功能: 发送xml消息，接受消息类型为49，应该都可以把xml拿下来重新发出去。只测试了发送公众号文章
参数：
1. wxid: 对方的wxid
2. xml: 发送的xml内容
3. dtype: xml里面的类型，可以从xml里解析出来

#### SendEmotionMsg
函数原型: `def SendEmotionMsg(wxid:str, path:str) -> int: ...`
功能: 发送表情包
参数：
1. wxid: 对方的wxid
2. path: 表情包的绝对路径，可以是未加密的表情包、也可以是 FileStorage\\CustomEmotion下的加密表情

#### SendCardMsg
函数原型: `def SendCardMsg(wxid:str, xml:str) -> int: ...`
功能: 发送某个好友的名片， 也可以使用下面那个函数，可以直接通过好友wxid发送
参数：
1. wxid: 对方的wxid
2. xml: 名片的xml数据，可以先发送一个出去，然后在接受消息里打印出来就能看到

#### SendCardMsgByWxid
函数原型: `def SendCardMsg(wxid:str, cardWxid:str) -> int: ...`
功能: 发送某个好友的名片
参数：
1. wxid: 对方的wxid
2. cardWxid: 需要发送的好友wxid

#### SendPatMsg
函数原型: `def SendPatMsg(roomid:str, wxid:str) -> int: ...`
功能: 发送拍一拍消息
参数：
1. roomid: 群id
2. wxid: 拍的人的wxid

#### SendImageMsg
函数原型: `def SendImageMsg(wxid:str, path:str) -> int: ...`
功能: 发送图片
参数：
1. wxid: ...
2. path: 发送的图片绝对路径

#### SendFileMsg
函数原型: `def SendFileMsg(wxid:str, path:str) -> int: ...`
功能: 发送文件
参数：
1. wxid: ...
2. path: 发送的文件绝对路径

#### SendAppMsg
函数原型: `def SendAppMsg(wxid:str, gappid:str) -> int: ...`
功能: 发送小程序消息
参数：
1. wxid: ...
2. gappid: 类似gh_xxxxxxxx@app这样的id, 可以转发一个小程序，里面的xml就有

#### ForwardMessage
函数原型: `def ForwardMessage(wxid:str, localid:int) -> int: ...`
功能: 转发消息
参数：
1. wxid: ...
2. localid: 消息里面的localid字段

#### EditRemark
函数原型: `def EditRemark(wxid:str, remark:str) -> int: ...`
功能: 编辑好友备注
参数：
1. wxid: ...
2. remark: 备注内容

#### RecvTransfer
函数原型: `def RecvTransfer(wxid:str, transferid:str, transcationid:str) -> int: ...`
功能: 接收转账
参数：
1. wxid: ...
2. transferid: 转账消息的xml里可以提取到
3. transcationid: 转账消息的xml里可以提取到

#### RefundTransfer
函数原型: `def RefundTransfer(wxid:str, transferid:str, transcationid:str) -> int: ...`
功能: 退还转账
参数：
1. wxid: ...
2. transferid: 转账消息的xml里可以提取到
3. transcationid: 转账消息的xml里可以提取到

#### GetChatRoomMembers
函数原型: `def GetChatRoomMembers(roomid:str) -> str: ...`
功能: 获取某个群的所有群成员
参数：
1. roomid: 群id

#### GetChatRoomMemberNickname
函数原型: `def GetChatRoomMemberNickname(roomid:str, wxid:str) -> str: ...`
功能: 获取群成员昵称
参数：
1. roomid: 群id
2. wxid: 要获取昵称的wxid

#### GetUserInfoJsonByCache
函数原型: `def GetUserInfoJsonByCache(wxid:str) -> str: ...`
功能: 获取某个用户的昵称, 可以是好友或者群成员
参数：
1. wxid: 要获取昵称的wxid

#### DelChatRoomMembers
函数原型: `def DelChatRoomMembers(roomid:str, wxid:str) -> int: ...`
功能: 删除群成员
参数：
1. roomid: 群id
2. wxid: 要删除的那个人的wxid

#### SetChatRoomAnnouncement
函数原型: `def SetChatRoomAnnouncement(roomid:str, content:str) -> int: ...`
功能: 设置群公告
参数：
1. roomid: 群id
2. content: 公告内容，仅支持文本内容

#### SetChatRoomName
函数原型: `def SetChatRoomName(roomid:str, name:str) -> int: ...`
功能: 修改群名称
参数：
1. roomid: 群id
2. name: 名称

#### SetChatRoomMyNickname
函数原型: `def SetChatRoomMyNickname(roomid:str, name:str) -> int: ...`
功能: 修改自己的群昵称
参数：
1. roomid: 群id
2. name: 名称

#### AddChatRoomMembers
函数原型: `def AddChatRoomMembers(roomid:str, wxid:str) -> int: ...`
功能: 邀请好友进程，该接口仅支持40人以下的群
参数：
1. roomid: 群id
2. wxid: 好友的wxid

#### DownloadImageFromCdnByLocalid
函数原型: `def DownloadImageFromCdnByLocalid(localid:int, file_path:str) -> int: ...`
功能: 下载某个图片消息的图片到指定路径下
参数：
1. localid: 消息的localid
2. file_path: 路径一般是微信的目录，然后解密拷贝出来。具体见Python示例

#### DownloadFileFromCdnByLocalid
函数原型: `def DownloadFileFromCdnByLocalid(localid:int, file_path:str) -> int: ...`
功能: 下载某个文件消息到指定路径下
参数：
1. localid: 消息的localid
2. file_path: 路径一般是微信的目录，然后拷贝出来。具体见Python示例

#### DownloadVideoFromCdnByLocalid
函数原型: `def DownloadVideoFromCdnByLocalid(localid:int, file_path:str) -> int: ...`
功能: 下载某个视频消息到指定路径下
参数：
1. localid: 消息的localid
2. file_path: 路径一般是微信的目录，然后拷贝出来。具体见Python示例

#### AddFriendByWxidOrV3
函数原型: `def AddFriendByV3V4(v3:str, v4:str, addType:int) -> int: ...`
功能: 同意还有请求，v3、v4和addType都在好友请求的消息xml里，具体字段见Python示例
参数：
1. v3: ...
2. v4: ...
3. addType: 添加的类型，比如通过wxid添加就是6，通过名片添加的就是17，

#### getVoiceByMsgid
函数原型: `def getVoiceByMsgid(msgid:str) -> str: ...`
功能: 通过msgid获取语音文件，获取的格式是slik，需要转常见的音频格式比如mp3才能播放
参数：
1. msgid: 音频消息中的msgid

#### CheckFriendStatus
函数原型: `def CheckFriendStatus(wxid:str) -> dict: ...`
功能: 检测好友状态，拉黑、删除等，可以用来做僵尸粉检测，建议调用增加间隔时间。可能会出现添加好友的提示，属于正常现象，对方看不到
参数：
1. wxid: ...

#### SearchFriend
函数原型: `def SearchFriend(phone:str) -> dict: ...`
功能: 通过微信号或者手机号搜索用户
参数：
1. phone: 要搜索的微信号或手机号