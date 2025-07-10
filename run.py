import asyncio
from app.main import request_all_epg_job

if __name__ == "__main__":
    asyncio.run(request_all_epg_job())
