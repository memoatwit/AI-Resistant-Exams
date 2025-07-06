import os
import subprocess
import random

def generate_watermark_code():
    """Generates LaTeX code for a random text watermark."""
    # Could add more random phrases here
    text = "CONFIDENTIAL --- DRAFT V2.1 --- " + str(random.randint(1000, 9999))
    return f"""
\\AddToShipoutPictureBG{{%
  \\AtPageCenter{{%
    \\rotatebox{{25}}{{%
      \\parbox{{\\paperwidth}}{{\\centering
        \\fontsize{{9}}{{11}}\\selectfont \\color{{gray!15}}
        {text}
      }}%
    }}%
  }}%
}}
"""

def create_exam_variant(template_path, output_name, attack_params):
    """Creates and compiles a modified LaTeX exam with specified attack parameters.
    
    Parameters:
    - template_path: Path to the LaTeX template file
    - output_name: Name for the output file (without extension)
    - attack_params: Dictionary with attack details including 'type' and 'params'
    
    Returns:
    - Path to the compiled PDF or None if compilation failed
    """
    with open(template_path, 'r') as f:
        template_content = f.read()
        
    # Generate appropriate code based on attack type
    attack_type = attack_params.get('type', 'none')
    params = attack_params.get('params', {})
    
    watermark_code = ""
    trap_question_code = ""
    
    if attack_type == 'none':
        # Clean baseline - no modifications
        pass
        
    elif attack_type == 'watermark':
        text = params.get('text', "CONFIDENTIAL")
        color = params.get('color', 'gray!15')
        size = params.get('size', 10)
        angle = params.get('angle', 30)
        
        watermark_code = f"""
\\AddToShipoutPictureBG{{%
  \\AtPageCenter{{%
    \\rotatebox{{{angle}}}{{%
      \\parbox{{\\paperwidth}}{{\\centering
        \\fontsize{{{size}}}{{{size+2}}}\\selectfont \\color{{{color}}}
        {text}
      }}%
    }}%
  }}%
}}
"""
    elif attack_type == 'texture':
        pattern = params.get('pattern', 'dots')
        density = params.get('density', 0.5)
        color = params.get('color', 'gray!10')
        
        if pattern == 'dots':
            # Use a more reasonable implementation for dots that won't overflow dimensions
            watermark_code = f"""
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    \\fill[{color}] (current page.south west) rectangle (current page.north east);
    \\foreach \\x in {{0,{density*10},...,20}}
      \\foreach \\y in {{0,{density*10},...,30}}
        {{\\fill[white] (\\x,\\y) circle (0.2pt);}}
  \\end{{tikzpicture}}
}}
"""
        elif pattern == 'lines':
            # Use fixed dimensions instead of paperwidth/paperheight to avoid overflow
            watermark_code = f"""
\\AddToShipoutPictureBG{{%
  \\begin{{tikzpicture}}[remember picture, overlay]
    \\foreach \\i in {{0,{density*5},...,20}}
      {{\\draw[{color}, thin] (\\i,0) -- (\\i,30);}}
    \\foreach \\i in {{0,{density*5},...,30}}
      {{\\draw[{color}, thin] (0,\\i) -- (20,\\i);}}
  \\end{{tikzpicture}}
}}
"""
    
    elif attack_type == 'kerning':
        amount = params.get('amount', -0.05)
        watermark_code = f"""
\\fontdimen2\\font={amount}em  % Inter word space
\\fontdimen3\\font={amount*2}em  % Inter word stretch
\\fontdimen4\\font={amount/2}em  % Inter word shrink
"""
    
    elif attack_type == 'combo':
        # Combine multiple attacks
        attacks = params.get('attacks', [])
        
        if 'watermark' in attacks:
            # Add a light watermark
            watermark_code += """
\\AddToShipoutPictureBG{%
  \\AtPageCenter{%
    \\rotatebox{30}{%
      \\parbox{\\paperwidth}{\\centering
        \\fontsize{10}{12}\\selectfont \\color{gray!15}
        CONFIDENTIAL --- EXAM MATERIAL --- DO NOT COPY
      }%
    }%
  }%
}
"""
        
        if 'texture' in attacks:
            # Add a light texture pattern (using fixed dimensions)
            watermark_code += """
\\AddToShipoutPictureBG{%
  \\begin{tikzpicture}[remember picture, overlay]
    \\foreach \\i in {0,4,...,20}
      {\\draw[gray!10, thin] (\\i,0) -- (\\i,30);}
  \\end{tikzpicture}
}
"""
    
    # Apply the modifications to the template
    modified_content = template_content.replace('%%WATERMARK_AREA%%', watermark_code)
    modified_content = modified_content.replace('%%TRAP_QUESTION_AREA%%', trap_question_code)

    variant_tex_path = f"{output_name}.tex"
    with open(variant_tex_path, 'w') as f:
        f.write(modified_content)

    print(f"Generated {variant_tex_path}. Compiling...")
    
    # Use lualatex. The -interaction=nonstopmode flag prevents it from pausing on errors.
    process = subprocess.run(
        ['lualatex', '-interaction=nonstopmode', variant_tex_path],
        capture_output=True, text=True
    )
    
    if process.returncode == 0:
        print(f"Successfully compiled {output_name}.pdf")
        return f"{output_name}.pdf"
    else:
        print(f"Error compiling {variant_tex_path}.")
        print(process.stdout)
        print(process.stderr)
        return None

# --- Main execution ---
if __name__ == "__main__":
    # Test with a simple watermark attack
    template_file = 'ex0.tex'
    
    # Sample attack parameters
    test_attack = {
        'name': 'test_watermark',
        'type': 'watermark',
        'params': {
            'text': "DO NOT COPY - EXAM PAPER",
            'color': 'gray!15',
            'size': 10,
            'angle': 30
        }
    }
    
    # Create and compile the PDF
    variant_id = f"variant_{test_attack['name']}"
    pdf_path = create_exam_variant(template_file, variant_id, test_attack)
    
    if pdf_path:
        print(f"Next step: Test {pdf_path} against an AI model.")