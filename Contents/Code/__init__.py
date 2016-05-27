from full30 import Full30

TITLE = 'Full30.com'
ART   = 'art-default.jpg'
ICON  = 'icon-default.jpg'

HTTP_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17"

ROUTE = "/video/fullthirty"
BASE_URL = "https://www.full30.com"

full30 = Full30(BASE_URL)

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
    
    channels = full30.get_channels()
    
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
# List Featured and Recent folders for the channel
#
@route(ROUTE + "/Channel")
def Channel_Menu(title, channel_url, thumbnail):
    oc = ObjectContainer(title2 = title)

    # Display Featured directory
    oc.add(DirectoryObject(
        key = 
        Callback(
            Channel_Featured,
            title = "Featured Videos",
            channel_url = channel_url
        ),
        title = "Featured Videos",
        thumb = thumbnail
    ))

    # Display Recent directory
    oc.add(DirectoryObject(
        key =
        Callback(
            Channel_Recent,
            title = "Recent Videos",
            channel_url = channel_url
        ),
        title = "Recent Videos",
        thumb = thumbnail
    ))

    return oc
        

@route(ROUTE + "/Recent")
def Channel_Recent(title, channel_url, page=1):
    oc = ObjectContainer(title2 = title)

    recent_videos = full30.get_recent_by_page(channel_url, page)
    
    limit = recent_videos['pages']

    for video in recent_videos['videos']:
        url = video['url']
        title = video['title']
        thumb = video['thumbnail']
        
        oc.add(VideoClipObject(
            url = url,
            title = title,
            summary = title,
            thumb = thumb
        ))	

    next_page = int(page) + 1
    if next_page <= limit:
        oc.add(DirectoryObject(
            key =
            Callback(
                Channel_Recent,
                title = "Recent Videos - Page {0}".format(next_page),
                channel_url = channel_url,
                page = next_page
            ),
            title = "Page {0}".format(next_page),
            summary = "View more videos"
       ))
            
        
    return oc

@route(ROUTE + "/Featured")
def Channel_Featured(title, channel_url):
    oc = ObjectContainer(title2 = title)

    featured_videos = full30.get_featured(channel_url)

    for video in featured_videos:
        url = video['url']
        title = video['title']
        thumb = video['thumbnail']

        oc.add(VideoClipObject(
            url = url,
            title = title,
            summary = title,
            thumb = thumb
        ))

    return oc
