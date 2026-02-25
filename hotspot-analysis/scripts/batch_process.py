"""
批量处理脚本 - 自动采集和分析多个平台的热榜数据
"""
import sys
import time
from pathlib import Path
from datetime import datetime

# 导入增强版模块
sys.path.insert(0, str(Path(__file__).parent))
from fetch_hotlist_enhanced import HotlistFetcher, PlatformConfig, load_api_keys
from analyze_content_enhanced import analyze_hotlist, ReportGenerator


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, output_dir="output", api_keys=None):
        """
        初始化批量处理器
        
        Args:
            output_dir: 输出目录
            api_keys: API密钥字典
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fetcher = HotlistFetcher(api_keys=api_keys)
        self.results = {}
    
    def fetch_all_platforms(self, platforms=None):
        """
        采集所有平台数据
        
        Args:
            platforms: 平台列表,默认为所有平台
        
        Returns:
            dict: {platform: (hotlist, filename)}
        """
        print("\n" + "=" * 70)
        print("【第一步】数据采集")
        print("=" * 70)
        
        # 并行获取数据
        hotlist_results = self.fetcher.fetch_all_platforms_parallel(platforms)
        
        # 保存数据
        saved_results = {}
        for platform, hotlist in hotlist_results.items():
            if hotlist:
                filename = self.fetcher.save_hotlist(hotlist, platform, self.output_dir)
                if filename:
                    saved_results[platform] = (hotlist, filename)
        
        print(f"\n✓ 采集完成,共获取 {len(saved_results)} 个平台的数据")
        return saved_results
    
    def analyze_all_platforms(self, fetch_results):
        """
        分析所有平台数据
        
        Args:
            fetch_results: 采集结果 {platform: (hotlist, filename)}
        
        Returns:
            dict: {platform: analysis_results}
        """
        print("\n" + "=" * 70)
        print("【第二步】数据分析")
        print("=" * 70)
        
        analysis_results = {}
        
        for platform, (hotlist, filename) in fetch_results.items():
            print(f"\n正在分析 {platform}...")
            
            # 构造热榜数据格式
            config = PlatformConfig.get_config(platform)
            hotlist_data = {
                "platform": platform,
                "platform_name": config.get("name", platform),
                "fetch_time": hotlist[0].get("fetch_time") if hotlist else "",
                "total": len(hotlist),
                "data": hotlist
            }
            
            # 执行分析
            results = analyze_hotlist(hotlist_data)
            if results:
                analysis_results[platform] = results
                
                # 保存分析报告
                output_file = Path(filename).with_suffix("").with_suffix(".json").name.replace("_hotlist", "_analysis")
                output_path = self.output_dir / output_file
                ReportGenerator.save_json_report(hotlist_data, results, output_path)
        
        print(f"\n✓ 分析完成,共分析 {len(analysis_results)} 个平台的数据")
        return analysis_results
    
    def generate_comparison_report(self, analysis_results):
        """
        生成平台对比报告
        
        Args:
            analysis_results: 分析结果 {platform: results}
        """
        print("\n" + "=" * 70)
        print("【第三步】平台对比分析")
        print("=" * 70)
        
        if len(analysis_results) < 2:
            print("\n⚠ 需要至少2个平台的数据才能进行对比分析")
            return
        
        # 对比标题长度
        print("\n" + "-" * 70)
        print("【标题长度对比】")
        print("-" * 70)
        print(f"{'平台':<15} {'平均长度':<12} {'最大长度':<12} {'最小长度':<12}")
        print("-" * 70)
        
        for platform, results in analysis_results.items():
            config = PlatformConfig.get_config(platform)
            platform_name = config.get("name", platform)
            length_stats = results.get("title_length", {})
            
            avg = length_stats.get("avg_length", 0)
            max_len = length_stats.get("max_length", 0)
            min_len = length_stats.get("min_length", 0)
            
            print(f"{platform_name:<15} {avg:<12.2f} {max_len:<12} {min_len:<12}")
        
        # 对比热度值
        print("\n" + "-" * 70)
        print("【热度值对比】")
        print("-" * 70)
        print(f"{'平台':<15} {'平均热度':<15} {'最高热度':<15} {'中位数':<15}")
        print("-" * 70)
        
        for platform, results in analysis_results.items():
            config = PlatformConfig.get_config(platform)
            platform_name = config.get("name", platform)
            hot_stats = results.get("hot_value", {})
            
            if "error" not in hot_stats:
                avg = hot_stats.get("avg_hot_value", 0)
                max_hot = hot_stats.get("max_hot_value", 0)
                median = hot_stats.get("median_hot_value", 0)
                
                print(f"{platform_name:<15} {avg:<15,.0f} {max_hot:<15,.0f} {median:<15,.0f}")
        
        # 对比话题分布
        print("\n" + "-" * 70)
        print("【话题分布对比】")
        print("-" * 70)
        
        # 收集所有话题
        all_topics = set()
        for results in analysis_results.values():
            topics = results.get("topics", {})
            all_topics.update(topics.keys())
        
        # 打印表头
        header = f"{'话题':<10}"
        for platform in analysis_results.keys():
            config = PlatformConfig.get_config(platform)
            platform_name = config.get("name", platform)
            header += f" {platform_name:<15}"
        print(header)
        print("-" * 70)
        
        # 打印各话题数据
        for topic in sorted(all_topics):
            row = f"{topic:<10}"
            for platform, results in analysis_results.items():
                topics = results.get("topics", {})
                topic_stats = topics.get(topic, {"count": 0, "percentage": 0})
                count = topic_stats["count"]
                percentage = topic_stats["percentage"]
                row += f" {count:3d}({percentage:5.1f}%)"
            print(row)
        
        # 对比关键词
        print("\n" + "-" * 70)
        print("【高频关键词对比 (Top 10)】")
        print("-" * 70)
        
        for platform, results in analysis_results.items():
            config = PlatformConfig.get_config(platform)
            platform_name = config.get("name", platform)
            keywords = results.get("keywords", [])[:10]
            
            print(f"\n{platform_name}:")
            for idx, kw in enumerate(keywords, 1):
                print(f"  {idx:2d}. {kw['keyword']:12s} ({kw['count']:2d}次, {kw['percentage']:5.1f}%)")
        
        print("\n" + "=" * 70)
    
    def run(self, platforms=None):
        """
        运行批量处理流程
        
        Args:
            platforms: 平台列表,默认为所有平台
        """
        start_time = time.time()
        
        print("\n" + "=" * 70)
        print("热点分析批量处理工具")
        print("=" * 70)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"输出目录: {self.output_dir}")
        
        # 第一步:采集数据
        fetch_results = self.fetch_all_platforms(platforms)
        
        if not fetch_results:
            print("\n✗ 未能获取任何平台的数据")
            return
        
        # 第二步:分析数据
        analysis_results = self.analyze_all_platforms(fetch_results)
        
        if not analysis_results:
            print("\n✗ 未能分析任何平台的数据")
            return
        
        # 第三步:对比分析
        self.generate_comparison_report(analysis_results)
        
        # 完成
        elapsed_time = time.time() - start_time
        print("\n" + "=" * 70)
        print("批量处理完成!")
        print("=" * 70)
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"耗时: {elapsed_time:.2f} 秒")
        print(f"输出目录: {self.output_dir}")
        print("=" * 70)
    
    def close(self):
        """关闭处理器"""
        self.fetcher.close()


def main():
    """主函数"""
    # 加载API密钥
    api_keys = load_api_keys()
    
    # 创建批量处理器
    processor = BatchProcessor(output_dir="output", api_keys=api_keys)
    
    try:
        # 运行批量处理
        # 可以指定平台列表,例如: ["douyin", "bilibili"]
        # 或者留空处理所有平台
        processor.run()
    finally:
        processor.close()


if __name__ == "__main__":
    main()
