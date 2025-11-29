import json
import urllib.request
import urllib.error
import os
import time
from datetime import datetime
import ssl

def fetch_radio_stations():
    print("🚀 开始获取全球电台数据...")
    
    # 禁用 SSL 证书验证
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    endpoints = [
        "https://de1.api.radio-browser.info/json/stations?limit=800&hidebroken=true&order=votes",
        "https://at1.api.radio-browser.info/json/stations?limit=800&hidebroken=true&order=votes"
    ]
    
    all_stations = []
    
    for endpoint in endpoints:
        try:
            print(f"📡 正在从 {endpoint} 获取数据...")
            
            req = urllib.request.Request(
                endpoint,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                data = response.read().decode('utf-8')
                stations = json.loads(data)
                print(f"✅ 获取到 {len(stations)} 个电台")
                all_stations.extend(stations)
                
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ 获取失败: {e}")
    
    if not all_stations:
        return create_fallback_data()
    
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
    
    # 数据清洗和优化
    processed_stations = []
    for station in unique_stations:
        has_url = station.get('url_resolved') or station.get('url')
        has_name = station.get('name') and station.get('name', '').strip()
        
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
    
    return processed_stations

def create_fallback_data():
    """创建备用示例数据"""
    fallback_stations = [
        {
            "stationuuid": "1",
            "name": "BBC Radio 1",
            "country": "United Kingdom",
            "countrycode": "GB",
            "url_resolved": "https://stream.live.vc.bbcmedia.co.uk/bbc_radio_one",
            "tags": "pop,music",
            "language": "english",
            "votes": 1000,
            "geo_lat": 51.5074,
            "geo_long": -0.1278
        },
        {
            "stationuuid": "2",
            "name": "Radio France Internationale",
            "country": "France",
            "countrycode": "FR",
            "url_resolved": "https://rfien-live.akamaized.net/hls/live/2038566/RFI_WEB/master.m3u8",
            "tags": "news,french",
            "language": "french",
            "votes": 800,
            "geo_lat": 48.8566,
            "geo_long": 2.3522
        },
        {
            "stationuuid": "3",
            "name": "Deutschlandfunk",
            "country": "Germany",
            "countrycode": "DE",
            "url_resolved": "https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3",
            "tags": "news,german",
            "language": "german",
            "votes": 700,
            "geo_lat": 52.5200,
            "geo_long": 13.4050
        },
        {
            "stationuuid": "4",
            "name": "中国国际广播电台",
            "country": "China",
            "countrycode": "CN",
            "url_resolved": "https://livecnm.cnr.cn/live/rmfygbb",
            "tags": "news,chinese",
            "language": "chinese",
            "votes": 600,
            "geo_lat": 39.9042,
            "geo_long": 116.4074
        },
        {
            "stationuuid": "5",
            "name": "NHK Radio 1",
            "country": "Japan",
            "countrycode": "JP",
            "url_resolved": "https://nhkradioakr1-i.akamaihd.net/hls/live/511633/1-r1/1-r1-01.m3u8",
            "tags": "news,japanese",
            "language": "japanese",
            "votes": 500,
            "geo_lat": 35.6762,
            "geo_long": 139.6503
        },
        {
            "stationuuid": "6",
            "name": "South Africa Radio",
            "country": "South Africa",
            "countrycode": "ZA",
            "url_resolved": "https://stream.radio.co/sd5add5ec9/listen",
            "tags": "music,african",
            "language": "english",
            "votes": 300,
            "geo_lat": -33.9249,
            "geo_long": 18.4241
        },
        {
            "stationuuid": "7",
            "name": "Egypt Radio",
            "country": "Egypt", 
            "countrycode": "EG",
            "url_resolved": "https://stream.radio.co/sd5add5ec9/listen",
            "tags": "arabic,music",
            "language": "arabic",
            "votes": 250,
            "geo_lat": 30.0444,
            "geo_long": 31.2357
        }
    ]
    print("🔄 使用备用示例数据")
    return fallback_stations

def split_by_region(stations, last_updated):
    """按地区分片数据 - 修复匹配逻辑"""
    print("🌍 开始按地区分片数据...")
    
    # 扩展国家列表，包含更多常见国家
    region_countries = {
        'asia': [
            'China', 'Japan', 'South Korea', 'India', 'Indonesia', 'Thailand', 
            'Vietnam', 'Malaysia', 'Philippines', 'Singapore', 'Taiwan', 'Hong Kong',
            'Bangladesh', 'Pakistan', 'Sri Lanka', 'Nepal', 'Bhutan', 'Maldives',
            'Myanmar', 'Cambodia', 'Laos', 'Mongolia', 'North Korea', 'Brunei'
        ],
        'europe': [
            'United Kingdom', 'Germany', 'France', 'Italy', 'Spain', 'Netherlands',
            'Sweden', 'Norway', 'Finland', 'Denmark', 'Switzerland', 'Austria',
            'Belgium', 'Ireland', 'Portugal', 'Poland', 'Russia', 'Ukraine',
            'Czech', 'Hungary', 'Romania', 'Greece', 'Bulgaria', 'Serbia'
        ],
        'americas': [
            'United States', 'Canada', 'Mexico', 'Brazil', 'Argentina', 'Chile',
            'Colombia', 'Peru', 'Venezuela', 'Cuba', 'Ecuador', 'Dominican',
            'Guatemala', 'Bolivia', 'Haiti', 'Paraguay', 'Uruguay', 'Jamaica'
        ],
        'africa': [
            'South Africa', 'Egypt', 'Nigeria', 'Kenya', 'Morocco', 'Ethiopia',
            'Ghana', 'Tanzania', 'Algeria', 'Uganda', 'Sudan', 'Angola',
            'Mozambique', 'Madagascar', 'Cameroon', 'Ivory Coast', 'Senegal'
        ],
        'oceania': [
            'Australia', 'New Zealand', 'Fiji', 'Papua New Guinea', 'New Caledonia',
            'Solomon Islands', 'Vanuatu', 'Samoa', 'Tonga'
        ]
    }
    
    total_regional_stations = 0
    
    for region, countries in region_countries.items():
        region_stations = []
        for station in stations:
            country = station.get('country', '')
            if country and country != 'Unknown':
                # 改进匹配逻辑：检查国家是否完全匹配或包含
                country_lower = country.lower()
                for country_name in countries:
                    if country_name.lower() in country_lower:
                        region_stations.append(station)
                        break
        
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
    
    # 调试信息：显示所有国家的分布
    print("\n📊 国家分布统计:")
    country_stats = {}
    for station in stations:
        country = station.get('country', 'Unknown')
        country_stats[country] = country_stats.get(country, 0) + 1
    
    # 显示前20个最多的国家
    sorted_countries = sorted(country_stats.items(), key=lambda x: x[1], reverse=True)[:20]
    for country, count in sorted_countries:
        print(f"  {country}: {count} 个电台")
    
    print(f"📈 地区分片完成！总共 {total_regional_stations} 个地区电台")

def main():
    """主函数"""
    try:
        # 确保数据目录存在
        os.makedirs('data', exist_ok=True)
        
        current_time = datetime.now().isoformat()
        
        # 获取和处理电台数据
        processed_stations = fetch_radio_stations()
        
        # 保存精选数据
        curated_output = {
            'lastUpdated': current_time,
            'totalStations': len(processed_stations),
            'source': 'Radio Browser API',
            'stations': processed_stations
        }
        
        with open('data/curated-stations.json', 'w', encoding='utf-8') as f:
            json.dump(curated_output, f, ensure_ascii=False, indent=2)
        
        print(f"💾 精选数据保存完成！共 {len(processed_stations)} 个电台")
        
        # 按地区分片
        split_by_region(processed_stations, current_time)
        
        print("🎉 数据预处理完成！")
        
    except Exception as e:
        print(f"💥 预处理失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
