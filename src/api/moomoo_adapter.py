import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from moomoo import (
    OpenSecTradeContext, TrdSide, OrderType, TrdEnv, TrdMarket, SecurityFirm,
    RET_OK, Currency, OrderStatus
)
import configparser
import logging
import threading
from .trading_interface import TradingInterface
import pandas as pd

logger = logging.getLogger(__name__)

class MoomooAdapter(TradingInterface):
    def __init__(self, config):
        self.config = config
        self.HOST = config.get('host', '127.0.0.1')
        self.PORT = int(config.get('port', '11111'))
        self.SECURITY_FIRM = getattr(SecurityFirm, config.get('security_firm', 'FUTUINC'))
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

    def get_account_info(self, **kwargs) -> Dict[str, Any]:
        acc_id = kwargs.get('acc_id')
        trade_env = kwargs.get('trade_env')
        market = kwargs.get('market')
        currency = kwargs.get('currency', Currency.USD)
        return self.get_account_info(acc_id, trade_env, market, currency)

    def get_positions(self, **kwargs) -> Dict[str, Any]:
        acc_id = kwargs.get('acc_id')
        trade_env = kwargs.get('trade_env')
        market = kwargs.get('market')
        return self.get_positions(acc_id, trade_env, market)

    def get_history_orders(self, **kwargs) -> Dict[str, Any]:
        acc_id = kwargs.get('acc_id')
        trade_env = kwargs.get('trade_env')
        market = kwargs.get('market')
        include_cancelled = kwargs.get('include_cancelled', False)
        days = kwargs.get('days', 30)
        return self.get_history_orders(acc_id, trade_env, market, include_cancelled, days)
    
    def place_order(self, **kwargs) -> Any:
        # 从 kwargs 中提取所需参数
        acc_id = kwargs.get('acc_id')
        trade_env = kwargs.get('trade_env')
        market = kwargs.get('market')
        code = kwargs.get('code')
        price = kwargs.get('price')
        qty = kwargs.get('qty')
        trd_side = kwargs.get('trd_side')
        return self.place_order(acc_id, trade_env, market, code, price, qty, trd_side)

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