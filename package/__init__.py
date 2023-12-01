


def get_wxid_from_contact_list(contact_list, name:str=None, wxh:str=None):
    '''根据昵称或者备注获取wxid'''
    for i in contact_list:
        if name and (i.get('备注') == name or i.get("昵称") == name):
            return i["wxid"]
        if wxh and i.get("微信号") == wxh:
            return i["wxid"]
        

def load_settings(settings) -> dict:
    '''将settings.py里的配置转成字典'''
    dict_settings = {i:getattr(settings, i, None) for i in dir(settings) if i.isupper()}
    return dict_settings