import requests
import json
from datetime import datetime

def fetch_douyin():
    """获取抖音热榜"""
    try:
        url = "https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        return {
            'platform': 'douyin',
            'platform_name': '抖音',
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total': len(data.get('word_list', [])),
            'data': data.get('word_list', [])
        }
    except Exception as e:
        print(f"抖音采集失败: {e}")
        return None

def fetch_bilibili():
    """获取B站热榜"""
    try:
        url = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Origin': 'https://www.bilibili.com'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"B站API返回状态码: {response.status_code}")
            return None
        data = response.json()
        list_data = data.get('data', {}).get('list', [])
        return {
            'platform': 'bilibili',
            'platform_name': 'B站',
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total': len(list_data),
            'data': list_data
        }
    except Exception as e:
        print(f"B站采集失败: {e}")
        return None

def analyze_platform(platform_data):
    """分析单个平台数据"""
    if not platform_data or not platform_data.get('data'):
        return None
    
    platform_name = platform_data['platform_name']
    data = platform_data['data']
    
    # 提取标题
    if platform_data['platform'] == 'douyin':
        titles = [item.get('word', '') for item in data if item.get('word')]
    else:  # bilibili
        titles = [item.get('title', '') for item in data if item.get('title')]
    
    # 标题长度分析
    lengths = [len(t) for t in titles]
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    
    # 关键词提取（简单版）
    from collections import Counter
    all_words = []
    for title in titles:
        # 简单分词（按字符）
        words = [title[i:i+2] for i in range(len(title)-1)]
        all_words.extend(words)
    
    keywords = Counter(all_words).most_common(20)
    
    # 热度分析
    if platform_data['platform'] == 'douyin':
        hot_values = [item.get('hot_value', 0) for item in data if 'hot_value' in item]
    else:  # bilibili
        hot_values = [item.get('stat', {}).get('view', 0) for item in data]
    
    avg_hot = sum(hot_values) / len(hot_values) if hot_values else 0
    max_hot = max(hot_values) if hot_values else 0
    
    return {
        'platform': platform_name,
        'total_count': len(titles),
        'title_length': {
            'average': round(avg_length, 2),
            'max': max(lengths) if lengths else 0,
            'min': min(lengths) if lengths else 0
        },
        'top_keywords': keywords[:10],
        'hot_value': {
            'average': round(avg_hot, 2),
            'max': max_hot
        },
        'top_5_titles': titles[:5]
    }

# 主程序
print("=" * 60)
print("开始采集各平台热点数据...")
print("=" * 60)

results = {}

# 采集抖音
print("\n正在采集抖音热榜...")
douyin_data = fetch_douyin()
if douyin_data:
    print(f"✓ 成功获取 {douyin_data['total']} 条抖音热榜数据")
    results['douyin'] = analyze_platform(douyin_data)

# 采集B站
print("\n正在采集B站热榜...")
bili_data = fetch_bilibili()
if bili_data:
    print(f"✓ 成功获取 {bili_data['total']} 条B站热榜数据")
    results['bilibili'] = analyze_platform(bili_data)

# 输出分析结果
print("\n" + "=" * 60)
print("热点分析结果")
print("=" * 60)

for platform, analysis in results.items():
    if analysis:
        print(f"\n【{analysis['platform']}】")
        print(f"  热榜条数: {analysis['total_count']}")
        print(f"  标题长度: 平均 {analysis['title_length']['average']} 字")
        print(f"  热度值: 平均 {analysis['hot_value']['average']:,.0f}, 最高 {analysis['hot_value']['max']:,.0f}")
        print(f"\n  Top 5 热点:")
        for i, title in enumerate(analysis['top_5_titles'], 1):
            print(f"    {i}. {title}")
        print(f"\n  高频关键词:")
        for word, count in analysis['top_keywords']:
            print(f"    {word}: {count}次")

print("\n" + "=" * 60)
