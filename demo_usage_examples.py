#!/usr/bin/env python3
"""
Simple Demo Usage Examples
Demonstrates how to use the modified simple_demo.py with different repository URLs
"""

import subprocess
import sys
import os

def run_demo_example(description, command):
    """Run a demo example with description"""
    print(f"\n{'='*80}")
    print(f" {description}")
    print(f" Command: {command}")
    print(f"{'='*80}")
    
    try:
        # Change to the project directory
        os.chdir("/Users/n0m08hp/ReleaseRiskAnalyserAgent")
        
        # Run the command
        result = subprocess.run(command.split(), capture_output=True, text=True, timeout=60)
        
        # Show first part of output
        if result.stdout:
            lines = result.stdout.split('\n')
            # Show first 30 lines to avoid overwhelming output
            for line in lines[:30]:
                print(line)
            if len(lines) > 30:
                print(f"... (output truncated, showing first 30 lines of {len(lines)} total)")
        
        if result.stderr:
            print(f" Errors: {result.stderr}")
        
        print(f" Exit code: {result.returncode}")
        
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out (60s limit)")
    except Exception as e:
        print(f" Error running command: {e}")

def main():
    """Demonstrate various usage patterns of the enhanced simple_demo.py"""
    
    print(" Release Risk Analyzer Agent - Command Line Demo Examples")
    print("="*80)
    print("This script demonstrates the enhanced simple_demo.py with command line arguments")
    
    # Example 1: Help message
    run_demo_example(
        "Display help information and usage examples",
        "python src/simple_demo.py --help"
    )
    
    # Example 2: Default repository
    print(f"\n Note: The following examples would run full analysis but are commented out")
    print(f"   to avoid overwhelming output. Uncomment to test:")
    print()
    
    examples = [
        ("Default repository analysis (TransactionPatterns)", 
         "python src/simple_demo.py"),
        
        ("Custom repository with limited PRs", 
         "python src/simple_demo.py --repo https://gecgithub01.walmart.com/n0m08hp/EntityResolution.git --limit 3"),
        
        ("Another repository with verbose logging", 
         "python src/simple_demo.py --repo https://github.com/user/repo.git --verbose --limit 2"),
        
        ("Analysis with maximum PRs", 
         "python src/simple_demo.py --repo https://gecgithub01.walmart.com/team/project.git --limit 10")
    ]
    
    for description, command in examples:
        print(f" {description}:")
        print(f"   {command}")
        print()
    
    print(" Key Features of Enhanced simple_demo.py:")
    print("="*60)
    print(" Command line argument support for repository URL")
    print(" Configurable PR fetch limit")
    print(" Verbose logging option")
    print(" Dynamic repository analysis")
    print(" Real-time PR fetching from specified repositories")
    print(" Agent-centric LLM analysis with Walmart LLM Gateway")
    print(" Comprehensive plugin framework evaluation")
    print(" Support for multiple Git providers (GitHub, GitHub Enterprise, GitLab)")
    
    print("\n Supported Repository Types:")
    print("-"*40)
    print(" GitHub: https://github.com/user/repo.git")
    print(" GitHub Enterprise: https://gecgithub01.walmart.com/team/project.git")
    print(" GitLab: https://gitlab.com/group/project.git")
    print(" Other Git providers (with appropriate configuration)")
    
    print("\n Environment Requirements:")
    print("-"*40)
    print(" Git access token configured in .env file")
    print(" Walmart LLM Gateway credentials")
    print(" Python environment with required dependencies")
    print(" Network access to target repositories")

if __name__ == "__main__":
    main()