# test_moomoo_api.py

from moomoo import *
import pandas as pd
import configparser
import os

pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)

def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'userconfig.ini')
    config.read(config_path)
    return config['MoomooAPI']

# 加载配置
moomoo_config = load_config()
HOST = moomoo_config.get('host', '127.0.0.1')
PORT = moomoo_config.getint('port', 11111)
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
    print(f"\n获取账户 {acc_id} 信息:")
    ret, data = trd_ctx.accinfo_query(trd_env=TRADE_ENV, acc_id=acc_id, currency=Currency.USD)
    if ret == RET_OK:
        print("账户资金信息:")
        print(data)
        print("\n账户摘要:")
        print(f"账户ID: {acc_id}")
        print(f"账户环境: {'真实账户' if TRADE_ENV == TrdEnv.REAL else '模拟账户'}")
        print(f"币种: {data['currency'].values[0]}")
        print(f"总资产: ${data['total_assets'].values[0]:.2f}")
        print(f"现金: ${data['cash'].values[0]:.2f}")
        print(f"市值: ${data['market_val'].values[0]:.2f}")
        print(f"购买力: ${data['power'].values[0]:.2f}")
    else:
        print(f'获取账户 {acc_id} 信息失败：', data)
    trd_ctx.close()

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
    print(f"\n查询账户 {acc_id} 持仓:")
    ret, data = trd_ctx.position_list_query(trd_env=TRADE_ENV, acc_id=acc_id)
    if ret == RET_OK:
        print(f"持仓股票数: {len(data)}")
        if not data.empty:
            print("持仓摘要:")
            for _, row in data.iterrows():
                print(f"{row['stock_name']} ({row['code']}): {row['qty']} 股, 市值: ${row['market_val']:.2f}, 盈亏比例: {row['pl_ratio']:.2f}%")
        else:
            print("当前没有持仓")
    else:
        print('查询持仓失败：', data)
    trd_ctx.close()

def main():
    print("开始 Moomoo API 测试...")
    print(f"使用配置: HOST={HOST}, PORT={PORT}, TRADE_ENV={TRADE_ENV}, SECURITY_FIRM={SECURITY_FIRM}")
    
    acc_list = get_acc_list()
    if acc_list is not None and not acc_list.empty:
        selected_acc_id = select_account(acc_list)
        get_account_info(selected_acc_id)
        get_history_orders(selected_acc_id)
        get_positions(selected_acc_id)
    else:
        print("没有找到任何账户")
    
    print("\nMoomoo API 测试完成。")

if __name__ == "__main__":
    main()