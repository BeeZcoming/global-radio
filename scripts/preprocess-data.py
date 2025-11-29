import json
import urllib.request
import urllib.error
import os
import time
from datetime import datetime
import ssl
import math

def fetch_all_stations():
    print("🚀 开始获取全球电台数据...")
    
    # 禁用 SSL 证书验证
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # 使用多个 API 端点
    base_urls = [
        "https://de1.api.radio-browser.info",
        "https://at1.api.radio-browser.info", 
        "https://nl1.api.radio-browser.info"
    ]
    
    all_stations = []
    max_attempts = 3
    
    for base_url in base_urls:
        print(f"\n📡 使用端点: {base_url}")
        
        # 首先获取总数量
        try:
            count_url = f"{base_url}/json/stations?limit=1&hidebroken=true"
            req = urllib.request.Request(count_url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                # 从响应头获取总数
                total_count = 0
                if 'x-total-count' in response.headers:
                    total_count = int(response.headers['x-total-count'])
                    print(f"📊 该端点共有 {total_count} 个电台")
                else:
                    # 如果没有总数头信息，使用默认值
                    total_count = 10000
                    print(f"⚠️ 无法获取总数，使用默认值: {total_count}")
            
            # 分页获取数据
            page_size = 1000  # 每页获取1000个
            pages = math.ceil(total_count / page_size)
            
            print(f"📄 需要获取 {pages} 页数据...")
            
            for page in range(pages):
                offset = page * page_size
                url = f"{base_url}/json/stations?offset={offset}&limit={page_size}&hidebroken=true&order=votes"
                
                for attempt in range(max_attempts):
                    try:
                        print(f"  正在获取第 {page + 1}/{pages} 页 (offset: {offset})...")
                        
                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, context=ssl_context, timeout=60) as response:
                            data = response.read().decode('utf-8')
                            stations = json.loads(data)
                            
                            if stations:
                                all_stations.extend(stations)
                                print(f"  ✅ 获取到 {len(stations)} 个电台")
                                break  # 成功，跳出重试循环
                            else:
                                print(f"  ⚠️ 第 {page + 1} 页没有数据")
                                break
                                
                    except Exception as e:
                        print(f"  ❌ 第 {page + 1} 页获取失败 (尝试 {attempt + 1}/{max_attempts}): {e}")
                        if attempt < max_attempts - 1:
                            time.sleep(2)  # 等待后重试
                        else:
                            print(f"  💥 第 {page + 1} 页获取失败，跳过")
                
                # 页间延迟
                time.sleep(1)
                
                # 如果已经获取足够数据，提前结束
                if len(all_stations) >= 20000:
                    print("🎯 已获取足够数据，提前结束")
                    break
                    
        except Exception as e:
            print(f"❌ 端点 {base_url} 初始化失败: {e}")
            continue
    
    if not all_stations:
        print("⚠️ 所有端点都失败，使用备用数据")
        return create_fallback_data()
    
    print(f"\n📊 总共获取到 {len(all_stations)} 个电台")
    return all_stations

def fetch_radio_stations_alternative():
    """备选方案：使用多个查询条件获取数据"""
    print("🔄 使用备选方案获取数据...")
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    base_urls = [
        "https://de1.api.radio-browser.info",
        "https://at1.api.radio-browser.info"
    ]
    
    all_stations = []
    
    # 使用不同的排序和过滤条件来获取更多数据
    queries = [
        "?limit=3000&hidebroken=true&order=votes",  # 按投票数
        "?limit=3000&hidebroken=true&order=clickcount",  # 按点击量
        "?limit=3000&hidebroken=true&order=name",  # 按名称
        "?limit=3000&hidebroken=true&order=country",  # 按国家
        "?limit=3000&hidebroken=true&order=language",  # 按语言
    ]
    
    for base_url in base_urls:
        print(f"\n📡 使用端点: {base_url}")
        
        for i, query in enumerate(queries):
            try:
                url = f"{base_url}/json/stations{query}"
                print(f"  查询 {i + 1}/{len(queries)}: {query}")
                
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, context=ssl_context, timeout=60) as response:
                    data = response.read().decode('utf-8')
                    stations = json.loads(data)
                    
                    if stations:
                        all_stations.extend(stations)
                        print(f"  ✅ 获取到 {len(stations)} 个电台")
                    else:
                        print(f"  ⚠️ 查询没有返回数据")
                
                time.sleep(2)  # 查询间延迟
                
            except Exception as e:
                print(f"  ❌ 查询失败: {e}")
                continue
    
    return all_stations

def process_stations_data(raw_stations):
    """处理原始电台数据"""
    print("🔄 开始处理数据...")
    
    # 数据去重
    unique_stations = []
    seen_uuids = set()
    
    for station in raw_stations:
        uuid = station.get('stationuuid')
        if uuid and uuid not in seen_uuids:
            seen_uuids.add(uuid)
            unique_stations.append(station)
    
    print(f"🔄 去重后剩余 {len(unique_stations)} 个电台")
    
    # 数据清洗和优化
    processed_stations = []
    valid_count = 0
    invalid_count = 0
    
    for station in unique_stations:
        # 过滤有效电台
        has_url = station.get('url_resolved') or station.get('url')
        has_name = station.get('name') and station.get('name', '').strip()
        is_working = station.get('lastcheckok', True)  # 默认为True
        
        if has_url and has_name and is_working:
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
                'geo_long': station.get('geo_long'),
                'lastchecktime': station.get('lastchecktime'),
                'clickcount': station.get('clickcount', 0),
                'bitrate': station.get('bitrate', 0),
                'codec': station.get('codec', '')
            }
            processed_stations.append(processed_station)
            valid_count += 1
        else:
            invalid_count += 1
    
    # 按投票数排序
    processed_stations.sort(key=lambda x: x.get('votes', 0), reverse=True)
    
    print(f"🧹 数据清洗完成:")
    print(f"  ✅ 有效电台: {valid_count}")
    print(f"  ❌ 无效电台: {invalid_count}")
    print(f"  📊 总计: {len(processed_stations)} 个电台")
    
    return processed_stations

def create_fallback_data():
    """创建备用示例数据"""
    print("🔄 使用备用示例数据")
    # 返回空数组，让前端知道是备用数据
    return []

def split_by_region(stations, last_updated):
    """按地区分片数据"""
    print("🌍 开始按地区分片数据...")
    
    # 完整的国家列表
    region_countries = {
        'asia': [
            'China', 'Japan', 'South Korea', 'India', 'Indonesia', 'Thailand', 
            'Vietnam', 'Malaysia', 'Philippines', 'Singapore', 'Taiwan', 'Hong Kong',
            'Bangladesh', 'Pakistan', 'Sri Lanka', 'Nepal', 'Bhutan', 'Maldives',
            'Myanmar', 'Cambodia', 'Laos', 'Mongolia', 'North Korea', 'Brunei',
            'Timor-Leste', 'Afghanistan', 'Armenia', 'Azerbaijan', 'Bahrain',
            'Georgia', 'Iran', 'Iraq', 'Israel', 'Jordan', 'Kazakhstan', 'Kuwait',
            'Kyrgyzstan', 'Lebanon', 'Oman', 'Qatar', 'Saudi Arabia', 'Syria',
            'Tajikistan', 'Turkey', 'Turkmenistan', 'United Arab Emirates', 'Uzbekistan', 'Yemen'
        ],
        'europe': [
            'United Kingdom', 'Germany', 'France', 'Italy', 'Spain', 'Netherlands',
            'Sweden', 'Norway', 'Finland', 'Denmark', 'Switzerland', 'Austria',
            'Belgium', 'Ireland', 'Portugal', 'Poland', 'Russia', 'Ukraine',
            'Czech Republic', 'Hungary', 'Romania', 'Greece', 'Bulgaria', 'Serbia',
            'Croatia', 'Slovakia', 'Belarus', 'Lithuania', 'Latvia', 'Estonia',
            'Slovenia', 'Luxembourg', 'Malta', 'Cyprus', 'Iceland', 'Albania',
            'Bosnia', 'Macedonia', 'Montenegro', 'Moldova', 'Monaco', 'San Marino',
            'Vatican', 'Liechtenstein', 'Andorra'
        ],
        'americas': [
            'United States', 'Canada', 'Mexico', 'Brazil', 'Argentina', 'Chile',
            'Colombia', 'Peru', 'Venezuela', 'Cuba', 'Ecuador', 'Dominican Republic',
            'Guatemala', 'Bolivia', 'Haiti', 'Paraguay', 'Uruguay', 'Jamaica',
            'Trinidad', 'Bahamas', 'Panama', 'Costa Rica', 'Puerto Rico', 'Honduras',
            'El Salvador', 'Nicaragua', 'Barbados', 'Saint Lucia', 'Grenada',
            'Suriname', 'Guyana', 'Belize', 'Bahamas', 'Saint Vincent', 'Antigua', 'Barbuda'
        ],
        'africa': [
            'South Africa', 'Egypt', 'Nigeria', 'Kenya', 'Morocco', 'Ethiopia',
            'Ghana', 'Tanzania', 'Algeria', 'Uganda', 'Sudan', 'Angola',
            'Mozambique', 'Madagascar', 'Cameroon', 'Ivory Coast', 'Senegal',
            'Zambia', 'Zimbabwe', 'Tunisia', 'Libya', 'Congo', 'Democratic Republic',
            'Somalia', 'Mali', 'Burkina Faso', 'Malawi', 'Niger', 'Chad',
            'Guinea', 'Rwanda', 'Benin', 'Burundi', 'South Sudan', 'Togo',
            'Sierra Leone', 'Central African', 'Liberia', 'Mauritania', 'Eritrea',
            'Namibia', 'Gambia', 'Botswana', 'Gabon', 'Lesotho', 'Guinea-Bissau',
            'Equatorial Guinea', 'Mauritius', 'Eswatini', 'Djibouti', 'Comoros', 'Cabo Verde'
        ],
        'oceania': [
            'Australia', 'New Zealand', 'Fiji', 'Papua New Guinea', 'New Caledonia',
            'Solomon Islands', 'Vanuatu', 'Samoa', 'Tonga', 'Micronesia',
            'Kiribati', 'Marshall Islands', 'Palau', 'Nauru', 'Tuvalu'
        ]
    }
    
    total_regional_stations = 0
    
    for region, countries in region_countries.items():
        region_stations = []
        for station in stations:
            country = station.get('country', '')
            if country and country != 'Unknown':
                # 宽松匹配
                country_lower = country.lower()
                for country_name in countries:
                    if country_name.lower() in country_lower or country_lower in country_name.lower():
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
    
    # 显示详细统计
    print(f"\n📊 详细统计:")
    country_stats = {}
    for station in stations:
        country = station.get('country', 'Unknown')
        country_stats[country] = country_stats.get(country, 0) + 1
    
    sorted_countries = sorted(country_stats.items(), key=lambda x: x[1], reverse=True)
    print(f"🌐 总共 {len(sorted_countries)} 个国家/地区")
    
    # 显示前50个国家
    for i, (country, count) in enumerate(sorted_countries[:50], 1):
        print(f"  {i:2d}. {country}: {count} 个电台")
    
    if len(sorted_countries) > 50:
        print(f"  ... 还有 {len(sorted_countries) - 50} 个国家/地区")
    
    print(f"📈 地区分片完成！总共 {total_regional_stations} 个地区电台")

def main():
    """主函数"""
    try:
        # 确保数据目录存在
        os.makedirs('data', exist_ok=True)
        
        current_time = datetime.now().isoformat()
        
        print("=" * 60)
        print("🎯 全球广播电台数据采集")
        print("=" * 60)
        
        # 尝试获取完整数据
        raw_stations = fetch_all_stations()
        
        # 如果数据太少，尝试备选方案
        if len(raw_stations) < 10000:
            print("\n🔄 数据量不足，尝试备选方案...")
            additional_stations = fetch_radio_stations_alternative()
            raw_stations.extend(additional_stations)
            
            # 再次去重
            unique_raw = []
            seen = set()
            for station in raw_stations:
                uuid = station.get('stationuuid')
                if uuid and uuid not in seen:
                    seen.add(uuid)
                    unique_raw.append(station)
            raw_stations = unique_raw
        
        print(f"\n📊 原始数据: {len(raw_stations)} 个电台")
        
        # 处理数据
        processed_stations = process_stations_data(raw_stations)
        
        if not processed_stations:
            print("💥 没有有效数据，创建空数据集")
            processed_stations = []
        
        # 保存精选数据
        curated_output = {
            'lastUpdated': current_time,
            'totalStations': len(processed_stations),
            'source': 'Radio Browser API',
            'note': '数据通过分页和多端点采集',
            'stations': processed_stations
        }
        
        with open('data/curated-stations.json', 'w', encoding='utf-8') as f:
            json.dump(curated_output, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 精选数据保存完成！")
        print(f"  文件: data/curated-stations.json")
        print(f"  电台数: {len(processed_stations)}")
        
        # 按地区分片
        if processed_stations:
            split_by_region(processed_stations, current_time)
        else:
            print("⚠️ 没有数据可分区")
        
        print("\n🎉 数据预处理完成！")
        
    except Exception as e:
        print(f"💥 预处理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
