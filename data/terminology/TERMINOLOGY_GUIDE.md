# 术语表使用指南 - Terminology Template Usage Guide

## 文件位置
- **术语表模板**: `/Users/vince/Documents/mediday/terminology_template.json`
- **使用指南**: `/Users/vince/Documents/mediday/TERMINOLOGY_GUIDE.md`

## 文件结构说明

### 1. 元数据部分 (`_metadata`)
包含版本信息、更新日期和使用说明，方便维护和追踪。

### 2. 术语分类
术语表按以下类别组织：

- **`core_mindfulness_terms`**: 核心正念术语
- **`meditation_practices`**: 冥想练习相关
- **`mental_states`**: 心理状态描述
- **`body_awareness`**: 身体觉知相关
- **`emotional_awareness`**: 情绪觉知相关
- **`time_and_space`**: 时空概念
- **`practice_instructions`**: 练习指导用语
- **`waking_up_specific`**: Waking Up 应用特定术语
- **`custom_terms`**: 自定义术语区域

## 如何编辑术语表

### 添加新术语
在相应分类下添加新的键值对：
```json
"new_english_term": "新的中文翻译"
```

### 修改现有翻译
直接修改对应的中文翻译：
```json
"mindfulness": "正念"  // 可以改为其他翻译
```

### 添加新分类
创建新的分类部分：
```json
"new_category_name": {
  "term1": "翻译1",
  "term2": "翻译2"
}
```

### 自定义术语区域
在 `custom_terms` 部分添加你的专用术语：
```json
"custom_terms": {
  "your_specific_term": "你的专用翻译",
  "another_term": "另一个翻译"
}
```

## 与翻译系统集成

### 在现有脚本中使用
1. 在你的翻译脚本中加载术语表：
```python
import json

def load_terminology():
    with open('/Users/vince/Documents/mediday/terminology_template.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 合并所有术语到一个字典
    terms = {}
    for category, category_terms in data.items():
        if category.startswith('_'):  # 跳过元数据
            continue
        if isinstance(category_terms, dict):
            terms.update(category_terms)
    
    return terms
```

### 创建 Google 翻译术语表
使用术语表创建 Google Cloud Translation 的 glossary：
```python
def create_google_glossary(terms_dict, glossary_name):
    # 转换为 Google 术语表格式
    glossary_entries = []
    for en_term, zh_term in terms_dict.items():
        glossary_entries.append(f"{en_term}\t{zh_term}")
    
    # 创建术语表文件
    with open(f'{glossary_name}.tsv', 'w', encoding='utf-8') as f:
        f.write('\n'.join(glossary_entries))
```

## 维护建议

### 定期更新
- 根据翻译质量反馈调整术语
- 添加新发现的重要术语
- 更新 `_metadata` 中的版本和日期

### 备份策略
- 定期备份术语表文件
- 使用版本控制跟踪变更
- 记录重要修改的原因

### 质量控制
- 保持翻译的一致性
- 确保术语符合正念冥想的语境
- 定期审查和优化翻译质量

## 注意事项

1. **编码格式**: 文件使用 UTF-8 编码，确保中文字符正确显示
2. **JSON 格式**: 注意 JSON 语法，避免语法错误
3. **术语一致性**: 同一英文术语在不同分类中应保持翻译一致
4. **上下文考虑**: 某些术语可能需要根据具体语境调整翻译

## 快速开始

1. 打开 `terminology_template.json` 文件
2. 找到相应的分类部分
3. 添加或修改术语对
4. 保存文件
5. 在翻译脚本中重新加载术语表

这个术语表模板为你的正念音频翻译项目提供了一个结构化、易于维护的术语管理方案。
