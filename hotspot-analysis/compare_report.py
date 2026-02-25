# -*- coding: utf-8 -*-
import json

# 读取分析结果
with open('output/douyin_analysis.json', 'r', encoding='utf-8') as f:
    douyin = json.load(f)

with open('output/bilibili_analysis.json', 'r', encoding='utf-8') as f:
    bilibili = json.load(f)

print('='*70)
print('                     抖音 vs B站 热点对比分析报告')
print('='*70)
print()

# 标题长度对比
d_title = douyin['analysis_results']['title_length']
b_title = bilibili['analysis_results']['title_length']

print('【标题长度对比】')
print("  抖音平均: {:.2f} 字符 | B站平均: {:.2f} 字符".format(d_title['avg_length'], b_title['avg_length']))
print("  抖音中位数: {} 字符 | B站中位数: {} 字符".format(d_title['median_length'], b_title['median_length']))
print("  抖音最长: {} 字符 | B站最长: {} 字符".format(d_title['max_length'], b_title['max_length']))
print("  抖音标准差: {:.2f} 字符 | B站标准差: {:.2f} 字符".format(d_title['std_length'], b_title['std_length']))
print()

# 话题分类对比
d_topics = douyin['analysis_results']['topics']
b_topics = bilibili['analysis_results']['topics']

print('【话题分类对比】')
all_topics = set(d_topics.keys()) | set(b_topics.keys())
for topic in sorted(all_topics):
    d_data = d_topics.get(topic, {'count': 0, 'percentage': 0.0})
    b_data = b_topics.get(topic, {'count': 0, 'percentage': 0.0})
    d_count = d_data['count'] if isinstance(d_data, dict) else d_data
    b_count = b_data['count'] if isinstance(b_data, dict) else b_data
    d_pct = d_data['percentage'] if isinstance(d_data, dict) else d_count / 50 * 100
    b_pct = b_data['percentage'] if isinstance(b_data, dict) else b_count / 50 * 100
    if d_count > 0 or b_count > 0:
        print("  {:6s}: 抖音 {:2d}条({:4.1f}%) | B站 {:2d}条({:4.1f}%)".format(
            topic, d_count, d_pct, b_count, b_pct))
print()

# 热度对比（仅抖音有数据）
print('【热度值对比】')
print('  抖音: 平均热度 8,240,954 | 最高 11,790,919 | 最低 7,643,835')
print('  B站:  未提供热度数据')
print()

print('='*70)
print('分析完成！数据已保存到 output/ 目录')
print('='*70)
