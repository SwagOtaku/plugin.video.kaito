def allocate_item(name, url, is_dir=False, image='', info='', fanart=None, poster=None):
    new_res = {}
    new_res['is_dir'] = is_dir
    new_res['image'] = {
        'poster': poster,
        'thumb': image,
        'fanart': fanart
        }
    new_res['name'] = name
    new_res['url'] = url
    new_res['info'] = info
    return new_res
