import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path
from config_loader import config

def test_model():
    # 检查.env文件
    env_path = Path('.env')
    print(f"\n.env文件路径: {env_path.absolute()}")
    print(f".env文件是否存在: {env_path.exists()}")
    
    if env_path.exists():
        print("\n.env文件内容预览:")
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('SILICONFLOW_API_KEY='):
                    api_key = line.strip().split('=', 1)[1].strip()
                    masked_key = api_key[:4] + '*' * 8 + api_key[-4:] if len(api_key) > 12 else api_key
                    print(f"找到API密钥: {masked_key}")
                    # 直接设置环境变量
                    os.environ['SILICONFLOW_API_KEY'] = api_key
                    break
    
    # 加载环境变量
    load_dotenv()
    
    # 获取API密钥
    api_key = os.getenv('SILICONFLOW_API_KEY')
    if not api_key:
        raise ValueError("请设置 SILICONFLOW_API_KEY 环境变量")
    
    # 打印API密钥前几位和后几位，中间用星号代替
    masked_key = api_key[:4] + '*' * 8 + api_key[-4:] if len(api_key) > 12 else api_key
    print(f"\n使用的API密钥: {masked_key}")
    
    # API配置
    api_url = 'https://api.siliconflow.cn/v1/chat/completions'
    models_to_test = [
        'gpt-3.5-turbo',
        'gpt-4',
        'qwen-7b-chat',
        'Qwen-7B-Chat',
        'deepseek-ai/DeepSeek-R1-0528-Qwen3-8B',
        'text-embedding-3-small'
    ]
    
    print("\n=== 开始测试模型 ===")
    for model in models_to_test:
        print(f"\n测试模型: {model}")
        
        # 构建请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 在打印时隐藏真实的API密钥
        headers_for_display = headers.copy()
        headers_for_display["Authorization"] = f"Bearer {masked_key}"
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个友好的助手。"},
                {"role": "user", "content": "你好"}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        print(f"请求头: {json.dumps(headers_for_display, indent=2, ensure_ascii=False)}")
        print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        try:
            # 发送请求
            response = requests.post(
                api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                print(f"✅ 模型 {model} 测试成功！")
                return model
            else:
                print(f"❌ 模型 {model} 测试失败！")
                if response.status_code == 401:
                    print("原因：API密钥无效")
                elif response.status_code == 400:
                    print("原因：模型名称可能不正确")
                else:
                    print(f"原因：未知错误 ({response.status_code})")
                
        except Exception as e:
            print(f"❌ 测试出错: {e}")
    
    print("\n没有找到可用的模型")
    return None

def test_api():
    """测试API连接"""
    # 获取API密钥
    api_key = config.get_secret('SILICONFLOW_API_KEY')
    if not api_key:
        print("错误: 未找到 SILICONFLOW_API_KEY")
        return False
    
    # 设置环境变量
    config.set_secret('SILICONFLOW_API_KEY', api_key)
    
    # 获取API配置
    api_url = config.get('api', 'url')
    model = config.get('api', 'model')
    
    print(f"API URL: {api_url}")
    print(f"Model: {model}")
    print(f"API Key: {api_key[:4]}****{api_key[-4:]}")
    
    # 测试API调用
    try:
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": "你好，请简单介绍一下自己。"}
                ],
                "max_tokens": config.getint('api', 'max_tokens', 2048),
                "temperature": config.getfloat('api', 'temperature', 0.7)
            },
            timeout=config.getint('api', 'timeout', 30)
        )
        
        if response.status_code == 200:
            result = response.json()
            print("API测试成功!")
            print(f"回复: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"API测试失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"API测试异常: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始测试 SiliconFlow API 模型名称...")
    working_model = test_model()
    if working_model:
        print(f"\n找到可用的模型: {working_model}") 