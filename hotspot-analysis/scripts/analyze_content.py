import json
import sys
import re
from collections import Counter
import numpy as np


def load_hotlist(filename):
    """加载热榜JSON数据"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"✗ 文件不存在: {filename}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"✗ JSON格式错误: {filename}")
        sys.exit(1)


def analyze_title_length(data):
    """分析标题长度"""
    lengths = [len(item["title"]) for item in data]
    
    return {
        "avg_length": round(np.mean(lengths), 2),
        "max_length": max(lengths),
        "min_length": min(lengths),
        "median_length": int(np.median(lengths)),
        "length_distribution": {
            "short (<10)": len([l for l in lengths if l < 10]),
            "medium (10-20)": len([l for l in lengths if 10 <= l < 20]),
            "long (>20)": len([l for l in lengths if l >= 20])
        }
    }


def extract_keywords(data, top_n=20):
    """提取高频关键词"""
    all_words = []
    
    for item in data:
        title = item["title"]
        # 简单分词:提取中文、英文单词
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', title)
        all_words.extend(words)
    
    word_counter = Counter(all_words)
    
    # 停用词过滤
    stopwords = {
        '的', '是', '在', '了', '和', '有', '我', '你', '他', '她', '它',
        '这', '那', '个', '与', '及', '等', '为', '被', '对', '从', '以',
        '到', '将', '把', '让', '给', '用', '于', '向', '着', '过', '起'
    }
    
    # 过滤停用词和单字词
    filtered_words = [
        (word, count) for word, count in word_counter.items()
        if word not in stopwords and len(word) > 1
    ]
    
    # 按频率排序
    sorted_words = sorted(filtered_words, key=lambda x: x[1], reverse=True)[:top_n]
    
    return [{"keyword": word, "count": count} for word, count in sorted_words]


def analyze_hot_value(data):
    """分析热度值"""
    hot_values = []
    
    for item in data:
        hot_str = str(item.get("hot_value", 0))
        # 提取数字部分
        match = re.search(r'[\d.]+', hot_str)
        if match:
            try:
                hot_values.append(float(match.group()))
            except ValueError:
                continue
    
    if not hot_values:
        return {
            "avg_hot_value": 0,
            "max_hot_value": 0,
            "min_hot_value": 0,
            "median_hot_value": 0,
            "hot_value_distribution": {
                "high (>70%)": 0,
                "medium (30%-70%)": 0,
                "low (<30%)": 0
            }
        }
    
    p30 = np.percentile(hot_values, 30)
    p70 = np.percentile(hot_values, 70)
    
    return {
        "avg_hot_value": round(np.mean(hot_values), 2),
        "max_hot_value": round(max(hot_values), 2),
        "min_hot_value": round(min(hot_values), 2),
        "median_hot_value": round(np.median(hot_values), 2),
        "hot_value_distribution": {
            "high (>70%)": len([v for v in hot_values if v >= p70]),
            "medium (30%-70%)": len([v for v in hot_values if p30 <= v < p70]),
            "low (<30%)": len([v for v in hot_values if v < p30])
        }
    }


def categorize_topics(data):
    """话题分类"""
    topic_keywords = {
        "娱乐": ["明星", "综艺", "电影", "音乐", "演唱会", "演员", "歌手", "粉丝", "偶像", "剧", "导演", "票房"],
        "科技": ["手机", "AI", "科技", "芯片", "汽车", "新能源", "数码", "苹果", "华为", "小米", "特斯拉", "智能"],
        "生活": ["美食", "旅行", "穿搭", "家居", "日常", "分享", "攻略", "教程", "美妆", "健身", "养生"],
        "游戏": ["游戏", "玩家", "电竞", "皮肤", "副本", "攻略", "开服", "英雄", "装备", "比赛"],
        "社会": ["新闻", "事件", "政策", "社会", "民生", "热搜", "热点", "曝光", "调查", "法律"],
        "教育": ["学习", "考试", "考研", "高考", "教育", "学校", "老师", "大学", "培训", "课程"]
    }
    
    topic_counts = {topic: 0 for topic in topic_keywords.keys()}
    uncategorized = 0
    
    for item in data:
        title = item["title"]
        categorized = False
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in title for keyword in keywords):
                topic_counts[topic] += 1
                categorized = True
                break
        
        if not categorized:
            uncategorized += 1
    
    topic_counts["其他"] = uncategorized
    return topic_counts


def print_analysis_report(hotlist_data, analysis_results):
    """打印分析报告"""
    print("\n" + "=" * 60)
    print(f"热点分析报告 - {hotlist_data['platform'].upper()}")
    print("=" * 60)
    print(f"数据获取时间: {hotlist_data['fetch_time']}")
    print(f"热榜总数: {hotlist_data['total']} 条")
    
    # 标题长度分析
    print("\n" + "-" * 60)
    print("【标题长度分析】")
    print("-" * 60)
    length_stats = analysis_results["title_length"]
    print(f"平均长度: {length_stats['avg_length']} 字符")
    print(f"最大长度: {length_stats['max_length']} 字符")
    print(f"最小长度: {length_stats['min_length']} 字符")
    print(f"中位数: {length_stats['median_length']} 字符")
    print("\n长度分布:")
    for category, count in length_stats["length_distribution"].items():
        print(f"  {category}: {count} 条")
    
    # 关键词分析
    print("\n" + "-" * 60)
    print("【高频关键词 TOP 20】")
    print("-" * 60)
    for idx, kw in enumerate(analysis_results["keywords"], 1):
        print(f"{idx:2d}. {kw['keyword']:10s} - 出现 {kw['count']} 次")
    
    # 热度值分析
    print("\n" + "-" * 60)
    print("【热度值分析】")
    print("-" * 60)
    hot_stats = analysis_results["hot_value"]
    print(f"平均热度: {hot_stats['avg_hot_value']}")
    print(f"最高热度: {hot_stats['max_hot_value']}")
    print(f"最低热度: {hot_stats['min_hot_value']}")
    print(f"中位数: {hot_stats['median_hot_value']}")
    print("\n热度分布:")
    for category, count in hot_stats["hot_value_distribution"].items():
        print(f"  {category}: {count} 条")
    
    # 话题分类
    print("\n" + "-" * 60)
    print("【话题分类统计】")
    print("-" * 60)
    topics = analysis_results["topics"]
    sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
    for topic, count in sorted_topics:
        percentage = (count / hotlist_data['total'] * 100) if hotlist_data['total'] > 0 else 0
        print(f"{topic:6s}: {count:3d} 条 ({percentage:5.1f}%)")
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python analyze_content.py <hotlist_json_file>")
        print("示例: python analyze_content.py douyin_hotlist.json")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    # 加载数据
    print(f"正在加载数据: {filename}")
    hotlist_data = load_hotlist(filename)
    data = hotlist_data["data"]
    
    if not data:
        print("✗ 数据为空,无法分析")
        sys.exit(1)
    
    print(f"✓ 成功加载 {len(data)} 条数据")
    
    # 执行分析
    print("\n正在分析...")
    analysis_results = {
        "title_length": analyze_title_length(data),
        "keywords": extract_keywords(data, top_n=20),
        "hot_value": analyze_hot_value(data),
        "topics": categorize_topics(data)
    }
    
    # 打印报告
    print_analysis_report(hotlist_data, analysis_results)
    
    # 保存分析结果
    output_filename = filename.replace(".json", "_analysis.json")
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump({
            "source_file": filename,
            "analysis_time": hotlist_data["fetch_time"],
            "results": analysis_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 分析结果已保存到: {output_filename}")


if __name__ == "__main__":
    main()
