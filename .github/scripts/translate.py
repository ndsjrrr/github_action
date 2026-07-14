#!/usr/bin/env python3
"""
Markdown 自动翻译脚本
检测语言 → 翻译 → 生成双语版
文件映射: xxx.md → xxx.{en|zh|bilingual}.md

本地测试:
  OPENAI_API_KEY=sk-xxx python .github/scripts/translate.py README.md
"""
import os
import re
import shutil
import sys
import time
import requests

MAX_FILE_SIZE = 100_000  # 超过 100KB 跳过，防 token 爆炸
MAX_RETRIES = 3
RETRY_DELAY = 5
SOURCE_DIR = 'src'
OUTPUT_DIRS = {
    'en': os.path.join('output', 'en'),
    'zh': os.path.join('output', 'zh'),
    'bilingual': os.path.join('output', 'bilingual'),
}


# ======================== 语言检测 ========================

def detect_language(content: str) -> str:
    """统计中文字符和英文单词，判断主语言。"""
    zh_count = len(re.findall(r'[\u4e00-\u9fff]', content))
    en_count = len(re.findall(r"\b[a-zA-Z]+(?:[-'][a-zA-Z]+)*\b", content))
    if zh_count == 0 and en_count == 0:
        return 'en'
    return 'zh' if zh_count > en_count else 'en'


# ======================== OpenAI 调用 ========================

def call_openai(system_prompt: str, user_content: str,
                api_key: str, model: str) -> str:
    """调用 OpenAI Chat Completion，带重试"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_content},
        ],
        'temperature': 0.2,
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers, json=payload, timeout=120,
            )
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                print(f"    API 失败，{RETRY_DELAY}s 后重试 "
                      f"({attempt + 1}/{MAX_RETRIES}): {e}")
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(
                    f"OpenAI API 连续 {MAX_RETRIES} 次失败: {e}"
                ) from e


# ======================== 翻译 ========================

def translate(content: str, target_lang: str,
              api_key: str, model: str) -> str:
    """纯翻译，保留 Markdown 格式"""
    lang_name = {'zh': '简体中文', 'en': 'English'}[target_lang]
    system_prompt = (
        f"你是一个专业的技术文档翻译员。"
        f"请将以下 Markdown 内容翻译为{lang_name}。\n"
        "规则：\n"
        "1. 严格保留所有 Markdown 语法（标题#、列表-/*、代码块```、"
        "表格|、链接[]()、图片![]()等）\n"
        "2. 代码块内的内容不翻译\n"
        "3. 专有名词、包名、命令、URL 保持原样\n"
        "4. 不要添加任何解释、注释或前后缀\n"
        "5. 只输出翻译结果"
    )
    return call_openai(system_prompt, content, api_key, model)


# ======================== 双语交替 ========================

def generate_bilingual(content: str, source_lang: str,
                       api_key: str, model: str) -> str:
    """生成中英双语交替版本"""
    lang_name = {'zh': '简体中文', 'en': 'English'}[source_lang]
    system_prompt = (
        f"你是一个专业的技术文档翻译员。"
        f"请将以下{lang_name} Markdown 内容生成为中英双语交替版本。\n"
        "格式规则：\n"
        "1. 每个元素（标题/段落/列表项/表格行）后紧跟其翻译，"
        "中间用空行分隔\n"
        "2. 标题翻译保持相同的 # 级别\n"
        "3. 列表项翻译保持相同的缩进和符号（- 或 * 或 数字.）\n"
        "4. 代码块不翻译，只保留一份（放在相关段落之后）\n"
        "5. 图片、链接、表格结构保持原样，仅翻译文字部分\n"
        "6. 专有名词、包名、命令保持原样\n"
        "7. 不要添加任何解释或注释\n"
        "8. 只输出结果\n\n"
        "示例（中文源）：\n"
        "# 安装指南\n"
        "\n"
        "# Installation Guide\n"
        "\n"
        "请先安装 Node.js。\n"
        "\n"
        "Please install Node.js first.\n"
        "\n"
        "```bash\n"
        "npm install\n"
        "```\n"
        "\n"
        "- 支持 macOS\n"
        "\n"
        "- Supports macOS"
    )
    return call_openai(system_prompt, content, api_key, model)


# ======================== 单文件处理 ========================

def output_path(filepath: str, language: str) -> str:
    """将 src 下的文件映射到指定输出目录，并保留子目录结构。"""
    source_root = os.path.abspath(SOURCE_DIR)
    absolute_path = os.path.abspath(filepath)
    if os.path.commonpath([source_root, absolute_path]) != source_root:
        raise ValueError(f"源文件必须位于 {SOURCE_DIR}/: {filepath}")

    relative_path = os.path.relpath(absolute_path, source_root)
    return os.path.join(OUTPUT_DIRS[language], relative_path)


def process_file(filepath: str, api_key: str, model: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"处理: {filepath}")

    file_size = os.path.getsize(filepath)
    if file_size > MAX_FILE_SIZE:
        print(f"  ⚠ 跳过: {file_size} 字节，超过 {MAX_FILE_SIZE} 限制")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.strip():
        print("  ⚠ 跳过: 文件为空")
        return

    source_lang = detect_language(content)
    print(f"  检测语言: { {'zh': '中文', 'en': '英文'}[source_lang] }")

    source_copy_file = output_path(filepath, source_lang)
    bilingual_file = output_path(filepath, 'bilingual')

    if source_lang == 'zh':
        translated_file = output_path(filepath, 'en')
        target_lang, target_label = 'en', '英文'
    else:
        translated_file = output_path(filepath, 'zh')
        target_lang, target_label = 'zh', '中文'

    # 原文副本：让 en / zh / bilingual 三个输出目录始终对应同一个源文件。
    print(f"  复制原文: {source_copy_file}")
    os.makedirs(os.path.dirname(source_copy_file), exist_ok=True)
    shutil.copyfile(filepath, source_copy_file)

    # 翻译
    print(f"  翻译为{target_label}: {translated_file}")
    translated = translate(content, target_lang, api_key, model)
    os.makedirs(os.path.dirname(translated_file), exist_ok=True)
    with open(translated_file, 'w', encoding='utf-8') as f:
        f.write(translated)
    print(f"  ✓ {translated_file}")

    # 双语
    print(f"  生成双语版: {bilingual_file}")
    bilingual = generate_bilingual(content, source_lang, api_key, model)
    os.makedirs(os.path.dirname(bilingual_file), exist_ok=True)
    with open(bilingual_file, 'w', encoding='utf-8') as f:
        f.write(bilingual)
    print(f"  ✓ {bilingual_file}")


# ======================== 入口 ========================

def main():
    if len(sys.argv) < 2:
        print("用法: python translate.py <file1.md> [file2.md] ...")
        print("  或: git diff -z --name-only ... | python translate.py --stdin0")
        sys.exit(1)

    if sys.argv[1:] == ['--stdin0']:
        files = [
            fp.decode('utf-8') for fp in sys.stdin.buffer.read().split(b'\0')
            if fp
        ]
    else:
        files = sys.argv[1:]

    source_files = [
        fp for fp in files
        if fp.endswith('.md')
        and fp.startswith(f'{SOURCE_DIR}{os.sep}')
    ]

    if not source_files:
        print("没有需要翻译的源 Markdown 文件")
        return

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("错误: 未设置 OPENAI_API_KEY 环境变量")
        sys.exit(1)

    model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    print(f"模型: {model}")

    ok, fail = 0, 0
    for fp in source_files:
        try:
            process_file(fp, api_key, model)
            ok += 1
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            fail += 1

    print(f"\n{'=' * 60}")
    print(f"完成: {ok} 成功, {fail} 失败")
    if fail:
        sys.exit(1)


if __name__ == '__main__':
    main()
