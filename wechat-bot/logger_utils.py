import logging
import time
import traceback
from functools import wraps

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LoggerUtils:
    @staticmethod
    def section_start(logger, title):
        """打印区块开始"""
        logger.info("\n" + "="*50)
        logger.info(title)
        logger.info("="*50)

    @staticmethod
    def section_end(logger, title):
        """打印区块结束"""
        logger.info("\n" + "="*50)
        logger.info(title)
        logger.info("="*50 + "\n")

    @staticmethod
    def step(logger, step_number, description):
        """打印步骤信息"""
        logger.info(f"\n--- 步骤{step_number}: {description} ---")

    @staticmethod
    def error_detail(logger, error, title="错误详情"):
        """打印详细错误信息"""
        logger.error(f"\n!!! {title} !!!")
        logger.error(f"错误类型: {type(error).__name__}")
        logger.error(f"错误信息: {str(error)}")
        logger.error("详细错误堆栈:")
        logger.error(traceback.format_exc())

    @staticmethod
    def preview_text(text, max_length=500):
        """生成文本预览"""
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text

    @staticmethod
    def log_execution_time(logger):
        """函数执行时间装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    logger.info(f"{func.__name__} 执行时间: {end_time - start_time:.2f} 秒")
                    return result
                except Exception as e:
                    end_time = time.time()
                    logger.error(f"{func.__name__} 执行失败，耗时: {end_time - start_time:.2f} 秒")
                    raise
            return wrapper
        return decorator

    @staticmethod
    def log_api_request(logger, url, method, headers, data, max_length=500):
        """记录API请求信息"""
        logger.info("\n=== API请求信息 ===")
        logger.info(f"URL: {url}")
        logger.info(f"方法: {method}")
        logger.info("请求头:")
        for key, value in headers.items():
            if 'auth' in key.lower():
                value = value[:10] + "..." + value[-5:]
            logger.info(f"  {key}: {value}")
        logger.info("请求数据预览:")
        logger.info(LoggerUtils.preview_text(str(data), max_length))

    @staticmethod
    def log_api_response(logger, response, max_length=500):
        """记录API响应信息"""
        logger.info("\n=== API响应信息 ===")
        logger.info(f"状态码: {response.status_code}")
        logger.info("响应内容预览:")
        logger.info(LoggerUtils.preview_text(response.text, max_length))

    @staticmethod
    def log_knowledge_base_stats(logger, vector_store):
        """记录知识库统计信息"""
        logger.info("\n=== 知识库统计信息 ===")
        if hasattr(vector_store, 'texts'):
            logger.info(f"文档总数: {len(vector_store.texts)}")
            if len(vector_store.texts) > 0:
                logger.info("文档示例:")
                for i, text in enumerate(vector_store.texts[:3]):
                    preview = LoggerUtils.preview_text(text, 200)
                    logger.info(f"文档[{i}]: {preview}")
        else:
            logger.warning("知识库未初始化或为空")

    @staticmethod
    def log_search_results(logger, results, max_results=3):
        """记录搜索结果"""
        logger.info("\n=== 搜索结果 ===")
        if not results:
            logger.info("未找到匹配结果")
            return

        logger.info(f"找到 {len(results)} 个结果")
        for i, (text, score, metadata) in enumerate(results[:max_results]):
            logger.info(f"\n结果[{i+1}]:")
            logger.info(f"相关度: {score:.4f}")
            logger.info(f"内容预览: {LoggerUtils.preview_text(text, 200)}")
            if metadata:
                logger.info(f"元数据: {metadata}") 