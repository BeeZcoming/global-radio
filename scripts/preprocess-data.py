import json
import urllib.request
import urllib.error
import os
import time
from datetime import datetime
import ssl
import math

def test_api_endpoint(base_url):
    """测试 API 端点是否可用"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        test_url = f"{base_url}/json/stations?limit=1"
        req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
            data = response.read().decode('utf-8')
            stations = json.loads(data)
            return len(stations) > 0
    except Exception as e:
        print(f"  ❌ 端点测试失败: {e}")
        return False

def get_total_count(base_url, ssl_context):
    """获取电台总数"""
    try:
        count_url = f"{base_url}/json/stations?limit=1&hidebroken=true"
        req = urllib.request.Request(count_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            if 'x-total-count' in response.headers:
                total_count = int(response.headers['x-total-count'])
                print(f"📊 API 报告总数: {total_count} 个电台")
                return total_count
            else:
                # 如果没有总数头信息，尝试直接获取大量数据来估算
                test_url = f"{base_url}/json/stations?limit=5000&hidebroken=true"
                req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, context=ssl_context, timeout=30) as resp:
                    data = resp.read().decode('utf-8')
                    stations = json.loads(data)
                    estimated_count = len(stations) * 6  # 粗略估算
                    print(f"📊 估算总数: {estimated_count} 个电台")
                    return min(estimated_count, 35000)  # 限制最大数量
    except Exception as e:
        print(f"❌ 获取总数失败: {e}")
        return 30000  # 默认值

def fetch_all_stations():
    print("🚀 开始获取全球电台数据...")
    
    # 禁用 SSL 证书验证
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # 测试可用的端点
    potential_urls = [
        "https://de1.api.radio-browser.info",
        "https://at1.api.radio-browser.info", 
        "https://nl1.api.radio-browser.info"
    ]
    
    available_urls = []
    print("🔍 测试 API 端点可用性...")
    for url in potential_urls:
        print(f"  测试 {url}...")
        if test_api_endpoint(url):
            available_urls.append(url)
            print(f"  ✅ 可用")
        else:
            print(f"  ❌ 不可用")
    
    if not available_urls:
        print("💥 所有端点都不可用，使用 de1 作为备用")
        available_urls = ["https://de1.api.radio-browser.info"]
    
    print(f"🎯 可用端点: {available_urls}")
    
    all_stations = []
    max_attempts = 3
    
    for base_url in available_urls:
        print(f"\n📡 使用端点: {base_url}")
        
        try:
            # 获取总数量
            total_count = get_total_count(base_url, ssl_context)
            
            # 分页获取数据
            page_size = 1000  # 每页获取1000个，避免过大请求
            pages = math.ceil(total_count / page_size)
            
            # 限制最大页数，但确保能获取足够数据
            max_pages = 35  # 35000个电台
            pages = min(pages, max_pages)
            
            print(f"📄 计划获取 {pages} 页数据，目标: {total_count} 个电台...")
            
            successful_pages = 0
            for page in range(pages):
                offset = page * page_size
                url = f"{base_url}/json/stations?offset={offset}&limit={page_size}&hidebroken=true"
                
                for attempt in range(max_attempts):
                    try:
                        print(f"  正在获取第 {page + 1}/{pages} 页 (offset: {offset})...")
                        
                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, context=ssl_context, timeout=60) as response:
                            data = response.read().decode('utf-8')
                            stations = json.loads(data)
                            
                            if stations:
                                all_stations.extend(stations)
                                successful_pages += 1
                                print(f"  ✅ 获取到 {len(stations)} 个电台")
                                print(f"  📈 累计: {len(all_stations)} 个电台")
                                break
                            else:
                                print(f"  ⚠️ 第 {page + 1} 页没有数据，可能已到末尾")
                                break
                                
                    except Exception as e:
                        print(f"  ❌ 第 {page + 1} 页获取失败 (尝试 {attempt + 1}/{max_attempts}): {e}")
                        if attempt < max_attempts - 1:
                            time.sleep(2)
                        else:
                            print(f"  💥 第 {page + 1} 页获取失败，跳过")
                            break
                
                # 页间延迟
                time.sleep(1)
                
                # 如果连续3页没有数据，提前结束
                if page > 2 and len(all_stations) == 0:
                    print("💥 连续多页没有数据，提前结束")
                    break
                    
            print(f"📊 从 {base_url} 成功获取 {successful_pages}/{pages} 页数据")
                    
        except Exception as e:
            print(f"❌ 端点 {base_url} 处理失败: {e}")
            continue
        
        # 如果从一个端点获取了足够数据，可以提前结束
        if len(all_stations) >= 28000:
            print("🎯 已获取接近完整数据，提前结束")
            break
    
    return all_stations

def fetch_additional_stations():
    """使用不同排序方式获取更多数据"""
    print("\n🔄 使用不同排序方式获取补充数据...")
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    base_url = "https://de1.api.radio-browser.info"
    additional_stations = []
    
    # 使用不同的排序方式
    sort_methods = [
        "order=votes",
        "order=clickcount", 
        "order=name",
        "order=country",
        "order=state",
        "order=language",
        "order=tags"
    ]
    
    for i, sort_method in enumerate(sort_methods):
        try:
            url = f"{base_url}/json/stations?limit=5000&hidebroken=true&{sort_method}"
            print(f"  补充查询 {i + 1}/{len(sort_methods)}: {sort_method}")
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ssl_context, timeout=60) as response:
                data = response.read().decode('utf-8')
                stations = json.loads(data)
                
                if stations:
                    additional_stations.extend(stations)
                    print(f"  ✅ 获取到 {len(stations)} 个电台")
                else:
                    print(f"  ⚠️ 查询没有返回数据")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ 补充查询失败: {e}")
            continue
    
    return additional_stations

def process_stations_data(raw_stations):
    """处理原始电台数据"""
    print("🔄 开始处理数据...")
    
    if not raw_stations:
        print("💥 没有原始数据可处理")
        return []
    
    print(f"📊 原始数据: {len(raw_stations)} 个电台")
    
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
        # 放宽过滤条件，获取更多电台
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

def split_by_region(stations, last_updated):
    """按地区分片数据"""
    print("🌍 开始按地区分片数据...")
    
    if not stations:
        print("⚠️ 没有数据可分区")
        return
    
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
    
    # 显示前30个国家
    for i, (country, count) in enumerate(sorted_countries[:30], 1):
        print(f"  {i:2d}. {country}: {count} 个电台")
    
    if len(sorted_countries) > 30:
        print(f"  ... 还有 {len(sorted_countries) - 30} 个国家/地区")
    
    print(f"📈 地区分片完成！总共 {total_regional_stations} 个地区电台")

def main():
    """主函数"""
    try:
        # 确保数据目录存在
        os.makedirs('data', exist_ok=True)
        
        current_time = datetime.now().isoformat()
        
        print("=" * 60)
        print("🎯 全球广播电台数据采集 - 完整版本")
        print("=" * 60)
        
        # 第一阶段：分页获取主要数据
        raw_stations = fetch_all_stations()
        
        # 第二阶段：使用不同排序方式获取补充数据
        if len(raw_stations) < 25000:
            print(f"\n🔄 第一阶段只获取了 {len(raw_stations)} 个电台，开始第二阶段...")
            additional_stations = fetch_additional_stations()
            raw_stations.extend(additional_stations)
            
            # 去重
            unique_raw = []
            seen = set()
            for station in raw_stations:
                uuid = station.get('stationuuid')
                if uuid and uuid not in seen:
                    seen.add(uuid)
                    unique_raw.append(station)
            raw_stations = unique_raw
            print(f"📊 合并后原始数据: {len(raw_stations)} 个电台")
        
        # 处理数据
        processed_stations = process_stations_data(raw_stations)
        
        if not processed_stations:
            print("💥 没有有效数据")
            processed_stations = []
        
        # 保存精选数据
        curated_output = {
            'lastUpdated': current_time,
            'totalStations': len(processed_stations),
            'source': 'Radio Browser API',
            'note': f'通过分页和多种排序方式采集，原始数据: {len(raw_stations)} 个电台',
            'stations': processed_stations
        }
        
        with open('data/curated-stations.json', 'w', encoding='utf-8') as f:
            json.dump(curated_output, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 精选数据保存完成！")
        print(f"  文件: data/curated-stations.json")
        print(f"  有效电台数: {len(processed_stations)}")
        print(f"  原始电台数: {len(raw_stations)}")
        
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
