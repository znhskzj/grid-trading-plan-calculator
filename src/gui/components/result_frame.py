# src/gui/components/result_frame.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os
from datetime import datetime
from typing import List, Any
from src.utils.logger import setup_logger
from src.utils.gui_helpers import exception_handler, get_project_root
from src.utils.error_handler import GUIError

logger = setup_logger(__name__)

class ResultFrame(tk.Frame):
    def __init__(self, master: tk.Widget, controller: Any):
        super().__init__(master)
        self.controller = controller
        self.create_widgets()

    def create_widgets(self) -> None:
        try:
            self.create_result_text()
        except Exception as e:
            self.handle_gui_error("创建结果框架组件时发生错误", e)

    def create_result_text(self) -> None:
        self.result_text = tk.Text(self, wrap=tk.WORD, height=20, width=80)
        self.result_text.pack(expand=True, fill=tk.BOTH)
        
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.configure(yscrollcommand=scrollbar.set)
    
    def display_results(self, result: str) -> None:
        logger.debug(f"显示结果: {result[:100]}...")  # 只记录前100个字符，避免过多日志
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result)
        self.result_text.see("1.0")  # 滚动到顶部
        
        self.update()
        self.result_text.update()
        
        # 更新状态栏
        first_line = result.split('\n')[0] if result else "无结果"
        self.controller.update_status(first_line)
        
    def _format_result_lines(self, lines: List[str]) -> List[str]:
        logger.debug(f"格式化结果行的输入: {lines}")
        formatted_lines = []
        
        if not lines:
            logger.warning("_format_result_lines 的输入为空")
            return formatted_lines
        
        if lines[0].startswith("标的:"):
            formatted_lines.append(lines.pop(0))
        
        if lines and lines[0].startswith("当前连接:"):
            formatted_lines.extend(lines)
        else:
            formatted_lines.extend(self._format_trading_plan(lines))
        
        logger.debug(f"格式化后的行: {formatted_lines}")
        return formatted_lines

    def _format_trading_plan(self, lines: List[str]) -> List[str]:
        formatted_lines = []

        # 处理警告信息
        warning_line = next((line for line in lines if line.startswith("警告:")), None)
        if warning_line:
            formatted_lines.append(warning_line)

        # 格式化资金信息
        funds_info = next((line for line in lines if line.startswith("总资金:")), "")
        if funds_info:
            formatted_lines.append(funds_info)

        # 格式化价格和网格信息
        price_grid_info = next((line for line in lines if line.startswith("初始价格:")), "")
        if price_grid_info:
            formatted_lines.append(price_grid_info)

        # 处理分配方式信息
        allocation_info = next((line for line in lines if "选择的分配方式:" in line), "")
        if allocation_info:
            formatted_lines.append(allocation_info)

        # 处理分配特点
        distribution_feature = next((line for line in lines if "分配特点:" in line), "")
        if distribution_feature:
            formatted_lines.append(distribution_feature)

        # 处理购买计划
        purchase_plan = [line for line in lines if line.startswith("价格:")]
        if purchase_plan:
            formatted_lines.append("购买计划如下：")
            formatted_lines.extend(purchase_plan)

        # 处理总结信息
        summary_lines = [line for line in lines if line.startswith(("总购买股数:", "总投资成本:", "平均购买价格:", "最大潜在亏损:", "最大亏损比例:"))]
        formatted_lines.extend(summary_lines)

        return formatted_lines
    
    @exception_handler
    def save_to_csv(self) -> None:
        """保存结果为CSV文件"""
        content = self.result_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "没有可保存的结果")
            return

        file_path = self._get_save_file_path()
        if not file_path:
            return

        try:
            self._write_csv_file(file_path, content)
            messagebox.showinfo("成功", f"结果已保存到 {file_path}")
        except Exception as e:
            self.handle_gui_error("保存CSV文件时发生错误", e)

    def _get_save_file_path(self) -> str:
        """获取保存文件路径"""
        default_filename = f"grid_trading_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        initial_dir = os.path.join(get_project_root(), 'output')
        os.makedirs(initial_dir, exist_ok=True)
        return filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default_filename,
            initialdir=initial_dir
        )

    def _write_csv_file(self, file_path: str, content: str) -> None:
        """写入CSV文件"""
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            for line in content.split('\n'):
                if line.strip():
                    if ':' in line:
                        key, value = line.split(':', 1)
                        writer.writerow([key.strip(), value.strip()])
                    else:
                        writer.writerow([line.strip()])

    def handle_gui_error(self, message: str, exception: Exception) -> None:
        logger.error(f"{message}: {str(exception)}", exc_info=True)
        raise GUIError(f"{message}: {str(exception)}")