# 快速测试Episode Selector

## 测试步骤

1. **启动GUI**
   ```bash
   bash process/4_review-record.sh
   ```

2. **验证初始状态**
   - ✓ Collection下拉列表应该显示: `awake_where_you_are_english`
   - ✓ Episode下拉列表应该显示: `1-2_foundational_meditation_sample-1`
   - ✓ Current标签应该显示: `Current: awake_where_you_are_english/1-2_foundational_meditation_sample-1`

3. **测试切换功能**
   - 点击Collection下拉列表，应该看到: `awake_where_you_are_english` (以及其他temp/下的目录)
   - 选择 `awake_where_you_are_english`
   - Episode下拉列表应该自动更新，显示:
     - `1-1_introduction`
     - `1-2_foundational_meditation`
     - `1-2_foundational_meditation_sample-1`
   - 选择不同的episode，比如 `1-1_introduction`
   - 点击 "✓ Switch Episode" 按钮
   - GUI应该重新加载，显示新episode的数据

## 预期结果

### Collection下拉列表应该包含:
- awake_where_you_are_english ✓ (正确的collection)
- 可能还有其他temp/下的目录（如果有的话）

### Episode下拉列表应该包含 (当选择awake_where_you_are_english时):
- 1-1_introduction
- 1-2_foundational_meditation  
- 1-2_foundational_meditation_sample-1
- test_sample_types_of_medidation

### 关键变更总结

**修复的问题**: 
- 之前 `temp_dir` 指向 collection 层级，导致Collection列表显示的是episodes
- 现在 `temp_dir` 正确指向 `temp/` 目录

**路径层级**:
```
temp/                                    ← temp_dir (4层parent)
└── awake_where_you_are_english/        ← collection (3层parent)
    └── 1-2_foundational_meditation_sample-1/  ← episode (2层parent)
        └── translations/                ← (1层parent)
            └── xxx.json                 ← translation_file
```

**命名更改**:
- "Project" → "Episode" (所有GUI显示)
- Collection = 项目集合 (如 awake_where_you_are_english)
- Episode = 具体章节 (如 1-1_introduction)
