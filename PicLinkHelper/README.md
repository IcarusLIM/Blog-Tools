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