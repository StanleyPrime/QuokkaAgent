import asyncio
import venv
from pathlib import Path
from pathlib import PureWindowsPath, PurePosixPath
from autogen_core import CancellationToken
from autogen_core.code_executor import CodeBlock
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from fastmcp import FastMCP
import re
import os

# 适配docker image的路径映射
WINPATH_RE = re.compile(r"""
    (["'])              # 开头引号
    ([A-Za-z]):         # 盘符
    [\\/]{1}            # 必有的反斜杠或斜杠
    ([^"']*?)           # 剩下的部分（非贪婪）
    \1                  # 收尾引号要和开头配对
""", re.VERBOSE)

def win_to_container_path(win_path: str, root: str = "/mnt") -> str:
    """把 C:\foo\bar → /mnt/c/foo/bar；如果不是盘符路径则原样返回"""
    p = PureWindowsPath(win_path)
    if p.drive:                                   # 有盘符才处理
        drive = p.drive[0].lower()
        posix = PurePosixPath(root) / drive / PurePosixPath(*p.parts[1:])
        return str(posix)
    return win_path

def patch_windows_paths(code: str) -> str:
    """在源代码里批量把硬编码盘符改成 /mnt/{drive}/…"""
    def _sub(m):
        quote, drive, rest = m.groups()
        new_path = win_to_container_path(f"{drive}:{os.sep}{rest}")
        return f'{quote}{new_path}{quote}'
    return WINPATH_RE.sub(_sub, code)


# ---------- 1. 优化：在服务器启动时一次性准备好环境（新增部分） ----------
# 定义工作目录和虚拟环境目录
work_dir = Path("coding")
venv_dir = work_dir / ".venv"

# 创建工作目录
work_dir.mkdir(exist_ok=True)

# 创建虚拟环境构建器并获取上下文
venv_builder = venv.EnvBuilder(with_pip=True)
# 只有当虚拟环境不存在时才创建，避免重复操作
if not venv_dir.exists():
    print(f"Creating virtual environment in {venv_dir}...")
    venv_builder.create(venv_dir)
else:
    print(f"Virtual environment in {venv_dir} already exists.")

venv_context = venv_builder.ensure_directories(venv_dir)

# 创建一个临时的 local_executor 实例，专门用于安装依赖
# 注意：这个 executor 只用于初始化，工具函数中会创建自己的 executor
installer_executor = LocalCommandLineCodeExecutor(work_dir=work_dir, virtual_env_context=venv_context)

# 定义需要安装的包
check_and_install_script = f"""
import subprocess, sys
subprocess.run([sys.executable, '-m', 'pip', 'install',
                '--no-cache-dir', 'matplotlib', 'pandas', 'numpy'],
               check=True)
"""

# 异步执行安装脚本
print("Checking and installing required packages...")
asyncio.run(installer_executor.execute_code_blocks(
    code_blocks=[
        CodeBlock(language="python", code=check_and_install_script),
    ],
    cancellation_token=CancellationToken(),
))
print("Environment setup complete.")

# ---------- 2. 创建 FastMCP 实例 ----------
mcp = FastMCP(name="Code_executed_Server")


# ---------- 3. 改造工具函数（修改部分） ----------

@mcp.tool()
async def python_code_execution(codeblock: str = None):  # 修改点 1: 将函数声明为 async def
    """
    在单独的环境中执行python代码,环境中包含了matplotlib模块和pandas模块还有numpy模块，不需要额外的安装。
    如果代码中需要保存内容的话，比如Image.save()或df.to_csv()等，**且如果用户没有指定保存路径**，请默认保存到: r'C:\\code_data'文件夹中。
    Params:
        codeblock: 标准格式的python代码块，只允许放入python的代码，不能有其他的任何文本
    Return：
        返回的是代码运行后控制台会输出的结果(String类型)
    """
    # sanitized = patch_windows_paths(codeblock)
    # 环境和依赖已在启动时准备好，这里直接使用
    local_executor = LocalCommandLineCodeExecutor(work_dir=work_dir, virtual_env_context=venv_context)

    # 修改点 2: 直接 await 异步函数，而不是用 asyncio.run()
    result = await local_executor.execute_code_blocks(
        code_blocks=[
            CodeBlock(language="python", code=codeblock),
        ],
        cancellation_token=CancellationToken(),
    )

    # 假设我们关心的是标准输出
    # aio_execute_code_blocks 返回的是一个列表，对应每个 code_block 的结果
    # 每个结果是一个元组 (exit_code, output_str, error_str)
    # 直接检查 result 对象是否存在即可
    if result:
        # 直接访问对象的属性，而不是通过索引
        if result.exit_code == 0:
            # 如果成功，返回标准输出
            return result.output
        else:
            # 如果失败，返回包含退出码和错误信息的字符串
            return f"Error executing code (exit code {result.exit_code}):\n{result}"

    return "No result from code execution."


if __name__ == '__main__':
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8004)