"""仓库侧入口 —— 薄壳，真正的实现在 `pasm_agents/selftest_companion.py`。

为什么实现放在包里、这里只留薄壳
--------------------------------
技能正文推荐的安装方式是 `pip install pasm-agents`，而 wheel **不含 `tools/`**
（`packages.find` 只收 `pasm_agents*` 与 `agents*`）。护栏若只放在这儿，
**照文档做的用户根本跑不了它**。放进包内后两种用户都能跑：

    python -m pasm_agents.selftest_companion      # pip 安装的用户（推荐，也是文档里的写法）
    python tools/selftest_companion.py            # 源码仓用户（本文件，转发到上面那个）

用法（本文件）：
    python tools/selftest_companion.py            # 退出码 0=全过，1=有失败
"""
from __future__ import annotations

import sys
from pathlib import Path

# 源码仓模式下 `pasm_agents` 在仓库根，先把它加进 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pasm_agents.selftest_companion import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
