import requests
import json
from flask import Blueprint, request

youtube_bp = Blueprint('youtube', __name__)

def yt_keyword_search(keyword: str) -> dict:
    """
    Perform a keyword search on YouTube.
    """
    url = "http://suggestqueries.google.com/complete/search?hl=zh-tw&client=youtube&jsonp=suggestCallBack&q={}"
    response = requests.get(url.format(keyword))
    if response.status_code != 200:
        raise Exception("Failed to fetch data from YouTube API")
    text = response.text
    if not text.startswith('suggestCallBack'):
        raise Exception("Invalid response from YouTube API")
    text = text[len('suggestCallBack') + 1:-1]
    json_data = json.loads(text)
    result = [json_data[0]]
    for item in json_data[1]:
        result.append(item[0])
    return result

def yt_search(keyword: str) -> dict:
    """
    Perform a search on YouTube.
    """
    url = "https://youtube.com/results?search_query={}"
    response = requests.get(url.format(keyword))
    if response.status_code != 200:
        raise Exception("Failed to fetch data from YouTube API")
    text = response.text
    results = []
    key = "ytInitialData"
    start = text.index(key) + len(key) + 3
    end = text.index('</script>', start)
    ytInitialData = text[start:end].strip()[:-1] # remove ; at the end
    json_data = json.loads(ytInitialData)
    for contents in json_data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"]:
        if "itemSectionRenderer" not in contents.keys():
            continue
        for video in contents["itemSectionRenderer"]["contents"]:
            res = {}
            if "videoRenderer" in video.keys():
                video_data = video.get("videoRenderer", {})
                res["id"] = video_data.get("videoId", None)
                res["thumbnail"] = video_data.get("thumbnail", {}).get("thumbnails", [{}])[0].get("url", None)
                res["title"] = video_data.get("title", {}).get("runs", [{}])[0].get("text", '')
                res["long_desc"] = ''.join([r.get("text", '') for r in video_data.get("detailedMetadataSnippets", [{}])[0].get("snippetText", {}).get("runs", [{}])])
                res["channel"] = video_data.get("longBylineText", {}).get("runs", [{}])[0].get("text", '')
                res["duration"] = video_data.get("lengthText", {}).get("simpleText", 0)
                res["publish_time"] = video_data.get("publishedTimeText", {}).get("simpleText", 0)
                res["url_suffix"] = video_data.get("navigationEndpoint", {}).get("commandMetadata", {}).get("webCommandMetadata", {}).get("url", None)
                res["viewCountText"] = video_data.get("viewCountText", {}).get("simpleText", '')
                results.append(res)
    return results

@youtube_bp.route('/keyword')
def handle_keyword():
    """
    Handle the search keyword request.
    """
    keyword = request.args.get('q')    
    return {
        'keyword': keyword,
        'options': yt_keyword_search(keyword)
    }

@youtube_bp.route('/search')
def handle_search():
    """
    Handle the search request.
    """
    keyword = request.args.get('q')
    return {
        'keyword': keyword,
        'results': yt_search(keyword)
    }