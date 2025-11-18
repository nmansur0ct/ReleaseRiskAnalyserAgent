"""
Formatting utilities for Risk Agent Analyzer

Provides consistent formatting and output functions.
"""

from typing import List, Optional

def format_output(message: str, width: int = 80) -> str:
    """Format output message with consistent width"""
    return message.ljust(width)

def print_header(title: str, width: int = 80, char: str = "=") -> None:
    """Print a formatted header"""
    print(char * width)
    centered_title = title.center(width)
    print(centered_title)
    print(char * width)

def print_section_header(title: str, width: int = 80) -> None:
    """Print a section header with dashes"""
    print("\n" + title)
    print("-" * width)

def print_framework_header(repo_urls: List[str], pr_limit: int, output_dir: str, pr_state: str = "open") -> None:
    """Print the analysis framework header"""
    print_header("MULTI-REPOSITORY PR ANALYSIS FRAMEWORK")
    print(f" Total Repositories to Analyze: {len(repo_urls)}")
    print(f" PR State Filter: {pr_state.upper()}")
    print(f" PR Limit per Repository: {pr_limit}")
    print(f" Reports will be saved to: {output_dir}/")
    print("=" * 80)

def print_repository_header(repo_index: int, total_repos: int, repo_name: str) -> None:
    """Print repository analysis header"""
    print("\n" + "#" * 80)
    print(f" REPOSITORY {repo_index}/{total_repos}: {repo_name}")
    print("#" * 80)

def format_pr_summary(pr_number: int, title: str, author: str, changes_add: int, changes_del: int, 
                     files: int, comments: int, url: str) -> str:
    """Format PR summary for display"""
    return (f"  {pr_number}. PR #{pr_number}: {title}\n"
           f"      Author: {author}\n" 
           f"      Changes: +{changes_add} -{changes_del}\n"
           f"      Files: {files}\n"
           f"      Comments: {comments}\n"
           f"      URL: {url}")

def format_verdict(recommendation: str, confidence: float, risk_level: str, score: int) -> str:
    """Format analysis verdict for display"""
    return (f"Recommendation: {recommendation}\n"
           f"Confidence: {confidence}%\n"
           f"Risk Level: {risk_level}\n" 
           f"Overall Score: {score}/100")

def format_time_duration(seconds: float) -> str:
    """Format execution time for display"""
    if seconds < 60:
        return f"~{seconds:.1f} seconds"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"~{minutes}m {remaining_seconds:.1f}s"

def format_repository_metrics(approved: int, conditional: int, rejected: int,
                             low_risk: int, medium_risk: int, high_risk: int,
                             avg_confidence: float, avg_score: float) -> str:
    """Format repository assessment metrics"""
    return f"""AGGREGATE ANALYSIS RESULTS:
 Approved PRs: {approved}
 Conditional PRs: {conditional}
 Rejected PRs: {rejected}

RISK DISTRIBUTION:
 Low Risk: {low_risk} PRs
 Medium Risk: {medium_risk} PRs
 High Risk: {high_risk} PRs

QUALITY METRICS:
 Average Confidence: {avg_confidence:.1f}%
 Average Quality Score: {avg_score:.1f}/100"""