import os
from resources.lib.ui import control


def allocate_item(name, url, is_dir=False, image='', info='', fanart=None, poster=None):
    new_res = {}
    new_res['is_dir'] = is_dir
    if image and '/' not in image:
        image = os.path.join(control.artPath(), image)
    if fanart and '/' not in fanart:
        fanart = os.path.join(control.artPath(), fanart)
    if poster and '/' not in poster:
        poster = os.path.join(control.artPath(), poster)
    new_res['image'] = {
        'poster': poster or image,
        'icon': image,
        'thumb': image,
        'fanart': fanart
    }
    new_res['name'] = name
    new_res['url'] = url
    new_res['info'] = info
    return new_res
