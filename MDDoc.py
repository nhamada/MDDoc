#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import distutils.dir_util
import sys
import yaml
import re

parser = argparse.ArgumentParser(
  prog='MDDoc',
  description='Markdown Document Tool')

parser.add_argument('contents',
  nargs=None,
  type=argparse.FileType(mode='r'),
  help='YAML file which describes list of markdown files')
parser.add_argument('--output_dir',
  nargs=None,
  default='./',
  help='Output directory; Default is a current directory')

class Chapter:
  def __init__(self, id, name):
    self.id = id
    self.name = name

  @property
  def tagName(self):
    return "chapter-{}".format(self.id)

"""
headingのレベルが1であれば、タイトル名を返す
"""
def findChapterTitle(text):
  if type(text) is not str:
    return None
  result = re.match('^#[\s]+(?P<title>.*)', text)
  if result is None:
    return None
  return result.group('title')

"""
目次を挿入するマーカーかどうかの判定
マーカーは `<!-- toc -->`の形式
"""
def isTableOfContentsMarker(text):
  if type(text) is not str:
    return False
  result = re.match('^<!--[\s]+(toc)[\s]+-->$', text)
  if result is None:
    return None
  return True

def main(argv = sys.argv):
  # コマンドライン引数の解析
  args = parser.parse_args(argv[1:])
  # コンテンツファイルが存在するかをチェック
  toc = yaml.load(args.contents)
  print('Check content files for \'{}\''.format(toc['title']))
  dirname = os.path.dirname(args.contents.name)
  for f in toc['contents']:
    filename = os.path.join(dirname, f)
    print('  Checking {}'.format(filename))
    if not os.path.exists(filename):
      print('    Not exist.')
      sys.exit(-1)
    if not os.path.isfile(filename):
      print('    Not file')
      sys.exit(-1)
    print('    OK')
  # 出力先のディレクトリを準備
  if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)
  outfile = os.path.join(args.output_dir, toc['output_file'])
  # TOCの抽出
  tableOfContents = []
  for f in toc['contents']:
    filename = os.path.join(dirname, f)
    with open(filename, mode='r') as rf:
      for line in rf:
        title = findChapterTitle(line)
        if title != None:
          chap = Chapter(len(tableOfContents) + 1, title)
          tableOfContents.append(chap)
  # コンテンツファイルを読み込んで、一つのファイルにまとめる
  print('Generate \'{}\', saved as \'{}\''.format(toc['title'], outfile))
  with open(outfile, mode='w') as of:
    for f in toc['contents']:
      filename = os.path.join(dirname, f)
      with open(filename, mode='r') as rf:
        for line in rf:
          if isTableOfContentsMarker(line):
            # TOCマーカーなので、抽出した情報から、目次を作る
            of.writelines(line)
            for c in tableOfContents:
              of.write('{}. [{}](#{})\n'.format(c.id, c.name, c.tagName))
          else:
            title = findChapterTitle(line)
            if title == None:
              # TOCの項目ではないので、そのまま書く
              of.writelines(line)
            else:
              # 抽出した情報から、TOCの項目と一致するものを探す
              chapter = None
              for c in tableOfContents:
                if c.name == title:
                  chapter = c
              if chapter != None:
                # リンク可能な形式にして書き出す
                of.write('# <a name="{}"></a>{}\n'.format(chapter.tagName, chapter.name))
              else:
                # 見つからなかったので、そのまま書く
                of.writelines(line)
      of.writelines('\n')
  # 画像のディレクトリをコピー
  if os.path.abspath(args.output_dir) != os.getcwd():
    srcImageDir = os.path.join(dirname, toc['image_root_directory'])
    if os.path.exists(srcImageDir) and os.path.isdir(srcImageDir):
      print("Copy image directory \'{}\' to \'{}\'".format(toc['image_root_directory'], args.output_dir))
      outImageDir = os.path.join(args.output_dir, toc['image_root_directory'])
      distutils.dir_util.copy_tree(srcImageDir, outImageDir)
    else:
      print("No image directory: \'{}\'".format(srcImageDir))

if __name__ == '__main__':
  main()
