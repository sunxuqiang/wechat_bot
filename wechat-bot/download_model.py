import os
import logging
from pathlib import Path
import requests
from tqdm import tqdm
import time
import certifi
from huggingface_hub import HfApi, create_repo
from ssl_config import configure_ssl, get_ssl_session
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_file(url: str, save_path: str, session: requests.Session = None) -> bool:
    """
    从URL下载文件
    
    Args:
        url: 下载链接
        save_path: 保存路径
        session: 请求会话
    
    Returns:
        bool: 是否下载成功
    """
    try:
        if session is None:
            session = requests.Session()
            
        # 发送HEAD请求获取文件大小
        response = session.head(url, allow_redirects=True)
        total_size = int(response.headers.get('content-length', 0))
        
        # 使用GET请求下载文件
        response = session.get(url, stream=True)
        response.raise_for_status()
        
        # 显示下载进度条
        progress_bar = tqdm(
            total=total_size,
            unit='iB',
            unit_scale=True,
            desc=f"下载 {os.path.basename(save_path)}"
        )
        
        # 写入文件
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    progress_bar.update(len(chunk))
                    f.write(chunk)
                    
        progress_bar.close()
        return True
        
    except Exception as e:
        logger.error(f"下载文件失败 {url}: {str(e)}")
        if os.path.exists(save_path):
            os.remove(save_path)
        return False

def download_model(model_name: str, local_dir: str = "models") -> bool:
    """
    下载模型到本地
    
    Args:
        model_name: 模型名称
        local_dir: 本地保存目录
    
    Returns:
        bool: 是否下载成功
    """
    try:
        logger.info(f"开始下载模型: {model_name}")
        
        # 创建保存目录
        save_dir = Path(local_dir) / model_name.split('/')[-1]
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置SSL
        session = configure_ssl()
        
        # 模型文件 URLs (使用镜像站点)
        base_urls = [
            "https://hf-mirror.com",
            "https://huggingface.tuna.tsinghua.edu.cn",
            "https://mirror.sjtu.edu.cn/hugging-face-models",
            "https://aliendao.cn/models",
            "https://huggingface.co"  # 作为最后的备选
        ]
        
        # 添加更多常见的模型文件
        model_files = [
            "config.json",
            "pytorch_model.bin",
            "pytorch_model.safetensors",  # 添加 safetensors 格式
            "special_tokens_map.json",
            "tokenizer_config.json",
            "tokenizer.json",
            "vocab.txt",
            "modules.json",
            "config_sentence_transformers.json",
            "sentence_bert_config.json"
        ]
        
        # 尝试从不同镜像下载
        for base_url in base_urls:
            success = True
            logger.info(f"尝试从 {base_url} 下载...")
            
            for file_name in model_files:
                file_url = f"{base_url}/{model_name}/resolve/main/{file_name}"
                save_path = save_dir / file_name
                
                if save_path.exists():
                    logger.info(f"文件已存在: {file_name}")
                    continue
                
                try:
                    if download_file(file_url, str(save_path), session):
                        logger.info(f"成功下载: {file_name}")
                    else:
                        # 如果是可选文件，跳过错误继续下载
                        if file_name in ["pytorch_model.safetensors", "modules.json", "sentence_bert_config.json"]:
                            logger.warning(f"可选文件下载失败，继续下载其他文件: {file_name}")
                            continue
                        success = False
                        break
                except Exception as e:
                    logger.warning(f"下载 {file_name} 时出错: {str(e)}")
                    if file_name in ["pytorch_model.safetensors", "modules.json", "sentence_bert_config.json"]:
                        continue
                    success = False
                    break
                    
                # 下载后等待一小段时间，避免请求过于频繁
                time.sleep(1.5)  # 增加等待时间，减少被限制的可能
                
            if success:
                logger.info(f"模型 {model_name} 下载完成")
                return True
                
            logger.warning(f"从 {base_url} 下载失败，尝试下一个镜像")
            
        logger.error(f"所有镜像下载失败")
        return False
        
    except Exception as e:
        logger.error(f"下载模型时发生错误: {str(e)}")
        return False

def main():
    """下载所需的模型"""
    # 创建模型目录
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # 要下载的模型列表
    model_names = [
        'shibing624/text2vec-base-chinese',
        'sentence-transformers/all-MiniLM-L6-v2',
        'sentence-transformers/paraphrase-MiniLM-L3-v2'
    ]
    
    # 配置SSL
    configure_ssl()
    
    # 下载模型
    success_count = 0
    for model_name in model_names:
        if download_model(model_name):
            success_count += 1
            logger.info(f"模型 {model_name} 下载成功")
        else:
            logger.error(f"模型 {model_name} 下载失败")
    
    if success_count > 0:
        logger.info(f"\n成功下载 {success_count} 个模型！")
    else:
        logger.warning("\n所有模型下载失败。")
        logger.info("将使用TF-IDF作为备选方案。")

if __name__ == "__main__":
    main() 