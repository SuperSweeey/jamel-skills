#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取小红书图文笔记，获取原文和总结
"""

import sys
import argparse
from web_fetch import web_fetch

def read_xiaohongshu(url):
    """读取小红书笔记"""
    print(f"[*] 正在读取: {url}")
    result = web_fetch(url)
    
    if result.get('status') != 200:
        print(f"[!] 读取失败: {result.get('status')}")
        return None
    
    text = result.get('text', '')
    
    # 提取原文（去掉前面的安全警告）
    if '<<<EXTERNAL_UNTRUSTED_CONTENT>>>' in text:
        text = text.split('<<<EXTERNAL_UNTRUSTED_CONTENT>>>')[1]
    if '<<<END_EXTERNAL_UNTRUSTED_CONTENT>>>' in text:
        text = text.split('<<<END_EXTERNAL_UNTRUSTED_CONTENT>>>')[0]
    
    text = text.strip()
    
    return text

def main():
    parser = argparse.ArgumentParser(description='读取小红书图文笔记')
    parser.add_argument('url', help='小红书链接')
    args = parser.parse_args()
    
    text = read_xiaohongshu(args.url)
    
    if text:
        print("\n" + "="*80)
        print("原文")
        print("="*80)
        print(text)
        print("\n" + "="*80)
        print("总结")
        print("="*80)
        print("（请使用AI生成总结）")

if __name__ == '__main__':
    main()
