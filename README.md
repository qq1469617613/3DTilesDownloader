# Download Google Maps 3D Tiles and convert to ceisum 3d tiles

Download Google Maps 3D Tiles as ceisum 3d tiles  (these can, for example, be imported into ceisum or deckgl or other usages).

Example:

```python
from scripts.get_tileset import download_tileset

lon,lat = 114.17242851577525,22.29458442453952
radius = 80
output_path = 'result_hk3'

download_tileset(lon,
                 lat,
                 radius,
                 api_key = 'Input your api key',
                 output_path='result',
                 thread_count=30)
```

![example](imgs/example.png)