# .md文件图片链接修改工具

本工具为 gitpage博客+gitee图床 使用场景编写，详细描述见[博客](https://ghamster0.github.io/2019/03/12/Hexo%20Blog折腾笔记/#图片与图床)

- `blog_repo_path`: 博客仓库本地路径(绝对路径)
- `pic_repo_path`: 图片仓库（`gitpage`图床）本地路径
- `pic_homepage`: 码云(等)图床主页
- `recent_only`: 是否只处理最近修改的文件，可选“h”小时、“m”分钟
- `default_images_folder`: 所有博客公用的图片目录

```bash
# 将本地图片链接（./folder/xxx.png）替换为http链接
python TransLink
# or
python TransLink p

# 将远程图片http链接替换为本地链接（./folder/xxx.png）
python TransLink r
```
