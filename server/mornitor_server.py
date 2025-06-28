import subprocess, sys, textwrap, pathlib,json,datetime
from typing import List, Dict,Optional
from fastmcp import FastMCP


mcp = FastMCP()


BASE_DIR   = pathlib.Path(__file__).parent.parent
TASK_FILE  = BASE_DIR / "Tasklist" / "Task.json"
TASK_FILE.parent.mkdir(exist_ok=True)          # 确保 Tasklist 目录存在


# ------------------ 工具：读 / 写 JSON ------------------ #
def _load_tasks() -> List[Dict]:
    if TASK_FILE.exists():
        return json.loads(TASK_FILE.read_text(encoding="utf-8"))
    return []

def _save_tasks(tasks: List[Dict]) -> None:
    TASK_FILE.write_text(
        json.dumps(tasks, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


@mcp.tool()
# ------------------ 创建 / 更新计划任务 ------------------ #
def create_search_task(task_name: str,
                query: str,
                save_dir: Optional[str] = None,
                *,
                # --- 调度相关 ---
                schedule: str = "daily",       # "daily" | "once"
                time_hhmm: str = "09:00",      # 触发时间（两种模式都用得到）
                date_ymd: str | None = None,   # schedule="once" 时必填；若 None 自动设为「明天」
                boot_trigger: bool = False,    # 仅对 daily 有意义
                # --- 账户 & 描述 ---
                description: str = "",
                as_system: bool = False,
                sent_to_phone:bool =True,
                # --- 路径 ---
                py_path: str | None = None,
                script_path: str | None = None
                ) -> None:
    """
     在 Windows 上注册一个定时“上网搜索答案并对答案进行分析后再发送到用户手机”的计划任务，并将创建的任务信息同步写入本项目目录的``Tasklist/Task.json`` 进行持久化管理。

    Params:
        task_name (str):计划任务的名称，即给这个任务起一个名字(英文)，如：DailyNews_IL_IR。
        query (str): 搜索关键词或高级查询字符串，用于上网搜索答案时输入的内容。
        save_dir (str | None, optional)(可选): 将搜索到的答案保存到指定的目录，已经有默认值，可以不填
        schedule:调度类型(有两个选择)，"daily"：每天触发，表示每天定时触发任务一次，"once" ：只触发一次，表示可以在指定的日期时间点触发一次任务
        time_hhmm (str, optional): 任务触发的时间，24 小时制 ``"HH:MM"``。*Daily* 与 *Once* 均适用。
        date_ymd (str | None, optional):``"YYYY-MM-DD"``，仅在 ``schedule="once"`` 时有效。若为 ``None`` 会取今日 +1 天。
        boot_trigger (bool, optional): 仅对 ``schedule="daily"`` 有意义。``True`` → 开机即执行；``False``（默认）→ 仅按 ``time_hhmm`` 执行。
        description (str, optional): 对当前这个任务的描述，描述一下这个任务是做什么的。
        as_system (bool, optional): 是否以 SYSTEM 账户运行（需管理员权限）。有默认值为False，不需要主动改。
        sent_to_phone(bool): 是否需要将结果发送到用户的手机上，如果是就True，不是就False，可以提前询问用户。默认为False。
        py_path (str | None, optional): Python 解释器绝对路径；默认 ``sys.executable``，有默认值，无需填写。
        script_path (str | None, optional): 被调用的抓取脚本绝对路径；默认 ``<BASE_DIR>/scripts/daily_news.py``。无需填写。
    Return：
        string,任务创建成功的提示。
    """

    if py_path is None:
        py_path = sys.executable
    if script_path is None:
        script_path = str(BASE_DIR / "scripts" / "daily_news.py")

    # ------- Powershell 触发器 -------
    if schedule not in {"daily", "once"}:
        raise ValueError('schedule 仅支持 "daily" 或 "once"')

    if schedule == "daily":
        # 09:00 → 9:00AM（PowerShell 需要这种格式）
        hh, mm = map(int, time_hhmm.split(":"))
        ampm   = "AM" if hh < 12 else "PM"
        hh_ps  = hh if 1 <= hh <= 12 else abs(hh - 12)
        time_ps = f"{hh_ps}:{mm:02d}{ampm}"

        trigger_lines = [f"$daily = New-ScheduledTaskTrigger -Daily -At {time_ps}"]
        trigger_names = ["$daily"]
        if boot_trigger:
            trigger_lines.append("$boot = New-ScheduledTaskTrigger -AtStartup")
            trigger_names.append("$boot")
        trigger_block = "\n".join(trigger_lines)
        trigger_list  = ",".join(trigger_names)

        # daily 任务不需要 DeleteExpiredTaskAfter
        settings_extra = "-MultipleInstances IgnoreNew"

    else:  # schedule == "once"
        if date_ymd is None:
            # 若未指定日期，则默认“明天”
            date_ymd = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        dt_ps = f"{date_ymd} {time_hhmm}"
        trigger_block = (
            f"$once = New-ScheduledTaskTrigger -Once "
            f"-At (Get-Date '{dt_ps}')"
        )
        trigger_list = "$once"

        # 过期 24h 后自动删除，防止残留
        # settings_extra = "-DeleteExpiredTaskAfter (New-TimeSpan -Days 1)"
        settings_extra = ""


        # 一次性任务不支持 boot_trigger
        if boot_trigger:
            print("[WARN] schedule='once' 时忽略 boot_trigger=True")

    # ------- 组装 PowerShell -------
    user_part = '-User "SYSTEM" -RunLevel Highest' if as_system else ""
    arg_parts = [
        f"`\"{script_path}`\"",
        f"--taskname `\"{task_name}`\"",
        f"--query `\"{query}`\""
    ]
    if save_dir:  # ← 为空就跳过
        arg_parts.append(f"--save_dir `\"{save_dir}`\"")
    if sent_to_phone:
        arg_parts.append("--sent_to_phone")
    if schedule == "once":
        arg_parts.append("--self_destruct")

    arg_ps = " ".join(arg_parts)

    ps = textwrap.dedent(f"""
        $action = New-ScheduledTaskAction `
                  -Execute "{py_path}" `
                  -Argument "{arg_ps}"

        {trigger_block}

        $set = New-ScheduledTaskSettingsSet `
                 -StartWhenAvailable `
                 {settings_extra}

        Register-ScheduledTask -TaskName "{task_name}" `
                               -Description "{description or query}" `
                               -Action $action `
                               -Trigger {trigger_list} `
                               -Settings $set `
                               {user_part} -Force
    """)

    subprocess.run(["powershell", "-NoLogo", "-NoProfile", "-Command", ps],
                   check=True, text=True)

    # ------- 写入 Task.json -------
    news_file = str(BASE_DIR / "news_logs" / f"{task_name}.json")
    tasks = _load_tasks()
    tasks = [t for t in tasks if t["TaskName"] != task_name]  # 去重
    tasks.append({
        "TaskName": task_name,
        "Description": description or query,
        "Query": query,
        "Schedule": schedule,
        "Date": date_ymd if schedule == "once" else None,
        "Time": time_hhmm,
        "BootTrigger": boot_trigger if schedule == "daily" else False,
        "AsSystem": as_system,
        "CreatedAt": datetime.datetime.now().isoformat(timespec="seconds"),
        "TaskFilePath": news_file
    })
    _save_tasks(tasks)


    return f"[OK] 计划任务 {task_name} 已创建/更新（{schedule}）"



@mcp.tool()
def sent_phone_task(task_name: str,
                task_job:str,
                *,
                # --- 调度相关 ---
                schedule: str = "daily",       # "daily" | "once"
                time_hhmm: str = "09:00",      # 触发时间（两种模式都用得到）
                date_ymd: str | None = None,   # schedule="once" 时必填；若 None 自动设为「明天」
                boot_trigger: bool = False,    # 仅对 daily 有意义
                # --- 账户 & 描述 ---
                description: str = "",
                as_system: bool = False,
                # --- 路径 ---
                py_path: str | None = None,
                script_path: str | None = None
                ) -> None:
    """
     在 Windows 上注册一个定时“发送固定消息到用户手机”计划任务，并将创建的任务信息同步写入本项目目录的``Tasklist/Task.json`` 进行持久化管理。

    Params:
        task_name (str): 计划任务的名称，即给这个任务起一个名字(英文)，如：DailyMessage。
        task_job (str): 告知一下任务是什么，比如:"每日的问候"或"提醒用户去xxxx"等。请直接说明任务，**任务中不要提任何时间**，如"明天或者几月几号等..都不能提！"
        schedule:调度类型(有两个选择)，"daily"：每天触发，表示每天定时触发任务一次，"once" ：只触发一次，表示可以在指定的日期时间点触发一次任务
        time_hhmm (str, optional): 任务触发的时间，24 小时制 ``"HH:MM"``。*Daily* 与 *Once* 均适用。
        date_ymd (str | None, optional):``"YYYY-MM-DD"``，仅在 ``schedule="once"`` 时有效。若为 ``None`` 会取今日 +1 天。
        boot_trigger (bool, optional): 仅对 ``schedule="daily"`` 有意义。``True`` → 开机即执行；``False``（默认）→ 仅按 ``time_hhmm`` 执行。
        description (str, optional): 对当前这个任务的详细描述，比如这个任务有什么注意事项，比如:"任务是提醒用户出门见朋友，**注意提醒用户记得带钱包。**"
        as_system (bool, optional): 是否以 SYSTEM 账户运行（需管理员权限）。有默认值为False，不需要主动改。
        py_path (str | None, optional): Python 解释器绝对路径；默认 ``sys.executable``，有默认值，无需填写。
        script_path (str | None, optional): 被调用的抓取脚本绝对路径；默认 ``<BASE_DIR>/scripts/Scheduled_Remind.py``。无需填写。
    Return：
        string,任务创建成功的提示。
    """

    if py_path is None:
        py_path = sys.executable
    if script_path is None:
        script_path = str(BASE_DIR / "scripts" / "Scheduled_Remind.py")

    # ------- Powershell 触发器 -------
    if schedule not in {"daily", "once"}:
        raise ValueError('schedule 仅支持 "daily" 或 "once"')

    if schedule == "daily":
        # 09:00 → 9:00AM（PowerShell 需要这种格式）
        hh, mm = map(int, time_hhmm.split(":"))
        ampm   = "AM" if hh < 12 else "PM"
        hh_ps  = hh if 1 <= hh <= 12 else abs(hh - 12)
        time_ps = f"{hh_ps}:{mm:02d}{ampm}"

        trigger_lines = [f"$daily = New-ScheduledTaskTrigger -Daily -At {time_ps}"]
        trigger_names = ["$daily"]
        if boot_trigger:
            trigger_lines.append("$boot = New-ScheduledTaskTrigger -AtStartup")
            trigger_names.append("$boot")
        trigger_block = "\n".join(trigger_lines)
        trigger_list  = ",".join(trigger_names)

        # daily 任务不需要 DeleteExpiredTaskAfter
        settings_extra = "-MultipleInstances IgnoreNew"

    else:  # schedule == "once"
        if date_ymd is None:
            # 若未指定日期，则默认“明天”
            date_ymd = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

        dt_ps = f"{date_ymd} {time_hhmm}"
        trigger_block = (
            f"$once = New-ScheduledTaskTrigger -Once "
            f"-At (Get-Date '{dt_ps}')"
        )
        trigger_list = "$once"

        # 过期 24h 后自动删除，防止残留
        # settings_extra = "-DeleteExpiredTaskAfter (New-TimeSpan -Days 1)"
        settings_extra = ""

        # 一次性任务不支持 boot_trigger
        if boot_trigger:
            print("[WARN] schedule='once' 时忽略 boot_trigger=True")

    # ------- 组装 PowerShell -------
    user_part = '-User "SYSTEM" -RunLevel Highest' if as_system else ""
    arg_parts = [
        f"`\"{script_path}`\"",
        f"--task_name `\"{task_name}`\"",
        f"--task_job `\"{task_job}`\"",
        f"--description `\"{description}`\""
    ]

    if schedule == "once":
        arg_parts.append("--self_destruct")

    arg_ps = " ".join(arg_parts)

    ps = textwrap.dedent(f"""
        $action = New-ScheduledTaskAction `
                  -Execute "{py_path}" `
                  -Argument "{arg_ps}"

        {trigger_block}

        $set = New-ScheduledTaskSettingsSet `
                 -StartWhenAvailable `
                 {settings_extra}

        Register-ScheduledTask -TaskName "{task_name}" `
                               -Description "{description}" `
                               -Action $action `
                               -Trigger {trigger_list} `
                               -Settings $set `
                               {user_part} -Force
    """)

    subprocess.run(["powershell", "-NoLogo", "-NoProfile", "-Command", ps],
                   check=True, text=True)

    # ------- 写入 Task.json -------
    news_file = str(BASE_DIR / "news_logs" / f"{task_name}.json")
    tasks = _load_tasks()
    tasks = [t for t in tasks if t["TaskName"] != task_name]  # 去重
    tasks.append({
        "TaskName": task_name,
        "Description": description,
        "TaskJob": task_job,
        "Schedule": schedule,
        "Date": date_ymd if schedule == "once" else None,
        "Time": time_hhmm,
        "BootTrigger": boot_trigger if schedule == "daily" else False,
        "AsSystem": as_system,
        "CreatedAt": datetime.datetime.now().isoformat(timespec="seconds"),
        "TaskFilePath": news_file
    })
    _save_tasks(tasks)


    return f"[OK] 计划任务 {task_name} 已创建/更新（{schedule}）"



@mcp.tool()
# ------------------ 删除计划任务 ------------------ #
def delete_task(task_name: str, *, force: bool = True) -> None:
    """用于删除已经创建好的定时任务
    Params:
        task_name:创建任务时使用的任务的名称(task_name),用于把这个任务停止并删除掉。
    注意: 一次只能删除一个任务。
    """
    cmd = ["schtasks", "/delete", "/tn", task_name]
    if force:
        cmd.append("/f")
    subprocess.run(cmd, check=True, text=True)

    # 同步删除 JSON 记录
    tasks = _load_tasks()
    new_tasks = [t for t in tasks if t["TaskName"] != task_name]
    if len(new_tasks) != len(tasks):
        _save_tasks(new_tasks)
        print(f"[OK] Task.json 中已移除 {task_name}")
    print(f"[OK] 计划任务 {task_name} 已删除")
    return f"[OK] 计划任务 {task_name} 已删除"




@mcp.tool()
def search_task():
    """用来查找目前用户创建了哪些定时任务。"""
    # 读取并解析
    with TASK_FILE.open("r", encoding="utf-8") as f:
        tasks = json.load(f)

    if not tasks:
        return "用户还未创建任何的定时任务"

    # 3. 拼接文本
    lines = []
    for idx, task in enumerate(tasks, start=1):
        name = task.get("TaskName", "")
        desc = task.get("Description", "")
        sched = task.get("Schedule", "")
        time = task.get("Time", "")
        date = task.get("Date", "")

        lines.append(f"任务{idx}：{name}")
        lines.append(f"任务描述: {desc}")

        # 根据 daily/once 分别处理
        if sched == "daily":
            lines.append(f"调度方式: 每日 {time} 执行一次")
        elif sched == "once":
            lines.append(f"调度方式: 在 {date} 的 {time} 执行一次")
        else:
            # 如果有其他类型，直接原样输出
            lines.append(f"调度方式: {sched} {date} {time}")

        # 分隔线
        if idx != len(tasks):
            lines.append("========================")

    # 4. 合并并输出
    result = "\n".join(lines)
    return result



if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8011)
