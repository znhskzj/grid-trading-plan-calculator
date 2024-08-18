# src/api_interface.py

from moomoo import *
import configparser
import os
import logging

logger = logging.getLogger(__name__)

def load_moomoo_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'userconfig.ini')
    if not os.path.exists(config_path):
        logger.warning("userconfig.ini not found. Using default values.")
        return {
            'host': '127.0.0.1',
            'port': '11111',
            'security_firm': 'FUTUINC'
        }
    config.read(config_path)
    if 'MoomooAPI' not in config:
        logger.warning("MoomooAPI section not found in userconfig.ini. Using default values.")
        return {
            'host': '127.0.0.1',
            'port': '11111',
            'security_firm': 'FUTUINC'
        }
    return config['MoomooAPI']

moomoo_config = load_moomoo_config()
HOST = moomoo_config.get('host', '127.0.0.1')
PORT = int(moomoo_config.get('port', '11111'))
TRADE_ENV = TrdEnv.REAL if moomoo_config.get('trade_env', 'REAL') == 'REAL' else TrdEnv.SIMULATE
SECURITY_FIRM = getattr(SecurityFirm, moomoo_config.get('security_firm', 'FUTUINC'))

def test_moomoo_connection(trade_env: TrdEnv, market: TrdMarket) -> bool:
    moomoo_config = load_moomoo_config()
    HOST = moomoo_config.get('host', '127.0.0.1')
    PORT = int(moomoo_config.get('port', '11111'))
    SECURITY_FIRM = getattr(SecurityFirm, moomoo_config.get('security_firm', 'FUTUINC'))

    try:
        trd_ctx = OpenSecTradeContext(host=HOST, port=PORT, security_firm=SECURITY_FIRM, filter_trdmarket=market)
        ret, data = trd_ctx.get_acc_list()
        trd_ctx.close()
        if ret == RET_OK:
            logger.info(f"Moomoo API connection successful for {market} in {trade_env} mode")
            return True
        else:
            logger.error(f"Moomoo API connection failed for {market} in {trade_env} mode: {data}")
            return False
    except Exception as e:
        logger.exception(f"Error testing Moomoo connection for {market} in {trade_env} mode: {str(e)}")
        return False

def get_acc_list():
    trd_ctx = OpenSecTradeContext(host=HOST, port=PORT, security_firm=SECURITY_FIRM, filter_trdmarket=TrdMarket.US)
    ret, data = trd_ctx.get_acc_list()
    trd_ctx.close()
    if ret == RET_OK:
        return data
    else:
        logger.error(f'获取账户列表失败：{data}')
        return None

def select_account(acc_list):
    print("\n可用账户:")
    for i, (_, acc) in enumerate(acc_list.iterrows()):
        print(f"{i+1}. 账户ID: {acc['acc_id']}, 类型: {acc['acc_type']}, 环境: {acc['trd_env']}")
    while True:
        try:
            choice = int(input("\n请选择要查询的账户 (输入序号): ")) - 1
            if 0 <= choice < len(acc_list):
                return acc_list.iloc[choice]['acc_id']
            else:
                print("无效的选择，请重试。")
        except ValueError:
            print("请输入有效的数字。")

def get_account_info(acc_id):
    trd_ctx = OpenSecTradeContext(host=HOST, port=PORT, security_firm=SECURITY_FIRM, filter_trdmarket=TrdMarket.US)
    ret, data = trd_ctx.accinfo_query(trd_env=TRADE_ENV, acc_id=acc_id, currency=Currency.USD)
    trd_ctx.close()
    if ret == RET_OK:
        return data
    else:
        print(f'获取账户 {acc_id} 信息失败：', data)
        return None

def get_history_orders(acc_id):
    trd_ctx = OpenSecTradeContext(host=HOST, port=PORT, security_firm=SECURITY_FIRM, filter_trdmarket=TrdMarket.US)
    print(f"\n查询账户 {acc_id} 历史订单:")
    ret, data = trd_ctx.history_order_list_query(trd_env=TRADE_ENV, acc_id=acc_id, start='2024-01-01', end='2024-08-13')
    if ret == RET_OK:
        print(f"总订单数: {len(data)}")
        print("最近5笔订单:")
        print(data.head())
    else:
        print('查询历史订单失败：', data)
    trd_ctx.close()

def get_positions(acc_id):
    trd_ctx = OpenSecTradeContext(host=HOST, port=PORT, security_firm=SECURITY_FIRM, filter_trdmarket=TrdMarket.US)
    ret, data = trd_ctx.position_list_query(trd_env=TRADE_ENV, acc_id=acc_id)
    trd_ctx.close()
    if ret == RET_OK:
        return data
    else:
        print(f'查询账户 {acc_id} 持仓失败：', data)
        return None
    
# 其他现有的API接口函数...