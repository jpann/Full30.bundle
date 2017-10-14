import urllib2
from bs4 import BeautifulSoup
import requests
import ssl
import re
import json

VERSION = ' V1.0.5'
NAME = 'Unofficial Full30.com Plex Channel'
TITLE = 'Unofficial Full30.com Plex Channel'
ART   = 'art-default.jpg'
ICON  = 'icon-default.jpg'

HTTP_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17"

ROUTE = "/video/fullthirty"
BASE_URL = "https://www.full30.com"
CHANNELS_URL = BASE_URL + "/channels/all"
VIDEO_URL = BASE_URL + "/video/{0}"
RECENT_API_URL = BASE_URL + "/api/v1.0/channel/{0}/recent-videos?page={1}"
THUMBNAIL_URL = BASE_URL + "/cdn/videos/{0}/{1}/thumbnails/320x180_{2}.jpg"
VIDEO_RESOLUTIONS_URL = "https://videos.full30.com/bitmotive/public/full30/v1.0/videos/{0}/{1}"
ALL_RECENT_API_URL = BASE_URL + "/api/v1.0/recents/all?page={0}"

def Start():
    ObjectContainer.title1 = TITLE
    ObjectContainer.art    = R(ART)

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art   = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art   = R(ART)

    HTTP.CacheTime             = CACHE_1HOUR
    HTTP.Headers['User-agent'] = HTTP_USER_AGENT
    
@handler(ROUTE, TITLE, thumb = ICON, art = ART)
def MainMenu():
    oc = ObjectContainer()

    #
    # Add 'All Recent Videos' menu item
    oc.add(DirectoryObject(
        key =
        Callback(
            ListRecentVideos,
            title = "All Recent Videos",
            page = 1
        ),
        title = "All Recent Videos",
        thumb = R(ICON)
    ))

    #
    # Add 'All Channels' menu item
    oc.add(DirectoryObject(
        key =
        Callback(
            ListChannels,
            title = "All Channels"
        ),
        title = "All Channels",
        thumb = R(ICON)
    ))

    return oc
#
# List All Channels
@route(ROUTE + "/AllChannels")
def ListChannels(title):
    oc = ObjectContainer(title2 = title)

    channels = get_channels()
    for channel in channels:
        title = channel['name']
        oc.add(DirectoryObject(
            key =
			Callback(
			    Channel_Menu,
			    title = title,
			    channel_url = channel['url'],
                thumbnail = channel['thumbnail']
		    ),
		    title = title,
            thumb = channel['thumbnail']
		))

    return oc

#
# List All Recent videos
#
@route(ROUTE + "/AllRecent")
def ListRecentVideos(title, page = 1):
    oc = ObjectContainer(title2 = title)

    recent_videos = get_all_recent(page)
    
    limit = recent_videos['pages']

    for video in recent_videos['videos']:
        url = video['url']
        channel = video['channel']
        title = video['title']
        desc = video['desc']
        thumb = video['thumbnail']
        mp4_url = video['mp4_url']
        views = video['views']
        
        oc.add(VideoClipObject(
            url = mp4_url,
            title = "{0} - {1}".format(channel, title),
            summary = "{0} views - {1}".format(views, desc),
            thumb = Callback(Thumb, url=thumb)
        ))	

    next_page = int(page) + 1
    if next_page <= limit:
        oc.add(DirectoryObject(
            key =
            Callback(
                ListRecentVideos,
                title = "All Recent Videos - Page {0}".format(next_page),
                page = next_page
            ),
            title = "Page {0}".format(next_page),
            summary = "View more recent videos"
       ))

    return oc

# 
# List 'Featured Videos' and 'Recent Videos' folders for the channel
#
@route(ROUTE + "/Channel")
def Channel_Menu(title, channel_url, thumbnail):
    oc = ObjectContainer(title2 = title)

    # Display Featured directory
    oc.add(DirectoryObject(
        key = 
        Callback(
            Channel_ListFeatured,
            title = "Featured Videos",
            channel_url = channel_url
        ),
        title = "Featured Videos",
        thumb = Callback(Thumb, url=thumbnail)
    ))

    # Display Recent directory
    oc.add(DirectoryObject(
        key =
        Callback(
            Channel_ListRecent,
            title = "Recent Videos",
            channel_url = channel_url
        ),
        title = "Recent Videos",
        thumb = Callback(Thumb, url=thumbnail)
    ))

    return oc

#
# List 'Recent Videos' for the channel
@route(ROUTE + "/Recent")
def Channel_ListRecent(title, channel_url, page=1):
    oc = ObjectContainer(title2 = title)

    recent_videos = get_recent(channel_url, page)
    
    limit = recent_videos['pages']

    for video in recent_videos['videos']:
        url = video['url']
        title = video['title']
        thumb = video['thumbnail']
        mp4_url = video['mp4_url']
        
        oc.add(VideoClipObject(
            url = mp4_url,
            title = title,
            thumb = Callback(Thumb, url=thumb)
        ))	

    next_page = int(page) + 1
    if next_page <= limit:
        oc.add(DirectoryObject(
            key =
            Callback(
                Channel_ListRecent,
                title = "Recent Videos - Page {0}".format(next_page),
                channel_url = channel_url,
                page = next_page
            ),
            title = "Page {0}".format(next_page),
            summary = "View more videos"
       ))

    return oc

#
# List 'Featured Videos' for the channel
@route(ROUTE + "/Featured")
def Channel_ListFeatured(title, channel_url):
    oc = ObjectContainer(title2 = title)

    featured_videos = get_featured(channel_url)

    Log.Info(featured_videos)

    for video in featured_videos:
        url = video['url']
        title = video['title']
        thumb = video['thumbnail']
        mp4_url = video['mp4_url']

        oc.add(VideoClipObject(
            url = mp4_url,
            title = title,
            thumb = Callback(Thumb, url=thumb)
        ))

    return oc

#
# Get thumbnail and cache it
def Thumb(url):
  try:
    data = HTTP.Request(url, cacheTime = CACHE_1MONTH).content
    return DataObject(data, 'image/jpeg')
  except:
    return Redirect(R(ICON))

#
# Get list of all channels from full30.com
def get_channels():
    channels = []

    data = HTTP.Request(CHANNELS_URL, cacheTime = CACHE_1HOUR).content

    soup = BeautifulSoup(data, "html.parser")

    videostreams = soup.find(class_="small-12 medium-4 large-4 columns show-for-large")

    for video in videostreams.find_next('ul').find_all('li'):
        channel_url = BASE_URL + video.find('a').get('href')
        
        channel_name = video.find('span', class_='channel-name text-uppercase').string.encode('ascii', 'ignore').decode('ascii')
        channel_thumbnail = BASE_URL + video.find('img', class_="channel-image").get('src')

        channels.append({ "name" : channel_name, "url" : channel_url, "thumbnail" : channel_thumbnail })

    return channels

#
# Get list of featured videos for specified channel url
def get_featured(url):
    featured = []

    data = HTTP.Request(url, cacheTime = 1200).content

    soup = BeautifulSoup(data, "html.parser")
    
    slug = soup.find(id="channel-slug").get('value')
    print 'slug: ', slug

    featured_videos = soup.find(class_=re.compile("featured-row"))
    
    if featured_videos:
        for video in featured_videos.find_all('div', class_="recent-item"):
            video_url = BASE_URL + video.find('a').get('href').encode('ascii', 'ignore').decode('ascii')
            video_hash = video_url.rsplit('/', 1)[-1]

            video_name = video.find('p', class_=re.compile('recent-title')).string.encode('ascii', 'ignore').decode('ascii')
            video_thumbnail = "http:" + video.find('img', class_="recentlyAdded-pictures").get('src')

            res_url = VIDEO_RESOLUTIONS_URL.format(slug, video_hash)
            
            video_metadata = get_video_metadata(video_url)

            featured.append(
                { 
                    "title" : video_name, 
                    "url" : video_url, 
                    "thumbnail" : video_thumbnail ,
                    "description" : video_metadata['desc'],
                    "mp4_url" : res_url
                })

    return featured

#
# Get recent videos by page for specified channel
def get_recent(url, page):
    recent = { 'title' : '', 'slug' : '', 'pages' : '', 'videos' : [] }
    
    if not page:
        page = 1
    
    channel_name = url.rsplit('/', 1)[-1]
    api_url = RECENT_API_URL.format(channel_name, page)
    
    html = HTTP.Request(api_url, cacheTime = 1200).content
    
    if not html:
        return None
        
    data = json.loads(html)
    
    if not data:
        return None
        
    recent['title'] = data['channel']['title']
    recent['pages'] = data['pages']
    recent['slug'] = data['channel']['slug']
    
    for video in data['videos']:
        v_hash = video['hashed_identifier']
        v_id = video['id']
        v_thumbnail = THUMBNAIL_URL.format(recent['slug'], v_hash, video['thumbnail_filename'])
        v_title = video['title']
        v_url = VIDEO_URL.format(v_hash)
        v_channel = recent['title']

        v_res_url = VIDEO_RESOLUTIONS_URL.format(recent['slug'], v_hash)
        
        recent['videos'].append({ "title" : v_title, "url" : v_url, "thumbnail" : v_thumbnail, "channel": v_channel, "mp4_url" : v_res_url })
    
    return recent

#
# Get all recent videos on full30.com by page
def get_all_recent(page):
    recent = { 'pages' : '', 'videos' : [] }

    if not page:
        page = 1
    
    api_url = ALL_RECENT_API_URL.format(page)
    
    html = HTTP.Request(api_url, cacheTime = 1200).content
    
    if not html:
        return None
        
    data = json.loads(html)
    
    if not data:
        return None
        
    recent['pages'] = data['pages']

    for key,value in data['videos'].iteritems():
        video = data['videos'][key]

        v_channel_slug = video['channel_slug']
        v_channel_title = video['channel_title']
        v_desc = video['description']
        v_hash = video['hashed_identifier']
        v_id = video['id']
        v_thumbnail = video['thumbnail_path']
        v_title = video['title']
        v_views = video['view_count']
        v_title = video['title']
        v_url = VIDEO_URL.format(v_hash)

        v_res_url = VIDEO_RESOLUTIONS_URL.format(v_channel_slug, v_hash)
        
        recent['videos'].append(
            { 
                "title" : v_title, 
                "url" : v_url, 
                "thumbnail" : v_thumbnail, 
                "desc" : v_desc,
                "channel": v_channel_title, 
                "channel_slug" : v_channel_slug,
                "mp4_url" : v_res_url,
                "views" : v_views
            })

    return recent

#
# Get metadata for specified video url
# TODO: May end up removing this
def get_video_metadata(url):
    metadata = {}
    
    data = HTTP.Request(url, cacheTime = CACHE_1MONTH).content

    soup = BeautifulSoup(data, "html.parser")
    
    metadata['desc'] = soup.find('meta', property='og:description').get('content')
    #metadata['uploaded'] = date
    metadata['views'] = soup.find('span', id="player-view-count").text
    
    return metadata