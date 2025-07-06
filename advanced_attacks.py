#!/usr/bin/env python3
# advanced_attacks.py
#
# This module implements advanced attack techniques that go beyond
# the basic watermark/texture/kerning attacks

import re
from typing import Dict, Any, List, Tuple, Optional

def get_advanced_preamble_code(attack_params: Dict[str, Any]) -> str:
    """Generate advanced attack preamble code"""
    attack_type = attack_params.get("type", "none")
    params = attack_params.get("params", {})
    code = ""
    
    if attack_type == "math_font_mixing":
        # Use different math fonts for different parts of equations
        primary_font = params.get("primary_font", "Latin Modern Math")
        secondary_font = params.get("secondary_font", "STIX Two Math")
        tertiary_font = params.get("tertiary_font", "Asana Math")
        operators = params.get("operators", True)
        letters = params.get("letters", True)
        numbers = params.get("numbers", False)
        
        code += """
% Math font mixing attack
\\usepackage{unicode-math}
\\setmathfont{Latin Modern Math}
"""
        
        if operators:
            code += f"\\setmathfont[range={{\\mathrel,\\mathbin}}]{{{secondary_font}}}\n"
        
        if letters:
            code += f"\\setmathfont[range={{Latin,latin}}]{{{secondary_font}}}\n"
            
        if numbers:
            code += f"\\setmathfont[range={{\"0\"-\"9\"}}]{{{tertiary_font}}}\n"
    
    elif attack_type == "custom_environment_targeting":
        # Target specific environments like matrices, tables
        target_env = params.get("target_env", "matrix")
        color = params.get("color", "gray!15")
        
        code += f"""
% Environment targeting attack
\\usepackage{{etoolbox}}
\\AtBeginEnvironment{{{target_env}}}{{%
  \\colorlet{{oldcolor}}{{.}}%
  \\color{{{color}}}%
}}
\\AtEndEnvironment{{{target_env}}}{{%
  \\color{{oldcolor}}%
}}
"""
    
    elif attack_type == "symbol_confusion":
        # Replace math symbols with visually similar but different ones
        code += """
% Symbol confusion attack
\\usepackage{amsmath}
\\usepackage{amssymb}
\\let\\originalequals=\\=
\\renewcommand{\\=}{\\dot=}

% Confuse minus and en-dash
\\let\\originalminus=\\-
\\renewcommand{\\-}{\\text{--}}

% Confuse multiplication
\\let\\originaltimes=\\times
\\renewcommand{\\times}{\\ast}
"""
    
    elif attack_type == "adversarial_spacing":
        # Add irregular spacing in equations
        intensity = params.get("intensity", "medium")
        
        space_map = {
            "low": "0.1em",
            "medium": "0.2em",
            "high": "0.4em"
        }
        space_amt = space_map.get(intensity, "0.2em")
        
        code += f"""
% Adversarial spacing attack
\\usepackage{{amsmath}}
\\usepackage{{etoolbox}}

% Add irregular spacing in equations
\\everymath{{\\addtolength{{\\jot}}{{0.2em}}}}
\\AtBeginEnvironment{{equation}}{{\\thickmuskip={space_amt}\\medmuskip={space_amt}}}
\\AtBeginEnvironment{{align}}{{\\thickmuskip={space_amt}\\medmuskip={space_amt}}}
"""
    
    elif attack_type == "visual_noise_injection":
        # Add visual noise to the document that's hard for AI but okay for humans
        intensity = params.get("intensity", "medium")
        pattern = params.get("pattern", "dots")
        color = params.get("color", "gray!10")
        
        # Scale noise intensity
        noise_scale = {
            "low": 0.5,
            "medium": 1.0,
            "high": 2.0
        }.get(intensity, 1.0)
        
        if pattern == "dots":
            step = 1.0 / noise_scale
            code += f"""
% Visual noise injection
\\usepackage{{tikz}}
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    % Add random noise dots
    \\foreach \\i in {{1,...,100}} {{
      \\pgfmathsetmacro{{\\x}}{{rand*20}}
      \\pgfmathsetmacro{{\\y}}{{rand*28}}
      \\node[circle, fill={color}, inner sep=0.1pt] at (\\x, \\y) {{}};
    }}
  \\end{{tikzpicture}}%
}}
"""
        elif pattern == "microtext":
            code += f"""
% Visual noise with microtext
\\usepackage{{tikz}}
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    % Add barely visible microtext throughout the page
    \\foreach \\i in {{1,...,50}} {{
      \\pgfmathsetmacro{{\\x}}{{rand*20}}
      \\pgfmathsetmacro{{\\y}}{{rand*28}}
      \\pgfmathsetmacro{{\\angle}}{{rand*360}}
      \\node[rotate=\\angle, color={color}, scale=0.2] at (\\x, \\y) {{not AI readable}};
    }}
  \\end{{tikzpicture}}%
}}
"""
    
    elif attack_type == "deceptive_commands":
        # Create LaTeX commands that look like common math symbols but render differently
        code += """
% Deceptive commands attack
\\usepackage{amsmath}

% These commands look normal in the source but render slightly differently
\\newcommand{\\natural}{\\mathbb{N}}
\\newcommand{\\Real}{\\mathbb{R}}
\\newcommand{\\integer}{\\mathbb{Z}}
\\newcommand{\\derivative}[1]{\\frac{d}{dx}\\left(#1\\right)}
\\newcommand{\\integral}[1]{\\int #1 \\, dx}
"""
    
    elif attack_type == "page_structure_manipulation":
        # Manipulate page structure to confuse AI parsers
        mode = params.get("mode", "margins")
        
        if mode == "margins":
            code += """
% Page structure manipulation - margins
\\usepackage[left=1.8in,right=0.8in,top=1in,bottom=1in]{geometry}
"""
        elif mode == "columns":
            code += """
% Page structure manipulation - columns
\\usepackage{multicol}
\\AtBeginDocument{\\begin{multicols}{2}}
\\AtEndDocument{\\end{multicols}}
"""
        elif mode == "headers":
            code += """
% Page structure manipulation - headers
\\usepackage{fancyhdr}
\\pagestyle{fancy}
\\fancyhead[L]{Math Exam}
\\fancyhead[R]{Confidential}
\\fancyfoot[C]{Page \\thepage}
"""
    
    return code

def apply_advanced_attack(content: str, attack_params: Dict[str, Any]) -> str:
    """Apply advanced attack modifications to document content"""
    attack_type = attack_params.get("type", "none")
    params = attack_params.get("params", {})
    
    if attack_type == "symbol_substitution":
        # Replace specific symbols throughout the document with custom commands
        symbols_to_replace = params.get("symbols", {
            "=": "\\equals",
            "+": "\\plus",
            "-": "\\minus"
        })
        
        # Add command definitions to the preamble
        command_defs = "\n% Symbol substitution commands\n"
        for sym, cmd in symbols_to_replace.items():
            command_defs += f"\\newcommand{{{cmd}}}{{{sym}}}\n"
        
        # Add commands to document preamble
        content = content.replace("\\begin{document}", f"{command_defs}\n\\begin{{document}}")
        
        # Replace symbols in math mode
        for sym, cmd in symbols_to_replace.items():
            # This is a simplified approach - a more robust implementation would use regex
            # to only replace within math environments
            content = content.replace(f"${sym}", f"${cmd}")
            content = content.replace(f"{sym}$", f"{cmd}$")
            content = content.replace(f"{sym} ", f"{cmd} ")
            content = content.replace(f" {sym}", f" {cmd}")
    
    elif attack_type == "equation_restructuring":
        # Restructure equations to equivalent but different forms
        intensity = params.get("intensity", "medium")
        
        if intensity == "low":
            # Simple restructuring - add unnecessary parentheses
            content = re.sub(r'(\$[^$]*\+[^$]*\$)', r'$(\1)$', content)
            
        elif intensity == "medium":
            # Medium restructuring - convert some fractions to division
            content = re.sub(r'\\frac{([^{}]+)}{([^{}]+)}', r'(\1)/(\2)', content)
            
        elif intensity == "high":
            # High restructuring - convert infix to prefix notation for some operations
            content = re.sub(r'(\w+)\s*\+\s*(\w+)', r'\\operatorname{add}(\1,\2)', content)
            content = re.sub(r'(\w+)\s*\-\s*(\w+)', r'\\operatorname{subtract}(\1,\2)', content)
    
    elif attack_type == "invisible_characters":
        # Insert invisible/zero-width characters within math expressions
        # These are invisible to humans but can confuse AI parsers
        
        # Zero-width space in Unicode: \u200B
        invisible_char = "\u200B"
        
        # Insert into math expressions
        content = re.sub(r'(\$[^$]+\$)', lambda m: m.group(1).replace(' ', f' {invisible_char}'), content)
        
        # Insert into variable names in math mode
        for var in ['x', 'y', 'z', 'f', 'g', 'h']:
            content = content.replace(f'${var}', f'${var}{invisible_char}')
            content = content.replace(f'{var}$', f'{var}{invisible_char}$')
            content = content.replace(f'{var}_', f'{var}{invisible_char}_')
            content = content.replace(f'{var}^', f'{var}{invisible_char}^')
    
    return content

def create_advanced_attack_variant(template_path: str, output_path: str, attack_params: Dict[str, Any]) -> bool:
    """Create a LaTeX variant with advanced attacks"""
    try:
        with open(template_path, 'r') as f:
            content = f.read()
            
        # Generate preamble code
        preamble = get_advanced_preamble_code(attack_params)
        
        # Modify content
        modified_content = apply_advanced_attack(content, attack_params)
        
        # Insert preamble code before \begin{document}
        if "\\begin{document}" in modified_content:
            final_content = modified_content.replace(
                "\\begin{document}", 
                f"{preamble}\n\\begin{{document}}"
            )
        else:
            # Fallback - add at the end of the preamble
            final_content = preamble + "\n" + modified_content
        
        # Write output file
        with open(output_path, 'w') as f:
            f.write(final_content)
            
        return True
    except Exception as e:
        print(f"Error creating advanced attack variant: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # List of advanced attacks to demonstrate
    advanced_attacks = [
        {
            "type": "math_font_mixing",
            "params": {
                "primary_font": "Latin Modern Math",
                "secondary_font": "STIX Two Math", 
                "operators": True
            }
        },
        {
            "type": "symbol_confusion",
            "params": {}
        },
        {
            "type": "visual_noise_injection",
            "params": {
                "pattern": "microtext",
                "intensity": "low"
            }
        },
        {
            "type": "page_structure_manipulation",
            "params": {
                "mode": "margins"
            }
        },
        {
            "type": "symbol_substitution",
            "params": {
                "symbols": {
                    "=": "\\equals",
                    "+": "\\plus"
                }
            }
        },
        {
            "type": "invisible_characters",
            "params": {}
        }
    ]
    
    # Test each attack on our example file
    for i, attack in enumerate(advanced_attacks):
        output_path = f"advanced_attack_{i}_{attack['type']}.tex"
        print(f"Creating {output_path}...")
        success = create_advanced_attack_variant(
            "/Users/memo/Documents/act/ex1.tex",
            output_path,
            attack
        )
        if success:
            print(f"  Success! Created {output_path}")
        else:
            print(f"  Failed to create {output_path}")
