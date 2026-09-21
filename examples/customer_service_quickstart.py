"""智能客服演示 —— 看到"就资料作答 / 查不到如实说 / 客诉转人工"：

    python -m pasm_agents demo customer-service    # 装过 pasm-agents 后
    python examples/customer_service_quickstart.py # 或从本仓源码直接跑

本产品建在应用框架的 ``BaseApplication`` 上（因为知识库是框架的插件），
所以除了基座 ``pasm-skills`` 还需要 ``pasm-framework`` ——
``pip install pasm-agents`` 会把两者一起装上。
"""

import sys
from pathlib import Path

# 从源码直接跑时用（pip install pasm-agents 后可以删掉这段）：
#   把本仓根加进 sys.path，才能 import pasm_agents
_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO))

from pasm_agents import CustomerServiceAgent, detect_escalation  # noqa: E402


def main():
    cs = CustomerServiceAgent(agent_id="example_shop_cs", persona={
        "name": "小智", "role": "售后客服",
        "tone": "温暖、专业、耐心",
        "hotline": "400-000-0000",
    })

    print(f"[init] {cs!r}  tier={cs.tier}")
    print(f"[kb]   起步资料库已就绪 → {cs.kb_stats()}")
    print()

    # ① 就资料作答（起步资料里已有退换货政策）
    print(f"[answer 就资料作答] {cs.answer('怎么退货？')}")
    print()

    # ② 资料库没有的 —— 如实说不知道，不编造（客服可信度的底线）
    print(f"[answer 查不到]     {cs.answer('你们能送到火星吗？')}")
    print()

    # ③ 客诉自动标记转人工（写入不可被闲聊挤掉的记忆）
    print(f"[answer 客诉]       {cs.answer('我要投诉你们，再不处理就曝光！')}")
    print()

    # ④ 增量喂自己的业务知识，立刻就能答
    n = cs.ingest_faq([{
        "title": "会员日优惠",
        "content": "每月 8 日会员日，黄金会员全场额外 9 折，不与其他优惠叠加。",
        "source": "faq", "tags": ["会员", "优惠"],
    }])
    print(f"[ingest]            +{n} 条")
    print(f"[answer 新资料]     {cs.answer('会员日有什么优惠？')}")
    print()

    # ⑤ 客诉判据可以脱离智能体单独用（例如网关层做预筛）
    print(f"[detect 起诉]       {detect_escalation('我要起诉你们')}")
    print(f"[detect 普通抱怨]   {detect_escalation('这个功能真难用啊')}")

    cs.save()
    print(f"\n[snapshot] {cs.snapshot()}")
    print(f"[saved] {cs.persist_dir}")


if __name__ == "__main__":
    main()
