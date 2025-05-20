import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Create output directory if it doesn't exist
os.makedirs("analyze/output", exist_ok=True)

# Load preprocessed data (or use existing df)
df = pd.read_csv("cleaning/data/hn_batdongsan.tsv", sep="\t")

# Re-run preprocessing (or assume it's already done)
# -- Include here the preprocessing code from previous step if needed --

# Only keep cleaned rows
df_clean = df.dropna(subset=["area", "price", "lat", "lon", "district"])

# 1. Price Distribution
fig_price = px.histogram(df_clean, x="price", nbins=50, title="Distribution of Property Prices (in million VND)")
fig_price.update_layout(xaxis_title="Price (triệu VND)", yaxis_title="Count")
fig_price.write_html("analyze/output/price_distribution.html")

# 2. Area Distribution
fig_area = px.histogram(df_clean, x="area", nbins=50, title="Distribution of Property Areas (m²)")
fig_area.update_layout(xaxis_title="Area (m²)", yaxis_title="Count")
fig_area.write_html("analyze/output/area_distribution.html")

# 3. Property Type Pie Chart (using 'furniture' as property type)
fig_type = px.pie(df_clean, names="furniture", title="Property Type Distribution")
fig_type.write_html("analyze/output/property_type_distribution.html")

# 4. Number of Listings per District
fig_district = px.bar(df_clean["district"].value_counts().reset_index(),
                      x="index", y="district", title="Number of Listings per District")
fig_district.update_layout(xaxis_title="District", yaxis_title="Number of Listings")
fig_district.write_html("analyze/output/district_distribution.html")

# 5. Price vs Area Scatter Plot
fig_scatter = px.scatter(df_clean, x="area", y="price", color="furniture",
                         title="Price vs Area by Property Type", hover_data=["district", "title"])
fig_scatter.update_layout(xaxis_title="Area (m²)", yaxis_title="Price (triệu VND)")
fig_scatter.write_html("analyze/output/price_vs_area.html")

# 6. Map of Listings by District
fig_map = px.scatter_mapbox(
    df_clean,
    lat="lat",
    lon="lon",
    color="furniture",
    size="price",
    hover_name="title",
    hover_data=["district", "price", "area"],
    zoom=10,
    height=600,
    title="Property Listings Map"
)

fig_map.update_layout(mapbox_style="open-street-map")
fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
fig_map.write_html("analyze/output/property_map.html")

print("All plots have been saved to the 'analyze/output' directory. You can open the HTML files in your web browser to view them.")
