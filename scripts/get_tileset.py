def check_glb(tile, glb_list):
    # 如果有content字段，且uri字段在glb_list中，则返回True
    if tile != None:
        if "content" in tile and "uri" in tile["content"]:
            if tile['content']['uri'] in glb_list:
                return True

        if 'children' in tile:
            for child_tile in tile['children']:
                if check_glb(child_tile, glb_list):
                    return True
            return False
        else:
            return False
    else:
        return False


def filter_tiles(tile, glb_list):
    #递归过滤，删除不满足条件的 children。
    if "content" in tile and "uri" in tile["content"]:
        if tile['content']['uri'] not in glb_list:
            #tile去掉content字段
            tile.pop('content')
            
    # 检查当前tile是否需要保留
    if not check_glb(tile, glb_list):
        return None
    
    # 如果有children，递归过滤
    if "children" in tile:
        filtered_children = []
        for child in tile["children"]:
            filtered_child = filter_tiles(child, glb_list)
            if filtered_child is not None:
                filtered_children.append(filtered_child)
        tile["children"] = filtered_children

    # 如果当前节点只有一个子节点，则只保留子节点
    if "children" in tile and len(tile["children"]) == 1:
        return tile["children"][0]
    
    return tile

def update_bounding_volume(tile):
    if "children" in tile and len(tile["children"]) > 0:
        #for child in tile["children"]:
        #    update_bounding_volume(child)
        
        # 获取所有子节点的 boundingVolume
        child_boxes = [child["boundingVolume"]["box"] for child in tile["children"]]

        # 更新父节点的 boundingVolume
        tile["boundingVolume"]["box"] = [
            min(box[0] for box in child_boxes),  # minX
            min(box[1] for box in child_boxes),  # minY
            min(box[2] for box in child_boxes),  # minZ
            max(box[3] for box in child_boxes),  # maxX
            max(box[4] for box in child_boxes),  # maxY
            max(box[5] for box in child_boxes),  # maxZ
            min(box[6] for box in child_boxes),  # center X
            min(box[7] for box in child_boxes),  # center Y
            min(box[8] for box in child_boxes),  # center Z
            max(box[9] for box in child_boxes),  # radius
            max(box[10] for box in child_boxes), # halfSize X
            max(box[11] for box in child_boxes)  # halfSize Y
        ]
def update_geometricError(tile):
    if "children" in tile and len(tile["children"]) > 0:
        for child in tile["children"]:
            update_geometricError(child)
        tile["geometricError"] = max(child["geometricError"] for child in tile["children"])*2

    if "children" in tile and len(tile["children"]) > 0:
        for child in tile["children"]:
            update_geometricError(child)
        tile["geometricError"] *=30

def json2tileset(thisjson,glbfiles):
    import json
    # 将字典转换为 JSON 字符串
    json_str = json.dumps(thisjson, indent=4)
    tileset_dict = json.loads(json_str.replace('/v1/3dtiles/datasets/CgA/files/','./'))
    # 示例 glb 列表
    glb_list = ['./'+glbfile for glbfile in glbfiles]

    # 过滤 root 下的 children
    filtered_root = filter_tiles(tileset_dict["root"], glb_list)


    # 如果根节点本身不满足条件，filtered_root 会是 None
    if filtered_root is not None:
        tileset_dict["root"] = filtered_root
        # 更新 boundingVolume
        update_bounding_volume(tileset_dict["root"])
        update_geometricError(tileset_dict["root"])
    else:
        # 处理根节点不满足条件的情况（例如，清空 children 或其他逻辑）
        tileset_dict["root"]["children"] = [] 

    return filtered_root
from src.tile_api import TileApi
from src.bounding_volume import Sphere
from src.wgs84 import cartesian_from_degrees
from scripts.download_tiles import _get_elevation

def download_tileset(lon,lat,radius,api_key,output_path='result',thread_count=30):
    print('Searching tileset...')
    elevation = _get_elevation(lon,lat ,api_key)
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from pathlib import Path
    import tqdm
    from tenacity import retry, stop_after_attempt, wait_fixed

    api = TileApi(key=api_key)

    tiles = list(tqdm.tqdm(api.get(Sphere(
        cartesian_from_degrees(lon, lat, elevation),
        radius
    ))))

    outdir = Path(output_path)
    outdir.mkdir(parents=True, exist_ok=True)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def download_tile(tile, index):
        data = tile.data
        with open(outdir / Path(f"{tile.basename}.glb"), "wb") as f:
            f.write(data)
        return index, True

    def download_tile_with_retry(tile, index):
        try:
            return download_tile(tile, index)
        except Exception as e:
            return index, False


    print("Downloading tiles...")
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [executor.submit(download_tile_with_retry, t, i) for i, t in enumerate(tiles)]
        
        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            index, success = future.result()
            if not success:
                print(f"Failed to download tile {index}")

    print("All tiles downloaded.")

    jsons = api.jsons

    import os

    glbfiles = os.listdir(output_path)
    glbfiles = [glbfile for glbfile in glbfiles if glbfile[-3:]=='glb']
    glbfiles_long = ['/v1/3dtiles/datasets/CgA/files/'+glbfile for glbfile in glbfiles] 
    thisjsons = [ thisjson for thisjson in jsons if check_glb(thisjson['root'],glbfiles_long)]

    tileset_jsons = [json2tileset(thisjson,glbfiles)for thisjson in thisjsons]

    tileset = json2tileset({
        'root': {
            'boundingVolume': {
                'box':[]
            },
            'geometricError': max([tileset_json['geometricError'] for tileset_json in tileset_jsons]),
            'children': tileset_jsons
        }
    },glbfiles)
    import json
    tileset = {'root':tileset,
    'asset':{'generatetool':'transbigdata',
            'version':'1.0'},
    }
    tileset['root']['boundingVolume']['box'] = tileset['root']['children'][0]['boundingVolume']['box']
    json.dump(tileset, open(f'{output_path}/tileset.json', 'w'))
    print('tileset.json saved')
    print('All done! Saved to',output_path)
