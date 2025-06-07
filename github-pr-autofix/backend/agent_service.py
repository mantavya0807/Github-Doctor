#!/usr/bin/env python3
"""
GitHub PR Auto-Fix Agent Service
Autonomous agent that monitors GitHub pushes, detects issues, and applies AI-powered fixes
"""

import os
import requests
import json
import re
import base64
import time
import logging
import hmac
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional, Union

# Import shared utilities
from utils import (
    analyze_code_content,
    calculate_security_score,
    categorize_issues,
    get_fix_suggestions,
    generate_intelligent_fixes,
    apply_fixes_to_content,
    create_env_file_content,
    get_gemini_status
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pr-autofix-agent')

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', 'demo_token_for_testing_only')
AI_SERVICE_API_KEY = os.getenv('AI_SERVICE_API_KEY', '')
AGENT_MODE = os.getenv('AGENT_MODE', 'monitor')
AUTO_COMMIT_FIXES = os.getenv('AUTO_COMMIT_FIXES', 'false').lower() == 'true'
MAX_FILES_TO_ANALYZE = int(os.getenv('MAX_FILES_TO_ANALYZE', '10'))
EXCLUDED_FILES = os.getenv('EXCLUDED_FILES', '.env,.git,node_modules,__pycache__,venv').split(',')
EXCLUDED_EXTENSIONS = os.getenv('EXCLUDED_EXTENSIONS', '.jpg,.png,.gif,.mp4,.mp3,.pdf').split(',')

def utc_now():
    """Get current UTC time in a timezone-aware way"""
    return datetime.now(timezone.utc)

class GitHubPRAgent:
    """Autonomous agent for monitoring GitHub PRs and applying fixes"""
    
    def __init__(self):
        self.github_headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'PR-AutoFix-Agent/2.0'
        }
        self.activity_log = []
        self.current_status = "idle"
        self.repos_being_monitored = []
        
    def filter_files_for_analysis(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter files for analysis based on extension and path"""
        if not files:
            return []
            
        filtered_files = []
        
        for file_info in files:
            filename = file_info.get('filename', '')
            
            if self.is_analyzable_file(filename):
                filtered_files.append(file_info)
                
        return filtered_files

    def get_file_extension(self, filename: str) -> str:
        """Get the file extension from a filename"""
        if not filename or '.' not in filename:
            return ''
        return filename.split('.')[-1].lower()

    def normalize_repository_name(self, repo_name: str) -> str:
        """
        Normalize repository name to username/repo format
        Handles both full URLs and username/repo formats
        """
        # Check if it's a full GitHub URL
        url_pattern = r'https?://github\.com/([^/]+)/([^/]+)'
        url_match = re.match(url_pattern, repo_name)
        
        if url_match:
            # Extract username and repo from URL
            username, repo = url_match.groups()
            # Remove .git suffix if present
            repo = repo.replace('.git', '')
            return f"{username}/{repo}"
        
        # If it's already in username/repo format, return as is
        if '/' in repo_name and not repo_name.startswith('http'):
            return repo_name
        
        # Otherwise, return as is (though it might not work)
        return repo_name

    def log_activity(self, action: str, details: Dict[str, Any], status: str = "success") -> None:
        """Log agent activity for dashboard display"""
        self.activity_log.append({
            "timestamp": utc_now().isoformat(),
            "action": action,
            "details": details,
            "status": status
        })
        if len(self.activity_log) > 100:  # Keep last 100 activities
            self.activity_log = self.activity_log[-100:]
        
        logger.info(f"Agent activity: {action} - {status}")
    
    def handle_push_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process a GitHub push event and trigger analysis/fixes"""
        try:
            self.current_status = "analyzing"
            
            # Extract repository and push information
            repo_name = payload.get('repository', {}).get('full_name', '')
            repo_url = payload.get('repository', {}).get('html_url', '')
            branch = payload.get('ref', '').replace('refs/heads/', '')
            pusher = payload.get('pusher', {}).get('name', 'Unknown')
            commit_count = len(payload.get('commits', []))
            
            print(f"Handling push event for {repo_name}, branch: {branch}, pusher: {pusher}")
            
            self.log_activity("push_received", {
                "repository": repo_name,
                "branch": branch,
                "pusher": pusher,
                "commit_count": commit_count
            })
            
            # Track this repository
            if repo_name and repo_name not in self.repos_being_monitored:
                self.repos_being_monitored.append(repo_name)
            
            # Get the commits
            commits = payload.get('commits', [])
            if not commits:
                print(f"No commits found in payload, using HEAD instead")
                commits = [{'id': 'HEAD', 'message': 'HEAD reference'}]
            
            # Analyze the latest commit
            latest_commit = commits[-1]
            commit_sha = latest_commit.get('id')
            commit_message = latest_commit.get('message', '')
            
            print(f"Analyzing commit: {commit_sha}, message: {commit_message}")
            
            # Skip if this is a fix commit from the agent
            if "[PR-AutoFix]" in commit_message:
                self.log_activity("push_skipped", {
                    "repository": repo_name,
                    "reason": "Agent fix commit"
                })
                return {"status": "skipped", "reason": "Agent fix commit"}
            
            # Get modified files from the commit
            modified_files = self.get_commit_files(repo_name, commit_sha)
            print(f"Found {len(modified_files)} modified files")
            
            # Filter files for analysis
            files_to_analyze = self.filter_files_for_analysis(modified_files)
            
            if not files_to_analyze:
                print(f"No analyzable files found in repository: {repo_name}")
                self.log_activity("analysis_skipped", {
                    "repository": repo_name,
                    "commit": commit_sha[:7] if len(commit_sha) > 7 else commit_sha,
                    "reason": "No analyzable files"
                })
                return {
                    "status": "skipped", 
                    "reason": "No analyzable files", 
                    "repository": repo_name, 
                    "commit": commit_sha,
                    "timestamp": utc_now().isoformat(),
                    "files_analyzed": 0,
                    "total_issues": 0,
                    "security_score": 100,
                    "risk_level": "LOW"
                }
            
            # Analyze each file
            all_issues = []
            file_analysis_results = []
            analyzed_file_count = 0
            
            # Use MAX_FILES_TO_ANALYZE to limit the number of files analyzed
            for file_info in files_to_analyze[:MAX_FILES_TO_ANALYZE]:
                file_path = file_info.get('filename')
                file_ext = self.get_file_extension(file_path)
                print(f"Getting content for: {file_path}, extension: {file_ext}")
                
                try:
                    file_content = self.get_file_content(repo_name, commit_sha, file_path)
                    
                    if not file_content:
                        print(f"Could not get content for file: {file_path}")
                        continue
                    
                    # Analyze file content
                    print(f"Analyzing content for: {file_path}")
                    issues = analyze_code_content(file_content, file_ext)
                    analyzed_file_count += 1
                    
                    if issues:
                        print(f"Found {len(issues)} issues in file: {file_path}")
                        all_issues.extend(issues)
                        
                        # Generate intelligent fixes
                        fixes = generate_intelligent_fixes(issues, file_content, file_ext)
                        
                        file_analysis_results.append({
                            "filename": file_path,
                            "issues_count": len(issues),
                            "issues": issues,
                            "fixes": fixes,
                            "fixes_count": len(fixes),
                            "file_content": file_content
                        })
                except Exception as e:
                    print(f"Error analyzing file {file_path}: {str(e)}")
                    continue
            
            # Calculate overall metrics
            security_score = calculate_security_score(all_issues)
            categorized_issues = categorize_issues(all_issues)
            risk_level = 'CRITICAL' if security_score < 60 else 'HIGH' if security_score < 80 else 'MEDIUM' if security_score < 95 else 'LOW'
            
            analysis_result = {
                "repository": repo_name,
                "commit": commit_sha,
                "branch": branch,
                "pusher": pusher,
                "timestamp": utc_now().isoformat(),
                "files_analyzed": analyzed_file_count,
                "total_issues": len(all_issues),
                "security_score": security_score,
                "risk_level": risk_level,
                "categorized_issues": categorized_issues,
                "file_results": file_analysis_results
            }
            
            self.log_activity("analysis_completed", {
                "repository": repo_name,
                "commit": commit_sha[:7] if len(commit_sha) > 7 else commit_sha,
                "issues_found": len(all_issues),
                "risk_level": risk_level
            })
            
            # Take action based on agent mode
            if len(all_issues) > 0:
                if AGENT_MODE == 'autofix':
                    fix_result = self.apply_fixes_to_repository(repo_name, branch, file_analysis_results)
                    analysis_result["fix_result"] = fix_result
                elif AGENT_MODE == 'suggest':
                    # Generate fixes but don't apply them
                    fix_suggestions = self.generate_fix_suggestions(file_analysis_results)
                    analysis_result["fix_suggestions"] = fix_suggestions
                    
                    # Create a PR with suggestions
                    if fix_suggestions:
                        self.create_suggestion_pr(repo_name, branch, commit_sha, fix_suggestions)
            
            self.current_status = "idle"
            print(f"Analysis completed: {len(all_issues)} issues found in {analyzed_file_count} files")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error handling push event: {str(e)}", exc_info=True)
            self.current_status = "error"
            self.log_activity("push_error", {
                "error": str(e),
                "repository": payload.get('repository', {}).get('full_name', '')
            }, status="error")
            return {"status": "error", "error": str(e)}
    
    def analyze_repository_directly(self, repo_name: str, branch: str = "main") -> Dict[str, Any]:
        """
        Directly analyze a repository by getting all files and analyzing them
        This is a simpler, more direct approach than the event-based method
        """
        # Normalize the repository name
        normalized_repo = self.normalize_repository_name(repo_name)
        print(f"DIRECT ANALYSIS: Starting direct analysis of {repo_name} (normalized to {normalized_repo}), branch {branch}")
        
        try:
            # 1. Get repository tree (all files) using GitHub's recursive tree API
            # This is more efficient than listing directories one by one
            url = f"https://api.github.com/repos/{normalized_repo}/git/trees/{branch}?recursive=1"
            print(f"Getting repository tree from: {url}")
            
            response = requests.get(url, headers=self.github_headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Failed to get repository tree: {response.status_code} - {response.text[:200]}")
                return {
                    "status": "error",
                    "repository": normalized_repo,
                    "branch": branch,
                    "timestamp": utc_now().isoformat(),
                    "files_analyzed": 0,
                    "total_issues": 0,
                    "security_score": 100,
                    "risk_level": "LOW",
                    "error": f"Failed to get repository tree: {response.status_code}"
                }
            
            tree_data = response.json()
            all_files = tree_data.get('tree', [])
            
            # Only include blob type (files, not directories)
            files_to_analyze = [
                item for item in all_files 
                if item.get('type') == 'blob' and self.is_analyzable_file(item.get('path', ''))
            ]
            
            print(f"Found {len(files_to_analyze)} analyzable files out of {len(all_files)} total files")
            
            # 2. Analyze each file
            all_issues = []
            file_analysis_results = []
            analyzed_file_count = 0
            
            # Limit the number of files to analyze
            for file_info in files_to_analyze[:MAX_FILES_TO_ANALYZE]:
                file_path = file_info.get('path', '')
                file_ext = self.get_file_extension(file_path)
                
                print(f"Analyzing file: {file_path}, extension: {file_ext}")
                
                try:
                    # Get file content using the blob URL
                    blob_sha = file_info.get('sha')
                    file_content = self.get_file_content_by_sha(normalized_repo, blob_sha)
                    
                    if not file_content:
                        print(f"Could not get content for file: {file_path}")
                        continue
                    
                    # Analyze file content
                    issues = analyze_code_content(file_content, file_ext)
                    analyzed_file_count += 1
                    
                    if issues:
                        print(f"Found {len(issues)} issues in file: {file_path}")
                        all_issues.extend(issues)
                        
                        # Generate intelligent fixes
                        fixes = generate_intelligent_fixes(issues, file_content, file_ext)
                        
                        file_analysis_results.append({
                            "filename": file_path,
                            "issues_count": len(issues),
                            "issues": issues,
                            "fixes": fixes,
                            "fixes_count": len(fixes),
                            "file_content": file_content,
                            "file_sha": blob_sha
                        })
                except Exception as e:
                    print(f"Error analyzing file {file_path}: {str(e)}")
                    continue
            
            # 3. Calculate metrics and prepare result
            security_score = calculate_security_score(all_issues)
            categorized_issues = categorize_issues(all_issues)
            risk_level = 'CRITICAL' if security_score < 60 else 'HIGH' if security_score < 80 else 'MEDIUM' if security_score < 95 else 'LOW'
            
            analysis_result = {
                "repository": normalized_repo,
                "commit": branch,  # Using branch as commit reference
                "branch": branch,
                "pusher": "direct-analysis",
                "timestamp": utc_now().isoformat(),
                "files_analyzed": analyzed_file_count,
                "total_issues": len(all_issues),
                "security_score": security_score,
                "risk_level": risk_level,
                "categorized_issues": categorized_issues,
                "file_results": file_analysis_results,
                "status": "analyzed"
            }
            
            # Log activity
            self.log_activity("analysis_completed", {
                "repository": normalized_repo,
                "commit": branch,
                "issues_found": len(all_issues),
                "risk_level": risk_level
            })
            
            print(f"DIRECT ANALYSIS: Completed analysis of {normalized_repo}: {analyzed_file_count} files analyzed, {len(all_issues)} issues found")
            return analysis_result
            
        except Exception as e:
            print(f"DIRECT ANALYSIS: Error during direct analysis: {str(e)}")
            return {
                "status": "error",
                "repository": normalized_repo,
                "branch": branch,
                "timestamp": utc_now().isoformat(),
                "files_analyzed": 0,
                "total_issues": 0,
                "security_score": 100,
                "risk_level": "LOW",
                "error": str(e)
            }

    def apply_fixes_to_repository(self, repo_name: str, branch: str, file_analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply fixes directly to repository files and create PR"""
        try:
            print(f"🔧 Applying fixes to repository: {repo_name}")
            
            # Create a new branch for fixes
            timestamp = int(time.time())
            fix_branch = f"pr-autofix-{timestamp}"
            
            # Get the latest commit SHA on the target branch
            branch_sha = self.get_branch_sha(repo_name, branch)
            if not branch_sha:
                return {
                    "status": "error",
                    "message": f"Failed to get branch SHA for {repo_name}/{branch}"
                }
            
            # Create new branch from current head
            if not self.create_branch(repo_name, fix_branch, branch_sha):
                return {
                    "status": "error",
                    "message": f"Failed to create fix branch"
                }
            
            print(f"✅ Created fix branch: {fix_branch}")
            
            # Apply fixes to each file
            files_fixed = []
            total_fixes_applied = 0
            env_vars_needed = set()
            
            for file_result in file_analysis_results:
                filename = file_result.get('filename')
                original_content = file_result.get('file_content')
                fixes = file_result.get('fixes', [])
                
                if not fixes or not original_content:
                    continue
                
                print(f"📝 Applying {len(fixes)} fixes to {filename}")
                
                # Apply fixes to file content
                fixed_content, fixes_applied_count, file_env_vars = apply_fixes_to_content(original_content, fixes)
                
                if fixes_applied_count > 0:
                    # Update the file in the repository
                    if self.update_file_in_repo(repo_name, fix_branch, filename, fixed_content, f"[PR-AutoFix] Apply {fixes_applied_count} fixes to {filename}"):
                        files_fixed.append({
                            "filename": filename,
                            "fixes_applied": fixes_applied_count,
                            "total_fixes": len(fixes)
                        })
                        total_fixes_applied += fixes_applied_count
                        env_vars_needed.update(file_env_vars)
                        
                        print(f"✅ Applied {fixes_applied_count}/{len(fixes)} fixes to {filename}")
                    else:
                        print(f"❌ Failed to update {filename} in repository")
            
            if not files_fixed:
                return {
                    "status": "no_fixes",
                    "message": "No fixes could be applied to the repository"
                }
            
            # Create .env.example file if environment variables are needed
            if env_vars_needed:
                env_file_content = create_env_file_content(list(env_vars_needed))
                self.create_file_in_repo(repo_name, fix_branch, ".env.example", env_file_content, "[PR-AutoFix] Add environment variables template")
                print(f"✅ Created .env.example with {len(env_vars_needed)} variables")
            
            # Create pull request
            pr_result = self.create_fix_pull_request_enhanced(repo_name, branch, fix_branch, files_fixed, env_vars_needed)
            
            if pr_result:
                self.log_activity("fix_pr_created", {
                    "repository": repo_name,
                    "pr_number": pr_result.get('number'),
                    "fixes_applied": total_fixes_applied,
                    "files_fixed": len(files_fixed)
                })
                
                return {
                    "status": "success",
                    "message": f"Applied {total_fixes_applied} fixes to {len(files_fixed)} files",
                    "pr_url": pr_result.get('html_url'),
                    "pr_number": pr_result.get('number'),
                    "files_fixed": files_fixed,
                    "total_fixes_applied": total_fixes_applied,
                    "env_vars_needed": list(env_vars_needed)
                }
            else:
                return {
                    "status": "error",
                    "message": "Fixes applied but failed to create pull request"
                }
                
        except Exception as e:
            logger.error(f"Error applying fixes to repository: {str(e)}", exc_info=True)
            self.log_activity("fix_error", {
                "repository": repo_name,
                "error": str(e)
            }, status="error")
            
            return {
                "status": "error",
                "message": f"Failed to apply fixes: {str(e)}"
            }

    def update_file_in_repo(self, repo_name: str, branch: str, file_path: str, content: str, message: str) -> bool:
        """Update a file in the repository"""
        try:
            # Get current file info to get its SHA
            url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}?ref={branch}"
            response = requests.get(url, headers=self.github_headers, timeout=15)
            
            file_sha = None
            if response.status_code == 200:
                file_info = response.json()
                file_sha = file_info.get('sha')
            elif response.status_code == 404:
                # File doesn't exist, we'll create it
                pass
            else:
                print(f"Failed to get file info for {file_path}: {response.status_code}")
                return False
            
            # Update or create the file
            url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
            
            data = {
                "message": message,
                "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                "branch": branch
            }
            
            if file_sha:
                data["sha"] = file_sha
            
            response = requests.put(url, headers=self.github_headers, json=data, timeout=15)
            
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"Failed to update file {file_path}: {response.status_code} - {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"Error updating file {file_path}: {str(e)}")
            return False

    def create_file_in_repo(self, repo_name: str, branch: str, file_path: str, content: str, message: str) -> bool:
        """Create a new file in the repository"""
        try:
            url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
            
            data = {
                "message": message,
                "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                "branch": branch
            }
            
            response = requests.put(url, headers=self.github_headers, json=data, timeout=15)
            
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"Failed to create file {file_path}: {response.status_code} - {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"Error creating file {file_path}: {str(e)}")
            return False

    def create_fix_pull_request_enhanced(self, repo_name: str, base_branch: str, fix_branch: str, files_fixed: List[Dict[str, Any]], env_vars_needed: set) -> Optional[Dict[str, Any]]:
        """Create an enhanced pull request with fix details"""
        try:
            total_fixes = sum(f.get('fixes_applied', 0) for f in files_fixed)
            
            pr_title = f"[PR-AutoFix] Applied {total_fixes} security and quality fixes"
            
            # Generate detailed PR body
            pr_body = f"""# 🤖 Automatic Code Quality and Security Fixes

This PR was automatically generated by the PR Auto-Fix agent and contains **{total_fixes} intelligent fixes** across **{len(files_fixed)} files**.

## 🔧 Fixes Applied

"""
            
            for file_fixed in files_fixed:
                pr_body += f"### 📄 `{file_fixed.get('filename')}`\n"
                pr_body += f"- **Fixes Applied:** {file_fixed.get('fixes_applied')}/{file_fixed.get('total_fixes')}\n"
                pr_body += f"- **Success Rate:** {(file_fixed.get('fixes_applied') / file_fixed.get('total_fixes') * 100):.1f}%\n\n"
            
            if env_vars_needed:
                pr_body += f"""## 🔑 Environment Variables Required

The following environment variables need to be configured:

"""
                for env_var in sorted(env_vars_needed):
                    pr_body += f"- `{env_var}`\n"
                
                pr_body += f"""
A `.env.example` file has been created with these variables. Copy it to `.env` and add your actual values.

"""
            
            pr_body += f"""## 🛡️ Security Improvements

This PR addresses:
- Hardcoded secrets and credentials
- Debug statements that could leak information
- Code quality issues that could introduce vulnerabilities
- Performance issues that could be exploited

## ✅ Testing

All fixes have been generated using AI-powered analysis and follow security best practices. Please review the changes and test thoroughly before merging.

## 🔍 Review Checklist

- [ ] Verify that no legitimate secrets were accidentally modified
- [ ] Confirm that environment variables are properly configured
- [ ] Test that the application still functions correctly
- [ ] Ensure all tests pass

---

*This PR was generated automatically by PR Auto-Fix Agent v2.0*
*Powered by AI for intelligent code analysis and fixes*
"""
            
            pr_data = {
                "title": pr_title,
                "body": pr_body,
                "head": fix_branch,
                "base": base_branch,
                "maintainer_can_modify": True
            }
            
            url = f"https://api.github.com/repos/{repo_name}/pulls"
            response = requests.post(url, headers=self.github_headers, json=pr_data, timeout=15)
            
            if response.status_code in [200, 201]:
                pr_result = response.json()
                print(f"✅ Created PR #{pr_result.get('number')}: {pr_result.get('html_url')}")
                return pr_result
            else:
                print(f"Failed to create PR: {response.status_code} - {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"Error creating enhanced PR: {str(e)}")
            return None

    def is_analyzable_file(self, filename: str) -> bool:
        """
        Check if a file is analyzable based on its extension and path
        """
        # Extensions we can analyze
        analyzable_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', 
            '.c', '.php', '.rb', '.go', '.cs', '.sql', '.html'
        ]
        
        # Skip excluded files and directories
        if any(excluded in filename for excluded in EXCLUDED_FILES):
            return False
            
        # Skip excluded extensions
        if any(filename.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
            return False
        
        # Check if file has an analyzable extension
        return any(filename.endswith(ext) for ext in analyzable_extensions)

    def get_file_content_by_sha(self, repo_name: str, blob_sha: str) -> Optional[str]:
        """
        Get file content directly using the blob SHA
        This is more reliable than using the file path
        """
        try:
            # Get the blob data
            url = f"https://api.github.com/repos/{repo_name}/git/blobs/{blob_sha}"
            response = requests.get(url, headers=self.github_headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Failed to get blob content: {response.status_code}")
                return None
            
            blob_data = response.json()
            content = blob_data.get('content', '')
            encoding = blob_data.get('encoding', '')
            
            if not content:
                return None
                
            # Decode content (usually base64)
            if encoding == 'base64':
                try:
                    return base64.b64decode(content).decode('utf-8')
                except Exception as e:
                    print(f"Error decoding base64 content: {str(e)}")
                    return None
            else:
                print(f"Unsupported encoding: {encoding}")
                return None
                
        except Exception as e:
            print(f"Error getting blob content: {str(e)}")
            return None
    
    def get_commit_files(self, repo_name: str, commit_sha: str) -> List[Dict[str, Any]]:
        """Get the files changed in a commit or all repository files for analysis"""
        try:
            print(f"Getting files for {repo_name}, commit: {commit_sha}")
            
            # For manual analysis or HEAD references, skip commit check and go straight to listing files
            if commit_sha == 'HEAD':
                print("Using HEAD reference, fetching all repository files")
                return self.list_repository_files(repo_name)
            
            # Try to get files from the specific commit
            url = f"https://api.github.com/repos/{repo_name}/commits/{commit_sha}"
            print(f"Fetching commit files from: {url}")
            
            response = requests.get(url, headers=self.github_headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Failed to get commit files: {response.status_code}, trying repository files instead")
                return self.list_repository_files(repo_name)
            
            commit_data = response.json()
            commit_files = commit_data.get('files', [])
            
            # If no files found in commit, get all repository files
            if not commit_files:
                print("No files found in commit, fetching all repository files")
                return self.list_repository_files(repo_name)
                
            print(f"Found {len(commit_files)} files in commit")
            return commit_files
                
        except Exception as e:
            print(f"Error getting commit files: {str(e)}")
            logger.error(f"Error getting commit files: {str(e)}")
            # Fallback to repository files on error
            return self.list_repository_files(repo_name)

    def list_repository_files(self, repo_name: str) -> List[Dict[str, Any]]:
        """List all files in a repository, handling pagination and recursion"""
        print(f"Listing all files in repository: {repo_name}")
        
        try:
            all_files = []
            
            # Start with the root directory
            contents_url = f"https://api.github.com/repos/{repo_name}/contents"
            contents_response = requests.get(contents_url, headers=self.github_headers, timeout=15)
            
            if contents_response.status_code != 200:
                print(f"Failed to get repository contents: {contents_response.status_code}")
                return []
            
            contents = contents_response.json()
            
            # Process each item (file or directory)
            dirs_to_process = []
            for item in contents:
                if item.get('type') == 'file':
                    # It's a file, add it to our list
                    all_files.append({
                        'filename': item.get('path', ''),
                        'status': 'modified',  # For analysis purposes
                        'additions': 1,        # Placeholder
                        'deletions': 0,
                        'changes': 1
                    })
                elif item.get('type') == 'dir':
                    # It's a directory, we'll process it
                    dirs_to_process.append(item.get('path', ''))
            
            # Process directories (limit depth to avoid excessive API calls)
            max_depth = 3
            current_depth = 0
            while dirs_to_process and current_depth < max_depth:
                next_dirs = []
                for dir_path in dirs_to_process:
                    # Get contents of this directory
                    dir_url = f"https://api.github.com/repos/{repo_name}/contents/{dir_path}"
                    dir_response = requests.get(dir_url, headers=self.github_headers, timeout=15)
                    
                    if dir_response.status_code != 200:
                        print(f"Failed to get directory contents: {dir_path}, status: {dir_response.status_code}")
                        continue
                    
                    dir_contents = dir_response.json()
                    for item in dir_contents:
                        if item.get('type') == 'file':
                            all_files.append({
                                'filename': item.get('path', ''),
                                'status': 'modified',
                                'additions': 1,
                                'deletions': 0,
                                'changes': 1
                            })
                        elif item.get('type') == 'dir':
                            next_dirs.append(item.get('path', ''))
                
                # Move to next level of directories
                dirs_to_process = next_dirs
                current_depth += 1
                
                # Respect GitHub API rate limits - add a small delay
                if next_dirs:
                    time.sleep(0.5)
            
            print(f"Found total of {len(all_files)} files in repository")
            return all_files
            
        except Exception as e:
            print(f"Error listing repository files: {str(e)}")
            logger.error(f"Error listing repository files: {str(e)}")
            return []
    
    def get_file_content(self, repo_name: str, commit_sha: str, file_path: str) -> Optional[str]:
        """Get the content of a file at a specific commit"""
        try:
            # First try to get file from the specific commit
            url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}?ref={commit_sha}"
            print(f"Fetching file content from: {url}")
            
            response = requests.get(url, headers=self.github_headers, timeout=15)
            
            # If file not found at commit, try without commit reference
            if response.status_code != 200 and commit_sha == 'HEAD':
                print(f"File not found at HEAD, trying without commit reference")
                url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
                response = requests.get(url, headers=self.github_headers, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"Failed to get file content: {response.status_code} - {response.text[:200]}")
                return None
            
            file_data = response.json()
            
            # Check if it's a file
            if isinstance(file_data, list):
                logger.error(f"Path points to a directory, not a file: {file_path}")
                return None
                
            if file_data.get('type') != 'file':
                logger.error(f"Not a file: {file_path}, type: {file_data.get('type')}")
                return None
                
            content = file_data.get('content', '')
            if not content:
                logger.error(f"Empty content for file: {file_path}")
                return None
                
            # Decode base64 content
            try:
                decoded_content = base64.b64decode(content).decode('utf-8')
                print(f"Successfully decoded content for {file_path}, length: {len(decoded_content)} bytes")
                return decoded_content
            except Exception as e:
                logger.error(f"Error decoding content: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting file content: {str(e)}")
            return None
    
    def generate_fix_suggestions(self, file_analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate fix suggestions for issues found"""
        suggestions = {}
        
        for file_result in file_analysis_results:
            filename = file_result.get('filename')
            fixes = file_result.get('fixes', [])
            
            if fixes:
                suggestions[filename] = fixes
        
        return suggestions
    
    def get_branch_sha(self, repo_name: str, branch: str) -> Optional[str]:
        """Get the SHA of the latest commit on a branch"""
        try:
            url = f"https://api.github.com/repos/{repo_name}/git/refs/heads/{branch}"
            response = requests.get(url, headers=self.github_headers, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"Failed to get branch SHA: {response.status_code} - {response.text[:200]}")
                return None
                
            data = response.json()
            return data.get('object', {}).get('sha')
            
        except Exception as e:
            logger.error(f"Error getting branch SHA: {str(e)}")
            return None
    
    def create_branch(self, repo_name: str, branch: str, sha: str) -> bool:
        """Create a new branch at the specified commit SHA"""
        try:
            url = f"https://api.github.com/repos/{repo_name}/git/refs"
            data = {
                "ref": f"refs/heads/{branch}",
                "sha": sha
            }
            
            response = requests.post(url, headers=self.github_headers, json=data, timeout=15)
            
            if response.status_code not in [200, 201]:
                logger.error(f"Failed to create branch: {response.status_code} - {response.text[:200]}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error creating branch: {str(e)}")
            return False
    
    def create_suggestion_pr(self, repo_name: str, branch: str, commit_sha: str, fix_suggestions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a PR with fix suggestions in the comments"""
        try:
            # Create a new branch for the fixes
            fix_branch = f"pr-autofix-suggestions-{int(time.time())}"
            
            # Create branch from the current commit
            self.create_branch(repo_name, fix_branch, commit_sha)
            
            # Prepare PR description with suggestions
            pr_description = self.generate_suggestion_pr_description(fix_suggestions)
            
            # Create the PR
            pr_data = {
                "title": "[PR-AutoFix] Code Quality Suggestions",
                "body": pr_description,
                "head": fix_branch,
                "base": branch
            }
            
            url = f"https://api.github.com/repos/{repo_name}/pulls"
            response = requests.post(url, headers=self.github_headers, json=pr_data, timeout=15)
            
            if response.status_code not in [200, 201]:
                logger.error(f"Failed to create suggestion PR: {response.status_code} - {response.text[:200]}")
                return None
                
            pr_result = response.json()
            
            self.log_activity("suggestion_pr_created", {
                "repository": repo_name,
                "pr_number": pr_result.get('number'),
                "suggestions_count": sum(len(fixes) for fixes in fix_suggestions.values())
            })
            
            return pr_result
            
        except Exception as e:
            logger.error(f"Error creating suggestion PR: {str(e)}", exc_info=True)
            return None
    
    def generate_suggestion_pr_description(self, fix_suggestions: Dict[str, Any]) -> str:
        """Generate a PR description with fix suggestions"""
        description = "# PR Auto-Fix Suggestions\n\n"
        description += "The PR Auto-Fix agent has analyzed your code and found some issues that could be improved.\n\n"
        
        for filename, fixes in fix_suggestions.items():
            description += f"## {filename}\n\n"
            
            for i, fix in enumerate(fixes, 1):
                description += f"### Fix {i}: {fix.get('explanation', 'Code improvement')}\n"
                description += f"- **Line**: {fix.get('line', 'Unknown')}\n"
                description += f"- **Confidence**: {fix.get('confidence', 'MEDIUM')}\n"
                
                if fix.get('original_code'):
                    description += f"- **Current code**: `{fix.get('original_code')}`\n"
                if fix.get('fixed_code'):
                    description += f"- **Suggested fix**: `{fix.get('fixed_code')}`\n"
                
                if fix.get('env_vars_needed'):
                    description += f"- **Environment variables needed**: {', '.join(fix.get('env_vars_needed'))}\n"
                
                description += "\n"
        
        description += "---\n"
        description += "These suggestions are automatically generated and should be reviewed before applying.\n"
        
        return description
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent"""
        gemini_status = get_gemini_status()
        
        return {
            "status": self.current_status,
            "repos_monitored": len(self.repos_being_monitored),
            "repos_list": self.repos_being_monitored,
            "agent_mode": AGENT_MODE,
            "auto_commit": AUTO_COMMIT_FIXES,
            "max_files": MAX_FILES_TO_ANALYZE,
            "recent_activity": self.activity_log[-5:] if self.activity_log else [],
            "ai_enabled": gemini_status.get('configured', False),
            "ai_status": gemini_status,
            "timestamp": utc_now().isoformat()
        }

# Initialize the agent
pr_agent = GitHubPRAgent()

# Export the agent for use in the main app
def get_agent():
    """Get the PR agent instance"""
    return pr_agent

def handle_webhook_event(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle a GitHub webhook event using the agent"""
    if event_type == 'push':
        return pr_agent.handle_push_event(payload)
    else:
        pr_agent.log_activity("event_skipped", {
            "event_type": event_type,
            "reason": "Unsupported event type"
        })
        return {"status": "skipped", "reason": f"Unsupported event type: {event_type}"}

if __name__ == "__main__":
    # This allows testing the agent directly
    logger.info("PR Auto-Fix Agent initialized and ready")
    logger.info(f"Agent mode: {AGENT_MODE}")
    logger.info(f"Auto-commit: {AUTO_COMMIT_FIXES}")
    logger.info(f"Max files to analyze: {MAX_FILES_TO_ANALYZE}")
    logger.info(f"AI enabled: {get_gemini_status().get('configured', False)}")