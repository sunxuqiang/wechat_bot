# 配置系统说明

## 概述

本项目已将环境变量中的秘钥移植到 `config.conf` 配置文件中，提供了更统一和安全的配置管理方式。

## 配置文件结构

### 主要配置文件
- `config.conf` - 主配置文件（包含实际配置）
- `config.example.conf` - 示例配置文件（不包含敏感信息）

### 配置项说明

#### [secrets] 部分 - 秘钥配置
```ini
[secrets]
# SiliconFlow API密钥
siliconflow_api_key = your-siliconflow-api-key-here
# Hugging Face Token
hf_token = your-huggingface-token-here
# OpenAI API密钥
openai_api_key = your-openai-api-key-here
```

#### [api] 部分 - API配置
```ini
[api]
url = https://api.siliconflow.cn/v1/chat/completions
model = deepseek-ai/DeepSeek-R1-0528-Qwen3-8B
max_tokens = 2048
temperature = 0.7
timeout = 30
```

#### [security] 部分 - 安全配置
```ini
[security]
# 是否禁用SSL验证
disable_ssl_verification = true
```

## 使用方法

### 1. 设置秘钥
将你的实际API密钥替换到 `config.conf` 文件中：

```ini
[secrets]
siliconflow_api_key = sk-your-actual-api-key-here
```

### 2. 在代码中使用
```python
from config_loader import config

# 获取秘钥
api_key = config.get_secret('SILICONFLOW_API_KEY')

# 获取其他配置
api_url = config.get('api', 'url')
model_name = config.get('api', 'model')
```

### 3. 配置加载优先级
1. 环境变量（最高优先级）
2. 配置文件
3. 默认值（最低优先级）

## 安全注意事项

1. **不要提交敏感信息**：确保 `config.conf` 文件不会被提交到版本控制系统
2. **使用示例文件**：开发时使用 `config.example.conf` 作为模板
3. **环境变量优先**：生产环境建议使用环境变量设置敏感信息

## 迁移指南

### 从环境变量迁移
如果你之前使用环境变量，现在可以：

1. 将环境变量值复制到 `config.conf` 的 `[secrets]` 部分
2. 删除环境变量设置代码
3. 使用 `config.get_secret()` 方法获取秘钥

### 示例迁移
**之前：**
```python
import os
api_key = os.environ.get('SILICONFLOW_API_KEY')
```

**现在：**
```python
from config_loader import config
api_key = config.get_secret('SILICONFLOW_API_KEY')
```

## 配置验证

运行以下命令验证配置是否正确：

```bash
python test_model.py
```

这将测试API连接和配置是否正确。

## 故障排除

### 常见问题

1. **配置未找到**
   - 确保 `config.conf` 文件存在
   - 检查文件路径是否正确

2. **秘钥无效**
   - 验证API密钥是否正确
   - 检查密钥是否过期

3. **SSL证书问题**
   - 在 `[security]` 部分设置 `disable_ssl_verification = true`

### 调试模式
启用详细日志：
```ini
[logging]
log_level = DEBUG
``` 