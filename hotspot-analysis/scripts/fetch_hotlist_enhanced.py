"""
增强版热点数据采集脚本 - 支持重试、并行、配置化
"""
import requests
import json
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path


class PlatformConfig:
    """平台配置类"""
    
    PLATFORMS = {
        "douyin": {
            "name": "抖音",
            "api_url": "https://v2.xxapi.cn/api/douyinhot",
            "need_api_key": False,
            "timeout": 10,
            "headers": {}
        },
        "bilibili": {
            "name": "B站",
            "api_url": "https://api.bilibili.com/x/web-interface/wbi/search/square",
            "need_api_key": False,
            "timeout": 10,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.bilibili.com"
            },
            "params": {"limit": 50}
        },
        "xiaohongshu": {
            "name": "小红书",
            "api_url": "https://api.szlessthan.com/xiaohongshu/hotlist",
            "need_api_key": True,
            "timeout": 10,
            "headers": {}
        }
    }
    
    @classmethod
    def get_config(cls, platform):
        """获取平台配置"""
        return cls.PLATFORMS.get(platform, {})
    
    @classmethod
    def list_platforms(cls):
        """列出所有支持的平台"""
        return list(cls.PLATFORMS.keys())


class RetrySession:
    """带重试机制的HTTP会话"""
    
    def __init__(self, retries=3, backoff_factor=0.5, status_forcelist=(500, 502, 504)):
        """
        初始化重试会话
        
        Args:
            retries: 重试次数
            backoff_factor: 退避因子
            status_forcelist: 需要重试的HTTP状态码
        """
        self.session = requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def get(self, url, **kwargs):
        """发送GET请求"""
        return self.session.get(url, **kwargs)
    
    def close(self):
        """关闭会话"""
        self.session.close()


class HotlistFetcher:
    """热榜数据采集器"""
    
    def __init__(self, api_keys=None):
        """
        初始化采集器
        
        Args:
            api_keys: API密钥字典 {"platform": "key"}
        """
        self.api_keys = api_keys or {}
        self.session = RetrySession()
    
    def fetch_douyin_hotlist(self):
        """获取抖音热榜数据"""
        print("正在获取抖音热榜...")
        try:
            config = PlatformConfig.get_config("douyin")
            url = config["api_url"]
            timeout = config["timeout"]
            
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200 and "data" in data:
                hotlist = []
                for idx, item in enumerate(data["data"], 1):
                    hotlist.append({
                        "rank": idx,
                        "title": item.get("word", item.get("title", "")),  # 抖音用word字段
                        "hot_value": item.get("hot_value", "0"),
                        "url": item.get("url", ""),
                        "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                print(f"✓ 成功获取 {len(hotlist)} 条抖音热榜数据")
                return hotlist
            else:
                print(f"✗ API返回异常: {data}")
                return []
        except requests.exceptions.Timeout:
            print(f"✗ 请求超时,请检查网络连接")
            return []
        except requests.exceptions.RequestException as e:
            print(f"✗ 网络请求失败: {e}")
            return []
        except Exception as e:
            print(f"✗ 获取抖音热榜失败: {e}")
            return []
    
    def fetch_bilibili_hotlist(self):
        """获取B站热榜数据"""
        print("正在获取B站热榜...")
        try:
            config = PlatformConfig.get_config("bilibili")
            url = config["api_url"]
            headers = config["headers"]
            params = config.get("params", {})
            timeout = config["timeout"]
            
            response = self.session.get(url, headers=headers, params=params, timeout=timeout)
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
                        "url": f"https://search.bilibili.com/all?keyword={item.get('keyword', '')}",
                        "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                print(f"✓ 成功获取 {len(hotlist)} 条B站热榜数据")
                return hotlist
            else:
                print(f"✗ API返回异常: {data}")
                return []
        except requests.exceptions.Timeout:
            print(f"✗ 请求超时,请检查网络连接")
            return []
        except requests.exceptions.RequestException as e:
            print(f"✗ 网络请求失败: {e}")
            return []
        except Exception as e:
            print(f"✗ 获取B站热榜失败: {e}")
            return []
    
    def fetch_xiaohongshu_hotlist(self):
        """获取小红书热榜数据"""
        print("正在获取小红书热榜...")
        
        api_key = self.api_keys.get("xiaohongshu")
        if not api_key:
            print("⚠ 小红书API需要密钥,请访问 https://api.szlessthan.com 申请")
            api_key = input("请输入API Key (留空跳过): ").strip()
            if not api_key:
                print("✗ 跳过小红书热榜获取")
                return []
        
        try:
            config = PlatformConfig.get_config("xiaohongshu")
            url = config["api_url"]
            headers = {**config["headers"], "Authorization": f"Bearer {api_key}"}
            timeout = config["timeout"]
            
            response = self.session.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200 and "data" in data:
                hotlist = []
                for idx, item in enumerate(data["data"], 1):
                    hotlist.append({
                        "rank": idx,
                        "title": item.get("title", ""),
                        "hot_value": item.get("hot_value", "0"),
                        "url": item.get("link", ""),
                        "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                print(f"✓ 成功获取 {len(hotlist)} 条小红书热榜数据")
                return hotlist
            else:
                print(f"✗ API返回异常: {data}")
                return []
        except requests.exceptions.Timeout:
            print(f"✗ 请求超时,请检查网络连接")
            return []
        except requests.exceptions.RequestException as e:
            print(f"✗ 网络请求失败: {e}")
            return []
        except Exception as e:
            print(f"✗ 获取小红书热榜失败: {e}")
            return []
    
    def fetch_platform_hotlist(self, platform):
        """
        获取指定平台的热榜数据
        
        Args:
            platform: 平台名称
        
        Returns:
            tuple: (platform, hotlist)
        """
        fetch_methods = {
            "douyin": self.fetch_douyin_hotlist,
            "bilibili": self.fetch_bilibili_hotlist,
            "xiaohongshu": self.fetch_xiaohongshu_hotlist
        }
        
        if platform not in fetch_methods:
            print(f"✗ 不支持的平台: {platform}")
            return (platform, [])
        
        hotlist = fetch_methods[platform]()
        return (platform, hotlist)
    
    def fetch_all_platforms_parallel(self, platforms=None):
        """
        并行获取多个平台的热榜数据
        
        Args:
            platforms: 平台列表,默认为所有平台
        
        Returns:
            dict: {platform: hotlist}
        """
        if platforms is None:
            platforms = PlatformConfig.list_platforms()
        
        print(f"\n开始并行获取 {len(platforms)} 个平台的热榜数据...")
        results = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_platform = {
                executor.submit(self.fetch_platform_hotlist, platform): platform
                for platform in platforms
            }
            
            for future in as_completed(future_to_platform):
                platform, hotlist = future.result()
                results[platform] = hotlist
        
        return results
    
    def save_hotlist(self, hotlist, platform, output_dir="."):
        """
        保存热榜数据到JSON文件
        
        Args:
            hotlist: 热榜数据列表
            platform: 平台名称
            output_dir: 输出目录
        
        Returns:
            str: 保存的文件路径,失败返回None
        """
        if not hotlist:
            print(f"✗ {platform}: 没有数据可保存")
            return None
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名(带日期)
        date_str = time.strftime("%Y%m%d")
        filename = output_path / f"{platform}_hotlist_{date_str}.json"
        
        try:
            output = {
                "platform": platform,
                "platform_name": PlatformConfig.get_config(platform).get("name", platform),
                "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total": len(hotlist),
                "data": hotlist
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            print(f"✓ {platform}: 数据已保存到 {filename}")
            return str(filename)
        except Exception as e:
            print(f"✗ {platform}: 保存文件失败 - {e}")
            return None
    
    def close(self):
        """关闭采集器"""
        self.session.close()


def load_api_keys(config_file="api_keys.json"):
    """
    从配置文件加载API密钥
    
    Args:
        config_file: 配置文件路径
    
    Returns:
        dict: API密钥字典
    """
    config_path = Path(config_file)
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠ 加载配置文件失败: {e}")
    return {}


def main():
    """主函数"""
    print("=" * 50)
    print("热点数据采集工具 (增强版)")
    print("=" * 50)
    
    # 加载API密钥
    api_keys = load_api_keys()
    
    print("\n支持的平台:")
    platforms = PlatformConfig.list_platforms()
    for idx, platform in enumerate(platforms, 1):
        config = PlatformConfig.get_config(platform)
        need_key = "需要API Key" if config.get("need_api_key") else "无需配置"
        print(f"{idx}. {config['name']} ({need_key})")
    print(f"{len(platforms) + 1}. 全部平台 (并行获取)")
    
    choice = input(f"\n请选择平台 (1-{len(platforms) + 1}): ").strip()
    
    # 创建采集器
    fetcher = HotlistFetcher(api_keys=api_keys)
    
    try:
        if choice == str(len(platforms) + 1):
            # 并行获取所有平台
            print(f"\n{'=' * 50}")
            results = fetcher.fetch_all_platforms_parallel()
            
            # 保存结果
            saved_files = []
            for platform, hotlist in results.items():
                if hotlist:
                    filename = fetcher.save_hotlist(hotlist, platform)
                    if filename:
                        saved_files.append(filename)
            
            print(f"\n{'=' * 50}")
            print(f"采集完成! 共保存 {len(saved_files)} 个文件")
            if saved_files:
                print("\n保存的文件:")
                for f in saved_files:
                    print(f"  - {f}")
        elif choice.isdigit() and 1 <= int(choice) <= len(platforms):
            # 获取单个平台
            platform = platforms[int(choice) - 1]
            print(f"\n{'=' * 50}")
            platform_name, hotlist = fetcher.fetch_platform_hotlist(platform)
            if hotlist:
                fetcher.save_hotlist(hotlist, platform_name)
        else:
            print("✗ 无效的选择")
            sys.exit(1)
    finally:
        fetcher.close()
    
    print(f"\n{'=' * 50}")
    print("程序结束")
    print("=" * 50)


if __name__ == "__main__":
    main()
