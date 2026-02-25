import requests
import json
import time
import sys


def fetch_douyin_hotlist():
    """获取抖音热榜数据"""
    print("正在获取抖音热榜...")
    try:
        url = "https://v2.xxapi.cn/api/douyinhot"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 200 and "data" in data:
            hotlist = []
            for idx, item in enumerate(data["data"], 1):
                hotlist.append({
                    "rank": idx,
                    "title": item.get("title", ""),
                    "hot_value": item.get("hot_value", "0"),
                    "url": item.get("url", "")
                })
            print(f"✓ 成功获取 {len(hotlist)} 条抖音热榜数据")
            return hotlist
        else:
            print(f"✗ API返回异常: {data}")
            return []
    except Exception as e:
        print(f"✗ 获取抖音热榜失败: {e}")
        return []


def fetch_bilibili_hotlist():
    """获取B站热榜数据"""
    print("正在获取B站热榜...")
    try:
        url = "https://api.bilibili.com/x/web-interface/wbi/search/square"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com"
        }
        params = {"limit": 50}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 0 and "data" in data:
            trending = data["data"].get("trending", {}).get("list", [])
            hotlist = []
            for idx, item in enumerate(trending, 1):
                hotlist.append({
                    "rank": idx,
                    "title": item.get("show_name", ""),
                    "hot_value": item.get("icon", ""),
                    "url": f"https://search.bilibili.com/all?keyword={item.get('keyword', '')}"
                })
            print(f"✓ 成功获取 {len(hotlist)} 条B站热榜数据")
            return hotlist
        else:
            print(f"✗ API返回异常: {data}")
            return []
    except Exception as e:
        print(f"✗ 获取B站热榜失败: {e}")
        return []


def fetch_xiaohongshu_hotlist(api_key=None):
    """获取小红书热榜数据"""
    print("正在获取小红书热榜...")
    
    if not api_key:
        print("⚠ 小红书API需要密钥,请访问 https://api.szlessthan.com 申请")
        api_key = input("请输入API Key (留空跳过): ").strip()
        if not api_key:
            print("✗ 跳过小红书热榜获取")
            return []
    
    try:
        url = "https://api.szlessthan.com/xiaohongshu/hotlist"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 200 and "data" in data:
            hotlist = []
            for idx, item in enumerate(data["data"], 1):
                hotlist.append({
                    "rank": idx,
                    "title": item.get("title", ""),
                    "hot_value": item.get("hot_value", "0"),
                    "url": item.get("link", "")
                })
            print(f"✓ 成功获取 {len(hotlist)} 条小红书热榜数据")
            return hotlist
        else:
            print(f"✗ API返回异常: {data}")
            return []
    except Exception as e:
        print(f"✗ 获取小红书热榜失败: {e}")
        return []


def save_hotlist(hotlist, platform):
    """保存热榜数据到JSON文件"""
    if not hotlist:
        print(f"✗ 没有数据可保存")
        return None
    
    filename = f"{platform}_hotlist.json"
    try:
        output = {
            "platform": platform,
            "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(hotlist),
            "data": hotlist
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 数据已保存到: {filename}")
        return filename
    except Exception as e:
        print(f"✗ 保存文件失败: {e}")
        return None


def main():
    """主函数"""
    print("=" * 50)
    print("热点数据采集工具")
    print("=" * 50)
    print("\n支持的平台:")
    print("1. 抖音 (无需配置)")
    print("2. B站 (无需配置)")
    print("3. 小红书 (需要API Key)")
    print("4. 全部平台")
    
    choice = input("\n请选择平台 (1-4): ").strip()
    
    platforms = {
        "1": ("douyin", fetch_douyin_hotlist),
        "2": ("bilibili", fetch_bilibili_hotlist),
        "3": ("xiaohongshu", fetch_xiaohongshu_hotlist)
    }
    
    if choice == "4":
        # 获取全部平台
        for platform_name, fetch_func in platforms.values():
            print(f"\n{'=' * 50}")
            hotlist = fetch_func() if platform_name != "xiaohongshu" else fetch_func(None)
            if hotlist:
                save_hotlist(hotlist, platform_name)
            time.sleep(1)  # 避免请求过快
    elif choice in platforms:
        platform_name, fetch_func = platforms[choice]
        print(f"\n{'=' * 50}")
        hotlist = fetch_func() if platform_name != "xiaohongshu" else fetch_func(None)
        if hotlist:
            save_hotlist(hotlist, platform_name)
    else:
        print("✗ 无效的选择")
        sys.exit(1)
    
    print(f"\n{'=' * 50}")
    print("采集完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
