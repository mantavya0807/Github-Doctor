#!/usr/bin/env python3
"""
GitHub PR Auto-Fix Flask Backend - Complete with AI Agent Integration
Enhanced with autonomous monitoring and auto-fix capabilities
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import hashlib
import hmac
import json
import requests
import re
import ast
from datetime import datetime, timezone
import traceback
import base64
import urllib.parse
import time

# Import enhanced utilities with AI fixes
from utils import (
    analyze_code_content,
    calculate_security_score,
    categorize_issues,
    get_fix_suggestions,
    generate_intelligent_fixes,
    apply_fixes_to_content,
    create_env_file_content,
    get_gemini_status,
    SECURITY_PATTERNS,
    DEBUG_PATTERNS,
    CODE_QUALITY_PATTERNS,
    PERFORMANCE_PATTERNS
)

# Import the agent service
from agent_service import get_agent, handle_webhook_event

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration with environment variables
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', 'demo-webhook-secret-12345')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', 'demo_token_for_testing_only')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
AGENT_MODE = os.getenv('AGENT_MODE', 'monitor')
AUTO_COMMIT_FIXES = os.getenv('AUTO_COMMIT_FIXES', 'false').lower() == 'true'
MAX_FILES_TO_ANALYZE = int(os.getenv('MAX_FILES_TO_ANALYZE', '10'))

# Global data storage (use database in production)
pr_history = []
fix_stats = {
    'secrets_fixed': 0,
    'debug_statements_removed': 0,
    'tests_generated': 0,
    'total_prs_processed': 0,
    'security_vulnerabilities_fixed': 0,
    'code_quality_improvements': 0,
    'performance_issues_fixed': 0,
    'documentation_added': 0,
    'ai_fixes_applied': 0,
    'rule_based_fixes_applied': 0
}

# Create or get the PR agent instance
pr_agent = get_agent()

# Helper function for timezone-aware datetime
def utc_now():
    """Get current UTC time in a timezone-aware way"""
    return datetime.now(timezone.utc)

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check with AI integration info"""
    agent_status = pr_agent.get_status()
    gemini_status = get_gemini_status()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': utc_now().isoformat(),
        'version': '4.0.0',
        'environment': 'development',
        'features': {
            'security_analysis': True,
            'github_pr_analysis': True,
            'code_quality_check': True,
            'performance_analysis': True,
            'multi_language_support': True,
            'detailed_reporting': True,
            'fix_suggestions': True,
            'auto_fix_agent': True,
            'ai_powered_fixes': gemini_status['configured'],
            'rule_based_fixes': True
        },
        'supported_languages': ['python', 'javascript', 'typescript', 'sql', 'jsx', 'tsx', 'java', 'cpp', 'c', 'php', 'rb'],
        'detection_categories': ['security', 'debug', 'quality', 'performance'],
        'github_integration': bool(GITHUB_TOKEN and GITHUB_TOKEN != 'demo_token_for_testing_only'),
        'agent': {
            'status': agent_status['status'],
            'mode': agent_status['agent_mode'],
            'repos_monitored': agent_status['repos_monitored'],
            'auto_commit': agent_status['auto_commit']
        },
        'ai_integration': gemini_status,
        'total_patterns': sum([
            len([p for patterns in SECURITY_PATTERNS.values() for p in patterns]),
            len([p for patterns in DEBUG_PATTERNS.values() for p in patterns]),
            len([p for patterns in CODE_QUALITY_PATTERNS.values() for p in patterns]),
            len([p for patterns in PERFORMANCE_PATTERNS.values() for p in patterns])
        ])
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_code():
    """Enhanced code analysis with AI-powered fix generation"""
    try:
        data = request.json or {}
        code_content = data.get('code', '')
        file_extension = data.get('extension', 'py')
        generate_fixes = data.get('generate_fixes', True)
        
        if not code_content.strip():
            return jsonify({
                'status': 'error',
                'message': 'No code provided for analysis'
            }), 400
        
        print(f"🔍 Analyzing {len(code_content)} characters of {file_extension} code...")
        
        # Analyze the code using your brilliant detection system
        issues = analyze_code_content(code_content, file_extension)
        
        # Sort issues by severity and line number
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        issues.sort(key=lambda x: (severity_order.get(x['severity'], 4), x['line']))
        
        # Calculate metrics
        security_score = calculate_security_score(issues)
        categorized_issues = categorize_issues(issues)
        
        # Generate AI-powered fixes if requested
        fixes = []
        if generate_fixes and issues:
            print(f"🤖 Generating intelligent fixes for {len(issues)} issues...")
            fixes = generate_intelligent_fixes(issues, code_content, file_extension)
        
        # Add fix suggestions to issues (your existing system)
        for issue in issues:
            issue['fix_suggestion'] = get_fix_suggestions(issue)
        
        # Generate detailed report
        report = {
            'status': 'analyzed',
            'timestamp': utc_now().isoformat(),
            'file_info': {
                'extension': file_extension,
                'lines_of_code': len(code_content.split('\n')),
                'characters': len(code_content),
                'estimated_complexity': 'HIGH' if len(code_content.split('\n')) > 100 else 'MEDIUM' if len(code_content.split('\n')) > 50 else 'LOW'
            },
            'summary': {
                'total_issues': len(issues),
                'critical_issues': len([i for i in issues if i['severity'] == 'CRITICAL']),
                'high_issues': len([i for i in issues if i['severity'] == 'HIGH']),
                'medium_issues': len([i for i in issues if i['severity'] == 'MEDIUM']),
                'low_issues': len([i for i in issues if i['severity'] == 'LOW']),
                'fixable_issues': len([i for i in issues if i['fix_available']]),
                'ai_fixes_available': len([f for f in fixes if f.get('fix_type') == 'ai_generated']),
                'rule_fixes_available': len([f for f in fixes if f.get('fix_type') == 'rule_based'])
            },
            'security_score': security_score,
            'risk_level': 'CRITICAL' if security_score < 60 else 'HIGH' if security_score < 80 else 'MEDIUM' if security_score < 95 else 'LOW',
            'categorized_issues': categorized_issues,
            'issues_found': issues,
            'intelligent_fixes': fixes,
            'ai_status': get_gemini_status(),
            'recommendations': {
                'immediate_actions': [
                    f"Fix {len([i for i in issues if i['severity'] == 'CRITICAL'])} critical security issues",
                    f"Remove {len([i for i in issues if i['type'] == 'debug_statement'])} debug statements",
                    f"Address {len([i for i in issues if i['severity'] == 'HIGH'])} high-priority issues"
                ],
                'code_quality_improvements': [
                    "Implement proper error handling",
                    "Add input validation",
                    "Use secure coding practices",
                    "Add comprehensive logging"
                ],
                'security_enhancements': [
                    "Use environment variables for secrets",
                    "Implement input sanitization",
                    "Add authentication and authorization",
                    "Regular security audits"
                ]
            }
        }
        
        print(f"✅ Analysis complete: {len(issues)} issues, {len(fixes)} fixes generated")
        return jsonify(report)
        
    except Exception as e:
        print(f"Code analysis error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Analysis failed: {str(e)}',
            'timestamp': utc_now().isoformat()
        }), 500

@app.route('/api/apply-fixes', methods=['POST'])
def apply_fixes():
    """Apply AI-generated fixes to code"""
    try:
        data = request.json or {}
        code_content = data.get('code', '')
        fixes = data.get('fixes', [])
        
        if not code_content:
            return jsonify({
                'status': 'error',
                'message': 'No code content provided'
            }), 400
        
        if not fixes:
            return jsonify({
                'status': 'error',
                'message': 'No fixes provided'
            }), 400
        
        print(f"🔧 Applying {len(fixes)} fixes to code...")
        
        # Apply fixes using enhanced utility
        fixed_code, fixes_applied, env_vars_needed = apply_fixes_to_content(code_content, fixes)
        
        # Generate .env file content if needed
        env_file_content = create_env_file_content(env_vars_needed) if env_vars_needed else ""
        
        # Update stats
        fix_stats['ai_fixes_applied'] += len([f for f in fixes if f.get('fix_type') == 'ai_generated'])
        fix_stats['rule_based_fixes_applied'] += len([f for f in fixes if f.get('fix_type') == 'rule_based'])
        
        result = {
            'status': 'success',
            'original_code': code_content,
            'fixed_code': fixed_code,
            'fixes_applied': fixes_applied,
            'total_fixes_attempted': len(fixes),
            'success_rate': (fixes_applied / len(fixes) * 100) if fixes else 0,
            'env_vars_needed': env_vars_needed,
            'env_file_content': env_file_content,
            'fixes_details': [
                {
                    'line': fix.get('line'),
                    'type': fix.get('fix_type', 'unknown'),
                    'confidence': fix.get('confidence', 'MEDIUM'),
                    'applied': fix.get('applied', False),
                    'explanation': fix.get('explanation', '')
                }
                for fix in fixes
            ],
            'timestamp': utc_now().isoformat()
        }
        
        print(f"✅ Applied {fixes_applied}/{len(fixes)} fixes successfully")
        return jsonify(result)
        
    except Exception as e:
        print(f"Fix application error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Failed to apply fixes: {str(e)}',
            'timestamp': utc_now().isoformat()
        }), 500

@app.route('/api/generate-fixes', methods=['POST'])
def generate_fixes():
    """Generate fixes for specific issues"""
    try:
        data = request.json or {}
        issues = data.get('issues', [])
        code_content = data.get('code', '')
        file_extension = data.get('extension', 'py')
        fix_type = data.get('fix_type', 'intelligent')
        
        if not issues:
            return jsonify({
                'status': 'error',
                'message': 'No issues provided'
            }), 400
        
        print(f"🛠️  Generating {fix_type} fixes for {len(issues)} issues...")
        
        if fix_type == 'intelligent':
            fixes = generate_intelligent_fixes(issues, code_content, file_extension)
        else:
            fixes = generate_intelligent_fixes(issues, code_content, file_extension)
        
        # Collect environment variables
        env_vars = []
        for fix in fixes:
            env_vars.extend(fix.get('env_vars_needed', []))
        
        result = {
            'status': 'success',
            'fixes_generated': len(fixes),
            'fixes': fixes,
            'env_vars_needed': list(set(env_vars)),
            'env_file_content': create_env_file_content(list(set(env_vars))),
            'ai_status': get_gemini_status(),
            'timestamp': utc_now().isoformat()
        }
        
        print(f"✅ Generated {len(fixes)} fixes")
        return jsonify(result)
        
    except Exception as e:
        print(f"Fix generation error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Failed to generate fixes: {str(e)}',
            'timestamp': utc_now().isoformat()
        }), 500

@app.route('/api/ai-status', methods=['GET'])
def ai_integration_status():
    """Get AI integration status"""
    return jsonify(get_gemini_status())

@app.route('/api/analyze-github-pr', methods=['POST'])
def analyze_github_pr():
    """Enhanced GitHub PR analysis with AI fixes"""
    try:
        data = request.json or {}
        pr_url = data.get('pr_url', '').strip()
        generate_fixes = data.get('generate_fixes', True)
        
        if not pr_url:
            return jsonify({
                'status': 'error',
                'message': 'GitHub PR URL is required'
            }), 400
        
        # Parse GitHub PR URL
        pr_pattern = r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
        match = re.match(pr_pattern, pr_url)
        
        if not match:
            return jsonify({
                'status': 'error',
                'message': 'Invalid GitHub PR URL format. Expected: https://github.com/owner/repo/pull/123'
            }), 400
        
        owner, repo, pr_number = match.groups()
        
        # Setup GitHub API headers
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'PR-AutoFix-Tool/4.0'
        }
        
        # Get PR details
        pr_api_url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}'
        print(f"Fetching PR data from: {pr_api_url}")
        
        pr_response = requests.get(pr_api_url, headers=headers, timeout=15)
        
        if pr_response.status_code == 404:
            return jsonify({
                'status': 'error',
                'message': 'PR not found. Check if the URL is correct and the repository is accessible.'
            }), 404
        elif pr_response.status_code == 401:
            return jsonify({
                'status': 'error',
                'message': 'GitHub API authentication failed. Please check your GitHub token.'
            }), 401
        elif pr_response.status_code == 403:
            return jsonify({
                'status': 'error',
                'message': 'GitHub API rate limit exceeded or insufficient permissions.'
            }), 403
        elif pr_response.status_code != 200:
            return jsonify({
                'status': 'error',
                'message': f'GitHub API error: {pr_response.status_code} - {pr_response.text[:200]}'
            }), 500
        
        pr_data = pr_response.json()
        
        # Get PR files
        files_api_url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files'
        files_response = requests.get(files_api_url, headers=headers, timeout=15)
        
        if files_response.status_code != 200:
            return jsonify({
                'status': 'error',
                'message': f'Failed to fetch PR files: {files_response.status_code} - {files_response.text[:200]}'
            }), 500
        
        files_data = files_response.json()
        
        # Analyze each changed file with AI fixes
        analyzed_files = []
        total_issues = []
        all_fixes = []
        
        # Define analyzable file extensions
        analyzable_extensions = {
            'py': 'python', 'js': 'javascript', 'ts': 'typescript', 
            'jsx': 'javascript', 'tsx': 'typescript', 'java': 'java',
            'cpp': 'cpp', 'c': 'c', 'php': 'php', 'rb': 'ruby', 'sql': 'sql'
        }
        
        print(f"🔍 Analyzing {len(files_data)} files from PR #{pr_number}")
        
        for file_info in files_data[:15]:  # Limit to first 15 files
            filename = file_info.get('filename', '')
            status = file_info.get('status', '')
            
            # Skip deleted files
            if status == 'removed':
                continue
                
            # Get file extension
            file_ext = filename.split('.')[-1].lower() if '.' in filename else 'txt'
            
            # Skip non-analyzable files
            if file_ext not in analyzable_extensions:
                continue
            
            # Get file content from patch
            if 'patch' in file_info and file_info['patch']:
                # Extract added lines from patch (lines starting with +)
                patch_lines = file_info['patch'].split('\n')
                added_lines = []
                
                for line in patch_lines:
                    if line.startswith('+') and not line.startswith('+++'):
                        added_lines.append(line[1:])  # Remove the + prefix
                
                file_content = '\n'.join(added_lines)
                
                if file_content.strip():
                    print(f"  📄 Analyzing {filename} ({len(added_lines)} new lines)")
                    
                    # Analyze the file content
                    file_issues = analyze_code_content(file_content, file_ext)
                    
                    # Generate AI fixes for this file if requested
                    file_fixes = []
                    if generate_fixes and file_issues:
                        print(f"    🤖 Generating fixes for {len(file_issues)} issues in {filename}")
                        file_fixes = generate_intelligent_fixes(file_issues, file_content, file_ext)
                        all_fixes.extend(file_fixes)
                    
                    analyzed_files.append({
                        'filename': filename,
                        'status': status,
                        'additions': file_info.get('additions', 0),
                        'deletions': file_info.get('deletions', 0),
                        'changes': file_info.get('changes', 0),
                        'issues_found': file_issues,
                        'issues_count': len(file_issues),
                        'fixes_generated': file_fixes,
                        'fixes_count': len(file_fixes),
                        'lines_analyzed': len(file_content.split('\n')),
                        'extension': file_ext
                    })
                    
                    total_issues.extend(file_issues)
        
        # Calculate overall metrics
        security_score = calculate_security_score(total_issues)
        categorized_issues = categorize_issues(total_issues)
        risk_level = 'CRITICAL' if security_score < 60 else 'HIGH' if security_score < 80 else 'MEDIUM' if security_score < 95 else 'LOW'
        
        # Collect environment variables from all fixes
        env_vars_needed = []
        for fix in all_fixes:
            env_vars_needed.extend(fix.get('env_vars_needed', []))
        env_vars_needed = list(set(env_vars_needed))
        
        # Store PR analysis in history
        pr_analysis = {
            'id': len(pr_history) + 1,
            'url': pr_url,
            'number': int(pr_number),
            'title': pr_data.get('title', 'Unknown Title'),
            'repository': f"{owner}/{repo}",
            'author': pr_data.get('user', {}).get('login', 'unknown'),
            'created_at': pr_data.get('created_at', utc_now().isoformat()),
            'updated_at': pr_data.get('updated_at', utc_now().isoformat()),
            'status': 'analyzed',
            'state': pr_data.get('state', 'unknown'),
            'analyzed_at': utc_now().isoformat(),
            'files_analyzed': len(analyzed_files),
            'total_issues': len(total_issues),
            'security_score': security_score,
            'risk_level': risk_level,
            'fixes_generated': len(all_fixes),
            'ai_fixes_available': len([f for f in all_fixes if f.get('fix_type') == 'ai_generated'])
        }
        
        pr_history.append(pr_analysis)
        fix_stats['total_prs_processed'] += 1
        
        result = {
            'status': 'success',
            'pr_info': {
                'url': pr_url,
                'number': int(pr_number),
                'title': pr_data.get('title'),
                'repository': f"{owner}/{repo}",
                'author': pr_data.get('user', {}).get('login'),
                'state': pr_data.get('state'),
                'created_at': pr_data.get('created_at'),
                'updated_at': pr_data.get('updated_at'),
                'mergeable': pr_data.get('mergeable'),
                'draft': pr_data.get('draft', False)
            },
            'analysis_summary': {
                'files_analyzed': len(analyzed_files),
                'total_issues': len(total_issues),
                'critical_issues': len([i for i in total_issues if i.get('severity') == 'CRITICAL']),
                'high_issues': len([i for i in total_issues if i.get('severity') == 'HIGH']),
                'medium_issues': len([i for i in total_issues if i.get('severity') == 'MEDIUM']),
                'low_issues': len([i for i in total_issues if i.get('severity') == 'LOW']),
                'security_score': security_score,
                'risk_level': risk_level,
                'languages_analyzed': list(set([f['extension'] for f in analyzed_files])),
                'fixes_generated': len(all_fixes),
                'ai_fixes_available': len([f for f in all_fixes if f.get('fix_type') == 'ai_generated']),
                'rule_fixes_available': len([f for f in all_fixes if f.get('fix_type') == 'rule_based'])
            },
            'files_analyzed': analyzed_files,
            'categorized_issues': categorized_issues,
            'all_issues': total_issues,
            'intelligent_fixes': all_fixes,
            'env_vars_needed': env_vars_needed,
            'env_file_content': create_env_file_content(env_vars_needed),
            'ai_status': get_gemini_status(),
            'timestamp': utc_now().isoformat()
        }
        
        print(f"✅ PR analysis complete: {len(total_issues)} issues, {len(all_fixes)} fixes generated")
        return jsonify(result)
        
    except requests.exceptions.Timeout:
        return jsonify({
            'status': 'error',
            'message': 'GitHub API request timed out. Please try again.'
        }), 500
    except requests.exceptions.ConnectionError:
        return jsonify({
            'status': 'error',
            'message': 'Cannot connect to GitHub API. Please check your internet connection.'
        }), 500
    except Exception as e:
        print(f"GitHub PR analysis error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Analysis failed: {str(e)}'
        }), 500

@app.route('/api/pr-history', methods=['GET'])
def get_pr_history():
    """Get list of processed PRs"""
    try:
        recent_prs = sorted(pr_history, key=lambda x: x.get('analyzed_at', x.get('created_at', '')), reverse=True)
        return jsonify({
            'prs': recent_prs[:25],  # Return last 25 PRs
            'total_count': len(pr_history)
        })
    except Exception as e:
        print(f"PR history error: {str(e)}")
        return jsonify({
            'prs': [],
            'total_count': 0
        })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get enhanced fix statistics with AI metrics"""
    try:
        gemini_status = get_gemini_status()
        
        return jsonify({
            **fix_stats,
            'analysis_capabilities': {
                'security_patterns': len([p for patterns in SECURITY_PATTERNS.values() for p in patterns]),
                'debug_patterns': len([p for patterns in DEBUG_PATTERNS.values() for p in patterns]),
                'quality_patterns': len([p for patterns in CODE_QUALITY_PATTERNS.values() for p in patterns]),
                'performance_patterns': len([p for patterns in PERFORMANCE_PATTERNS.values() for p in patterns])
            },
            'ai_integration': gemini_status,
            'fix_success_rate': {
                'ai_fixes': fix_stats.get('ai_fixes_applied', 0),
                'rule_fixes': fix_stats.get('rule_based_fixes_applied', 0),
                'total_fixes': fix_stats.get('ai_fixes_applied', 0) + fix_stats.get('rule_based_fixes_applied', 0)
            },
            'last_updated': utc_now().isoformat()
        })
    except Exception as e:
        print(f"Stats error: {str(e)}")
        return jsonify(fix_stats)

@app.route('/api/webhook', methods=['POST'])
def github_webhook():
    """Enhanced webhook handler with AI fixes"""
    try:
        # Verify webhook signature if configured
        if GITHUB_WEBHOOK_SECRET != 'demo-webhook-secret-12345':
            signature = request.headers.get('X-Hub-Signature-256')
            if not signature:
                return jsonify({'status': 'error', 'message': 'No signature provided'}), 401
                
            # Calculate expected signature
            payload_body = request.data
            expected_signature = 'sha256=' + hmac.new(
                GITHUB_WEBHOOK_SECRET.encode('utf-8'),
                payload_body,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return jsonify({'status': 'error', 'message': 'Invalid signature'}), 401
        
        # Get the event type and payload
        event_type = request.headers.get('X-GitHub-Event', 'unknown')
        payload = request.json or {}
        
        print(f"🔔 Received GitHub webhook event: {event_type}")
        
        # Let the agent handle the event (now with AI fixes)
        result = handle_webhook_event(event_type, payload)
        
        return jsonify({
            'status': 'processed',
            'event': event_type,
            'result': result,
            'ai_enabled': get_gemini_status()['configured']
        })
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'error': str(e)}), 500

# Agent endpoints
@app.route('/api/agent/status', methods=['GET'])
def agent_status():
    """Get the current status of the PR auto-fix agent"""
    try:
        agent_data = pr_agent.get_status()
        agent_data['ai_integration'] = get_gemini_status()
        return jsonify(agent_data)
    except Exception as e:
        print(f"Agent status error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get agent status: {str(e)}'
        }), 500

@app.route('/api/agent/activity', methods=['GET'])
def agent_activity():
    """Get the activity log of the PR auto-fix agent"""
    try:
        return jsonify({
            'activity': pr_agent.activity_log,
            'count': len(pr_agent.activity_log)
        })
    except Exception as e:
        print(f"Agent activity error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get agent activity: {str(e)}'
        }), 500

@app.route('/api/agent/configure', methods=['POST'])
def configure_agent():
    """Configure the PR auto-fix agent"""
    try:
        data = request.json or {}
        
        # Update agent configuration
        global AGENT_MODE, AUTO_COMMIT_FIXES, MAX_FILES_TO_ANALYZE
        
        if 'agent_mode' in data:
            AGENT_MODE = data['agent_mode']
            os.environ['AGENT_MODE'] = AGENT_MODE
            
        if 'auto_commit' in data:
            AUTO_COMMIT_FIXES = data['auto_commit']
            os.environ['AUTO_COMMIT_FIXES'] = str(AUTO_COMMIT_FIXES).lower()
            
        if 'max_files' in data:
            MAX_FILES_TO_ANALYZE = int(data['max_files'])
            os.environ['MAX_FILES_TO_ANALYZE'] = str(MAX_FILES_TO_ANALYZE)
            
        if 'excluded_files' in data:
            os.environ['EXCLUDED_FILES'] = ','.join(data['excluded_files'])
            
        if 'excluded_extensions' in data:
            os.environ['EXCLUDED_EXTENSIONS'] = ','.join(data['excluded_extensions'])
        
        return jsonify({
            'status': 'success',
            'message': 'Agent configuration updated',
            'current_config': {
                'agent_mode': AGENT_MODE,
                'auto_commit': AUTO_COMMIT_FIXES,
                'max_files': MAX_FILES_TO_ANALYZE,
                'excluded_files': os.getenv('EXCLUDED_FILES', '').split(','),
                'excluded_extensions': os.getenv('EXCLUDED_EXTENSIONS', '').split(',')
            },
            'ai_integration': get_gemini_status()
        })
        
    except Exception as e:
        print(f"Agent configuration error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to configure agent: {str(e)}'
        }), 500

@app.route('/api/agent/manual-analyze', methods=['POST'])
def manual_analyze():
    """Manually trigger the agent to analyze a repository with AI fixes"""
    try:
        data = request.json or {}
        repo = data.get('repository')
        branch = data.get('branch', 'main')
        
        if not repo:
            return jsonify({
                'status': 'error',
                'message': 'Repository is required'
            }), 400
        
        print(f"🔍 Manual analysis triggered for {repo}, branch: {branch}")
        
        # Use the direct repository analysis method
        result = pr_agent.analyze_repository_directly(repo, branch)
        
        # Enhance with AI fixes if issues were found
        if result.get('file_results') and get_gemini_status()['configured']:
            print("🤖 Enhancing analysis with AI fixes...")
            
            for file_result in result.get('file_results', []):
                if file_result.get('issues'):
                    file_extension = file_result.get('filename', '').split('.')[-1] if '.' in file_result.get('filename', '') else 'py'
                    ai_fixes = generate_intelligent_fixes(file_result['issues'], "", file_extension)
                    file_result['ai_fixes'] = ai_fixes
                    file_result['ai_fixes_count'] = len(ai_fixes)
        
        print(f"✅ Analysis complete. Status: {result.get('status')}, Files: {result.get('files_analyzed')}, Issues: {result.get('total_issues', 0)}")
        
        return jsonify({
            'status': 'success',
            'message': 'Analysis completed with AI enhancements',
            'result': result,
            'ai_integration': get_gemini_status()
        })
        
    except Exception as e:
        print(f"Manual analysis error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Failed to trigger analysis: {str(e)}'
        }), 500

@app.route('/api/agent/apply-fixes', methods=['POST'])
def apply_fixes_to_repository():
    """Apply fixes directly to a repository and create PR"""
    try:
        data = request.json or {}
        repository = data.get('repository')
        branch = data.get('branch', 'main')
        file_results = data.get('file_results', [])
        
        if not repository:
            return jsonify({
                'status': 'error',
                'message': 'Repository is required'
            }), 400
            
        if not file_results:
            return jsonify({
                'status': 'error',
                'message': 'No file results with fixes provided'
            }), 400
        
        print(f"🔧 Applying fixes to repository: {repository}")
        
        # Use the agent to apply fixes
        result = pr_agent.apply_fixes_to_repository(repository, branch, file_results)
        
        if result.get('status') == 'success':
            # Update global stats
            fix_stats['ai_fixes_applied'] += result.get('total_fixes_applied', 0)
            
            return jsonify({
                'status': 'success',
                'message': result.get('message'),
                'pr_url': result.get('pr_url'),
                'pr_number': result.get('pr_number'),
                'files_fixed': result.get('files_fixed'),
                'total_fixes_applied': result.get('total_fixes_applied'),
                'env_vars_needed': result.get('env_vars_needed', []),
                'timestamp': utc_now().isoformat()
            })
        else:
            return jsonify({
                'status': result.get('status', 'error'),
                'message': result.get('message', 'Failed to apply fixes'),
                'timestamp': utc_now().isoformat()
            }), 500
        
    except Exception as e:
        print(f"Apply fixes to repository error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Failed to apply fixes to repository: {str(e)}',
            'timestamp': utc_now().isoformat()
        }), 500

# Initialize sample data
def initialize_sample_data():
    """Initialize with sample data for demonstration"""
    sample_prs = [
        {
            'id': 1,
            'url': 'https://github.com/sample/security-repo/pull/1',
            'number': 1,
            'title': 'Add authentication with hardcoded secrets',
            'repository': 'sample/security-repo',
            'author': 'developer1',
            'created_at': '2024-06-01T10:00:00Z',
            'status': 'analyzed',
            'state': 'open',
            'analyzed_at': '2024-06-01T10:30:00Z',
            'files_analyzed': 3,
            'total_issues': 8,
            'security_score': 65,
            'risk_level': 'HIGH',
            'fixes_generated': 8,
            'ai_fixes_available': 5
        },
        {
            'id': 2,
            'url': 'https://github.com/sample/clean-repo/pull/2',
            'number': 2,
            'title': 'Fix database connection with proper env vars',
            'repository': 'sample/clean-repo',
            'author': 'developer2',
            'created_at': '2024-06-02T14:00:00Z',
            'status': 'analyzed',
            'state': 'closed',
            'analyzed_at': '2024-06-02T14:15:00Z',
            'files_analyzed': 2,
            'total_issues': 1,
            'security_score': 98,
            'risk_level': 'LOW',
            'fixes_generated': 1,
            'ai_fixes_available': 1
        }
    ]
    
    pr_history.extend(sample_prs)
    fix_stats['total_prs_processed'] = len(sample_prs)
    fix_stats['secrets_fixed'] = 5
    fix_stats['debug_statements_removed'] = 12
    fix_stats['tests_generated'] = 3
    fix_stats['ai_fixes_applied'] = 8
    fix_stats['rule_based_fixes_applied'] = 4

# Initialize sample data
initialize_sample_data()

# Main application entry point
if __name__ == '__main__':
    print("🚀 GitHub PR Auto-Fix Flask Backend v4.0.0 - With Gemini AI Integration")
    print("=" * 80)
    print("🔍 Your Brilliant Detection System:")
    print("   ✅ 70+ Security vulnerability patterns")
    print("   ✅ Debug statement detection (10+ languages)")
    print("   ✅ Code quality analysis")
    print("   ✅ Performance optimization detection")
    print("   ✅ GitHub PR integration with full analysis")
    print()
    print("🤖 AI-Powered Intelligent Fixes:")
    gemini_status = get_gemini_status()
    if gemini_status['configured']:
        print("   ✅ Google Gemini AI integration active")
        print("   ✅ Context-aware fix generation")
        print("   ✅ Multi-language intelligent fixes")
        print("   ✅ Environment variable suggestions")
        print("   ✅ Confidence scoring for fixes")
    else:
        print("   ⚠️  Gemini API not configured (using rule-based fixes)")
        print("   💡 Set GEMINI_API_KEY environment variable to enable AI fixes")
    print()
    print("🤖 Agent Capabilities:")
    print("   ✅ Autonomous monitoring of GitHub repositories")
    print("   ✅ Automatic issue detection on new commits")
    print("   ✅ AI-powered fix generation and application")
    print("   ✅ Pull request creation with detailed reports")
    print("   ✅ Environment variable management")
    print()
    print("🌐 Enhanced API Endpoints:")
    print("   ✅ GET  /api/health - System health + AI status")
    print("   ✅ POST /api/analyze - Code analysis + AI fixes")
    print("   ✅ POST /api/apply-fixes - Apply AI-generated fixes")
    print("   ✅ POST /api/generate-fixes - Generate fixes for specific issues")
    print("   ✅ GET  /api/ai-status - AI integration status")
    print("   ✅ POST /api/analyze-github-pr - Enhanced GitHub PR analysis")
    print("   ✅ GET  /api/pr-history - PR analysis history")
    print("   ✅ GET  /api/stats - Enhanced statistics with AI metrics")
    print("   ✅ POST /api/webhook - GitHub webhook handler")
    print("   ✅ GET  /api/agent/* - Agent management endpoints")
    print("   ✅ POST /api/agent/apply-fixes - Apply fixes to repository")
    print()
    print("🔧 Configuration:")
    github_configured = GITHUB_TOKEN != 'demo_token_for_testing_only'
    print(f"   GitHub Token: {'✅ Configured' if github_configured else '❌ Demo Mode'}")
    print(f"   Gemini API: {'✅ Configured' if gemini_status['configured'] else '❌ Not Configured'}")
    print(f"   Agent Mode: {AGENT_MODE}")
    print(f"   Auto-Commit: {'✅ Enabled' if AUTO_COMMIT_FIXES else '❌ Disabled'}")
    print()
    print("🎯 Ready to analyze code with AI-powered intelligent fixes!")
    print("🌐 Server starting on http://localhost:5000")
    print("=" * 80)
    
    # Start the Flask application
    app.run(debug=True, host='0.0.0.0', port=5000)