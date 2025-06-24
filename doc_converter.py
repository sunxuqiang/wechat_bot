#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
.doc文件自动转换工具
"""

import os
import subprocess
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DocConverter:
    """DOC文件转换器"""
    
    def __init__(self):
        self.supported_tools = []
        self._detect_tools()
    
    def _detect_tools(self):
        """检测可用的转换工具"""
        # 检测LibreOffice
        try:
            result = subprocess.run(['soffice', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.supported_tools.append('libreoffice')
                logger.info("检测到LibreOffice")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # 检测WPS Office
        wps_paths = [
            r"C:\Program Files (x86)\WPS Office\11.1.0.11664\office6\wps.exe",
            r"C:\Program Files\WPS Office\11.1.0.11664\office6\wps.exe",
            r"C:\Users\{}\AppData\Local\Kingsoft\WPS Office\11.1.0.11664\office6\wps.exe".format(os.getenv('USERNAME', ''))
        ]
        
        for wps_path in wps_paths:
            if os.path.exists(wps_path):
                self.supported_tools.append('wps')
                logger.info(f"检测到WPS Office: {wps_path}")
                break
        
        # 检测Microsoft Word (通过COM接口)
        try:
            import win32com.client
            self.supported_tools.append('word_com')
            logger.info("检测到Microsoft Word COM接口")
        except ImportError:
            pass
        
        if not self.supported_tools:
            logger.warning("未检测到可用的转换工具")
    
    def convert_doc_to_docx(self, doc_path: str, output_dir: str = None) -> str:
        """
        将.doc文件转换为.docx文件
        
        Args:
            doc_path: .doc文件路径
            output_dir: 输出目录，如果为None则使用原文件所在目录
            
        Returns:
            str: 转换后的.docx文件路径，如果转换失败返回None
        """
        if not os.path.exists(doc_path):
            logger.error(f"文件不存在: {doc_path}")
            return None
        
        if not doc_path.lower().endswith('.doc'):
            logger.error(f"文件不是.doc格式: {doc_path}")
            return None
        
        if output_dir is None:
            output_dir = os.path.dirname(doc_path)
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        docx_path = os.path.join(output_dir, f"{base_name}.docx")
        
        # 尝试不同的转换方法
        for tool in self.supported_tools:
            try:
                if tool == 'libreoffice':
                    success = self._convert_with_libreoffice(doc_path, docx_path)
                elif tool == 'wps':
                    success = self._convert_with_wps(doc_path, docx_path)
                elif tool == 'word_com':
                    success = self._convert_with_word_com(doc_path, docx_path)
                
                if success and os.path.exists(docx_path):
                    logger.info(f"使用{tool}成功转换文件: {docx_path}")
                    return docx_path
                    
            except Exception as e:
                logger.warning(f"使用{tool}转换失败: {str(e)}")
                continue
        
        logger.error("所有转换方法都失败了")
        return None
    
    def _convert_with_libreoffice(self, doc_path: str, docx_path: str) -> bool:
        """使用LibreOffice转换"""
        try:
            cmd = [
                'soffice',
                '--headless',
                '--convert-to', 'docx:MS Word 2007 XML',
                '--outdir', os.path.dirname(docx_path),
                doc_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # LibreOffice可能会生成不同的文件名，需要重命名
                temp_docx = os.path.join(os.path.dirname(docx_path), 
                                       os.path.splitext(os.path.basename(doc_path))[0] + '.docx')
                if os.path.exists(temp_docx) and temp_docx != docx_path:
                    shutil.move(temp_docx, docx_path)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"LibreOffice转换失败: {str(e)}")
            return False
    
    def _convert_with_wps(self, doc_path: str, docx_path: str) -> bool:
        """使用WPS Office转换"""
        try:
            # WPS Office的命令行参数可能不同，这里提供一个基本实现
            wps_path = r"C:\Program Files (x86)\WPS Office\11.1.0.11664\office6\wps.exe"
            if not os.path.exists(wps_path):
                wps_path = r"C:\Program Files\WPS Office\11.1.0.11664\office6\wps.exe"
            
            if not os.path.exists(wps_path):
                return False
            
            # 复制文件到临时位置，然后让WPS打开并另存为
            temp_dir = os.path.join(os.path.dirname(doc_path), 'temp_convert')
            os.makedirs(temp_dir, exist_ok=True)
            temp_doc = os.path.join(temp_dir, os.path.basename(doc_path))
            shutil.copy2(doc_path, temp_doc)
            
            # 这里需要实现WPS的自动化，比较复杂
            # 暂时返回False，表示需要手动转换
            return False
            
        except Exception as e:
            logger.error(f"WPS转换失败: {str(e)}")
            return False
    
    def _convert_with_word_com(self, doc_path: str, docx_path: str) -> bool:
        """使用Microsoft Word COM接口转换"""
        try:
            import win32com.client
            
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            
            try:
                doc = word.Documents.Open(os.path.abspath(doc_path))
                doc.SaveAs2(os.path.abspath(docx_path), FileFormat=16)  # 16 = docx格式
                doc.Close()
                return True
            finally:
                word.Quit()
                
        except Exception as e:
            logger.error(f"Word COM转换失败: {str(e)}")
            return False
    
    def get_conversion_help(self) -> str:
        """获取转换帮助信息"""
        help_text = """
.doc文件转换帮助：

1. 自动转换（如果检测到转换工具）：
   - 系统会自动尝试转换.doc文件为.docx格式

2. 手动转换方法：
   a) 使用Microsoft Word：
      - 打开.doc文件
      - 点击"另存为"
      - 选择"Word文档(.docx)"格式
      - 保存文件
   
   b) 使用LibreOffice：
      - 安装LibreOffice: https://www.libreoffice.org/
      - 打开.doc文件
      - 点击"另存为"
      - 选择"Word 2007-365 (.docx)"格式
   
   c) 使用WPS Office：
      - 打开.doc文件
      - 点击"另存为"
      - 选择".docx"格式
   
   d) 在线转换：
      - https://convertio.co/doc-docx/
      - https://www.zamzar.com/convert/doc-to-docx/
      - https://cloudconvert.com/doc-to-docx

3. 批量转换：
   - 如果有多个.doc文件，建议使用LibreOffice命令行：
     soffice --headless --convert-to docx:MS Word 2007 XML *.doc
"""
        return help_text

def main():
    """主函数"""
    converter = DocConverter()
    
    print("=== .doc文件转换工具 ===")
    print(f"检测到的转换工具: {converter.supported_tools}")
    
    if not converter.supported_tools:
        print("\n未检测到可用的转换工具，请手动转换文件。")
        print(converter.get_conversion_help())
        return
    
    # 测试转换
    test_file = "uploads/word/test.doc"
    if os.path.exists(test_file):
        print(f"\n测试转换文件: {test_file}")
        result = converter.convert_doc_to_docx(test_file)
        if result:
            print(f"转换成功: {result}")
        else:
            print("转换失败")
    else:
        print(f"\n测试文件不存在: {test_file}")

if __name__ == "__main__":
    main() 