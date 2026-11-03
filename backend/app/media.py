# CrossVideo — Cross-platform video playback progress synchronization tool
# Copyright (C) 2026 WGRJLYSYB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache

from guessit import guessit


@dataclass(frozen=True)
class ParsedMedia:
    title: str
    title_key: str
    season: int
    episode: int


@lru_cache(maxsize=4096)
def parse_media_title(raw_title: str) -> ParsedMedia | None:
    cleaned = raw_title
    for noise in (
        "在线观看", "免费播放", "高清1080P", "4K超清", "1080P", "HD中字",
        "瓢虫影音", "腾讯视频", "爱奇艺", "优酷", "电视剧", "电影", "动漫",
        "综艺", "直播", "全集", "国语", "日语", "韩语",
    ):
        cleaned = cleaned.replace(noise, "")
    cleaned = re.sub(r"^.*《", "", cleaned)
    cleaned = re.sub(r"[\s\-_【】\[\]《》]", " ", cleaned)

    result = guessit(cleaned)
    title = result.get("title")
    season = result.get("season", 1)
    episode = result.get("episode")
    if (
        not isinstance(title, str)
        or not title.strip()
        or not isinstance(season, int)
        or isinstance(season, bool)
        or not isinstance(episode, int)
        or isinstance(episode, bool)
    ):
        return None

    normalized_title = title.strip()
    normalized_key = re.sub(r"[\W_]+", "", normalized_title.casefold(), flags=re.UNICODE)
    if not normalized_key:
        return None
    title_key = hashlib.sha256(normalized_key.encode("utf-8")).hexdigest()
    return ParsedMedia(normalized_title, title_key, season, episode)
