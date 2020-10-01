import youtube_dl
import discord
from urllib.parse import quote
import aiohttp
import json


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop, stream=False):
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class YoutubeSearch:

    def __init__(self, loop, search_terms: str, max_results=None):
        self.BASE_URL = 'https://www.youtube.com'
        self.search_terms = search_terms
        self.max_results = max_results
        self.videos = self.search()
        self.session = None

    async def search(self):
        encoded_search = quote(self.search_terms)

        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/results?search_query={encoded_search}"
            async with session.get(url) as resp:
                response = await resp.text()

            while 'window["ytInitialData"]' not in response:
                async with session.get(url) as resp:
                    response = await resp.text()

        results = self.parse_html(response)
        if self.max_results is not None and len(results) > self.max_results:
            return results[: self.max_results]
        return results

    @staticmethod
    def parse_html(response):
        results = []
        start = (
            response.index('window["ytInitialData"]')
            + len('window["ytInitialData"]')
            + 3
        )
        end = response.index("};", start) + 1
        json_str = response[start:end]
        data = json.loads(json_str)

        videos = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"][
            "sectionListRenderer"
        ]["contents"][0]["itemSectionRenderer"]["contents"]

        for video in videos:
            res = {}
            if "videoRenderer" in video:
                video_data = video.get("videoRenderer", {})
                res["id"] = video_data.get("videoId", None)
                res["title"] = video_data.get("title", {}).get("runs", [[{}]])[0].get("text", None)
                results.append(res)
        return results

    def to_dict(self):
        return self.videos

    def to_json(self):
        return json.dumps({"videos": self.videos})
