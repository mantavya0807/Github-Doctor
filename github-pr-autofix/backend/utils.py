#!/usr/bin/env python3
"""
Enhanced utility functions with AI fix integration
Contains your existing brilliant detection + new AI-powered fixes
"""

import re
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Import the AI fix service
try:
    from gemini_fix_service import get_ai_fix_service
    AI_FIXES_AVAILABLE = True
except ImportError:
    AI_FIXES_AVAILABLE = False
    print("AI fix service not available - using rule-based fixes only")

def utc_now():
    """Get current UTC time in a timezone-aware way"""
    return datetime.now(timezone.utc)

# Your existing brilliant detection patterns (keeping them all!)
SECURITY_PATTERNS = {
    'api_keys': [
        (r'api[_-]?key["\']?\s*[:=]\s*["\']([^"\']{8,})["\']', 'CRITICAL', 'API Key Exposure'),
        (r'secret[_-]?key["\']?\s*[:=]\s*["\']([^"\']{8,})["\']', 'CRITICAL', 'Secret Key Exposure'),
        (r'access[_-]?token["\']?\s*[:=]\s*["\']([^"\']{10,})["\']', 'CRITICAL', 'Access Token Exposure'),
        (r'auth[_-]?token["\']?\s*[:=]\s*["\']([^"\']{10,})["\']', 'CRITICAL', 'Auth Token Exposure'),
        (r'client[_-]?secret["\']?\s*[:=]\s*["\']([^"\']{10,})["\']', 'CRITICAL', 'Client Secret Exposure'),
    ],
    'passwords': [
        (r'password["\']?\s*[:=]\s*["\']([^"\']{6,})["\']', 'CRITICAL', 'Password Hardcoded'),
        (r'passwd["\']?\s*[:=]\s*["\']([^"\']{6,})["\']', 'CRITICAL', 'Password Hardcoded'),
        (r'pwd["\']?\s*[:=]\s*["\']([^"\']{6,})["\']', 'HIGH', 'Password Variable'),
        (r'pass["\']?\s*[:=]\s*["\']([^"\']{6,})["\']', 'HIGH', 'Password Field'),
    ],
    'cloud_keys': [
        (r'sk_[a-zA-Z0-9]{24,}', 'CRITICAL', 'Stripe Secret Key'),
        (r'pk_[a-zA-Z0-9]{24,}', 'HIGH', 'Stripe Public Key'),
        (r'rk_[a-zA-Z0-9]{24,}', 'CRITICAL', 'Stripe Restricted Key'),
        (r'AKIA[0-9A-Z]{16}', 'CRITICAL', 'AWS Access Key ID'),
        (r'[0-9a-zA-Z/+]{40}', 'HIGH', 'AWS Secret Access Key (Potential)'),
        (r'ghp_[A-Za-z0-9]{36}', 'CRITICAL', 'GitHub Personal Access Token'),
        (r'github_pat_[A-Za-z0-9]{22,}', 'CRITICAL', 'GitHub Fine-grained Token'),
        (r'gho_[A-Za-z0-9]{36}', 'HIGH', 'GitHub OAuth Token'),
        (r'ghu_[A-Za-z0-9]{36}', 'HIGH', 'GitHub User Token'),
        (r'ya29\.[0-9A-Za-z\-_]+', 'CRITICAL', 'Google OAuth Access Token'),
        (r'AIza[0-9A-Za-z\-_]{35}', 'HIGH', 'Google API Key'),
        (r'[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com', 'HIGH', 'Google OAuth Client ID'),
    ],
    'database_urls': [
        (r'mongodb://[^"\s]+', 'HIGH', 'MongoDB Connection String'),
        (r'postgresql://[^"\s]+', 'HIGH', 'PostgreSQL Connection String'),
        (r'mysql://[^"\s]+', 'HIGH', 'MySQL Connection String'),
        (r'redis://[^"\s]+', 'MEDIUM', 'Redis Connection String'),
        (r'sqlite:///[^"\s]+', 'MEDIUM', 'SQLite Database Path'),
    ],
    'jwt_secrets': [
        (r'jwt[_-]?secret["\']?\s*[:=]\s*["\']([^"\']{10,})["\']', 'CRITICAL', 'JWT Secret Key'),
        (r'signing[_-]?key["\']?\s*[:=]\s*["\']([^"\']{10,})["\']', 'HIGH', 'Signing Key'),
        (r'encryption[_-]?key["\']?\s*[:=]\s*["\']([^"\']{10,})["\']', 'CRITICAL', 'Encryption Key'),
    ],
    'crypto_keys': [
        (r'-----BEGIN[^-]+PRIVATE KEY-----', 'CRITICAL', 'Private Key'),
        (r'-----BEGIN CERTIFICATE-----', 'MEDIUM', 'Certificate'),
        (r'-----BEGIN RSA PRIVATE KEY-----', 'CRITICAL', 'RSA Private Key'),
        (r'-----BEGIN DSA PRIVATE KEY-----', 'CRITICAL', 'DSA Private Key'),
        (r'-----BEGIN EC PRIVATE KEY-----', 'CRITICAL', 'EC Private Key'),
    ],
    'social_media': [
        (r'twitter[_-]?api[_-]?key["\']?\s*[:=]\s*["\']([^"\']+)["\']', 'HIGH', 'Twitter API Key'),
        (r'facebook[_-]?app[_-]?secret["\']?\s*[:=]\s*["\']([^"\']+)["\']', 'HIGH', 'Facebook App Secret'),
        (r'linkedin[_-]?client[_-]?secret["\']?\s*[:=]\s*["\']([^"\']+)["\']', 'HIGH', 'LinkedIn Client Secret'),
    ],
    'email_services': [
        (r'sendgrid[_-]?api[_-]?key["\']?\s*[:=]\s*["\']([^"\']+)["\']', 'HIGH', 'SendGrid API Key'),
        (r'mailgun[_-]?api[_-]?key["\']?\s*[:=]\s*["\']([^"\']+)["\']', 'HIGH', 'Mailgun API Key'),
        (r'ses[_-]?access[_-]?key["\']?\s*[:=]\s*["\']([^"\']+)["\']', 'HIGH', 'AWS SES Access Key'),
    ]
}

# Debug Statement Patterns
DEBUG_PATTERNS = {
    'python': [
        (r'print\s*\([^)]*\)', 'MEDIUM', 'Print Statement'),
        (r'pprint\s*\([^)]*\)', 'MEDIUM', 'Pretty Print Statement'),
        (r'logging\.debug\s*\([^)]*\)', 'LOW', 'Debug Logging'),
        (r'breakpoint\s*\(\)', 'HIGH', 'Breakpoint'),
        (r'import\s+pdb.*pdb\.set_trace\(\)', 'HIGH', 'PDB Debugger'),
        (r'import\s+ipdb.*ipdb\.set_trace\(\)', 'HIGH', 'IPDB Debugger'),
        (r'__import__\(["\']pdb["\']\)', 'HIGH', 'Dynamic PDB Import'),
        (r'input\s*\([^)]*\)', 'LOW', 'Input Statement (Debug)'),
    ],
    'javascript': [
        (r'console\.log\s*\([^)]*\)', 'MEDIUM', 'Console Log'),
        (r'console\.debug\s*\([^)]*\)', 'MEDIUM', 'Console Debug'),
        (r'console\.warn\s*\([^)]*\)', 'LOW', 'Console Warning'),
        (r'console\.error\s*\([^)]*\)', 'LOW', 'Console Error'),
        (r'console\.info\s*\([^)]*\)', 'LOW', 'Console Info'),
        (r'console\.trace\s*\([^)]*\)', 'MEDIUM', 'Console Trace'),
        (r'debugger\s*;?', 'HIGH', 'Debugger Statement'),
        (r'alert\s*\([^)]*\)', 'MEDIUM', 'Alert Statement'),
    ],
    'typescript': [
        (r'console\.log\s*\([^)]*\)', 'MEDIUM', 'Console Log'),
        (r'console\.debug\s*\([^)]*\)', 'MEDIUM', 'Console Debug'),
        (r'debugger\s*;?', 'HIGH', 'Debugger Statement'),
    ],
    'general': [
        (r'#\s*TODO[:\s].*', 'LOW', 'TODO Comment'),
        (r'#\s*FIXME[:\s].*', 'MEDIUM', 'FIXME Comment'),
        (r'#\s*HACK[:\s].*', 'HIGH', 'HACK Comment'),
        (r'#\s*XXX[:\s].*', 'MEDIUM', 'XXX Comment'),
        (r'#\s*BUG[:\s].*', 'HIGH', 'BUG Comment'),
        (r'//\s*TODO[:\s].*', 'LOW', 'TODO Comment'),
        (r'//\s*FIXME[:\s].*', 'MEDIUM', 'FIXME Comment'),
        (r'//\s*HACK[:\s].*', 'HIGH', 'HACK Comment'),
    ]
}

# Code Quality Patterns
CODE_QUALITY_PATTERNS = {
    'python': [
        (r'except\s*:', 'MEDIUM', 'Bare Except Clause'),
        (r'exec\s*\(', 'HIGH', 'Exec Statement (Security Risk)'),
        (r'eval\s*\(', 'HIGH', 'Eval Statement (Security Risk)'),
        (r'import\s+\*', 'MEDIUM', 'Wildcard Import'),
        (r'global\s+\w+', 'LOW', 'Global Variable Usage'),
        (r'def\s+\w+\([^)]*\):\s*pass', 'LOW', 'Empty Function'),
        (r'class\s+\w+[^:]*:\s*pass', 'LOW', 'Empty Class'),
        (r'if\s+True\s*:', 'LOW', 'Hardcoded True Condition'),
        (r'while\s+True\s*:', 'LOW', 'Infinite Loop'),
    ],
    'javascript': [
        (r'eval\s*\(', 'HIGH', 'Eval Usage (Security Risk)'),
        (r'document\.write\s*\(', 'MEDIUM', 'Document.write Usage'),
        (r'innerHTML\s*=', 'MEDIUM', 'Direct innerHTML Assignment'),
        (r'setTimeout\s*\(\s*["\'][^"\']*["\']', 'MEDIUM', 'setTimeout with String'),
        (r'setInterval\s*\(\s*["\'][^"\']*["\']', 'MEDIUM', 'setInterval with String'),
        (r'var\s+\w+', 'LOW', 'Var Declaration (Use let/const)'),
        (r'==\s*null|null\s*==', 'LOW', 'Loose Null Comparison'),
        (r'==\s*undefined|undefined\s*==', 'LOW', 'Loose Undefined Comparison'),
    ],
    'sql': [
        (r'["\'][^"\']*\+[^"\']*["\']', 'HIGH', 'Potential SQL Injection'),
        (r'SELECT\s+\*\s+FROM', 'MEDIUM', 'SELECT * Usage'),
        (r'DROP\s+TABLE', 'CRITICAL', 'DROP TABLE Statement'),
        (r'DELETE\s+FROM.*WHERE', 'MEDIUM', 'DELETE Statement'),
        (r'UPDATE.*SET.*WHERE', 'MEDIUM', 'UPDATE Statement'),
    ]
}

# Performance Patterns
PERFORMANCE_PATTERNS = {
    'python': [
        (r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\([^)]+\)\s*\)', 'MEDIUM', 'Inefficient Range Loop'),
        (r'\+\s*=.*["\']', 'LOW', 'String Concatenation in Loop (Potential)'),
        (r'time\.sleep\s*\(\s*[0-9]+\s*\)', 'LOW', 'Hard-coded Sleep'),
        (r'\.append\s*\([^)]*\)\s*for\s+', 'LOW', 'List Comprehension Opportunity'),
    ],
    'javascript': [
        (r'document\.getElementById', 'LOW', 'DOM Query (Consider Caching)'),
        (r'for\s*\(\s*var\s+\w+\s*=\s*0.*\.length', 'LOW', 'Length Property in Loop'),
        (r'setInterval\s*\([^,]+,\s*[0-9]+\s*\)', 'MEDIUM', 'Frequent Interval'),
        (r'setTimeout\s*\([^,]+,\s*0\s*\)', 'LOW', 'setTimeout with 0ms'),
    ]
}

def calculate_security_score(issues):
    """Calculate security score based on issues found (0-100)"""
    score = 100
    severity_weights = {'CRITICAL': 25, 'HIGH': 15, 'MEDIUM': 8, 'LOW': 3}
    
    for issue in issues:
        severity = issue.get('severity', 'LOW')
        score -= severity_weights.get(severity, 3)
    
    return max(0, score)

def categorize_issues(issues):
    """Categorize issues by type and severity"""
    categories = {
        'security': {'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': []},
        'debug': {'HIGH': [], 'MEDIUM': [], 'LOW': []},
        'quality': {'HIGH': [], 'MEDIUM': [], 'LOW': []},
        'performance': {'MEDIUM': [], 'LOW': []}
    }
    
    for issue in issues:
        issue_type = issue.get('category', 'quality')
        severity = issue.get('severity', 'LOW')
        
        if issue_type in categories and severity in categories[issue_type]:
            categories[issue_type][severity].append(issue)
    
    return categories

def get_fix_suggestions(issue):
    """Get basic fix suggestions for each issue type"""
    suggestions = {
        'secret_exposure': {
            'immediate': 'Remove the hardcoded secret immediately',
            'solution': 'Use environment variables: os.getenv("SECRET_NAME")',
            'example': 'api_key = os.getenv("API_KEY")',
            'security_impact': 'CRITICAL - Exposed secrets can lead to unauthorized access'
        },
        'debug_statement': {
            'immediate': 'Remove or comment out debug statements',
            'solution': 'Use proper logging with configurable levels',
            'example': 'logger.debug("Debug message") instead of print()',
            'security_impact': 'LOW - May expose sensitive information in logs'
        },
        'code_quality': {
            'immediate': 'Review and refactor the flagged code',
            'solution': 'Follow language-specific best practices',
            'example': 'Use specific exception handling instead of bare except',
            'security_impact': 'MEDIUM - Poor code quality can introduce vulnerabilities'
        },
        'performance': {
            'immediate': 'Optimize the identified performance bottleneck',
            'solution': 'Use more efficient algorithms or data structures',
            'example': 'Cache DOM queries or use list comprehensions',
            'security_impact': 'LOW - Performance issues can lead to DoS vulnerabilities'
        }
    }
    
    issue_type = issue.get('type', 'code_quality')
    return suggestions.get(issue_type, suggestions['code_quality'])

def analyze_code_content(code_content, file_extension):
    """Your existing brilliant analysis function - keeping it unchanged!"""
    issues = []
    
    # Security Analysis
    for category, patterns in SECURITY_PATTERNS.items():
        for pattern, severity, description in patterns:
            try:
                matches = re.finditer(pattern, code_content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_number = code_content[:match.start()].count('\n') + 1
                    issues.append({
                        'type': 'secret_exposure',
                        'category': 'security',
                        'subcategory': category,
                        'line': line_number,
                        'column': match.start() - code_content.rfind('\n', 0, match.start()) - 1,
                        'severity': severity,
                        'message': description,
                        'match': match.group()[:100] + '...' if len(match.group()) > 100 else match.group(),
                        'fix_available': True,
                        'confidence': 'HIGH' if severity in ['CRITICAL', 'HIGH'] else 'MEDIUM'
                    })
            except re.error:
                continue
    
    # Debug Statement Analysis
    debug_patterns = DEBUG_PATTERNS.get(file_extension, [])
    debug_patterns.extend(DEBUG_PATTERNS.get('general', []))
    
    for pattern, severity, description in debug_patterns:
        try:
            matches = re.finditer(pattern, code_content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_number = code_content[:match.start()].count('\n') + 1
                issues.append({
                    'type': 'debug_statement',
                    'category': 'debug',
                    'subcategory': 'development_artifacts',
                    'line': line_number,
                    'column': match.start() - code_content.rfind('\n', 0, match.start()) - 1,
                    'severity': severity,
                    'message': description,
                    'match': match.group().strip(),
                    'fix_available': True,
                    'confidence': 'HIGH'
                })
        except re.error:
            continue
    
    # Code Quality Analysis
    quality_patterns = CODE_QUALITY_PATTERNS.get(file_extension, [])
    
    for pattern, severity, description in quality_patterns:
        try:
            matches = re.finditer(pattern, code_content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_number = code_content[:match.start()].count('\n') + 1
                issues.append({
                    'type': 'code_quality',
                    'category': 'quality',
                    'subcategory': 'best_practices',
                    'line': line_number,
                    'column': match.start() - code_content.rfind('\n', 0, match.start()) - 1,
                    'severity': severity,
                    'message': description,
                    'match': match.group().strip(),
                    'fix_available': True,
                    'confidence': 'MEDIUM'
                })
        except re.error:
            continue
    
    # Performance Analysis
    perf_patterns = PERFORMANCE_PATTERNS.get(file_extension, [])
    
    for pattern, severity, description in perf_patterns:
        try:
            matches = re.finditer(pattern, code_content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_number = code_content[:match.start()].count('\n') + 1
                issues.append({
                    'type': 'performance',
                    'category': 'performance',
                    'subcategory': 'optimization',
                    'line': line_number,
                    'column': match.start() - code_content.rfind('\n', 0, match.start()) - 1,
                    'severity': severity,
                    'message': description,
                    'match': match.group().strip(),
                    'fix_available': True,
                    'confidence': 'MEDIUM'
                })
        except re.error:
            continue
    
    return issues

# NEW: Enhanced functions with AI integration
def generate_intelligent_fixes(issues: List[Dict[str, Any]], code_content: str = "", file_extension: str = "py") -> List[Dict[str, Any]]:
    """
    Generate AI-powered fixes for detected issues
    Falls back to rule-based fixes if AI is unavailable
    """
    if not issues:
        return []
    
    if AI_FIXES_AVAILABLE:
        try:
            ai_service = get_ai_fix_service()
            
            if ai_service.is_configured():
                print(f"🤖 Generating AI fixes for {len(issues)} issues...")
                fixes = ai_service.batch_generate_fixes(issues, code_content, file_extension)
                
                # Add AI fix status to each issue
                for i, fix in enumerate(fixes):
                    if i < len(issues):
                        issues[i]['ai_fix_available'] = True
                        issues[i]['ai_fix'] = fix
                
                return fixes
            else:
                print("⚠️  Gemini API not configured - using rule-based fixes")
        except Exception as e:
            print(f"❌ AI fix generation failed: {str(e)} - using rule-based fixes")
    
    # Fallback to rule-based fixes
    return generate_rule_based_fixes(issues, file_extension)

def generate_rule_based_fixes(issues: List[Dict[str, Any]], file_extension: str = "py") -> List[Dict[str, Any]]:
    """Generate fixes using your existing rule-based system"""
    fixes = []
    
    for issue in issues:
        issue_type = issue.get('type', '')
        original_code = issue.get('match', '')
        line = issue.get('line', 0)
        
        if issue_type == 'secret_exposure':
            var_match = re.search(r'(\w+)\s*[=:]\s*["\']', original_code)
            var_name = var_match.group(1).upper() if var_match else 'SECRET_KEY'
            
            if file_extension in ['py']:
                fixed_code = f"{var_match.group(1) if var_match else 'secret'} = os.getenv('{var_name}')"
            elif file_extension in ['js', 'ts', 'jsx', 'tsx']:
                fixed_code = f"const {var_match.group(1) if var_match else 'secret'} = process.env.{var_name}"
            else:
                fixed_code = f"// Replace with environment variable: {var_name}"
            
            fixes.append({
                "original_code": original_code,
                "fixed_code": fixed_code,
                "explanation": f"Replace hardcoded secret with environment variable {var_name}",
                "env_vars_needed": [var_name],
                "confidence": "HIGH",
                "fix_type": "rule_based",
                "line": line,
                "applied": False
            })
        
        elif issue_type == 'debug_statement':
            if 'print(' in original_code:
                fixes.append({
                    "original_code": original_code,
                    "fixed_code": f"# {original_code}  # TODO: Remove debug statement",
                    "explanation": "Comment out debug print statement",
                    "env_vars_needed": [],
                    "confidence": "HIGH",
                    "fix_type": "rule_based",
                    "line": line,
                    "applied": False
                })
            elif 'console.log(' in original_code:
                fixes.append({
                    "original_code": original_code,
                    "fixed_code": f"// {original_code}  // TODO: Remove debug statement",
                    "explanation": "Comment out debug console.log statement",
                    "env_vars_needed": [],
                    "confidence": "HIGH",
                    "fix_type": "rule_based",
                    "line": line,
                    "applied": False
                })
        
        elif issue_type == 'code_quality':
            if 'except:' in original_code:
                fixes.append({
                    "original_code": original_code,
                    "fixed_code": original_code.replace('except:', 'except Exception as e:'),
                    "explanation": "Replace bare except with specific exception handling",
                    "env_vars_needed": [],
                    "confidence": "HIGH",
                    "fix_type": "rule_based",
                    "line": line,
                    "applied": False
                })
    
    return fixes

def apply_fixes_to_content(code_content: str, fixes: List[Dict[str, Any]]) -> tuple[str, int, List[str]]:
    """
    Apply fixes to code content and return results
    
    Returns:
        Tuple of (fixed_code, fixes_applied_count, env_vars_needed)
    """
    if not fixes:
        return code_content, 0, []
    
    # Use AI service if available
    if AI_FIXES_AVAILABLE:
        try:
            ai_service = get_ai_fix_service()
            fixed_code, fixes_applied = ai_service.apply_fixes_to_code(code_content, fixes)
            
            # Collect environment variables needed
            env_vars = []
            for fix in fixes:
                env_vars.extend(fix.get('env_vars_needed', []))
            
            return fixed_code, fixes_applied, list(set(env_vars))
        except Exception as e:
            print(f"Error applying AI fixes: {str(e)}")
    
    # Fallback to manual application
    lines = code_content.split('\n')
    fixes_applied = 0
    env_vars = []
    
    # Sort fixes by line number in descending order
    sorted_fixes = sorted(fixes, key=lambda x: x.get('line', 0), reverse=True)
    
    for fix in sorted_fixes:
        line_num = fix.get('line', 0) - 1
        original_code = fix.get('original_code', '')
        fixed_code = fix.get('fixed_code', '')
        
        if line_num >= 0 and line_num < len(lines) and original_code and fixed_code:
            if original_code.strip() in lines[line_num]:
                lines[line_num] = lines[line_num].replace(original_code.strip(), fixed_code.strip())
                fixes_applied += 1
                fix['applied'] = True
                env_vars.extend(fix.get('env_vars_needed', []))
    
    return '\n'.join(lines), fixes_applied, list(set(env_vars))

def create_env_file_content(env_vars: List[str]) -> str:
    """Create .env.example content from environment variables"""
    if not env_vars:
        return ""
    
    content = "# Environment Variables\n"
    content += "# Copy this file to .env and add your actual values\n\n"
    
    for var in sorted(env_vars):
        content += f"{var}=your_{var.lower()}_here\n"
    
    content += "\n# Add this file to your .gitignore!\n"
    return content

def get_gemini_status() -> Dict[str, Any]:
    """Get status of Gemini AI integration"""
    if not AI_FIXES_AVAILABLE:
        return {
            "available": False,
            "configured": False,
            "status": "Service not imported",
            "fix_types": ["rule_based"]
        }
    
    try:
        ai_service = get_ai_fix_service()
        configured = ai_service.is_configured()
        
        return {
            "available": True,
            "configured": configured,
            "status": "Ready" if configured else "API key not configured",
            "fix_types": ["ai_generated", "rule_based"] if configured else ["rule_based"],
            "api_key_set": bool(os.getenv('GEMINI_API_KEY'))
        }
    except Exception as e:
        return {
            "available": False,
            "configured": False,
            "status": f"Error: {str(e)}",
            "fix_types": ["rule_based"]
        }