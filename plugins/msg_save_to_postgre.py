from . import MsgPluginTemplate, DealMsgThread, ChatMsgStruct, Database
from . import settings, NotConfigured



class SaveToPostgre(MsgPluginTemplate):
    def __init__(self, wxfunction, dtObj:DealMsgThread) -> None:
        super().__init__(wxfunction, dtObj)
        if not getattr(settings, "POSTGRE_DB", None):
            raise NotConfigured
        print(f"插件[{self._name(__file__)}]加载成功")
        db_config = getattr(settings, "POSTGRE_DB", None)

        db_config_copy = db_config.copy()
        self.db_table = db_config_copy.pop("db_table")
        self.db = Database(db_config_copy)
        if not self.check_conn():
            raise NotConfigured
    
    def check_conn(self):
        try:
            self.db.connect()
        except:
            return False
        else:
            return True

    def deal_msg(self, msg_struct:ChatMsgStruct):
        msg_data = msg_struct.to_dict()
        if 'wxpid' in msg_data:
            msg_data.pop('wxpid')
        if not msg_data.get("self_wxid"):
            msg_data["self_wxid"] = self.dtObj.wxid
        self.db.insert(self.db_table, msg_data)