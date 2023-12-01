#-*- coding: utf-8 -*-
import traceback
import settings

from threading import Event
from package import load_settings
from package.deal_msg import DealMsgThread, load_plugins, NotConfigured


# 这一段代码没啥用，只是为了语法提示
# wxfunction已经在软件内导入了, 它是aardio写的代码，提供了接口给Python使用
try:
    from package import wxfunction
except:
    pass


def main_func():
    # 控制消息处理线程是否终止
    event = Event()
    event.set()
    # 开启消息处理线程
    dict_settings = load_settings(settings)
    msg_plugins, gen_plugins = load_plugins()
    msgThread = DealMsgThread(wxfunction, event, msg_plugins=msg_plugins, **dict_settings)
    msgThread.start()
    
    plugin_objs = []
    for plugin_class in gen_plugins:
        try:
            plugin_obj = plugin_class(wxfunction)
        except NotConfigured:
            continue
        except:
            print(f"加载插件({plugin_class})异常")
            traceback.print_exc()
        else:
            plugin_obj.start()
            plugin_objs.append(plugin_obj)

    for obj in plugin_objs:
        obj.join()

    msgThread.join()


if __name__ == '__main__':
    main_func()