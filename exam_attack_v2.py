# exam_attack_v2.py

import os
import subprocess
import re

def get_preamble_code(attack_params: dict) -> str:
    """Generates LaTeX code for the preamble based on the attack type."""
    attack_type = attack_params.get('type', 'none')
    params = attack_params.get('params', {})
    code = ""

    # This preamble code will be added for any attack needing page dimensions
    dimension_setup = """
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
        # Generate watermark in the background of the document
        text = params.get('text', 'EXAM COPY')
        color = params.get('color', 'gray!10')
        angle = params.get('angle', 45)
        size = params.get('size', 5)
        
        code += f"""
\usepackage{eso-pic}
\AddToShipoutPictureBG{%
  \AtPageCenter{%
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
        code += f"""
\AddToShipoutPictureBG{%
  \begin{tikzpicture}[remember picture, overlay]
    % Fixed loop to use fixed steps instead of calculated dimensions
    \foreach \x in {{1,{{1+x_step}},...,20}} {{
      \foreach \y in {{1,{{1+y_step}},...,28}} {{
        \node[rotate={angle}, color={color}, anchor=center] at (\x cm, \y cm) {{\fontsize{{{size}}}{{{size+2}}}\selectfont ${text}$}};
      }}
    }}
  \end{tikzpicture}%
}}
"""
    elif attack_type == 'texture':
        pattern = params.get('pattern', 'dots')
        density = params.get('density', 0.7)
        color = params.get('color', 'gray!10')
        step = 2.0 / density if density > 0 else 2.0

        if pattern == 'dots':
            code += f"""
\AddToShipoutPictureBG{%
  \begin{tikzpicture}[remember picture, overlay]
    \foreach \x in {{0,{{step}},...,20}} {{
      \foreach \y in {{0,{{step}},...,28}} {{
        \node[circle, fill={color}, inner sep=0.2pt] at (\x cm, \y cm) {{}};
      }}
    }}
  \end{tikzpicture}%
}}"""
        elif pattern == 'lines':
            code += f"""
\AddToShipoutPictureBG{%
  \begin{tikzpicture}[remember picture, overlay]
    \foreach \x in {{0,{{step}},...,20}} {{\draw[{color}, thin] (\x,0) -- (\x,28);}}
    \foreach \y in {{0,{{step}},...,28}} {{\draw[{color}, thin] (0,\y) -- (20,\y);}}
  \end{tikzpicture}%
}}"""
        elif pattern == 'wave':
            # Simplified wave pattern to avoid calculation errors
            code += f"""
\AddToShipoutPictureBG{%
  \begin{tikzpicture}[remember picture, overlay]
    \foreach \i in {{0,1,...,20}} {{
      \draw[{color}, thin] 
        plot[domain=0:20, samples=100, smooth] 
        (\x, {{\i*{step} + 0.1*sin(\x*90)}});
    }}
  \end{tikzpicture}%
}}"""

    elif attack_type == 'font_swap':
        font_name = params.get('font_name', 'Comic Sans MS')
        symbol = params.get('symbol_to_swap', '+')
        safe_name = ''.join(c for c in symbol if c.isalnum())
        if not safe_name:
            safe_name = "weirdsymbol"
        command_name = f"\\weird{safe_name}"
        
        code = f"""
% Ensure fontspec is loaded with proper options
\RequirePackage{{fontspec}}
\newfontfamily\weirdfont{{{font_name}}}[Scale=1.0]
\newcommand{{{command_name}}}{{{{\weirdfont {symbol}}}}}
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
            # For LaTeX math expressions, insert kerning at specific places instead
            # of between every character which could break the math
            
            # Replace the target in math mode with a kerned version
            mathPattern = f"${re.escape(target)}$"
            replacement = f"${target}\\mkern{{amount}}em$"
            
            # Apply replacement
            return content.replace(mathPattern, replacement)
        return content

    if attack_type == 'symbol_stretch':
        stretch_amount = params.get('stretch_amount', 1.5)
        if 'target' in params:
            target = params['target']
            # Replace the target symbol with a stretched version
            replacement = f"\\scalebox{{{stretch_amount}}[1]}{{{target}}}"
            return content.replace(target, replacement)
        return content

    if attack_type == 'font_swap':
        symbol = params.get('symbol_to_swap', '+')
        # Generate a simple command name with no special chars
        safe_name = ''.join(c for c in symbol if c.isalnum())
        if not safe_name:  # If the symbol has no alphanumeric chars
            safe_name = "weirdsymbol"
        command_name = f"\\weird{safe_name}"
        
        # Simple string replace is more reliable here
        return content.replace(symbol, command_name)

    return content

def create_exam_variant(template_path: str, output_name: str, attack_params: dict) -> str | None:
    """Creates and compiles a modified LaTeX exam with specified attack parameters."""
    with open(template_path, 'r') as f:
        template_content = f.read()

    preamble_mods = ""
    modified_content = template_content
    attack_type = attack_params.get('type', 'none')

    if attack_type == 'combo':
        # For combo attacks, be more careful with order and how we apply attacks
        params = attack_params.get('params', {})
        sub_attacks = params.get('sub_attacks', [])
        
        # Special handling - first add all preambles
        for sub_attack in sub_attacks:
            # Don't double-add dimension setup
            if sub_attack.get('type') == 'texture' and 'watermark_tiled' in [a.get('type') for a in sub_attacks]:
                # Special handling for texture + watermark combo - strip duplicate dimension setup
                preamble_code = get_preamble_code(sub_attack)
                if '\\usepackage{layouts}' in preamble_code and '\\usepackage{layouts}' in preamble_mods:
                    # Strip out the dimension setup part
                    setup_end = preamble_code.find('\\AddToShipoutPictureBG')
                    if setup_end > 0:
                        preamble_mods += preamble_code[setup_end:]
                else:
                    preamble_mods += preamble_code
            else:
                preamble_mods += get_preamble_code(sub_attack)
        
        # Then apply all body modifications
        for sub_attack in sub_attacks:
            modified_content = modify_body_content(modified_content, sub_attack)
    else:
        # For single attacks
        preamble_mods = get_preamble_code(attack_params)
        modified_content = modify_body_content(modified_content, attack_params)

    # Apply the modifications to the template
    final_content = modified_content.replace('%%WATERMARK_AREA%%', preamble_mods)
    final_content = final_content.replace('%%TRAP_QUESTION_AREA%%', '') # Not using trap questions for now

    variant_tex_path = f"{output_name}.tex"
    with open(variant_tex_path, 'w') as f:
        f.write(final_content)

    print(f"Generated {variant_tex_path}. Compiling...")
    # Make sure to use lualatex or xelatex for fontspec compatibility
    process = subprocess.run(
        ['/usr/local/texlive/2025/bin/universal-darwin/lualatex', '-interaction=nonstopmode', variant_tex_path],
        capture_output=True, text=True
    )

    if process.returncode == 0:
        print(f"Successfully compiled {output_name}.pdf")
        return f"{output_name}.pdf"
    else:
        print(f"!!!!!! Error compiling {variant_tex_path}. !!!!!!")
        print("Error Log:", process.stderr[-500:]) # Print last part of stderr
        return None
