## 1. 本项目

```bash
crontab -e 
```

进入vim编辑

```bash
*/1 * * * * zsh /Users/mac/Documents/Git_ndsjrrr/github_action/auto_commit.zsh
```

macOS 在较新版本的 macOS（Catalina 及以后）中，系统为了安全会默认限制 Cron 访问磁盘文件夹（如“文档”或“桌面”）。
操作步骤：

- 打开 系统设置 -> 隐私与安全性 -> 完全磁盘访问权限 (Full Disk Access)。
- 点击底部的 + 号。
- 按下快捷键 Cmd + Shift + G，输入 /usr/sbin/cron 并添加它。
- 确保开关已打开。

## 2. 常用操作命令 (实操)

在 macOS 终端中，你可以通过 crontab 命令来管理你的任务列表：

```bash
crontab -e
crontab -l
crontab -r
```

## 3. 经典示例

- 每分钟执行一次脚本：
`* * * * * /path/to/script.sh`
- 每天凌晨 2:30 执行备份：
`30 2 * * * /usr/bin/backup.sh`
- 每周一到周五，上午 9 点整提醒开会：
`0 9 * * 1-5 /usr/bin/remind.sh`
- 每小时的第 0, 20, 40 分钟检查服务：
`0,20,40 * * * * /usr/bin/check.sh`
