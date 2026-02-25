"""
增强版热点内容分析脚本 - 支持批量分析、趋势对比、高级统计
"""
import json
import sys
import re
from collections import Counter
from pathlib import Path
import numpy as np
from datetime import datetime


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_hotlist_data(data):
        """
        验证热榜数据格式
        
        Args:
            data: 热榜数据
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not data:
            return False, "数据为空"
        
        if not isinstance(data, dict):
            return False, "数据格式错误,应为字典"
        
        required_fields = ["platform", "fetch_time", "total", "data"]
        for field in required_fields:
            if field not in data:
                return False, f"缺少必需字段: {field}"
        
        if not isinstance(data["data"], list):
            return False, "data字段应为列表"
        
        if len(data["data"]) == 0:
            return False, "热榜数据为空"
        
        return True, ""


class TitleAnalyzer:
    """标题分析器"""
    
    @staticmethod
    def analyze_length(data):
        """分析标题长度"""
        if not data:
            return {}
        
        lengths = [len(item.get("title", "")) for item in data]
        
        if not lengths:
            return {}
        
        return {
            "avg_length": round(np.mean(lengths), 2),
            "max_length": max(lengths),
            "min_length": min(lengths),
            "median_length": int(np.median(lengths)),
            "std_length": round(np.std(lengths), 2),
            "length_distribution": {
                "very_short (<5)": len([l for l in lengths if l < 5]),
                "short (5-10)": len([l for l in lengths if 5 <= l < 10]),
                "medium (10-20)": len([l for l in lengths if 10 <= l < 20]),
                "long (20-30)": len([l for l in lengths if 20 <= l < 30]),
                "very_long (>30)": len([l for l in lengths if l >= 30])
            }
        }
    
    @staticmethod
    def extract_keywords(data, top_n=20, min_word_length=2):
        """
        提取高频关键词
        
        Args:
            data: 热榜数据
            top_n: 返回前N个关键词
            min_word_length: 最小词长
        
        Returns:
            list: 关键词列表
        """
        if not data:
            return []
        
        all_words = []
        
        for item in data:
            title = item.get("title", "")
            # 提取中文、英文单词、数字
            words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|\d+', title)
            all_words.extend(words)
        
        word_counter = Counter(all_words)
        
        # 扩展停用词表
        stopwords = {
            '的', '是', '在', '了', '和', '有', '我', '你', '他', '她', '它',
            '这', '那', '个', '与', '及', '等', '为', '被', '对', '从', '以',
            '到', '将', '把', '让', '给', '用', '于', '向', '着', '过', '起',
            '来', '去', '说', '要', '会', '能', '可', '就', '都', '而', '又',
            '也', '还', '更', '很', '最', '太', '非常', '十分', '特别'
        }
        
        # 过滤停用词和短词
        filtered_words = [
            (word, count) for word, count in word_counter.items()
            if word not in stopwords and len(word) >= min_word_length
        ]
        
        # 按频率排序
        sorted_words = sorted(filtered_words, key=lambda x: x[1], reverse=True)[:top_n]
        
        return [{"keyword": word, "count": count, "percentage": round(count / len(data) * 100, 2)} 
                for word, count in sorted_words]


class HotValueAnalyzer:
    """热度值分析器"""
    
    @staticmethod
    def extract_numeric_value(hot_str):
        """
        从热度字符串中提取数值
        
        Args:
            hot_str: 热度字符串
        
        Returns:
            float: 数值,失败返回0
        """
        if not hot_str:
            return 0.0
        
        hot_str = str(hot_str)
        
        # 处理"万"、"亿"等单位
        if "亿" in hot_str:
            match = re.search(r'([\d.]+)亿', hot_str)
            if match:
                return float(match.group(1)) * 100000000
        elif "万" in hot_str:
            match = re.search(r'([\d.]+)万', hot_str)
            if match:
                return float(match.group(1)) * 10000
        
        # 提取纯数字
        match = re.search(r'[\d.]+', hot_str)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return 0.0
        
        return 0.0
    
    @staticmethod
    def analyze(data):
        """分析热度值"""
        if not data:
            return {}
        
        hot_values = []
        for item in data:
            hot_str = item.get("hot_value", 0)
            value = HotValueAnalyzer.extract_numeric_value(hot_str)
            if value > 0:
                hot_values.append(value)
        
        if not hot_values:
            return {
                "error": "未找到有效的热度值",
                "total_items": len(data),
                "valid_items": 0
            }
        
        # 计算百分位数
        p10 = np.percentile(hot_values, 10)
        p30 = np.percentile(hot_values, 30)
        p50 = np.percentile(hot_values, 50)
        p70 = np.percentile(hot_values, 70)
        p90 = np.percentile(hot_values, 90)
        
        return {
            "total_items": len(data),
            "valid_items": len(hot_values),
            "avg_hot_value": round(np.mean(hot_values), 2),
            "max_hot_value": round(max(hot_values), 2),
            "min_hot_value": round(min(hot_values), 2),
            "median_hot_value": round(np.median(hot_values), 2),
            "std_hot_value": round(np.std(hot_values), 2),
            "percentiles": {
                "p10": round(p10, 2),
                "p30": round(p30, 2),
                "p50": round(p50, 2),
                "p70": round(p70, 2),
                "p90": round(p90, 2)
            },
            "hot_value_distribution": {
                "very_high (>p90)": len([v for v in hot_values if v >= p90]),
                "high (p70-p90)": len([v for v in hot_values if p70 <= v < p90]),
                "medium (p30-p70)": len([v for v in hot_values if p30 <= v < p70]),
                "low (p10-p30)": len([v for v in hot_values if p10 <= v < p30]),
                "very_low (<p10)": len([v for v in hot_values if v < p10])
            }
        }


class TopicClassifier:
    """话题分类器"""
    
    # 扩展的话题关键词库
    TOPIC_KEYWORDS = {
        "娱乐": [
            "明星", "综艺", "电影", "音乐", "演唱会", "演员", "歌手", "粉丝", 
            "偶像", "剧", "导演", "票房", "影视", "娱乐", "艺人", "爱豆",
            "演出", "节目", "嘉宾", "主持", "表演", "舞台", "红毯"
        ],
        "科技": [
            "手机", "AI", "科技", "芯片", "汽车", "新能源", "数码", "苹果",
            "华为", "小米", "特斯拉", "智能", "技术", "互联网", "5G", "6G",
            "电脑", "软件", "硬件", "算法", "机器人", "无人机", "VR", "AR"
        ],
        "生活": [
            "美食", "旅行", "穿搭", "家居", "日常", "分享", "攻略", "教程",
            "美妆", "健身", "养生", "美容", "时尚", "搭配", "护肤", "化妆",
            "减肥", "运动", "瑜伽", "美甲", "发型", "装修", "收纳"
        ],
        "游戏": [
            "游戏", "玩家", "电竞", "皮肤", "副本", "攻略", "开服", "英雄",
            "装备", "比赛", "战队", "主播", "直播", "手游", "端游", "网游",
            "单机", "联机", "竞技", "排位", "段位", "赛季"
        ],
        "社会": [
            "新闻", "事件", "政策", "社会", "民生", "热搜", "热点", "曝光",
            "调查", "法律", "案件", "安全", "环境", "交通", "教育", "医疗",
            "就业", "房价", "物价", "消费", "经济", "金融", "股市"
        ],
        "教育": [
            "学习", "考试", "考研", "高考", "教育", "学校", "老师", "大学",
            "培训", "课程", "知识", "技能", "证书", "留学", "升学", "招生",
            "专业", "院校", "成绩", "分数", "录取", "毕业", "就业"
        ],
        "体育": [
            "足球", "篮球", "比赛", "运动员", "冠军", "联赛", "世界杯", "奥运",
            "体育", "球队", "教练", "赛事", "竞技", "训练", "转会", "进球",
            "得分", "排名", "战绩", "夺冠", "金牌", "银牌", "铜牌"
        ],
        "财经": [
            "股票", "基金", "投资", "理财", "金融", "经济", "市场", "行情",
            "涨跌", "收益", "风险", "资产", "财富", "创业", "公司", "企业",
            "上市", "融资", "估值", "营收", "利润", "亏损", "破产"
        ]
    }
    
    @staticmethod
    def classify(data):
        """话题分类统计"""
        if not data:
            return {}
        
        topic_counts = {topic: 0 for topic in TopicClassifier.TOPIC_KEYWORDS.keys()}
        uncategorized = 0
        
        for item in data:
            title = item.get("title", "")
            categorized = False
            
            for topic, keywords in TopicClassifier.TOPIC_KEYWORDS.items():
                if any(keyword in title for keyword in keywords):
                    topic_counts[topic] += 1
                    categorized = True
                    break
            
            if not categorized:
                uncategorized += 1
        
        topic_counts["其他"] = uncategorized
        
        # 计算百分比
        total = len(data)
        topic_stats = {
            topic: {
                "count": count,
                "percentage": round(count / total * 100, 2) if total > 0 else 0
            }
            for topic, count in topic_counts.items()
        }
        
        return topic_stats


class ReportGenerator:
    """报告生成器"""
    
    @staticmethod
    def print_console_report(hotlist_data, analysis_results):
        """打印控制台报告"""
        print("\n" + "=" * 70)
        print(f"{'热点分析报告':^66}")
        print("=" * 70)
        
        # 基本信息
        platform_name = hotlist_data.get("platform_name", hotlist_data.get("platform", "未知"))
        print(f"\n平台: {platform_name}")
        print(f"数据获取时间: {hotlist_data.get('fetch_time', '未知')}")
        print(f"热榜总数: {hotlist_data.get('total', 0)} 条")
        
        # 标题长度分析
        if "title_length" in analysis_results:
            print("\n" + "-" * 70)
            print("【标题长度分析】")
            print("-" * 70)
            stats = analysis_results["title_length"]
            print(f"平均长度: {stats.get('avg_length', 0)} 字符")
            print(f"标准差: {stats.get('std_length', 0)} 字符")
            print(f"最大长度: {stats.get('max_length', 0)} 字符")
            print(f"最小长度: {stats.get('min_length', 0)} 字符")
            print(f"中位数: {stats.get('median_length', 0)} 字符")
            
            if "length_distribution" in stats:
                print("\n长度分布:")
                for category, count in stats["length_distribution"].items():
                    percentage = (count / hotlist_data.get('total', 1) * 100)
                    print(f"  {category:20s}: {count:3d} 条 ({percentage:5.1f}%)")
        
        # 关键词分析
        if "keywords" in analysis_results and analysis_results["keywords"]:
            print("\n" + "-" * 70)
            print("【高频关键词 TOP 20】")
            print("-" * 70)
            for idx, kw in enumerate(analysis_results["keywords"], 1):
                print(f"{idx:2d}. {kw['keyword']:15s} - 出现 {kw['count']:2d} 次 ({kw['percentage']:5.1f}%)")
        
        # 热度值分析
        if "hot_value" in analysis_results:
            print("\n" + "-" * 70)
            print("【热度值分析】")
            print("-" * 70)
            stats = analysis_results["hot_value"]
            
            if "error" in stats:
                print(f"⚠ {stats['error']}")
            else:
                print(f"有效数据: {stats.get('valid_items', 0)}/{stats.get('total_items', 0)} 条")
                print(f"平均热度: {stats.get('avg_hot_value', 0):,.2f}")
                print(f"标准差: {stats.get('std_hot_value', 0):,.2f}")
                print(f"最高热度: {stats.get('max_hot_value', 0):,.2f}")
                print(f"最低热度: {stats.get('min_hot_value', 0):,.2f}")
                print(f"中位数: {stats.get('median_hot_value', 0):,.2f}")
                
                if "percentiles" in stats:
                    print("\n百分位数:")
                    p = stats["percentiles"]
                    print(f"  P10: {p.get('p10', 0):,.2f}")
                    print(f"  P30: {p.get('p30', 0):,.2f}")
                    print(f"  P50: {p.get('p50', 0):,.2f}")
                    print(f"  P70: {p.get('p70', 0):,.2f}")
                    print(f"  P90: {p.get('p90', 0):,.2f}")
                
                if "hot_value_distribution" in stats:
                    print("\n热度分布:")
                    for category, count in stats["hot_value_distribution"].items():
                        percentage = (count / stats.get('valid_items', 1) * 100)
                        print(f"  {category:20s}: {count:3d} 条 ({percentage:5.1f}%)")
        
        # 话题分类
        if "topics" in analysis_results:
            print("\n" + "-" * 70)
            print("【话题分类统计】")
            print("-" * 70)
            topics = analysis_results["topics"]
            sorted_topics = sorted(topics.items(), key=lambda x: x[1]["count"], reverse=True)
            
            for topic, stats in sorted_topics:
                print(f"{topic:8s}: {stats['count']:3d} 条 ({stats['percentage']:5.1f}%)")
        
        print("\n" + "=" * 70)
    
    @staticmethod
    def save_json_report(hotlist_data, analysis_results, output_file):
        """保存JSON格式报告"""
        try:
            report = {
                "source_data": {
                    "platform": hotlist_data.get("platform"),
                    "platform_name": hotlist_data.get("platform_name"),
                    "fetch_time": hotlist_data.get("fetch_time"),
                    "total": hotlist_data.get("total")
                },
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "analysis_results": analysis_results
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n✓ 分析结果已保存到: {output_file}")
            return True
        except Exception as e:
            print(f"\n✗ 保存分析结果失败: {e}")
            return False


def load_hotlist_file(filename):
    """加载热榜JSON文件"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"✗ 文件不存在: {filename}")
        return None
    except json.JSONDecodeError:
        print(f"✗ JSON格式错误: {filename}")
        return None
    except Exception as e:
        print(f"✗ 加载文件失败: {e}")
        return None


def analyze_hotlist(hotlist_data):
    """
    分析热榜数据
    
    Args:
        hotlist_data: 热榜数据字典
    
    Returns:
        dict: 分析结果
    """
    # 验证数据
    is_valid, error_msg = DataValidator.validate_hotlist_data(hotlist_data)
    if not is_valid:
        print(f"✗ 数据验证失败: {error_msg}")
        return None
    
    data = hotlist_data["data"]
    
    print(f"✓ 成功加载 {len(data)} 条数据")
    print("\n正在分析...")
    
    # 执行各项分析
    analysis_results = {
        "title_length": TitleAnalyzer.analyze_length(data),
        "keywords": TitleAnalyzer.extract_keywords(data, top_n=20),
        "hot_value": HotValueAnalyzer.analyze(data),
        "topics": TopicClassifier.classify(data)
    }
    
    return analysis_results


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python analyze_content_enhanced.py <hotlist_json_file> [output_file]")
        print("示例: python analyze_content_enhanced.py douyin_hotlist_20260210.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace(".json", "_analysis.json")
    
    # 加载数据
    print(f"正在加载数据: {input_file}")
    hotlist_data = load_hotlist_file(input_file)
    
    if hotlist_data is None:
        sys.exit(1)
    
    # 分析数据
    analysis_results = analyze_hotlist(hotlist_data)
    
    if analysis_results is None:
        sys.exit(1)
    
    # 生成报告
    ReportGenerator.print_console_report(hotlist_data, analysis_results)
    ReportGenerator.save_json_report(hotlist_data, analysis_results, output_file)


if __name__ == "__main__":
    main()
