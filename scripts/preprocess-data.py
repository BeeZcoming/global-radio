import json
import urllib.request
import urllib.error
import os
import time
from datetime import datetime
import ssl
import math

def clean_and_categorize_tags(tags):
    """清理和分类标签"""
    if not tags:
        return '未分类'
    
    # 扩展标签映射
    tag_mapping = {
        # 音乐风格
        'top40': '流行金曲', 'hits': '热门金曲', 'oldies': '经典老歌',
        'rnb': '节奏蓝调', 'r&b': '节奏蓝调', 'edm': '电子舞曲',
        'kpop': '韩流', 'jpop': '日流', 'cpop': '华语流行',
        'mandopop': '华语流行', 'cantopop': '粤语流行',
        'hiphop': '嘻哈', 'rap': '说唱', 'reggae': '雷鬼',
        'latin': '拉丁', 'world': '世界音乐', 'folk': '民谣',
        'blues': '蓝调', 'jazz': '爵士', 'classical': '古典',
        'rock': '摇滚', 'metal': '金属', 'pop': '流行',
        'electronic': '电子', 'dance': '舞曲', 'house': '浩室',
        'techno': '科技', 'trance': '迷幻', 'indie': '独立',
        'country': '乡村',
        
        # 电台类型
        'fm': '调频', 'am': '调幅', 'public': '公共广播',
        'college': '校园电台', 'community': '社区电台', 'local': '本地',
        'regional': '区域', 'national': '全国', 'international': '国际',
        
        # 内容类型
        'news': '新闻', 'talk': '谈话', 'sports': '体育',
        'business': '财经', 'weather': '天气', 'traffic': '交通',
        'education': '教育', 'culture': '文化', 'religious': '宗教',
        'entertainment': '娱乐', 'comedy': '喜剧', 'lifestyle': '生活',
        'health': '健康', 'fashion': '时尚', 'food': '美食',
        'travel': '旅游', 'children': '儿童', 'family': '家庭'
    }
    
    # 分割标签
    tag_list = [tag.strip().lower() for tag in tags.split(',')]
    cleaned_tags = []
    
    for tag in tag_list:
        # 使用映射替换
        if tag in tag_mapping:
            if tag_mapping[tag] not in cleaned_tags:
                cleaned_tags.append(tag_mapping[tag])
        # 保留有意义的标签
        elif len(tag) > 2 and not tag.isdigit() and tag not in ['the', 'and', 'radio', 'station']:
            if tag not in cleaned_tags:
                cleaned_tags.append(tag)
    
    return ', '.join(cleaned_tags[:3]) if cleaned_tags else '未分类'

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
                test_url = f"{base_url}/json/stations?limit=5000&hidebroken=true"
                req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, context=ssl_context, timeout=30) as resp:
                    data = resp.read().decode('utf-8')
                    stations = json.loads(data)
                    estimated_count = len(stations) * 6
                    print(f"📊 估算总数: {estimated_count} 个电台")
                    return min(estimated_count, 35000)
    except Exception as e:
        print(f"❌ 获取总数失败: {e}")
        return 30000

def fetch_all_stations():
    print("🚀 开始获取全球电台数据...")
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
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
            total_count = get_total_count(base_url, ssl_context)
            
            page_size = 1000
            pages = math.ceil(total_count / page_size)
            max_pages = 35
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
                
                time.sleep(1)
                
                if page > 2 and len(all_stations) == 0:
                    print("💥 连续多页没有数据，提前结束")
                    break
                    
            print(f"📊 从 {base_url} 成功获取 {successful_pages}/{pages} 页数据")
                    
        except Exception as e:
            print(f"❌ 端点 {base_url} 处理失败: {e}")
            continue
        
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
        has_url = station.get('url_resolved') or station.get('url')
        has_name = station.get('name') and station.get('name', '').strip()
        
        if has_url and has_name:
            # 优化标签
            raw_tags = station.get('tags') or ''
            cleaned_tags = clean_and_categorize_tags(raw_tags)
            
            processed_station = {
                'stationuuid': station.get('stationuuid'),
                'name': station.get('name', '').strip(),
                'country': station.get('country', 'Unknown'),
                'countrycode': station.get('countrycode', ''),
                'url_resolved': station.get('url_resolved') or station.get('url'),
                'tags': cleaned_tags,
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
    
    print(f"📈 地区分片完成！总共 {total_regional_stations} 个地区电台")

def main():
    """主函数"""
    try:
        os.makedirs('data', exist_ok=True)
        
        current_time = datetime.now().isoformat()
        
        print("=" * 60)
        print("🎯 全球广播电台数据采集 - 优化版本")
        print("=" * 60)
        
        raw_stations = fetch_all_stations()
        
        if len(raw_stations) < 25000:
            print(f"\n🔄 第一阶段只获取了 {len(raw_stations)} 个电台，开始第二阶段...")
            additional_stations = fetch_additional_stations()
            raw_stations.extend(additional_stations)
            
            unique_raw = []
            seen = set()
            for station in raw_stations:
                uuid = station.get('stationuuid')
                if uuid and uuid not in seen:
                    seen.add(uuid)
                    unique_raw.append(station)
            raw_stations = unique_raw
            print(f"📊 合并后原始数据: {len(raw_stations)} 个电台")
        
        processed_stations = process_stations_data(raw_stations)
        
        if not processed_stations:
            print("💥 没有有效数据")
            processed_stations = []
        
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
