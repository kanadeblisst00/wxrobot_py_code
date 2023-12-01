from . import MsgPluginTemplate, DealMsgThread, ChatMsgStruct
from . import settings, NotConfigured
from . import SqliteDatabase



class SaveToPostgre(MsgPluginTemplate):
    def __init__(self, wxfunction, dtObj:DealMsgThread) -> None:
        super().__init__(wxfunction, dtObj)
        if not getattr(settings, "SQLITE_DB", None):
            raise NotConfigured
        print(f"插件[{self._name(__file__)}]加载成功")
        self.db_config = getattr(settings, "SQLITE_DB")
        self.db_table = self.db_config.pop("db_table")
        sql = f'''CREATE TABLE {self.db_table} (
            localid INTEGER,
            msgid TEXT,
            msg_type INTEGER,
            is_self_msg INTEGER,
            timestamp INTEGER,
            sender TEXT,
            sender_nickname TEXT,
            room_sender TEXT,
            content text,
            sign TEXT,
            thumb_path TEXT,
            file_path TEXT,
            extrainfo TEXT,
            unknow_value0 INTEGER,
            unknow_value1 INTEGER,
            unknow_value2 text,
            unknow_value3 TEXT,
            unknow_value4 INTEGER,
            self_wxid TEXT,
            room_nickname TEXT
        );'''
        self.db_config["check_same_thread"] = False
        self.db = SqliteDatabase(self.db_config, create_table_sql=sql, db_table=self.db_table)
    
    def deal_msg(self, msg_struct:ChatMsgStruct):
        msg_data = msg_struct.to_dict()
        if msg_data.get('wxpid'):
            msg_data.pop('wxpid')
        if not msg_data.get("self_wxid"):
            msg_data["self_wxid"] = self.dtObj.wxid
        self.db.insert(self.db_table, msg_data)