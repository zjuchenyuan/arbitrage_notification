from argparse import ArgumentParser
import runpy
from dtb import Bot


parser = ArgumentParser(description='A DingTalk bot.')
parser.add_argument('--config-file', type=str, nargs='?',
                    default='config.py',
                    help='configuration file')
parser.add_argument('--config', type=str, nargs='?',
                    default='config',
                    help='configuration object')

args = parser.parse_args()


def main():
    config = runpy.run_path(args.config_file)[args.config]
    bot = Bot(config)
    bot.link('时代的火车向前开',
             '这个即将发布的新版本，创始人陈航（花名“无招”）称它为“红树林”。而在此之前，每当面临重大升级，产品经理们都会取一个应景的代号，这一次，为什么是“红树林”？',
             'https://www.dingtalk.com/s?__biz=MzA4NjMwMTA2Ng==&mid=2650316842&idx=1&sn=60da3ea2b29f1dcc43a7c8e4a7c97a16&scene=2&srcid=09189AnRJEdIiWVaKltFzNTw&from=timeline&isappinstalled=0&key=&ascene=2&uin=&devicetype=android-23&version=26031933&nettype=WIFI')

if __name__ == '__main__':
    main()
