import os
import time
import json
import requests
import win32gui
import win32con
import win32api
import traceback
import re
from wxauto import WeChat
from knowledge_bot import KnowledgeBot
from pathlib import Path
import logging
from config_loader import config
from knowledge_query_service import get_knowledge_query_service
from prompt_manager import get_prompt_manager
import threading

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化知识库查询服务
knowledge_query_service = get_knowledge_query_service()
vector_store = None

# 初始化提示词管理器
prompt_manager = get_prompt_manager()

# 初始化向量存储（模块级，便于search_knowledge_base使用）
def init_vector_store():
    global vector_store
    from vector_store import FaissVectorStore
    vector_store = FaissVectorStore()
    vector_store_path = "knowledge_base/vector_store"
    if os.path.exists(f"{vector_store_path}.index") and os.path.exists(f"{vector_store_path}.pkl"):
        vector_store.load(vector_store_path)
        logger.info("知识库加载成功")
    else:
        logger.info("知识库文件不存在，将创建新的知识库")
    knowledge_query_service.set_vector_store(vector_store)
    logger.info("知识库查询服务已设置向量存储")

# 初始化模块级向量存储和服务
init_vector_store()

# 对外暴露统一的知识库查询接口
def search_knowledge_base(query, top_k=None, min_score=None):
    return knowledge_query_service.search_for_wechat(query, top_k=top_k, min_score=min_score)

def list_window_names():
    """列出所有窗口名称"""
    windows = []
    def winEnumHandler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            classname = win32gui.GetClassName(hwnd)
            if title:
                windows.append((hwnd, title, classname))
                print(f"Window: {title} (Handle: {hwnd}, Class: {classname})")
    win32gui.EnumWindows(winEnumHandler, None)
    return windows

def find_wechat_window():
    """查找微信窗口"""
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            classname = win32gui.GetClassName(hwnd)
            # 微信主窗口的类名是 'WeChatMainWndForPC'
            if classname == 'WeChatMainWndForPC':
                hwnds.append(hwnd)
                print(f"找到微信窗口 - 标题: {title}, 句柄: {hwnd}, 类名: {classname}")
        return True
    
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    if not hwnds:
        # 如果没有找到主窗口，尝试查找其他可能的微信窗口
        def backup_callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                classname = win32gui.GetClassName(hwnd)
                if 'WeChat' in classname or '微信' in title:
                    hwnds.append(hwnd)
                    print(f"找到备选微信窗口 - 标题: {title}, 句柄: {hwnd}, 类名: {classname}")
            return True
        win32gui.EnumWindows(backup_callback, hwnds)
    
    return hwnds[0] if hwnds else None

def activate_window(hwnd):
    """激活指定窗口"""
    if not hwnd:
        return False
    
    try:
        # 获取当前窗口状态
        placement = win32gui.GetWindowPlacement(hwnd)
        print(f"窗口状态: {placement}")*9
        
        # 如果窗口最小化，恢复它
        if placement[1] == win32con.SW_SHOWMINIMIZED:
            print("窗口已最小化，正在恢复...")
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        # 确保窗口可见
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        
        # 将窗口置前
        win32gui.SetForegroundWindow(hwnd)
        
        # 给窗口一些时间来响应
        time.sleep(1)
        
        # 验证窗口是否真的激活
        foreground_hwnd = win32gui.GetForegroundWindow()
        if foreground_hwnd == hwnd:
            print("窗口已成功激活")
            return True
        else:
            print(f"窗口激活失败，当前前台窗口句柄: {foreground_hwnd}")
            return False
            
    except Exception as e:
        print(f"激活窗口失败: {e}")
        return False

class WeChatBot:
    def __init__(self):
        # 初始化配置
        from config_loader import config
        
        # 设置API密钥
        api_key = config.get_secret('SILICONFLOW_API_KEY')
        if api_key:
            config.set_secret('SILICONFLOW_API_KEY', api_key)
        
        # 初始化日志
        logging.basicConfig(
            level=getattr(logging, config.get('logging', 'log_level', 'INFO')),
            format=config.get('logging', 'log_format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # 初始化知识库
        self.init_knowledge_base()
        
        # 初始化微信机器人
        logger.info("正在初始化微信机器人...")
        self.wx = WeChat()
        logger.info("微信实例创建成功")
        logger.info(f"微信初始化成功，当前共有 {len(self.wx.GetSessionList())} 个会话")
        
        # 加载环境变量和配置
        self.load_env()
        
        # 初始化 HTTP 会话
        self.session = requests.Session()
        
        # 打印环境变量（调试用）
        logger.info("=== 环境变量检查 ===")
        for key, value in os.environ.items():
            if 'API' in key or 'KEY' in key or 'TOKEN' in key:
                # 隐藏敏感信息
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '****'
                logger.info(f"{key}: {masked_value}")
        
        # 初始化对话历史记录
        self.conversation_history = {}  # 用于存储每个用户的对话历史
        self.max_history_length = 10    # 每个用户最多保存10轮对话
        
        self.vector_store_path = "knowledge_base/vector_store"
        self._last_index_mtime = None
        self._last_pkl_mtime = None
        self._start_vector_store_watcher()
        
    def load_env(self):
        """加载环境变量和配置"""
        from config_loader import config
        
        # 加载API密钥
        self.api_key = config.get_secret('SILICONFLOW_API_KEY')
        if not self.api_key:
            raise ValueError("请设置 SILICONFLOW_API_KEY 配置")
        
        # 打印API密钥前几位和后几位，中间用星号代替
        masked_key = self.api_key[:4] + '*' * 8 + self.api_key[-4:] if len(self.api_key) > 12 else self.api_key
        logger.info(f"使用的API密钥: {masked_key}")
        
        # 从配置文件加载API配置
        self.api_url = config.get('api', 'url')
        self.model = config.get('api', 'model')
        self.max_tokens = config.getint('api', 'max_tokens')
        self.temperature = config.getfloat('api', 'temperature')
        self.top_p = config.getfloat('api', 'top_p')
        self.frequency_penalty = config.getfloat('api', 'frequency_penalty')
        self.presence_penalty = config.getfloat('api', 'presence_penalty')
        self.timeout = config.getint('api', 'timeout')
        self.max_retries = config.getint('api', 'max_retries')
        self.retry_delay = config.getint('api', 'retry_delay')
        
        # 从配置文件加载聊天配置
        self.trigger = f"@{config.get('chat', 'trigger_word')}"
        self.max_history_length = config.getint('chat', 'max_history_length')
        self.check_interval = config.getint('chat', 'check_interval')
        self.message_expire_time = config.getint('chat', 'message_expire_time')
        self.max_processed_hashes = config.getint('chat', 'max_processed_hashes')
        
        # 从配置文件加载向量存储配置
        self.chunk_size = config.getint('vector_store', 'chunk_size')
        self.chunk_overlap = config.getint('vector_store', 'chunk_overlap')
        self.similarity_threshold = config.getfloat('vector_store', 'similarity_threshold')
        self.max_results = config.getint('vector_store', 'max_results')
        
        # 初始化其他变量
        self.last_message = ""
        self.error_sent = False
        self.last_check_time = time.time()
        
        logger.info("配置加载完成")
        logger.info(f"API URL: {self.api_url}")
        logger.info(f"模型: {self.model}")
        logger.info(f"触发词: {self.trigger}")
        logger.info(f"最大历史长度: {self.max_history_length}")
        logger.info(f"检查间隔: {self.check_interval}秒")
        logger.info(f"消息过期时间: {self.message_expire_time}秒")
        
    def init_knowledge_base(self):
        """初始化知识库"""
        try:
            logger.info("初始化知识库...")
            from vector_store import FaissVectorStore
            # 初始化向量存储
            self.vector_store = FaissVectorStore()
            # 尝试加载现有向量存储
            vector_store_path = "knowledge_base/vector_store"
            if os.path.exists(f"{vector_store_path}.index") and os.path.exists(f"{vector_store_path}.pkl"):
                self.vector_store.load(vector_store_path)
                logger.info("知识库加载成功")
            else:
                logger.info("知识库文件不存在，将创建新的知识库")
            # 设置知识库查询服务的向量存储（确保加载后再设置）
            knowledge_query_service.set_vector_store(self.vector_store)
            # 调试：打印所有文本块信息
            logger.info(f"微信端知识库文本块数量: {len(self.vector_store.documents)}")
            for i, (text, metadata) in enumerate(self.vector_store.documents):
                logger.info(f"块{i+1}: 来源: {metadata.get('source', '无')}, 类型: {metadata.get('type', '无')}, 内容前50: {text[:50]}")
        except Exception as e:
            logger.error(f"初始化知识库失败: {str(e)}")
            logger.error(traceback.format_exc())
            self.vector_store = None
    
    def get_ai_response(self, message):
        """生成AI回复"""
        try:
            logger.info("\n" + "="*50)
            logger.info("开始处理微信消息请求")
            logger.info("="*50)
            logger.info(f"用户查询: {message}")
            
            # 检查知识库状态
            logger.info("\n--- 步骤1: 检查知识库状态 ---")
            if not hasattr(self.vector_store, 'documents') or not self.vector_store.documents:
                logger.warning("知识库为空，将直接使用大模型回答")
                return self._get_llm_response(message, context=None)
            
            logger.info(f"知识库状态正常，当前包含 {len(self.vector_store.documents)} 条文档")
            
            # 在知识库中搜索
            logger.info("\n--- 步骤2: 搜索知识库 ---")
            try:
                logger.info("执行知识库搜索...")
                search_result = knowledge_query_service.search_for_wechat(message)
                logger.info(f"搜索完成，结果: {search_result['success']}")
            except Exception as search_error:
                logger.error("知识库搜索失败")
                logger.error(f"错误类型: {type(search_error).__name__}")
                logger.error(f"错误信息: {str(search_error)}")
                logger.error("详细错误堆栈:")
                logger.error(traceback.format_exc())
                logger.info("由于搜索失败，将直接使用大模型回答")
                return self._get_llm_response(message, context=None)
            
            if search_result['success'] and search_result['results']:
                # 记录搜索结果
                logger.info("\n--- 步骤3: 处理搜索结果 ---")
                relevant_contexts = []
                logger.info("搜索结果详情:")
                for i, result in enumerate(search_result['results']):
                    logger.info(f"\n结果 [{i+1}]:")
                    logger.info(f"相关度得分: {result['score']:.4f}")
                    logger.info(f"内容预览: {result['content'][:200]}...")
                    if 'metadata' in result:
                        logger.info(f"元数据: {result['metadata']}")
                    relevant_contexts.append(f"相关度{result['score']:.4f}: {result['content']}")
                
                # 将相关内容组合成上下文
                logger.info("\n--- 步骤4: 准备大模型上下文 ---")
                context = "\n\n".join(relevant_contexts[:3])  # 使用前3个最相关的结果
                logger.info(f"选取前 {min(3, len(relevant_contexts))} 条最相关结果作为上下文")
                logger.info("上下文预览:")
                context_preview = context[:500] + "..." if len(context) > 500 else context
                logger.info(context_preview)
                
                # 调用大模型生成最终回复
                logger.info("\n--- 步骤5: 调用大模型生成回复 ---")
                return self._get_llm_response(message, context=context)
            else:
                logger.warning("\n--- 步骤3: 未找到匹配结果 ---")
                logger.info("由于未找到相关内容，将直接使用大模型回答")
                return self._get_llm_response(message, context=None)
                
        except Exception as e:
            logger.error("\n!!! 处理请求过程中发生错误 !!!")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误信息: {str(e)}")
            logger.error("详细错误堆栈:")
            logger.error(traceback.format_exc())
            return f"抱歉，处理请求时出错: {str(e)}"

    def _get_llm_response(self, message: str, context: str = None, user_id: str = None) -> str:
        """调用大模型生成回复"""
        max_retries = 3
        retry_delay = 2  # 重试延迟秒数
        
        for attempt in range(max_retries):
            try:
                logger.info("\n" + "="*50)
                logger.info(f"开始调用大模型API (尝试 {attempt + 1}/{max_retries})")
                logger.info("="*50)
                
                # 构建系统提示词
                logger.info("\n--- 步骤1: 准备提示词 ---")
                system_prompt = prompt_manager.get_system_prompt()

                # 准备用户提示词
                # 构建历史对话字符串
                history_str = ""
                if user_id and user_id in self.conversation_history:
                    history = self.conversation_history[user_id]
                    if history:
                        for msg in history:
                            role = "用户" if msg['role'] == 'user' else "助手"
                            history_str += f"{role}：{msg['content']}\n"
                
                # 使用提示词管理器格式化用户提示词
                user_prompt = prompt_manager.format_user_prompt(
                    message=message,
                    context=context or "",
                    history=history_str
                )
                
                # 添加知识库上下文
                if context:
                    user_prompt += f"知识库相关信息：\n{context}\n\n"
                
                # 添加当前问题
                user_prompt += f"用户当前问题：{message}\n\n请基于以上信息生成回答。"
                
                # 准备请求数据
                logger.info("\n--- 步骤2: 准备API请求 ---")
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                data = {
                    'model': self.model,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    'stream': False,
                    'max_tokens': 2048,
                    'temperature': 0.7,
                    'top_p': 0.7,
                    'frequency_penalty': 0.5,
                    'presence_penalty': 0.0
                }
                
                # 打印请求信息
                logger.info("请求配置:")
                logger.info(f"API URL: {self.api_url}")
                logger.info(f"模型名称: {self.model}")
                logger.info("系统提示词预览:")
                logger.info(system_prompt)
                logger.info("用户提示词预览:")
                prompt_preview = user_prompt[:500] + "..." if len(user_prompt) > 500 else user_prompt
                logger.info(prompt_preview)
                
                # 发送请求
                logger.info("\n--- 步骤3: 发送API请求 ---")
                logger.info("正在发送请求...")
                start_time = time.time()
                
                # 添加超时设置
                response = self.session.post(
                    self.api_url, 
                    headers=headers, 
                    json=data,
                    timeout=30  # 设置30秒超时
                )
                end_time = time.time()
                
                # 打印响应信息
                logger.info("\n--- 步骤4: 处理API响应 ---")
                logger.info(f"请求耗时: {end_time - start_time:.2f} 秒")
                logger.info(f"状态码: {response.status_code}")
                
                # 检查响应状态
                if response.status_code == 500:
                    logger.warning(f"服务器返回500错误，尝试重试 ({attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        return "抱歉，服务器暂时无法响应，请稍后再试。"
                
                response.raise_for_status()
                result = response.json()
                
                # 获取AI回复
                ai_response = result['choices'][0]['message']['content']
                
                return ai_response
                
            except requests.exceptions.Timeout:
                logger.error(f"请求超时 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "抱歉，请求超时，请稍后重试。"
                
            except requests.exceptions.RequestException as e:
                logger.error(f"请求异常 (尝试 {attempt + 1}/{max_retries})")
                logger.error(f"错误信息: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "抱歉，请求失败，请稍后重试。"
                
            except Exception as e:
                logger.error(f"处理请求时出错 (尝试 {attempt + 1}/{max_retries})")
                logger.error(f"错误类型: {type(e).__name__}")
                logger.error(f"错误信息: {str(e)}")
                logger.error("详细错误堆栈:")
                logger.error(traceback.format_exc())
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return "抱歉，处理请求时出错，请稍后重试。"
        
        return "抱歉，多次尝试后仍然无法获取回复，请稍后重试。"

    def send_message(self, message):
        """发送消息"""
        try:
            # 使用微信的SendMsg方法发送消息
            self.wx.SendMsg(message)
            logger.info(f"消息发送成功: {message}")
            return True
        except Exception as e:
            logger.error(f"消息发送失败: {e}")
            return False

    def extract_message_content(self, message):
        """提取消息内容"""
        try:
            content = str(message)
            sender = None
            
            # 尝试获取发送者信息
            try:
                if hasattr(message, 'sender'):
                    sender = message.sender
                else:
                    parts = content.split(':', 1)
                    if len(parts) > 1:
                        sender = parts[0].strip()
            except Exception as e:
                logger.error(f"获取发送者信息失败: {e}")
            
            if content:
                # 检查消息是否包含触发词
                if self.trigger in content:
                    logger.info(f"- 检测到{self.trigger}标记")
                    # 提取触发词后面的实际消息内容
                    try:
                        # 尝试按空格分割获取实际消息
                        parts = content.split(self.trigger, 1)
                        if len(parts) > 1:
                            actual_message = parts[1].strip()
                            if actual_message:
                                logger.info(f"- 提取到的消息内容: {actual_message}")
                                return {
                                    'content': actual_message,
                                    'sender': sender
                                }
                            else:
                                logger.warning("- 提取到的消息内容为空")
                        else:
                            logger.warning("- 无法分割消息内容")
                    except Exception as e:
                        logger.error(f"- 提取{self.trigger}消息内容失败: {e}")
                else:
                    logger.info(f"- 消息未包含{self.trigger}标记")
                
                logger.info(f"消息未{self.trigger}或格式不正确，忽略")
                return None
        except Exception as e:
            logger.error(f"提取消息内容时出错: {e}")
            logger.debug(f"消息对象类型: {type(message)}")
            logger.debug(f"消息对象内容: {message}")
            return None

    def monitor_messages(self):
        """监控并处理新消息，支持多轮上下文（5轮），优先查知识库"""
        logger.info("\n=== 开始监听消息 ===")
        logger.info("- 提示：在当前聊天窗口中@auto发送消息来与机器人对话")
        logger.info(f"- 提示：每{self.check_interval}秒检查一次当前窗口的未读消息")
        logger.info(f"- 提示：只处理{self.message_expire_time}秒内的未读未回复消息")
        logger.info("- 按Ctrl+C可以停止程序\n")
        
        processed_hashes = set()
        last_check_time = time.time()
        
        # 从配置文件获取指代词列表
        pronouns = config.get('chat', 'pronouns').split(',')
        logger.info(f"已加载指代词列表: {pronouns}")
        
        def get_message_hash(msg_str, sender=None, msg_time=None):
            if '@auto' in msg_str:
                content = msg_str.split('@auto', 1)[1].strip()
            else:
                content = msg_str
            hash_content = f"{sender}:{content}:{msg_time}" if sender else f"{content}:{msg_time}"
            return hash(hash_content)
        
        try:
            while True:
                try:
                    current_time = time.time()
                    if current_time - last_check_time < self.check_interval:
                        time.sleep(1)
                        continue
                    last_check_time = current_time
                    logger.info(f"\n=== 检查新消息 [{time.strftime('%Y-%m-%d %H:%M:%S')}] ===")
                    messages = self.wx.GetAllMessage()
                    if not messages or not isinstance(messages, list):
                        continue
                    for msg in reversed(messages):
                        try:
                            msg_str = str(msg)
                            if '@auto' not in msg_str:
                                continue
                            sender = None
                            try:
                                if hasattr(msg, 'sender'):
                                    sender = msg.sender
                                else:
                                    parts = msg_str.split(':', 1)
                                    if len(parts) > 1:
                                        sender = parts[0].strip()
                            except Exception as e:
                                logger.warning(f"获取发送者信息失败: {e}")
                                continue
                            msg_time = None
                            try:
                                time_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', msg_str)
                                if time_match:
                                    msg_time = time.mktime(time.strptime(time_match.group(), "%Y-%m-%d %H:%M:%S"))
                                else:
                                    msg_time = current_time
                            except:
                                msg_time = current_time
                            msg_hash = get_message_hash(msg_str, sender, msg_time)
                            if msg_hash in processed_hashes:
                                continue
                            if current_time - msg_time > self.message_expire_time:
                                logger.info("跳过超过过期时间的消息")
                                processed_hashes.add(msg_hash)
                                continue
                            has_reply = False
                            reply_pattern = f"@{sender}" if sender else None
                            if reply_pattern:
                                for reply in messages[messages.index(msg)+1:]:
                                    if reply_pattern in str(reply):
                                        has_reply = True
                                        break
                            if has_reply:
                                logger.info("跳过已回复的消息")
                                processed_hashes.add(msg_hash)
                                continue
                            logger.info(f"\n收到新消息: {msg_str}")
                            logger.info(f"- 消息时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg_time))}")
                            actual_message = msg_str.split('@auto', 1)[1].strip()
                            if actual_message:
                                logger.info(f"- 消息内容: {actual_message}")
                                logger.info(f"- 发送者: {sender if sender else '未知'}")
                                user_id = sender or 'unknown'
                                if user_id not in self.conversation_history:
                                    self.conversation_history[user_id] = []
                                self.conversation_history[user_id].append({'role': 'user', 'content': actual_message})
                                self.conversation_history[user_id] = self.conversation_history[user_id][-self.max_history_length*2:]
                                
                                # 搜索知识库
                                kb_context = None
                                try:
                                    # 使用知识库查询服务进行带上下文的搜索
                                    search_result = knowledge_query_service.search_with_context(
                                        query=actual_message,
                                        user_id=user_id,
                                        conversation_history=self.conversation_history[user_id],
                                        pronouns=pronouns
                                    )
                                    
                                    if search_result['success']:
                                        # 记录搜索结果
                                        logger.info(f"知识库搜索结果数量: {len(search_result['results'])}")
                                        for i, result in enumerate(search_result['results'][:self.max_results]):
                                            logger.info(f"结果 {i+1} (相关度: {result['score']:.4f}): {result['content'][:200]}...")
                                        
                                        kb_context = search_result['kb_context']
                                    else:
                                        logger.warning(f"知识库检索失败: {search_result.get('error', '未知错误')}")
                                        
                                except Exception as e:
                                    logger.warning(f"知识库检索异常: {e}")
                                
                                # 生成回复
                                response = self._get_llm_response(actual_message, context=kb_context, user_id=user_id)
                                self.conversation_history[user_id].append({'role': 'assistant', 'content': response})
                                self.conversation_history[user_id] = self.conversation_history[user_id][-self.max_history_length*2:]
                                
                                if sender:
                                    full_response = f"@{sender} {response}"
                                else:
                                    full_response = response
                                logger.info(f"\n生成的回复: {full_response}")
                                if self.send_message(full_response):
                                    processed_hashes.add(msg_hash)
                            else:
                                error_msg = f"@{sender} 抱歉，我暂时无法回答这个问题。" if sender else "抱歉，我暂时无法回答这个问题。"
                                logger.info(f"\n发送错误提示: {error_msg}")
                                if self.send_message(error_msg):
                                    processed_hashes.add(msg_hash)
                        except Exception as e:
                            logger.error(f"处理消息时出错: {str(e)}")
                            logger.error(traceback.format_exc())
                            continue
                    if len(processed_hashes) > self.max_processed_hashes:
                        current_time = time.time()
                        processed_hashes = {h for h in processed_hashes if h > hash(str(current_time - self.message_expire_time))}
                        logger.info(f"清理消息历史记录，剩余 {len(processed_hashes)} 条记录")
                except Exception as e:
                    logger.error(f"\n获取消息时出错: {str(e)}")
                    logger.error(traceback.format_exc())
                    time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("\n收到停止信号，程序退出")

    def handle_message(self, message: str, sender: str) -> str:
        """处理接收到的消息"""
        print(f"\n=== 处理新消息 ===")
        print(f"发送者: {sender}")
        print(f"消息内容: {message}")
        
        try:
            # 如果消息与上一条相同，直接返回
            if message == self.last_message:
                print("消息与上一条相同，跳过处理")
                return None
            self.last_message = message
            
            # 生成回复
            print("\n=== 开始生成回复 ===")
            print("1. 尝试使用知识库...")
            response = self.vector_store.search(message)
            
            # 如果回复为空或者是错误消息，尝试使用大模型
            if not response or "出错" in response:
                print("\n2. 知识库查询失败，尝试使用大模型...")
                response = self._get_llm_response(message, user_id=sender)
            else:
                print("\n2. 知识库查询成功，使用知识库的回复")
                response = self._get_llm_response(message, context=response, user_id=sender)
            
            print(f"\n=== 最终回复 ===\n{response}")
            return f"@{sender} {response}"
            
        except Exception as e:
            error_msg = f"处理消息时出错: {str(e)}"
            print(f"\n错误：{error_msg}")
            return f"@{sender} 抱歉，{error_msg}"

    def _start_vector_store_watcher(self, interval=30):
        def watcher():
            import os
            import time
            while True:
                try:
                    index_file = f"{self.vector_store_path}.index"
                    pkl_file = f"{self.vector_store_path}.pkl"
                    index_mtime = os.path.getmtime(index_file) if os.path.exists(index_file) else None
                    pkl_mtime = os.path.getmtime(pkl_file) if os.path.exists(pkl_file) else None
                    changed = []
                    if index_mtime != self._last_index_mtime:
                        changed.append(f"index文件: {self._last_index_mtime} -> {index_mtime}")
                    if pkl_mtime != self._last_pkl_mtime:
                        changed.append(f"pkl文件: {self._last_pkl_mtime} -> {pkl_mtime}")
                    if changed:
                        logger.info("检测到知识库文件变更，自动重新加载向量库... 变动详情: " + "; ".join(changed))
                        self.vector_store.load(self.vector_store_path)
                        knowledge_query_service.set_vector_store(self.vector_store)
                        self._last_index_mtime = index_mtime
                        self._last_pkl_mtime = pkl_mtime
                        logger.info("微信端知识库已自动热加载最新内容。")
                except Exception as e:
                    logger.error(f"热加载知识库失败: {e}")
                time.sleep(interval)
        t = threading.Thread(target=watcher, daemon=True)
        t.start()

def main():
    try:
        print("\n=== 微信机器人启动 ===")
        print("- 初始化机器人...")
        bot = WeChatBot()
        
        # 开始监听消息
        bot.monitor_messages()
                
    except Exception as e:
        print(f"\n程序启动失败: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()

if __name__ == "__main__":
    main()