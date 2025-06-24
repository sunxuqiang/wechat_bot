import os
import configparser
from pathlib import Path

class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.conf')
        
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")
        
        self.config.read(self.config_path, encoding='utf-8')
        
        # 确保必要的目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        paths = [
            self.get('paths', 'model_cache_dir'),
            self.get('paths', 'upload_folder'),
            os.path.dirname(self.get('database', 'database_path'))
        ]
        
        for path in paths:
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def get(self, section, option, fallback=None):
        """获取配置项的字符串值"""
        return self.config.get(section, option, fallback=fallback)
    
    def getboolean(self, section, option, fallback=None):
        """获取配置项的布尔值"""
        return self.config.getboolean(section, option, fallback=fallback)
    
    def getint(self, section, option, fallback=None):
        """获取配置项的整数值"""
        return self.config.getint(section, option, fallback=fallback)
    
    def getfloat(self, section, option, fallback=None):
        """获取配置项的浮点数值"""
        return self.config.getfloat(section, option, fallback=fallback)
    
    def get_secret(self, key, fallback=None):
        """获取秘钥，优先从环境变量获取，然后从配置文件获取"""
        # 首先尝试从环境变量获取
        env_value = os.environ.get(key)
        if env_value:
            return env_value
        
        # 如果环境变量中没有，从配置文件获取
        try:
            return self.get('secrets', key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def set_secret(self, key, value):
        """设置秘钥到环境变量"""
        os.environ[key] = value

# 创建全局配置实例
config = Config() 