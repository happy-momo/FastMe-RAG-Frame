"""
FastMe RAG 快速开始示例

这个示例演示如何使用 FastMe RAG 框架完成文档入库和场景化问答。
"""

from app_factory import FastMeRAG

# ========== 1. 初始化 ==========
rag = FastMeRAG()

print("=" * 50)
print("FastMe RAG 快速开始")
print("=" * 50)

# ========== 2. 查看支持的场景和文档类型 ==========
print("\n支持的场景:", rag.get_scenes())
print("支持的文档类型:", rag.get_doc_types())

# ========== 3. 文档入库 ==========
# 单个文件入库
print("\n--- 文档入库 ---")
result = rag.ingest(
    file_path="samples/sample_log.log",
    doc_type="log",
    extra_metadata={"device_id": "EQ001"}
)
print(f"入库结果：{result}")

# 批量文件夹入库（如果有文件夹）
# results = rag.batch_ingest("./manuals", doc_type="manual")
# print(f"批量入库：{len(results)} 个文件")

# ========== 4. 场景化问答 ==========
print("\n--- 故障诊断场景问答 ---")
result = rag.chat(
    question="设备 E001 有哪些故障记录？",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}
)

print(f"问题：{result['question']}")
print(f"答案：{result['answer']}")
print(f"溯源数量：{len(result['sources'])}")

# 打印溯源信息
for i, source in enumerate(result['sources'][:3], 1):
    print(f"\n溯源 {i}:")
    print(f"  Chunk ID: {source.get('chunk_id', 'N/A')}")
    print(f"  设备 ID: {source.get('device_id', 'N/A')}")
    print(f"  故障码：{source.get('fault_code', 'N/A')}")
    print(f"  时间：{source.get('timestamp', 'N/A')}")
    print(f"  预览：{source.get('preview', '')[:100]}...")

# ========== 5. 切换场景 ==========
print("\n--- 设备手册查询场景 ---")
# 假设有手册文档
# rag.ingest("设备手册.pdf", doc_type="manual")
# result = rag.chat("如何更换润滑油？", scene="manual_query")
# print(f"答案：{result['answer']}")

# ========== 6. 自定义场景 ==========
print("\n--- 添加自定义场景 ---")
rag.add_scene(
    name="quality_check",
    doc_type="business",
    prompt_template="default",
    source_fields=["work_order_id", "quality_result", "station"],
    description="质检查询"
)
print(f"当前场景：{rag.get_scenes()}")

# ========== 7. 查看向量库统计 ==========
print(f"\n向量总数：{rag.get_vector_count()}")
