N1 pt rss
=====
N1安装entware
-----
* 修改/etc/opkg/entware.conf 
```shell
src/gz entware https://bin.entware.net/aarch64-k3.10/ 
```
* 执行以下命令
```shell
mv /etc/opkg/hacklog.conf /etc/opkg/hacklog.conf.bak
sh /opt/entware_aarch64-k3.10_init.sh
/opt/bin/opkg update
```
安装python
-----
```shell
/opt/bin/opkg install python3 python3-pip python3-setuptools python3-lib2to3 python3-requests python3-lxml python3-sqlite3
/opt/bin/pip3 install --upgrade pip
/opt/bin/pip3 install --upgrade setuptools
/opt/bin/pip3 install feedparser pyyaml
```
测试运行
-----
* 将config.yml和ptrss.py复制到服务器上，两者同一目录
```shell
/opt/bin/python3 /root/rss/ptrss.py
```
#### 正常运行会在界面显示爬取的内容,并在当前目录下生成rss.db数据库文件

部署
-----
* 在N1->Scheduled Tasks里添加
```shell
*/15 * * * * /opt/bin/python3 /root/rss/ptrss.py > /root/rss/rss.log 2>&1
```
#### */15 表示每15分钟执行一次

# `happy`
