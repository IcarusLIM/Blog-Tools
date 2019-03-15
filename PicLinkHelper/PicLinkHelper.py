# default: 拷贝博客仓库下的图片到图片仓库，修改markdown中的链接为gitee图床链接
# copy: 只拷贝图片
# r(restore): 拷贝图片仓库图片到博客仓库，还原markdown中的链接为本地图片链接
# r_pic: 只恢复图片

# install package pyyaml
import datetime
import os
import re
import shutil
import sys
from pathlib import Path

import yaml

with open('tool_config.yml', 'r') as f:
    config = yaml.safe_load(f)


def main():
    if not os.path.isdir(config['blog_repo_path']):
        print("未检测到博客目录！")
        exit(0)
    if not os.path.isdir(config['pic_repo_path']):
        print("未检测到图床目录!")
        exit(0)
    source_files, source_dirs = get_resource_list()
    target_dirs = get_pic_bed_list()
    print()
    if len(sys.argv) == 1:
        copy_pic(source_dirs, target_dirs)
        modify_link(source_files, source_dirs, target_dirs)
    elif sys.argv[1] == 'copy':
        copy_pic(source_dirs, target_dirs)
    elif sys.argv[1] == 'r' or sys.argv[1] == 'restore':
        r_pic(source_dirs, target_dirs)
        r_link(source_files, source_dirs, target_dirs)
    elif sys.argv[1] == 'r_pic':
        r_pic(source_dirs, target_dirs)
    else:
        print("Command error!")


def copy_pic(source_dirs, target_dirs):
    for s_key in source_dirs.keys():
        if s_key not in target_dirs:
            (Path(config['pic_repo_path']) / s_key).mkdir()
        copy_file(source_dirs[s_key], Path(config['pic_repo_path']) / s_key)


def modify_link(source_files, source_dirs, target_dirs):
    post_path = Path(config['blog_repo_path']) / 'source/_posts'
    pic_re = re.compile("(!\[.+]\((.+)\))")
    link_re = re.compile("^(/|\./|\.\./|)((\w|\s|-)+(\.(\w|\s|-)+)*/?)+$")
    link_re_begin_with_slash = re.compile("^/")
    for blog_file_path in source_files.values():
        # 读取blog全部文字
        print("=> Processing:", blog_file_path)
        with open(blog_file_path, 'r') as f1:
            content = f1.read()
        is_modified = False
        for pic_match in pic_re.findall(content):
            if link_re.match(pic_match[1]) is None:
                print("  - Can't deal with:", pic_match)
                continue
            # 处理以"/"开头的链接，在md中表示当前目录
            link_match_relative_path = pic_match[1] if link_re_begin_with_slash.match(pic_match[1]) is None \
                else '.' + pic_match[1]
            pic_path_local = post_path / link_match_relative_path
            pic_path_local_dir = pic_path_local.parent
            # 查找链接对应的本地文件
            if pic_path_local_dir.name in source_dirs \
                    and pic_path_local_dir == source_dirs[pic_path_local_dir.name] \
                    and pic_path_local.exists() \
                    and pic_path_local.is_file():
                link_transformed = config['pic_homepage'] + pic_path_local_dir.name + '/' + pic_path_local.name
            elif pic_path_local_dir.name in target_dirs \
                    and pic_path_local.name in [x.name for x in target_dirs[pic_path_local_dir.name].iterdir()]:
                link_transformed = config['pic_homepage'] + pic_path_local_dir.name + '/' + pic_path_local.name
            else:
                print("  - Correspond pic not found:", pic_match)
                continue
            is_modified = True
            print("  + Transfer:", pic_match[0], "\n    ->", link_transformed)
            pic_replacement = pic_match[0].replace(pic_match[1], link_transformed)
            new_content = content.replace(pic_match[0], pic_replacement)
            content = new_content
        if is_modified:
            os.remove(blog_file_path)
            with open(blog_file_path, 'w') as fw:
                fw.write(new_content)


def r_pic(source_dirs, target_dirs):
    if config['default_images_folder'] is not None:
        source_default_dir = Path(config['blog_repo_path']) / config['default_images_folder']
    post_path = Path(config['blog_repo_path']) / 'source/_posts'
    for s_key in target_dirs.keys():
        if source_default_dir is not None and s_key == source_default_dir.name:
            if not source_default_dir.exists():
                source_default_dir.mkdir()
            copy_file(target_dirs[s_key], source_default_dir)
        else:
            if s_key not in source_dirs:
                (post_path / s_key).mkdir()
            copy_file(target_dirs[s_key], post_path / s_key)


def r_link(source_files, source_dirs, target_dirs):
    post_path = Path(config['blog_repo_path']) / 'source/_posts'
    pic_homepage = config['pic_homepage']
    source_default_dir = None if config['default_images_folder'] is None \
        else Path(config['blog_repo_path']) / config['default_images_folder']
    pic_re = re.compile("(!\[.+]\((.+)\))")
    # link_re = re.compile("^"+config['pic_homepage']+".*")
    for blog_file_path in source_files.values():
        # 读取blog全部文字
        print("=> Processing:", blog_file_path)
        with open(blog_file_path, 'r') as f1:
            content = f1.read()
        is_modified = False
        for pic_match in pic_re.findall(content):
            temp_index = pic_match[1].find(pic_homepage)
            if temp_index <= -1:
                print("  - Can't deal with:", pic_match)
                continue
            else:
                dir_slash_file = pic_match[1][temp_index + len(pic_homepage):len(pic_match[1])]
                dir_and_file = [x for x in dir_slash_file.split("/") if x != '']
                dir_name = dir_and_file[0]
                file_name = dir_and_file[1]
                # 查找链接对应的本地文件
                if dir_name in source_dirs.keys() \
                        and source_dirs[dir_name].exists() \
                        and file_name in [x.name for x in source_dirs[dir_name].iterdir()]:
                    link_transformed = relative_path(post_path, source_dirs[dir_name]) + file_name
                elif dir_name in target_dirs.keys() \
                        and file_name in [x.name for x in target_dirs[dir_name].iterdir()]:
                    if source_default_dir is not None and source_default_dir.name == dir_name:
                        link_transformed = relative_path(post_path, source_default_dir) + file_name
                    else:
                        link_transformed = './' + dir_name + '/' + file_name
                else:
                    print("  - Correspond pic not found:", pic_match)
                    continue
                is_modified = True
                print("  + Transfer:", pic_match[0], "\n    ->", link_transformed)
                pic_replacement = pic_match[0].replace(pic_match[1], link_transformed)
                new_content = content.replace(pic_match[0], pic_replacement)
                content = new_content
        if is_modified:
            os.remove(blog_file_path)
            with open(blog_file_path, 'w') as fw:
                fw.write(new_content)


# 返回博客仓库中所有存放图片的目录、最近更新的文章
def get_resource_list():
    post_path = Path(config['blog_repo_path']) / 'source/_posts'
    dirs_basename_path = {}
    files_basename_path = {}
    for root, dirs, files in os.walk(post_path):
        for dir_name in dirs:
            dirs_basename_path[dir_name] = post_path / dir_name
        for file_name in files:
            files_basename_path[file_name] = post_path / file_name
        break

    if config['default_images_folder'] is not None:
        default_folder = Path(config['blog_repo_path']) / config['default_images_folder']
        if default_folder.exists():
            dirs_basename_path[default_folder.name] = default_folder

    modify_recent = config['post']['modify_recent']
    if modify_recent['enable']:
        current_time = datetime.datetime.now()
        time_delta = datetime.timedelta(hours=24 if modify_recent['enable'] is None else modify_recent['enable'])
        to_remove = []
        for key in files_basename_path.keys():
            modify_time = os.path.getmtime(files_basename_path[key])
            if datetime.datetime.fromtimestamp(modify_time) < current_time - time_delta:
                to_remove.append(key)
        for key in to_remove:
            print("-> Ignore Old File:", files_basename_path.pop(key))

    if config['post']['markdown_only']:
        to_remove = []
        end_with_md = re.compile(".*\.md$")
        for key in files_basename_path.keys():
            if end_with_md.match(key) is None:
                to_remove.append(key)
        for key in to_remove:
            print("-> Ignore not md File:", files_basename_path.pop(key))
    return files_basename_path, dirs_basename_path


def get_pic_bed_list():
    pic_repo_path = config['pic_repo_path']
    dirs_path_basename = {}
    for root, dirs, files in os.walk(pic_repo_path):
        for dir_name in dirs:
            dirs_path_basename[dir_name] = Path(pic_repo_path) / dir_name
        break
    if '.git' in dirs_path_basename:
        dirs_path_basename.pop('.git')
    return dirs_path_basename


def copy_file(src_dir, dst_dir):
    for file in src_dir.iterdir():
        src = src_dir / file.name
        dst = dst_dir / file.name
        if src.is_file() and not dst.exists():
            print("==> Copy file:", src, "to", dst)
            shutil.copyfile(src, dst)


def relative_path(from_path, to):
    re_split = re.compile(r'[\\/]')
    src = re_split.split(str(from_path))
    dst = re_split.split(str(to))
    diff_index = 0
    while len(src) > diff_index and len(dst) > diff_index and src[diff_index] == dst[diff_index]:
        diff_index += 1
    path = ""
    if len(src) > diff_index:
        for i in range(len(src) - diff_index):
            path += "../"
    if len(dst) > diff_index:
        for i in range(len(dst) - diff_index):
            path += dst[i + diff_index] + "/"
    return path


if __name__ == "__main__":
    print("！！！！！！！！！！！！！！！！！\n"
          "    程序有可能损坏你的博客！\n"
          "  请确保你已经commit全部内容！\n"
          "！！！！！！！！！！！！！！！！！\n")
    # os.system('pause')
    main()
