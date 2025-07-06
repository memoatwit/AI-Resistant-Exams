#!/usr/bin/env python3
# generalized_attack.py
#
# This is an enhanced version of exam_attack.py that implements
# attacks that are robust across diverse math problems

import os
import subprocess
import re
import shutil
from pathlib import Path

class DocumentAnalyzer:
    """Analyzes a LaTeX document to understand its structure and content."""
    
    def __init__(self, tex_content):
        self.tex_content = tex_content
        self.has_figures = '\\begin{figure}' in tex_content or '\\includegraphics' in tex_content
        self.has_enums = '\\begin{enumerate}' in tex_content
        self.has_complex_math = '\\begin{align}' in tex_content or '\\begin{equation}' in tex_content
        self.math_environments = self._find_math_environments()
        self.math_expressions = self._extract_math_expressions()
        self.document_class = self._extract_document_class()
        self.packages = self._extract_packages()
        
    def _find_math_environments(self):
        """Find all math environments in the document."""
        env_pattern = r'\\begin\{(align|equation|gather|multline|array|matrix|pmatrix|bmatrix|vmatrix)\}(.*?)\\end\{\1\}'
        return re.findall(env_pattern, self.tex_content, re.DOTALL)
    
    def _extract_math_expressions(self):
        """Extract inline math expressions from the document."""
        # Match both $...$ and \(...\) style math expressions
        inline_pattern = r'\$(.*?)\$|\\\((.*?)\\\)'
        return re.findall(inline_pattern, self.tex_content, re.DOTALL)
    
    def _extract_document_class(self):
        """Extract document class and options."""
        class_pattern = r'\\documentclass(?:\[(.*?)\])?\{(.*?)\}'
        match = re.search(class_pattern, self.tex_content)
        if match:
            options = match.group(1) or ""
            doc_class = match.group(2)
            return {'class': doc_class, 'options': options}
        return {'class': 'article', 'options': ''}
    
    def _extract_packages(self):
        """Extract all packages used in the document."""
        pkg_pattern = r'\\usepackage(?:\[(.*?)\])?\{(.*?)\}'
        packages = []
        for match in re.finditer(pkg_pattern, self.tex_content):
            options = match.group(1) or ""
            pkg = match.group(2)
            packages.append({'name': pkg, 'options': options})
        return packages
    
    def get_target_math_for_attacks(self):
        """Identify suitable math expressions for targeted attacks."""
        candidates = []
        
        # First try to extract from defined math environments
        for env, content in self.math_environments:
            # Clean the content to remove LaTeX commands that might interfere with the attack
            cleaned = re.sub(r'\\\\|\\label\{.*?\}', ' ', content)
            # Extract meaningful expressions (avoid just single symbols)
            expressions = re.findall(r'[a-zA-Z0-9](?:[a-zA-Z0-9\+\-\*\/\^\{\}\(\)]{3,}[a-zA-Z0-9])', cleaned)
            for expr in expressions:
                if len(expr) > 5 and not expr.startswith('\\'):  # Avoid commands
                    candidates.append(expr)
        
        # If we don't have enough, look at inline expressions
        if len(candidates) < 3:
            for expr in self.math_expressions:
                # Combine the two capturing groups
                expr_text = expr[0] if expr[0] else expr[1]
                if len(expr_text) > 5:
                    candidates.append(expr_text)
        
        return candidates[:5]  # Return up to 5 candidates
    
    def get_subject_hint(self):
        """Try to guess the mathematical subject of the document."""
        content_lower = self.tex_content.lower()
        
        # Check for subject indicators
        if 'calculus' in content_lower or 'derivative' in content_lower or '\\frac{d}{dx}' in content_lower:
            return 'calculus'
        elif 'probability' in content_lower or 'random' in content_lower:
            return 'probability'
        elif 'linear algebra' in content_lower or '\\begin{matrix}' in content_lower:
            return 'linear_algebra'
        elif 'complex' in content_lower and ('analysis' in content_lower or 'variable' in content_lower):
            return 'complex_analysis'
        elif 'discrete' in content_lower or 'graph' in content_lower:
            return 'discrete_math'
        elif 'machine learning' in content_lower or 'neural' in content_lower:
            return 'machine_learning'
        else:
            return 'general_math'


def get_attack_config(attack_type, subject='general_math'):
    """
    Gets appropriate attack configuration parameters based on document subject.
    """
    # Default configs
    configs = {
        'watermark': {
            'general_math': {'text': 'EXAM', 'color': 'gray!10', 'angle': 45, 'size': 5},
            'calculus': {'text': r'f\'(x)', 'color': 'gray!12', 'angle': 30, 'size': 6},
            'complex_analysis': {'text': r'f(z)', 'color': 'gray!12', 'angle': 30, 'size': 6},
            'discrete_math': {'text': r'G(V,E)', 'color': 'gray!12', 'angle': 25, 'size': 6},
            'linear_algebra': {'text': r'A\vec{x}=\vec{b}', 'color': 'gray!12', 'angle': 20, 'size': 5},
            'probability': {'text': r'P(X)', 'color': 'gray!12', 'angle': 35, 'size': 5},
            'machine_learning': {'text': r'\nabla J(\theta)', 'color': 'gray!12', 'angle': 40, 'size': 5}
        },
        'texture': {
            'general_math': {'pattern': 'dots', 'color': 'gray!10', 'density': 0.7},
            'calculus': {'pattern': 'wave', 'color': 'gray!12', 'density': 0.6},
            'complex_analysis': {'pattern': 'circles', 'color': 'gray!12', 'density': 0.6},
            'discrete_math': {'pattern': 'grid', 'color': 'gray!12', 'density': 0.7},
            'linear_algebra': {'pattern': 'lines', 'color': 'gray!12', 'density': 0.6},
            'probability': {'pattern': 'dots', 'color': 'gray!12', 'density': 0.7},
            'machine_learning': {'pattern': 'dots', 'color': 'gray!12', 'density': 0.8}
        },
        'kerning': {
            'general_math': {'amount': -0.05},
            'calculus': {'amount': -0.06},
            'complex_analysis': {'amount': -0.07},
            'discrete_math': {'amount': -0.05},
            'linear_algebra': {'amount': -0.06},
            'probability': {'amount': -0.05},
            'machine_learning': {'amount': -0.06}
        },
        'font_swap': {
            'general_math': {'symbol_to_swap': '=', 'font_name': 'Comic Sans MS'},
            'calculus': {'symbol_to_swap': '+', 'font_name': 'Comic Sans MS'},
            'complex_analysis': {'symbol_to_swap': 'z', 'font_name': 'Times New Roman'},
            'discrete_math': {'symbol_to_swap': '\\in', 'font_name': 'Arial'},
            'linear_algebra': {'symbol_to_swap': '=', 'font_name': 'Georgia'},
            'probability': {'symbol_to_swap': '(', 'font_name': 'Courier New'},
            'machine_learning': {'symbol_to_swap': '\\theta', 'font_name': 'Arial'}
        }
    }
    
    # Return subject-specific config if it exists, otherwise general math config
    if attack_type in configs:
        return configs[attack_type].get(subject, configs[attack_type]['general_math'])
    return {}


def get_preamble_code(attack_params: dict, context_level=0, doc_analyzer=None) -> str:
    """
    Enhanced version of get_preamble_code that can adapt to document structure.
    
    Args:
        attack_params: Dictionary with attack details
        context_level: Level of context awareness (0-3)
        doc_analyzer: DocumentAnalyzer instance for document structure awareness
        
    Returns:
        LaTeX code to be inserted in the preamble
    """
    attack_type = attack_params.get('type', 'none')
    params = attack_params.get('params', {})
    code = ""

    # This preamble code will be added for any attack needing page dimensions
    dimension_setup = """
\\usepackage{layouts}
\\usepackage{atbegshi}
\\newlength\\pgwidth
\\newlength\\pgheight
\\AtBeginDocument{%
  \\pgwidth=\\paperwidth
  \\pgheight=\\paperheight
}
"""

    # Check if the package is already in the document (level 2+ feature)
    if context_level >= 2 and doc_analyzer:
        if not any(pkg['name'] == 'layouts' for pkg in doc_analyzer.packages):
            if attack_type in ['watermark_tiled', 'texture', 'background_color']:
                code += dimension_setup
    elif attack_type in ['watermark_tiled', 'texture', 'background_color']:
        code += dimension_setup

    if attack_type == 'watermark':
        # Generate watermark in the background of the document
        text = params.get('text', 'EXAM COPY')
        color = params.get('color', 'gray!10')
        angle = params.get('angle', 45)
        size = params.get('size', 5)
        
        # Level 2+: Check if the document has figures and adjust watermark opacity
        if context_level >= 2 and doc_analyzer and doc_analyzer.has_figures:
            color = color.replace('gray!10', 'gray!8')  # Make lighter if figures exist
        
        code += f"""
\\usepackage{{eso-pic}}
\\AddToShipoutPictureBG{{%
  \\AtPageCenter{{%
    \\rotatebox{{{angle}}}{{%
      \\scalebox{{{size}}}{{%
        \\textcolor{{{color}}}{{{text}}}%
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
        
        # Level 1+: Adjust watermark for documents with figures
        if context_level >= 1 and doc_analyzer and doc_analyzer.has_figures:
            # Make slightly less dense to avoid overwhelming figures
            x_step += 1
            y_step += 1
        
        # Level 3: Subject-specific watermarks
        if context_level >= 3 and doc_analyzer:
            subject = doc_analyzer.get_subject_hint()
            if 'text' not in params:  # Only if not explicitly set
                subject_text = {
                    'calculus': r'f\'(x)',
                    'complex_analysis': 'f(z)',
                    'discrete_math': 'G(V,E)',
                    'linear_algebra': r'A\vec{x}',
                    'probability': 'P(X)',
                    'machine_learning': r'\nabla J'
                }.get(subject, text)
                text = subject_text
        
        code += f"""
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    % Fixed loop to use fixed steps instead of calculated dimensions
    \\foreach \\x in {{1,{1+x_step},...,20}} {{
      \\foreach \\y in {{1,{1+y_step},...,28}} {{
        \\node[rotate={angle}, color={color}, anchor=center] at (\\x cm, \\y cm) {{\\fontsize{{{size}}}{{{size+2}}}\\selectfont ${text}$}};
      }}
    }}
  \\end{{tikzpicture}}%
}}
"""
    elif attack_type == 'texture':
        pattern = params.get('pattern', 'dots')
        density = params.get('density', 0.7)
        color = params.get('color', 'gray!10')
        step = 2.0 / density if density > 0 else 2.0
        
        # Level 1+: Adjust pattern based on document content
        if context_level >= 1 and doc_analyzer:
            if doc_analyzer.has_figures:
                density *= 0.8  # Reduce density for documents with figures
                step = 2.0 / density if density > 0 else 2.0
                color = color.replace('gray!10', 'gray!8')  # Lighter color
        
        # Level 3: Choose pattern based on subject
        if context_level >= 3 and doc_analyzer:
            subject = doc_analyzer.get_subject_hint()
            if 'pattern' not in params:  # Only if not explicitly set
                pattern = {
                    'calculus': 'wave',
                    'complex_analysis': 'circles',
                    'discrete_math': 'grid',
                    'linear_algebra': 'lines',
                    'probability': 'dots',
                    'machine_learning': 'dots'
                }.get(subject, pattern)

        if pattern == 'dots':
            code += f"""
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    \\foreach \\x in {{0,{step},...,20}} {{
      \\foreach \\y in {{0,{step},...,28}} {{
        \\node[circle, fill={color}, inner sep=0.2pt] at (\\x cm, \\y cm) {{}};
      }}
    }}
  \\end{{tikzpicture}}%
}}"""
        elif pattern == 'lines':
            code += f"""
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    \\foreach \\x in {{0,{step},...,20}} {{\\draw[{color}, thin] (\\x,0) -- (\\x,28);}}
    \\foreach \\y in {{0,{step},...,28}} {{\\draw[{color}, thin] (0,\\y) -- (20,\\y);}}
  \\end{{tikzpicture}}%
}}"""
        elif pattern == 'wave':
            # Simplified wave pattern to avoid calculation errors
            code += f"""
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    \\foreach \\i in {{0,1,...,20}} {{
      \\draw[{color}, thin] 
        plot[domain=0:20, samples=100, smooth] 
        (\\x, {{\\i*{step} + 0.1*sin(\\x*90)}});
    }}
  \\end{{tikzpicture}}%
}}"""
        elif pattern == 'circles':
            code += f"""
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    \\foreach \\i in {{1,2,...,10}} {{
      \\draw[{color}, thin] (10,14) circle (\\i*{step*2}cm);
    }}
  \\end{{tikzpicture}}%
}}"""
        elif pattern == 'grid':
            code += f"""
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    \\draw[{color}, thin, step={step}cm] (0,0) grid (20,28);
  \\end{{tikzpicture}}%
}}"""

    elif attack_type == 'font_swap':
        font_name = params.get('font_name', 'Comic Sans MS')
        symbol = params.get('symbol_to_swap', '+')
        safe_name = ''.join(c for c in symbol if c.isalnum())
        if not safe_name:
            safe_name = "weirdsymbol"
        command_name = f"\\weird{safe_name}"
        
        # Level 2+: Adapt to subject matter if no specific symbol is provided
        if context_level >= 2 and doc_analyzer and 'symbol_to_swap' not in params:
            subject = doc_analyzer.get_subject_hint()
            symbol = {
                'calculus': '+',
                'complex_analysis': 'z',
                'discrete_math': '\\in',
                'linear_algebra': '=',
                'probability': '(',
                'machine_learning': '\\theta'
            }.get(subject, symbol)
            
            # Regenerate command name for new symbol
            safe_name = ''.join(c for c in symbol if c.isalnum())
            if not safe_name:  # If the symbol has no alphanumeric chars
                safe_name = "weirdsymbol"
            command_name = f"\\weird{safe_name}"
        
        code = f"""
% Ensure fontspec is loaded with proper options
\\RequirePackage{{fontspec}}
\\newfontfamily\\weirdfont{{{font_name}}}[Scale=1.0]
\\newcommand{{{command_name}}}{{{{\\weirdfont {symbol}}}}}
"""

    elif attack_type == 'background_color':
        # New attack type: subtle background color variation
        color = params.get('color', 'yellow!3')
        mode = params.get('mode', 'full')
        
        if mode == 'full':
            code += f"""
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    \\fill[{color}] (current page.south west) rectangle (current page.north east);
  \\end{{tikzpicture}}%
}}"""
        elif mode == 'gradient':
            code += f"""
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    \\shade[left color={color}, right color=white] 
      (current page.south west) rectangle (current page.north east);
  \\end{{tikzpicture}}%
}}"""
        elif mode == 'sections':
            code += f"""
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    \\foreach \\i in {{0,2,...,28}} {{
      \\fill[{color}] (0, \\i) rectangle (20, \\i+1);
    }}
  \\end{{tikzpicture}}%
}}"""
    
    return code


def modify_body_content(content: str, attack_params: dict, context_level=0, doc_analyzer=None) -> str:
    """
    Enhanced version of modify_body_content that adapts to document structure.
    
    Args:
        content: Original LaTeX content
        attack_params: Dictionary with attack details
        context_level: Level of context awareness (0-3)
        doc_analyzer: DocumentAnalyzer instance for document structure awareness
        
    Returns:
        Modified LaTeX content
    """
    attack_type = attack_params.get('type', 'none')
    params = attack_params.get('params', {})

    if attack_type == 'kerning':
        amount = params.get('amount', -0.05)
        
        # Level 0: Simple global kerning like the original
        if 'target' in params:
            target = params['target']
            # For LaTeX math expressions, insert kerning at specific places instead
            # of between every character which could break the math
            
            # Replace the target in math mode with a kerned version
            mathPattern = f"${re.escape(target)}$"
            replacement = f"${target}\\mkern{amount}em$"
            
            # Apply replacement
            return content.replace(mathPattern, replacement)
        
        # Level 2+: Smart targeting of math expressions
        elif context_level >= 2 and doc_analyzer:
            modified_content = content
            
            # Get suitable math targets
            targets = doc_analyzer.get_target_math_for_attacks()
            
            for target in targets:
                # Skip if it's too simple
                if len(target) < 5:
                    continue
                    
                # Safely escape target for regex
                escaped_target = re.escape(target)
                
                # Insert the kerning command carefully
                modified_content = re.sub(
                    f"({escaped_target})", 
                    f"\\1\\\\mkern{amount}em", 
                    modified_content
                )
            
            return modified_content
            
        return content

    if attack_type == 'font_swap':
        symbol = params.get('symbol_to_swap', '+')
        # Generate a simple command name with no special chars
        safe_name = ''.join(c for c in symbol if c.isalnum())
        if not safe_name:  # If the symbol has no alphanumeric chars
            safe_name = "weirdsymbol"
        command_name = f"\\weird{safe_name}"
        
        # Level 3: Smart symbol replacement based on context
        if context_level >= 3 and doc_analyzer:
            modified_content = content
            
            # For complex math expressions, be more surgical about replacements
            # Only apply to displayed math, not inline math
            if doc_analyzer.has_complex_math:
                # Extract display math environments
                for env_name, env_content in doc_analyzer.math_environments:
                    # Replace only in this environment
                    modified_env = env_content.replace(symbol, command_name)
                    # Put it back in the content
                    modified_content = modified_content.replace(
                        f"\\begin{{{env_name}}}{env_content}\\end{{{env_name}}}", 
                        f"\\begin{{{env_name}}}{modified_env}\\end{{{env_name}}}"
                    )
                return modified_content
        
        # Simple string replace is more reliable here for level 0-2
        return content.replace(symbol, command_name)

    if attack_type == 'line_spacing':
        # New attack: subtle line spacing variations
        factor = params.get('factor', 1.1)
        
        # Level 1+: Don't mess with figures
        if context_level >= 1 and doc_analyzer and doc_analyzer.has_figures:
            # Apply only to text paragraphs, not figure environments
            parts = re.split(r'(\\begin\{figure\}.*?\\end\{figure\})', content, flags=re.DOTALL)
            modified_parts = []
            
            for i, part in enumerate(parts):
                if i % 2 == 0:  # Text part, not a figure
                    modified_parts.append(f"\\linespread{{{factor}}}{part}")
                else:  # Figure part, leave unchanged
                    modified_parts.append(part)
            
            return ''.join(modified_parts)
        
        # Level 0: Simple global line spacing
        return f"\\linespread{{{factor}}}{content}"

    if attack_type == 'symbol_stretch':
        # New attack: subtle stretching of math symbols
        target = params.get('target', '=')
        x_scale = params.get('x_scale', 1.05)
        y_scale = params.get('y_scale', 1.0)
        
        command_def = f"\\newcommand{{\\stretchedsymbol}}{{\\scalebox{{{x_scale}}}[{y_scale}]{{{target}}}}}}}"
        
        # First, add the command definition after documentclass
        modified = re.sub(
            r'(\\documentclass(?:\[.*?\])?\{.*?\})',
            f'\\1\n\n{command_def}',
            content
        )
        
        # Then replace all occurrences
        return modified.replace(target, "\\stretchedsymbol")

    return content


def create_exam_variant(template_path: str, output_name: str, attack_params: dict, context_level=0) -> str | None:
    """
    Creates and compiles a modified LaTeX exam with specified attack parameters.
    
    Args:
        template_path: Path to the original LaTeX template
        output_name: Name for the output files (without extension)
        attack_params: Dictionary with attack details
        context_level: Level of context awareness (0-3)
        
    Returns:
        Path to generated PDF, or None if compilation failed
    """
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Create a document analyzer if using context level > 0
    doc_analyzer = None
    if context_level > 0:
        doc_analyzer = DocumentAnalyzer(template_content)
    
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
                preamble_code = get_preamble_code(sub_attack, context_level, doc_analyzer)
                if '\\usepackage{layouts}' in preamble_code and '\\usepackage{layouts}' in preamble_mods:
                    # Strip out the dimension setup part
                    setup_end = preamble_code.find('\\AddToShipoutPictureBG')
                    if setup_end > 0:
                        preamble_mods += preamble_code[setup_end:]
                else:
                    preamble_mods += preamble_code
            else:
                preamble_mods += get_preamble_code(sub_attack, context_level, doc_analyzer)
        
        # Then apply all body modifications
        for sub_attack in sub_attacks:
            modified_content = modify_body_content(modified_content, sub_attack, context_level, doc_analyzer)
    else:
        # For single attacks
        preamble_mods = get_preamble_code(attack_params, context_level, doc_analyzer)
        modified_content = modify_body_content(modified_content, attack_params, context_level, doc_analyzer)

    # Apply the modifications to the template
    # Look for the placeholder, but if it doesn't exist, add before \begin{document}
    if '%%WATERMARK_AREA%%' in modified_content:
        final_content = modified_content.replace('%%WATERMARK_AREA%%', preamble_mods)
    else:
        final_content = modified_content.replace('\\begin{document}', f"{preamble_mods}\n\\begin{{document}}")
    
    # Handle trap question area if it exists
    if '%%TRAP_QUESTION_AREA%%' in final_content:
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


# Example usage (can be commented out when imported)
if __name__ == "__main__":
    # Example of using the generalized attack with context awareness
    watermark_attack = {
        'name': 'A1_watermark_tiled_math',
        'type': 'watermark_tiled',
        'params': {'text': r"f'(x)", 'color': 'gray!15', 'size': 8, 'angle': 20, 'x_step': 4, 'y_step': 3}
    }
    
    # Test with different context levels
    for level in [0, 1, 2, 3]:
        result = create_exam_variant(
            template_path='ex1.tex',
            output_name=f'test_variant_ex1_level{level}',
            attack_params=watermark_attack,
            context_level=level
        )
        print(f"Level {level} result: {result}")
