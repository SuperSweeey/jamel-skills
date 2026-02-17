# GitHub Pages Publisher Skill

## 描述
把转录内容发布到GitHub Pages的自动化skill。免费、不需要备案、公开访问、Cubox可收藏。

## 使用方法

### 1. 准备工作
- GitHub账号
- GitHub仓库：`用户名.github.io`（比如`SuperSweeey.github.io`）
- GitHub Personal Access Token（PAT），需要`public_repo`权限

### 2. 发布转录笔记
使用`create_transcript.py`脚本，加上`--github`选项：

```bash
cd /root/.openclaw/workspace/transcript_web
python3 create_transcript.py \
  --title "文章标题" \
  --url "原视频链接" \
  --task-id "任务ID" \
  --summary "AI总结内容" \
  --original "原文内容" \
  --github
```

### 3. 访问页面
发布成功后，页面URL是：
`https://用户名.github.io/notes/转录ID.html`

## 文件位置
- 脚本：`/root/.openclaw/workspace/transcript_web/publish_to_github.py`
- GitHub仓库：`/root/.openclaw/workspace/SuperSweeey.github.io`
- 修改后的create_transcript.py：`/root/.openclaw/workspace/transcript_web/create_transcript.py`

## 配置
- GitHub用户名：你的GitHub用户名
- GitHub仓库：用户名.github.io
- GitHub Token：需要自己配置到脚本中

## 特点
- ✅ 免费
- ✅ 不需要备案
- ✅ 公开访问
- ✅ Cubox可收藏
- ✅ 自动生成HTML页面
- ✅ 自动更新首页列表
- ✅ 自动推送到GitHub Pages

## 注意事项
- GitHub Pages在国内访问可能有点慢
- 内容要遵守GitHub使用条款和版权法
- 本地保留备份
