import pandas as pd
# Đọc dữ liệu từ file TSV
df = pd.read_csv('cleaning/output/merged_file.tsv', sep='\t')

# Xóa các cột không cần thiết
df.drop(['direction', 'furniture', 'width', 'address'], axis=1, inplace=True)

# Xóa các hàng có giá trị 0 hoặc NaN trong các trường 'area', 'number_of_bedrooms', 'number_of_toilets'
df = df[(df['number_of_bedrooms'] != 0) & (df['number_of_toilets'] != 0)]

# Xóa các hàng có giá trị NaN trong các trường 'lat' và 'lon'
df.dropna(subset=['lat', 'lon'], how='any', inplace=True)

# Xóa các hàng thiếu trường price
df = df[(df['price'] != 0) & (df['price'].notna()) & (df['area'] != 0)]

# #Tukey's Fences
# for column in ['price']:
#     Q1 = df[column].quantile(0.25)
#     Q3 = df[column].quantile(0.75)
#     IQR = Q3 - Q1

#     # Lọc outliers
#     df = df[~((df[column] < (Q1 - 1.5 * IQR)) |(df[column] > (Q3 + 1.5 * IQR)))]

upper_limit = df['price'].quantile(0.90)
df = df[ (df['price'] <= upper_limit)]

upper_limit = df['number_of_bedrooms'].quantile(0.95)
df = df[ (df['number_of_bedrooms'] <= upper_limit)]

upper_limit = df['number_of_toilets'].quantile(0.95)
df = df[ (df['number_of_toilets'] <= upper_limit)]

district_mapping = {district: i for i, district in enumerate(df['district'].unique())}

# Write district mapping to a text file
with open('cleaning/output/district_mapping.txt', 'w', encoding='utf-8') as f:
    f.write("District Mapping\n")
    f.write("===============\n\n")
    for district, index in district_mapping.items():
        f.write(f"{index}: {district}\n")

# Thay thế giá trị trong cột 'district' bằng các số tương ứng
df['district'] = df['district'].map(district_mapping)

#Scale data
# scaler = StandardScaler()
# df['area'] = scaler.fit_transform(df[['area']])

# plt.figure(figsize=(10, 6))
# sns.histplot(df['price'], bins=30, kde=True, color='blue')
# plt.xlabel('Giá nhà')
# plt.ylabel('Số lượng')
# plt.title('Phân bố giá nhà')
# plt.grid(True)

# # Display the mean of 'price'
# mean_price = df['price'].mean()

# # Show the plot
# plt.axvline(mean_price, color='red', linestyle='dashed', linewidth=2)
# plt.legend({"Mean: " ,mean_price})
# plt.show()

# Lưu dataframe sau khi xóa vào file mới (nếu cần)
df.to_csv('cleaning/output/processed_data.tsv', sep='\t', index=False)
