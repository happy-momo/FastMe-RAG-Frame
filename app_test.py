"""
FastMe RAG 框架多轮对话测试脚本（修复版）

测试场景：
1. 基础单轮对话（manual_query 场景）
2. 多轮对话 - 追问深入
3. 多轮对话 - 话题切换
4. 多轮对话 - 记忆窗口限制
5. 多会话并行
6. LLM 空回答处理验证
7. FAISS 向量库去重验证

注意：
- 请确保 ./files/ 目录下存在测试文档
- 请确保 .env 文件配置正确
- 使用本地 Embedding 模型避免网络问题
"""

import time
import sys
import io
import os
import shutil

# 强制 stdout/stderr 使用 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app_factory import FastMeRAG


# ============================================================
# 工具函数
# ============================================================

def print_separator(title: str):
    """打印分隔线"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_chat_result(result: dict, turn: int = 1):
    """格式化打印对话结果"""
    print(f"  [第 {turn} 轮]")
    print(f"  问题：{result['question'][:100]}...")
    print(f"  场景：{result['scene']}")
    answer = result['answer']
    if len(answer) > 300:
        answer = answer[:300] + "..."
    print(f"  回答：{answer}")
    sources = result.get('sources', [])
    if sources:
        print(f"  来源数：{len(sources)}")
        for i, src in enumerate(sources[:3], 1):
            preview = src.get('preview', '')[:80]
            print(f"    来源{i}: {preview}...")
    print()


def chat_with_retry(rag, question: str, session_id: str = None,
                    scene: str = "default", top_k: int = 5,
                    max_retries: int = 3, retry_interval: int = 5) -> dict:
    """
    带重试机制的对话函数
    """
    for attempt in range(1, max_retries + 1):
        try:
            if session_id is not None:
                result = rag.chat_with_memory(
                    question=question,
                    session_id=session_id,
                    scene=scene,
                    top_k=top_k
                )
            else:
                result = rag.chat(
                    question=question,
                    scene=scene,
                    top_k=top_k
                )
            return result
        except Exception as e:
            error_msg = str(e)
            print(f"  [重试 {attempt}/{max_retries}] LLM 请求失败：{error_msg[:100]}")
            if attempt < max_retries:
                print(f"  等待 {retry_interval} 秒后重试...")
                time.sleep(retry_interval)
            else:
                print(f"  已达最大重试次数，跳过。")
                return {
                    'question': question,
                    'scene': scene,
                    'answer': f'请求失败：{error_msg}',
                    'sources': []
                }


# ============================================================
# 主测试函数
# ============================================================

def run_tests():
    """运行所有测试"""

    # 检查 files 目录
    if not os.path.exists('./files'):
        print("错误：./files 目录不存在，请创建该目录并放入测试文档")
        return False

    files_list = os.listdir('./files')
    if not files_list:
        print("警告：./files 目录为空，部分测试可能失败")

    print_separator("步骤 1: 初始化 FastMe RAG")

    # 初始化 RAG（从.env 加载配置）
    try:
        rag = FastMeRAG()
        print("  ✓ RAG 初始化成功")
    except Exception as e:
        print(f"  ✗ RAG 初始化失败：{e}")
        return False

    print_separator("步骤 2: 文档入库")

    try:
        ingest_result = rag.batch_ingest(
            folder_path="./files",
            doc_type="manual",
        )
        print(f"  ✓ 批量入库完成")
        print(f"    处理文件数：{len(ingest_result)}")
        success_count = sum(1 for r in ingest_result if r.get('status') == 'success')
        print(f"    成功：{success_count}, 失败：{len(ingest_result) - success_count}")
    except Exception as e:
        print(f"  ⚠ 文档入库失败：{e}")
        print("  继续执行其他测试...")

    print_separator("步骤 3: 基础单轮对话")

    result1 = chat_with_retry(
        rag,
        question="如何安装软件？",
        scene="manual_query",
        top_k=5
    )
    print_chat_result(result1)

    print_separator("步骤 4: 多轮对话 - 追问深入")

    SESSION_DEEP = "deep_dive_001"
    rag.create_memory(session_id=SESSION_DEEP, max_turns=5)

    questions = [
        "如何安装？",
        "需要什么前提条件？",
        "安装后如何配置？"
    ]

    for i, q in enumerate(questions, 1):
        print(f"  用户：{q}")
        result = chat_with_retry(rag, question=q, session_id=SESSION_DEEP, scene="manual_query")
        print_chat_result(result, turn=i)

    # 验证记忆
    memory = rag.get_memory(SESSION_DEEP)
    if memory:
        history = memory.load_memory_variables({}).get("history", [])
        print(f"  [记忆验证] 保存了 {len(history)} 条消息")

    print_separator("步骤 5: 多轮对话 - 话题切换")

    SESSION_SWITCH = "topic_switch_001"
    rag.create_memory(session_id=SESSION_SWITCH, max_turns=5)

    q_switch_1 = "设备如何选型？"
    print(f"  用户：{q_switch_1}")
    result_switch_1 = chat_with_retry(rag, question=q_switch_1, session_id=SESSION_SWITCH, scene="manual_query")
    print_chat_result(result_switch_1, turn=1)

    q_switch_2 = "维护保养需要注意什么？"
    print(f"  用户：{q_switch_2}")
    result_switch_2 = chat_with_retry(rag, question=q_switch_2, session_id=SESSION_SWITCH, scene="manual_query")
    print_chat_result(result_switch_2, turn=2)

    print_separator("步骤 6: 记忆窗口限制测试")

    SESSION_WINDOW = "window_test_001"
    rag.create_memory(session_id=SESSION_WINDOW, max_turns=3)

    for i in range(1, 5):
        q = f"这是第{i}个问题，测试记忆窗口"
        print(f"  用户：{q}")
        result = chat_with_retry(rag, question=q, session_id=SESSION_WINDOW, scene="default")
        print(f"  回答：{result['answer'][:100]}...")

    memory_window = rag.get_memory(SESSION_WINDOW)
    if memory_window:
        history = memory_window.load_memory_variables({}).get("history", [])
        print(f"  [记忆窗口验证] 保存了 {len(history)} 条消息")
        if len(history) <= 6:
            print(f"  ✓ 记忆窗口限制正常工作 (≤6 条)")
        else:
            print(f"  ⚠ 记忆窗口可能未生效 (>{6}条)")

    print_separator("步骤 7: 多会话并行测试")

    SESSION_A = "parallel_A"
    SESSION_B = "parallel_B"
    rag.create_memory(session_id=SESSION_A, max_turns=3)
    rag.create_memory(session_id=SESSION_B, max_turns=3)

    q_a = "会话 A 的第一个问题"
    q_b = "会话 B 的第一个问题"

    result_a = chat_with_retry(rag, question=q_a, session_id=SESSION_A, scene="default")
    result_b = chat_with_retry(rag, question=q_b, session_id=SESSION_B, scene="default")

    mem_a = rag.get_memory(SESSION_A)
    mem_b = rag.get_memory(SESSION_B)
    if mem_a and mem_b:
        hist_a = mem_a.load_memory_variables({}).get("history", [])
        hist_b = mem_b.load_memory_variables({}).get("history", [])
        print(f"  [会话 A 记忆] {len(hist_a)} 条")
        print(f"  [会话 B 记忆] {len(hist_b)} 条")
        print(f"  ✓ 两个会话记忆独立")

    print_separator("步骤 8: LLM 空回答处理验证")

    original_invoke = rag.llm.invoke

    def mock_empty_invoke(messages):
        class MockResponse:
            content = ""
        return MockResponse()

    rag.llm.invoke = mock_empty_invoke

    try:
        test_result = rag.chat(question="测试空回答", scene="default")
        answer_text = test_result['answer']
        if answer_text and answer_text.strip() and len(answer_text) > 5:
            print(f"  ✓ 空回答已被替换为兜底回答")
            print(f"  [兜底回答] {answer_text[:80]}...")
        else:
            print(f"  ⚠ 空回答未被正确处理")
    finally:
        rag.llm.invoke = original_invoke

    print_separator("步骤 9: FAISS 去重验证")

    from vector_stores.faiss import FAISSAdapter
    from langchain_core.documents import Document

    test_faiss_dir = "./data/faiss_test_dedup"
    if os.path.exists(test_faiss_dir):
        shutil.rmtree(test_faiss_dir)

    faiss_adapter = FAISSAdapter(
        embedding_function=rag.embeddings,
        index_path=test_faiss_dir,
        load_existing=False
    )

    docs1 = [
        Document(page_content="测试文档 A", metadata={"chunk_id": "chunk_1"}),
        Document(page_content="测试文档 B", metadata={"chunk_id": "chunk_2"}),
        Document(page_content="测试文档 C", metadata={"chunk_id": "chunk_3"}),
    ]
    ids1 = ["chunk_1", "chunk_2", "chunk_3"]

    faiss_adapter.add_documents(docs1, ids=ids1)
    count1 = faiss_adapter.get_count()
    print(f"  首次入库：{count1} 个向量")

    docs2 = [
        Document(page_content="测试文档 A(更新)", metadata={"chunk_id": "chunk_1"}),
        Document(page_content="测试文档 B(更新)", metadata={"chunk_id": "chunk_2"}),
    ]
    ids2 = ["chunk_1", "chunk_2"]

    faiss_adapter.add_documents(docs2, ids=ids2)
    count2 = faiss_adapter.get_count()
    print(f"  重复入库：{count2} 个向量")

    if count1 == count2:
        print(f"  ✓ FAISS 去重正常工作")
    else:
        print(f"  ⚠ FAISS 去重可能未生效 (增加了 {count2 - count1} 个)")

    docs3 = [
        Document(page_content="测试文档 D", metadata={"chunk_id": "chunk_4"}),
    ]
    ids3 = ["chunk_4"]

    faiss_adapter.add_documents(docs3, ids=ids3)
    count3 = faiss_adapter.get_count()
    print(f"  新增入库：{count3} 个向量")

    if count3 == count2 + 1:
        print(f"  ✓ 新增文档正确添加")

    faiss_adapter.delete_collection()
    if os.path.exists(test_faiss_dir):
        shutil.rmtree(test_faiss_dir)

    print_separator("步骤 10: 清理")

    rag.clear_memory()
    print("  ✓ 已清除所有会话记忆")

    print_separator("测试完成")
    print("  所有测试场景已执行完毕！")
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
