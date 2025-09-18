#!/usr/bin/env python3
"""
批量整合 Whisper 输出文件
扫描指定目录，找到所有的 JSON 和 SRT 文件对，并进行整合
"""

import os
import argparse
from pathlib import Path
import logging
from whisper_output_integrator import integrate_whisper_outputs

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_whisper_file_pairs(directory: str) -> list:
    """
    在指定目录中查找 Whisper 输出文件对（JSON + SRT）
    
    Args:
        directory: 搜索目录
        
    Returns:
        文件对列表，每个元素包含 (json_path, srt_path, base_name)
    """
    directory = Path(directory)
    pairs = []
    
    # 查找所有 JSON 文件
    json_files = list(directory.rglob("*.json"))
    
    for json_file in json_files:
        # 跳过已经整合的文件
        if "_integrated" in json_file.stem:
            continue
            
        # 查找对应的 SRT 文件
        # 尝试几种可能的命名模式
        possible_srt_names = [
            json_file.with_suffix('.srt'),  # 同名但不同扩展名
            json_file.parent / f"{json_file.stem}.srt",  # 确保在同一目录
        ]
        
        # 如果 JSON 文件名包含 .wav，也尝试去掉 .wav 的版本
        if '.wav' in json_file.stem:
            base_name = json_file.stem.replace('.wav', '')
            possible_srt_names.append(json_file.parent / f"{base_name}.srt")
        
        srt_file = None
        for possible_srt in possible_srt_names:
            if possible_srt.exists():
                srt_file = possible_srt
                break
        
        if srt_file:
            pairs.append((str(json_file), str(srt_file), json_file.stem))
            logger.debug(f"找到文件对: {json_file.name} + {srt_file.name}")
        else:
            logger.warning(f"未找到对应的 SRT 文件: {json_file}")
    
    return pairs


def batch_integrate(directory: str, output_suffix: str = "_integrated", dry_run: bool = False) -> int:
    """
    批量整合指定目录中的 Whisper 输出文件
    
    Args:
        directory: 搜索目录
        output_suffix: 输出文件后缀
        dry_run: 是否只是预览而不实际执行
        
    Returns:
        成功处理的文件对数量
    """
    logger.info(f"扫描目录: {directory}")
    
    pairs = find_whisper_file_pairs(directory)
    
    if not pairs:
        logger.warning("未找到任何 JSON+SRT 文件对")
        return 0
    
    logger.info(f"找到 {len(pairs)} 个文件对")
    
    success_count = 0
    
    for json_path, srt_path, base_name in pairs:
        logger.info(f"\n处理文件对: {base_name}")
        logger.info(f"  JSON: {json_path}")
        logger.info(f"  SRT:  {srt_path}")
        
        # 确定输出路径
        json_file = Path(json_path)
        output_path = json_file.parent / f"{base_name}{output_suffix}.json"
        
        # 检查输出文件是否已存在
        if output_path.exists():
            logger.info(f"  输出文件已存在，跳过: {output_path}")
            continue
        
        if dry_run:
            logger.info(f"  [预览] 将输出到: {output_path}")
            success_count += 1
            continue
        
        try:
            logger.info(f"  整合中...")
            integrate_whisper_outputs(json_path, srt_path, str(output_path))
            success_count += 1
            logger.info(f"  ✅ 成功: {output_path}")
        except Exception as e:
            logger.error(f"  ❌ 失败: {e}")
    
    return success_count


def main():
    parser = argparse.ArgumentParser(description='批量整合 Whisper 输出文件')
    parser.add_argument('directory', help='搜索目录路径')
    parser.add_argument('-s', '--suffix', default='_integrated', help='输出文件后缀（默认：_integrated）')
    parser.add_argument('-n', '--dry-run', action='store_true', help='预览模式，不实际执行')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归搜索子目录（默认行为）')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 检查目录
    directory = Path(args.directory)
    if not directory.exists():
        logger.error(f"目录不存在: {directory}")
        return 1
    
    if not directory.is_dir():
        logger.error(f"路径不是目录: {directory}")
        return 1
    
    if args.dry_run:
        logger.info("🔍 预览模式 - 不会实际创建文件")
    
    try:
        success_count = batch_integrate(
            str(directory), 
            args.suffix, 
            args.dry_run
        )
        
        if args.dry_run:
            logger.info(f"\n🔍 预览完成！找到 {success_count} 个可处理的文件对")
            logger.info("使用不带 --dry-run 参数的命令来实际执行整合")
        else:
            logger.info(f"\n✅ 批量整合完成！成功处理 {success_count} 个文件对")
        
        return 0
        
    except Exception as e:
        logger.error(f"批量整合失败: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
