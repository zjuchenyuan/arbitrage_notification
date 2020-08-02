from collections import OrderedDict
from enum import Enum
from .base import Message
from ..bot import Bot


class AtableMessage(Message):
    def __init__(self, msgtype: str, atMobiles: list = None, isAtAll: bool = None):
        super(AtableMessage, self).__init__(msgtype)
        if atMobiles or isAtAll:
            self.at = {}
            if atMobiles is not None:
                self.at['atMobiles'] = atMobiles
            if isAtAll is not None:
                self.at['isAtAll'] = isAtAll


@Bot.register('test')
class TextMessage(AtableMessage):
    '''
    Sample
    ```
    {
        "msgtype": "text",
        "text": {
            "content": "我就是我, 是不一样的烟火@156xxxx8827"
        },
        "at": {
            "atMobiles": [
                "156xxxx8827",
                "189xxxx8325"
            ],
            "isAtAll": false
        }
    }
    ```
    | 参数        | 参数类型   | 必须 | 说明                         |
    | --------- | ------ | -- | -------------------------- |
    | msgtype   | String | 是  | 消息类型，此时固定为：text            |
    | content   | String | 是  | 消息内容                       |
    | atMobiles | Array  | 否  | 被@人的手机号(在content里添加@人的手机号) |
    | isAtAll   | bool   | 否  | @所有人时：true，否则为：false       |
    '''

    def __init__(self, content: str, atMobiles: list = None, isAtAll: bool = None):
        super(TextMessage, self).__init__('text', atMobiles, isAtAll)
        self.text = {'content': content}


@Bot.register('link')
class LinkMessage(Message):
    '''
    Sample
    ```
    {
        "msgtype": "link",
        "link": {
            "text": "这个即将发布的新版本，创始人陈航（花名"无招"）称它为"红树林"。
    而在此之前，每当面临重大升级，产品经理们都会取一个应景的代号，这一次，为什么是"红树林"？",
            "title": "时代的火车向前开",
            "picUrl": "",
            "messageUrl": "https://www.dingtalk.com/s?__biz=MzA4NjMwMTA2Ng==&mid=2650316842&idx=1&sn=60da3ea2b29f1dcc43a7c8e4a7c97a16&scene=2&srcid=09189AnRJEdIiWVaKltFzNTw&from=timeline&isappinstalled=0&key=&ascene=2&uin=&devicetype=android-23&version=26031933&nettype=WIFI"
        }
    }
    ```
    | 参数         | 参数类型   | 必须 | 说明              |
    | ---------- | ------ | -- | --------------- |
    | msgtype    | String | 是  | 消息类型，此时固定为：link |
    | title      | String | 是  | 消息标题            |
    | text       | String | 是  | 消息内容。如果太长只会部分展示 |
    | messageUrl | String | 是  | 点击消息跳转的URL      |
    | picUrl     | String | 否  | 图片URL           |
    '''

    def __init__(self, title: str, text: str, messageUrl: str, picUrl: str = None):
        super(LinkMessage, self).__init__('link')
        self.link = {'title': title,
                     'text': text,
                     'messageUrl': messageUrl}
        if picUrl is not None:
            self.link['picUrl'] = picUrl


@Bot.register('markdown')
class MarkdownMessage(AtableMessage):
    '''
    Sample
    ```
    {
         "msgtype": "markdown",
         "markdown": {
             "title":"杭州天气",
             "text": "#### 杭州天气 @156xxxx8827n" +
                     "> 9度，西北风1级，空气良89，相对温度73%nn" +
                     "> ![screenshot](https://gw.alipayobjects.com/zos/skylark-tools/public/files/84111bbeba74743d2771ed4f062d1f25.png)n"  +
                     "> ###### 10点20分发布 [天气](http://www.thinkpage.cn/) n"
         },
        "at": {
            "atMobiles": [
                "156xxxx8827",
                "189xxxx8325"
            ],
            "isAtAll": false
        }
    }
    ```
    | 参数        | 类型     | 必选 | 说明                      |
    | --------- | ------ | -- | ----------------------- |
    | msgtype   | String | 是  | 此消息类型为固定markdown        |
    | title     | String | 是  | 首屏会话透出的展示内容             |
    | text      | String | 是  | markdown格式的消息           |
    | atMobiles | Array  | 否  | 被@人的手机号(在text内容里要有@手机号) |
    | isAtAll   | bool   | 否  | @所有人时：true，否则为：false    |
    '''

    def __init__(self, title: str, text: str, atMobiles: list = None, isAtAll: bool = None):
        super(MarkdownMessage, self).__init__('markdown', atMobiles, isAtAll)
        self.markdown = {'title': title,
                         'text': text}


class BtnOrientation(Enum):
    VERTICAL = '0'
    HORIZONTAL = '1'


class HideAvatar(Enum):
    SHOW = '0'
    HIDE = '1'


class ActionCardMessage(Message):
    def __init__(self, title: str, text: str, btnOrientation: BtnOrientation = None, hideAvatar: HideAvatar = None):
        super(ActionCardMessage, self).__init__('actionCard')
        self.actionCard = {'title': title,
                           'text': text}
        if btnOrientation is not None:
            self.actionCard['btnOrientation'] = btnOrientation.value
        if hideAvatar is not None:
            self.actionCard['hideAvatar'] = hideAvatar.value


@Bot.register('single_action')
class SingleActionCardMessage(ActionCardMessage):
    '''
    Sample
    ```
    {
        "actionCard": {
            "title": "乔布斯 20 年前想打造一间苹果咖啡厅，而它正是 Apple Store 的前身",
            "text": "![screenshot](serverapi2/@lADOpwk3K80C0M0FoA)
     ### 乔布斯 20 年前想打造的苹果咖啡厅
     Apple Store 的设计正从原来满满的科技感走向生活化，而其生活化的走向其实可以追溯到 20 年前苹果一个建立咖啡馆的计划",
            "hideAvatar": "0",
            "btnOrientation": "0",
            "singleTitle" : "阅读全文",
            "singleURL" : "https://www.dingtalk.com/"
        },
        "msgtype": "actionCard"
    }
    ```
    | 参数             | 类型     | 必选    | 说明                              |
    | -------------- | ------ | ----- | ------------------------------- |
    | msgtype        | string | true  | 此消息类型为固定actionCard              |
    | title          | string | true  | 首屏会话透出的展示内容                     |
    | text           | string | true  | markdown格式的消息                   |
    | singleTitle    | string | true  | 单个按钮的方案。(设置此项和singleURL后btns无效) |
    | singleURL      | string | true  | 点击singleTitle按钮触发的URL           |
    | btnOrientation | string | false | 0-按钮竖直排列，1-按钮横向排列               |
    | hideAvatar     | string | false | 0-正常发消息者头像，1-隐藏发消息者头像           |
    '''

    def __init__(self, title: str, text: str, singleTitle: str, singleURL: str, btnOrientation: BtnOrientation = None, hideAvatar: HideAvatar = None):
        super(SingleActionCardMessage, self).__init__(
            title, text, btnOrientation, hideAvatar)
        self.actionCard.update({
            'singleTitle': singleTitle,
            'singleURL': singleURL})

@Bot.register('multi_action')
class MultiActionCardMessage(ActionCardMessage):
    '''
    Sample
    ```
    {
        "actionCard": {
            "title": "乔布斯 20 年前想打造一间苹果咖啡厅，而它正是 Apple Store 的前身",
            "text": "![screenshot](serverapi2/@lADOpwk3K80C0M0FoA)
     ### 乔布斯 20 年前想打造的苹果咖啡厅
     Apple Store 的设计正从原来满满的科技感走向生活化，而其生活化的走向其实可以追溯到 20 年前苹果一个建立咖啡馆的计划",
            "hideAvatar": "0",
            "btnOrientation": "0",
            "btns": [
                {
                    "title": "内容不错",
                    "actionURL": "https://www.dingtalk.com/"
                },
                {
                    "title": "不感兴趣",
                    "actionURL": "https://www.dingtalk.com/"
                }
            ]
        },
        "msgtype": "actionCard"
    }
    ```
    | 参数             | 类型     | 必选    | 说明                                    |
    | -------------- | ------ | ----- | ------------------------------------- |
    | msgtype        | string | true  | 此消息类型为固定actionCard                    |
    | title          | string | true  | 首屏会话透出的展示内容                           |
    | text           | string | true  | markdown格式的消息                         |
    | btns           | array  | true  | 按钮的信息：title-按钮方案，actionURL-点击按钮触发的URL |
    | btnOrientation | string | false | 0-按钮竖直排列，1-按钮横向排列                     |
    | hideAvatar     | string | false | 0-正常发消息者头像，1-隐藏发消息者头像                 |
    '''

    def __init__(self, title: str, text: str, btns: OrderedDict, btnOrientation: BtnOrientation = None, hideAvatar: HideAvatar = None):
        super(MultiActionCardMessage, self).__init__(
            title, text, btnOrientation, hideAvatar)
        self.actionCard['btns'] = []
        for title, actionURL in btns.items():
            self.actionCard['btns'].append({'title': title,
                                            'actionURL': actionURL})


@Bot.register('feed')
class FeedCardCardMessage(Message):
    '''
    Sample
    ```
    {
        "feedCard": {
            "links": [
                {
                    "title": "时代的火车向前开",
                    "messageURL": "https://www.dingtalk.com/s?__biz=MzA4NjMwMTA2Ng==&mid=2650316842&idx=1&sn=60da3ea2b29f1dcc43a7c8e4a7c97a16&scene=2&srcid=09189AnRJEdIiWVaKltFzNTw&from=timeline&isappinstalled=0&key=&ascene=2&uin=&devicetype=android-23&version=26031933&nettype=WIFI",
                    "picURL": "https://www.dingtalk.com/"
                },
                {
                    "title": "时代的火车向前开2",
                    "messageURL": "https://www.dingtalk.com/s?__biz=MzA4NjMwMTA2Ng==&mid=2650316842&idx=1&sn=60da3ea2b29f1dcc43a7c8e4a7c97a16&scene=2&srcid=09189AnRJEdIiWVaKltFzNTw&from=timeline&isappinstalled=0&key=&ascene=2&uin=&devicetype=android-23&version=26031933&nettype=WIFI",
                    "picURL": "https://www.dingtalk.com/"
                }
            ]
        },
        "msgtype": "feedCard"
    }
    ```
    | 参数         | 类型     | 必选   | 说明               |
    | ---------- | ------ | ---- | ---------------- |
    | msgtype    | string | true | 此消息类型为固定feedCard |
    | title      | string | true | 单条信息文本           |
    | messageURL | string | true | 点击单条信息到跳转链接      |
    | picURL     | string | true | 单条信息后面图片的URL     |
    '''

    def __init__(self, links: list):
        super(FeedCardCardMessage, self).__init__('feedCard')
        self.links = []
        for title, messageURL, picURL in links:
            self.links.append({'title': title,
                               'messageURL': messageURL,
                               'picURL': picURL})
