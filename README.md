# WeChat Bot with Knowledge Base Integration

一个基于大语言模型的智能问答机器人，集成了本地知识库检索功能，支持 Web 界面和微信接口。

## 功能特点

### 1. 智能微信机器人
- 基于 itchat/wxpy 实现微信消息自动获取
- 支持私聊和群聊消息处理
- 自动维护微信登录状态
- 支持消息队列，防止消息丢失
- 智能限流，防止触发微信安全机制

### 2. 混合智能问答
- 结合本地知识库检索和大语言模型能力
- 优先从知识库中检索相关内容（Top-K 检索 + 相似度过滤）
- 使用大语言模型对检索结果进行加工和补充
- 当知识库无相关内容时自动切换为纯大模型回答
- 支持多轮对话上下文维护

### 3. 知识库管理
- 支持文档导入和向量化存储
- 使用 FAISS 进行高效的向量检索
- 支持文档的批量导入和更新
- 自动文本分段和向量化处理
- 支持增量更新和文档版本管理

### 4. 系统特性
- 详细的日志记录系统
- 灵活的配置管理
- 完善的错误处理机制
- 支持自定义提示词模板
- 分布式部署支持

## 技术架构

### 1. 微信消息处理
- **消息获取**: itchat/wxpy
- **消息队列**: Redis
- **并发处理**: asyncio
- **状态管理**: SQLite/Redis
- **限流机制**: Token Bucket 算法

### 2. 知识库系统
- **向量数据库**: FAISS
- **文本分词**: jieba
- **文本向量化**: 
  * Sentence Transformers
  * 支持模型：
    - text2vec-base-chinese
    - m3e-base
    - bge-base-zh
- **文档处理**:
  * 支持格式：TXT、PDF、DOCX、MD
  * 分段策略：按段落/按字数/按语义
  * 去重策略：MinHash + LSH

### 3. 大语言模型集成
- **模型支持**:
  * ChatGPT (GPT-3.5/GPT-4)
  * Claude
  * 文心一言
  * 讯飞星火
  * 智谱 ChatGLM
- **API 封装**:
  * 统一的接口抽象
  * 自动重试机制
  * 负载均衡
  * 模型回退策略
- **上下文管理**:
  * 滑动窗口机制
  * 基于 Redis 的分布式存储
  * 会话超时自动清理

### 4. 提示词工程
- **系统提示词模板**:
```python
SYSTEM_PROMPT = """你是一个专业、友好的AI助手。请基于提供的相关信息回答用户的问题。
如果相关信息不足以完整回答问题，你可以：
1. 使用已有信息回答问题的相关部分
2. 明确指出哪些部分缺少信息
3. 建议用户如何获取更多信息

请用简洁专业的语言回答，确保回答准确、有帮助且易于理解。"""
```

- **知识库集成提示词**:
```python
KNOWLEDGE_PROMPT = """请基于以下相关信息回答问题。

相关信息：
{context}

用户问题：{query}

请生成专业、准确的回答。如果信息不足，请说明。"""
```

## 部署指南

### 环境要求
- Python 3.8+
- FAISS 向量库
- Redis (可选，用于消息队列和分布式部署)
- SQLite/MySQL (用于状态管理)
- 微信接入相关依赖

### 安装步骤

1. 克隆仓库
```bash
git clone [repository_url]
cd wechat-bot
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
# 配置大语言模型 API
export LLM_API_KEY=your_api_key
export LLM_API_URL=your_api_url

# 配置向量库路径
export VECTOR_STORE_PATH=path/to/vector/store

# 配置Redis（可选）
export REDIS_URL=redis://localhost:6379/0
```

### 配置说明

1. 微信机器人配置
```python
WECHAT_CONFIG = {
    'auto_reply_all': False,  # 是否自动回复所有消息
    'reply_groups': [],  # 允许回复的群组列表
    'reply_delay': 1,  # 回复延迟（秒）
    'max_queue_size': 100,  # 消息队列最大长度
    'rate_limit': {  # 限流配置
        'capacity': 60,
        'rate': 1
    }
}
```

2. 知识库配置
```python
VECTOR_STORE_CONFIG = {
    'dimension': 1536,  # 向量维度
    'similarity_threshold': 0.6,  # 相似度阈值
    'top_k': 3,  # 返回结果数量
    'index_type': 'IVFFlat',  # FAISS索引类型
    'nlist': 100  # 聚类中心数量
}
```

3. 大语言模型配置
```python
LLM_CONFIG = {
    'model': 'gpt-3.5-turbo',  # 模型名称
    'temperature': 0.7,  # 温度参数
    'max_tokens': 2048,  # 最大token数
    'retry': {  # 重试配置
        'max_retries': 3,
        'delay': 1
    },
    'timeout': 30  # 超时时间（秒）
}
```

## 使用流程

### 1. 启动微信机器人
```bash
python wechat_bot.py
```

### 2. 扫码登录
- 首次启动时需要扫码登录
- 支持热登录，避免频繁扫码
- 自动保存登录状态

### 3. 消息处理流程

1. 接收消息
```python
@bot.register(msg_types=SUPPORTED_MSG_TYPES)
def handle_message(msg):
    # 1. 消息预处理
    if not should_reply(msg):
        return
    
    # 2. 加入消息队列
    message_queue.put(msg)
```

2. 知识库检索
```python
def search_knowledge_base(query):
    # 1. 向量化查询
    query_vector = embeddings.encode(query)
    
    # 2. FAISS检索
    results = vector_store.search(query_vector, top_k=3)
    
    # 3. 相似度过滤
    filtered_results = [r for r in results if r[1] >= 0.6]
    
    return filtered_results
```

3. 大模型调用
```python
def get_llm_response(query, context=None):
    # 1. 构建提示词
    if context:
        prompt = KNOWLEDGE_PROMPT.format(
            context=context,
            query=query
        )
    else:
        prompt = query
    
    # 2. 调用API
    response = llm_client.chat.completions.create(
        model=LLM_CONFIG['model'],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content
```

### 4. 日志示例

```
=== 开始处理微信消息请求 ===
用户查询: 如何使用知识库系统？

--- 步骤1: 检查知识库状态 ---
知识库状态正常，当前包含 100 条文档

--- 步骤2: 搜索知识库 ---
执行向量搜索...
找到 3 个相关结果

结果 [1]:
相关度得分: 0.8956
内容预览: 知识库系统使用说明...

--- 步骤3: 调用大模型生成回复 ---
请求配置:
API URL: https://api.openai.com/v1/chat/completions
模型名称: gpt-3.5-turbo

生成回复成功
处理完成
=== 结束请求处理 ===
```

## 性能优化

1. 向量检索优化
- FAISS IVF 索引
- 异步预加载
- 批量检索

2. 大模型调用优化
- 连接池
- 结果缓存
- 并发请求

3. 内存优化
- 向量量化
- 文档分片
- 定期清理

## 常见问题

1. 知识库检索失败
   - 检查向量库文件是否完整
   - 确认文档格式是否正确
   - 查看详细错误日志

2. 大模型调用失败
   - 验证 API 密钥是否正确
   - 检查网络连接状态
   - 确认请求参数格式

3. 微信连接问题
   - 确保微信客户端正常登录
   - 检查相关依赖是否安装
   - 查看连接日志

## 开发计划

- [ ] 支持更多文档格式
- [ ] 优化检索算法
- [ ] 添加用户反馈机制
- [ ] 增强错误处理
- [ ] 支持更多对话模型
- [ ] 添加管理后台
- [ ] 优化分布式部署
- [ ] 增加数据分析功能

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。 
