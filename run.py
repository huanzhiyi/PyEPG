import asyncio
import os
from app.main import request_all_epg_job, EPG_PLATFORMS, logger

def platform_enabled(platform):
    """判断 enable 环境变量"""
    env_key = f"EPG_ENABLE_{platform.upper()}"
    val = os.getenv(env_key, "true").strip().lower()
    return val in {"1", "true", "yes", "on"}

async def main():
    tasks = [
        globals()[conf["fetcher"]]()
        for conf in EPG_PLATFORMS
        if platform_enabled(conf["platform"])
    ]
    # 并行执行所有任务
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # 处理可能的异常
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # 获取函数名称更好地标识任务
            task_name = EPG_PLATFORMS[i].get("fetcher", f"Task {i}")
            logger.error(f"{task_name} 请求EPG时发生错误: {str(result)}")

if __name__ == "__main__":
    asyncio.run(main())
