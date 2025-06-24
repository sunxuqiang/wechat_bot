import os
import certifi
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from huggingface_hub import HfApi
from config_loader import config

class SSLContextAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        kwargs['ssl_context'] = context
        return super(SSLContextAdapter, self).init_poolmanager(*args, **kwargs)

def get_ssl_session():
    """Get a requests session with proper SSL configuration"""
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=3)
    session.mount('https://', adapter)
    session.verify = certifi.where()
    return session

def setup_ssl_config():
    """设置SSL配置"""
    # 检查是否禁用SSL验证
    if config.getboolean('security', 'disable_ssl_verification', False):
        # 禁用SSL证书验证
        os.environ['CURL_CA_BUNDLE'] = ''
        os.environ['REQUESTS_CA_BUNDLE'] = ''
        print("SSL证书验证已禁用")
    else:
        # 启用SSL证书验证
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
        os.environ['SSL_CERT_FILE'] = certifi.where()
        print("SSL证书验证已启用")
    
    # 设置Hugging Face相关环境变量
    os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
    os.environ['HF_HOME'] = os.path.join(os.getcwd(), 'models')
    os.environ['TRANSFORMERS_CACHE'] = os.path.join(os.getcwd(), 'models')
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = os.path.join(os.getcwd(), 'models')
    
    # 设置离线模式（如果需要）
    if config.getboolean('model', 'offline_mode', False):
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['HF_DATASETS_OFFLINE'] = '1'
        os.environ['HF_HUB_OFFLINE'] = '1'
        print("模型离线模式已启用")
    
    print("SSL配置设置完成")

def configure_ssl():
    """Configure SSL settings for the application"""
    try:
        # 1. Set SSL environment variables
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
        os.environ['SSL_CERT_FILE'] = certifi.where()
        
        # 2. Configure HuggingFace settings
        os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
        os.environ['HF_HOME'] = os.path.join(os.getcwd(), 'models')
        os.environ['TRANSFORMERS_CACHE'] = os.path.join(os.getcwd(), 'models')
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = os.path.join(os.getcwd(), 'models')
        
        # 3. Create a custom session with SSL configuration
        session = get_ssl_session()
        
        # 4. Configure HuggingFace client
        hf_api = HfApi()
        hf_api._session = session
        
        print("SSL configuration completed successfully")
        return session
        
    except Exception as e:
        print(f"Error configuring SSL: {e}")
        raise 

if __name__ == "__main__":
    setup_ssl_config() 