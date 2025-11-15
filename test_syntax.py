#!/usr/bin/env python3

# Test if f-string syntax works as expected
metrics = {
    'avg_confidence': 88.5,
    'avg_score': 92.1
}

test_string = f"""
Test Repository Assessment:
- Average Confidence: {metrics['avg_confidence']:.1f}%
- Average Quality Score: {metrics['avg_score']:.1f}/100
"""

print(test_string)
print("✅ Syntax test passed!")