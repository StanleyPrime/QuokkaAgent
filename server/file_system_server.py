import os
import shutil
import pathlib
from datetime import datetime
import difflib
import fnmatch
from fastmcp import FastMCP
import re
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).with_name(".env")   # 100% 指向当前脚本所在目录

load_dotenv(dotenv_path=ENV_PATH, override=False)

mcp = FastMCP()



@mcp.tool()
def read_file(path: str) -> str | None:
    """
    读取文件的全部内容。

    以 UTF-8 编码读取文件的完整内容。
    输入: path (字符串) - 文件路径
    返回: 文件内容 (字符串)，如果发生错误则返回 None。
    """
    description = "以 UTF-8 编码读取文件的完整内容。" # 函数内部的描述信息
    print(f"描述: {description}")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"错误: 文件未找到 '{path}'")
        return None
    except Exception as e:
        print(f"读取文件 '{path}' 时出错: {e}")
        return None


@mcp.tool()
def read_image_file(path:str):
    """
直接获取到图片格式的文件内容(jpg，png,webp等).**如果是想要直接看到图片内容就调用这个函数。**
Params:
    path:图片的绝对路径，比如:r"C:\\Users\\85321\\OneDrive\\图片\\屏幕快照\\1.png"
Return:
    直接返回图片的内容以便做图片描述或者理解。
"""



@mcp.tool()
def read_multiple_files(paths: list[str]) -> dict[str, str | None]:
    """
    同时读取多个文件。

    读取失败不会中断整个操作。
    输入: paths (字符串列表) - 文件路径列表。
    返回: 一个字典，键是文件路径，值是文件内容 (字符串)，
             如果某个文件读取失败，则对应的值为 None。
    """
    description = "同时读取多个文件；读取失败不会中断整个操作。" # 函数内部的描述信息
    print(f"描述: {description}")
    results = {}
    for path_item in paths:
        results[path_item] = read_file(path_item) # 重用单个 read_file 函数的逻辑
    return results



@mcp.tool()
def write_file(path: str, content: str) -> bool:
    """
    创建新文件或覆盖现有文件 (请谨慎操作)。

    输入:
    path (字符串): 文件位置
    content (字符串): 文件内容
    返回: 如果成功则为 True，否则为 False。
    """
    description = "创建新文件或覆盖现有文件。" # 函数内部的描述信息
    print(f"描述: {description}")
    try:
        # 确保父目录存在
        parent_dir = pathlib.Path(path).parent
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
            print(f"已创建父目录: '{parent_dir}'")

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"文件 '{path}' 写入成功。")
        return True
    except Exception as e:
        print(f"写入文件 '{path}' 时出错: {e}")
        return False



@mcp.tool()
def edit_file(path: str, edits: list[dict[str, str]], dryRun: bool = False) -> str | None:
    """
    使用模式匹配和格式化进行选择性编辑。

    特性:
    基于行和多行的内容匹配 (通过字符串替换实现)。
    具有正确定位能力的多个同时编辑 (按顺序应用)。
    Git 风格的差异输出及上下文 (使用 difflib)。
    使用演练模式预览更改。
    注意: 此实现简化了“空白标准化与缩进保留”和“缩进样式检测与保留”等高级功能。
          替换是字面上的。

    输入:
    path (字符串): 要编辑的文件
    edits (数组): 编辑操作列表。每个字典应包含 'oldText' 和 'newText'。
                   示例: [{'oldText': '查找此文本', 'newText': '替换为此文本'}]
    dryRun (布尔值): 预览更改而不应用 (默认为 False)

    返回: 如果 dryRun 为 True 且检测到更改，则返回详细的差异字符串。
             如果 dryRun 为 False (直接应用更改) 或在 dryRun 中无更改，则返回 None。
             如果发生问题，则向控制台打印错误。
    """
    description = "使用高级模式匹配和格式化进行选择性编辑。" # 函数内部的描述信息
    print(f"描述: {description}")

    original_content = read_file(path)
    if original_content is None:
        print(f"错误: 无法编辑文件 '{path}'，因为它无法被读取。")
        return None

    modified_content = original_content
    has_changes = False

    for edit_op in edits:
        old_text = edit_op.get('oldText')
        new_text = edit_op.get('newText')

        if old_text is None or new_text is None:
            print(f"警告: 无效的编辑操作被跳过 (缺少 'oldText' 或 'newText'): {edit_op}")
            continue

        if old_text in modified_content:
            modified_content = modified_content.replace(old_text, new_text)
            if old_text != new_text: # 检查是否发生了实际更改
                 has_changes = True


    if not has_changes:
        print("根据提供的编辑，未检测到任何更改。")
        if dryRun:
            return "没有要应用的更改。"
        return None

    if dryRun:
        print(f"对 '{path}' 进行演练:")
        # 生成差异
        diff = difflib.unified_diff(
            original_content.splitlines(keepends=True),
            modified_content.splitlines(keepends=True),
            fromfile=f"a/{path}", # 差异源文件标记
            tofile=f"b/{path}",   # 差异目标文件标记
            lineterm='\n'
        )
        diff_output = "".join(diff)
        if not diff_output:
            return "没有文本差异可显示 (尽管如果 oldText 等于 newText，替换可能已发生但被计为更改)。"
        print("--- 差异开始 ---")
        print(diff_output)
        print("--- 差异结束 ---")
        return diff_output
    else:
        print(f"正在将更改应用于 '{path}':")
        if write_file(path, modified_content):
            print(f"文件 '{path}' 编辑成功。")
        else:
            print(f"错误: 未能将更改写入 '{path}'。")
        return None # 非演练模式不返回差异输出



@mcp.tool()
def create_directory(path: str) -> bool:
    """
    创建新目录或确保其存在。

    如果需要，会创建父目录。
    如果目录已存在，则静默成功。
    Input: path (字符串) - 目录路径
    返回: 如果目录存在或已创建，则为 True，出错则为 False。
    """
    description = "创建新目录或确保其存在，包括父目录。" # 函数内部的描述信息
    print(f"描述: {description}")
    try:
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        print(f"目录 '{path}' 已确保存在。")
        return True
    except Exception as e:
        print(f"创建目录 '{path}' 时出错: {e}")
        return False



@mcp.tool()
def list_directory(path: str) -> list[str] | None:
    """
    列出目录内容，并带有 [FILE] 或 [DIR] 前缀。

    输入: path (字符串) - 目录路径
    返回: 表示目录内容的字符串列表，如果路径无效则返回 None。
    """
    description = "列出目录内容，并带有 [FILE] 或 [DIR] 前缀。" # 函数内部的描述信息
    print(f"描述: {description}")
    dir_path = pathlib.Path(path)
    if not dir_path.is_dir():
        print(f"错误: 路径 '{path}' 不是一个目录或不存在。")
        return None

    contents = []
    try:
        for item in dir_path.iterdir():
            if item.is_file():
                contents.append(f"[FILE] {item.name}")
            elif item.is_dir():
                contents.append(f"[DIR] {item.name}")
            else:
                contents.append(f"[OTHER] {item.name}") # 其他类型，如符号链接等
        return contents
    except Exception as e:
        print(f"列出目录 '{path}' 内容时出错: {e}")
        return None



@mcp.tool()
def move_file(source: str, destination: str) -> bool:
    """
    移动或重命名文件和目录。

    如果目标存在，则操作失败以防止意外覆盖。
    输入:
    source (字符串) - 源路径
    destination (字符串) - 目标路径
    返回: 如果成功则为 True，否则为 False。
    """
    description = "移动或重命名文件和目录；如果目标存在则失败。" # 函数内部的描述信息
    print(f"描述: {description}")
    # ① 先做路径映射 → ② 再转 Path 对象
    src_path = pathlib.Path(source)
    dst_path = pathlib.Path(destination)

    # --- 基本检查 ---
    if not src_path.exists():
        print(f"错误: 源路径 '{source}' 不存在。")
        return False
    if dst_path.exists():
        print(f"错误: 目标路径 '{destination}' 已存在。移动操作中止。")
        return False

    try:
        # 确保目标父目录存在
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        print(f"已成功将 '{source}' 移动到 '{destination}'。")
        return True
    except Exception as e:
        print(f"移动 '{source}' 到 '{destination}' 时出错: {e}")
        return False



@mcp.tool()
def search_files(path: str, pattern: str, exclude_patterns: list[str] | None = None) -> list[str]:
    """
    递归搜索文件/目录。

    主模式匹配不区分大小写。
    排除模式支持 Glob 格式。
    输入:
    path (字符串): 起始目录
    pattern (字符串): 搜索模式 (对文件名/目录名不区分大小写)
    exclude_patterns (字符串列表): 可选。要排除的 glob 模式列表。
                                 匹配任何这些模式的路径将被跳过。
    返回: list[字符串] - 匹配项的完整路径列表。
    """
    description = "递归搜索文件/目录，具有不区分大小写的匹配和排除功能。" # 函数内部的描述信息
    print(f"描述: {description}")
    matches = []
    start_path = pathlib.Path(path)
    if not start_path.is_dir():
        print(f"错误: 搜索路径 '{path}' 不是一个目录或不存在。")
        return []

    if exclude_patterns is None:
        exclude_patterns = []

    # 为不区分大小写的搜索规范化模式
    search_pattern_lower = pattern.lower()

    for item in start_path.rglob("*"): # rglob 执行递归搜索
        item_str = str(item)
        item_name_lower = item.name.lower()

        # 首先检查排除模式
        excluded = False
        for ex_pattern in exclude_patterns:
            if fnmatch.fnmatch(item_str, ex_pattern) or fnmatch.fnmatch(item.name, ex_pattern):
                excluded = True
                break
        if excluded:
            continue

        # 检查主搜索模式 (不区分大小写)
        if search_pattern_lower in item_name_lower:
            matches.append(item_str)

    return matches



@mcp.tool()
def get_file_info(path: str) -> dict | None:
    """
    获取详细的文件/目录元数据。

    输入: path (字符串) - 文件或目录路径
    返回: 包含元数据的字典，如果路径不存在则返回 None。
             键: 'name', 'fullPath', 'type', 'size' (字节),
                   'creationTime', 'modifiedTime', 'accessTime',
                   'permissions' (八进制字符串)。
    """
    description = "获取详细的文件/目录元数据。" # 函数内部的描述信息
    print(f"描述: {description}")
    file_path = pathlib.Path(path)

    if not file_path.exists():
        print(f"错误: 路径 '{path}' 不存在。")
        return None

    try:
        stat_info = file_path.stat()
        info = {
            "name": file_path.name,
            "fullPath": str(file_path.resolve()),
            "type": "directory" if file_path.is_dir() else "file" if file_path.is_file() else "other",
            "size": stat_info.st_size, # 单位：字节
            "creationTime": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "modifiedTime": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "accessTime": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            "permissions": oct(stat_info.st_mode & 0o777) # 权限（八进制格式，例如 0o755）
        }
        return info
    except Exception as e:
        print(f"获取 '{path}' 信息时出错: {e}")
        return None



@mcp.tool()
def list_allowed_directories(predefined_list: list[str] | None = None) -> list[str]:
    """
    列出服务器允许访问的所有目录。

    对于本地脚本，这通常意味着运行脚本的用户有权访问的目录。
    此函数可以通过返回预定义列表或一些常见的可访问目录 (如果未提供列表) 来模拟此行为。
    无需输入 (可选地，可以传递预定义列表用于测试/配置)。
    返回: 目录路径的列表。
    """
    description = "列出服务器（或脚本环境）配置为允许访问的所有目录。" # 函数内部的描述信息
    print(f"描述: {description}")

    if predefined_list is not None:
        # 在此示例中，确保所有预定义路径都是绝对路径并且目录存在
        # 在实际场景中，这些可能只是来自配置的字符串。
        return [str(pathlib.Path(p).resolve()) for p in predefined_list if pathlib.Path(p).is_dir()]

    # 示例：返回当前工作目录和用户的主目录
    # 这些通常是可访问的。
    allowed = []
    try:
        allowed.append(str(pathlib.Path.cwd()))
    except Exception as e:
        print(f"无法获取当前工作目录: {e}")

    try:
        allowed.append(str(pathlib.Path.home()))
    except Exception as e:
        print(f"无法获取主目录: {e}")

    # 您也可以从环境变量添加路径
    # env_allowed_paths = os.environ.get("ALLOWED_SCRIPT_DIRS")
    # if env_allowed_paths:
    #     allowed.extend(p.strip() for p in env_allowed_paths.split(os.pathsep))

    # 在此示例中，过滤掉非目录和重复项
    # 在真实的“允许列表”场景中，它们将只是字符串。
    final_allowed = []
    seen = set()
    for p_str in allowed:
        p = pathlib.Path(p_str)
        if p.is_dir() and str(p) not in seen:
            final_allowed.append(str(p))
            seen.add(str(p))

    return final_allowed


@mcp.tool()
def delete_path(path: str, recursive: bool = False) -> bool:
    """
    删除文件或目录。

    参数
    ----
    path : str
        目标文件或目录的路径。
    recursive : bool, 默认 False
        • 当 path 指向目录时：
          - False：仅当目录为空时才会删除，否则报错。
          - True ：递归删除目录及其全部内容（相当于 `rm -rf`）。
        • 当 path 指向文件或符号链接时，该参数忽略。

    返回值
    ------
    bool
        删除成功返回 True；出现任何错误返回 False，并在控制台打印原因。
    """
    description = "删除文件或目录，支持递归删除并提供详细错误提示。"
    print(f"描述: {description}")

    target = pathlib.Path(path)

    # 1. 基本存在性检查
    if not target.exists():
        print(f"错误: 路径 '{path}' 不存在。")
        return False

    try:
        # 2. 文件或符号链接
        if target.is_file() or target.is_symlink():
            target.unlink()                      # os.remove 的 pathlib 形式
        # 3. 目录处理
        elif target.is_dir():
            if recursive:
                shutil.rmtree(target)            # 递归删除（目录可非空）
            else:
                if any(target.iterdir()):        # 非空目录 → 报错
                    print(
                        f"错误: 目录 '{path}' 非空。"
                        " 若要强制删除请将 recursive=True。"
                    )
                    return False
                target.rmdir()                   # 空目录删除
        else:
            # 极少见：既不是普通文件也不是目录（如设备文件）
            print(f"错误: 路径 '{path}' 既不是文件也不是目录。")
            return False

        print(f"'{path}' 删除成功。")
        return True

    except Exception as e:
        print(f"删除 '{path}' 时出错: {e}")
        return False

if __name__ == '__main__':
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
