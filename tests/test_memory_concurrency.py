"""记忆并发安全测试"""
import threading

from core.chat_pipeline import ChatPipeline


class _NoopLLM:
    def invoke(self, messages):
        class R:
            content = "ok"
        return R()


def _make_pipeline():
    """构建一个跳过 __init__ 的 ChatPipeline,仅保留记忆相关状态"""
    p = ChatPipeline.__new__(ChatPipeline)
    p.prompt_adapter = None
    p.llm = _NoopLLM()
    p.scene_aware_retriever = None
    p.memories = {}
    p.memory_configs = {}
    return p


def _hammer_memory(p, sid, count, barrier, errs):
    try:
        for _ in range(count):
            p.create_memory(sid)                       # 并发创建同一会话
            memory = p.memories[sid]
            memory.save_context({"input": "q"}, {"output": "a"})
        barrier.wait()
    except Exception as e:  # noqa: BLE001
        errs.append(e)


def test_create_memory_concurrent_same_session():
    p = _make_pipeline()
    p._lock = threading.RLock()
    sid = "s1"
    p.create_memory(sid)
    n = 4
    barrier = threading.Barrier(n)
    errs = []
    threads = [
        threading.Thread(target=_hammer_memory, args=(p, sid, 20, barrier, errs))
        for _ in range(n)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errs, f"并发写记忆出现异常: {errs}"
    assert len(p.memories) == 1  # 同一会话只保留一份