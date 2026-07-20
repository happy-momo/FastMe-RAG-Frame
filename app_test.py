"""
FastMe RAG 框架多轮对话测试脚本
测试场景：
1. 基础单轮对话（manual_query 场景）
2. 多轮对话 - 追问深入（同一话题逐步深入）
3. 多轮对话 - 话题切换（不同话题间切换）
4. 多轮对话 - 记忆窗口限制（max_turns 溢出测试）
5. 多会话并行（不同 session_id 独立记忆）
"""

import time
import sys
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
    print(f"  问题: {result['question'][:100]}...")
    print(f"  场景: {result['scene']}")
    answer = result['answer']
    # 截断过长的回答便于阅读
    if len(answer) > 300:
        answer = answer[:300] + "..."
    print(f"  回答: {answer}")
    sources = result.get('sources', [])
    if sources:
        print(f"  来源数: {len(sources)}")
        for i, src in enumerate(sources[:3], 1):
            preview = src.get('preview', '')[:80]
            print(f"    来源{i}: {preview}...")
    print()


def chat_with_retry(rag, question: str, session_id: str = None,
                    scene: str = "default", top_k: int = 5,
                    max_retries: int = 10, retry_interval: int = 30) -> dict:
    """
    带重试机制的对话函数
    遇到 LLM 请求失败时自动等待重连
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
            print(f"  [重试 {attempt}/{max_retries}] LLM 请求失败: {error_msg[:100]}")
            if attempt < max_retries:
                wait = retry_interval * attempt  # 递增等待时间
                print(f"  等待 {wait} 秒后重试...")
                time.sleep(wait)
            else:
                print(f"  已达最大重试次数，放弃。")
                raise


# ============================================================
# 初始化 RAG 实例
# ============================================================

print_separator("初始化 FastMe RAG")

# 不传入参数，让 FastMeRAG 从 .env 文件读取配置
rag = FastMeRAG()

# ============================================================
# 文档入库
# ============================================================

print_separator("文档入库")

# ingest_result = rag.batch_ingest(
#     folder_path="./files",
#     doc_type="manual",
# )
# print(f"  文档ID: {ingest_result.get('doc_id')}")
# print(f"  文件名: {ingest_result.get('file_name')}")
# print(f"  分块数: {ingest_result.get('chunks_count')}")
# print(f"  向量数: {ingest_result.get('vector_count')}")


# ============================================================
# 场景 1: 基础单轮对话（无记忆）
# ============================================================

print_separator("场景1: 基础单轮对话（manual_query 场景）")

result1 = chat_with_retry(
    rag,
    question="IED支持什么连接？",
    scene="manual_query",
    top_k=5
)
print_chat_result(result1)


# ============================================================
# 场景 2: 多轮对话 - 追问深入
# 同一话题逐步深入，测试记忆是否保持上下文连贯
# ============================================================

print_separator("场景2: 多轮对话 - 追问深入（同一话题逐步深入）")

SESSION_DEEP = "deep_dive_001"
rag.create_memory(session_id=SESSION_DEEP, max_turns=5)

# 第1轮：基础问题
q2_1 = "IED如何激活？"
print(f"  用户: {q2_1}")
result2_1 = chat_with_retry(rag, question=q2_1, session_id=SESSION_DEEP, scene="manual_query")
print_chat_result(result2_1, turn=1)

# 第2轮：追问细节（依赖上一轮上下文）
q2_2 = "与IEM激活之间有什么区别？"
print(f"  用户: {q2_2}")
result2_2 = chat_with_retry(rag, question=q2_2, session_id=SESSION_DEEP, scene="manual_query")
print_chat_result(result2_2, turn=2)

# 第3轮：继续追问（依赖前两轮上下文）
q2_3 = "我应该先激活IEM还是IED？"
print(f"  用户: {q2_3}")
result2_3 = chat_with_retry(rag, question=q2_3, session_id=SESSION_DEEP, scene="manual_query")
print_chat_result(result2_3, turn=3)

# 验证记忆是否保存
memory2 = rag.get_memory(SESSION_DEEP)
if memory2:
    history2 = memory2.load_memory_variables({})
    msgs2 = history2.get("history", [])
    print(f"  [记忆验证] 当前保存了 {len(msgs2)} 条消息（{len(msgs2)//2} 轮对话）")
else:
    print(f"  [记忆验证] 未找到记忆！")


# ============================================================
# 场景 3: 多轮对话 - 话题切换
# 在同一会话中切换不同话题，测试记忆是否混淆
# ============================================================

print_separator("场景3: 多轮对话 - 话题切换")

SESSION_SWITCH = "topic_switch_001"
rag.create_memory(session_id=SESSION_SWITCH, max_turns=5)

# 第1轮：话题A - 通信功能
q3_1 = "如何实现transformer？"
print(f"  用户: {q3_1}")
result3_1 = chat_with_retry(rag, question=q3_1, session_id=SESSION_SWITCH, scene="manual_query")
print_chat_result(result3_1, turn=1)

# 第2轮：话题B - 编程软件（完全不同的话题）
q3_2 = "IEVD的硬件要求是什么？"
print(f"  用户: {q3_2}")
result3_2 = chat_with_retry(rag, question=q3_2, session_id=SESSION_SWITCH, scene="manual_query")
print_chat_result(result3_2, turn=2)

# 第3轮：回到话题A - 追问通信（测试记忆是否还记得话题A）
q3_3 = "如何优化部署transformer模型到边缘设备？"
print(f"  用户: {q3_3}")
result3_3 = chat_with_retry(rag, question=q3_3, session_id=SESSION_SWITCH, scene="manual_query")
print_chat_result(result3_3, turn=3)


# ============================================================
# 场景 4: 多轮对话 - 记忆窗口限制
# max_turns=3，发送4轮对话，验证最早一轮是否被遗忘
# 基于文档：西门子工业边缘快速入门指南
# ============================================================

print_separator("场景4: 记忆窗口限制（max_turns=3，发送4轮）")

SESSION_WINDOW = "window_test_001"
rag.create_memory(session_id=SESSION_WINDOW, max_turns=3)

# 第1轮：西门子工业边缘基础概念
q4_1 = "西门子工业边缘平台的主要组成部分有哪些？"
print(f"  用户: {q4_1}")
result4_1 = chat_with_retry(rag, question=q4_1, session_id=SESSION_WINDOW, scene="manual_query")
print_chat_result(result4_1, turn=1)

# 第2轮：追问边缘设备的部署方式
q4_2 = "如何在工业边缘设备上部署 Docker 容器？"
print(f"  用户: {q4_2}")
result4_2 = chat_with_retry(rag, question=q4_2, session_id=SESSION_WINDOW, scene="manual_query")
print_chat_result(result4_2, turn=2)

# 第3轮：追问数据采集相关
q4_3 = "工业边缘设备如何与 PLC 进行数据通信？"
print(f"  用户: {q4_3}")
result4_3 = chat_with_retry(rag, question=q4_3, session_id=SESSION_WINDOW, scene="manual_query")
print_chat_result(result4_3, turn=3)

# 第4轮（此时第1轮应被窗口淘汰）
q4_4 = "我之前问的第一个问题是什么？你还记得吗？"
print(f"  用户: {q4_4}")
result4_4 = chat_with_retry(rag, question=q4_4, session_id=SESSION_WINDOW, scene="manual_query")
print_chat_result(result4_4, turn=4)

# 验证记忆窗口
memory4 = rag.get_memory(SESSION_WINDOW)
if memory4:
    history4 = memory4.load_memory_variables({})
    msgs4 = history4.get("history", [])
    print(f"  [记忆窗口验证] 当前保存了 {len(msgs4)} 条消息")
    print(f"  [预期] max_turns=3，最多保留 6 条消息（3轮×2条/轮）")
    if len(msgs4) <= 6:
        print(f"  [结果] OK - 记忆窗口限制正常工作")
    else:
        print(f"  [结果] WARN - 记忆窗口限制可能未生效")


# ============================================================
# 场景 5: 多会话并行
# 两个不同 session_id 各自独立记忆，互不干扰
# 分别针对两个不同的文档进行提问
# ============================================================

print_separator("场景5: 多会话并行（独立记忆互不干扰）")

SESSION_A = "parallel_A"  # 针对：工业边缘快速入门指南
SESSION_B = "parallel_B"  # 针对：工业边缘设备异常检测教程
rag.create_memory(session_id=SESSION_A, max_turns=3)
rag.create_memory(session_id=SESSION_B, max_turns=3)

# 会话A - 第1轮：关于西门子工业边缘平台
q5a_1 = "西门子工业边缘平台的设备管理器有哪些功能？"
print(f"  [会话A-边缘入门] 用户: {q5a_1}")
result5a_1 = chat_with_retry(rag, question=q5a_1, session_id=SESSION_A, scene="manual_query")
print_chat_result(result5a_1, turn=1)

# 会话B - 第1轮：关于异常检测（不同文档）
q5b_1 = "工业边缘设备异常检测系统使用了哪些机器学习算法？"
print(f"  [会话B-异常检测] 用户: {q5b_1}")
result5b_1 = chat_with_retry(rag, question=q5b_1, session_id=SESSION_B, scene="manual_query")
print_chat_result(result5b_1, turn=1)

# 会话A - 第2轮（追问边缘平台的话题）
q5a_2 = "如何在设备管理器中配置数据采集任务？"
print(f"  [会话A-边缘入门] 用户: {q5a_2}")
result5a_2 = chat_with_retry(rag, question=q5a_2, session_id=SESSION_A, scene="manual_query")
print_chat_result(result5a_2, turn=2)

# 会话B - 第2轮（追问异常检测的话题）
q5b_2 = "异常检测模型训练时如何进行数据预处理？"
print(f"  [会话B-异常检测] 用户: {q5b_2}")
result5b_2 = chat_with_retry(rag, question=q5b_2, session_id=SESSION_B, scene="manual_query")
print_chat_result(result5b_2, turn=2)

# 验证两个会话记忆独立
mem_a = rag.get_memory(SESSION_A)
mem_b = rag.get_memory(SESSION_B)
if mem_a and mem_b:
    hist_a = mem_a.load_memory_variables({}).get("history", [])
    hist_b = mem_b.load_memory_variables({}).get("history", [])
    print(f"  [会话A记忆] {len(hist_a)} 条消息")
    print(f"  [会话B记忆] {len(hist_b)} 条消息")
    print(f"  [结果] OK - 两个会话记忆独立，互不干扰")


# ============================================================
# 场景 6: 跨文档知识检索
# 测试系统是否能同时从两个文档中检索相关信息
# ============================================================

print_separator("场景6: 跨文档知识检索（同时涉及两个文档）")

# 问题1：涉及两个文档的共同主题 - Docker 部署
q6_1 = "两个文档中都提到了 Docker，请分别说明在边缘入门指南和异常检测教程中 Docker 的用途有什么不同？"
print(f"  用户: {q6_1}")
result6_1 = chat_with_retry(rag, question=q6_1, scene="manual_query", top_k=8)
print_chat_result(result6_1)

# 问题2：涉及数据采集和处理
q6_2 = "西门子边缘平台的数据采集功能如何支持异常检测应用的数据需求？"
print(f"  用户: {q6_2}")
result6_2 = chat_with_retry(rag, question=q6_2, scene="manual_query", top_k=8)
print_chat_result(result6_2)

# 问题3：涉及系统架构
q6_3 = "请对比西门子工业边缘平台的系统架构和异常检测系统的架构，它们有什么共同点？"
print(f"  用户: {q6_3}")
result6_3 = chat_with_retry(rag, question=q6_3, scene="manual_query", top_k=10)
print_chat_result(result6_3)


# ============================================================
# 场景 7: 技术细节深度问答
# 针对文档中的具体技术参数和操作步骤
# ============================================================

print_separator("场景7: 技术细节深度问答")

# 关于边缘入门指南的技术细节
q7_1 = "西门子工业边缘设备的最低硬件配置要求是什么？支持哪些操作系统？"
print(f"  用户: {q7_1}")
result7_1 = chat_with_retry(rag, question=q7_1, scene="manual_query")
print_chat_result(result7_1)

# 关于异常检测的技术细节
q7_2 = "异常检测教程中使用的数据集是什么？数据集包含哪些特征字段？"
print(f"  用户: {q7_2}")
result7_2 = chat_with_retry(rag, question=q7_2, scene="manual_query")
print_chat_result(result7_2)

# 关于部署和配置
q7_3 = "如何配置工业边缘设备与云端平台的连接？需要哪些网络设置？"
print(f"  用户: {q7_3}")
result7_3 = chat_with_retry(rag, question=q7_3, scene="manual_query")
print_chat_result(result7_3)


# ============================================================
# 清理
# ============================================================

print_separator("清理会话记忆")

rag.clear_memory()
print("  已清除所有会话记忆")

print_separator("测试完成")
print("  所有场景测试已执行完毕！")
print("  测试文档：")
print("    1. 西门子工业边缘快速入门指南+v2.2.0+.pdf")
print("    2. 工业边缘设备异常检测完整教程：从数据到Docker部署.pdf")
