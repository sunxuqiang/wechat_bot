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
from dotenv import load_dotenv
from knowledge_bot import KnowledgeBot
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 打印当前工作目录
print(f"当前工作目录: {os.getcwd()}")

# 检查.env文件
env_path = Path('.env')
print(f".env文件路径: {env_path.absolute()}")
print(f".env文件是否存在: {env_path.exists()}")

# 直接从.env文件读取API密钥
api_key = None
if env_path.exists():
    print("\n.env文件内容预览:")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('SILICONFLOW_API_KEY='):
                api_key = line.strip().split('=', 1)[1]
                masked_key = api_key[:4] + '*' * 8 + api_key[-4:] if len(api_key) > 12 else api_key
                print(f"从.env文件读取到API密钥: {masked_key}")
                # 直接设置环境变量
                os.environ['SILICONFLOW_API_KEY'] = api_key
                break

if not api_key:
    raise ValueError("无法从.env文件读取API密钥")

# 加载其他环境变量
load_dotenv()

# 打印所有环境变量
print("\n环境变量:")
for key, value in os.environ.items():
    if 'KEY' in key:  # 只打印包含 'KEY' 的环境变量，并且隐藏具体值
        masked_value = value[:4] + '*' * 8 + value[-4:] if len(value) > 12 else value
        print(f"{key}: {masked_value}")

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
        """初始化微信机器人"""
        logger.info("正在初始化微信机器人...")
        self.wx = WeChat()
        logger.info("微信实例创建成功")
        logger.info(f"微信初始化成功，当前共有 {len(self.wx.GetSessionList())} 个会话")
        
        # 加载环境变量
        self.load_env()
        
        # 初始化知识库
        self.init_knowledge_base()
        
        # 初始化 HTTP 会话
        self.session = requests.Session()
        
    def load_env(self):
        """加载环境变量"""
        self.api_key = os.getenv('SILICONFLOW_API_KEY')  # 从环境变量获取API密钥
        if not self.api_key:
            raise ValueError("请设置 SILICONFLOW_API_KEY 环境变量")
            
        # 打印API密钥前几位和后几位，中间用星号代替
        masked_key = self.api_key[:4] + '*' * 8 + self.api_key[-4:] if len(self.api_key) > 12 else self.api_key
        logger.info(f"使用的API密钥: {masked_key}")
            
        self.api_url = 'https://api.siliconflow.cn/v1/chat/completions'  # 使用正确的 API URL
        self.model = 'deepseek-ai/DeepSeek-R1-0528-Qwen3-8B'  # 使用正确的模型名称
        self.last_message = ""
        self.error_sent = False
        self.last_check_time = time.time()
        
    def init_knowledge_base(self):
        """初始化知识库"""
        try:
            logger.info("=== 初始化知识库 ===")
            
            # 使用与前端相同的向量存储实例
            from vector_store import FaissVectorStore
            self.vector_store = FaissVectorStore()  # 会返回相同的实例
            
            # 检查知识库文件是否存在
            kb_path = os.path.join('knowledge_base', 'vector_store')  # 使用与前端相同的路径
            if os.path.exists(f"{kb_path}.pkl"):
                logger.info(f"找到知识库文件: {kb_path}")
                try:
                    self.vector_store.load(kb_path)
                    logger.info(f"成功加载知识库文件")
                except Exception as e:
                    logger.error(f"加载知识库文件失败: {str(e)}")
                    logger.error(traceback.format_exc())
            else:
                logger.warning(f"知识库文件不存在: {kb_path}")
            
            logger.info("成功连接到全局知识库实例")
            logger.info(f"当前知识库包含 {len(self.vector_store.documents)} 条文档")
            
            # 打印知识库内容预览
            if len(self.vector_store.documents) > 0:
                logger.info("知识库内容预览:")
                for i, (text, metadata) in enumerate(self.vector_store.documents[:5]):  # 只显示前5条
                    preview = text[:100] + "..." if len(text) > 100 else text
                    logger.info(f"文档[{i}]: {preview}")
            else:
                logger.warning("知识库为空，请先添加文档")
            
        except Exception as e:
            logger.error("=== 详细错误信息 ===")
            logger.error(traceback.format_exc())
            raise e
    
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
                # 使用多级相似度阈值
                thresholds = [0.05, 0.03, 0.01]  # 从相对严格到宽松
                best_results = None
                best_threshold = None
                
                for threshold in thresholds:
                    logger.info(f"\n尝试相似度阈值: {threshold}")
                    self.vector_store.similarity_threshold = threshold
                    
                    try:
                        current_results = self.vector_store.search(message)
                        if current_results:
                            logger.info(f"在阈值 {threshold} 下找到 {len(current_results)} 个结果")
                            # 如果是第一次找到内容，或者当前内容更相关（基于长度），则更新
                            if not best_results or len(current_results) > len(best_results):
                                best_results = current_results
                                best_threshold = threshold
                                logger.info(f"更新为当前最佳结果")
                    except Exception as search_error:
                        logger.error(f"在阈值 {threshold} 下搜索失败: {str(search_error)}")
                        continue
                
                if not best_results:
                    logger.warning("\n在所有阈值下都没有找到相关内容")
                    return self._get_llm_response(message, context=None)
                
                # 记录最佳搜索结果
                logger.info(f"\n--- 步骤3: 处理搜索结果 ---")
                logger.info(f"使用最佳阈值 {best_threshold} 的搜索结果:")
                relevant_contexts = []
                for i, (text, score, metadata) in enumerate(best_results):
                    logger.info(f"\n结果 [{i+1}]:")
                    logger.info(f"相关度得分: {score:.4f}")
                    logger.info(f"内容预览: {text[:200]}...")
                    if metadata:
                        logger.info(f"元数据: {metadata}")
                    relevant_contexts.append(f"相关度{score:.4f}: {text}")
                
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
                
            except Exception as search_error:
                logger.error("知识库搜索失败")
                logger.error(f"错误类型: {type(search_error).__name__}")
                logger.error(f"错误信息: {str(search_error)}")
                logger.error("详细错误堆栈:")
                logger.error(traceback.format_exc())
                logger.info("由于搜索失败，将直接使用大模型回答")
                return self._get_llm_response(message, context=None)
                
        except Exception as e:
            logger.error("\n!!! 处理请求过程中发生错误 !!!")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误信息: {str(e)}")
            logger.error("详细错误堆栈:")
            logger.error(traceback.format_exc())
            return f"抱歉，处理请求时出错: {str(e)}"

    def _get_llm_response(self, message: str, context: str = None) -> str:
        """调用大模型生成回复"""
        try:
            logger.info("\n" + "="*50)
            logger.info("开始调用大模型API")
            logger.info("="*50)
            
            # 构建系统提示词
            logger.info("\n--- 步骤1: 准备提示词 ---")
            system_prompt = """你是一个专业、友好的AI助手。请基于提供的相关信息回答用户的问题。
如果相关信息不足以完整回答问题，你可以：
1. 使用已有信息回答问题的相关部分
2. 明确指出哪些部分缺少信息
3. 建议用户如何获取更多信息

请用简洁专业的语言回答，确保回答准确、有帮助且易于理解。"""

            # 准备用户提示词
            if context:
                logger.info("使用知识库上下文构建提示词")
                user_prompt = f"""请基于以下相关信息回答问题。

相关信息：
{context}

用户问题：{message}

请生成专业、准确的回答。如果信息不足，请说明。"""
            else:
                logger.info("无知识库上下文，直接使用用户问题")
                user_prompt = message

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
            response = self.session.post(self.api_url, headers=headers, json=data)
            end_time = time.time()
            
            # 打印响应信息
            logger.info("\n--- 步骤4: 处理API响应 ---")
            logger.info(f"请求耗时: {end_time - start_time:.2f} 秒")
            logger.info(f"状态码: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                answer = result['choices'][0]['message']['content']
                logger.info("\n--- 步骤5: 生成回复成功 ---")
                logger.info("回复内容:")
                logger.info(answer)
                logger.info("\n" + "="*50)
                logger.info("处理完成")
                logger.info("="*50)
                return answer
            else:
                error_msg = "API返回的数据格式不正确"
                logger.error(f"\n!!! {error_msg} !!!")
                logger.error(f"API响应内容: {result}")
                return f"抱歉，{error_msg}"
                
        except Exception as e:
            error_msg = f"调用大模型出错: {str(e)}"
            logger.error("\n!!! API调用失败 !!!")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误信息: {str(e)}")
            logger.error("详细错误堆栈:")
            logger.error(traceback.format_exc())
            return f"抱歉，{error_msg}"

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
        """从消息对象中提取文本内容和发送者信息"""
        try:
            logger.info("开始提取消息内容...")
            # 检查是否是消息对象
            if hasattr(message, 'content') and hasattr(message, 'sender'):
                # 获取消息内容和发送者
                content = message.content
                sender = message.sender
                logger.info(f"- 原始发送者: {sender}")
                logger.info(f"- 原始消息内容: {content}")
                
                # 检查消息是否@了auto
                if '@auto' in content:
                    logger.info("- 检测到@auto标记")
                    # 提取@auto后面的实际消息内容
                    try:
                        # 尝试按空格分割获取实际消息
                        parts = content.split('@auto', 1)
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
                        logger.error(f"- 提取@auto消息内容失败: {e}")
                else:
                    logger.info("- 消息未包含@auto标记")
                
                logger.info("消息未@auto或格式不正确，忽略")
                return None
                    
            else:
                logger.warning(f"未知的消息类型: {type(message)}")
                logger.debug(f"消息对象的属性: {dir(message)}")
                return None
        except Exception as e:
            logger.error(f"提取消息内容时出错: {e}")
            logger.debug(f"消息对象类型: {type(message)}")
            logger.debug(f"消息对象内容: {message}")
            return None

    def monitor_messages(self):
        """监控并处理新消息"""
        logger.info("\n=== 开始监听消息 ===")
        logger.info("- 提示：在当前聊天窗口中@auto发送消息来与机器人对话")
        logger.info("- 提示：每10秒检查一次当前窗口的未读消息")
        logger.info("- 提示：只处理10分钟内的未读未回复消息")
        logger.info("- 按Ctrl+C可以停止程序\n")
        
        # 用于存储已处理的消息的哈希值
        processed_hashes = set()
        last_check_time = time.time()  # 记录上次检查时间
        
        def get_message_hash(msg_str, sender=None, msg_time=None):
            """生成消息的唯一标识"""
            # 提取@auto后面的实际内容
            if '@auto' in msg_str:
                content = msg_str.split('@auto', 1)[1].strip()
            else:
                content = msg_str
            
            # 组合发送者、内容和时间生成唯一标识
            hash_content = f"{sender}:{content}:{msg_time}" if sender else f"{content}:{msg_time}"
            return hash(hash_content)
        
        try:
            while True:
                try:
                    current_time = time.time()
                    
                    # 每10秒检查一次消息
                    if current_time - last_check_time < 10:
                        time.sleep(1)
                        continue
                    
                    # 更新检查时间
                    last_check_time = current_time
                    print(f"\n=== 检查新消息 [{time.strftime('%Y-%m-%d %H:%M:%S')}] ===")
                    
                    # 获取当前活动窗口的所有消息
                    messages = self.wx.GetAllMessage()
                    if not messages or not isinstance(messages, list):
                        continue
                    
                    # 处理消息
                    for msg in reversed(messages):  # 从最新的消息开始处理
                        try:
                            # 将消息转换为字符串用于比较
                            msg_str = str(msg)
                            
                            # 如果消息不包含@auto，跳过
                            if '@auto' not in msg_str:
                                continue
                            
                            # 获取发送者信息
                            sender = None
                            try:
                                if hasattr(msg, 'sender'):
                                    sender = msg.sender
                                else:
                                    parts = msg_str.split(':', 1)
                                    if len(parts) > 1:
                                        sender = parts[0].strip()
                            except Exception as e:
                                print(f"获取发送者信息失败: {e}")
                                continue
                            
                            # 获取消息时间
                            msg_time = None
                            try:
                                time_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', msg_str)
                                if time_match:
                                    msg_time = time.mktime(time.strptime(time_match.group(), "%Y-%m-%d %H:%M:%S"))
                                else:
                                    msg_time = current_time
                            except:
                                msg_time = current_time
                            
                            # 生成消息哈希
                            msg_hash = get_message_hash(msg_str, sender, msg_time)
                            
                            # 检查是否已处理过
                            if msg_hash in processed_hashes:
                                continue
                            
                            # 检查消息是否在10分钟内
                            if current_time - msg_time > 600:  # 600秒 = 10分钟
                                print(f"跳过超过10分钟的消息")
                                processed_hashes.add(msg_hash)
                                continue
                            
                            # 检查消息是否已经有回复
                            has_reply = False
                            reply_pattern = f"@{sender}" if sender else None
                            if reply_pattern:
                                for reply in messages[messages.index(msg)+1:]:
                                    if reply_pattern in str(reply):
                                        has_reply = True
                                        break
                            
                            if has_reply:
                                print(f"跳过已回复的消息")
                                processed_hashes.add(msg_hash)
                                continue
                            
                            # 处理新消息
                            print(f"\n收到新消息: {msg_str}")
                            print(f"- 消息时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg_time))}")
                            
                            # 提取@auto后面的实际消息内容
                            actual_message = msg_str.split('@auto', 1)[1].strip()
                            if actual_message:
                                print(f"- 消息内容: {actual_message}")
                                print(f"- 发送者: {sender if sender else '未知'}")
                                
                                # 生成回复
                                response = self.get_ai_response(actual_message)
                                if response:
                                    # 在回复前添加@发送者
                                    if sender:
                                        full_response = f"@{sender} {response}"
                                    else:
                                        full_response = response
                                        
                                    print(f"\n生成的回复: {full_response}")
                                    # 发送回复
                                    if self.send_message(full_response):
                                        processed_hashes.add(msg_hash)
                                else:
                                    error_msg = f"@{sender} 抱歉，我暂时无法回答这个问题。" if sender else "抱歉，我暂时无法回答这个问题。"
                                    print(f"\n发送错误提示: {error_msg}")
                                    if self.send_message(error_msg):
                                        processed_hashes.add(msg_hash)
                        
                        except Exception as e:
                            print(f"处理消息时出错: {str(e)}")
                            traceback.print_exc()
                            continue
                    
                    # 定期清理过期的消息记录
                    if len(processed_hashes) > 1000:
                        # 只保留最近10分钟内的消息哈希
                        current_time = time.time()
                        processed_hashes = {h for h in processed_hashes if h > hash(str(current_time - 600))}
                        print(f"清理消息历史记录，剩余 {len(processed_hashes)} 条记录")
                    
                except Exception as e:
                    print(f"\n获取消息时出错: {str(e)}")
                    traceback.print_exc()
                    time.sleep(10)  # 出错后等待10秒再继续
                
        except KeyboardInterrupt:
            print("\n收到停止信号，程序退出")

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
                response = self._get_llm_response(message)
            else:
                print("\n2. 知识库查询成功，使用知识库的回复")
            
            print(f"\n=== 最终回复 ===\n{response}")
            return f"@{sender} {response}"
            
        except Exception as e:
            error_msg = f"处理消息时出错: {str(e)}"
            print(f"\n错误：{error_msg}")
            return f"@{sender} 抱歉，{error_msg}"

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