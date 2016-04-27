# TweetP

表示解析过的微博

# 成员

- `uid`  用户id int
- `mid`  微博mid Base62文本 unicode
- `nickname` 显示的名称 unicode
- `pageurl` 微博地址，不保证是绝对地址 unicode
- `raw_html` 原始 HTML 数据 unicode
- `timestamp` 发布时间戳 毫秒 int
- `device` = 发布设备 unicode
- `location` 位置信息 unicode
- `text` 文本 unicode
- `share` 转发数 int
- `comment` 评论数 int
- `like` 点赞数 int
- `isforward` 是否为转发 bool
- `forward_tweet` 转发的微博 TweetP对象
