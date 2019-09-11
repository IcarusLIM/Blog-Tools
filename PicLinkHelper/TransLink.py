from datetime import datetime, timedelta
import re
import shutil
import sys
from pathlib import Path
import json

with open('config.json', 'r') as cf:
    config = json.load(cf)

work_dir = Path(config['blog_repo_path']) / 'source/_posts'
image_link_re = re.compile("(!\[.*]\((.+)\))")


def main():
    for blog in blog_list():
        if len(sys.argv) <= 1 or sys.argv[1] == 'p':
            print('==> Process blog: ', blog.name)
            process_blog(blog)
        else:  # sys.argv[1]=='r':
            print('==> Recover blog: ', blog.name)
            recover_blog(blog)


def blog_list():
    if 'recent_only' in config:
        recent = config['recent_only']
        time_delta = {'h': timedelta(hours=recent['value']),
                      'm': timedelta(minutes=recent['value'])
                      }.get(recent['unit']) or timedelta(hours=2)
        limit = datetime.now() - time_delta
        return [blog for blog in work_dir.glob('*.md') if datetime.fromtimestamp(blog.stat().st_mtime) > limit]
    return [blog for blog in work_dir.glob('*.md')]


def process_blog(blog):
    origin_dir, remote_dir = get_image_dir(blog)
    default_od, default_rd = get_default_image_dir()
    with blog.open() as f:
        content = f.read()
    modified = False
    for link_match in image_link_re.findall(content):
        image = work_dir / link_match[1]
        if not file_exist(image):
            print("- unresolved local link (file not exist): ", link_match[1])
            continue
        if image.parent.samefile(default_od):
            copy_file(image, default_rd / image.name, force=True)
            remote_link = default_rd.name + '/' + image.name
        else:
            copy_file(image, remote_dir / image.name, force=True)
            remote_link = remote_dir.name + '/' + image.name
        remote_link = config['pic_homepage'] + remote_link
        print('+ Replace link: ', link_match[0], ' -> ', remote_link)
        content = content.replace(link_match[0], link_match[0].replace(link_match[1], remote_link))
        modified = True
    if modified:
        safe_write_file(blog, content)


def recover_blog(blog):
    origin_dir, remote_dir = get_image_dir(blog)
    default_od, default_rd = get_default_image_dir()
    with blog.open() as f:
        content = f.read()
    modified = False
    for link_match in image_link_re.findall(content):
        image = Path(config['pic_repo_path']) / link_match[1].replace(config['pic_homepage'], '')
        if not file_exist(image):
            print("- unresolved remote link (file not exist): ", link_match[1])
            continue
        if image.parent.samefile(default_rd):
            copy_file(image, default_od / image.name, force=False)
            origin_link = str(relative_path(work_dir, default_od) / image.name)
        else:
            copy_file(image, origin_dir / image.name, force=False)
            origin_link = origin_dir.name + '/' + image.name
        print('+ Replace link: ', link_match[0], ' -> ', origin_link)
        content = content.replace(link_match[0], link_match[0].replace(link_match[1], origin_link))
        modified = True
    if modified:
        safe_write_file(blog, content)


def get_image_dir(blog):
    dir_name = blog.name[:-3].replace(' ', '_')
    origin_dir = blog.parent / dir_name
    origin_dir.mkdir(parents=True, exist_ok=True)
    remote_dir = Path(config['pic_repo_path']) / dir_name
    remote_dir.mkdir(parents=True, exist_ok=True)
    return origin_dir, remote_dir


def get_default_image_dir():
    origin_dir = Path(config['blog_repo_path']) / (config['default_images_folder'] or 'source/images')
    origin_dir.mkdir(parents=True, exist_ok=True)
    remote_dir = Path(config['pic_repo_path']) / origin_dir.name
    remote_dir.mkdir(parents=True, exist_ok=True)
    return origin_dir, remote_dir


def copy_file(src, dst, force=False):
    if not dst.exists() or (not src.samefile(dst) and force):
        print('+ copy file: ', src, " -> ", dst)
        shutil.copyfile(src, dst)


def safe_write_file(blog, content):
    blog_backup = blog.parent / (blog.name + '.back')
    blog_backup.unlink()
    blog.rename(blog_backup)
    blog.touch()
    blog.open('w').write(content)


def file_exist(path):
    try:
        return path.exists() and path.is_file()
    except OSError:
        return False


def relative_path(start, to):
    prefix = Path('')
    while True:
        try:
            rel_path = to.relative_to(start)
            full_rel_path = prefix / rel_path
            return full_rel_path
        except ValueError:
            tmp = start.parent
            if tmp.samefile(start):
                raise Exception("Fail to find relative path, that can't happen")
            start = tmp
            prefix = prefix / '..'


if __name__ == "__main__":
    print("！！！！！！！！！！！！！！！！！\n"
          "    程序有可能损坏你的博客！\n"
          "  请确保你已经commit全部内容！\n"
          "！！！！！！！！！！！！！！！！！\n")
    # os.system('pause')
    main()
