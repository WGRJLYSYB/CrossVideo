# CrossVideo — Cross-platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import logging
from html.parser import HTMLParser

import httpx

from .db import SessionLocal
from .models import UserSite

logger = logging.getLogger(__name__)

# 用于从 HTML 中提取 <title> 标签内容
class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self._inside_title = False

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._inside_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._inside_title = False

    def handle_data(self, data: str) -> None:
        if self._inside_title:
            self.title_parts.append(data)


def fetch_homepage_title(site_host: str) -> str | None:
    """尝试获取网站首页的 <title> 标签文本，返回清理后的标题字符串或 None。

    site_host 应为无 schema 的纯域名，例如 www.abc.com
    """
    host = site_host.strip().rstrip(".").encode("idna").decode("ascii").lower()
    if not host or any(char in host for char in "/:@?#"):
        raise ValueError("invalid site host")

    # 优先 HTTPS，失败后降级 HTTP
    for scheme in ("https", "http"):
        url = f"{scheme}://{host}"
        try:
            with httpx.Client(timeout=10, follow_redirects=True) as client:
                response = client.get(url, headers={
                    "User-Agent": "CrossVideo title checker",
                })
                if response.status_code < 200 or response.status_code >= 300:
                    continue
                body = response.text
                parser = _TitleParser()
                parser.feed(body)
                title = " ".join("".join(parser.title_parts).split())
                if title:
                    return title[:20]
        except httpx.TimeoutException:
            logger.warning("Homepage title request timed out for %s", url)
            continue
        except Exception:
            logger.warning("Homepage title request failed for %s", url, exc_info=True)
            continue
    return None


def fetch_and_save_site_title(site_id: int) -> None:
    """获取指定站点的标题并保存到数据库。"""
    try:
        with SessionLocal() as db:
            site = db.get(UserSite, site_id)
            if site is not None and not site.title_fetch_attempted:
                title = fetch_homepage_title(site.site_host)
                if title:
                    site.site_name = title
                site.title_fetch_attempted = True
                db.commit()
    except Exception:
        logger.exception("Could not complete homepage title check for site id %s", site_id)