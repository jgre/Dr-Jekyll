#!/usr/bin/env python

import argparse
import re
import os, os.path
from datetime import datetime
from ConfigParser import SafeConfigParser
import sys
import subprocess
import pprint
import shutil
import threading
import time

def parse_date(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M')

class PostError(Exception):
    pass

class Post(object):
    def __init__(self, path, draft, title=None, date=None):
        if not os.path.isfile(path):
            raise PostError('Could not open {}'.format(path))
        self.path = path
        self.draft = draft
        if title and date:
            self.title = title
            self.date  = date
        else:
            with open(path) as f:
                # FIXME we could optimize this by not reading entire files
                txt = f.read()
                m = re.search(r'^title: "?([^"]*?)"?$', txt, re.MULTILINE)
                if m:
                    self.title = m.group(1)
                else:
                    raise PostError('Could not find title in {}'.format(path))
                m = re.search(r'^date: (.*?)$', txt, re.MULTILINE)
                if m:
                    self.date = parse_date(m.group(1))
                else:
                    m = re.search(r'^(\d{4,4}-\d{2,2}-\d{2,2})',
                            os.path.basename(path))
                    if m:
                        self.date = datetime.strptime(m.group(1), '%Y-%m-%d')
                    else:
                        raise PostError(
                                'Could not find date in {}'.format(path))

    def __cmp__(self, other):
        if self.date < other.date:
            return -1
        elif self.date == other.date:
            return 0
        else:
            return 1

    def __repr__(self):
        base = '{} {}'.format(self.date, self.title)
        if self.draft:
            base += ' DRAFT'
        return base

def make_filename(title, date, extension):
    date_str = date.strftime('%Y-%m-%d')
    title_str = re.sub('\W', ' ', title.lower())
    title_str = re.sub(' +', '-', title_str)
    return '{date}-{title}{ext}'.format(date=date_str, title=title_str,
            ext=extension)

def edit_file(fname, args):
    subprocess.call(args.editor.split() + [fname])

def list_posts(args, drafts=True, published=True):
    def get_posts(path, draft):
        ret = []
        for fn in os.listdir(path):
            try:
                ret.append(Post(os.path.join(path, fn), draft=draft))
            except PostError as err:
                print err, 'ignoring'
        return ret
                
    ret = []
    if drafts:
        ret += get_posts(args.drafts_dir, True)
    if published:
        ret += get_posts(args.published_dir, False)
    return sorted(ret)

def match_post(title, posts):
    if title.strip() == '':
        return posts[-1]
    matches = [p for p in posts if re.search(title, p.title, re.IGNORECASE)]
    if not matches:
        print 'No posts matching', title
        sys.exit()
    elif len(matches) == 1:
        return matches[0]
    else:
        for idx, post in enumerate(matches):
            print '[{}]\t{}'.format(idx, post.title)
        print 'Select the post'
        resp = sys.stdin.readline()
        return matches[int(resp)]

def new(args):
    fname = make_filename(args.title, args.date, args.extension)
    path  = os.path.join(args.base_dir, '_drafts', fname)
    if os.path.isfile(path):
        print path, 'already exists'
        sys.exit()
    date_str = args.date.strftime('%Y-%m-%d %H:%M')
    with open(path, 'w') as f:
        t='---\ntitle: "{title}"\nlayout: post\ndate: {date}\n---\n\n'.format(
                title=args.title, date=date_str)
        f.write(t)
    print 'Created a new draft:', path
    edit_file(path,args)

def publish(args):
    posts = list_posts(args)
    post = match_post(args.title, posts)
    ext = os.path.splitext(post.path)[1]
    fname = make_filename(post.title, args.date, ext)
    path  = os.path.join(args.published_dir, fname)
    print 'Publishing {} in {}'.format(post.title, path)
    date_str = args.date.strftime('%Y-%m-%d %H:%M')
    def parse_start(line):
        if line.strip() == '---':
            return (line, parse_hdr)
        else:
            return (line, parse_start)
    def parse_hdr(line):
        if line.strip().startswith('date:'):
            return ('date: {}\n'.format(date_str), parse_rest)
        elif line.strip() == '---':
            return ('date: {}\n---\n'.format(date_str), parse_rest)
        else:
            return (line, parse_hdr)
    def parse_rest(line):
        return (line, parse_rest)
    with open(post.path) as fin:
        with open(path, 'w') as fout:
            parser = parse_start
            for line in fin.readlines():
                output, parser = parser(line)
                fout.write(output)
    os.remove(post.path)

def ls(args):
    if args.drafts:
        drafts, published = True, False
    elif args.published:
        drafts, published = False, True
    else:
        drafts, published = True, True
    posts = list_posts(args, drafts=drafts, published=published)
    for post in posts:
        s = '{} {}'.format(post.date.strftime('%Y-%m-%d'), post.title)
        # Print drafts in green
        if post.draft:
            s = '\033[32m' + s + '\033[0m'
        print s
    print len(posts), 'posts'

def edit(args):
    posts = list_posts(args)
    post = match_post(args.title, posts)
    edit_file(post.path, args)

def rm(args):
    posts = list_posts(args)
    post = match_post(args.title, posts)
    print 'Really delete', post.title
    resp = sys.stdin.readline()
    if resp.strip().lower().startswith('y'):
        os.remove(post.path)

def generate(args):
    def check_dir(last_check, d):
        for fn in os.listdir(d):
            p = os.path.join(d, fn)
            if os.path.getmtime(p) > last_check:
                print 'Updating', fn
                shutil.copyfile(p, os.path.join(args.posts_dir, fn))
    # empty the _posts directory
    for fn in os.listdir(args.posts_dir):
        os.remove(os.path.join(args.posts_dir, fn))
    for fn in os.listdir(args.published_dir):
        shutil.copyfile(os.path.join(args.published_dir, fn),
                os.path.join(args.posts_dir, fn))
    if not args.published:
        for fn in os.listdir(args.drafts_dir):
            shutil.copyfile(os.path.join(args.drafts_dir, fn),
                    os.path.join(args.posts_dir, fn))
    if args.auto:
        last_check = time.time()
        while True:
            # periodically to look for changes in published 
            check_dir(last_check, args.published_dir)
            # periodically to look for changes in drafts 
            if not args.published:
                check_dir(last_check, args.drafts_dir)
            last_check = time.time()
            time.sleep(5)

def upload(args):
    if not 'upload_cmd' in args:
        print('An upload command must be given on the command line or in the '+
        'config file')
        sys.exit()
    print 'upload', args

parser = argparse.ArgumentParser(
        description='Command-line tool for managing a Jekyll blog')

parser.add_argument('--config', default='~/.drjekyll',
        help='Set the path to the configuration file (default: %(default)s)')
parser.add_argument('--base-dir', metavar='PATH', default=argparse.SUPPRESS,
        help='Set the path to your blog (default: .)')
subparsers = parser.add_subparsers(title='Commands', help='Commands')

new_parser = subparsers.add_parser('new', help='Create a new draft')
new_parser.add_argument('title', nargs='+',
        help='The new post\'s title')
new_parser.add_argument('--editor', default=argparse.SUPPRESS,
        help='Set the command to launch an editor for the post')
new_parser.add_argument('--date', default=datetime.now(), type=parse_date,
        help='Set date and time for the new post (default: now). ' +
        'The format is "YEAR-MONTH-DAY HOUR:MINUTE".')
new_parser.add_argument('--extension', default=argparse.SUPPRESS,
        help='Set the file extension (default: .md)')
new_parser.set_defaults(func=new)

publish_parser = subparsers.add_parser('publish', help='Publish a draft')
publish_parser.add_argument('title', nargs='+',
        help='A pattern matching the post\'s title')
publish_parser.add_argument('--date', default=datetime.now(), type=parse_date,
        help='Set date and time for the post (default: now). ' +
        'The format is "YEAR-MONTH-DAY HOUR:MINUTE".')
publish_parser.set_defaults(func=publish)

ls_parser = subparsers.add_parser('ls', help='List posts')
scope_group = ls_parser.add_mutually_exclusive_group()
scope_group.add_argument('--published', action='store_true',
        help='Show only published posts')
scope_group.add_argument('--drafts', action='store_true',
        help='Show only drafts')
ls_parser.set_defaults(func=ls)

edit_parser = subparsers.add_parser('edit', help='Edit a post')
edit_parser.add_argument('title', nargs='*',
        help='A pattern matching the post\'s title. If no title is given, ' +
        'edit the most recent post')
edit_parser.add_argument('--editor', default=argparse.SUPPRESS,
         help='Set the command to launch an editor for the post')
edit_parser.set_defaults(func=edit)

rm_parser = subparsers.add_parser('rm', help='Delete a post')
rm_parser.add_argument('title', nargs='+',
        help='A pattern matching the post\'s title.')
rm_parser.set_defaults(func=rm)

generate_parser = subparsers.add_parser('generate',
        help='Automatically generate the pages and start a web generate')
generate_parser.add_argument('--published', action='store_true',
        help='Only generate the published posts')
generate_parser.add_argument('--auto', action='store_true',
        help='Wait for changes and automatically regenerate')
generate_parser.set_defaults(func=generate)

upload_parser = subparsers.add_parser('upload',
        help='Upload the blog to the hosting site')
upload_parser.add_argument('--upload-cmd', metavar='CMD',
        default=argparse.SUPPRESS,
        help='Set the command to be used for uploading. The string "{site}" ' +
        'will be replaced with the absolute path of the _site directory')
upload_parser.set_defaults(func=upload)

if __name__ == '__main__':
    args = parser.parse_args()
    # Expand the base path and resolve the ~ variable
    args.config = os.path.abspath(os.path.expanduser(args.config))
    config = SafeConfigParser({
        'editor': 'vim',
        'base-dir': '.',
        'extension': '.md'})
    config.read(args.config)
    if not 'editor' in args:
        args.editor = config.get('DEFAULT', 'editor')
    if not 'base_dir' in args:
        args.base_dir = config.get('DEFAULT', 'base-dir')
    if not 'extension' in args:
        args.extension = config.get('DEFAULT', 'extension')
    if not 'upload_cmd' in args and config.has_option('DEFAULT', 'upload-cmd'):
        args.upload_cmd = config.get('DEFAULT', 'upload-cmd')

    # Expand the base path and resolve the ~ variable
    args.base_dir = os.path.abspath(os.path.expanduser(args.base_dir))

    if not os.path.isdir(args.base_dir):
        print args.base_dir, 'is not valid directory'
        sys,exit()
    args.posts_dir = os.path.join(args.base_dir, '_posts')
    if not os.path.isdir(args.posts_dir):
        print 'Creating', args.posts_dir
        os.mkdir(args.posts_dir)
    args.published_dir = os.path.join(args.base_dir, '_published')
    if not os.path.isdir(args.published_dir):
        print 'Creating', args.published_dir
        os.mkdir(args.published_dir)
    args.drafts_dir = os.path.join(args.base_dir, '_drafts')
    if not os.path.isdir(args.drafts_dir):
        print 'Creating', args.drafts_dir
        os.mkdir(args.drafts_dir)

    # Concatenate the title into one string
    if 'title' in args:
        args.title = ' '.join(args.title)

    # Call the handler function for the subparser
    args.func(args)
