# DNSHE DDNS FOR IPV4

## 由DNSSHE DDNS改来的供IPV4 更新记录的版本

原作者 [Gaowenbin789](https://github.com/Gaowenbin789/ "Gaowenbin789")
原仓库 [https://github.com/Gaowenbin789/dnshe-ddns](https://github.com/Gaowenbin789/dnshe-ddns "https://github.com/Gaowenbin789/dnshe-ddns")

具体的配置使用方式参考[原仓库](https://github.com/Gaowenbin789/dnshe-ddns "原仓库")

## 注意
**本程序完全由Deepseek编写，纯AI无人工**

## 配置事项
本版本在树莓派上通过了测试，但是不确保其稳定性
在使用的时候**一定要修改所有文件的路径**，否则会有成吨的报错

包括后端的	ddns_dnshe.py
前端WEB页面的	ddns_web.py
和所有	*.sh的启动脚本

**路径一定要匹配！！！**

## 新增内容
本人在部署时在树莓派上同步部署了Tailscale做远程组网，发现一个问题
原作在获取自己的IP时既有调用外部的API（不一定会成功）
也会根据自身的网卡信息从Linux系统中获取IP
但是获取出的IP会有可能是以10.**为头的C段IP
导致直接在DNS里加了两条记录，无法正常解析

在原作的代码中又对IPV6本地和环路地址的过滤，但是对IPV4来说要过滤的内容相对更多

因此加入了一定的针对IPV4过滤机制，过滤了Tailscale内网的网段与本地网段

如果有需要配置更多路由的，**一定一定要注意地址的过滤**

## 分发
严格遵守原作MIT License
