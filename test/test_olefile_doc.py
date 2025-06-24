#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试olefile读取.doc文件
"""

import os
import sys
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_olefile_doc():
    """测试olefile读取.doc文件"""
    print("=== 测试olefile读取.doc文件 ===")
    
    # 测试文件路径
    test_file = "uploads/word/test.doc"
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return
    
    print(f"测试文件: {test_file}")
    print(f"文件大小: {os.path.getsize(test_file)} 字节")
    
    try:
        import olefile
        
        # 检查是否是OLE文件
        if olefile.isOleFile(test_file):
            print("✓ 文件是OLE格式")
            
            ole = olefile.OleFileIO(test_file)
            
            # 列出所有流
            print("\n文件中的流:")
            for stream in ole.listdir():
                print(f"  - {stream}")
            
            # 尝试读取WordDocument流
            if ole.exists('WordDocument'):
                print("\n✓ 找到WordDocument流")
                word_doc = ole.openstream('WordDocument').read()
                print(f"WordDocument流大小: {len(word_doc)} 字节")
                
                # 尝试提取文本
                content = extract_text_from_ole(ole)
                if content:
                    print(f"\n✓ 成功提取文本，长度: {len(content)} 字符")
                    print(f"文本预览: {content[:200]}...")
                else:
                    print("\n✗ 未能提取到有效文本")
            else:
                print("\n✗ 未找到WordDocument流")
            
            ole.close()
        else:
            print("✗ 文件不是OLE格式")
            
    except ImportError:
        print("✗ olefile库未安装")
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

def extract_text_from_ole(ole):
    """从OLE文件中提取文本"""
    try:
        content = ""
        
        # 尝试读取不同的流
        streams_to_try = ['WordDocument', 'Contents', '1Table', '0Table']
        
        for stream_name in streams_to_try:
            if ole.exists(stream_name):
                try:
                    print(f"尝试读取流: {stream_name}")
                    stream = ole.openstream(stream_name)
                    data = stream.read()
                    print(f"  流大小: {len(data)} 字节")
                    
                    # 尝试解码为文本
                    try:
                        text = data.decode('utf-8', errors='ignore')
                        # 清理文本
                        text = clean_ole_text(text)
                        if text.strip():
                            content += text + "\n"
                            print(f"  ✓ 成功提取文本: {len(text)} 字符")
                        else:
                            print(f"  ✗ 提取的文本为空")
                    except:
                        # 如果UTF-8失败，尝试其他编码
                        try:
                            text = data.decode('gbk', errors='ignore')
                            text = clean_ole_text(text)
                            if text.strip():
                                content += text + "\n"
                                print(f"  ✓ 使用GBK编码成功提取文本: {len(text)} 字符")
                            else:
                                print(f"  ✗ GBK编码提取的文本为空")
                        except:
                            print(f"  ✗ 无法解码为文本")
                    
                    stream.close()
                except Exception as e:
                    print(f"  ✗ 读取流失败: {str(e)}")
                    continue
        
        return content
        
    except Exception as e:
        print(f"从OLE文件提取文本失败: {str(e)}")
        return ""

def clean_ole_text(text):
    """清理从OLE文件提取的文本"""
    # 移除控制字符
    import re
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

if __name__ == "__main__":
    test_olefile_doc() 