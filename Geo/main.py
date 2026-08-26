import json
import os
import folium
from folium.plugins import MarkerCluster

# 1). paths for your GeoJSON file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
geojson_path = os.path.join(BASE_DIR, "parks.geojson")
output_path = os.path.join(BASE_DIR, "mmr_ultimate_map.html")

if not os.path.exists(geojson_path):
    print("❌ Error: Could not find 'parks.geojson'!")
    print("Make sure it is saved in the same folder as this script.")
    exit()


# 2. Map Configuration [center, bounds]
mmr_center = [19.1136, 72.8697]
south_limit = 18.80
north_limit = 19.50
west_limit = 72.60
east_limit = 73.30

mmr_bounds = [
    [18.80, 72.60],  # South-West corner
    [19.50, 73.30]   # North-East corner
]

# 3. Create the Map
mumbai_map = folium.Map(
    location=mmr_center,
    zoom_start=11,
    min_zoom=10,
    max_zoom=17,
    min_lat=south_limit,
    max_lat=north_limit,
    min_lon=west_limit,
    max_lon=east_limit,
    max_bounds=True,
    tiles=None,
    prefer_canvas=True,
)

# Added the base tile layer manually with control = False
folium.TileLayer(
    tiles="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles courtesy of <a href="https://www.hotosm.org/">Humanitarian OpenStreetMap Team</a>',
    name="OSM HOT",
    control=False,
    min_zoom=10,
    max_zoom=17,
    bounds=mmr_bounds
).add_to(mumbai_map)

# 4. Add Suburb Markers

#this is for the button
suburbs_group = folium.FeatureGroup(name="Districts", show=True).add_to(mumbai_map)

regions = {
    "South Mumbai (City)": [18.9388, 72.8258],
    "Mumbai Suburban": [19.1136, 72.8697],
    "Navi Mumbai": [19.0330, 73.0297],
    "Thane": [19.2183, 72.9781],
    "Kalyan-Dombivli": [19.2354, 73.1299],
    "Vasai-Virar": [19.3919, 72.8397],
    "Panvel": [18.9894, 73.1175],
    "Mira-Bhayandar": [19.2952, 72.8544],
    "Ulhasnagar": [19.2215, 73.1645],
}

for name, coords in regions.items():
    if "" in name:
        marker_color = "red"
        icon_type = "info-sign"

# 5) This the code for the folium marker

    folium.Marker(
        location=coords,
        popup=folium.Popup(f"<b>{name}</b>", max_width=200),
        tooltip=name,
        icon=folium.Icon(color=marker_color, icon=icon_type),
    ).add_to(suburbs_group)

# 6) Custom CSS code to disable the click focus outline box
custom_css = """
<style>
.leaflet-container:focus, 
.leaflet-container * {
    outline: none !important;
}
</style>
"""
mumbai_map.get_root().html.add_child(folium.Element(custom_css))

# 7. Add the Lag-Free Clustered Parks (Set show=True or show=False for default state)

marker_cluster = MarkerCluster(name="Parks & Gardens", show=True).add_to(mumbai_map)
print("Loading and clustering parks data. This might take a few seconds...")

with open(geojson_path, "r", encoding="utf-8") as f:
    geo_data = json.load(f)

count = 0
for feature in geo_data.get("features", []):
    geom = feature.get("geometry")
    props = feature.get("properties", {})
    park_name = props.get("name", "Unnamed Park / Garden")

    if not geom:
        continue

    geom_type = geom.get("type")
    coords = geom.get("coordinates")

    lat, lon = None, None

    try:
        if geom_type == "Point":
            lon, lat = coords
        elif geom_type == "Polygon":
            lon, lat = coords[0][0]
        elif geom_type == "MultiPolygon":
            lon, lat = coords[0][0][0]
    except (TypeError, IndexError):
        continue

    if lat is not None and lon is not None:
        # Build HTML content for popup from all properties in GeoJSON
        popup_html = "<div style='font-family: Arial; font-size: 12px; max-height: 200px; overflow-y: auto;'>"
        popup_html += f"<b>{park_name}</b><hr style='margin: 4px 0;'/>"
        
        for key, val in props.items():
            if key != "name" and val:  # Skip name (already displayed) and empty values
                clean_key = key.replace("_", " ").title()
                popup_html += f"<b>{clean_key}:</b> {val}<br/>"
                
        popup_html += "</div>"

        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color="#39FF14",
            fill=True,
            fill_color="#39FF14",
            fill_opacity=0.6,
            tooltip=park_name,
            popup=folium.Popup(popup_html, max_width=250),
        ).add_to(marker_cluster)
        count += 1

# 8. adding the Layer Control (Button to turn layers on/off)
folium.LayerControl(collapsed=False).add_to(mumbai_map)

# 9. saving final map
mumbai_map.save(output_path)
print(f"Successfully added {count} clustered parks to your map!")
print(f"Map saved as '{output_path}'")