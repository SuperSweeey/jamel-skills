"""
抖音视频下载模块
使用Playwright绕过反爬
"""

import asyncio
import re
import time
from pathlib import Path
from typing import Optional
import requests

from pipeline.logger import Logger


class DouyinDownloader:
    """抖音视频下载器"""

    def __init__(self, output_dir: str = "./downloads", cookies_path: str = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.vurl = None
        self.cookies_path = None

        # 如果提供了cookies_path，直接使用
        if cookies_path:
            if Path(cookies_path).exists():
                self.cookies_path = str(cookies_path)
                Logger.info(f"使用指定的cookies文件: {cookies_path}")
                return

        # 自动查找cookies.txt
        possible_paths = [
            Path("cookies.txt"),
            Path("skills/jamel-skills/douyin-transcriber-skill/douyin-notion/cookies.txt"),
            Path("../douyin-notion/cookies.txt"),
        ]
        for path in possible_paths:
            if path.exists():
                self.cookies_path = str(path)
                Logger.info(f"找到cookies文件: {path}")
                break

    async def _capture(self, url):
        """使用Playwright捕获视频URL"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            Logger.error("Playwright未安装")
            return False

        async with async_playwright() as p:
            b = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                ],
            )

            c = await b.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1280, "height": 720},
            )

            # 加载cookies (支持Netscape格式和JSON格式)
            if self.cookies_path:
                try:
                    with open(self.cookies_path, "r", encoding="utf-8") as f:
                        first_line = f.readline()
                        f.seek(0)

                        if first_line.startswith("# Netscape"):
                            # Netscape格式
                            cookies = []
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                # 处理#HttpOnly_开头的行
                                is_http_only = False
                                if line.startswith("#HttpOnly_"):
                                    line = line[len("#HttpOnly_"):]
                                    is_http_only = True
                                elif line.startswith("#"):
                                    continue
                                parts = line.split("\t")
                                if len(parts) >= 7:
                                    cookie = {
                                        "name": parts[5],
                                        "value": parts[6],
                                        "domain": parts[0],
                                        "path": parts[2],
                                        "secure": parts[3].lower() == "true",
                                    }
                                    if is_http_only:
                                        cookie["httpOnly"] = True
                                    cookies.append(cookie)
                            await c.add_cookies(cookies)
                        else:
                            # JSON格式
                            import json

                            cookies = json.load(f)
                            await c.add_cookies(cookies)
                except Exception as e:
                    Logger.warning(f"加载cookies失败: {e}")

            page = await c.new_page()

            async def h(r):
                if "/web/aweme/detail/" in r.url and r.status == 200:
                    try:
                        self.vurl = (await r.json())["aweme_detail"]["video"][
                            "play_addr"
                        ]["url_list"][-1]
                        Logger.info(f"捕获到视频URL: {self.vurl[:60]}...")
                    except:
                        pass

            page.on("response", h)

            try:
                target = url
                if "v.douyin.com" in url or "iesdouyin.com" in url:
                    Logger.info(f"访问短链接: {url}")
                elif "modal_id=" in url:
                    match = re.search(r"modal_id=([0-9]+)", url)
                    if match:
                        target = f"https://www.douyin.com/video/{match.group(1)}"

                Logger.info(f"访问页面: {target}")

                try:
                    await page.goto(
                        target, timeout=30000, wait_until="domcontentloaded"
                    )
                except:
                    pass

                try:
                    await page.wait_for_selector("video", timeout=10000)
                    await page.mouse.wheel(0, 500)
                except:
                    pass

                for i in range(20):
                    if self.vurl:
                        break
                    await asyncio.sleep(0.5)

                if not self.vurl:
                    try:
                        src = await page.eval_on_selector("video", "v => v.src")
                        if src and not src.startswith("blob:"):
                            self.vurl = (
                                src if src.startswith("http") else ("https:" + src)
                            )
                    except:
                        pass

            except Exception as e:
                Logger.error(f"页面访问错误: {e}")
            finally:
                await b.close()

        return bool(self.vurl)

    def _classify_download_error(self, exc: Exception) -> tuple[str, str]:
        if isinstance(exc, requests.exceptions.Timeout):
            return "NETWORK_TIMEOUT", "下载超时，建议稍后重试。"
        if isinstance(exc, requests.exceptions.HTTPError):
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            if status_code == 403:
                return "ACCESS_DENIED", "视频被平台拒绝访问，可能需要 cookies 或请求头已失效。"
            if status_code == 429:
                return "RATE_LIMITED", "平台限流，建议稍后重试。"
            return "HTTP_ERROR", f"下载接口返回 HTTP {status_code}。"
        if isinstance(exc, requests.exceptions.RequestException):
            return "NETWORK_ERROR", "网络异常导致下载失败。"
        return "UNKNOWN", str(exc)

    def download(self, url: str, filename: str = None) -> str:
        """下载视频"""
        self.vurl = None
        for attempt in range(1, 4):
            try:
                Logger.info(f"开始解析抖音视频地址（第 {attempt}/3 次）")
                asyncio.run(self._capture(url))
                if self.vurl:
                    break
            except Exception as e:
                Logger.warning(f"Playwright运行失败（第 {attempt}/3 次）: {e}")
            if attempt < 3:
                time.sleep(2 * attempt)

        if not self.vurl:
            raise RuntimeError("抖音下载失败[CAPTURE_FAILED]: 无法获取视频下载链接，可能是页面结构变化、网络异常或缺少有效 cookies。")

        if not filename:
            filename = f"douyin_{int(time.time())}"

        out = self.output_dir / f"{filename}.mp4"
        Logger.info(f"下载视频到: {out}")

        for attempt in range(1, 4):
            try:
                r = requests.get(
                    self.vurl,
                    headers={"User-Agent": "Mozilla/5.0"},
                    stream=True,
                    timeout=120,
                )
                r.raise_for_status()

                total_size = int(r.headers.get("content-length", 0))
                downloaded = 0

                with open(out, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0 and downloaded % (1024 * 1024) < 8192:
                                percent = (downloaded / total_size) * 100
                                print(f"\r  进度: {percent:.1f}%", end="", flush=True)

                print()
                break
            except Exception as e:
                code, hint = self._classify_download_error(e)
                if out.exists():
                    out.unlink(missing_ok=True)
                if attempt < 3 and code in {"NETWORK_TIMEOUT", "NETWORK_ERROR", "RATE_LIMITED"}:
                    Logger.warning(f"抖音下载重试（第 {attempt}/3 次）: {code} - {hint}")
                    time.sleep(3 * attempt)
                    continue
                raise RuntimeError(f"抖音下载失败[{code}]: {hint}") from e

        file_size = out.stat().st_size / (1024 * 1024)
        Logger.success(f"下载完成: {out.name} ({file_size:.2f} MB)")

        return str(out)
