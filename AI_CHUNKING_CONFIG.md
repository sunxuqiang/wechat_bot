# AI分块服务配置参数移植说明

## 概述

本次更新将 `ai_chunk_service.py` 中的硬编码参数移植到 `config.conf` 配置文件中，实现了配置的集中管理和灵活调整。

## 变更内容

### 1. 配置文件变更 (`config.conf`)

在 `[api]` 部分新增了以下AI分块专用配置参数：

```ini
# AI分块专用配置
ai_chunking_model = Qwen/Qwen2-7B-Instruct
ai_chunking_max_tokens = 256
ai_chunking_timeout = 15
ai_chunking_max_retries = 3
ai_chunking_retry_delay = 2
ai_chunking_min_text_length = 10
ai_chunking_min_chunk_length = 5
ai_chunking_max_chunk_length = 1000
```

### 2. 代码变更 (`ai_chunk_service.py`)

#### 2.1 `__init__` 方法变更

**变更前：**
```python
# 硬编码参数
self.model = "Qwen/Qwen2-7B-Instruct"
self.max_tokens = 256
self.timeout = 15
# ... 其他硬编码参数
```

**变更后：**
```python
# 从配置文件读取参数
self.model = config.get('api', 'ai_chunking_model')
self.max_tokens = config.getint('api', 'ai_chunking_max_tokens')
self.timeout = config.getint('api', 'ai_chunking_timeout')
# ... 其他配置参数
```

#### 2.2 新增配置参数

- `max_retries`: 最大重试次数
- `retry_delay`: 重试延迟时间
- `min_text_length`: 最小文本长度
- `min_chunk_length`: 最小块长度
- `max_chunk_length`: 最大块长度

#### 2.3 方法参数更新

以下方法中的硬编码参数已替换为实例变量：

- `chunk_with_ai()`: 使用 `self.max_retries`, `self.retry_delay`, `self.min_text_length` 等
- `validate_chunks()`: 使用 `self.min_chunk_length`, `self.max_chunk_length`
- `_smart_split_content()`: 使用 `self.min_text_length`, `self.min_chunk_length`, `self.max_chunk_length`

## 配置参数说明

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `ai_chunking_model` | string | Qwen/Qwen2-7B-Instruct | AI分块使用的模型 |
| `ai_chunking_max_tokens` | int | 256 | 最大生成token数 |
| `ai_chunking_timeout` | int | 15 | API请求超时时间(秒) |
| `ai_chunking_max_retries` | int | 3 | 最大重试次数 |
| `ai_chunking_retry_delay` | int | 2 | 重试延迟时间(秒) |
| `ai_chunking_min_text_length` | int | 10 | 最小文本长度 |
| `ai_chunking_min_chunk_length` | int | 5 | 最小块长度 |
| `ai_chunking_max_chunk_length` | int | 1000 | 最大块长度 |

## 兼容性说明

- **向后兼容**: 所有原有业务逻辑保持不变
- **配置灵活**: 可以通过修改 `config.conf` 文件调整参数，无需修改代码
- **环境适配**: 支持不同环境使用不同的配置参数

## 测试验证

使用 `test_config_params.py` 脚本验证配置参数是否正确加载：

```bash
python test_config_params.py
```

## 优势

1. **配置集中化**: 所有AI分块相关参数统一在配置文件中管理
2. **灵活性提升**: 可以通过修改配置文件调整参数，无需重新部署代码
3. **环境隔离**: 不同环境可以使用不同的配置文件
4. **维护性增强**: 参数调整更加透明和可控
5. **业务逻辑保护**: 核心业务逻辑保持不变，确保系统稳定性

## 注意事项

1. 修改配置文件后需要重启应用才能生效
2. 建议在生产环境修改配置前先在测试环境验证
3. 配置文件中的敏感信息（如API密钥）建议使用环境变量管理 