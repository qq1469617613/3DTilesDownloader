# Download Google Maps 3D Tiles and convert to ceisum 3d tiles

Download Google Maps 3D Tiles as [ceisum 3d tiles](https://cesium.com/why-cesium/3d-tiles/)  (these can, for example, be imported into ceisum or deckgl or other usages).

You need to obtain a [google map api key](https://developers.google.com/maps/documentation/javascript/get-api-key) and make sure to enable [3D tiles](https://developers.google.cn/maps/documentation/tile/3d-tiles?) to use this script.

## Example

```python
from scripts.get_tileset import download_tileset

lon,lat = 114.17242851577525,22.29458442453952
radius = 80
output_path = 'result_hk3'

download_tileset(lon,
                 lat,
                 radius,
                 api_key = 'Paste your google map api key here',
                 output_path='result',
                 thread_count=30)
```

![example](imgs/example.png)