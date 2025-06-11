from huggingface_hub import snapshot_download
import os

def download_model():
    try:
        print("开始下载模型文件...")
        model_path = snapshot_download(
            repo_id="shibing624/text2vec-base-chinese",
            local_dir="models/text2vec-base-chinese",
            local_dir_use_symlinks=False,
            ignore_patterns=["*.md", "*.h5", "*.onnx", "*.bin"]  # 忽略一些大文件
        )
        print(f"模型文件下载成功，保存在: {model_path}")
        return True
    except Exception as e:
        print(f"下载失败: {str(e)}")
        return False

if __name__ == "__main__":
    download_model() 