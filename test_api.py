import os
import json
import requests
from dotenv import load_dotenv

def test_api():
    # 加载环境变量
    load_dotenv()
    api_key = os.getenv('SILICONFLOW_API_KEY')
    
    # API 配置
    api_url = 'https://api.siliconflow.cn/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # 请求数据
    data = {
        'model': 'deepseek-ai/DeepSeek-R1-0528-Qwen3-8B',
        'messages': [
            {'role': 'system', 'content': '你是一个专业、友好的AI助手。请用简洁专业的语言回答问题。'},
            {'role': 'user', 'content': '你好，这是一个测试消息。'}
        ],
        'stream': False,
        'max_tokens': 2048,
        'temperature': 0.7,
        'top_p': 0.7,
        'frequency_penalty': 0.5,
        'presence_penalty': 0.0
    }
    
    print("\n=== 请求详情 ===")
    print(f"API URL: {api_url}")
    print(f"请求头: {headers}")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    print("===============\n")
    
    try:
        # 发送请求
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        
        print("\n=== 响应详情 ===")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        print(f"响应内容: {response.text}")
        print("===============\n")
        
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            print("\n=== 模型回复 ===")
            print(result['choices'][0]['message']['content'])
            print("===============\n")
            return True
        else:
            print("\n错误：API 返回的数据格式不正确")
            return False
            
    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP错误: {str(e)}")
        if e.response.status_code == 400:
            print(f"请求参数错误: {e.response.text}")
        elif e.response.status_code == 401:
            print("API密钥无效或已过期")
        elif e.response.status_code == 429:
            print("请求频率超限")
        elif e.response.status_code >= 500:
            print("服务器错误")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"\n连接错误: {str(e)}")
        return False
        
    except requests.exceptions.Timeout as e:
        print(f"\n请求超时: {str(e)}")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"\n请求异常: {str(e)}")
        return False

if __name__ == '__main__':
    test_api() 