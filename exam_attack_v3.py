# exam_attack_v3.py

import os
import subprocess
import re
import shutil

def get_preamble_code(attack_params: dict) -> str:
    """Generates LaTeX code for the preamble based on the attack type."""
    attack_type = attack_params.get('type', 'none')
    params = attack_params.get('params', {})
    code = ""

    dimension_setup = r"""
\usepackage{layouts}
\usepackage{atbegshi}

\newlength\pgwidth
\newlength\pgheight
\AtBeginDocument{%
  \pgwidth=\paperwidth
  \pgheight=\paperheight
}
"""

    if attack_type in ['watermark_tiled', 'texture']:
        code += dimension_setup

    if attack_type == 'watermark':
        text = params.get('text', 'EXAM COPY')
        color = params.get('color', 'gray!10')
        angle = params.get('angle', 45)
        size = params.get('size', 5)
        code += fr"""
\usepackage{{eso-pic}}
\AddToShipoutPictureBG{{%
  \AtPageCenter{{%
    \rotatebox{{{angle}}}{{%
      \scalebox{{{size}}}{{%
        \textcolor{{{color}}}{{{text}}}%
      }}%
    }}%
  }}%
}}
"""

    elif attack_type == 'watermark_tiled':
        text = params.get('text', 'WATERMARK')
        color = params.get('color', 'gray!12')
        size = params.get('size', 8)
        angle = params.get('angle', 30)
        x_step = params.get('x_step', 5)
        y_step = params.get('y_step', 4)
        code += fr"""
\AddToShipoutPictureBG{{%
  \begin{{tikzpicture}}[remember picture, overlay]
    \foreach \x in {{1,{x_step+1},...,20}} {{
      \foreach \y in {{1,{y_step+1},...,28}} {{
        \node[rotate={angle}, color={color}, anchor=center] at (\x cm, \y cm) {{\fontsize{{{size}}}{{{size+2}}}\selectfont ${text}$}};
      }}
    }}
  \end{{tikzpicture}}%
}}
"""
    elif attack_type == 'texture':
        pattern = params.get('pattern', 'dots')
        density = params.get('density', 0.7)
        color = params.get('color', 'gray!10')
        step = 2.0 / density if density > 0 else 2.0
        if pattern == 'dots':
            code += fr"""
\AddToShipoutPictureBG{{%
  \begin{{tikzpicture}}[remember picture, overlay]
    \foreach \x in {{0,{step},...,20}} {{
      \foreach \y in {{0,{step},...,28}} {{
        \node[circle, fill={color}, inner sep=0.2pt] at (\x cm, \y cm) {{}};
      }}
    }}
  \end{{tikzpicture}}%
}}"""
        elif pattern == 'lines':
            code += fr"""
\AddToShipoutPictureBG{{%
  \begin{{tikzpicture}}[remember picture, overlay]
    \foreach \x in {{0,{step},...,20}} {{\draw[{color}, thin] (\x,0) -- (\x,28);}}
    \foreach \y in {{0,{step},...,28}} {{\draw[{color}, thin] (0,\y) -- (20,\y);}}
  \end{{tikzpicture}}%
}}"""
        elif pattern == 'wave':
            code += fr"""
\AddToShipoutPictureBG{{%
  \begin{{tikzpicture}}[remember picture, overlay]
    \foreach \i in {{0,1,...,20}} {{
      \draw[{color}, thin] plot[domain=0:20, samples=100, smooth] (\x, {{\i*{step} + 0.1*sin(90*\x)}});
    }}
  \end{{tikzpicture}}%
}}"""

    elif attack_type == 'font_swap':
        font_name = params.get('font_name', 'Comic Sans MS')
        symbol = params.get('symbol_to_swap', '+')
        safe_name = ''.join(c for c in symbol if c.isalnum())
        if not safe_name:
            safe_name = "weirdsymbol"
        command_name = f"\\weird{safe_name}"
        code = fr"""
\RequirePackage{{fontspec}}
\newfontfamily\weirdfont{{{font_name}}}[Scale=1.0]
\newcommand{{{command_name}}}{{{{\\weirdfont {symbol}}}}}
"""
    return code

def modify_body_content(content: str, attack_params: dict) -> str:
    """Modifies the body of the LaTeX document for certain attacks."""
    attack_type = attack_params.get('type', 'none')
    params = attack_params.get('params', {})

    if attack_type == 'kerning':
        amount = params.get('amount', -0.05)
        if 'target' in params:
            target = params['target']
            mathPattern = f"${re.escape(target)}$"
            replacement = f"${target}\\mkern{{{amount}}}em$"
            return content.replace(mathPattern, replacement)
        return content

    if attack_type == 'symbol_stretch':
        stretch_amount = params.get('stretch_amount', 1.5)
        if 'target' in params:
            target = params['target']
            replacement = f"\\scalebox{{{stretch_amount}}}[1]{{{target}}}"
            return content.replace(target, replacement)
        return content

    if attack_type == 'font_swap':
        symbol = params.get('symbol_to_swap', '+')
        safe_name = ''.join(c for c in symbol if c.isalnum())
        if not safe_name:
            safe_name = "weirdsymbol"
        command_name = f"\\weird{safe_name}"
        return content.replace(symbol, command_name)

    if attack_type == 'homoglyph':
        substitutions = {
            'a': 'а', 'e': 'е', 'o': 'о', 'c': 'с', # Cyrillic
            'l': 'I', 'I': 'l',
        }
        target_word = params.get('target', '')
        if target_word:
            new_word = ""
            for char in target_word:
                new_word += substitutions.get(char, char)
            return content.replace(target_word, new_word)
        return content

    if attack_type == 'ligature':
        # Disrupt common ligatures by inserting a zero-width non-joiner.
        target_word = params.get('target', '')
        if target_word:
            # Using a simple but effective method of breaking ligatures
            replacement = target_word.replace('fi', 'f{{\\kern0pt}}i').replace('fl', 'f{{\\kern0pt}}l')
            return content.replace(target_word, replacement)
        return content

    if attack_type == 'low_contrast':
        target_word = params.get('target', '')
        color = params.get('color', 'gray!80')
        if target_word:
            replacement = f"\\textcolor{{{color}}}{{{target_word}}}"
            return content.replace(target_word, replacement)
        return content

    return content

def create_exam_variant(template_path: str, output_name: str, attack_params: dict) -> str | None:
    """Creates and compiles a modified LaTeX exam with specified attack parameters."""
    with open(template_path, 'r') as f:
        template_content = f.read()

    preamble_mods = ""
    modified_content = template_content
    attack_type = attack_params.get('type', 'none')

    if attack_type == 'combo':
        params = attack_params.get('params', {})
        sub_attacks = params.get('sub_attacks', [])
        for sub_attack in sub_attacks:
            if sub_attack.get('type') == 'texture' and 'watermark_tiled' in [a.get('type') for a in sub_attacks]:
                preamble_code = get_preamble_code(sub_attack)
                if '\\usepackage{layouts}' in preamble_code and '\\usepackage{layouts}' in preamble_mods:
                    setup_end = preamble_code.find('\\AddToShipoutPictureBG')
                    if setup_end > 0:
                        preamble_mods += preamble_code[setup_end:]
                else:
                    preamble_mods += preamble_code
            else:
                preamble_mods += get_preamble_code(sub_attack)
        for sub_attack in sub_attacks:
            modified_content = modify_body_content(modified_content, sub_attack)
    else:
        preamble_mods = get_preamble_code(attack_params)
        modified_content = modify_body_content(modified_content, attack_params)

    final_content = modified_content.replace('%%WATERMARK_AREA%%', preamble_mods)
    final_content = final_content.replace('%%TRAP_QUESTION_AREA%%', '')

    variant_tex_path = f"{output_name}.tex"
    with open(variant_tex_path, 'w') as f:
        f.write(final_content)

    print(f"Generated {variant_tex_path}. Compiling...")
    # Use shutil.which to find lualatex in PATH, with fallback to common locations
    lualatex_path = shutil.which('lualatex') or '/usr/local/texlive/2025/bin/universal-darwin/lualatex'
    if not os.path.exists(lualatex_path):
        print(f"Warning: LuaLaTeX not found at {lualatex_path}. Compilation may fail.")
    
    process = subprocess.run(
        [lualatex_path, '-interaction=nonstopmode', variant_tex_path],
        capture_output=True, text=True
    )

    if process.returncode == 0:
        print(f"Successfully compiled {output_name}.pdf")
        return f"{output_name}.pdf"
    else:
        print(f"!!!!!! Error compiling {variant_tex_path}. !!!!!!")
        
        # Save full error log to file for later inspection
        error_log_file = f"{output_name}_error.log"
        with open(error_log_file, 'w') as f:
            f.write(process.stderr)
        
        # Print summary of error for immediate feedback
        print(f"Full error log saved to {error_log_file}")
        
        # Find common LaTeX errors
        common_errors = ["Undefined control sequence", "Missing", "File not found", "Emergency stop"]
        for error in common_errors:
            if error in process.stderr:
                print(f"Found error type: {error}")
                # Find the line containing this error and a few lines around it
                error_index = process.stderr.find(error)
                context_start = max(0, process.stderr.rfind('\n', 0, error_index - 100))
                context_end = min(len(process.stderr), process.stderr.find('\n', error_index + 100))
                print(process.stderr[context_start:context_end])
                break
        else:
            # If no common errors found, print the last 500 characters
            print("Error Log (last part):", process.stderr[-500:])
            
        return None
