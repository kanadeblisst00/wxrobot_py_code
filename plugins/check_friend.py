import time
from threading import Thread
from . import settings, NotConfigured


class CheckFriendStatus(Thread):
    def __init__(self, wxfunction) -> None:
        super().__init__()
        if not getattr(settings, "IS_CHECK_FRIEND", None):
            raise NotConfigured
        print(f"插件[{self._name(__file__)}]加载成功")
        self.result_name = "检测好友结果.csv"
        self.wxfunction = wxfunction
        self.filter_contact = [
            "fmessage","qqmail","medianote","qmessage","newsapp","filehelper","weixin",
            "tmessage","mphelper","gh_7aac992b0363","qqsafe","floatbottle","gh_3dfda90e39d6",
            "exmail_tool","gh_bf214c93111c"
        ]
        self.contact_list = list(wxfunction.GetContactList())

    def run(self):
        results = []
        keys = ("wxid", "微信号", "备注", "昵称", "验证消息")
        count = len(self.contact_list)
        print(f"你的好友和群有{count}个，预计需要时间{6*count//60+1}分钟")
        for contact in self.contact_list:
            wxid:str = contact["wxid"]
            if wxid.endswith('@chatroom') or wxid in self.filter_contact:
                continue
            verify_msg = self.wxfunction.CheckFriendStatus(wxid)
            print(f"{contact.get('昵称')}[{wxid}], 验证消息: {verify_msg}")
            contact["验证消息"] = verify_msg
            result = tuple((contact.get(i, "") for i in keys))
            results.append(result)
            time.sleep(5)
        print("已全部验证完成, 正在保存到csv中！")
        self.save_results(results, keys)
    
    def save_results(self, results, keys):
        s = '\n'.join([','.join(result) for result in results if "对方是您的好友" not in result[-1]])

        with open(self.result_name, 'w', encoding='utf-8-sig') as f:
            f.write(','.join(keys) + '\n')
            f.write(s)

