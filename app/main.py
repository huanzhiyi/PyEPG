import asyncio
import os
from datetime import datetime

from fastapi import FastAPI, Response, HTTPException, Query

from app.epg.EpgGenerator import generateEpg
from app.epg_platform import MyTvSuper, Hami

from loguru import logger
import xml.etree.ElementTree as ET

from app.epg_platform.Astro import get_astro_epg
from app.epg_platform.CN_epg_pw import get_cn_channels_epg
from app.epg_platform.HOY import get_hoy_epg
from app.epg_platform.NowTV import request_nowtv_today_epg
from app.epg_platform.RTHK import get_rthk_epg

logger.add("runtime.log", rotation="10 MB")

app = FastAPI(openapi_url=None)

EPG_PLATFORMS = [
    {"platform": "cn", "fetcher": "request_cn_epg"},
    {"platform": "tvb", "fetcher": "request_my_tv_super_epg"},
    {"platform": "nowtv", "fetcher": "request_now_tv_epg"},
    {"platform": "hami", "fetcher": "request_hami_epg"},
    {"platform": "astro", "fetcher": "request_astro_epg"},
    {"platform": "rthk", "fetcher": "request_rthk_epg"},
    {"platform": "hoy", "fetcher": "request_hoy_epg"},
]


def platform_enabled(platform):
    """判断 enable 环境变量"""
    env_key = f"EPG_ENABLE_{platform.upper()}"
    val = os.getenv(env_key, "true").strip().lower()
    return val in {"1", "true", "yes", "on"}


@app.get("/")
async def root():
    return {"message": ""}


def mkdir_if_need(file_path):
    # 获取文件的目录
    directory = os.path.dirname(file_path)
    # 检查目录是否存在，如果不存在则创建目录
    if not os.path.exists(directory):
        os.makedirs(directory)  # 创建多层目录


async def request_my_tv_super_epg():
    file_path = get_epg_file_name_today("tvb")
    mkdir_if_need(file_path)
    if not os.path.exists(file_path):
        channels, programs = await MyTvSuper.get_channels(force=True)
        response_xml = await gen_channel(channels, programs)
        # 使用 with 语句打开文件，确保文件在操作完成后被正确关闭
        with open(file_path, "wb") as file:
            file.write(response_xml)
    else:
        print(f"今日mytvsuper epg已获取，不执行更新")
    # 删除旧的EPG
    delete_old_epg_file("tvb")


async def request_hami_epg():
    file_path = get_epg_file_name_today("hami")
    mkdir_if_need(file_path)
    if not os.path.exists(file_path):
        channels, programs = await Hami.request_all_epg()
        response_xml = await gen_channel(channels, programs)
        # 使用 with 语句打开文件，确保文件在操作完成后被正确关闭
        with open(file_path, "wb") as file:
            file.write(response_xml)
    else:
        print(f"今日hami epg已获取，不执行更新")
    # 删除旧的EPG
    delete_old_epg_file("hami")


async def request_cn_epg():
    file_path = get_epg_file_name_today("cn")
    mkdir_if_need(file_path)
    if not os.path.exists(file_path):
        response_xml = await get_cn_channels_epg()
        # 使用 with 语句打开文件，确保文件在操作完成后被正确关闭
        with open(file_path, "w", encoding='utf-8') as file:
            file.write(response_xml)
    else:
        print(f"今日cn epg已获取，不执行更新")
    # 删除旧的EPG
    delete_old_epg_file("cn")


async def request_astro_epg():
    file_path = get_epg_file_name_today("astro")
    mkdir_if_need(file_path)
    if not os.path.exists(file_path):
        channels, programs = await get_astro_epg()
        response_xml = await gen_channel(channels, programs)
        # 使用 with 语句打开文件，确保文件在操作完成后被正确关闭
        with open(file_path, "wb") as file:
            file.write(response_xml)
    else:
        print(f"今日Astro epg已获取，不执行更新")
    # 删除旧的EPG
    delete_old_epg_file("astro")


async def request_rthk_epg():
    file_path = get_epg_file_name_today("rthk")
    mkdir_if_need(file_path)
    if not os.path.exists(file_path):
        channels, programs = await get_rthk_epg()
        response_xml = await gen_channel(channels, programs)
        # 使用 with 语句打开文件，确保文件在操作完成后被正确关闭
        with open(file_path, "wb") as file:
            file.write(response_xml)
    else:
        print(f"今日RTHK epg已获取，不执行更新")
    # 删除旧的EPG
    delete_old_epg_file("rthk")


async def request_hoy_epg():
    file_path = get_epg_file_name_today("hoy")
    mkdir_if_need(file_path)
    if not os.path.exists(file_path):
        channels, programs = await get_hoy_epg()
        response_xml = await gen_channel(channels, programs)
        # 使用 with 语句打开文件，确保文件在操作完成后被正确关闭
        with open(file_path, "wb") as file:
            file.write(response_xml)
    else:
        print(f"今日HOY epg已获取，不执行更新")
    # 删除旧的EPG
    delete_old_epg_file("hoy")


async def request_now_tv_epg():
    file_path = get_epg_file_name_today("nowtv")
    mkdir_if_need(file_path)
    if not os.path.exists(file_path):
        response_xml = await request_nowtv_today_epg()
        # 使用 with 语句打开文件，确保文件在操作完成后被正确关闭
        with open(file_path, "wb") as file:
            file.write(response_xml)
    else:
        print(f"今日nowtv epg已获取，不执行更新")
    # 删除旧的EPG
    delete_old_epg_file("nowtv")


def get_date_str():
    # 获取当前时间
    current_time = datetime.now()
    # 格式化当前时间为 YYYYMMDD
    formatted_time = current_time.strftime('%Y%m%d')
    return formatted_time


def get_epg_file_name_today(platform):
    """
    获取今天的epg文件名
    :param platform:
    :return:
    """
    current_directory = os.getcwd()
    epgDir = f'{current_directory}/epg_files/{platform}'
    return f'{epgDir}/{platform}_{get_date_str()}.xml'


def delete_old_epg_file(platform):
    """
    删除旧的EPG
    :param platform:
    :return:
    """
    current_directory = os.getcwd()
    epgDir = f'{current_directory}/epg_files/{platform}'
    todayFile = os.path.basename(get_epg_file_name_today(platform))  # 获取今天的文件名
    try:
        for file in os.listdir(epgDir):
            if file.endswith(".xml") and file != todayFile:
                os.remove(os.path.join(epgDir, file))
                logger.info(f"删除旧的EPG：{file}")
    except FileNotFoundError:
        logger.info(f"Directory not found, skipping delete: {epgDir}")


@app.get("/epg/{platform}")
async def request_epg_by_platform(platform: str):
    filePath = get_epg_file_name_today(platform)
    if os.path.exists(filePath):
        with open(filePath, "rb") as file:  # 使用 'rb' 模式
            xml_bytes = file.read()  # 读取文件内容，返回 bytes
        return Response(content=xml_bytes, media_type="application/xml")
    else:
        raise HTTPException(status_code=404)


@app.get("/epg")
async def custom_aggregate_epg(platforms: str = Query(..., description="平台列表，用逗号分隔，按优先级排序")):
    """
    自定义聚合EPG数据

    platforms参数示例: ?platforms=tvb,nowtv,hami
    """
    # 分割平台列表
    platform_list = [p.strip() for p in platforms.split(',') if p.strip()]
    return await checkout_epg_multiple(platform_list)


@app.get("/all")
async def aggregate_epg():
    # 只聚合启用的
    platform_list = [
        conf["platform"]
        for conf in EPG_PLATFORMS
        if platform_enabled(conf["platform"])
    ]
    return await checkout_epg_multiple(platform_list)  # 按优先级排序的平台列表


async def checkout_epg_multiple(platform_list):
    merged_root = ET.Element("tv")
    merged_root.set("generator-info-name", "Charming Aggregate")

    channels_seen = set()  # 跟踪已处理的channel id

    for platform in platform_list:
        file_path = get_epg_file_name_today(platform)
        if not os.path.exists(file_path):
            continue

        with open(file_path, "rb") as file:
            xml_content = file.read()

        try:
            platform_root = ET.fromstring(xml_content)

            # 处理channels
            for channel in platform_root.findall("./channel"):
                channel_id = channel.get("id")
                if channel_id not in channels_seen:
                    channels_seen.add(channel_id)
                    merged_root.append(channel)

                    # 同时添加该频道的所有节目
                    for programme in platform_root.findall(f"./programme[@channel='{channel_id}']"):
                        merged_root.append(programme)

        except ET.ParseError as e:
            print(f"Error parsing XML for platform {platform}: {e}")
            continue

    if len(list(merged_root)) == 0:
        raise HTTPException(status_code=404, detail="No EPG data available")

    # 将合并后的XML转换回字符串
    merged_xml = ET.tostring(merged_root, encoding="utf-8", xml_declaration=True)
    return Response(content=merged_xml, media_type="application/xml")


async def gen_channel(channels, programs):
    return await generateEpg(channels, programs)


FETCHERS = {
    "request_cn_epg": request_cn_epg,
    "request_my_tv_super_epg": request_my_tv_super_epg,
    "request_now_tv_epg": request_now_tv_epg,
    "request_hami_epg": request_hami_epg,
    "request_astro_epg": request_astro_epg,
    "request_rthk_epg": request_rthk_epg,
    "request_hoy_epg": request_hoy_epg,
}


async def request_all_epg_job():
    enabled_platforms = [
        conf for conf in EPG_PLATFORMS if platform_enabled(conf["platform"])
    ]
    tasks = [FETCHERS[conf["fetcher"]]() for conf in enabled_platforms]
    # 并行执行所有任务
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # 处理可能的异常
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # 获取函数名称更好地标识任务
            task_name = enabled_platforms[i].get("fetcher", f"Task {i}")
            logger.error(f"{task_name} 请求EPG时发生错误: {str(result)}")

