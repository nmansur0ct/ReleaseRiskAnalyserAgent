#!/usr/bin/env python3
"""

Script to update all LLM integration patterns to use the new llm_client.
"""

import re

def update_llm_patterns(file_path):
    """Update llm_manager.generate_with_fallback patterns"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern 1: await llm_manager.generate_with_fallback(prompt, provider)
    pattern1 = r'await llm_manager\.generate_with_fallback\(([^)]+)\)'
    replacement1 = lambda m: f'llm_client.call_llm({m.group(1).split(",")[0].strip()})'
    
    content = re.sub(pattern1, replacement1, content)
    
    # Pattern 2: llm_result['success'] -> llm_result.get('success', False)
    content = content.replace("llm_result['success']", "llm_result.get('success', False)")
    
    # Pattern 3: llm_result['response'] -> llm_result.get('response', '')
    content = content.replace("llm_result['response']", "llm_result.get('response', '')")
    
    with open(file_path, 'w') as f:
        f.write(content)

# Test the patterns
if __name__ == "__main__":
    print("LLM pattern update script ready")