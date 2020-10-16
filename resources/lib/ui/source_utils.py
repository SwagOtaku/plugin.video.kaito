import re
import string

def strip_non_ascii_and_unprintable(text):
    result = ''.join(char for char in text if char in string.printable)
    return result.encode('ascii', errors='ignore').decode('ascii', errors='ignore')

def getAudio_lang(release_title):
    lang = 0
    release_title = cleanTitle(release_title)
    if any(i in release_title for i in ['dual audio']):
        lang = 1
    if any(i in release_title for i in ['dub', 'dubbed']):
        lang = 2

    return lang
    
def getInfo(release_title):
    info = []
    release_title = cleanTitle(release_title)
    #info.video
    if any(i in release_title for i in ['x264', 'x 264', 'h264', 'h 264', 'avc']):
        info.append('AVC')
    if any(i in release_title for i in ['x265', 'x 265', 'h265', 'h 265', 'hevc']):
        info.append('HEVC')
    if any(i in release_title for i in ['xvid']):
        info.append('XVID')
    if any(i in release_title for i in ['divx']):
        info.append('DIVX')
    if any(i in release_title for i in ['mp4']):
        info.append('MP4')
    if any(i in release_title for i in ['wmv']):
        info.append('WMV')
    if any(i in release_title for i in ['mpeg']):
        info.append('MPEG')
    if any(i in release_title for i in ['remux', 'bdremux']):
        info.append('REMUX')
    if any(i in release_title for i in [' hdr ', 'hdr10', 'hdr 10']):
        info.append('HDR')
    if any(i in release_title for i in [' sdr ']):
        info.append('SDR')
    
    #info.audio
    if any(i in release_title for i in ['aac']):
        info.append('AAC')
    if any(i in release_title for i in ['dts']):
        info.append('DTS')
    if any(i in release_title for i in ['hd ma' , 'hdma']):
        info.append('HD-MA')
    if any(i in release_title for i in ['atmos']):
        info.append('ATMOS')
    if any(i in release_title for i in ['truehd', 'true hd']):
        info.append('TRUEHD')
    if any(i in release_title for i in ['ddp', 'dd+', 'eac3']):
        info.append('DD+')
    if any(i in release_title for i in [' dd ', 'dd2', 'dd5', 'dd7', ' ac3']):
        info.append('DD')
    if any(i in release_title for i in ['mp3']):
        info.append('MP3')
    if any(i in release_title for i in [' wma']):
        info.append('WMA')
    if any(i in release_title for i in ['dub', 'dubbed']):
        info.append('DUB')
    if any(i in release_title for i in ['dual audio']):
        info.append('DUAL-AUDIO')
    
    #info.channels
    if any(i in release_title for i in ['2 0 ', '2 0ch', '2ch']):
        info.append('2.0')
    if any(i in release_title for i in ['5 1 ', '5 1ch', '6ch']):
        info.append('5.1')
    if any(i in release_title for i in ['7 1 ', '7 1ch', '8ch']):
        info.append('7.1')
    
    #info.source 
    # no point at all with WEBRip vs WEB-DL cuz it's always labeled wrong with TV Shows 
    # WEB = WEB-DL in terms of size and quality
    if any(i in release_title for i in ['bluray' , 'blu ray' , 'bdrip', 'bd rip', 'brrip', 'br rip']):
        info.append('BLURAY')
    if any(i in release_title for i in [' web ' , 'webrip' , 'webdl', 'web rip', 'web dl']):
        info.append('WEB')
    if any(i in release_title for i in ['hdrip', 'hd rip']):
        info.append('HDRIP')
    if any(i in release_title for i in ['dvdrip', 'dvd rip']):
        info.append('DVDRIP')
    if any(i in release_title for i in ['hdtv']):
        info.append('HDTV')
    if any(i in release_title for i in ['pdtv']):
        info.append('PDTV')
    if any(i in release_title for i in [' cam ', 'camrip', 'hdcam', 'hd cam', ' ts ', 'hd ts', 'hdts', 'telesync', ' tc ', 'hd tc', 'hdtc', 'telecine', 'xbet']):
        info.append('CAM')
    if any(i in release_title for i in ['dvdscr', ' scr ', 'screener']):
        info.append('SCR')
    if any(i in release_title for i in ['korsub', ' kor ', ' hc']):
        info.append('HC')
    if any(i in release_title for i in ['blurred']):
        info.append('BLUR')
    if any(i in release_title for i in [' 3d']):
        info.append('3D')
        
    return info

def get_best_match(episode, filename):
    filename = re.sub(r'\[.*?\]', '', filename)
    match = re.search(
        r'''(?ix)                                           # Ignore case (i), and use verbose regex (x)
        (?:                                                 # non-grouping pattern
          e|x|episode|ep|ep\.|_|-                            # e or x or episode or start of a line
          )                                                 # end non-grouping pattern 
        \s*                                                 # 0-or-more whitespaces
        (?<![\d])
        ({}|{})                                             # episode num format: xx or xxx
        (?![\d])
        '''.format(episode.zfill(2), episode.zfill(3)), filename)
    if match:
        return match.group(1)

def cleanTitle(title):
    title = clean_title(title)
    return title

def clean_title(title, broken=None):
    title = title.lower()
    # title = tools.deaccentString(title)
    title = strip_non_ascii_and_unprintable(title)

    if broken == 1:
        apostrophe_replacement = ''
    elif broken == 2:
        apostrophe_replacement = ' s'
    else:
        apostrophe_replacement = 's'
    title = title.replace("\\'s", apostrophe_replacement)
    title = title.replace("'s", apostrophe_replacement)
    title = title.replace("&#039;s", apostrophe_replacement)
    title = title.replace(" 039 s", apostrophe_replacement)

    title = re.sub(r'\:|\\|\/|\,|\!|\?|\(|\)|\'|\"|\\|\[|\]|\-|\_|\.', ' ', title)
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'\&', 'and', title)

    return title.strip()

def is_file_ext_valid(file_name):
    try:
        import xbmc

        COMMON_VIDEO_EXTENSIONS = xbmc.getSupportedMedia('video').split('|')

        COMMON_VIDEO_EXTENSIONS = [i for i in COMMON_VIDEO_EXTENSIONS if i != '' and i != '.zip']
    except:
        pass

    if '.' + file_name.split('.')[-1] not in COMMON_VIDEO_EXTENSIONS:
        return False

    return True
