# src/api/moomoo_adapter.py

import os
import configparser
import threading
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from moomoo import (
    OpenSecTradeContext, TrdSide, OrderType, TrdEnv, TrdMarket, SecurityFirm,
    RET_OK, Currency, OrderStatus
)

from src.utils.logger import setup_logger
from src.utils.error_handler import TradingError
from .trading_interface import TradingInterface

logger = setup_logger('moomoo_adapter')

class MoomooAdapter(TradingInterface):
    def __init__(self, config=None):
        """
        初始化 MoomooAdapter
        :param config: 可选的配置字典
        """
        super().__init__()  # 如果有父类的话需要调用
        self.stop_event = threading.Event()  # 先初始化 stop_event
        self.connection_thread = None
        self.trd_ctx = None
        
        self.config = config if config is not None else self.load_moomoo_config()
        self.HOST = self.config.get('host', '127.0.0.1')
        self.PORT = int(self.config.get('port', '11111'))
        self.SECURITY_FIRM = getattr(SecurityFirm, self.config.get('security_firm', 'FUTUINC'))

    @staticmethod
    def load_moomoo_config() -> Dict[str, str]:
        """
        加载 Moomoo API 配置
        
        :return: Moomoo API 配置字典
        """
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'userconfig.ini')
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

    def test_moomoo_connection(self, trade_env: TrdEnv, market: TrdMarket, timeout: float = 10.0, max_retries: int = 3) -> bool:
        if self.stop_event.is_set():
            return False

        market_str = "美股" if market == TrdMarket.US else "港股"
        env_str = "真实" if trade_env == TrdEnv.REAL else "模拟"
        
        logger.info(f"开始测试连接 {market_str}（{env_str}环境）...")
        
        for attempt in range(max_retries):
            if self.stop_event.is_set():
                logger.info("收到停止信号，终止连接尝试")
                return False

            result = [False]
            connection_completed = threading.Event()

            def connection_attempt():
                try:
                    self.trd_ctx = OpenSecTradeContext(
                        host=self.HOST, 
                        port=self.PORT, 
                        security_firm=self.SECURITY_FIRM, 
                        filter_trdmarket=market
                    )
                    
                    if self.stop_event.is_set():
                        if self.trd_ctx:
                            self.trd_ctx.close()
                        return

                    ret, data = self.trd_ctx.get_acc_list()
                    if ret == RET_OK:
                        logger.info(f"Moomoo API 连接成功：{market_str}（{env_str}环境）")
                        result[0] = True
                    else:
                        logger.error(f"Moomoo API 连接失败：{market_str}（{env_str}环境）: {data}")
                except Exception as e:
                    if not self.stop_event.is_set():
                        logger.exception(f"测试连接时发生错误：{str(e)}")
                finally:
                    if self.trd_ctx:
                        self.trd_ctx.close()
                        self.trd_ctx = None
                    connection_completed.set()

            try:
                self.connection_thread = threading.Thread(target=connection_attempt)
                self.connection_thread.daemon = True
                self.connection_thread.start()

                # 等待连接完成或超时
                if not connection_completed.wait(timeout):
                    logger.warning(f"连接尝试 {attempt + 1} 超时")
                    self.stop_event.set()  # 设置停止标志
                    if self.trd_ctx:
                        self.trd_ctx.close()
                        self.trd_ctx = None
                    if attempt == max_retries - 1:
                        return False
                    self.stop_event.clear()  # 重置停止标志准备下一次尝试
                    continue

                if result[0]:
                    return True

                if attempt < max_retries - 1:
                    logger.warning(f"连接尝试 {attempt + 1} 失败，重试...")
                    time.sleep(1)

            except Exception as e:
                if not self.stop_event.is_set():
                    logger.error(f"连接过程发生错误: {str(e)}")
                if attempt == max_retries - 1:
                    break
            finally:
                if self.connection_thread and self.connection_thread.is_alive():
                    self.stop_event.set()
                    if self.trd_ctx:
                        self.trd_ctx.close()
                        self.trd_ctx = None
                    self.connection_thread.join(1)

        logger.error(f"{market_str}（{env_str}环境）连接测试失败，已尝试 {max_retries} 次")
        return False

    def stop_all_connections(self):
        """停止所有连接"""
        logger.info("停止所有Moomoo API连接")
        self.stop_event.set()
        
        # 关闭当前的连接上下文
        if self.trd_ctx:
            try:
                self.trd_ctx.close()
                logger.debug("交易上下文关闭成功")
            except Exception as e:
                logger.error(f"关闭交易上下文时发生错误: {str(e)}")
            finally:
                self.trd_ctx = None
        
        # 等待当前连接线程结束，设置更长的超时时间
        if self.connection_thread and self.connection_thread.is_alive():
            try:
                # 增加等待时间到5秒，避免过早超时
                self.connection_thread.join(5)
                if self.connection_thread.is_alive():
                    logger.warning("连接线程未能在预定时间内结束")
            except Exception as e:
                logger.error(f"等待连接线程结束时发生错误: {str(e)}")
                
        # 重置状态
        self.stop_event.clear()
        self.connection_thread = None
        logger.info("所有连接已清理完成")

    def __del__(self):
        """析构函数确保清理"""
        try:
            if hasattr(self, 'stop_event') and hasattr(self, 'trd_ctx'):
                self.stop_all_connections()
        except:
            pass  # 析构函数中的异常应该被忽略

    def get_acc_list(self, trade_env: TrdEnv, market: TrdMarket) -> Optional[pd.DataFrame]:
        """
        获取账户列表
        
        :param trade_env: 交易环境
        :param market: 交易市场
        :return: 账户列表 DataFrame
        :raises TradingError: 如果获取账户列表失败
        """
        logger.info(f"Getting account list for trade_env: {trade_env}, market: {market}")
        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                ret, data = trd_ctx.get_acc_list()
            if ret == RET_OK:
                filtered_data = data[data['trd_env'] == trade_env]
                logger.info(f"Filtered account list: {filtered_data.to_dict()}")
                return filtered_data
            else:
                raise TradingError(f'获取账户列表失败：{data}')
        except Exception as e:
            logger.exception(f"获取账户列表时发生错误：{str(e)}")
            raise TradingError(f"获取账户列表失败：{str(e)}")

    @staticmethod
    def select_account(acc_list: pd.DataFrame) -> Optional[int]:
        """
        从账户列表中选择一个账户
        
        :param acc_list: 账户列表 DataFrame
        :return: 选中的账户 ID
        """
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
        """
        获取账户信息
        
        :param kwargs: 包含 acc_id, trade_env, market, currency 的字典
        :return: 账户信息字典
        :raises TradingError: 如果获取账户信息失败
        """
        acc_id = kwargs.get('acc_id')
        trade_env = kwargs.get('trade_env')
        market = kwargs.get('market')
        currency = kwargs.get('currency', Currency.USD)
        
        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                ret, data = trd_ctx.accinfo_query(acc_id=acc_id, trd_env=trade_env, currency=currency)
            if ret == RET_OK:
                return data.to_dict('records')[0]
            else:
                raise TradingError(f'获取账户 {acc_id} 信息失败：{data}')
        except Exception as e:
            logger.exception(f"获取账户信息时发生错误：{str(e)}")
            raise TradingError(f"获取账户信息失败：{str(e)}")

    def get_history_orders(self, **kwargs) -> List[Dict[str, Any]]:
        """
        获取历史订单
        
        :param kwargs: 必须包含 acc_id, trade_env, market，可选 include_cancelled, days
        :return: 历史订单列表
        :raises TradingError: 如果获取历史订单失败
        """
        acc_id = kwargs.get('acc_id')
        trade_env = kwargs.get('trade_env')
        market = kwargs.get('market')
        include_cancelled = kwargs.get('include_cancelled', False)
        days = kwargs.get('days', 30)

        if not all([acc_id, trade_env, market]):
            raise ValueError("Missing required parameters: acc_id, trade_env, market")

        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                status_filter_list = [] if include_cancelled else [
                    OrderStatus.SUBMITTED,
                    OrderStatus.FILLED_PART,
                    OrderStatus.FILLED_ALL,
                    OrderStatus.CANCELLED_PART,
                    OrderStatus.CANCELLED_ALL
                ]
                
                ret, data = trd_ctx.history_order_list_query(
                    status_filter_list=status_filter_list,
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    trd_env=trade_env,
                    acc_id=acc_id
                )
                
                if ret == RET_OK:
                    return data.to_dict('records')
                else:
                    raise TradingError(f'查询账户 {acc_id} 历史订单失败：{data}')
        except Exception as e:
            logger.exception(f"获取历史订单信息时发生错误：{str(e)}")
            raise TradingError(f"获取历史订单失败：{str(e)}")

    def get_positions(self, **kwargs) -> List[Dict[str, Any]]:
        """
        获取持仓信息
        
        :param kwargs: 必须包含 acc_id, trade_env, market
        :return: 持仓信息列表
        :raises TradingError: 如果获取持仓信息失败
        """
        acc_id = kwargs.get('acc_id')
        trade_env = kwargs.get('trade_env')
        market = kwargs.get('market')

        if not all([acc_id, trade_env, market]):
            raise ValueError("Missing required parameters: acc_id, trade_env, market")

        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                ret, data = trd_ctx.position_list_query(acc_id=acc_id, trd_env=trade_env)
            if ret == RET_OK:
                logger.info(f"Successfully retrieved {len(data)} positions")
                return data.to_dict('records')
            else:
                raise TradingError(f'查询账户 {acc_id} 持仓失败：{data}')
        except Exception as e:
            logger.exception(f"获取持仓信息时发生错误：{str(e)}")
            raise TradingError(f"获取持仓信息失败：{str(e)}")

    def place_order(self, **kwargs) -> Any:
        """
        下单
        
        :param kwargs: 包含 acc_id, trade_env, market, code, price, qty, trd_side 的字典
        :return: 下单结果
        :raises TradingError: 如果下单失败
        """
        acc_id = kwargs.get('acc_id')
        trade_env = kwargs.get('trade_env')
        market = kwargs.get('market')
        code = kwargs.get('code')
        price = kwargs.get('price')
        qty = kwargs.get('qty')
        trd_side = kwargs.get('trd_side')

        try:
            # 根据市场添加前缀
            if market == TrdMarket.US:
                code = f"US.{code}"
            elif market == TrdMarket.HK:
                code = f"HK.{code}"
            
            with OpenSecTradeContext(filter_trdmarket=market, host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM) as trd_ctx:
                ret, data = trd_ctx.place_order(
                    price=price, 
                    qty=qty, 
                    code=code, 
                    trd_side=trd_side,
                    order_type=OrderType.NORMAL, 
                    trd_env=trade_env,
                    acc_id=acc_id
                )
                if ret == RET_OK:
                    logger.info(f"下单成功：{data}")
                    return data
                else:
                    raise TradingError(f"下单失败：{data}")
        except Exception as e:
            logger.exception(f"下单时发生异常：{str(e)}")
            raise TradingError(f"下单失败：{str(e)}")

    def unlock_trade(self, acc_id: int, trade_env: TrdEnv, market: TrdMarket, password: str) -> bool:
        """
        解锁交易
        
        :param acc_id: 账户 ID
        :param trade_env: 交易环境
        :param market: 交易市场
        :param password: 交易密码
        :return: 是否成功解锁
        :raises TradingError: 如果解锁失败
        """
        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                ret, data = trd_ctx.unlock_trade(password, acc_id=acc_id, trd_env=trade_env)
            if ret == RET_OK:
                logger.info("Successfully unlocked trade")
                return True
            else:
                raise TradingError(f'解锁交易失败：{data}')
        except Exception as e:
            logger.exception(f"解锁交易时发生错误：{str(e)}")
            raise TradingError(f"解锁交易失败：{str(e)}")
        
    def close(self):
        """关闭 Moomoo API 连接"""
        # 实现关闭连接的逻辑
        logger.info("Closing Moomoo API connection")
        # 如果有需要关闭的资源，在这里添加相应的代码
        pass

    def cancel_order(self, order_id: str, **kwargs) -> bool:
        """
        取消订单
        
        :param order_id: 订单ID
        :param kwargs: 额外的参数
        :return: 是否成功取消订单
        :raises TradingError: 如果取消订单失败
        """
        # 实现取消订单的逻辑
        pass

    def get_real_time_quotes(self, symbols: List[str], **kwargs) -> Dict[str, Any]:
        """
        获取实时报价
        
        :param symbols: 股票代码列表
        :param kwargs: 额外的参数
        :return: 实时报价字典
        :raises TradingError: 如果获取实时报价失败
        """
        # 实现