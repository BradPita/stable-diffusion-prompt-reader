import sys
import traceback
from sd_prompt_reader.app import main
from sd_prompt_reader.cli import cli

def is_console():
    return False if sys.stdin is None else sys.stdin.isatty()

if __name__ == "__main__":
    try:
        if is_console():
            cli()
        else:
            main()
    except Exception as e:
        # 如果图形界面崩溃，把错误信息写到 error.log 文件里
        with open("error.log", "w") as f:
            f.write(traceback.format_exc())
        # 重新抛出错误，让系统也知道程序崩溃了
        raise e
