# T4 · BGE-M3 真嵌入 + FAISS 索引

> 主仓库 M3_art_rag 默认使用 hash-mock embedding 作为离线兜底。
> 这一步换上真的 BGE-M3（中英双语 dense + sparse 多向量），让检索从语义"对得上但分不出朝代"升级为可用 RAG。

---

## 模型依赖

| 模型 | HF repo | 大小 | 协议 |
|---|---|---|---|
| BGE-M3 | `BAAI/bge-m3` | 2.2 GB | MIT |

```bash
huggingface-cli download BAAI/bge-m3
```

## 数据依赖

| 数据 | 路径 | 大小 | 来源 |
|---|---|---|---|
| RAG 切片 | `$ECHOSCROLL_DATA/rag/chunks.jsonl` | 1.5 MB / 1129 行 | 主仓库 `echoscroll/scripts/build_rag_corpus.py` 已生成 |

格式（每行）：

```json
{
  "id": "cle_127815__0",
  "text": "...策展文 ≤ 500 字符...",
  "meta": {"dynasty": "Ming", "painter": "Du Jin", "motif": "literati", "source": "cleveland"}
}
```

## 运行

```bash
pip install -r requirements.txt
python build_index.py \
    --chunks $ECHOSCROLL_DATA/rag/chunks.jsonl \
    --model BAAI/bge-m3 \
    --batch-size 32 \
    --out index/
```

4090 跑 1129 chunk × 1024 维 ≈ **10 min**；CPU 也能跑，约 1 h。

## 期望产出

```
index/
├── faiss_bge_m3.index        # FAISS IndexFlatIP, dim=1024
├── id_map.json               # int → chunk_id 映射
├── chunks_meta.parquet       # 元数据副本，供过滤检索
└── build_stats.json          # 构建耗时、模型版本、chunks 总数
```

## 接 EchoScroll 主仓库

把 `index/` 整个拷到：

```bash
cp -r index/* /path/to/echoscroll/M3_art_rag/index/
```

主仓库 `rag_store.py::ArtRAGStore.from_index()` 会自动读它，替换 hash-mock。

## 验证

```bash
python query.py --q "Northern Song mountain landscape misty distance"
# 期望：top-1 命中 Juran / Fan Kuan / 同期山水
```
