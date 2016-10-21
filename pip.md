pip 使用技巧
==========

# 1. 快速安装项目依赖包
* -i 指定镜像源
* -r 指定项目的 requirements.txt
* --trusted-host 指定信任源（不是https需要指定）

    如下表示指定从豆瓣的源获取requirements.txt中指定版本的包。
```
sudo pip3 install --trusted-host pypi.douban.com -i http://pypi.douban.com/simple -r requirements.txt
```