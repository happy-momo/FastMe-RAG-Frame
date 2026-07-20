"""
FastMe RAG 自定义配置示例

演示如何动态添加场景、元数据规则，以及更新配置。
"""

from app_factory import FastMeRAG

rag = FastMeRAG()

print("=" * 60)
print("FastMe RAG 自定义配置示例")
print("=" * 60)

# ========== 1. 查看当前配置 ==========
print("\n【当前配置】")
print(f"支持的场景：{rag.get_scenes()}")
print(f"支持的文档类型：{rag.get_doc_types()}")

# ========== 2. 添加新场景 ==========
print("\n【添加新场景】质检查询")

rag.add_scene(
    name="quality_check",
    doc_type="business",
    prompt_template="default",
    top_k=5,
    source_fields=["work_order_id", "quality_result", "station", "line_id"],
    description="质检查询 - 基于质检单和生产记录"
)

print(f"添加后的场景：{rag.get_scenes()}")

# 使用新场景
# result = rag.chat("批次 2024001 的质检结果", scene="quality_check")
# print(f"答案：{result['answer']}")

# ========== 3. 添加元数据抽取规则 ==========
print("\n【添加元数据规则】")

rag.add_metadata_rule(
    field="batch_number",
    patterns=[
        r"批次 (?:号)?[：:\s]*([A-Za-z0-9\-_]+)",
        r"批号 [：:\s]*([A-Za-z0-9\-_]+)",
        r"\b(BATCH[-_]?\d{3,})\b"
    ],
    description="生产批号"
)

rag.add_metadata_rule(
    field="operator_id",
    patterns=[
        r"操作员 [：:\s]*([A-Za-z0-9\-_]+)",
        r"操作工 [：:\s]*([A-Za-z0-9\-_]+)",
        r"\b(OP[-_]?\d{3,})\b"
    ],
    description="操作员编号"
)

print("已添加的元数据字段：batch_number, operator_id")

# ========== 4. 更新场景配置 ==========
print("\n【更新场景配置】")

# 修改 top_k
rag.update_scene_top_k("fault_diagnosis", 10)
print("fault_diagnosis 场景 top_k 已更新为 10")

# 直接修改场景配置
rag.scene_router.scene_config["manual_query"]["top_k"] = 8
print("manual_query 场景 top_k 已更新为 8")

# ========== 5. 批量入库 ==========
print("\n【批量入库】")

# 假设有一个文件夹包含多个日志文件
# results = rag.batch_ingest(
#     folder_path="./logs",
#     doc_type="log",
#     extra_metadata={"line_id": "LN01"},
#     file_extensions=[".log", ".txt"]
# )
#
# success_count = sum(1 for r in results if r.get("status") == "success")
# print(f"批量入库完成：{success_count}/{len(results)} 个文件成功")

# ========== 6. 带审核的入库 ==========
print("\n【带审核的入库】")

# 如果需要先预览切片再确认入库
# result = rag.ingest(
#     file_path="故障日志.log",
#     doc_type="log",
#     extra_metadata={"device_id": "EQ001"},
#     require_review=True  # 返回切片预览，不直接入库
# )
#
# if result["status"] == "waiting_review":
#     print(f"等待审核：{len(result['chunks'])} 个切片")
#     for chunk in result["chunks"][:3]:
#         print(f"  - {chunk['chunk_id']}: {chunk['text'][:50]}...")

# ========== 7. 查看向量库统计 ==========
print("\n【向量库统计】")
print(f"向量总数：{rag.get_vector_count()}")

# ========== 8. 完整工作流示例 ==========
print("\n【完整工作流】")
print("-" * 60)

# 1. 添加新场景
rag.add_scene(
    name="maintenance_check",
    doc_type="manual",
    prompt_template="default",
    source_fields=["chapter_num", "device_model", "source"],
    description="设备点检"
)

# 2. 添加元数据规则
rag.add_metadata_rule(
    field="maintenance_type",
    patterns=[
        r"(定期 | 日常 | 紧急 | 预防性) 维护",
        r"(定期 | 日常 | 紧急 | 预防性) 保养"
    ]
)

# 3. 批量入库
# rag.batch_ingest("./maintenance_logs", doc_type="log")

# 4. 问答
result = rag.chat(
    "设备 E001 的定期维护记录",
    scene="maintenance_check",
    filters={"device_id": "EQ001"}
)

print(f"问题：{result['question']}")
print(f"场景：{result['scene']}")
print(f"答案摘要：{result['answer'][:100]}...")
