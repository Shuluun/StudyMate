# StudyMate：本地运行与发布说明

完整团队应用，包含 Profile、Schedule、Matching 和 Session。
它不是已经上线的校园产品；Google Calendar 连接已从主应用移除。

## Windows

安装 Python 3.11 或更新版本。双击 `Setup-StudyMate.cmd` 安装依赖，再双击
`Start-StudyMate.cmd` 启动，浏览器打开 http://127.0.0.1:8020 。
如果 `python` 指向旧版本，请先选择正确的解释器；不要使用指向 Python 2.7 的旧配置。

等价命令：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m app.demo
```

macOS / Linux 将 `.venv\Scripts\python.exe` 换成 `.venv/bin/python`。

演示账号：`maya@example.edu` / `studymate`。也可以注册新的虚构账号，完成
Profile 后测试独立资料、日程和 Session。请勿填入真实隐私。
新账号可填 `Physics`、`Math 54`，地址填公开校园示例 `UC Berkeley`；
离线模式不会解析任意真实地址。

## 演示操作

1. 登录 Maya，在 Profile 查看示例课程和偏好。
2. 在 Schedule 选择 2026-10-26，创建、编辑、删除不可用时间或考试。
3. 在 Session 输入 `Math 54 Monday 1 to 2 pm at a library`。
4. 加入房间或开新房间。回到 Schedule，会出现只读 Session 时间块。
5. 在 Session 改期或退出，Schedule 会在打开时/约五秒内更新。

固定演示周为 2026-10-26 至 2026-10-31；自然语言日期尚未推广到任意当前周。
离线模式使用示例地点，禁用地图与模型请求，不能当作实时地点推荐。

## 保存与验证

数据保存在 `data/demo/studymate.db` 和 `data/demo/calendar.db`，重启不会重置。
没有配置稳定登录密钥时，每次进程重启会生成新会话密钥，需要重新登录；
账号、资料、日程和房间本身仍保留。

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/smoke.py
.\.venv\Scripts\python.exe -m pip check
```

Smoke test 启动临时服务、创建两个虚构账号、实际重启进程，检查完整保存与同步。
它不操作你的演示数据库，不访问真实日历、地图或模型。

要开独立预览：

```powershell
.\.venv\Scripts\python.exe -m app.demo --port 8032 --data-dir data/review
```

## 发布到 GitHub

保留 `LICENSE` 与 `CONTRIBUTORS.md`，明确是团队作品。推荐 fork 团队仓库以保留
历史，不要把完整网站写成单人作品。`python tools/package_release.py` 生成干净
源码包，排除密钥、个人数据、数据库和虚拟环境。GitHub push 不等于网站上线。
