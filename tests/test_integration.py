#!/usr/bin/env python3
"""
测试 Whisper 输出整合器的功能
创建示例数据来验证整合逻辑
"""

import json
import tempfile
import os
from pathlib import Path
import sys

# 添加脚本目录到路径
sys.path.append('/Users/vince/Documents/mediday/scripts')

from whisper_output_integrator import integrate_whisper_outputs, parse_srt_file, parse_whisper_json


def create_sample_srt_content():
    """创建示例 SRT 内容"""
    return """1
00:00:00,000 --> 00:00:03,500
Welcome to this mindfulness meditation.

2
00:00:03,500 --> 00:00:07,200
Take a moment to settle into your seat.

3
00:00:07,200 --> 00:00:11,800
And begin to notice your breath naturally flowing.
"""


def create_sample_json_content():
    """创建示例 JSON 内容（模拟 Whisper 输出格式）"""
    return {
        "transcription": [
            {
                "text": "Welcome",
                "timestamps": {
                    "from": 0,
                    "to": 500,
                    "from_str": "00:00:00,000",
                    "to_str": "00:00:00,500"
                }
            },
            {
                "text": "to",
                "timestamps": {
                    "from": 500,
                    "to": 800,
                    "from_str": "00:00:00,500",
                    "to_str": "00:00:00,800"
                }
            },
            {
                "text": "this",
                "timestamps": {
                    "from": 800,
                    "to": 1200,
                    "from_str": "00:00:00,800",
                    "to_str": "00:00:01,200"
                }
            },
            {
                "text": "mindfulness",
                "timestamps": {
                    "from": 1200,
                    "to": 2000,
                    "from_str": "00:00:01,200",
                    "to_str": "00:00:02,000"
                }
            },
            {
                "text": "meditation.",
                "timestamps": {
                    "from": 2000,
                    "to": 3500,
                    "from_str": "00:00:02,000",
                    "to_str": "00:00:03,500"
                }
            },
            {
                "text": "Take",
                "timestamps": {
                    "from": 3500,
                    "to": 3800,
                    "from_str": "00:00:03,500",
                    "to_str": "00:00:03,800"
                }
            },
            {
                "text": "a",
                "timestamps": {
                    "from": 3800,
                    "to": 3900,
                    "from_str": "00:00:03,800",
                    "to_str": "00:00:03,900"
                }
            },
            {
                "text": "moment",
                "timestamps": {
                    "from": 3900,
                    "to": 4500,
                    "from_str": "00:00:03,900",
                    "to_str": "00:00:04,500"
                }
            }
        ]
    }


def test_integration():
    """测试整合功能"""
    print("🧪 开始测试 Whisper 输出整合器...")
    
    # 创建临时文件
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建示例文件
        srt_file = temp_path / "test.srt"
        json_file = temp_path / "test.json"
        output_file = temp_path / "test_integrated.json"
        
        # 写入示例内容
        with open(srt_file, 'w', encoding='utf-8') as f:
            f.write(create_sample_srt_content())
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(create_sample_json_content(), f, ensure_ascii=False, indent=2)
        
        print(f"📁 临时文件创建在: {temp_dir}")
        print(f"   SRT: {srt_file}")
        print(f"   JSON: {json_file}")
        
        # 测试 SRT 解析
        print("\n📖 测试 SRT 解析...")
        sentences = parse_srt_file(str(srt_file))
        print(f"   解析到 {len(sentences)} 个句子:")
        for i, sentence in enumerate(sentences, 1):
            print(f"   {i}. [{sentence['start_timestamp']} --> {sentence['end_timestamp']}] {sentence['text']}")
        
        # 测试 JSON 解析
        print("\n📖 测试 JSON 解析...")
        words = parse_whisper_json(str(json_file))
        print(f"   解析到 {len(words)} 个词:")
        for i, word in enumerate(words, 1):
            print(f"   {i}. [{word['start_timestamp']} --> {word['end_timestamp']}] '{word['text']}'")
        
        # 测试整合
        print("\n🔄 测试整合功能...")
        try:
            result = integrate_whisper_outputs(str(json_file), str(srt_file), str(output_file))
            
            print(f"\n✅ 整合成功！")
            print(f"   输出文件: {output_file}")
            print(f"   句子数量: {result['summary']['sentence_count']}")
            print(f"   词数量: {result['summary']['word_count']}")
            print(f"   总时长: {result['summary']['total_duration_seconds']:.2f} 秒")
            
            # 显示整合结果的结构
            print(f"\n📋 整合结果结构:")
            print(f"   - metadata: 包含源文件信息和统计")
            print(f"   - sentences: {len(result['sentences'])} 个句子（来自 SRT）")
            print(f"   - words: {len(result['words'])} 个词（来自 JSON）")
            print(f"   - summary: 汇总信息")
            
            # 显示部分内容示例
            if result['sentences']:
                print(f"\n📝 句子示例:")
                sentence = result['sentences'][0]
                print(f"   '{sentence['text']}' ({sentence['start_timestamp']} --> {sentence['end_timestamp']})")
            
            if result['words']:
                print(f"\n🔤 词示例:")
                for word in result['words'][:3]:
                    print(f"   '{word['text']}' ({word['start_timestamp']} --> {word['end_timestamp']})")
            
            return True
            
        except Exception as e:
            print(f"❌ 整合失败: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = test_integration()
    if success:
        print(f"\n🎉 所有测试通过！")
        exit(0)
    else:
        print(f"\n💥 测试失败！")
        exit(1)
