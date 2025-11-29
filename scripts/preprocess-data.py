import json
import requests
import os
from datetime import datetime

def fetch_radio_stations():
    print("🚀 开始获取全球电台数据...")
    
    endpoints = [
        "https://de1.api.radio-browser.info/json/stations?limit=500&hidebroken=true&order=votes",
        "https://at1.api.radio-browser.info/json/stations?limit=500&hidebroken=true&order=votes"
    ]
    
    all_stations = []
    
    for endpoint in endpoints:
        try:
            print(f"📡 正在从 {endpoint} 获取数据...")
            response = requests.get(endpoint, timeout=30)
            response.raise_for_status()
            stations = response.json()
            print(f"✅ 从 {endpoint} 获取到 {len(stations)} 个电台")
            all_stations.extend(stations)
            
        except Exception as e:
            print(f"❌ 从 {endpoint} 获取数据失败: {e}")
    
    if not all_stations:
        raise Exception("无法从任何端点获取数据")
    
    print(f"📊 总共获取到 {len(all_stations)} 个电台")
    
    # 数据去重
    unique_stations = []
    seen_uuids = set()
    
    for station in all_stations:
        uuid = station.get('stationuuid')
        if uuid and uuid not in seen_uuids:
            seen_uuids.add(uuid)
            unique_stations.append(station)
    
    print(f"🔄 去重后剩余 {len(unique_stations)} 个电台")
    
    # 数据清洗
    processed_stations = []
    for station in unique_stations:
        # 过滤有效电台
        has_url = station.get('url_resolved') or station.get('url')
        has_name = station.get('name', '').strip()
        
        if has_url and has_name:
            processed_station = {
                'stationuuid': station.get('stationuuid'),
                'name': station.get('name', '').strip(),
                'country': station.get('country', 'Unknown'),
                'countrycode': station.get('countrycode', ''),
                'url_resolved': station.get('url_resolved') or station.get('url'),
                'tags': (station.get('tags') or '').lower()[:100],
                'language': (station.get('language') or '').lower(),
                'votes': station.get('votes', 0),
                'geo_lat': station.get('geo_lat'),
                'geo_long': station.get('geo_long')
            }
            processed_stations.append(processed_station)
    
    # 按投票数排序
    processed_stations.sort(key=lambda x: x.get('votes', 0), reverse=True)
    
    print(f"🧹 数据清洗后剩余 {len(processed_stations)} 个有效电台")
    
    # 确保数据目录存在
    os.makedirs('data', exist_ok=True)
    
    # 保存精选数据
    curated_output = {
        'lastUpdated': datetime.now().isoformat(),
        'totalStations': len(processed_stations),
        'source': 'Radio Browser API',
        'stations': processed_stations
    }
    
    with open('data/curated-stations.json', 'w', encoding='utf-8') as f:
        json.dump(curated_output, f, ensure_ascii=False, indent=2)
    
    print(f"💾 精选数据保存完成！共 {len(processed_stations)} 个电台")
    
    # 按地区分片
    split_by_region(processed_stations, curated_output['lastUpdated'])
    
    return processed_stations

def split_by_region(stations, last_updated):
    print("🌍 开始按地区分片数据...")
    
    region_countries = {
        'asia': ['China', 'Japan', 'South Korea', 'India', 'Indonesia', 'Thailand', 
                'Vietnam', 'Malaysia', 'Philippines', 'Singapore', 'Taiwan', 'Hong Kong'],
        'europe': ['United Kingdom', 'Germany', 'France', 'Italy', 'Spain', 'Netherlands',
                  'Sweden', 'Norway', 'Finland', 'Denmark', 'Switzerland', 'Austria'],
        'americas': ['United States', 'Canada', 'Mexico', 'Brazil', 'Argentina', 'Chile'],
        'africa': ['South Africa', 'Egypt', 'Nigeria', 'Kenya', 'Morocco', 'Ethiopia'],
        'oceania': ['Australia', 'New Zealand', 'Fiji', 'Papua New Guinea']
    }
    
    total_regional_stations = 0
    
    for region, countries in region_countries.items():
        region_stations = []
        for station in stations:
            country = station.get('country', '')
            if country and any(c.lower() in country.lower() for c in countries):
                region_stations.append(station)
        
        output = {
            'lastUpdated': last_updated,
            'totalStations': len(region_stations),
            'region': region,
            'countries': countries,
            'stations': region_stations
        }
        
        with open(f'data/{region}-stations.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {region}地区: {len(region_stations)} 个电台")
        total_regional_stations += len(region_stations)
    
    print(f"📈 地区分片完成！总共 {total_regional_stations} 个地区电台")

if __name__ == "__main__":
    try:
        fetch_radio_stations()
        print("🎉 数据预处理完成！")
    except Exception as e:
        print(f"💥 预处理失败: {e}")
        exit(1)
