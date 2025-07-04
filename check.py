#!/usr/bin/env python3
import re, sys, argparse

YELLOW_BOLD = '\033[1;93m'
YELLOW      = '\033[93m'
CYAN        = '\033[1;96m'
RED_BOLD    = '\033[1;91m'
RESET       = '\033[0m'

bad_char_pattern = re.compile(r'[\u3000-\u303F\uFF00-\uFFEF\u4E00-\u9FFF]')

def highlight_bad_chars(text):
    return ''.join(
        c if not bad_char_pattern.match(c)
        else f'{RED_BOLD}{c}{RESET}'
        for c in text
    )

def strip_text_commands(s: str) -> str:
    return re.sub(r'\\text\{.*?\}', '', s)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('texfile', help="Path to the .tex file")
    parser.add_argument('-t', '--check-text',
                        action='store_true',
                        help="check contents in \\text{}")
    args = parser.parse_args()

    try:
        with open(args.texfile, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Can't find file {args.texfile}")
        sys.exit(1)

    math_envs = [
        'equation', 'equation*',
        'align',    'align*',
        'gather',   'gather*',
        'multline','multiline*',
        'cases'
    ]

    in_math_block = False
    env_name      = ''
    start_line    = 0
    math_block    = []
    end_pattern   = None

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        if not in_math_block:
            m1 = re.match(r'\$\$(.*?)\$\$', stripped, flags=re.DOTALL)
            if m1:
                content = m1.group(1)
                to_check = content if args.check_text else strip_text_commands(content)
                if bad_char_pattern.search(to_check):
                    print(
                        f"[{CYAN}$${RESET}] "
                        f"{YELLOW}lines {YELLOW_BOLD}{i}-{i}{RESET}{YELLOW} contain bad character(s):{RESET}"
                    )
                    print(highlight_bad_chars(to_check))
                continue

            m2 = re.match(r'\\\[(.*?)\\\]', stripped, flags=re.DOTALL)
            if m2:
                content = m2.group(1)
                to_check = content if args.check_text else strip_text_commands(content)
                if bad_char_pattern.search(to_check):
                    print(
                        f"[{CYAN}\\[{RESET}] "
                        f"{YELLOW}lines {YELLOW_BOLD}{i}-{i}{RESET}{YELLOW} contain bad character(s):{RESET}"
                    )
                    print(highlight_bad_chars(to_check))
                continue

            m3 = re.match(r'\\\((.*?)\\\)', stripped, flags=re.DOTALL)
            if m3:
                content = m3.group(1)
                to_check = content if args.check_text else strip_text_commands(content)
                if bad_char_pattern.search(to_check):
                    print(
                        f"[{CYAN}\\({RESET}] "
                        f"{YELLOW}lines {YELLOW_BOLD}{i}-{i}{RESET}{YELLOW} contain bad character(s):{RESET}"
                    )
                    print(highlight_bad_chars(to_check))
                continue

        m_begin = re.match(r'\\begin\{(\w+\*?)\}', stripped)
        if m_begin and m_begin.group(1) in math_envs:
            in_math_block = True
            env_name      = m_begin.group(1)
            start_line    = i
            math_block    = [line]
            end_pattern   = re.compile(rf'\\end\{{{re.escape(env_name)}\}}')
            continue

        if not in_math_block:
            if stripped.startswith('$$'):
                in_math_block = True
                env_name      = '$$'
                start_line    = i
                math_block    = [line]
                end_pattern   = re.compile(r'\$\$')
                continue
            if stripped.startswith('\\['):
                in_math_block = True
                env_name      = '\\['
                start_line    = i
                math_block    = [line]
                end_pattern   = re.compile(r'\\\]')
                continue
            if stripped.startswith('\\('):
                in_math_block = True
                env_name      = '\\('
                start_line    = i
                math_block    = [line]
                end_pattern   = re.compile(r'\\\)')
                continue

        if in_math_block:
            math_block.append(line)
            if end_pattern.search(stripped):
                in_math_block = False
                content = ''.join(math_block)
                to_check = content if args.check_text else strip_text_commands(content)
                if bad_char_pattern.search(to_check):
                    print(
                        f"[{CYAN}{env_name}{RESET}] "
                        f"{YELLOW}lines {YELLOW_BOLD}{start_line}-{i}{RESET}{YELLOW} contain bad character(s):{RESET}"
                    )
                    print(highlight_bad_chars(to_check))
                math_block = []
            continue

        def scan_inline(pattern, label):
            for m in re.findall(pattern, line, flags=re.DOTALL):
                to_check = m if args.check_text else strip_text_commands(m)
                if bad_char_pattern.search(to_check):
                    print(
                        f"[{CYAN}{label}{RESET}] "
                        f"{YELLOW}line {YELLOW_BOLD}{i}{RESET}{YELLOW}:{RESET}"
                        f"{highlight_bad_chars(to_check)}"
                    )

        scan_inline(r'\$([^$]+)\$',      "Inline $")
        scan_inline(r'\\\((.*?)\\\)',    "\\( \\)")
        scan_inline(r'\\\[(.*?)\\\]',    "\\[ \\]")

if __name__ == '__main__':
    main()
