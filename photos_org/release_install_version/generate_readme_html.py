#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
README.md to HTML Converter
将README.md转换为HTML页面，用于安装后的用户指南显示
"""

import os
import sys
from pathlib import Path

def convert_markdown_to_html(markdown_content):
    """Convert markdown content to HTML"""
    lines = markdown_content.split('\n')
    html_lines = []
    in_code_block = False
    code_language = ''

    for line in lines:
        # Handle code blocks
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_language = line.strip()[3:]
                html_lines.append('<pre><code class="language-' + code_language + '">')
            else:
                in_code_block = False
                html_lines.append('</code></pre>')
            continue

        if in_code_block:
            # Escape HTML entities in code blocks
            line = (line.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))
            html_lines.append(line)
            continue

        # Handle headers
        if line.startswith('# '):
            html_lines.append(f'<h1>{line[2:].strip()}</h1>')
        elif line.startswith('## '):
            html_lines.append(f'<h2>{line[3:].strip()}</h2>')
        elif line.startswith('### '):
            html_lines.append(f'<h3>{line[4:].strip()}</h3>')
        elif line.startswith('#### '):
            html_lines.append(f'<h4>{line[5:].strip()}</h4>')

        # Handle lists
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            html_lines.append(f'<li>{line.strip()[2:].strip()}</li>')

        # Handle bold text
        elif '**' in line:
            line = line.replace('**', '<strong>', 1)
            line = line.replace('**', '</strong>', 1)
            html_lines.append(f'<p>{line.strip()}</p>')

        # Handle links
        elif '[' in line and ']' in line and '(' in line and ')' in line:
            # Simple link conversion
            line = line.replace('[', '<a href="').replace(']', '">')
            line = line.replace('(', '').replace(')', '</a>')
            html_lines.append(f'<p>{line.strip()}</p>')

        # Handle empty lines
        elif line.strip() == '':
            html_lines.append('')

        # Handle regular paragraphs
        else:
            if line.strip():
                html_lines.append(f'<p>{line.strip()}</p>')

    return '\n'.join(html_lines)

def generate_html_page(markdown_content, output_path):
    """Generate complete HTML page"""

    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能照片系统 - 使用指南</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px 30px;
        }}

        h1 {{
            color: #1f2937;
            font-size: 2rem;
            margin: 2rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #e5e7eb;
        }}

        h2 {{
            color: #374151;
            font-size: 1.5rem;
            margin: 1.5rem 0 1rem 0;
            padding-left: 1rem;
            border-left: 4px solid #4f46e5;
        }}

        h3 {{
            color: #4b5563;
            font-size: 1.25rem;
            margin: 1.25rem 0 0.75rem 0;
        }}

        h4 {{
            color: #6b7280;
            font-size: 1.1rem;
            margin: 1rem 0 0.5rem 0;
        }}

        p {{
            margin-bottom: 1rem;
            line-height: 1.7;
        }}

        ul, ol {{
            margin: 1rem 0;
            padding-left: 2rem;
        }}

        li {{
            margin-bottom: 0.5rem;
        }}

        .highlight {{
            background: #f3f4f6;
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 4px solid #4f46e5;
            margin: 1.5rem 0;
        }}

        .highlight h3 {{
            margin-top: 0;
            color: #1f2937;
        }}

        code {{
            background: #f1f5f9;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
        }}

        pre {{
            background: #1f2937;
            color: #f9fafb;
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
        }}

        pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}

        a {{
            color: #4f46e5;
            text-decoration: none;
            transition: color 0.3s ease;
        }}

        a:hover {{
            color: #7c3aed;
            text-decoration: underline;
        }}

        .footer {{
            text-align: center;
            padding: 30px;
            background: #f9fafb;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
        }}

        .emoji {{
            font-size: 1.2em;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}

            .header {{
                padding: 30px 20px;
            }}

            .header h1 {{
                font-size: 2rem;
            }}

            .content {{
                padding: 30px 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 智能照片系统</h1>
            <p>让家庭回忆永不丢失</p>
        </div>

        <div class="content">
            {content}
        </div>

        <div class="footer">
            <p>🎉 安装成功！现在您可以开始使用智能照片系统了</p>
            <p>如有问题，请查看上面的使用指南或联系技术支持</p>
        </div>
    </div>
</body>
</html>"""

    # Convert markdown to HTML
    html_content = convert_markdown_to_html(markdown_content)

    # Generate complete HTML page
    complete_html = html_template.format(content=html_content)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(complete_html)

    print(f"✅ HTML file generated: {output_path}")

def main():
    """Main function"""
    # Get script directory
    script_dir = Path(__file__).parent

    # Input README.md path (from current directory)
    readme_path = script_dir / 'README.md'
    output_path = script_dir / 'README.html'

    try:
        # Read README.md
        with open(readme_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Generate HTML
        generate_html_page(markdown_content, output_path)

        print(f"🎉 README.html generated successfully!")
        print(f"📁 Location: {output_path}")

    except FileNotFoundError:
        print(f"❌ Error: README.md not found at {readme_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating HTML: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
