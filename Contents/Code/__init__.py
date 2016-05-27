from full30 import Full30

TITLE = 'Full30.com'
ART   = 'art-default.jpg'
ICON  = 'icon-default.jpg'

HTTP_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17"

BASE_URL = "https://www.full30.com"

full30 = Full30(BASE_URL)

##########################################################################################
def Start():
    # Setup the default attributes for the ObjectContainer
    ObjectContainer.title1 = TITLE
    ObjectContainer.art    = R(ART)

    # Setup the default attributes for the other objects
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art   = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art   = R(ART)

    HTTP.CacheTime             = CACHE_1HOUR
    HTTP.Headers['User-agent'] = HTTP_USER_AGENT
    
    ##########################################################################################
@handler('/video/fullthirty', TITLE, thumb = ICON, art = ART)
def MainMenu():
    oc = ObjectContainer()
    
    channels = full30.get_channels()
    
    for channel in channels:
	    title = channel['name']
	    oc.add(
		DirectoryObject(
		    key =
			Callback(
			    Channel_Recent,
			    title = title,
			    channel_url = channel['url']
			),
		    title = title
		)
	    )
    
    return oc

##########################################################################################
@route("/video/fullthirty/Recent")
def Channel_Recent(title, channel_url):
	
    container = Container.MP4
    video_codec = VideoCodec.H264
    audio_codec = AudioCodec.AAC
    audio_channels = 2
    
    oc = ObjectContainer(title2 = title)
    
    recent_videos = full30.get_recent_by_page(channel_url, 1)
    
    for video in recent_videos['videos']:
        url = video['mp4_url']
        title = video['title']
        
        try:
            thumb =video['thumbnail']
        except:
            thumb = R(ICON)
            
	episode = CreateEpisodeObject(url, title, title, thumb, False)
	
	oc.add(episode)
        
    return oc

def CreateEpisodeObject(url, title, summary, thumbnail = None, include_container=False):
    container = Container.MP4
    video_codec = VideoCodec.H264
    audio_codec = AudioCodec.AAC
    audio_channels = 2
    
    Log("CreateEpisodeObject: {0}".format(url))

    track_object = EpisodeObject(
        key = Callback(
            CreateEpisodeObject,
            url=url,
            title=title,
	    summary = summary,
            thumbnail=thumbnail,
            include_container=True
        ),
        rating_key = title,
        title = title,
        summary = title,
        thumb=thumbnail,
        originally_available_at = None,
        duration = None,
        producers = [],
        show = title,
        items = [
            MediaObject(
                parts = [
                    PartObject(key=Callback(PlayVideo, url=url))
                ],
                container = container,
                video_codec = video_codec,
                audio_codec = audio_codec,
                audio_channels = audio_channels,
            )
        ]
    )

    if include_container:
        return ObjectContainer(objects=[track_object])
    else:
        return track_object

def PlayVideo(url):
    return IndirectResponse(VideoClipObject, key=url)
	