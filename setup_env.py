import os
import sys
import subprocess
import platform

def setup_pip_config():
    """配置pip使用国内镜像源"""
    # 确定pip配置文件的位置
    if platform.system() == "Windows":
        pip_config_dir = os.path.expanduser("~/pip")
    else:
        pip_config_dir = os.path.expanduser("~/.pip")
    
    os.makedirs(pip_config_dir, exist_ok=True)
    config_file = os.path.join(pip_config_dir, "pip.conf")
    
    # 写入配置
    config_content = """[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
extra-index-url = 
    https://mirrors.aliyun.com/pypi/simple/
    https://mirrors.163.com/pypi/simple/
trusted-host = 
    pypi.tuna.tsinghua.edu.cn
    mirrors.aliyun.com
    mirrors.163.com
"""
    
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config_content)
    
    print(f"pip配置文件已创建：{config_file}")

def install_dependencies():
    """安装项目依赖"""
    print("开始安装依赖...")
    
    # 更新pip
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # 安装依赖
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def main():
    print("开始配置环境...")
    setup_pip_config()
    install_dependencies()
    print("\n环境配置完成！")
    print("\n接下来您可以运行 python download_model.py 来下载模型文件。")

if __name__ == "__main__":
    main() 