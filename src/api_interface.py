# src/api_interface.py

from typing import Dict, Optional
from moomoo import OpenSecTradeContext, TrdEnv, TrdMarket, SecurityFirm, RET_OK, Currency, TrdSide
import configparser
import pandas as pd
import os
import time
import threading
import logging

logger = logging.getLogger(__name__)

class MoomooAPI:
    def __init__(self):
        self.config = self.load_moomoo_config()
        self.HOST = self.config.get('host', '127.0.0.1')
        self.PORT = int(self.config.get('port', '11111'))
        self.SECURITY_FIRM = getattr(SecurityFirm, self.config.get('security_firm', 'FUTUINC'))
        self.stop_event = threading.Event()

    @staticmethod
    def load_moomoo_config() -> Dict[str, str]:
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
        return dict(config['MoomooAPI'])

    def test_moomoo_connection(self, trade_env: TrdEnv, market: TrdMarket, timeout: float = 10.0) -> bool:
        result = [False]
        exception = [None]

        def connection_attempt():
            try:
                with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                    ret, data = trd_ctx.get_acc_list()
                if ret == RET_OK:
                    logger.info(f"Moomoo API connection successful for {market} in {trade_env} mode")
                    result[0] = True
                else:
                    logger.error(f"Moomoo API connection failed for {market} in {trade_env} mode: {data}")
            except Exception as e:
                logger.exception(f"Error testing Moomoo connection for {market} in {trade_env} mode: {str(e)}")
                exception[0] = e

        thread = threading.Thread(target=connection_attempt)
        thread.start()

        # 等待线程完成或超时
        thread.join(timeout)

        if thread.is_alive():
            logger.error(f"Moomoo API connection timed out after {timeout} seconds")
            self.stop_event.set()  # 设置停止标志
            thread.join(1)  # 再次等待线程结束
            return False

        if exception[0]:
            raise exception[0]

        return result[0]
    
    def stop_all_connections(self):
        self.stop_event.set()

    def get_acc_list(self, trade_env: TrdEnv, market: TrdMarket) -> Optional[pd.DataFrame]:
        logger.info(f"Getting account list for trade_env: {trade_env}, market: {market}")
        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                ret, data = trd_ctx.get_acc_list()
            if ret == RET_OK:
                filtered_data = data[data['trd_env'] == trade_env]
                logger.info(f"Filtered account list: {filtered_data.to_dict()}")
                return filtered_data
            else:
                logger.error(f'获取账户列表失败：{data}')
                return None
        except Exception as e:
            logger.exception(f"获取账户列表时发生错误：{str(e)}")
            return None

    @staticmethod
    def select_account(acc_list: pd.DataFrame) -> Optional[int]:
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
            except Exception as e:
                logger.exception(f"选择账户时发生错误：{str(e)}")
                return None

    def get_account_info(self, acc_id: int, trade_env: TrdEnv, market: TrdMarket) -> Optional[pd.DataFrame]:
        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                ret, data = trd_ctx.accinfo_query(acc_id=acc_id, trd_env=trade_env, currency=Currency.USD)
            if ret == RET_OK:
                return data
            else:
                logger.error(f'获取账户 {acc_id} 信息失败：{data}')
                return None
        except Exception as e:
            logger.exception(f"获取账户信息时发生错误：{str(e)}")
            return None

    def get_history_orders(self, acc_id: int, trade_env: TrdEnv, market: TrdMarket) -> Optional[pd.DataFrame]:
        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                ret, data = trd_ctx.history_order_list_query(acc_id=acc_id, trd_env=trade_env)
            if ret == RET_OK:
                logger.info(f"Successfully retrieved {len(data)} history orders")
                return data
            else:
                logger.error(f'查询账户 {acc_id} 历史订单失败：{data}')
                return None
        except Exception as e:
            logger.exception(f"获取历史订单时发生错误：{str(e)}")
            return None

    def get_positions(self, acc_id: int, trade_env: TrdEnv, market: TrdMarket) -> Optional[pd.DataFrame]:
        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                ret, data = trd_ctx.position_list_query(acc_id=acc_id, trd_env=trade_env)
            if ret == RET_OK:
                logger.info(f"Successfully retrieved {len(data)} positions")
                return data
            else:
                logger.error(f'查询账户 {acc_id} 持仓失败：{data}')
                return None
        except Exception as e:
            logger.exception(f"获取持仓信息时发生错误：{str(e)}")
            return None

def place_order(self, acc_id: int, trade_env: TrdEnv, market: TrdMarket, 
                code: str, price: float, qty: float, trd_side: TrdSide) -> Optional[pd.DataFrame]:
    try:
        with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
            ret, data = trd_ctx.place_order(price=price, qty=qty, code=code, trd_side=trd_side, 
                                            acc_id=acc_id, trd_env=trade_env)
        if ret == RET_OK:
            logger.info(f"Successfully placed order: {data.to_dict()}")
            return data
        else:
            logger.error(f'下单失败：{data}')
            return None
    except Exception as e:
        logger.exception(f"下单时发生错误：{str(e)}")
        return None

def unlock_trade(self, acc_id: int, trade_env: TrdEnv, market: TrdMarket, password: str) -> bool:
    try:
        with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
            ret, data = trd_ctx.unlock_trade(password, acc_id=acc_id, trd_env=trade_env)
        if ret == RET_OK:
            logger.info("Successfully unlocked trade")
            return True
        else:
            logger.error(f'解锁交易失败：{data}')
            return False
    except Exception as e:
        logger.exception(f"解锁交易时发生错误：{str(e)}")
        return False

moomoo_api = MoomooAPI()    
