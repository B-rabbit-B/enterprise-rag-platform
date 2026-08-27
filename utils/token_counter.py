"""
Token 统计 & 上下文截断工具（Day5）
- count_tokens: 统计文本 token 数（基于 tiktoken cl100k_base）
- truncate_context: 顺序截断 hits，确保总 token 不超过阈值
"""
from typing import List, Dict

# tiktoken 可选；若未安装，退化为按字符粗略估算（1 token ≈ 4 字符）
try:
    import tiktoken
    _ENCODING = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
        """统计文本 token 数量"""
        if not text:
            return 0
        enc = tiktoken.get_encoding(encoding_name)
        return len(enc.encode(text))
except Exception:
    _ENCODING = None

    def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
        """未安装 tiktoken 时的退化实现：按 4 字符/token 粗略估算"""
        if not text:
            return 0
        return max(1, len(text) // 4)


def truncate_context(hits: List[Dict], max_total_tokens: int) -> List[Dict]:
    """
    上下文截断：从前往后累加 token，超过阈值丢弃后面的片段。
    保证最终拼接到 Prompt 的上下文不会超出模型窗口。

    :param hits: 重排完成后的文档片段列表
    :param max_total_tokens: 允许的最大上下文 token 数
    :return: 截断后的 hits
    """
    if not hits:
        return []

    total = 0
    output = []
    for item in hits:
        doc_text = item.get("document", "")
        cnt = count_tokens(doc_text)
        if total + cnt > max_total_tokens:
            break
        total += cnt
        output.append(item)
    return output