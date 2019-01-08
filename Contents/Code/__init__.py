import urllib2
from bs4 import BeautifulSoup
import requests
import ssl
import re
import json
from datetime import datetime

GetPage = SharedCodeService.scrape.GetPage
GetThumb = SharedCodeService.scrape.GetThumb
RemoveTags = SharedCodeService.utils.RemoveTags

VERSION         = 'V1.0.8'
NAME            = 'Unofficial Full30.com Plex Channel'
TITLE           = 'Unofficial Full30.com Plex Channel'
ART             = 'art-default.jpg'
ICON            = 'icon-default.jpg'

HTTP_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17'

ROUTE                       = '/video/fullthirty'
BASE_URL                    = 'https://www.full30.com'
CHANNELS_API_URL            = BASE_URL + '/api/v2.0/channels?page={0}&per_page=25'
VIDEO_URL                   = BASE_URL + '/watch/{0}'
THUMBNAIL_URL               = BASE_URL + '/cdn/videos/{0}/{1}/thumbnails/320x180_{2}.jpg'
VIDEO_DETAILS_API_URL       = BASE_URL + '/api/v2.0/videos?filter_id={0}'
ALL_RECENT_API_URL          = BASE_URL + '/api/v2.0/videos?order_by=new&page={0}'
ALL_TRENDING_API_URL        = BASE_URL + '/api/v2.0/videos?order_by=trending&page={0}'

CHANNEL_URL                 = BASE_URL + '/channels/{0}'
CHANNEL_IMAGE_URL           = BASE_URL + '/cdn/c/b/{0}'
CHANNEL_RECENT_API_URL      = BASE_URL + '/api/v1.0/channel/{0}/recent-videos?page={1}'
CHANNEL_MOSTVIEWED_API_URL  = BASE_URL + '/api/v1.0/mostviewed/{0}?page={1}'


def Start():
    Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
    Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
    Plugin.AddViewGroup('Pictures', viewMode='Pictures', mediaType='items')

    ObjectContainer.title1      = TITLE
    ObjectContainer.art         = R(ART)
    ObjectContainer.view_group  = 'InfoList'

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)

    HTTP.CacheTime             = CACHE_1HOUR
    HTTP.Headers['User-agent'] = HTTP_USER_AGENT

    # For debugging
    #HTTP.ClearCache()
    
@handler(ROUTE, TITLE, thumb = ICON, art = ART)
def MainMenu():
    oc = ObjectContainer(no_cache=True)

    #
    # Add 'Recent Videos' menu item
    oc.add(DirectoryObject(
        key =
        Callback(
            ListRecentVideos,
            title = 'Recent Videos',
            page = 1
        ),
        title = 'Recent Videos',
        thumb = R(ICON)
    ))

    #
    # Add 'Trending Videos' menu item
    oc.add(DirectoryObject(
        key =
        Callback(
            ListTrendingVideos,
            title = 'Trending Videos',
            page = 1
        ),
        title = 'Trending Videos',
        thumb = R(ICON)
    ))

    #
    # Add 'All Channels' menu item
    oc.add(DirectoryObject(
        key =
        Callback(
            ListChannels,
            title = 'All Channels'
        ),
        title = 'All Channels',
        thumb = R(ICON)
    ))

    return oc
#
# List All Channels
@route(ROUTE + '/AllChannels')
def ListChannels(title, page = 1):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    channels = GetChannels(page)
    limit = channels['pages']

    for channel in channels['channels']:
        title = channel['name']
        thumbnail = channel['thumbnail']
        url = channel['url']
        slug = channel['slug']
        banner = channel['banner']
        desc = channel['desc']
        subscribers = channel['subscribers']

        Log.Info('ListChannels - {0}; Slug={1}; Url={2}; Thumb={3}'.format(title, slug, url, thumbnail))

        oc.add(DirectoryObject(
            key =
			Callback(
			    Channel_Menu,
			    title = title,
			    channel_url = url,
                slug = slug,
                thumbnail = thumbnail,
                banner = banner
		    ),
		    title = title,
            thumb = Callback(GetThumb, url = thumbnail),
            art = Callback(GetThumb, url = banner),
            summary = desc + '\n\r\n\r' + 'Subscribers: {0}'.format(subscribers)
		))
    
    next_page = int(page) + 1
    if next_page <= limit:
        oc.add(DirectoryObject(
            key =
            Callback(
                ListChannels,
                title = 'All Channels - Page {0}'.format(next_page),
                page = next_page
            ),
            title = 'Page {0}'.format(next_page),
            summary = 'View more channels'
       ))

    return oc

#
# List All Recent videos
#
@route(ROUTE + '/AllRecent')
def ListRecentVideos(title, page = 1):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    recent_videos = GetAllRecent(page)
    
    limit = recent_videos['pages']

    for video in recent_videos['videos']:
        url = video['url']
        channel = video['channel']
        title = video['title']
        desc = video['desc']
        thumb = video['thumbnail']
        details_url = video['details_url']
        views = video['views']
        pub_date = video['pub_date']

        Log.Info('ListRecentVideos - {0}; Channel={1}; Url={2}; Thumb={3}'.format(title, channel, url, thumb))

        oc.add(VideoClipObject(
            url = details_url,
            title = '{0} - {1}'.format(channel, title),
            summary = '{0} views - {1}'.format(views, desc),
            thumb = Callback(GetThumb, url=thumb),
            originally_available_at = pub_date.date(),
	        year = pub_date.year,
            rating_key = details_url
        ))	

    next_page = int(page) + 1
    if next_page <= limit:
        oc.add(DirectoryObject(
            key =
            Callback(
                ListRecentVideos,
                title = 'Recent Videos - Page {0}'.format(next_page),
                page = next_page
            ),
            title = 'Page {0}'.format(next_page),
            summary = 'View more recent videos'
       ))

    return oc

#
# List All Trending videos
#
@route(ROUTE + '/AllTrending')
def ListTrendingVideos(title, page = 1):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    trending_videos = GetAllTrending(page)
    
    limit = trending_videos['pages']

    for video in trending_videos['videos']:
        url = video['url']
        channel = video['channel']
        title = video['title']
        desc = video['desc']
        thumb = video['thumbnail']
        details_url = video['details_url']
        views = video['views']
        pub_date = video['pub_date']

        Log.Info('ListTrendingVideos - {0}; Channel={1}; Url={2}; Thumb={3}'.format(title, channel, url, thumb))

        oc.add(VideoClipObject(
            url = details_url,
            title = '{0} - {1}'.format(channel, title),
            summary = '{0} views - {1}'.format(views, desc),
            thumb = Callback(GetThumb, url=thumb),
            originally_available_at = pub_date.date(),
	        year = pub_date.year,
            rating_key = details_url
        ))	

    next_page = int(page) + 1
    if next_page <= limit:
        oc.add(DirectoryObject(
            key =
            Callback(
                ListTrendingVideos,
                title = 'Trending Videos - Page {0}'.format(next_page),
                page = next_page
            ),
            title = 'Page {0}'.format(next_page),
            summary = 'View more trending videos'
       ))

    return oc

# 
# List 'Featured Videos' and 'Recent Videos' folders for the channel
#
@route(ROUTE + '/Channel')
def Channel_Menu(title, channel_url, slug, thumbnail, banner):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    # Display Most Viewed directory
    oc.add(DirectoryObject(
        key =
        Callback(
            Channel_MostViewed,
            title = 'Most Viewed Videos',
            channel_slug = slug
        ),
        title = 'Most Viewed',
        thumb = Callback(GetThumb, url=thumbnail),
        art = Callback(GetThumb, url=banner),
    ))

    # Display Recent directory
    oc.add(DirectoryObject(
        key =
        Callback(
            Channel_ListRecent,
            title = 'Recent Videos',
            channel_slug = slug
        ),
        title = 'Recent Videos',
        thumb = Callback(GetThumb, url=thumbnail),
        art = Callback(GetThumb, url=banner),
    ))

    return oc

#
# List 'Most Viewed Videos' for the channel
@route(ROUTE + '/MostViewed')
def Channel_MostViewed(title, channel_slug, page=1):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    mostviewed_videos = GetChannelMostViewed(channel_slug, page)
    
    limit = mostviewed_videos['pages']

    for video in mostviewed_videos['videos']:
        url = video['url']
        channel = video['channel']
        title = video['title']
        desc = video['desc']
        thumb = video['thumbnail']
        details_url = video['details_url']
        views = video['views']
        pub_date = video['pub_date']

        Log.Info('Channel_MostViewed - {0}; Channel={1}; Url={2}; Thumb={3}'.format(title, channel, url, thumb))
        
        oc.add(VideoClipObject(
            url = details_url,
            title = '{0} - {1}'.format(channel, title),
            summary = '{0} views - {1}'.format(views, desc),
            thumb = Callback(GetThumb, url=thumb),
            originally_available_at = pub_date.date(),
	        year = pub_date.year,
            rating_key = details_url
        ))		

    next_page = int(page) + 1
    if next_page <= limit:
        oc.add(DirectoryObject(
            key =
            Callback(
                Channel_MostViewed,
                title = 'Most Viewed Videos - Page {0}'.format(next_page),
                channel_slug = channel_slug,
                page = next_page
            ),
            title = 'Page {0}'.format(next_page),
            summary = 'View more videos'
       ))

    return oc

#
# List 'Recent Videos' for the channel
@route(ROUTE + '/Recent')
def Channel_ListRecent(title, channel_slug, page=1):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    recent_videos = GetChannelRecent(channel_slug, page)
    
    limit = recent_videos['pages']

    for video in recent_videos['videos']:
        url = video['url']
        channel = video['channel']
        title = video['title']
        desc = video['desc']
        thumb = video['thumbnail']
        details_url = video['details_url']
        pub_date = video['pub_date']

        Log.Info('Channel_ListRecent - {0}; Channel={1}; Url={2}; Thumb={3}'.format(title, channel, url, thumb))
        
        oc.add(VideoClipObject(
            url = details_url,
            title = title,
            summary  = desc,
            thumb = Callback(GetThumb, url=thumb),
            rating_key = details_url,
            originally_available_at = pub_date.date(),
	        year = pub_date.year,
        ))		

    next_page = int(page) + 1
    if next_page <= limit:
        oc.add(DirectoryObject(
            key =
            Callback(
                Channel_ListRecent,
                title = 'Recent Videos - Page {0}'.format(next_page),
                channel_slug = channel_slug,
                page = next_page
            ),
            title = 'Page {0}'.format(next_page),
            summary = 'View more videos'
       ))

    return oc

#
# Get list of all channels from full30.com
def GetChannels(page = 1):
    channels = { 'pages' : '', 'channels' : [] }
    
    channel_url = CHANNELS_API_URL.format(page)

    Log.Info('GetChannels: url = ' + channel_url)

    html = GetPage(channel_url)
    
    if not html:
        return None
        
    data = json.loads(html)
    
    if not data:
        return None

    channels['pages'] = data['meta']['pages']

    for video in data['data']:
        channel_url = CHANNEL_URL.format(video['slug'])

        channel_name = video['title']
        channel_thumbnail = '' if video['profile_filename'] is None else CHANNEL_IMAGE_URL.format(video['profile_filename'])
        channel_desc = video['description']
        channel_banner = '' if video['banner_filename'] is None else CHANNEL_IMAGE_URL.format(video['banner_filename'])
        channel_subscribers = video['subscriber_count']
        channel_slug = video['slug']

        channel_desc = RemoveTags(channel_desc)

        channels['channels'].append(
            { 
                "name" : channel_name, 
                "url" : channel_url, 
                "thumbnail" : channel_thumbnail,
                "desc" : channel_desc,
                "banner" : channel_banner,
                "subscribers" : channel_subscribers,
                "slug" : channel_slug
            })

    return channels

#
# Get a list of most viewed videos for specified channel
def GetChannelMostViewed(slug, page):
    mostviewed = { 'pages' : '', 'videos' : [] }

    if not page:
        page = 1
    
    api_url = CHANNEL_MOSTVIEWED_API_URL.format(slug, page)

    Log.Info('GetChannelMostViewed: url = ' + api_url)
    
    #html = HTTP.Request(api_url, cacheTime = 1200).content
    html = GetPage(api_url)
    
    if not html:
        return None
        
    data = json.loads(html)
    
    if not data:
        return None
        
    mostviewed['pages'] = data['pages']

    for key,value in data['videos'].iteritems():
        video = data['videos'][key]

        v_channel_slug = video['channel_slug']
        v_channel_title = video['channel_title']
        v_desc = video['description']
        v_hash = video['hashed_identifier']
        v_id = video['id']
        v_thumbnail = THUMBNAIL_URL.format(v_channel_slug, v_hash, video['thumbnail_filename'])
        v_title = video['title']
        v_views = video['view_count']
        v_title = video['title']
        v_url = VIDEO_URL.format(v_hash)      
        v_pub_date = datetime.strptime(video['publication_date'], '%a, %d %b %Y %H:%M:%S %Z')  

        # Remove markup from desc
        v_desc = RemoveTags(v_desc)

        v_details_url = VIDEO_DETAILS_API_URL.format(v_id)
        
        mostviewed['videos'].append(
            { 
                'title' : v_title, 
                'url' : v_url, 
                'thumbnail' : v_thumbnail, 
                'desc' : v_desc,
                'channel' : v_channel_title, 
                'channel_slug' : v_channel_slug,
                'details_url' : v_details_url,
                'views' : v_views,
                'pub_date' : v_pub_date,
                'id' : v_id
            })

    # Sort videos by ID which seems like is the proper order
    mostviewed['videos'] = sorted(mostviewed['videos'], key=lambda k: k['id'], reverse=True) 

    return mostviewed

#
# Get a list of most recent videos for specified channel
def GetChannelRecent(slug, page):
    recent = { 'pages' : '', 'videos' : [] }

    if not page:
        page = 1
    
    api_url = CHANNEL_RECENT_API_URL.format(slug, page)
    
    Log.Info('GetChannelRecent: url = ' + api_url)

    #html = HTTP.Request(api_url, cacheTime = 1200).content
    html = GetPage(api_url)
    
    if not html:
        return None
        
    data = json.loads(html)
    
    if not data:
        return None
        
    recent['pages'] = data['pages']
    channel = data['channel']

    for video in data['videos']:
        v_channel_slug = channel['slug']
        v_channel_title = channel['title']

        v_hash = video['hashed_identifier']
        v_b64 = video['b64_identifier']
        v_id = video['id']
        v_thumbnail = THUMBNAIL_URL.format(channel['slug'], video['hashed_identifier'], video['thumbnail_filename'])
        v_title = video['title']
        v_desc = v_title
        v_pub_date = None

        v_url = VIDEO_URL.format(v_b64)      

        v_details_url = VIDEO_DETAILS_API_URL.format(v_id)

        # Get video details
        v_details_html = GetPage(v_details_url)

        if v_details_html:
            v_details_data = json.loads(v_details_html)

            if v_details_data:
                v_desc = v_details_data['data'][0]['meta']['description']
                v_pub_date = datetime.strptime(v_details_data['data'][0]['meta']['publication_date'], '%m/%d/%Y')
 
        # Remove markup from desc
        v_desc = RemoveTags(v_desc)

        recent['videos'].append(
            { 
                'title' : v_title, 
                'url' : v_url, 
                'thumbnail' : v_thumbnail, 
                'desc' : v_desc,
                'channel' : v_channel_title, 
                'channel_slug' : v_channel_slug,
                'details_url' : v_details_url,
                'pub_date' : v_pub_date,
                'id' : v_id
            })

    # Sort videos by ID which seems like is the proper order
    recent['videos'] = sorted(recent['videos'], key=lambda k: k['id'], reverse=True)

    return recent

#
# Get all recent videos on full30.com by page
def GetAllRecent(page):
    recent = { 'pages' : '', 'videos' : [] }

    if not page:
        page = 1
    
    api_url = ALL_RECENT_API_URL.format(page)

    Log.Info('GetAllRecent: url = ' + api_url)
    
    #html = HTTP.Request(api_url, cacheTime = 1200).content
    html = GetPage(api_url)
    
    if not html:
        return None
        
    data = json.loads(html)
    
    if not data:
        return None
        
    recent['pages'] = data['meta']['pages']

    for post in data['data']:
        channel = post['channel']
        meta = post['meta']
        
        v_channel_slug = channel['slug']
        v_channel_title = channel['title']
        v_desc = meta['description']
        v_hash = meta['hashed_identifier']
        v_b64 = meta['b64_id']
        v_id = meta['id']

        v_thumbnail = post['images']['thumbnails'][0]
        if v_thumbnail.startswith('http') == False:
            v_thumbnail = BASE_URL + v_thumbnail

        v_title = meta['title']
        v_views = meta['view_count']

        v_url = VIDEO_URL.format(v_hash)        
        v_pub_date = datetime.strptime(meta['publication_date'], '%m/%d/%Y')

        # Remove markup from desc
        v_desc = RemoveTags(v_desc)

        v_details_url = VIDEO_DETAILS_API_URL.format(v_id)
        
        recent['videos'].append(
            { 
                'title' : v_title, 
                'url' : v_url, 
                'thumbnail' : v_thumbnail, 
                'desc' : v_desc,
                'channel' : v_channel_title, 
                'channel_slug' : v_channel_slug,
                'details_url' : v_details_url,
                'views' : v_views,
                'pub_date' : v_pub_date,
                'id' : v_id
            })

    # Sort videos by ID which seems like is the proper order
    recent['videos'] = sorted(recent['videos'], key=lambda k: k['id'], reverse=True)

    return recent

#
# Get all trending videos on full30.com by page
def GetAllTrending(page):
    trending = { 'pages' : '', 'videos' : [] }

    if not page:
        page = 1
    
    api_url = ALL_TRENDING_API_URL.format(page)

    Log.Info('GetAllTrending: url = ' + api_url)
    
    html = GetPage(api_url)
    
    if not html:
        return None
        
    data = json.loads(html)
    
    if not data:
        return None
        
    trending['pages'] = data['meta']['pages']

    for post in data['data']:
        channel = post['channel']
        meta = post['meta']
        
        v_channel_slug = channel['slug']
        v_channel_title = channel['title']
        v_desc = meta['description']
        v_hash = meta['hashed_identifier']
        v_b64 = meta['b64_id']
        v_id = meta['id']

        v_thumbnail = post['images']['thumbnails'][0]
        if v_thumbnail.startswith('http') == False:
            v_thumbnail = BASE_URL + v_thumbnail

        v_title = meta['title']
        v_views = meta['view_count']

        v_url = VIDEO_URL.format(v_hash)        
        v_pub_date = datetime.strptime(meta['publication_date'], '%m/%d/%Y')

        # Remove markup from desc
        v_desc = RemoveTags(v_desc)

        v_details_url = VIDEO_DETAILS_API_URL.format(v_id)
        
        trending['videos'].append(
            { 
                'title' : v_title, 
                'url' : v_url, 
                'thumbnail' : v_thumbnail, 
                'desc' : v_desc,
                'channel' : v_channel_title, 
                'channel_slug' : v_channel_slug,
                'details_url' : v_details_url,
                'views' : v_views,
                'pub_date' : v_pub_date,
                'id' : v_id
            })

    # Sort videos by ID which seems like is the proper order
    trending['videos'] = sorted(trending['videos'], key=lambda k: k['id'], reverse=True)

    return trending
