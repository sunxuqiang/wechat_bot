# WeChat Knowledge Base Bot

一个基于RAG（检索增强生成）技术的智能问答机器人，支持微信和Web双端交互，具备完整的知识库管理和智能问答功能。

## 🚀 项目特性

### 核心功能
- **RAG架构**: 基于向量检索和大语言模型的智能问答系统
- **双端支持**: 微信机器人 + Web管理界面
- **多格式文档**: 支持PDF、Word、Excel、PPT、TXT等多种格式
- **智能分块**: 支持传统分块和AI智能分块两种模式
- **权限管理**: 完整的用户权限控制系统
- **实时监控**: 知识库状态实时监控和统计

### 技术特性
- **混合搜索**: 向量相似度 + 关键词匹配的混合检索策略
- **自适应阈值**: 多级相似度阈值自适应调整
- **上下文感知**: 支持对话历史和上下文理解
- **高可用性**: 完善的错误处理和重试机制
- **性能优化**: 向量索引优化和批量处理

## 🏗️ 系统架构

### RAG流程
```
用户提问 → 向量化 → 知识库检索 → 上下文构建 → 大模型生成 → 智能回答
    ↓
文档上传 → 智能分块 → 向量化存储 → 知识库更新
```

### 核心组件
- **向量存储**: FAISS + Sentence Transformers
- **文档处理**: 多格式文档解析器
- **知识检索**: 混合搜索算法
- **大语言模型**: DeepSeek API集成
- **Web框架**: Flask + SQLAlchemy
- **微信集成**: wxauto + win32api

### 技术栈
- **后端**: Python 3.8+, Flask, SQLAlchemy
- **向量化**: text2vec-base-chinese, FAISS
- **文档处理**: PyPDF2, python-docx, openpyxl
- **AI模型**: DeepSeek-R1-0528-Qwen3-8B
- **数据库**: SQLite
- **前端**: HTML5, Bootstrap, JavaScript

## 📁 项目结构

```
wechat-bot/
├── app.py                          # Flask主应用
├── wechat_bot.py                   # 微信机器人
├── web_interface.py                # Web界面
├── knowledge_query_service.py      # 知识库查询服务
├── vector_store.py                 # 向量存储管理
├── document_processor.py           # 文档处理器
├── file_processors/                # 文件处理器
│   ├── base_processor.py          # 基础处理器
│   ├── pdf_processor.py           # PDF处理器
│   ├── word_processor.py          # Word处理器
│   ├── excel_processor.py         # Excel处理器
│   └── text_processor.py          # 文本处理器
├── knowledge_base/                 # 知识库存储
│   ├── docs/                      # 文档存储
│   ├── vector_store.index         # FAISS索引
│   └── vector_store.pkl           # 向量数据
├── uploads/                       # 上传文件目录
├── templates/                     # Web模板
├── static/                        # 静态资源
├── config.conf                    # 配置文件
└── requirements.txt               # 依赖包
```

## 🛠️ 安装部署

### 环境要求
- **操作系统**: Windows 10/11（微信客户端支持）
- **Python**: 3.8+
- **内存**: 8GB+ 推荐
- **存储**: 10GB+ 可用空间
- **GPU**: 支持CUDA的GPU（可选，用于加速）

### 快速开始

1. **克隆项目**
```bash
git clone <repository-url>
cd wechat-bot
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
```bash
# 复制配置文件
cp config.example.conf config.conf

# 编辑配置文件
# 设置API密钥和其他必要配置
```

4. **初始化数据库**
```bash
python app.py
```

5. **启动服务**
```bash
# 启动Web服务
python web_interface.py

# 启动微信机器人（新终端）
python wechat_bot.py
```

### 配置说明

#### 核心配置项
```ini
[api]
url = https://api.siliconflow.cn/v1/chat/completions
model = deepseek-ai/DeepSeek-R1-0528-Qwen3-8B
siliconflow_api_key = your-api-key-here

[vector_store]
similarity_threshold = 0.7
max_results = 10
chunk_size = 1000
chunk_overlap = 200

[model]
model_name = text2vec-base-chinese
device = auto
```

## 📖 使用指南

### Web界面功能

1. **知识库管理**
   - 文档上传和管理
   - 批量删除和编辑
   - 知识库统计信息

2. **智能问答**
   - 实时知识检索
   - 搜索结果展示
   - 相关度评分

3. **系统管理**
   - 用户权限管理
   - 提示词配置
   - 系统监控

### 微信机器人功能

1. **自动回复**
   - 基于知识库的智能问答
   - 上下文感知对话
   - 多轮对话支持

2. **触发机制**
   - 自动触发模式
   - 关键词触发
   - 手动触发

## 🔧 高级功能

### AI智能分块
- 支持AI辅助的智能文档分块
- 可配置分块参数和策略
- 提升分块质量和相关性

### 混合搜索算法
- 向量相似度搜索
- 关键词匹配
- TF-IDF权重计算
- 自适应阈值调整

### 权限管理系统
- 用户角色管理
- 功能权限控制
- 操作日志记录

### 实时监控
- 知识库状态监控
- 搜索性能统计
- 系统资源监控

## 🚀 性能优化

### 向量存储优化
- FAISS索引优化
- 批量向量化处理
- 内存使用优化

### 搜索性能
- 多级缓存机制
- 并行搜索处理
- 结果排序优化

### 系统稳定性
- 错误恢复机制
- 自动重试策略
- 日志监控告警

## 📊 监控和日志

### 日志系统
- 结构化日志记录
- 多级别日志控制
- 日志文件轮转

### 性能监控
- 搜索响应时间
- 向量化性能
- 内存使用情况

### 错误处理
- 异常捕获和记录
- 自动错误恢复
- 用户友好的错误提示

## 🔒 安全特性

### 数据安全
- 文件上传验证
- 路径遍历防护
- 敏感信息保护

### 访问控制
- 用户认证
- 权限验证
- 会话管理

### API安全
- 请求频率限制
- 输入验证
- 错误信息脱敏

## 🤝 贡献指南

### 开发环境设置
1. Fork项目
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request

### 代码规范
- 遵循PEP 8规范
- 添加适当的注释
- 编写单元测试
- 更新相关文档

## 📝 更新日志

### v2.0.0 (最新)
- ✨ 新增AI智能分块功能
- 🔧 优化混合搜索算法
- 🎨 改进Web界面设计
- 🐛 修复多个已知问题

### v1.5.0
- ✨ 新增权限管理系统
- 🔧 优化向量存储性能
- 📊 增强监控和统计功能

### v1.0.0
- 🎉 初始版本发布
- ✨ 基础RAG功能
- 🌐 Web界面和微信机器人

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与反馈

- 提交Issue: [GitHub Issues](https://github.com/your-repo/issues)
- 功能建议: [Feature Requests](https://github.com/your-repo/discussions)
- 技术交流: [Discussions](https://github.com/your-repo/discussions)

---

**注意**: 使用前请确保已正确配置API密钥和相关环境变量。详细配置说明请参考 `config.example.conf` 文件。 