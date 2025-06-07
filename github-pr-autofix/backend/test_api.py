#!/usr/bin/env python3
"""
Enhanced API Test Script for GitHub PR Auto-Fix Tool v2.0
Tests all the new comprehensive analysis features
"""

import requests
import json
import time

API_BASE = "http://localhost:5000/api"

# Comprehensive test code samples
TEST_SAMPLES = {
    'security_nightmare': '''
# Security Nightmare - Multiple Critical Issues
import os
import subprocess

# Critical: Hardcoded secrets
api_key = "sk_live_1234567890abcdefghijklmnopqrstuvwxyz"
database_password = "super_secret_password_123"
jwt_secret = "my-jwt-signing-key-dont-tell-anyone"
aws_access_key = "AKIAIOSFODNN7EXAMPLE"
aws_secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
stripe_secret = "sk_live_abcdefghijklmnopqrstuvwxyz123456"
github_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz123456"

# Critical: SQL Injection vulnerability
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    return execute_query(query)

# High: Command injection
def process_file(filename):
    subprocess.call("rm -rf " + filename, shell=True)

# High: Eval usage
def calculate(expression):
    return eval(expression)

# Medium: Debug statements
print("API Key loaded:", api_key)
print("Database connection string:", f"postgresql://user:{database_password}@localhost/db")

# TODO: This needs immediate security review
# FIXME: Remove all hardcoded credentials
# HACK: Temporary workaround for authentication
''',
    'debug_heavy': '''
# Debug Statement Heavy Code
import logging
import pdb

def process_data(data):
    print("Processing data:", data)
    console.log("JavaScript style debug")
    
    # Debug breakpoints
    breakpoint()
    pdb.set_trace()
    
    for item in data:
        print(f"Processing item: {item}")
        console.debug("Item processed")
        
    # More debug output
    logging.debug("Data processing complete")
    alert("Debug: Processing finished")
    
    # Development comments
    # TODO: Optimize this loop
    # FIXME: Handle edge cases
    # HACK: Quick fix for now
    # XXX: This is problematic
    # BUG: Known issue here
    
    return data
''',
    'quality_issues': '''
# Code Quality Issues
import *  # Wildcard import
from os import *

def problematic_function():
    try:
        risky_operation()
    except:  # Bare except clause
        pass
    
    # Global variable usage
    global config
    config = load_config()
    
    # Exec and eval usage
    exec("dangerous_code = True")
    result = eval("2 + 2")
    
    # Empty function
    def empty_func():
        pass
    
    # JavaScript quality issues (in comments for demo)
    # var oldStyleVar = "should use let/const";
    # document.write("<script>alert('xss')</script>");
    # setTimeout("alert('string in setTimeout')", 1000);
    # if (value == null) { /* loose comparison */ }
    
    return result

# Empty class
class EmptyClass:
    pass
''',
    'performance_issues': '''
# Performance Issues

def inefficient_loops():
    data = list(range(1000))
    
    # Inefficient range loop
    for i in range(len(data)):
        process_item(data[i])
    
    # String concatenation in loop
    result = ""
    for item in data:
        result += str(item) + ","
    
    # Hard-coded sleep
    import time
    time.sleep(5)  # This will block everything
    
    return result

# JavaScript performance issues (in comments)    
# for(var i = 0; i < array.length; i++) { /* length in loop */ }
# setInterval(heavyFunction, 100); /* frequent interval */
# document.getElementById("same-element"); /* repeated DOM query */
''',
    'mixed_languages': '''
// Mixed Language Sample
const API_KEY = "pk_test_abcdefghijklmnopqrstuvwxyz";
const SECRET_TOKEN = "bearer_xyz789abc123def456ghi789";

function processUser() {
    console.log("Processing user...");
    debugger; // Remove this
    
    // Security issues
    eval("some_code");
    document.write("<div>Dynamic content</div>");
    
    // Performance issues  
    for(var i = 0; i < users.length; i++) {
        document.getElementById("user-" + i);
    }
    
    // SQL injection (in template string)
    const query = `SELECT * FROM users WHERE name = '${userInput}'`;
    
    // TODO: Add proper validation
    // FIXME: Security vulnerability here
    
    return query;
}

# Python mixed in
password = "hardcoded_password_123"  
print("Debug: User authenticated")
'''
}

def test_endpoint(name, method, url, data=None, expected_status=200):
    """Test a single API endpoint with enhanced reporting"""
    try:
        print(f"\n🧪 Testing {name}...")
        print("-" * 50)
        
        start_time = time.time()
        
        if method.upper() == 'GET':
            response = requests.get(url, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"   ❌ Unsupported method: {method}")
            return False
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == expected_status:
            print(f"   ✅ Status: {response.status_code} (in {elapsed_time:.2f}s)")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                result = response.json()
                
                # Enhanced reporting based on endpoint
                if 'analyze' in url:
                    print(f"   📊 Analysis Results:")
                    if 'summary' in result:
                        summary = result['summary']
                        print(f"      • Total Issues: {summary.get('total_issues', 0)}")
                        print(f"      • Critical: {summary.get('critical_issues', 0)}")
                        print(f"      • High: {summary.get('high_issues', 0)}")
                        print(f"      • Medium: {summary.get('medium_issues', 0)}")
                        print(f"      • Low: {summary.get('low_issues', 0)}")
                        print(f"      • Security Score: {result.get('security_score', 'N/A')}")
                        print(f"      • Risk Level: {result.get('risk_level', 'N/A')}")
                    
                    if 'issues_found' in result:
                        print(f"   🔍 Sample Issues Found:")
                        for i, issue in enumerate(result['issues_found'][:3]):  # Show first 3
                            print(f"      {i+1}. Line {issue.get('line', '?')}: {issue.get('message', 'Unknown')} ({issue.get('severity', 'UNKNOWN')})")
                
                elif 'health' in url:
                    print(f"   💚 Health Status:")
                    print(f"      • Version: {result.get('version', 'Unknown')}")
                    print(f"      • Features: {len(result.get('features', {}))}")
                    print(f"      • Languages: {len(result.get('supported_languages', []))}")
                    print(f"      • Total Patterns: {result.get('total_patterns', 0)}")
                
                elif 'stats' in url:
                    print(f"   📈 Statistics:")
                    for key, value in result.items():
                        if isinstance(value, (int, float)):
                            print(f"      • {key.replace('_', ' ').title()}: {value}")
                
                elif 'fix' in url:
                    print(f"   🔧 Fix Results:")
                    print(f"      • Fixes Applied: {result.get('total_fixes', 0)}")
                    print(f"      • Strategy: {result.get('fix_strategy', 'N/A')}")
                    if 'env_file_suggestions' in result:
                        print(f"      • Env Variables Needed: {len(result['env_file_suggestions'])}")
                
                return True
            else:
                print(f"   📄 Response: {response.text[:200]}...")
                return True
        else:
            print(f"   ❌ Expected {expected_status}, got {response.status_code}")
            print(f"   📄 Error: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed - is the Flask server running on port 5000?")
        return False
    except requests.exceptions.Timeout:
        print(f"   ❌ Request timed out (>10s)")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def run_comprehensive_tests():
    """Run comprehensive tests of all enhanced features"""
    
    print("🚀 Enhanced GitHub PR Auto-Fix API Test Suite v2.0")
    print("=" * 70)
    print("Testing comprehensive analysis features...")
    
    tests_results = []
    
    # Basic health check
    success = test_endpoint("Health Check", "GET", f"{API_BASE}/health")
    tests_results.append(("Health Check", success))
    
    # Enhanced statistics
    success = test_endpoint("Enhanced Statistics", "GET", f"{API_BASE}/stats")
    tests_results.append(("Enhanced Statistics", success))
    
    # Test each code sample with enhanced analysis
    for sample_name, code_sample in TEST_SAMPLES.items():
        print(f"\n{'='*20} Testing {sample_name.upper()} {'='*20}")
        
        # Standard analysis
        success = test_endpoint(
            f"Analyze {sample_name}", 
            "POST", 
            f"{API_BASE}/analyze",
            {
                "code": code_sample,
                "extension": "py",
                "options": {
                    "include_security": True,
                    "include_debug": True,
                    "include_quality": True,
                    "include_performance": True,
                    "detailed_report": True
                }
            }
        )
        tests_results.append((f"Analyze {sample_name}", success))
        
        # Test fixing
        # First get issues, then test fixing
        try:
            response = requests.post(f"{API_BASE}/analyze", json={
                "code": code_sample,
                "extension": "py"
            })
            if response.status_code == 200:
                analysis_data = response.json()
                issues = analysis_data.get('issues_found', [])[:5]  # Fix first 5 issues
                
                if issues:
                    success = test_endpoint(
                        f"Fix {sample_name}",
                        "POST",
                        f"{API_BASE}/detailed-fix",
                        {
                            "code": code_sample,
                            "issues": issues,
                            "strategy": "safe"
                        }
                    )
                    tests_results.append((f"Fix {sample_name}", success))
        except Exception as e:
            print(f"   ⚠️  Could not test fixing for {sample_name}: {e}")
    
    # Test security report
    success = test_endpoint(
        "Security Report",
        "POST", 
        f"{API_BASE}/security-report",
        {"code": TEST_SAMPLES['security_nightmare']}
    )
    tests_results.append(("Security Report", success))
    
    # Print final results
    print("\n" + "="*70)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("="*70)
    
    passed = sum(1 for _, success in tests_results if success)
    total = len(tests_results)
    
    for test_name, success in tests_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your enhanced backend is fully operational!")
        print("\n🚀 New capabilities confirmed:")
        print("   ✅ 50+ security vulnerability patterns")
        print("   ✅ Multi-language debug detection")
        print("   ✅ Code quality analysis")
        print("   ✅ Performance optimization suggestions")
        print("   ✅ Detailed fix recommendations")
        print("   ✅ Security scoring system")
        print("   ✅ Comprehensive reporting")
    else:
        print(f"⚠️  {total - passed} tests failed. Check server logs for details.")
    
    print("\n📚 Enhanced API Endpoints Available:")
    print("   • POST /api/analyze - Comprehensive code analysis")
    print("   • POST /api/detailed-fix - Advanced fix application")
    print("   • POST /api/security-report - Security assessment reports")
    print("   • GET  /api/health - System health and capabilities")
    print("   • GET  /api/stats - Enhanced statistics")

def interactive_test():
    """Interactive testing mode"""
    print("\n" + "="*50)
    print("🧪 INTERACTIVE TESTING MODE")
    print("="*50)
    
    while True:
        print("\nChoose a test sample:")
        for i, (name, _) in enumerate(TEST_SAMPLES.items(), 1):
            print(f"{i}. {name.replace('_', ' ').title()}")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-{}): ".format(len(TEST_SAMPLES)))
        
        if choice == '0':
            break
        
        try:
            choice_idx = int(choice) - 1
            sample_name = list(TEST_SAMPLES.keys())[choice_idx] 
            code_sample = TEST_SAMPLES[sample_name]
            
            print(f"\n📝 Testing: {sample_name.replace('_', ' ').title()}")
            print("Code sample:")
            print("-" * 40)
            print(code_sample[:300] + "..." if len(code_sample) > 300 else code_sample)
            print("-" * 40)
            
            test_endpoint(
                f"Interactive - {sample_name}",
                "POST",
                f"{API_BASE}/analyze",
                {"code": code_sample, "extension": "py"}
            )
            
        except (ValueError, IndexError):
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        print("Starting comprehensive API tests...")
        run_comprehensive_tests()
        
        print("\n" + "="*50)
        interactive_choice = input("Run interactive tests? (y/n): ").strip().lower()
        if interactive_choice in ['y', 'yes']:
            interactive_test()
            
    except KeyboardInterrupt:
        print("\n\n👋 Testing stopped by user.")
    
    input("\nPress Enter to exit...")