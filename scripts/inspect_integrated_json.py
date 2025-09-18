#!/usr/bin/env python3
"""
检查整合后的 JSON 文件内容
"""

import json
import argparse
from pathlib import Path


def inspect_integrated_json(file_path: str):
    """检查整合后的 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📁 文件: {file_path}")
    print(f"📊 统计信息:")
    print(f"   - 句子数量: {data['summary']['sentence_count']}")
    print(f"   - 词数量: {data['summary']['word_count']}")
    print(f"   - 总时长: {data['summary']['total_duration_seconds']:.2f} 秒")
    
    print(f"\n📝 句子列表:")
    for i, sentence in enumerate(data['sentences'], 1):
        print(f"   {i}. [{sentence['start_timestamp']} --> {sentence['end_timestamp']}]")
        print(f"      {sentence['text']}")
    
    print(f"\n🔤 词列表:")
    for i, word in enumerate(data['words'], 1):
        print(f"   {i}. [{word['start_timestamp']} --> {word['end_timestamp']}] '{word['text']}'")
    
    print(f"\n📋 元数据:")
    print(f"   - 源 JSON: {data['metadata']['source_json']}")
    print(f"   - 源 SRT: {data['metadata']['source_srt']}")


def main():
    parser = argparse.ArgumentParser(description='检查整合后的 JSON 文件')
    parser.add_argument('file', help='整合后的 JSON 文件路径')
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return 1
    
    try:
        inspect_integrated_json(str(file_path))
        return 0
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
