#!/usr/bin/env python3
# attack_configurator.py
#
# A tool for configuring and applying AI-resistant attacks to LaTeX exams

import os
import json
import argparse
from pathlib import Path
import tempfile
import subprocess
from typing import Dict, Any, List, Optional

from generalized_attack import create_exam_variant, DocumentAnalyzer
from advanced_attacks import create_advanced_attack_variant

# --- Configuration Settings ---

# Basic attack types
BASIC_ATTACKS = [
    {
        "id": "watermark",
        "name": "Background Watermark",
        "description": "Adds a large watermark to the background of the document"
    },
    {
        "id": "watermark_tiled",
        "name": "Tiled Math Watermarks",
        "description": "Adds tiled mathematical expressions as watermarks"
    },
    {
        "id": "texture",
        "name": "Background Texture",
        "description": "Adds a textured pattern to the document background"
    },
    {
        "id": "kerning",
        "name": "Character Kerning",
        "description": "Modifies the spacing between characters in math expressions"
    },
    {
        "id": "font_swap",
        "name": "Symbol Font Swap",
        "description": "Replaces specific symbols with different fonts"
    },
    {
        "id": "background_color",
        "name": "Background Color",
        "description": "Adds subtle background coloration to the document"
    },
    {
        "id": "line_spacing",
        "name": "Line Spacing Modification",
        "description": "Subtly adjusts the spacing between lines"
    }
]

# Advanced attack types
ADVANCED_ATTACKS = [
    {
        "id": "math_font_mixing",
        "name": "Math Font Mixing",
        "description": "Uses different fonts for different parts of equations"
    },
    {
        "id": "symbol_confusion",
        "name": "Symbol Confusion",
        "description": "Replaces math symbols with visually similar ones"
    },
    {
        "id": "visual_noise_injection",
        "name": "Visual Noise Injection",
        "description": "Adds subtle visual noise that's hard for AI to filter"
    },
    {
        "id": "symbol_substitution",
        "name": "Symbol Substitution",
        "description": "Replaces symbols with custom LaTeX commands"
    },
    {
        "id": "invisible_characters",
        "name": "Invisible Characters",
        "description": "Inserts zero-width spaces in math expressions"
    },
    {
        "id": "page_structure_manipulation",
        "name": "Page Structure Manipulation",
        "description": "Modifies page layout and structure"
    }
]

# Combination presets
COMBO_PRESETS = [
    {
        "id": "light_protection",
        "name": "Light Protection",
        "description": "Subtle changes that maintain full readability",
        "attacks": [
            {"type": "watermark", "params": {"color": "gray!5", "angle": 45, "size": 4}},
            {"type": "kerning", "params": {"amount": -0.04}}
        ]
    },
    {
        "id": "medium_protection",
        "name": "Medium Protection",
        "description": "Balance between AI resistance and readability",
        "attacks": [
            {"type": "watermark_tiled", "params": {"text": "f(x)", "color": "gray!10", "angle": 30}},
            {"type": "texture", "params": {"pattern": "dots", "density": 0.6, "color": "gray!10"}}
        ]
    },
    {
        "id": "strong_protection",
        "name": "Strong Protection",
        "description": "Maximum AI resistance with acceptable readability",
        "attacks": [
            {"type": "kerning", "params": {"amount": -0.08}},
            {"type": "watermark_tiled", "params": {"text": "\\nabla f(x)", "color": "gray!15"}},
            {"type": "font_swap", "params": {"symbol_to_swap": "="}}
        ]
    },
    {
        "id": "extreme_protection",
        "name": "Extreme Protection",
        "description": "Maximum AI resistance using advanced techniques",
        "basic_attacks": [
            {"type": "watermark_tiled", "params": {"text": "f'(x)", "color": "gray!12"}},
            {"type": "texture", "params": {"pattern": "wave", "color": "gray!12"}}
        ],
        "advanced_attacks": [
            {"type": "invisible_characters", "params": {}},
            {"type": "symbol_confusion", "params": {}}
        ]
    }
]

def list_attacks():
    """List all available attacks with descriptions"""
    print("\n=== AVAILABLE ATTACKS ===\n")
    
    print("--- BASIC ATTACKS ---")
    for attack in BASIC_ATTACKS:
        print(f"- {attack['name']} ({attack['id']})")
        print(f"  {attack['description']}")
    
    print("\n--- ADVANCED ATTACKS ---")
    for attack in ADVANCED_ATTACKS:
        print(f"- {attack['name']} ({attack['id']})")
        print(f"  {attack['description']}")
    
    print("\n--- COMBINATION PRESETS ---")
    for preset in COMBO_PRESETS:
        print(f"- {preset['name']} ({preset['id']})")
        print(f"  {preset['description']}")

def configure_attack(attack_id: str, context_level: int = 2) -> Dict[str, Any]:
    """Configure an attack based on the ID and return attack parameters"""
    # Check if it's a basic attack
    for attack in BASIC_ATTACKS:
        if attack["id"] == attack_id:
            params = {}
            
            if attack_id == "watermark":
                text = input("Watermark text [EXAM COPY]: ") or "EXAM COPY"
                color = input("Color [gray!10]: ") or "gray!10"
                angle = input("Angle [45]: ") or "45"
                size = input("Size [5]: ") or "5"
                
                params = {
                    "text": text,
                    "color": color,
                    "angle": int(angle),
                    "size": int(size)
                }
            
            elif attack_id == "watermark_tiled":
                text = input("Math expression to tile [f'(x)]: ") or "f'(x)"
                color = input("Color [gray!15]: ") or "gray!15"
                angle = input("Angle [20]: ") or "20"
                size = input("Size [8]: ") or "8"
                
                params = {
                    "text": text,
                    "color": color,
                    "angle": int(angle),
                    "size": int(size)
                }
                
            elif attack_id == "texture":
                pattern = input("Pattern (dots/lines/wave) [wave]: ") or "wave"
                color = input("Color [gray!15]: ") or "gray!15"
                density = input("Density (0.1-2.0) [0.7]: ") or "0.7"
                
                params = {
                    "pattern": pattern,
                    "color": color,
                    "density": float(density)
                }
                
            elif attack_id == "kerning":
                amount = input("Kerning amount (-0.1 to -0.01) [-0.08]: ") or "-0.08"
                target = input("Target expression (leave empty for auto-detection): ")
                
                params = {"amount": float(amount)}
                if target:
                    params["target"] = target
                    
            elif attack_id == "font_swap":
                symbol = input("Symbol to swap [=]: ") or "="
                font = input("Font name [Comic Sans MS]: ") or "Comic Sans MS"
                
                params = {
                    "symbol_to_swap": symbol,
                    "font_name": font
                }
                
            elif attack_id == "background_color":
                color = input("Color [yellow!3]: ") or "yellow!3"
                mode = input("Mode (full/gradient/sections) [full]: ") or "full"
                
                params = {
                    "color": color,
                    "mode": mode
                }
                
            elif attack_id == "line_spacing":
                factor = input("Spacing factor (1.0-1.5) [1.08]: ") or "1.08"
                
                params = {
                    "factor": float(factor)
                }
            
            return {
                "name": attack_id,
                "type": attack_id,
                "params": params
            }
            
    # Check if it's an advanced attack
    for attack in ADVANCED_ATTACKS:
        if attack["id"] == attack_id:
            params = {}
            
            if attack_id == "math_font_mixing":
                params = {
                    "primary_font": "Latin Modern Math",
                    "secondary_font": input("Secondary font [STIX Two Math]: ") or "STIX Two Math",
                    "operators": input("Modify operators (y/n) [y]: ").lower() != "n",
                    "letters": input("Modify letters (y/n) [y]: ").lower() != "n",
                    "numbers": input("Modify numbers (y/n) [n]: ").lower() == "y"
                }
                
            elif attack_id == "symbol_confusion":
                params = {}  # Uses defaults
                
            elif attack_id == "visual_noise_injection":
                pattern = input("Pattern (dots/microtext) [dots]: ") or "dots"
                intensity = input("Intensity (low/medium/high) [medium]: ") or "medium"
                color = input("Color [gray!10]: ") or "gray!10"
                
                params = {
                    "pattern": pattern,
                    "intensity": intensity,
                    "color": color
                }
                
            elif attack_id == "symbol_substitution":
                symbols = {}
                print("Enter symbols to replace (blank to finish):")
                while True:
                    symbol = input("Symbol: ")
                    if not symbol:
                        break
                    command = input(f"Command for {symbol} [\\{symbol}cmd]: ") or f"\\{symbol}cmd"
                    symbols[symbol] = command
                
                if not symbols:
                    symbols = {"=": "\\equals", "+": "\\plus"}
                    
                params = {"symbols": symbols}
                
            elif attack_id == "invisible_characters":
                params = {}  # Uses defaults
                
            elif attack_id == "page_structure_manipulation":
                mode = input("Mode (margins/columns/headers) [margins]: ") or "margins"
                params = {"mode": mode}
            
            return {
                "name": attack_id,
                "type": attack_id,
                "params": params
            }
    
    # Check if it's a preset
    for preset in COMBO_PRESETS:
        if preset["id"] == attack_id:
            if "advanced_attacks" in preset:
                # This is a mixed preset with both basic and advanced attacks
                return {
                    "name": preset["id"],
                    "type": "mixed_combo",
                    "params": {
                        "basic_attacks": preset.get("basic_attacks", []),
                        "advanced_attacks": preset.get("advanced_attacks", [])
                    }
                }
            else:
                # This is a basic combo preset
                return {
                    "name": preset["id"],
                    "type": "combo",
                    "params": {
                        "sub_attacks": preset.get("attacks", [])
                    }
                }
    
    # If we get here, the attack ID wasn't found
    print(f"Error: Attack '{attack_id}' not found")
    return {"name": "none", "type": "none", "params": {}}

def apply_attack(template_path: str, output_name: str, attack_config: Dict[str, Any], context_level: int = 2) -> Optional[str]:
    """Apply the configured attack to the template and generate PDF"""
    attack_type = attack_config.get("type", "none")
    
    if attack_type == "none":
        print("No attack selected.")
        return None
    
    # Create output filename
    output_path = f"{output_name}.tex"
    
    # Handle mixed combo attacks (combining basic and advanced attacks)
    if attack_type == "mixed_combo":
        # First apply basic attacks
        basic_attacks = attack_config.get("params", {}).get("basic_attacks", [])
        if basic_attacks:
            # Create a temporary file for the basic attack result
            temp_file = tempfile.NamedTemporaryFile(suffix=".tex", delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # Apply basic attacks
            basic_config = {
                "name": "basic_combo",
                "type": "combo",
                "params": {
                    "sub_attacks": basic_attacks
                }
            }
            
            basic_result = create_exam_variant(
                template_path=template_path,
                output_name=temp_path[:-4],  # Remove .tex extension
                attack_params=basic_config,
                context_level=context_level
            )
            
            if not basic_result:
                print("Failed to apply basic attacks")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return None
            
            # Now apply advanced attacks using the result as the template
            advanced_attacks = attack_config.get("params", {}).get("advanced_attacks", [])
            if advanced_attacks:
                # Apply each advanced attack in sequence
                current_template = temp_path
                for adv_attack in advanced_attacks:
                    advanced_result = create_advanced_attack_variant(
                        current_template,
                        output_path,
                        adv_attack
                    )
                    
                    if not advanced_result:
                        print(f"Failed to apply advanced attack: {adv_attack['type']}")
                        # Continue with next attack
                    
                    # Update current template for next attack
                    current_template = output_path
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
            # Compile the final result
            compile_result = compile_tex(output_path)
            if compile_result:
                return f"{output_name}.pdf"
            else:
                return None
            
        else:
            # Only advanced attacks
            advanced_attacks = attack_config.get("params", {}).get("advanced_attacks", [])
            if not advanced_attacks:
                print("No attacks specified in mixed combo")
                return None
            
            # Apply each advanced attack in sequence
            current_template = template_path
            for adv_attack in advanced_attacks:
                advanced_result = create_advanced_attack_variant(
                    current_template,
                    output_path,
                    adv_attack
                )
                
                if not advanced_result:
                    print(f"Failed to apply advanced attack: {adv_attack['type']}")
                    # Continue with next attack
                
                # Update current template for next attack
                current_template = output_path
            
            # Compile the final result
            compile_result = compile_tex(output_path)
            if compile_result:
                return f"{output_name}.pdf"
            else:
                return None
    
    # Handle advanced attacks
    elif attack_type in [attack["id"] for attack in ADVANCED_ATTACKS]:
        # Use advanced attacks module
        advanced_result = create_advanced_attack_variant(
            template_path,
            output_path,
            attack_config
        )
        
        if not advanced_result:
            print(f"Failed to apply advanced attack: {attack_type}")
            return None
        
        # Compile the result
        compile_result = compile_tex(output_path)
        if compile_result:
            return f"{output_name}.pdf"
        else:
            return None
    
    # Handle basic attacks (including regular combos)
    else:
        # Use the standard attack generator
        result = create_exam_variant(
            template_path=template_path,
            output_name=output_name,
            attack_params=attack_config,
            context_level=context_level
        )
        
        return result

def compile_tex(tex_path: str) -> bool:
    """Compile a LaTeX file using lualatex"""
    print(f"Compiling {tex_path}...")
    try:
        process = subprocess.run(
            ['/usr/local/texlive/2025/bin/universal-darwin/lualatex', '-interaction=nonstopmode', tex_path],
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            print(f"Successfully compiled {tex_path}")
            return True
        else:
            print(f"Error compiling {tex_path}")
            print(process.stderr[-500:])  # Print the last part of stderr
            return False
    except Exception as e:
        print(f"Exception during compilation: {e}")
        return False

def analyze_template(template_path: str):
    """Analyze a template and suggest attacks"""
    try:
        with open(template_path, 'r') as f:
            content = f.read()
        
        analyzer = DocumentAnalyzer(content)
        subject = analyzer.get_subject_hint()
        
        print("\n=== TEMPLATE ANALYSIS ===")
        print(f"Subject detected: {subject}")
        print(f"Has figures: {analyzer.has_figures}")
        print(f"Has complex math: {analyzer.has_complex_math}")
        print(f"Math environments: {len(analyzer.math_environments)}")
        print(f"Math expressions: {len(analyzer.math_expressions)}")
        
        print("\n=== SUGGESTED ATTACKS ===")
        
        if analyzer.has_figures:
            print("- Template contains figures. Recommended:")
            print("  * Background texture with low density")
            print("  * Light watermark")
            print("  * Avoid heavy kerning that might affect image captions")
        
        if analyzer.has_complex_math:
            print("- Template has complex math. Recommended:")
            print("  * Math font mixing")
            print("  * Symbol confusion")
            print("  * Targeted kerning on specific expressions")
        
        if subject != "general_math":
            print(f"- Subject-specific attacks for {subject}:")
            if subject == "calculus":
                print("  * Watermark with calculus symbols (e.g., f'(x), ∫)")
                print("  * Target derivative and integral symbols")
            elif subject == "linear_algebra":
                print("  * Target matrix environments")
                print("  * Use vector symbols in watermarks")
            elif subject == "discrete_math":
                print("  * Target set notation and logical symbols")
            elif subject == "machine_learning":
                print("  * Target gradient and vector notation")
        
        # Suggest attack targets
        targets = analyzer.get_target_math_for_attacks()
        if targets:
            print("\n=== SUGGESTED KERNING TARGETS ===")
            for i, target in enumerate(targets):
                print(f"{i+1}. {target}")
        
        print("\nBased on this analysis, recommended configuration:")
        if analyzer.has_figures and analyzer.has_complex_math:
            print("- Use 'medium_protection' preset with context level 3")
        elif analyzer.has_complex_math:
            print("- Use 'strong_protection' preset with context level 2")
        elif analyzer.has_figures:
            print("- Use 'light_protection' preset with context level 1")
        else:
            print("- Use 'extreme_protection' preset with context level 2")
            
    except Exception as e:
        print(f"Error analyzing template: {e}")

def save_config(attack_config: Dict[str, Any], filename: str):
    """Save attack configuration to a file"""
    try:
        with open(filename, 'w') as f:
            json.dump(attack_config, f, indent=2)
        print(f"Configuration saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False

def load_config(filename: str) -> Dict[str, Any]:
    """Load attack configuration from a file"""
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        print(f"Configuration loaded from {filename}")
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {"name": "none", "type": "none", "params": {}}

def main():
    parser = argparse.ArgumentParser(description="Configure and apply AI-resistant attacks to LaTeX exams")
    parser.add_argument("--template", type=str, help="Path to LaTeX template file")
    parser.add_argument("--output", type=str, help="Output filename (without extension)")
    parser.add_argument("--attack", type=str, help="Attack ID to apply")
    parser.add_argument("--level", type=int, default=2, choices=[0, 1, 2, 3],
                        help="Context awareness level (0-3)")
    parser.add_argument("--list", action="store_true", help="List available attacks")
    parser.add_argument("--analyze", type=str, help="Analyze a template and suggest attacks")
    parser.add_argument("--save-config", type=str, help="Save attack configuration to file")
    parser.add_argument("--load-config", type=str, help="Load attack configuration from file")
    
    args = parser.parse_args()
    
    # List attacks
    if args.list:
        list_attacks()
        return
    
    # Analyze template
    if args.analyze:
        analyze_template(args.analyze)
        return
    
    # Interactive mode if no specific arguments are provided
    if not args.template or not args.output or not args.attack and not args.load_config:
        print("=== AI-Resistant Exam Attack Configurator ===")
        
        # Get template path
        template_path = args.template
        while not template_path or not os.path.exists(template_path):
            template_path = input("Template LaTeX file: ")
            if not os.path.exists(template_path):
                print(f"File not found: {template_path}")
        
        # Analyze template
        analyze_template(template_path)
        
        # Get output name
        output_name = args.output or input("Output filename (without extension): ")
        
        # Get context level
        context_level = args.level
        if not args.level:
            level_input = input("Context awareness level (0-3) [2]: ") or "2"
            context_level = int(level_input)
        
        # Choose attack
        list_attacks()
        attack_id = args.attack
        while not attack_id:
            attack_id = input("\nSelect attack ID: ")
        
        # Configure attack
        attack_config = configure_attack(attack_id, context_level)
        
        # Save configuration if requested
        save_path = input("Save configuration to file? (leave empty to skip): ")
        if save_path:
            save_config(attack_config, save_path)
        
        # Apply attack
        result = apply_attack(template_path, output_name, attack_config, context_level)
        
        if result:
            print(f"\nSuccess! Generated: {result}")
        else:
            print("\nFailed to generate PDF.")
            
    else:
        # Non-interactive mode
        template_path = args.template
        output_name = args.output
        
        # Load or configure attack
        attack_config = None
        if args.load_config:
            attack_config = load_config(args.load_config)
        else:
            attack_config = configure_attack(args.attack, args.level)
        
        # Save configuration if requested
        if args.save_config:
            save_config(attack_config, args.save_config)
        
        # Apply attack
        result = apply_attack(template_path, output_name, attack_config, args.level)
        
        if result:
            print(f"Success! Generated: {result}")
        else:
            print("Failed to generate PDF.")

if __name__ == "__main__":
    main()
