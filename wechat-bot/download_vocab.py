import os
import requests
from pathlib import Path
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_vocab():
    """从国内镜像下载 vocab.txt 文件"""
    # 模型目录
    model_dir = Path("models/text2vec-base-chinese")
    vocab_path = model_dir / "vocab.txt"
    
    # 确保目录存在
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # 国内镜像源
    mirrors = [
        "https://mirror.sjtu.edu.cn/hugging-face-models/shibing624/text2vec-base-chinese/resolve/main/vocab.txt",
        "https://huggingface.tuna.tsinghua.edu.cn/shibing624/text2vec-base-chinese/resolve/main/vocab.txt",
        "https://hf-mirror.com/shibing624/text2vec-base-chinese/resolve/main/vocab.txt"
    ]
    
    # 尝试从不同镜像下载
    for mirror in mirrors:
        try:
            logger.info(f"尝试从 {mirror} 下载 vocab.txt...")
            
            # 配置请求会话
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # 发送请求
            response = session.get(mirror, stream=True, timeout=30)
            response.raise_for_status()
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 保存文件
            with open(vocab_path, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            # 打印下载进度
                            percent = int(downloaded * 100 / total_size)
                            print(f"\r下载进度: {percent}%", end='', flush=True)
                    print()  # 换行
            
            logger.info(f"成功下载 vocab.txt 到 {vocab_path}")
            
            # 验证文件
            if vocab_path.stat().st_size > 0:
                logger.info("文件验证成功")
                return True
            else:
                logger.warning("下载的文件为空，尝试下一个镜像")
                os.remove(vocab_path)
                continue
                
        except Exception as e:
            logger.warning(f"从 {mirror} 下载失败: {str(e)}")
            # 如果文件下载失败，删除可能存在的不完整文件
            if vocab_path.exists():
                os.remove(vocab_path)
            continue
            
        # 下载成功后等待一小段时间再继续
        time.sleep(1)
    
    logger.error("所有镜像下载失败")
    return False

if __name__ == "__main__":
    if download_vocab():
        print("\nvocab.txt 文件下载成功！")
    else:
        print("\n下载失败，请检查网络连接或手动下载文件。") 