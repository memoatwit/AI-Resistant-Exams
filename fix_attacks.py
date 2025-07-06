#!/usr/bin/env python3
# fix_attacks.py
#
# This script fixes the issues with kerning and font swapping attacks
# and regenerates the failed PDFs

import os
import json
import subprocess
from pathlib import Path

def fix_kerning_attack(tex_file):
    """Fix issues in the kerning attack tex file"""
    print(f"Fixing kerning attack in {tex_file}...")
    
    with open(tex_file, "r") as f:
        content = f.read()
    
    # The main issue is that \mkern isn't properly setup
    # Add amsmath package if it's not already included
    if "\\usepackage{amsmath}" not in content:
        content = content.replace("\\documentclass[12pt]{article}", 
                                "\\documentclass[12pt]{article}\n\\usepackage{amsmath}")
    
    # Replace direct \mkern insertions with a safer approach
    content = content.replace("\\mkern-0.08em", "\\mspace{-3mu}")
    
    with open(tex_file, "w") as f:
        f.write(content)
    
    print(f"Fixed kerning attack in {tex_file}")
    return content

def fix_font_swap_attack(tex_file):
    """Fix issues in the font swap attack tex file"""
    print(f"Fixing font swap attack in {tex_file}...")
    
    with open(tex_file, "r") as f:
        content = f.read()
    
    # The main issue is that the font command isn't defined
    # Add a proper definition for the font command
    preamble_addition = """
% Define the symbol replacement commands
\\usepackage{ifthen}
\\newcommand{\\weird}{\\fontfamily{cmss}\\selectfont}
\\DeclareRobustCommand{\\weirdsymbol}{\\text{\\weird =}}
"""
    
    # Insert after the last \usepackage
    last_usepackage = content.rfind("\\usepackage")
    if last_usepackage > 0:
        last_usepackage_end = content.find("\n", last_usepackage)
        if last_usepackage_end > 0:
            content = content[:last_usepackage_end+1] + preamble_addition + content[last_usepackage_end+1:]
    
    with open(tex_file, "w") as f:
        f.write(content)
    
    print(f"Fixed font swap attack in {tex_file}")
    return content

def fix_combo_attack(tex_file):
    """Fix issues in combination attack tex files"""
    print(f"Fixing combination attack in {tex_file}...")
    
    with open(tex_file, "r") as f:
        content = f.read()
    
    # Apply both fixes
    content = content.replace("\\mkern-0.08em", "\\mspace{-3mu}")
    content = content.replace("\\mkern-0.07em", "\\mspace{-3mu}")
    
    # Add font commands
    preamble_addition = """
% Define the symbol replacement commands
\\usepackage{ifthen}
\\newcommand{\\weird}{\\fontfamily{cmss}\\selectfont}
\\DeclareRobustCommand{\\weirdsymbol}{\\text{\\weird =}}
"""
    
    # Insert after the last \usepackage
    last_usepackage = content.rfind("\\usepackage")
    if last_usepackage > 0:
        last_usepackage_end = content.find("\n", last_usepackage)
        if last_usepackage_end > 0:
            content = content[:last_usepackage_end+1] + preamble_addition + content[last_usepackage_end+1:]
    
    with open(tex_file, "w") as f:
        f.write(content)
    
    print(f"Fixed combination attack in {tex_file}")
    return content

def recompile_tex(tex_file):
    """Recompile a tex file and report success or failure"""
    print(f"Recompiling {tex_file}...")
    
    try:
        # Use lualatex to compile
        result = subprocess.run(
            ["lualatex", "--interaction=nonstopmode", tex_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            pdf_file = tex_file.replace(".tex", ".pdf")
            print(f"Successfully compiled {pdf_file}")
            return pdf_file
        else:
            print(f"Failed to compile {tex_file}")
            print(f"Error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception during compilation: {e}")
        return None

def fix_and_recompile_all_attacks():
    """Find, fix and recompile all failed attacks"""
    # Find the failed tex files
    kerning_files = list(Path('.').glob("*kerning*.tex"))
    font_swap_files = list(Path('.').glob("*font_swap*.tex"))
    combo_files = list(Path('.').glob("*combo*.tex"))
    kitchen_sink_files = list(Path('.').glob("*kitchen_sink*.tex"))
    
    fixed_files = []
    
    # Fix kerning attacks
    for tex_file in kerning_files:
        if "combo" not in str(tex_file):  # Skip combo files for now
            fix_kerning_attack(str(tex_file))
            pdf = recompile_tex(str(tex_file))
            if pdf:
                fixed_files.append(pdf)
    
    # Fix font swap attacks
    for tex_file in font_swap_files:
        if "combo" not in str(tex_file):  # Skip combo files for now
            fix_font_swap_attack(str(tex_file))
            pdf = recompile_tex(str(tex_file))
            if pdf:
                fixed_files.append(pdf)
    
    # Fix combo attacks
    all_combo_files = combo_files + kitchen_sink_files
    for tex_file in all_combo_files:
        fix_combo_attack(str(tex_file))
        pdf = recompile_tex(str(tex_file))
        if pdf:
            fixed_files.append(pdf)
    
    return fixed_files

if __name__ == "__main__":
    fixed_pdfs = fix_and_recompile_all_attacks()
    
    print("\nSummary:")
    print(f"Fixed and recompiled {len(fixed_pdfs)} PDF files:")
    for pdf in fixed_pdfs:
        print(f"- {pdf}")
    
    print("\nNow you can run test_fixed_pdfs.py to evaluate these fixed PDFs.")
