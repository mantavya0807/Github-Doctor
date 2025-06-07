#!/usr/bin/env python3
"""
AI Fix Service using Google Gemini Free API
Integrates with existing detection system for intelligent code fixes
"""

import os
import requests
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class GeminiFixService:
    """AI-powered fix service using Google Gemini API"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY', '')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.fix_cache = {}  # Simple in-memory cache for fix suggestions
        
    def is_configured(self) -> bool:
        """Check if Gemini API is properly configured"""
        return bool(self.api_key and self.api_key != '')
    
    def generate_fix(self, issue: Dict[str, Any], code_context: str = "", file_extension: str = "py") -> Optional[Dict[str, Any]]:
        """
        Generate intelligent fix for a detected issue using Gemini
        
        Args:
            issue: Issue detected by your existing system
            code_context: Surrounding code for better context
            file_extension: File type for language-specific fixes
        
        Returns:
            Dict with fix details or None if fix couldn't be generated
        """
        if not self.is_configured():
            return self._fallback_fix(issue, file_extension)
        
        # Create cache key
        cache_key = f"{issue.get('type')}_{issue.get('severity')}_{hash(issue.get('match', ''))}"
        if cache_key in self.fix_cache:
            return self.fix_cache[cache_key]
        
        try:
            prompt = self._create_fix_prompt(issue, code_context, file_extension)
            response = self._call_gemini_api(prompt)
            
            if response:
                fix_result = self._parse_gemini_response(response, issue)
                # Cache the result
                self.fix_cache[cache_key] = fix_result
                return fix_result
            else:
                # Fallback to rule-based fixes
                return self._fallback_fix(issue, file_extension)
                
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return self._fallback_fix(issue, file_extension)
    
    def _create_fix_prompt(self, issue: Dict[str, Any], code_context: str, file_extension: str) -> str:
        """Create a detailed prompt for Gemini to generate fixes"""
        
        language_map = {
            'py': 'Python',
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'jsx': 'React JSX',
            'tsx': 'React TSX',
            'java': 'Java',
            'cpp': 'C++',
            'c': 'C',
            'php': 'PHP',
            'rb': 'Ruby',
            'go': 'Go',
            'cs': 'C#',
            'sql': 'SQL'
        }
        
        language = language_map.get(file_extension, file_extension.upper())
        issue_type = issue.get('type', 'unknown')
        severity = issue.get('severity', 'MEDIUM')
        message = issue.get('message', 'Code issue detected')
        problematic_code = issue.get('match', '')
        line_number = issue.get('line', 0)
        
        prompt = f"""You are a code security and quality expert. Fix this {language} code issue:

**Issue Details:**
- Type: {issue_type}
- Severity: {severity}
- Message: {message}
- Line: {line_number}
- Problematic Code: `{problematic_code}`

**Code Context:**
```{file_extension}
{code_context}
```

**Fix Requirements:**
1. Provide ONLY the fixed code snippet (no explanations)
2. Maintain the same functionality
3. Follow {language} best practices
4. Make minimal changes needed to fix the issue

**Specific Fix Guidelines:**
"""

        # Add specific guidelines based on issue type
        if issue_type == 'secret_exposure':
            prompt += """
- Replace hardcoded secrets with environment variables
- Use os.getenv() for Python or process.env for JavaScript
- Suggest appropriate environment variable names
- Add error handling for missing environment variables
"""
        elif issue_type == 'debug_statement':
            prompt += """
- Remove or replace debug statements with proper logging
- Use logging module for Python or console methods appropriately
- Keep any essential error handling
- Don't remove legitimate user-facing messages
"""
        elif issue_type == 'code_quality':
            prompt += """
- Fix syntax or logic issues
- Improve code structure and readability
- Add proper error handling where needed
- Follow language-specific conventions
"""
        elif issue_type == 'performance':
            prompt += """
- Optimize the code for better performance
- Reduce computational complexity where possible
- Use more efficient data structures or algorithms
- Maintain the same output/behavior
"""
        
        prompt += f"""
**Response Format (JSON):**
{{
    "fixed_code": "ONLY the corrected code snippet",
    "explanation": "Brief explanation of what was fixed",
    "env_vars_needed": ["LIST_OF_ENV_VARS"] (if applicable),
    "confidence": "HIGH|MEDIUM|LOW"
}}

Fix this issue now:"""
        
        return prompt
    
    def _call_gemini_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Make API call to Gemini"""
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,  # Low temperature for consistent fixes
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 1024,
                }
            }
            
            url = f"{self.base_url}?key={self.api_key}"
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Gemini API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Gemini API call failed: {str(e)}")
            return None
    
    def _parse_gemini_response(self, response: Dict[str, Any], original_issue: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gemini's response and extract fix information"""
        try:
            # Extract text from Gemini response
            candidates = response.get('candidates', [])
            if not candidates:
                return self._fallback_fix(original_issue)
            
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                return self._fallback_fix(original_issue)
            
            response_text = parts[0].get('text', '')
            
            # Try to parse JSON response
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    fix_data = json.loads(json_match.group())
                    
                    return {
                        "original_code": original_issue.get('match', ''),
                        "fixed_code": fix_data.get('fixed_code', ''),
                        "explanation": fix_data.get('explanation', 'AI-generated fix'),
                        "env_vars_needed": fix_data.get('env_vars_needed', []),
                        "confidence": fix_data.get('confidence', 'MEDIUM'),
                        "fix_type": "ai_generated",
                        "line": original_issue.get('line', 0),
                        "applied": False
                    }
            except json.JSONDecodeError:
                # If JSON parsing fails, extract fix from text
                pass
            
            # Fallback: extract fixed code from markdown code blocks
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', response_text, re.DOTALL)
            if code_blocks:
                return {
                    "original_code": original_issue.get('match', ''),
                    "fixed_code": code_blocks[0].strip(),
                    "explanation": "AI-suggested fix",
                    "env_vars_needed": [],
                    "confidence": "MEDIUM",
                    "fix_type": "ai_generated",
                    "line": original_issue.get('line', 0),
                    "applied": False
                }
            
            # Last resort: use the whole response as explanation
            return {
                "original_code": original_issue.get('match', ''),
                "fixed_code": "",
                "explanation": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                "env_vars_needed": [],
                "confidence": "LOW",
                "fix_type": "ai_suggestion",
                "line": original_issue.get('line', 0),
                "applied": False
            }
            
        except Exception as e:
            print(f"Error parsing Gemini response: {str(e)}")
            return self._fallback_fix(original_issue)
    
    def _fallback_fix(self, issue: Dict[str, Any], file_extension: str = "py") -> Dict[str, Any]:
        """Fallback to rule-based fixes when AI is unavailable"""
        issue_type = issue.get('type', '')
        original_code = issue.get('match', '')
        line = issue.get('line', 0)
        
        if issue_type == 'secret_exposure':
            # Extract potential variable name
            var_match = re.search(r'(\w+)\s*[=:]\s*["\']', original_code)
            var_name = var_match.group(1).upper() if var_match else 'SECRET_KEY'
            
            if file_extension in ['py']:
                fixed_code = f"{var_match.group(1) if var_match else 'secret'} = os.getenv('{var_name}')"
            elif file_extension in ['js', 'ts', 'jsx', 'tsx']:
                fixed_code = f"const {var_match.group(1) if var_match else 'secret'} = process.env.{var_name}"
            else:
                fixed_code = f"// Replace with environment variable: {var_name}"
            
            return {
                "original_code": original_code,
                "fixed_code": fixed_code,
                "explanation": f"Replace hardcoded secret with environment variable {var_name}",
                "env_vars_needed": [var_name],
                "confidence": "HIGH",
                "fix_type": "rule_based",
                "line": line,
                "applied": False
            }
        
        elif issue_type == 'debug_statement':
            if 'print(' in original_code:
                return {
                    "original_code": original_code,
                    "fixed_code": f"# {original_code}  # TODO: Remove debug statement",
                    "explanation": "Comment out debug print statement",
                    "env_vars_needed": [],
                    "confidence": "HIGH",
                    "fix_type": "rule_based",
                    "line": line,
                    "applied": False
                }
            elif 'console.log(' in original_code:
                return {
                    "original_code": original_code,
                    "fixed_code": f"// {original_code}  // TODO: Remove debug statement",
                    "explanation": "Comment out debug console.log statement",
                    "env_vars_needed": [],
                    "confidence": "HIGH",
                    "fix_type": "rule_based",
                    "line": line,
                    "applied": False
                }
        
        elif issue_type == 'code_quality':
            if 'except:' in original_code:
                return {
                    "original_code": original_code,
                    "fixed_code": original_code.replace('except:', 'except Exception as e:'),
                    "explanation": "Replace bare except with specific exception handling",
                    "env_vars_needed": [],
                    "confidence": "HIGH",
                    "fix_type": "rule_based",
                    "line": line,
                    "applied": False
                }
        
        # Generic fallback
        return {
            "original_code": original_code,
            "fixed_code": "",
            "explanation": f"Manual review needed for {issue_type} issue",
            "env_vars_needed": [],
            "confidence": "LOW",
            "fix_type": "manual_review",
            "line": line,
            "applied": False
        }
    
    def apply_fixes_to_code(self, code_content: str, fixes: List[Dict[str, Any]]) -> tuple[str, int]:
        """
        Apply multiple fixes to code content
        
        Args:
            code_content: Original code
            fixes: List of fix objects from generate_fix()
        
        Returns:
            Tuple of (fixed_code, number_of_fixes_applied)
        """
        if not fixes:
            return code_content, 0
        
        lines = code_content.split('\n')
        fixes_applied = 0
        
        # Sort fixes by line number in descending order to avoid offset issues
        sorted_fixes = sorted(fixes, key=lambda x: x.get('line', 0), reverse=True)
        
        for fix in sorted_fixes:
            line_num = fix.get('line', 0) - 1  # Convert to 0-based index
            original_code = fix.get('original_code', '')
            fixed_code = fix.get('fixed_code', '')
            
            if line_num >= 0 and line_num < len(lines) and original_code and fixed_code:
                # Check if the original code matches
                if original_code.strip() in lines[line_num]:
                    lines[line_num] = lines[line_num].replace(original_code.strip(), fixed_code.strip())
                    fixes_applied += 1
                    fix['applied'] = True
        
        return '\n'.join(lines), fixes_applied
    
    def batch_generate_fixes(self, issues: List[Dict[str, Any]], code_content: str = "", file_extension: str = "py") -> List[Dict[str, Any]]:
        """Generate fixes for multiple issues at once"""
        fixes = []
        
        for issue in issues:
            # Extract context around the issue line
            context = self._extract_code_context(code_content, issue.get('line', 0))
            fix = self.generate_fix(issue, context, file_extension)
            
            if fix:
                fixes.append(fix)
        
        return fixes
    
    def _extract_code_context(self, code_content: str, line_number: int, context_lines: int = 5) -> str:
        """Extract code context around a specific line"""
        if not code_content:
            return ""
        
        lines = code_content.split('\n')
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        context_lines_list = lines[start:end]
        return '\n'.join(context_lines_list)
    
    def get_env_file_content(self, fixes: List[Dict[str, Any]]) -> str:
        """Generate .env.example content from fixes that require environment variables"""
        env_vars = set()
        
        for fix in fixes:
            env_vars.update(fix.get('env_vars_needed', []))
        
        if not env_vars:
            return ""
        
        env_content = "# Environment Variables\n"
        env_content += "# Add these to your .env file\n\n"
        
        for var in sorted(env_vars):
            env_content += f"{var}=your_{var.lower()}_here\n"
        
        return env_content

# Global instance
gemini_fix_service = GeminiFixService()

def get_ai_fix_service():
    """Get the global Gemini fix service instance"""
    return gemini_fix_service