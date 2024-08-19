# test_moomoo_api.py

import configparser
import os
from moomoo import *
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)

# 使用字典存储不同类型的账户，每种类型可以有多个账户
ACCOUNT_DICT = {
    'SIMULATE_US': [],
    'SIMULATE_HK': [],
    'REAL_US': [],
    'REAL_HK': []
}

def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'userconfig.ini')
    
    # Default configuration
    default_config = {
        'host': '127.0.0.1',
        'port': '11111',
        'trade_env': 'REAL',
        'security_firm': 'FUTUINC'
    }
    
    if not os.path.exists(config_path):
        print("Warning: userconfig.ini not found. Using default values.")
        config['MoomooAPI'] = default_config
    else:
        config.read(config_path)
        if 'MoomooAPI' not in config:
            print("Warning: MoomooAPI section not found in userconfig.ini. Using default values.")
            config['MoomooAPI'] = default_config
    
    return config

# Load configuration
moomoo_config = load_config()['MoomooAPI']
HOST = moomoo_config.get('host', '127.0.0.1')
PORT = int(moomoo_config.get('port', '11111'))
TRADE_ENV = TrdEnv.REAL if moomoo_config.get('trade_env', 'REAL') == 'REAL' else TrdEnv.SIMULATE
SECURITY_FIRM = getattr(SecurityFirm, moomoo_config.get('security_firm', 'FUTUINC'))

def get_acc_list():
    trd_ctx = OpenSecTradeContext(host=HOST, port=PORT, security_firm=SECURITY_FIRM, filter_trdmarket=TrdMarket.US)
    print("\n获取账户列表:")
    ret, data = trd_ctx.get_acc_list()
    trd_ctx.close()
    if ret == RET_OK:
        print(data)
        return data
    else:
        print('获取账户列表失败：', data)
        return None

def classify_accounts(acc_list):
    for _, acc in acc_list.iterrows():
        acc_type = f"{'REAL' if acc['trd_env'] == 'REAL' else 'SIMULATE'}_{'US' if 'US' in acc['trdmarket_auth'] else 'HK'}"
        ACCOUNT_DICT[acc_type].append(acc['acc_id'])
    
    # 确保 283445327928853566 被正确分类
    if '283445327928853566' in acc_list['acc_id'].values:
        if '283445327928853566' not in ACCOUNT_DICT['REAL_US']:
            ACCOUNT_DICT['REAL_US'].insert(0, '283445327928853566')

def get_account_info(acc_id):
    trd_ctx = OpenSecTradeContext(host=HOST, port=PORT, security_firm=SECURITY_FIRM, filter_trdmarket=TrdMarket.US)
    print(f"\n获取账户 {acc_id} 信息:")
    ret, data = trd_ctx.accinfo_query(trd_env=TRADE_ENV, acc_id=acc_id, currency=Currency.USD)
    if ret == RET_OK:
        print("账户资金信息:")
        print(data)
    else:
        print(f'获取账户 {acc_id} 信息失败：', data)
    trd_ctx.close()

def main():
    print("开始 Moomoo API 测试...")
    print(f"使用配置: HOST={HOST}, PORT={PORT}, TRADE_ENV={TRADE_ENV}, SECURITY_FIRM={SECURITY_FIRM}")
    
    acc_list = get_acc_list()
    if acc_list is not None and not acc_list.empty:
        classify_accounts(acc_list)
        
        print("\n账户分类结果:")
        for acc_type, acc_ids in ACCOUNT_DICT.items():
            print(f"{acc_type} 账户: {acc_ids}")

        # 示例：获取真实美股账户的信息（优先选择 283445327928853566）
        if ACCOUNT_DICT['REAL_US']:
            get_account_info(ACCOUNT_DICT['REAL_US'][0])
    else:
        print("没有找到任何账户")
    
    print("\nMoomoo API 测试完成。")

if __name__ == "__main__":
    main()