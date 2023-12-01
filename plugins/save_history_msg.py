import time
import json
import traceback
from . import DealMsgThread, ChatMsgStruct, MsgType
from . import load_plugins, load_settings
from . import settings, NotConfigured


DEFAULT_RUN_PLUGINS = ("EXE_PATH", "FILE_SAVE_PATH", "IS_SAVE_FILE", "IS_SAVE_IMAGE", )


class SaveHistoryMsg(DealMsgThread):
    def __init__(self, wxfunction) -> None:
        if not getattr(settings, "SAVE_HISTORY_MSG_TIMESTAMP", None):
            raise NotConfigured
        msg_plugins, _ = load_plugins()
        run_plugin_settings = getattr(settings, "RUN_PLUGINS_SETTINGS", [])
        dict_settings = self.update_settings(run_plugin_settings)
        super().__init__(wxfunction, None, msg_plugins=msg_plugins, **dict_settings)
        self.latest_timestamp = getattr(settings, "SAVE_HISTORY_MSG_TIMESTAMP")

    def update_settings(self, run_plugin_settings):
        s = set(list(run_plugin_settings) + list(DEFAULT_RUN_PLUGINS))
        dict_settings = load_settings(settings)
        new_settings = {i:dict_settings.get(i) for i in s}
        return new_settings
    
    def run(self):
        latest_timestamp = self.latest_timestamp
        one_limit_count = 1000
        dbcount = self.wxfunction.getMaxDbindex()
        for dbindex in range(0, dbcount+1):
            count = int(self.wxfunction.GetLatestMsgLocalidsCount(latest_timestamp, dbindex))
            t = time.strftime("%Y-%m:%d %H:%M:%S", time.localtime(latest_timestamp))
            print(f"数据库(MSG{dbindex}.db), {t}到现在的消息总数据量: {count}")
            for i in range(0, count, one_limit_count):
                localids = list(self.wxfunction.GetLatestMsgLocalidsSlice(latest_timestamp, dbindex, one_limit_count, i))
                print(f"数据库(MSG{dbindex}.db), limit({one_limit_count}), offset({i}), 查询出的localids: {localids}")
                self._deal_localid_msg(localids, dbindex)
    
    def _deal_localid_msg(self, localids, dbindex):
        for localid in localids:
            msg = self.wxfunction.GetChatMsgJsonByLocalid(localid, dbindex)
            if not msg:
                continue
            msg_data = json.loads(msg)
            self.get_room_sender_nickname(msg_data)
            msg_data["sender_nickname"] = self.get_sender_name(msg_data["sender"])
            msg_struct = ChatMsgStruct(**msg_data)
            if msg_struct.msg_type in (MsgType.IMAGE, MsgType.VIDEO, MsgType.XML) \
                and not msg_struct.file_path:
                self.get_filepath(localid, dbindex, msg_struct)
            try:
                self._deal_msg(msg_struct)
                self.run_in_plugins(msg_struct)
            except:
                with open('errmsg.log', 'w', encoding='utf-8') as f:
                    f.write(msg)
                traceback.print_exc()
                continue
            time.sleep(0.05)
        
    # def run(self):
    #     localids = list(self.wxfunction.GetLatestMsgLocalids(self.latest_timestamp))
    #     print("localids: ", localids)
    
    
    def get_filepath(self, localid, dbindex, msg_struct:ChatMsgStruct):
        datas = self.wxfunction.GetFilePathByLocalid(localid, dbindex)
        if not datas:
            return
        datas = json.loads(datas)
        data = {i["1"]:i["2"] for i in datas["3"]}
        msg_struct.sign = data.get(2)
        msg_struct.file_path = data.get(4)
        msg_struct.thumb_path = data.get(3)
        

