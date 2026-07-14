# GitHub Action Markdown 翻译

将待翻译的 Markdown 放在 `src/`。工作流会保留源文件的子目录结构，并生成：

```text
src/             # 源文件，只放单语言 Markdown
output/
  en/            # 英文版
  zh/            # 中文版
  bilingual/     # 中英双语版
```

例如 `src/guides/start.md` 会生成：

- 中文源文件：原文复制到 `output/zh/guides/start.md`，英文翻译写入
  `output/en/guides/start.md`，并生成 `output/bilingual/guides/start.md`。
- 英文源文件：原文复制到 `output/en/guides/start.md`，中文翻译写入
  `output/zh/guides/start.md`，并生成 `output/bilingual/guides/start.md`。

源文件只应放入 `src/`，不要放入双语版；脚本会自动检测英文或中文。

本地运行前设置 `OPENAI_API_KEY`，然后执行：

```zsh
python .github/scripts/translate.py src/your-file.md
```
