#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI文档分块服务
使用大语言模型对文档进行智能分块
"""

import json
import logging
import time
import traceback
from typing import List, Dict, Any, Optional
import requests
from config_loader import config
from prompt_manager import get_prompt_manager

logger = logging.getLogger(__name__)

class AIChunkService:
    """AI文档分块服务"""
    
    def __init__(self):
        """初始化AI分块服务"""
        # 获取配置
        self.api_url = config.get('api', 'url')
        self.api_key = config.get_secret('siliconflow_api_key')
        self.model = config.get('api', 'ai_chunking_model')
        self.max_tokens = config.getint('api', 'ai_chunking_max_tokens', fallback=2048)
        self.timeout = config.getint('api', 'ai_chunking_timeout', fallback=600)
        self.max_retries = config.getint('api', 'ai_chunking_max_retries', fallback=3)
        self.retry_delay = config.getint('api', 'ai_chunking_retry_delay', fallback=2)
        self.min_text_length = config.getint('api', 'ai_chunking_min_text_length', fallback=10)
        self.min_chunk_length = config.getint('api', 'ai_chunking_min_chunk_length', fallback=5)
        self.max_chunk_length = config.getint('api', 'ai_chunking_max_chunk_length', fallback=1000)
        
        # 新增：AI参数
        self.temperature = config.getfloat('api', 'temperature', fallback=0.7)
        self.top_p = config.getfloat('api', 'top_p', fallback=0.9)
        self.frequency_penalty = config.getfloat('api', 'frequency_penalty', fallback=0.0)
        self.presence_penalty = config.getfloat('api', 'presence_penalty', fallback=0.0)
        
        # 获取提示词管理器
        self.prompt_manager = get_prompt_manager()
        
        # 获取分块提示词
        self.chunk_prompt = self.prompt_manager.get_ai_chunking_prompt()
        
        logger.info("AI分块服务初始化完成")
        logger.info(f"使用模型: {self.model}")
        logger.info(f"最大重试次数: {self.max_retries}")
        logger.info(f"超时时间: {self.timeout}秒")
    
    def _clean_json_response(self, content: str) -> str:
        """
        清理AI响应中的JSON内容
        
        Args:
            content: AI原始响应内容
            
        Returns:
            str: 清理后的JSON字符串
        """
        if not content:
            return ""
        
        # 移除前后空白
        content = content.strip()
        
        # 移除markdown代码块标记（包括反引号）
        import re
        
        # 移除 ```json 和 ``` 标记
        content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
        
        # 移除所有反引号
        content = re.sub(r'`', '', content)
        
        # 移除前后空白
        content = content.strip()
        
        # 尝试找到JSON开始和结束位置
        json_start = content.find('{')
        json_end = content.rfind('}')
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            content = content[json_start:json_end + 1]
        
        return content
    
    def _fix_json_format(self, json_str: str) -> str:
        """
        修复不标准的JSON格式
        
        Args:
            json_str: 原始JSON字符串
            
        Returns:
            str: 修复后的JSON字符串
        """
        import re
        
        # 第一步：清理特殊字符和转义字符
        # 移除零宽字符
        json_str = re.sub(r'[\u2000-\u200F\u2028-\u202F\u205F-\u206F]', '', json_str)
        
        # 修复转义的双引号
        json_str = re.sub(r'\\"', '"', json_str)
        
        # 修复转义的反斜杠
        json_str = re.sub(r'\\\\\\\\', '\\\\', json_str)
        
        # 第二步：修复单引号为双引号
        json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)
        
        # 第三步：修复缺少双引号的属性名
        # 匹配 pattern: property_name: value (其中property_name不包含引号)
        def fix_property_names(match):
            whitespace = match.group(1)
            property_name = match.group(2)
            colon_whitespace = match.group(3)
            value = match.group(4)
            return f'{whitespace}"{property_name}"{colon_whitespace}{value}'
        
        # 更精确的匹配，避免匹配数组中的内容
        json_str = re.sub(r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:\s*)([^,\n\r}]+?)(\s*[,}])', 
                         lambda m: f'{m.group(1)}"{m.group(2)}"{m.group(3)}{m.group(4)}{m.group(5)}', json_str)
        
        # 第四步：修复缺少引号的字符串值
        # 匹配 pattern: "property": value (其中value不是数字、true、false、null、数组、对象)
        def fix_string_values(match):
            property_part = match.group(1)  # "property":
            value_part = match.group(2).strip()  # value
            
            # 如果值不是数字、布尔值、null、数组、对象，且不是以引号开头，则添加引号
            if (not value_part.startswith('"') and 
                not value_part.startswith("'") and
                not value_part.isdigit() and
                not value_part.lower() in ['true', 'false', 'null'] and
                not value_part.startswith('[') and
                not value_part.startswith('{') and
                not value_part.endswith(']') and
                not value_part.endswith('}')):
                return f'{property_part} "{value_part}"'
            return match.group(0)
        
        json_str = re.sub(r'("[\w]+"\s*:\s*)([^,\n\r}]+)', fix_string_values, json_str)
        
        # 第五步：修复多余的引号
        json_str = re.sub(r'""([^"]*?)""', r'"\1"', json_str)
        
        # 第六步：修复缺少逗号的问题
        json_str = re.sub(r'}(\s*)(?=[^,}\]]*")', r'},\1', json_str)
        
        return json_str
    
    def _parse_json_with_fallback(self, json_str: str):
        """
        优先用pyjson5解析，失败则用修复逻辑+标准json解析
        """
        import json
        try:
            return pyjson5.decode(json_str)
        except Exception as e1:
            try:
                fixed = self._fix_json_format(json_str)
                return json.loads(fixed)
            except Exception as e2:
                logger.error(f"pyjson5和修复后解析都失败: {e1} | {e2}")
                return None
    
    def postprocess_merge_chapters(self, chunks: list) -> list:
        """
        后处理：将第一章相关的多个块自动合并为一个块，确保第一章内容始终为一个完整块。
        """
        if not chunks or not isinstance(chunks, list):
            return chunks
        merged_chunks = []
        chapter1_keywords = ["第一章", "系统概述", "系统特点"]
        chapter1_indices = []
        # 找到所有属于第一章的块索引
        for i, chunk in enumerate(chunks):
            content = chunk.get('content', '')
            if any(kw in content for kw in chapter1_keywords):
                chapter1_indices.append(i)
        if not chapter1_indices:
            return chunks
        # 合并第一章相关块
        merged_content = ''
        merged_summary = []
        merged_type = '章节'
        for i, chunk in enumerate(chunks):
            if i in chapter1_indices:
                merged_content += (chunk.get('content', '') + '\n')
                summary = chunk.get('summary', '')
                if summary:
                    merged_summary.append(summary)
        # 构建合并后的第一章块
        merged_chunk = {
            'content': merged_content.strip(),
            'type': merged_type,
            'summary': '；'.join(merged_summary) or '第一章内容'
        }
        # 构建最终块列表
        inserted = False
        for i, chunk in enumerate(chunks):
            if i == chapter1_indices[0]:
                merged_chunks.append(merged_chunk)
                inserted = True
            elif i in chapter1_indices:
                continue
            else:
                merged_chunks.append(chunk)
        # 如果没有插入，直接加到最前面
        if not inserted:
            merged_chunks.insert(0, merged_chunk)
        return merged_chunks
    
    def chunk_with_ai(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """
        使用AI模型进行智能分块
        
        Args:
            text: 待分块的文本
            
        Returns:
            List[Dict[str, Any]]: 分块结果，每个块包含content、type、reason字段
        """
        if not text or len(text.strip()) < self.min_text_length:
            logger.warning(f"文本内容过短，无法进行AI分块 (最小长度: {self.min_text_length})")
            return None
        
        response = None
        content = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"开始使用AI模型进行智能分块 (尝试 {attempt + 1}/{self.max_retries})")
                
                # 发送给AI前，先清理非法字符
                import re
                def clean_text_for_ai(text):
                    # 去除BOM
                    text = text.encode('utf-8').decode('utf-8-sig')
                    # 去除不可见字符、控制字符、全角空格
                    text = re.sub(r'[\u2000-\u200F\u2028-\u202F\u205F-\u206F\u3000\uFEFF]', '', text)
                    # 去除ASCII控制字符（除换行、回车、制表符）
                    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
                    return text
                text_cleaned = clean_text_for_ai(text)
                
                # 构建请求
                url = self.api_url
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}'
                }
                logger.debug("已构建请求头")
                
                # 构建提示词
                try:
                    prompt = self.chunk_prompt.format(text=text_cleaned)
                    logger.debug(f"已构建提示词，长度: {len(prompt)} 字符")
                    logger.debug(f"提示词前200字符: {prompt[:200]}...")
                except Exception as e_prompt:
                    logger.error(f"构建提示词失败: {str(e_prompt)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None
                
                # 构建请求参数
                request_data = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "frequency_penalty": self.frequency_penalty,
                    "presence_penalty": self.presence_penalty
                }
                logger.debug("已构建请求参数")
                logger.debug(f"请求参数: {request_data}")
                
                logger.info(f"准备发送请求到AI服务: {url}")
                logger.info(f"请求参数: model={self.model}, max_tokens={request_data['max_tokens']}, temperature={request_data['temperature']}")
                
                # 发送请求
                start_time = time.time()
                try:
                    response = requests.post(
                        url,
                        headers=headers,
                        json=request_data,
                        timeout=self.timeout
                    )
                    logger.debug("请求已发送")
                except requests.exceptions.RequestException as e_req:
                    logger.error(f"发送请求失败: {str(e_req)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None
                
                end_time = time.time()
                logger.info(f"AI服务响应时间: {end_time - start_time:.2f}秒")
                logger.info(f"AI服务响应状态码: {response.status_code}")
                
                try:
                    logger.debug(f"AI原始response.text: {response.text}")
                except Exception as e_text:
                    logger.error(f"无法获取response.text: {str(e_text)}")
                
                if response.status_code != 200:
                    logger.error(f"AI服务返回错误状态码: {response.status_code}")
                    try:
                        logger.error(f"错误响应: {response.text}")
                    except:
                        logger.error("无法获取错误响应内容")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None
                
                # 解析响应
                try:
                    response_data = response.json()
                    logger.debug(f"已解析response.json(): {response_data}")
                except Exception as e_json:
                    logger.error(f"response.json() 解析失败: {str(e_json)}")
                    try:
                        logger.error(f"完整的AI原始response.text: {response.text}")
                    except:
                        logger.error("无法获取response.text")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None

                content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # 新增：打印AI原始响应内容（未清理前）
                logger.info(f"AI原始响应内容（未清理前）长度: {len(content)} 字符")
                logger.info(f"AI原始响应内容（未清理前）全部内容: {content}")
                
                # 自动去除前后多余字符（如BOM、不可见字符、前后非JSON内容）
                import re
                def extract_json(text):
                    # 去除BOM和不可见字符
                    text = text.encode('utf-8').decode('utf-8-sig')
                    text = re.sub(r'[\u2000-\u200F\u2028-\u202F\u205F-\u206F]', '', text)
                    # 尝试提取最外层JSON对象
                    match = re.search(r'\{[\s\S]*\}', text)
                    if match:
                        return match.group()
                    return text
                content_extracted = extract_json(content)
                logger.info(f"AI响应内容（自动提取JSON后）长度: {len(content_extracted)} 字符")
                logger.info(f"AI响应内容（自动提取JSON后）前500字符: {content_extracted[:500]}")
                
                # 清理和解析JSON响应
                try:
                    # 清理响应内容
                    cleaned_content = self._clean_json_response(content_extracted)
                    logger.debug(f"清理后的内容长度: {len(cleaned_content)} 字符")
                    logger.debug(f"清理后的内容: {cleaned_content[:500]}...")
                    
                    if not cleaned_content:
                        logger.error("清理后的内容为空")
                        logger.error(f"原始content: {content}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                        return None
                    
                    # 使用强大的JSON解析函数
                    chunk_data = self._robust_json_parse(cleaned_content)
                    if not chunk_data:
                        logger.error("JSON解析失败")
                        logger.error(f"清理后的内容: {cleaned_content}")
                        # 新增：只用标准json.loads试试
                        import json
                        try:
                            obj = json.loads(cleaned_content)
                            logger.error("标准json.loads解析成功（但自定义解析失败）")
                        except Exception as e:
                            logger.error(f"标准json.loads解析失败: {e}")
                            logger.error(f"出错内容片段: {cleaned_content[:500]}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                        return None
                    
                    logger.debug(f"解析后的数据: {chunk_data}")
                    chunks = chunk_data.get('chunks', [])
                    logger.debug(f"提取的chunks: {chunks}")
                    
                    # 验证chunks的有效性
                    if chunks and isinstance(chunks, list):
                        valid_chunks = []
                        for chunk in chunks:
                            if isinstance(chunk, dict) and 'content' in chunk:
                                content = chunk['content']
                                if content and len(content.strip()) > 0:
                                    valid_chunks.append(chunk)
                        
                        if valid_chunks:
                            logger.info(f"AI分块成功，共生成 {len(valid_chunks)} 个文本块")
                            # 后处理：合并第一章相关块
                            valid_chunks = self.postprocess_merge_chapters(valid_chunks)
                            return valid_chunks
                        else:
                            logger.warning("所有chunks的content都为空")
                    else:
                        logger.warning("chunks不是有效列表或为空")
                    
                    # 处理AI返回单个content对象的情况
                    if isinstance(chunk_data, dict) and 'content' in chunk_data:
                        content = chunk_data['content']
                        if content and len(content.strip()) > 0:
                            logger.info("AI返回单个content对象，进行智能分块")
                            # 使用智能分块方法
                            chunks = self._smart_split_content(content)
                            if chunks:
                                logger.info(f"智能分块成功，共生成 {len(chunks)} 个文本块")
                                return chunks
                    
                    # 如果AI返回了chunks但验证失败，尝试修复
                    if chunks and isinstance(chunks, list):
                        logger.info("尝试修复AI返回的chunks")
                        fixed_chunks = []
                        for chunk in chunks:
                            if isinstance(chunk, dict):
                                # 确保chunk有content字段
                                if 'content' not in chunk:
                                    logger.warning("chunk缺少content字段，跳过")
                                    continue
                                
                                content = chunk['content']
                                if not content or len(content.strip()) == 0:
                                    logger.warning("chunk的content为空，跳过")
                                    continue
                                
                                # 如果content太短，尝试合并到下一个chunk
                                if len(content.strip()) < self.min_chunk_length:
                                    logger.info(f"chunk内容过短({len(content.strip())}字符)，尝试合并")
                                    if fixed_chunks:
                                        # 合并到上一个chunk
                                        fixed_chunks[-1]['content'] += '\n' + content
                                    else:
                                        # 作为第一个chunk，保留
                                        fixed_chunks.append(chunk)
                                else:
                                    fixed_chunks.append(chunk)
                        
                        if fixed_chunks:
                            logger.info(f"修复后生成 {len(fixed_chunks)} 个有效chunks")
                            return fixed_chunks
                    
                    logger.warning("AI返回的分块结果为空")
                    logger.warning(f"解析后的完整数据: {chunk_data}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None
                    
                except Exception as e:
                    logger.error(f"解析AI响应JSON失败: {str(e)}")
                    logger.error(f"错误位置: {e.pos if hasattr(e, 'pos') else '未知'}, 行: {e.lineno if hasattr(e, 'lineno') else '未知'}, 列: {e.colno if hasattr(e, 'colno') else '未知'}")
                    logger.error(f"AI响应内容: {content}")
                    if response is not None:
                        try:
                            logger.error(f"AI原始response.text: {response.text}")
                        except Exception as e2:
                            logger.error(f"无法打印response.text: {str(e2)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                logger.error(f"AI服务请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"AI服务请求异常: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return None
                
            except Exception as e:
                logger.error(f"AI分块过程中发生未知错误: {str(e)}")
                logger.error(f"AI原始返回内容: {content}")
                if response is not None:
                    try:
                        logger.error(f"AI原始response.text: {response.text}")
                    except Exception as e2:
                        logger.error(f"无法打印response.text: {str(e2)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return None
        
        return None
    
    def validate_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        验证分块结果的有效性
        
        Args:
            chunks: 分块结果列表
            
        Returns:
            bool: 验证是否通过
        """
        if not chunks:
            return False
        
        valid_count = 0
        for chunk in chunks:
            # 检查必要字段
            if 'content' not in chunk:
                logger.warning("分块结果缺少content字段")
                continue
            
            content = chunk['content']
            if not content or len(content.strip()) < self.min_chunk_length:
                logger.warning(f"分块内容过短: {len(content.strip())} 字符 (最小长度: {self.min_chunk_length})")
                continue
            
            if len(content) > self.max_chunk_length:
                logger.warning(f"分块内容过长: {len(content)} 字符 (最大长度: {self.max_chunk_length})")
                continue
            
            valid_count += 1
        
        # 只要有一个有效分块就认为验证通过
        if valid_count > 0:
            logger.info(f"验证通过，有效分块数量: {valid_count}/{len(chunks)}")
            return True
        else:
            logger.warning("没有有效的分块")
            return False
    
    def extract_text_content(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        从分块结果中提取纯文本内容
        
        Args:
            chunks: 分块结果列表
            
        Returns:
            List[str]: 纯文本内容列表
        """
        return [chunk['content'].strip() for chunk in chunks if chunk.get('content')]

    def _robust_json_parse(self, json_str: str) -> Optional[Dict]:
        """
        强大的JSON解析函数，专门处理大模型返回的各种不规范JSON格式
        
        Args:
            json_str: 原始JSON字符串
            
        Returns:
            Dict: 解析后的JSON对象，失败返回None
        """
        import re
        import json
        
        if not json_str:
            return None
        
        # 第一步：基础清理
        json_str = json_str.strip()
        
        # 移除markdown代码块标记
        if json_str.startswith('```json'):
            json_str = json_str[7:]
        elif json_str.startswith('```'):
            json_str = json_str[3:]
        if json_str.endswith('```'):
            json_str = json_str[:-3]
        
        json_str = json_str.strip()
        
        # 第二步：尝试多种解析策略
        strategies = [
            self._strategy_simple_json,  # 新增：简单JSON解析
            self._strategy_pyjson5,
            self._strategy_fix_and_parse,
            self._strategy_demjson3,  # 新增：demjson3宽容解析
            self._strategy_extract_json,
            self._strategy_manual_parse,
            self._strategy_aggressive_clean
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                logger.debug(f"尝试解析策略 {i+1}: {strategy.__name__}")
                result = strategy(json_str)
                if result:
                    logger.info(f"策略 {i+1} 解析成功")
                    return result
            except Exception as e:
                logger.debug(f"策略 {i+1} 失败: {str(e)}")
                continue
        
        logger.error("所有解析策略都失败了")
        return None
    
    def _strategy_simple_json(self, json_str: str) -> Optional[Dict]:
        """策略0：简单JSON解析，处理标准格式"""
        try:
            return json.loads(json_str)
        except Exception:
            return None
    
    def _strategy_pyjson5(self, json_str: str) -> Optional[Dict]:
        """策略1：使用pyjson5解析"""
        try:
            return pyjson5.decode(json_str)
        except Exception:
            return None
    
    def _strategy_fix_and_parse(self, json_str: str) -> Optional[Dict]:
        """策略2：修复后使用标准json解析"""
        try:
            fixed = self._fix_json_format(json_str)
            return json.loads(fixed)
        except Exception:
            return None
    
    def _strategy_demjson3(self, json_str: str) -> Optional[Dict]:
        """策略：使用demjson3宽容解析AI生成的伪JSON"""
        try:
            import demjson3
            return demjson3.decode(json_str)
        except Exception as e:
            logger.error(f"demjson3解析失败: {e}")
            return None
    
    def _strategy_extract_json(self, json_str: str) -> Optional[Dict]:
        """策略3：提取JSON部分"""
        try:
            # 找到最外层的JSON对象
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', json_str, re.DOTALL)
            if json_match:
                json_part = json_match.group()
                return json.loads(json_part)
            return None
        except Exception:
            return None
    
    def _strategy_manual_parse(self, json_str: str) -> Optional[Dict]:
        """策略4：手动解析chunks数组"""
        try:
            # 尝试手动解析chunks数组
            chunks = []
            
            # 使用更精确的匹配模式，能够处理嵌套的JSON对象
            # 查找所有可能的chunk对象（支持新的格式：content, type, summary）
            chunk_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*"content"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            chunk_matches = re.findall(chunk_pattern, json_str, re.DOTALL)
            
            for chunk_str in chunk_matches:
                try:
                    # 清理chunk字符串
                    chunk_str = re.sub(r'[\n\r\t]', ' ', chunk_str)
                    chunk_str = re.sub(r'\s+', ' ', chunk_str)
                    
                    # 提取content
                    content_match = re.search(r'"content"\s*:\s*"([^"]*)"', chunk_str)
                    content = content_match.group(1) if content_match else ""
                    
                    # 提取type
                    type_match = re.search(r'"type"\s*:\s*"([^"]*)"', chunk_str)
                    chunk_type = type_match.group(1) if type_match else "内容"
                    
                    # 提取summary
                    summary_match = re.search(r'"summary"\s*:\s*"([^"]*)"', chunk_str)
                    summary = summary_match.group(1) if summary_match else ""
                    
                    if content:
                        chunk_obj = {
                            "content": content,
                            "type": chunk_type
                        }
                        if summary:
                            chunk_obj["summary"] = summary
                        chunks.append(chunk_obj)
                except Exception:
                    continue
            
            if chunks:
                return {"chunks": chunks}
            return None
        except Exception:
            return None
    
    def _strategy_aggressive_clean(self, json_str: str) -> Optional[Dict]:
        """策略5：激进清理和解析"""
        try:
            # 移除所有换行符和多余空格
            cleaned = re.sub(r'\s+', ' ', json_str)
            
            # 修复常见的JSON问题
            cleaned = re.sub(r',\s*}', '}', cleaned)  # 移除末尾逗号
            cleaned = re.sub(r',\s*]', ']', cleaned)  # 移除数组末尾逗号
            cleaned = re.sub(r'}\s*}\s*}', '}}}', cleaned)  # 修复多余的大括号
            
            # 尝试解析
            return json.loads(cleaned)
        except Exception:
            return None

    def _smart_split_content(self, content: str) -> List[Dict[str, Any]]:
        """
        智能分块方法，将单个content按语义单元分割
        
        Args:
            content: 待分块的文本内容
            
        Returns:
            List[Dict[str, Any]]: 分块结果列表
        """
        import re
        
        if not content or len(content.strip()) < self.min_text_length:
            return []
        
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_title = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测章节标题（如：第一章、第二章等）
            if re.match(r'^第[一二三四五六七八九十\d]+章', line):
                # 保存当前块
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    if len(chunk_text) >= self.min_chunk_length:
                        chunks.append({
                            'content': chunk_text,
                            'type': '章节',
                            'summary': current_title or '文档章节内容'
                        })
                
                # 开始新块
                current_chunk = [line]
                current_title = line
                
            # 检测小节标题（如：一、二、三、等）
            elif re.match(r'^[一二三四五六七八九十\d]+、', line):
                # 保存当前块
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    if len(chunk_text) >= self.min_chunk_length:
                        chunks.append({
                            'content': chunk_text,
                            'type': '小节',
                            'summary': current_title or '文档小节内容'
                        })
                
                # 开始新块
                current_chunk = [line]
                
            # 检测数字标题（如：1. 2. 3. 等）
            elif re.match(r'^\d+\.', line):
                # 如果当前块已经有内容，且这行很长，可能是新段落
                if current_chunk and len(line) > 20:
                    # 保存当前块
                    chunk_text = '\n'.join(current_chunk)
                    if len(chunk_text) >= self.min_chunk_length:
                        chunks.append({
                            'content': chunk_text,
                            'type': '段落',
                            'summary': current_title or '文档段落内容'
                        })
                    current_chunk = [line]
                else:
                    current_chunk.append(line)
                    
            else:
                # 普通内容行
                current_chunk.append(line)
                
                # 如果当前块太长（超过最大长度），强制分割
                if len('\n'.join(current_chunk)) > self.max_chunk_length:
                    chunk_text = '\n'.join(current_chunk)
                    if len(chunk_text) >= self.min_chunk_length:
                        chunks.append({
                            'content': chunk_text,
                            'type': '段落',
                            'summary': current_title or '文档段落内容'
                        })
                    current_chunk = []
        
        # 保存最后一个块
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_length:
                chunks.append({
                    'content': chunk_text,
                    'type': '段落',
                    'summary': current_title or '文档段落内容'
                })
        
        # 如果分块太少，尝试按段落分割
        if len(chunks) < 2:
            chunks = []
            paragraphs = re.split(r'\n\s*\n', content)
            for i, para in enumerate(paragraphs):
                para = para.strip()
                if para and len(para) >= self.min_chunk_length:
                    chunks.append({
                        'content': para,
                        'type': '段落',
                        'summary': f'第{i+1}段内容'
                    })
        
        return chunks

def test_ai_chunk_service():
    """测试AI分块服务"""
    print("=== 测试AI分块服务 ===\n")
    
    service = AIChunkService()
    
    # 测试文本
    test_text = """
智能系统使用手册

第一章：系统概述
本智能系统是一款基于人工智能技术的知识管理平台，旨在帮助用户高效地管理和查询文档信息。

系统特点：
1. 智能文档处理
   支持多种文档格式，包括PDF、Word、Excel、TXT等。
   自动提取文档内容，生成结构化数据。

2. 高效搜索功能
   基于向量数据库的语义搜索。
   支持关键词匹配和相似度排序。

3. 用户友好界面
   简洁直观的操作界面。
   支持批量操作和实时预览。
    """
    
    print("测试文本:")
    print(test_text)
    print("\n开始AI分块...")
    
    # 执行AI分块
    chunks = service.chunk_with_ai(test_text)
    
    if chunks:
        print(f"\nAI分块成功，共 {len(chunks)} 个块:")
        for i, chunk in enumerate(chunks, 1):
            print(f"\n块 {i}:")
            print(f"  内容: {chunk.get('content', '')[:100]}...")
            print(f"  类型: {chunk.get('type', '未知')}")
            print(f"  原因: {chunk.get('reason', '未知')}")
        
        # 验证结果
        if service.validate_chunks(chunks):
            print("\n✓ 分块结果验证通过")
        else:
            print("\n✗ 分块结果验证失败")
        
        # 提取纯文本
        text_contents = service.extract_text_content(chunks)
        print(f"\n提取的纯文本块数量: {len(text_contents)}")
        
    else:
        print("\n✗ AI分块失败")

if __name__ == "__main__":
    test_ai_chunk_service() 