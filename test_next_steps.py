#!/usr/bin/env python3
# test_next_steps.py
#
# This script tests the newly developed next-step tools

import os
import subprocess
import time
import sys
from pathlib import Path

def print_header(message):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80)

def run_command(command, description):
    """Run a command and capture output"""
    print(f"\n> {description}")
    print(f"  $ {command}")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            print(f"  ✓ Success (took {elapsed:.2f} seconds)")
            if result.stdout and len(result.stdout) > 0:
                print("\n  Output:")
                # Limit output to 15 lines
                lines = result.stdout.strip().split("\n")
                if len(lines) > 15:
                    print("  " + "\n  ".join(lines[:10]))
                    print("  ... (output truncated) ...")
                    print("  " + "\n  ".join(lines[-5:]))
                else:
                    print("  " + "\n  ".join(lines))
            return True
        else:
            print(f"  ✗ Failed with exit code {result.returncode}")
            print("\n  Error output:")
            print("  " + "\n  ".join(result.stderr.strip().split("\n")))
            return False
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return False

def check_file(filepath):
    """Check if a file exists and show its size"""
    path = Path(filepath)
    if path.exists():
        size = path.stat().st_size
        print(f"  ✓ File exists: {filepath} ({size} bytes)")
        return True
    else:
        print(f"  ✗ File does not exist: {filepath}")
        return False

def main():
    print_header("Testing Next Steps Tools")
    
    # Define the test directory
    work_dir = "/Users/memo/Documents/act"
    os.chdir(work_dir)
    print(f"Working directory: {work_dir}")
    
    # 1. Test the generalized attack framework
    print_header("1. Testing generalized_attack.py")
    run_command(
        "python generalized_attack.py",
        "Running generalized attack script to test watermark with different context levels"
    )
    
    for level in range(4):
        check_file(f"test_variant_ex1_level{level}.pdf")
    
    # 2. Test advanced attacks
    print_header("2. Testing advanced_attacks.py")
    run_command(
        "python advanced_attacks.py",
        "Running advanced attacks script to test new attack types"
    )
    
    for i, attack in enumerate(["math_font_mixing", "symbol_confusion", "visual_noise_injection"]):
        check_file(f"advanced_attack_{i}_{attack}.tex")
    
    # 3. Test attack configurator in non-interactive mode
    print_header("3. Testing attack_configurator.py")
    run_command(
        "python attack_configurator.py --list",
        "Listing available attacks"
    )
    
    run_command(
        f"python attack_configurator.py --analyze {work_dir}/ex1.tex",
        "Analyzing ex1.tex template"
    )
    
    run_command(
        f"python attack_configurator.py --template {work_dir}/ex1.tex --output configurator_test --attack medium_protection --level 2",
        "Applying medium protection preset to ex1.tex"
    )
    
    check_file("configurator_test.pdf")
    
    # 4. Test comprehensive test script
    print_header("4. Testing comprehensive_test.py")
    run_command(
        "python comprehensive_test.py --quick-test",
        "Running comprehensive tests in quick mode"
    )
    
    # 5. Test benchmark script
    print_header("5. Testing benchmark_attacks.py")
    run_command(
        "python benchmark_attacks.py --sample",
        "Running benchmark with sample PDFs"
    )
    
    print_header("Test Summary")
    print("\nAll tests completed. Check the results above for any issues.")
    print("\nNext steps to take:")
    print("1. Fix any failed tests")
    print("2. Run full comprehensive tests on all exam types")
    print("3. Run benchmarks with different AI models")
    print("4. Refine attack parameters based on benchmark results")
    print("5. Document the most effective attacks for each exam type")

if __name__ == "__main__":
    main()
