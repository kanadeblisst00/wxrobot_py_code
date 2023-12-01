import sys
import os
import traceback


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from package.wxstruct import ChatMsgStruct, MsgType, XmlMsgType, SysMsgType, AddFriendXmlField
    from package.deal_msg import DealMsgThread, NotConfigured, load_plugins
    from package.plugin_class import PluginTemplate, MsgPluginTemplate
    from package.postgresqldb import Database
    from package.sqlitedb import SqliteDatabase
    from package import get_wxid_from_contact_list, load_settings
    import settings
except Exception as e:
    traceback.print_exc()
finally:
    sys.path.pop(0)






    