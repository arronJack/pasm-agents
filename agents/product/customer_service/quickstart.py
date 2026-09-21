"""CustomerServiceAgent 的 60 秒上手示例。

直接跑：
    python agents/product/customer_service/quickstart.py

（pip install pasm-agents 之后可以把上面那段 sys.path 引导删掉）
"""
import sys
from pathlib import Path

# 从源码直接跑时用（pip install pasm-agents 之后可以删掉这几行）：
#   把仓库根加进 sys.path，才能 import pasm_agents
_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))
try:
    import pasm_agents  # noqa: F401
except ImportError:
    for _sib_name in ("pasm-framework", "pasm-skills"):
        _sib = _REPO.parent / _sib_name
        if _sib.is_dir():
            sys.path.insert(0, str(_sib))

from pasm_agents import CustomerServiceAgent  # noqa: E402


def main() -> None:
    cs = CustomerServiceAgent(agent_id="quickstart_cs", persona={
        "name": "小智", "role": "售后客服",
        "tone": "温暖、专业、耐心",
        "hotline": "400-000-0000",
    })

    # 起步资料首次启动已自动灌好，直接就能答
    print("Q: 怎么退货？")
    print("A:", cs.answer("怎么退货？"))
    print()

    # 换成自己的业务知识（增量补充，不会清掉已有资料）
    cs.ingest_faq([{
        "title": "会员日优惠",
        "content": "每月 8 日会员日，黄金会员全场额外 9 折，不与其他优惠叠加。",
        "source": "faq", "tags": ["会员", "优惠"],
    }])
    print("Q: 会员日有什么优惠？")
    print("A:", cs.answer("会员日有什么优惠？"))
    print()

    # 查不到就如实说不知道（不编造）
    print("Q: 你们能送到火星吗？")
    print("A:", cs.answer("你们能送到火星吗？"))
    print()

    # 客诉自动标记转人工
    print("Q: 我要投诉你们，再不处理就曝光！")
    print("A:", cs.answer("我要投诉你们，再不处理就曝光！"))
    print()

    cs.save()
    print("快照:", cs.snapshot())
    print()
    print("[ok] 完成")


if __name__ == "__main__":
    main()
