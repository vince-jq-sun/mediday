#!/usr/bin/env python3
"""
Whisper 输出整合器
整合 Whisper 生成的 JSON（词级时间戳）和 SRT（正确句子）文件
输出包含正确句子和所有词时间戳的统一 JSON 格式
"""

import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_srt_file(srt_path: str) -> List[Dict[str, Any]]:
    """
    解析 SRT 文件，提取句子和时间信息
    
    Args:
        srt_path: SRT 文件路径
        
    Returns:
        包含句子信息的列表，每个元素包含：
        - text: 句子文本
        - start_time: 开始时间（秒）
        - end_time: 结束时间（秒）
    """
    sentences = []
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # 分割 SRT 条目
    entries = re.split(r'\n\s*\n', content)
    
    for entry in entries:
        lines = entry.strip().split('\n')
        if len(lines) < 3:
            continue
            
        # 第一行是序号，第二行是时间戳，第三行及以后是文本
        timestamp_line = lines[1]
        text_lines = lines[2:]
        text = ' '.join(text_lines).strip()
        
        # 解析时间戳：00:00:01,234 --> 00:00:03,456
        timestamp_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', timestamp_line)
        if not timestamp_match:
            logger.warning(f"无法解析时间戳: {timestamp_line}")
            continue
            
        start_h, start_m, start_s, start_ms = map(int, timestamp_match.groups()[:4])
        end_h, end_m, end_s, end_ms = map(int, timestamp_match.groups()[4:])
        
        start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
        end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
        
        sentences.append({
            'text': text,
            'start_time': start_time,
            'end_time': end_time
        })
    
    return sentences


def parse_whisper_json(json_path: str) -> List[Dict[str, Any]]:
    """
    解析 Whisper 生成的 JSON 文件，提取词级时间戳
    
    Args:
        json_path: JSON 文件路径
        
    Returns:
        包含所有词和时间戳的列表，每个元素包含：
        - text: 词文本
        - start_time: 开始时间（秒）
        - end_time: 结束时间（秒）
    """
    words = []
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 从 transcription 数组中提取所有 tokens
    if 'transcription' in data and isinstance(data['transcription'], list):
        for segment in data['transcription']:
            if 'tokens' in segment and isinstance(segment['tokens'], list):
                for token in segment['tokens']:
                    # 跳过特殊标记（如 [_BEG_], [_TT_xxx] 等）
                    text = token.get('text', '').strip()
                    if text.startswith('[') and text.endswith(']'):
                        continue
                    
                    # 提取时间戳信息
                    timestamps = token.get('timestamps', {})
                    start_timestamp = timestamps.get('from', '00:00:00,000')
                    end_timestamp = timestamps.get('to', '00:00:00,000')
                    
                    # 转换时间戳为秒
                    start_time = timestamp_to_seconds(start_timestamp)
                    end_time = timestamp_to_seconds(end_timestamp)
                    
                    word_data = {
                        'text': text,
                        'start_time': start_time,
                        'end_time': end_time
                    }
                    words.append(word_data)
                    logger.debug(f"找到词: '{text}' ({start_timestamp} -> {end_timestamp})")
    
    logger.info(f"总共提取到 {len(words)} 个词")
    return words


def timestamp_to_seconds(timestamp_str: str) -> float:
    """
    将时间戳字符串转换为秒数
    
    Args:
        timestamp_str: 时间戳字符串，格式如 "00:01:23,456"
        
    Returns:
        秒数（浮点数）
    """
    if not timestamp_str or timestamp_str == "00:00:00,000":
        return 0.0
    
    try:
        # 解析格式：HH:MM:SS,mmm
        time_part, ms_part = timestamp_str.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        
        total_seconds = h * 3600 + m * 60 + s + ms / 1000.0
        return total_seconds
    except (ValueError, IndexError):
        logger.warning(f"无法解析时间戳: {timestamp_str}")
        return 0.0


def milliseconds_to_timestamp(ms) -> str:
    """将毫秒转换为时间戳字符串格式"""
    # 处理不同的输入类型
    if isinstance(ms, str):
        # 如果已经是字符串格式，直接返回
        if ':' in ms:
            return ms
        # 如果是字符串数字，转换为整数
        try:
            ms = int(float(ms))
        except (ValueError, TypeError):
            return "00:00:00,000"
    elif ms is None:
        return "00:00:00,000"
    
    # 确保是整数
    ms = int(ms)
    
    total_seconds = ms // 1000
    milliseconds = ms % 1000
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def map_words_to_sentence_positions(words: List[Dict[str, Any]], sentence_text: str) -> List[Tuple[int, int]]:
    """
    将词数组中的每个词映射到句子文本中的位置
    
    Args:
        words: 词数组，每个元素包含 'text' 字段
        sentence_text: 完整句子文本
        
    Returns:
        位置映射列表，每个元素是 (start_pos, end_pos) 元组
    """
    positions = []
    search_start = 0
    
    for word_data in words:
        word_text = word_data['text'].strip()
        if not word_text:
            positions.append((-1, -1))  # 空词标记为无效位置
            continue
            
        # 在句子中查找这个词的位置
        word_pos = sentence_text.find(word_text, search_start)
        
        if word_pos == -1:
            # 如果找不到，尝试忽略大小写
            word_pos = sentence_text.lower().find(word_text.lower(), search_start)
            
        if word_pos == -1:
            logger.warning(f"无法在句子中找到词: '{word_text}'")
            positions.append((-1, -1))  # 标记为无效位置
        else:
            end_pos = word_pos + len(word_text)
            positions.append((word_pos, end_pos))
            search_start = end_pos  # 下次从这个词的结束位置开始搜索
            
    return positions


def is_punctuation(text: str) -> bool:
    """
    判断文本是否为标点符号
    
    Args:
        text: 要检查的文本
        
    Returns:
        如果是标点符号返回True，否则返回False
    """
    import string
    # 检查是否全部为标点符号或空白字符
    return text.strip() and all(c in string.punctuation or c.isspace() for c in text.strip())


def detect_pauses_and_create_sentence_with_pauses(words: List[Dict[str, Any]], 
                                                  sentence_text: str, 
                                                  pause_threshold: float = 1.0) -> str:
    """
    检测词间停顿并创建带停顿标记的句子
    
    调整后的逻辑：
    1. 跳过标点符号，直接比较标点前后的词
    2. 仅比较两个词的开始时间（不再使用前一个词的结束时间）
    3. 如果需要插入停顿，则插入在标点后
    
    Args:
        words: 词数组，每个元素包含 'text', 'start_time', 'end_time'
        sentence_text: 原始句子文本
        pause_threshold: 停顿阈值（秒）
        
    Returns:
        带停顿标记的句子文本
    """
    if not words or len(words) < 2:
        return sentence_text
    
    # 获取词到句子位置的映射
    word_positions = map_words_to_sentence_positions(words, sentence_text)
    
    # 构建带停顿标记的句子
    sentence_with_pauses = ""
    last_end_pos = 0
    
    # 找到所有非标点符号的词的索引
    non_punct_indices = []
    for i, word_data in enumerate(words):
        if not is_punctuation(word_data['text']):
            non_punct_indices.append(i)
    
    for i, (word_data, (start_pos, end_pos)) in enumerate(zip(words, word_positions)):
        # 添加从上一个词结束到当前词开始之间的文本
        if start_pos > last_end_pos:
            sentence_with_pauses += sentence_text[last_end_pos:start_pos]
        
        # 添加当前词
        if start_pos != -1 and end_pos != -1:
            sentence_with_pauses += sentence_text[start_pos:end_pos]
            last_end_pos = end_pos
        
        # 检查是否需要在当前词后添加停顿标记
        # 只有当前词是标点符号时才考虑在其后插入停顿
        if is_punctuation(word_data['text']) and i < len(words) - 1:
            # 找到标点前的非标点词
            prev_word_idx = None
            for j in range(i - 1, -1, -1):
                if not is_punctuation(words[j]['text']):
                    prev_word_idx = j
                    break
            
            # 找到标点后的非标点词
            next_word_idx = None
            for j in range(i + 1, len(words)):
                if not is_punctuation(words[j]['text']):
                    next_word_idx = j
                    break
            
            # 如果找到了标点前后的词，比较它们的开始时间
            if prev_word_idx is not None and next_word_idx is not None:
                prev_start_time = words[prev_word_idx].get('start_time', 0)
                prev_end_time = words[prev_word_idx].get('end_time', 0)
                next_start_time = words[next_word_idx].get('start_time', 0)
                
                # 额外条件：前一个词的结束时间必须早于后一个词的开始时间
                if (next_start_time > prev_start_time and 
                    prev_end_time < next_start_time):
                    pause_duration = next_start_time - prev_start_time
                    
                    if pause_duration >= pause_threshold:
                        # 在标点后插入停顿标记
                        pause_mark = f" <{pause_duration:.2f}> "
                        sentence_with_pauses += pause_mark
                        logger.debug(f"在标点 '{word_data['text']}' 后检测到 {pause_duration:.2f}s 停顿 ('{words[prev_word_idx]['text']}' [{prev_end_time:.2f}] -> '{words[next_word_idx]['text']}' [{next_start_time:.2f}])") 
        
        # 对于非标点词之间的直接比较（没有标点分隔的情况）
        elif not is_punctuation(word_data['text']) and i < len(words) - 1:
            # 找到下一个非标点词
            next_word_idx = None
            for j in range(i + 1, len(words)):
                if not is_punctuation(words[j]['text']):
                    next_word_idx = j
                    break
            
            if next_word_idx is not None:
                current_start_time = word_data.get('start_time', 0)
                current_end_time = word_data.get('end_time', 0)
                next_start_time = words[next_word_idx].get('start_time', 0)
                
                # 额外条件：当前词的结束时间必须早于下一个词的开始时间
                if (next_start_time > current_start_time and 
                    current_end_time < next_start_time):
                    pause_duration = next_start_time - current_start_time
                    
                    if pause_duration >= pause_threshold:
                        # 检查中间是否有标点，如果有则不在这里插入
                        has_punct_between = any(is_punctuation(words[k]['text']) for k in range(i + 1, next_word_idx))
                        if not has_punct_between:
                            pause_mark = f" <{pause_duration:.2f}> "
                            sentence_with_pauses += pause_mark
                            logger.debug(f"在词 '{word_data['text']}' [{current_end_time:.2f}] 后检测到 {pause_duration:.2f}s 停顿 (-> '{words[next_word_idx]['text']}' [{next_start_time:.2f}])") 
    
    # 添加剩余的文本
    if last_end_pos < len(sentence_text):
        sentence_with_pauses += sentence_text[last_end_pos:]
    
    return sentence_with_pauses


def integrate_whisper_outputs(json_path: str, srt_path: str, output_path: str, pause_threshold: float = 1.0) -> Dict[str, Any]:
    """
    整合 Whisper 的 JSON 和 SRT 输出
    
    句子层面：将所有 SRT 句子合并为一句（连续文本）
    单词层面：使用 JSON 文件的词级时间戳（精确到词）
    停顿检测：检测词间停顿并生成带停顿标记的句子副本
    
    Args:
        json_path: Whisper JSON 文件路径
        srt_path: SRT 文件路径
        output_path: 输出文件路径
        pause_threshold: 停顿阈值（秒），默认1.0秒
        
    Returns:
        整合后的数据字典
    """
    logger.info(f"解析 SRT 文件获取句子: {srt_path}")
    sentences = parse_srt_file(srt_path)
    
    logger.info(f"解析 JSON 文件获取词级时间戳: {json_path}")
    words = parse_whisper_json(json_path)
    
    # 将所有句子合并为一句
    merged_sentence = None
    if sentences:
        # 合并所有句子的文本
        merged_text = ' '.join([s['text'] for s in sentences])
        
        # 使用第一句的开始时间和最后一句的结束时间
        start_time = sentences[0]['start_time']
        end_time = sentences[-1]['end_time']
        
        merged_sentence = {
            'text': merged_text,
            'start_time': start_time,
            'end_time': end_time
        }
        
        logger.info(f"合并了 {len(sentences)} 个句子为一句")
        logger.info(f"合并后文本: {merged_text[:100]}{'...' if len(merged_text) > 100 else ''}")
    
    # 生成带停顿标记的句子
    sentence_with_pauses = None
    pause_count = 0
    if merged_sentence and words:
        sentence_with_pauses = detect_pauses_and_create_sentence_with_pauses(
            words, merged_sentence['text'], pause_threshold
        )
        # 计算检测到的停顿数量
        pause_count = sentence_with_pauses.count('<')
        logger.info(f"检测到 {pause_count} 个停顿（阈值: {pause_threshold}s）")
    
    # 创建整合后的数据结构
    integrated_data = {
        'metadata': {
            'source_json': json_path,
            'source_srt': srt_path,
            'original_sentences_count': len(sentences),
            'total_words': len(words),
            'pause_threshold': pause_threshold,
            'processing_timestamp': None,  # 可以添加处理时间戳
            'integration_method': {
                'sentences_source': 'srt_file_merged',
                'words_source': 'json_tokens',
                'pause_detection': 'word_level_timing',
                'description': '所有SRT句子合并为一句，单词使用JSON tokens（时间戳精确），检测词间停顿'
            }
        },
        'sentence': merged_sentence,  # 单个合并句子
        'sentence_wt_pause': sentence_with_pauses,  # 带停顿标记的句子副本
        'original_sentences': sentences,  # 保留原始句子信息供参考
        'words': words,
        'summary': {
            'total_duration_seconds': max([s['end_time'] for s in sentences]) if sentences else 0,
            'word_count': len(words),
            'original_sentence_count': len(sentences),
            'merged_sentence_count': 1 if merged_sentence else 0,
            'detected_pauses': pause_count
        }
    }
    
    # 保存整合后的数据
    logger.info(f"保存整合数据到: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(integrated_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 整合完成！")
    logger.info(f"   - 原始句子数量: {len(sentences)} -> 合并为 1 句")
    logger.info(f"   - 词数量: {len(words)} (来源: JSON tokens)")
    logger.info(f"   - 总时长: {integrated_data['summary']['total_duration_seconds']:.2f} 秒")
    logger.info(f"   - 检测到停顿: {pause_count} 个 (阈值: {pause_threshold}s)")
    if sentence_with_pauses:
        preview = sentence_with_pauses[:100] + '...' if len(sentence_with_pauses) > 100 else sentence_with_pauses
        logger.info(f"   - 带停顿句子预览: {preview}")
    
    return integrated_data


def main():
    parser = argparse.ArgumentParser(description='整合 Whisper 的 JSON 和 SRT 输出')
    parser.add_argument('json_file', help='Whisper JSON 文件路径')
    parser.add_argument('srt_file', help='SRT 文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（默认：{json_file}_integrated.json）')
    parser.add_argument('-p', '--pause-threshold', type=float, default=1.0, 
                       help='停顿阈值（秒），默认1.0秒。相邻词间隔超过此值时在句子副本中添加停顿标记')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 检查输入文件
    json_path = Path(args.json_file)
    srt_path = Path(args.srt_file)
    
    if not json_path.exists():
        logger.error(f"JSON 文件不存在: {json_path}")
        return 1
        
    if not srt_path.exists():
        logger.error(f"SRT 文件不存在: {srt_path}")
        return 1
    
    # 确定输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        # 移除 .wav 扩展名（如果存在）
        json_stem = json_path.stem
        if json_stem.endswith('.wav'):
            json_stem = json_stem[:-4]  # 移除 '.wav'
        output_path = json_path.parent / f"{json_stem}_integrated.json"
    
    try:
        integrate_whisper_outputs(str(json_path), str(srt_path), str(output_path), args.pause_threshold)
        return 0
    except Exception as e:
        logger.error(f"整合失败: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
