# AI-Resistant Exam Framework

A comprehensive framework for creating math documents that resist AI-based processing while maintaining human readability.

## Overview

This project provides tools to apply adversarial modifications to LaTeX math documents, making them more resistant to AI-based analysis tools while remaining legible to human readers. The framework works across diverse math problem types, including calculus, linear algebra, discrete mathematics, complex analysis, and machine learning.

## Key Findings

Our research demonstrates that targeted adversarial attacks can significantly reduce Vision-Language Models' ability to process mathematical content while maintaining human readability:

- **Most Effective Attacks**: Combination attacks achieved up to 47.7% effectiveness in reducing model output
- **Task Sensitivity**: Higher-level reasoning tasks (solving, explanation) are more vulnerable than basic transcription
- **Model Differences**: Different models show distinct vulnerability patterns
- **Physical Testing**: Real-world printing and photography generally amplifies attack effectiveness

## Features

### Context-Aware Attacks

The framework offers four levels of context awareness:

- **Level 0:** Basic attacks with no document analysis
- **Level 1:** Image and figure-aware positioning of attacks
- **Level 2:** Math environment analysis and targeting
- **Level 3:** Full subject-specific customization

### Attack Types

#### Basic Attacks

- **Watermarks:** Background text or tiled math expressions
- **Textures:** Background patterns like dots, lines, or waves
- **Kerning:** Character spacing modifications in math expressions
- **Font Swaps:** Replacing specific symbols with different fonts
- **Background Colors:** Subtle coloration effects
- **Line Spacing:** Variable spacing between lines

#### Advanced Attacks

- **Math Font Mixing:** Using different fonts for different parts of equations
- **Symbol Confusion:** Replacing symbols with visually similar alternatives
- **Visual Noise Injection:** Adding subtle noise patterns
- **Symbol Substitution:** Replacing symbols with custom LaTeX commands
- **Invisible Characters:** Inserting zero-width spaces in expressions
- **Page Structure Manipulation:** Altering page layout and structure

### Tools

- **generalized_attack.py:** Core framework with context-aware attack generation
- **advanced_attacks.py:** Implementation of advanced attack techniques
- **attack_configurator.py:** User-friendly tool for configuring and applying attacks
- **comprehensive_test.py:** Tests attacks across different exam types
- **benchmark_attacks.py:** Evaluates attack effectiveness against AI models
- **run_generalized_experiment.py:** Orchestrates experiments across multiple attacks

## Getting Started

### Prerequisites

- TeX Live with LuaLaTeX
- Python 3.7+
- Required Python packages: see requirements.txt

### Installation

1. Clone this repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Basic Usage

#### Using the Attack Configurator (Original Framework)

```bash
python attack_configurator.py
```

This will guide you through an interactive process to:

1. Select a LaTeX template
2. Analyze the template to suggest appropriate attacks
3. Choose and configure attacks
4. Generate a protected PDF

#### Running the Most Effective Attacks (Recommended)

```bash
# Run the top attacks against an AI model
./run_top_attacks_experiment.sh

# Or specify options
./run_top_attacks_experiment.sh --model="claude-3.5-sonnet" --template="exam_template.tex"
```

#### Physical Testing Workflow

```bash
# Generate PDFs, guide through physical testing, and analyze results
./run_physical_attack_test.sh --model="gemma3:4b"
```

#### Using the Command Line (Advanced)

```bash
# Apply a basic attack
python generalized_attack.py --template ex1.tex --output protected_exam --attack watermark_tiled --level 2

# Run top attacks only
python run_top_attacks.py --template ex1.tex --log-file results.jsonl --model gemma3:4b

# Generate PDFs for physical testing
python generate_top_attack_pdfs.py --template ex1.tex --output-dir attack_pdfs

# Analyze results
python analyze_top_attacks.py --log-file results.jsonl
```

## Understanding Attack Levels

Each attack can be configured with different intensity levels:

- **Light Protection:** Subtle modifications with minimal impact on readability
- **Medium Protection:** Balanced approach that degrades AI performance while maintaining readability
- **Strong Protection:** Significant AI resistance with acceptable readability trade-offs
- **Extreme Protection:** Maximum protection using multiple attack types

## File Organization

### Original Framework
- **ex0.tex:** Original template with simple calculus problem
- **ex1.tex:** Enhanced template with diverse math problems
- **generalized_attack.py:** Context-aware attack framework
- **advanced_attacks.py:** Advanced attack techniques
- **attack_configurator.py:** User-friendly configuration tool
- **comprehensive_test.py:** Test framework
- **benchmark_attacks.py:** Attack effectiveness evaluation
- **run_generalized_experiment.py:** Experiment orchestration

### New Tools and Research
- **exam_attack_v3.py:** Enhanced attack implementation with new techniques
- **run_experiment_v3.py:** Improved experiment orchestration
- **run_top_attacks.py:** Script to run only the most effective attacks
- **generate_top_attack_pdfs.py:** Generate PDFs for physical testing
- **test_uploaded_images.py:** Test photos of printed attack PDFs
- **analyze_top_attacks.py:** Analyze effectiveness of top attacks
- **analyze_overnight_detailed.py:** Detailed analysis with baseline comparisons
- **run_top_attacks_experiment.sh:** End-to-end top attack testing
- **run_physical_attack_test.sh:** Physical testing workflow
- **ai_resistant_math_paper.tex:** Research paper summarizing findings

## Best Practices

1. **Start with Analysis:** Always analyze your document first to understand its structure
2. **Match Attacks to Content:** Use subject-specific attacks for best results
3. **Test with Multiple Models:** Different AI models have different vulnerabilities
4. **Balance Protection vs. Readability:** Ensure humans can still read the exam
5. **Use Combination Attacks:** Multiple subtle attacks often work better than one strong attack

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The project builds upon research in adversarial examples for vision models
- Thanks to all contributors and testers
