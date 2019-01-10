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

VERSION         = 'V1.0.9'
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
SITE_VIDEOS_API_URL         = BASE_URL + '/api/v2.0/videos?order_by={0}&page={1}'
SITE_SECTIONS_API_URL       = BASE_URL + '/api/v2.0/videos?filter_section_id={0}&page={1}'
CHANNEL_URL                 = BASE_URL + '/channels/{0}'
CHANNEL_IMAGE_URL           = BASE_URL + '/cdn/c/b/{0}'
CHANNEL_VIDEOS_API_URL      = BASE_URL + '/api/v2.0/videos?order_by={0}&page={1}&channel={2}'


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

    #
    # Add 'Hot Videos' menu item
    oc.add(DirectoryObject(
        key =
        Callback(
            SiteListHotVideos,
            title = 'Hot Videos',
            page = 1
        ),
        title = 'Hot Videos',
        thumb = R(ICON)
    ))

    #
    # Add 'New Videos' menu item
    oc.add(DirectoryObject(
        key =
        Callback(
            SiteListNewVideos,
            title = 'New Videos',
            page = 1
        ),
        title = 'New Videos',
        thumb = R(ICON)
    ))

    #
    # Add 'Trending Videos' menu item
    oc.add(DirectoryObject(
        key =
        Callback(
            SiteListTrendingVideos,
            title = 'Trending Videos',
            page = 1
        ),
        title = 'Trending Videos',
        thumb = R(ICON)
    ))

    #
    # Sections menu item
    oc.add(DirectoryObject(
        key =
        Callback(
            SiteSections,
            title = 'Sections',
        ),
        title = 'Sections',
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
			    ChannelMenu,
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
# List All New videos
#
@route(ROUTE + '/AllNew')
def SiteListNewVideos(title, page = 1):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    new_videos = GetSiteVideos('new', page)
    
    limit = new_videos['pages']

    for video in new_videos['videos']:
        url = video['url']
        channel = video['channel']
        title = video['title']
        desc = video['desc']
        thumb = video['thumbnail']
        details_url = video['details_url']
        views = video['views']
        pub_date = video['pub_date']

        Log.Info('ListNewVideos - {0}; Channel={1}; Url={2}; Thumb={3}'.format(title, channel, url, thumb))

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
                SiteListNewVideos,
                title = 'New Videos - Page {0}'.format(next_page),
                page = next_page
            ),
            title = 'Page {0}'.format(next_page),
            summary = 'View more new videos'
       ))

    return oc

#
# List All Hot videos
#
@route(ROUTE + '/AllHot')
def SiteListHotVideos(title, page = 1):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    hot_videos = GetSiteVideos('hot', page)
    
    limit = hot_videos['pages']

    for video in hot_videos['videos']:
        url = video['url']
        channel = video['channel']
        title = video['title']
        desc = video['desc']
        thumb = video['thumbnail']
        details_url = video['details_url']
        views = video['views']
        pub_date = video['pub_date']

        Log.Info('ListHotVideos - {0}; Channel={1}; Url={2}; Thumb={3}'.format(title, channel, url, thumb))

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
                SiteListHotVideos,
                title = 'Hot Videos - Page {0}'.format(next_page),
                page = next_page
            ),
            title = 'Page {0}'.format(next_page),
            summary = 'View more hot videos'
       ))

    return oc

#
# List All Trending videos
#
@route(ROUTE + '/AllTrending')
def SiteListTrendingVideos(title, page = 1):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    trending_videos = GetSiteVideos('trending', page)
    
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
                SiteListTrendingVideos,
                title = 'Trending Videos - Page {0}'.format(next_page),
                page = next_page
            ),
            title = 'Page {0}'.format(next_page),
            summary = 'View more trending videos'
       ))

    return oc

#
# List Sections
#
@route(ROUTE + '/Sections')
def SiteSections(title):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    oc.add(DirectoryObject(
            key =
            Callback(
                SiteListSectionVideos,
                title = 'Long Guns',
                id = 1,
                page = 1
            ),
            title = 'Long Guns',
            summary = 'Long Guns'
       ))

    oc.add(DirectoryObject(
            key =
            Callback(
                SiteListSectionVideos,
                title = 'Hand Guns',
                id = 2,
                page = 1
            ),
            title = 'Hand Guns',
            summary = 'Hand Guns'
       ))

    oc.add(DirectoryObject(
            key =
            Callback(
                SiteListSectionVideos,
                title = 'Gear & Accessories',
                id = 3,
                page = 1
            ),
            title = 'Gear & Accessories',
            summary = 'Gear & Accessories'
       ))

    oc.add(DirectoryObject(
            key =
            Callback(
                SiteListSectionVideos,
                title = 'Hunting & Outdoors',
                id = 4,
                page = 1
            ),
            title = 'Hunting & Outdoors',
            summary = 'Hunting & Outdoors'
       ))

    oc.add(DirectoryObject(
            key =
            Callback(
                SiteListSectionVideos,
                title = 'Sounding Board',
                id = 5,
                page = 1
            ),
            title = 'Sounding Board',
            summary = 'Sounding Board'
       ))
    
    oc.add(DirectoryObject(
            key =
            Callback(
                SiteListSectionVideos,
                title = 'Miscellaneous',
                id = 6,
                page = 1
            ),
            title = 'Miscellaneous',
            summary = 'Miscellaneous'
       ))

    return oc

#
# List Section content by id
#
@route(ROUTE + '/SectionsList')
def SiteListSectionVideos(title, id, page = 1):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    section_title = title

    trending_videos = GetSiteSectionVideos(id, page)
    
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

        Log.Info('SiteListSectionVideos - {0}; id={1}; Url={2}; Thumb={3}'.format(title, id, url, thumb))

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
                SiteListTrendingVideos,
                title = '{0} Videos - Page {1}'.format(section_title, next_page),
                page = next_page
            ),
            title = '{0} Videos - Page {1}'.format(section_title, next_page),
            summary = 'View more {0} videos'.format(section_title)
       ))

    return oc

# 
# List 'New Videos', 'Hot Videos' and 'Trending Videos' for a specific channel
#
@route(ROUTE + '/Channel')
def ChannelMenu(title, channel_url, slug, thumbnail, banner):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    # Display New directory
    oc.add(DirectoryObject(
        key =
        Callback(
            ChannelListNew,
            title = 'New Videos',
            channel_slug = slug
        ),
        title = 'New Videos',
        thumb = Callback(GetThumb, url=thumbnail),
        art = Callback(GetThumb, url=banner),
    ))

    # Display Hot directory
    oc.add(DirectoryObject(
        key =
        Callback(
            ChannelListHot,
            title = 'Hot Videos',
            channel_slug = slug
        ),
        title = 'Hot Viewed',
        thumb = Callback(GetThumb, url=thumbnail),
        art = Callback(GetThumb, url=banner),
    ))

    # Display Trending directory
    oc.add(DirectoryObject(
        key =
        Callback(
            ChannelListTrending,
            title = 'Trending Videos',
            channel_slug = slug
        ),
        title = 'Trending Viewed',
        thumb = Callback(GetThumb, url=thumbnail),
        art = Callback(GetThumb, url=banner),
    ))

    return oc

#
# List 'New Videos' for the channel
@route(ROUTE + '/ChannelNew')
def ChannelListNew(title, channel_slug, page=1):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    new_videos = GetChannelVideos(channel_slug, 'new', page)
    
    limit = new_videos['pages']

    for video in new_videos['videos']:
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
                ChannelListNew,
                title = 'Recent Videos - Page {0}'.format(next_page),
                channel_slug = channel_slug,
                page = next_page
            ),
            title = 'Page {0}'.format(next_page),
            summary = 'View more videos'
       ))

    return oc

#
# List 'Hot Videos' for the channel
@route(ROUTE + '/ChannelHot')
def ChannelListHot(title, channel_slug, page=1):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    hot_videos = GetChannelVideos(channel_slug, 'hot', page)
    
    limit = hot_videos['pages']

    for video in hot_videos['videos']:
        url = video['url']
        channel = video['channel']
        title = video['title']
        desc = video['desc']
        thumb = video['thumbnail']
        details_url = video['details_url']
        views = video['views']
        pub_date = video['pub_date']

        Log.Info('Channel_ListHot - {0}; Channel={1}; Url={2}; Thumb={3}'.format(title, channel, url, thumb))
        
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
                ChannelListHot,
                title = 'Hot Videos - Page {0}'.format(next_page),
                channel_slug = channel_slug,
                page = next_page
            ),
            title = 'Page {0}'.format(next_page),
            summary = 'View hot videos'
       ))

    return oc

#
# List 'Trending Videos' for the channel
@route(ROUTE + '/ChannelTrending')
def ChannelListTrending(title, channel_slug, page=1):
    oc = ObjectContainer(title2 = title, view_group='InfoList')

    trending_videos = GetChannelVideos(channel_slug, 'trending', page)
    
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

        Log.Info('Channel_ListTrending - {0}; Channel={1}; Url={2}; Thumb={3}'.format(title, channel, url, thumb))
        
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
                ChannelListTrending,
                title = 'Trending Videos - Page {0}'.format(next_page),
                channel_slug = channel_slug,
                page = next_page
            ),
            title = 'Page {0}'.format(next_page),
            summary = 'View trending videos'
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
# Get site videos by a specific order_by filter
def GetSiteVideos(order_by, page):
    result = { 'pages' : '', 'videos' : [] }

    if not page:
        page = 1
    
    api_url = SITE_VIDEOS_API_URL.format(order_by, page)

    Log.Info('GetPopularVideos: url = ' + api_url)
    
    #html = HTTP.Request(api_url, cacheTime = 1200).content
    html = GetPage(api_url)
    
    if not html:
        return None
        
    data = json.loads(html)
    
    if not data:
        return None
        
    result['pages'] = data['meta']['pages']

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
        
        result['videos'].append(
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

    return result

#
# Get site videos by a specific order_by filter
def GetSiteSectionVideos(id, page):
    result = { 'pages' : '', 'videos' : [] }

    if not page:
        page = 1
    
    api_url = SITE_SECTIONS_API_URL.format(id, page)

    Log.Info('GetSiteSectionVideos: url = ' + api_url)
    
    #html = HTTP.Request(api_url, cacheTime = 1200).content
    html = GetPage(api_url)
    
    if not html:
        return None
        
    data = json.loads(html)
    
    if not data:
        return None
        
    result['pages'] = data['meta']['pages']

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
        
        result['videos'].append(
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

    return result

#
# Get videos for a specific channel using an order_by filter
def GetChannelVideos(channel, order_by, page):
    result = { 'pages' : '', 'videos' : [] }

    if not page:
        page = 1
    
    api_url = CHANNEL_VIDEOS_API_URL.format(order_by, page, channel)

    Log.Info('GetChannelVideos: url = ' + api_url)
    
    #html = HTTP.Request(api_url, cacheTime = 1200).content
    html = GetPage(api_url)
    
    if not html:
        return None
        
    data = json.loads(html)
    
    if not data:
        return None
        
    result['pages'] = data['meta']['pages']

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
        
        result['videos'].append(
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

    return result