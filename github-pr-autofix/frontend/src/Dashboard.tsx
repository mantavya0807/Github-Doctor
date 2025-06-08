import React, { useState, useEffect } from 'react';
import { Activity, GitPullRequest, Shield, Bug, TestTube, Settings, RefreshCw, ExternalLink, Bot, Brain, Zap, Wand2, CheckCircle2 } from 'lucide-react';
import AgentPanel from './AgentPanel';

interface PR {
  id: number;
  number: number;
  title: string;
  repository: string;
  author: string;
  created_at: string;
  status: string;
  issues_found: any[];
  fixes_applied: any[];
  url?: string;
  analyzed_at?: string;
  files_analyzed?: number;
  total_issues?: number;
  security_score?: number;
  risk_level?: string;
  state?: string;
  fixes_generated?: number;
  ai_fixes_available?: number;
}

interface Stats {
  secrets_fixed: number;
  debug_statements_removed: number;
  tests_generated: number;
  total_prs_processed: number;
  security_vulnerabilities_fixed?: number;
  code_quality_improvements?: number;
  performance_issues_fixed?: number;
  documentation_added?: number;
  ai_fixes_applied?: number;
  rule_based_fixes_applied?: number;
}

interface Issue {
  type: string;
  line: number;
  message: string;
  match: string;
  fix_available: boolean;
  severity?: string;
  category?: string;
  ai_fix_available?: boolean;
}

interface IntelligentFix {
  original_code: string;
  fixed_code: string;
  explanation: string;
  env_vars_needed: string[];
  confidence: string;
  fix_type: string;
  line: number;
  applied: boolean;
}

interface AIStatus {
  available: boolean;
  configured: boolean;
  status: string;
  fix_types: string[];
}

const Dashboard: React.FC = () => {
  const [prs, setPRs] = useState<PR[]>([]);
  const [stats, setStats] = useState<Stats>({
    secrets_fixed: 0,
    debug_statements_removed: 0,
    tests_generated: 0,
    total_prs_processed: 0
  });
  const [aiStatus, setAIStatus] = useState<AIStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [codeInput, setCodeInput] = useState('');
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [intelligentFixes, setIntelligentFixes] = useState<IntelligentFix[]>([]);
  const [showFixesPanel, setShowFixesPanel] = useState(false);
  const [applyingFixes, setApplyingFixes] = useState(false);
  const [serverStatus, setServerStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [prUrl, setPrUrl] = useState('');
  const [prAnalysisResult, setPrAnalysisResult] = useState<any>(null);
  const [isAnalyzingPR, setIsAnalyzingPR] = useState(false);

  const API_BASE = 'http://localhost:5000/api';

  // Check server health and AI status
  const checkServerHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      if (response.ok) {
        const healthData = await response.json();
        setServerStatus('online');
        
        // Extract AI status from health check
        if (healthData.ai_integration) {
          setAIStatus(healthData.ai_integration);
        }
      } else {
        setServerStatus('offline');
      }
    } catch (error) {
      setServerStatus('offline');
    }
  };

  // Fetch AI status separately
  const fetchAIStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/ai-status`);
      if (response.ok) {
        const data = await response.json();
        setAIStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch AI status:', error);
    }
  };

  // Fetch PR history
  const fetchPRHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/pr-history`);
      if (response.ok) {
        const data = await response.json();
        setPRs(data.prs || []);
      }
    } catch (error) {
      console.error('Failed to fetch PR history:', error);
    }
  };

  // Fetch enhanced stats with AI metrics
  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  // Analyze GitHub PR with AI fixes
  const analyzeGitHubPR = async () => {
    if (!prUrl.trim()) return;
    
    setIsAnalyzingPR(true);
    try {
      const response = await fetch(`${API_BASE}/analyze-github-pr`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pr_url: prUrl,
          generate_fixes: true  // Enable AI fix generation
        })
      });
      
      const result = await response.json();
      
      if (response.ok) {
        setPrAnalysisResult(result);
        // Also refresh PR history to show the new PR
        await fetchPRHistory();
        await fetchStats(); // Update stats with new analysis
      } else {
        setPrAnalysisResult({
          status: 'error',
          message: result.message || 'Failed to analyze GitHub PR'
        });
      }
    } catch (error) {
      console.error('GitHub PR analysis failed:', error);
      setPrAnalysisResult({
        status: 'error',
        message: 'Network error: Could not connect to server'
      });
    } finally {
      setIsAnalyzingPR(false);
    }
  };

  // Enhanced code analysis with AI fixes
  const analyzeCode = async () => {
    if (!codeInput.trim()) return;
    
    setIsLoading(true);
    setIntelligentFixes([]);
    setShowFixesPanel(false);
    
    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: codeInput,
          extension: 'py',
          generate_fixes: true  // Enable AI fix generation
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setAnalysisResult(result);
        
        // Extract intelligent fixes if available
        if (result.intelligent_fixes && result.intelligent_fixes.length > 0) {
          setIntelligentFixes(result.intelligent_fixes);
          setShowFixesPanel(true);
        }
      }
    } catch (error) {
      console.error('Analysis failed:', error);
      setAnalysisResult({
        status: 'error',
        message: 'Failed to analyze code'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Apply AI-generated fixes
  const applyIntelligentFixes = async () => {
    if (!intelligentFixes.length) return;
    
    setApplyingFixes(true);
    try {
      const response = await fetch(`${API_BASE}/apply-fixes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: codeInput,
          fixes: intelligentFixes
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        
        // Update the code input with fixed code
        if (result.fixed_code) {
          setCodeInput(result.fixed_code);
        }
        
        // Show success message
        alert(`Applied ${result.fixes_applied}/${result.total_fixes_attempted} fixes successfully! Success rate: ${result.success_rate.toFixed(1)}%`);
        
        // Update stats
        await fetchStats();
        
        // Re-analyze to show remaining issues
        setTimeout(() => {
          analyzeCode();
        }, 1000);
        
      } else {
        alert('Failed to apply fixes');
      }
    } catch (error) {
      console.error('Failed to apply fixes:', error);
      alert('Error applying fixes');
    } finally {
      setApplyingFixes(false);
    }
  };

  // Refresh all data
  const refreshData = async () => {
    setIsLoading(true);
    await Promise.all([
      checkServerHealth(),
      fetchPRHistory(),
      fetchStats(),
      fetchAIStatus()
    ]);
    setIsLoading(false);
  };

  useEffect(() => {
    refreshData();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-500';
      case 'offline': return 'text-red-500';
      default: return 'text-yellow-500';
    }
  };

  const getIssueTypeIcon = (type: string) => {
    switch (type) {
      case 'secret_exposure': return <Shield className="w-4 h-4 text-red-500" />;
      case 'debug_statement': return <Bug className="w-4 h-4 text-yellow-500" />;
      case 'missing_test': return <TestTube className="w-4 h-4 text-blue-500" />;
      default: return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL': return 'text-red-600 bg-red-50';
      case 'HIGH': return 'text-orange-600 bg-orange-50';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-50';
      case 'LOW': return 'text-blue-600 bg-blue-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel?.toUpperCase()) {
      case 'CRITICAL': return 'text-red-600';
      case 'HIGH': return 'text-orange-600';
      case 'MEDIUM': return 'text-yellow-600';
      case 'LOW': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getFixTypeIcon = (fixType: string) => {
    switch (fixType) {
      case 'ai_generated': return <Brain className="w-4 h-4 text-purple-500" />;
      case 'rule_based': return <Wand2 className="w-4 h-4 text-blue-500" />;
      default: return <CheckCircle2 className="w-4 h-4 text-green-500" />;
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence?.toUpperCase()) {
      case 'HIGH': return 'bg-green-100 text-green-800';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800';
      case 'LOW': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                GitHub PR Auto-Fix Dashboard
                {aiStatus?.configured && (
                  <span className="ml-3 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                    <Brain className="h-4 w-4 mr-1" />
                    AI-Powered
                  </span>
                )}
              </h1>
              <p className="text-gray-600 mt-1">
                Automated code quality and security fixes for your pull requests
                {aiStatus?.configured && (
                  <span className="text-purple-600 ml-2">• Enhanced with AI intelligence</span>
                )}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {/* AI Status Indicator */}
              {aiStatus && (
                <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
                  aiStatus.configured ? 'bg-purple-50 text-purple-700' : 'bg-yellow-50 text-yellow-700'
                }`}>
                  <Brain className={`w-4 h-4 ${aiStatus.configured ? 'text-purple-500' : 'text-yellow-500'}`} />
                  <span className="text-sm font-medium">
                    AI: {aiStatus.configured ? 'Ready' : 'Setup Required'}
                  </span>
                </div>
              )}
              
              {/* Server Status */}
              <div className={`flex items-center space-x-2 ${getStatusColor(serverStatus)}`}>
                <div className={`w-2 h-2 rounded-full ${serverStatus === 'online' ? 'bg-green-500' : serverStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'}`}></div>
                <span className="text-sm font-medium">
                  {serverStatus === 'online' ? 'Server Online' : serverStatus === 'offline' ? 'Server Offline' : 'Checking...'}
                </span>
              </div>
              
              <button
                onClick={refreshData}
                disabled={isLoading}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Enhanced Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <GitPullRequest className="h-6 w-6 text-blue-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      PRs Processed
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.total_prs_processed}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Shield className="h-6 w-6 text-red-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Secrets Fixed
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.secrets_fixed}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Brain className="h-6 w-6 text-purple-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      AI Fixes Applied
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.ai_fixes_applied || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Zap className="h-6 w-6 text-yellow-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Fixes Applied
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {(stats.ai_fixes_applied || 0) + (stats.rule_based_fixes_applied || 0)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* AI Agent Panel */}
        <div className="mb-8">
          <AgentPanel />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* GitHub PR Analysis Panel */}
          <div className="lg:col-span-1 bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                GitHub PR Analysis
                {aiStatus?.configured && (
                  <Brain className="h-4 w-4 ml-2 text-purple-500" />
                )}
              </h3>
              <p className="text-sm text-gray-600">
                Analyze a GitHub Pull Request {aiStatus?.configured ? 'with AI-powered fixes' : 'directly'}
              </p>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    GitHub PR URL:
                  </label>
                  <input
                    type="url"
                    value={prUrl}
                    onChange={(e) => setPrUrl(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="https://github.com/owner/repo/pull/123"
                  />
                </div>
                <button
                  onClick={analyzeGitHubPR}
                  disabled={isAnalyzingPR || !prUrl.trim()}
                  className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAnalyzingPR ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing PR...
                    </>
                  ) : (
                    <>
                      <GitPullRequest className="w-4 h-4 mr-2" />
                      {aiStatus?.configured ? 'Analyze with AI' : 'Analyze GitHub PR'}
                    </>
                  )}
                </button>

                {/* Enhanced GitHub PR Analysis Results */}
                {prAnalysisResult && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-md">
                    <h4 className="font-medium text-gray-900 mb-2">GitHub PR Analysis Results:</h4>
                    {prAnalysisResult.status === 'error' ? (
                      <div className="text-red-600">
                        <p className="font-medium">Error:</p>
                        <p className="text-sm">{prAnalysisResult.message}</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="bg-white p-3 rounded border">
                          <p className="text-sm font-medium text-gray-900">
                            {prAnalysisResult.pr_info?.title}
                          </p>
                          <p className="text-xs text-gray-500">
                            #{prAnalysisResult.pr_info?.number} • {prAnalysisResult.pr_info?.repository} • by {prAnalysisResult.pr_info?.author}
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            State: {prAnalysisResult.pr_info?.state}
                          </p>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div className="bg-blue-50 p-2 rounded">
                            <p className="font-medium text-blue-900">Files Analyzed</p>
                            <p className="text-blue-700">{prAnalysisResult.analysis_summary?.files_analyzed || 0}</p>
                          </div>
                          <div className="bg-red-50 p-2 rounded">
                            <p className="font-medium text-red-900">Total Issues</p>
                            <p className="text-red-700">{prAnalysisResult.analysis_summary?.total_issues || 0}</p>
                          </div>
                          <div className="bg-yellow-50 p-2 rounded">
                            <p className="font-medium text-yellow-900">Security Score</p>
                            <p className="text-yellow-700">{prAnalysisResult.analysis_summary?.security_score || 0}/100</p>
                          </div>
                          <div className="bg-purple-50 p-2 rounded">
                            <p className="font-medium text-purple-900">Risk Level</p>
                            <p className="text-purple-700">{prAnalysisResult.analysis_summary?.risk_level || 'Unknown'}</p>
                          </div>
                        </div>

                        {/* AI Fixes Summary */}
                        {prAnalysisResult.analysis_summary?.ai_fixes_available > 0 && (
                          <div className="bg-purple-100 border border-purple-200 p-2 rounded">
                            <p className="text-purple-800 text-xs font-medium flex items-center">
                              <Brain className="w-3 h-3 mr-1" />
                              {prAnalysisResult.analysis_summary.ai_fixes_available} AI-powered fixes generated!
                            </p>
                          </div>
                        )}

                        {prAnalysisResult.analysis_summary?.critical_issues > 0 && (
                          <div className="bg-red-100 border border-red-200 p-2 rounded">
                            <p className="text-red-800 text-xs font-medium">
                              ⚠️ {prAnalysisResult.analysis_summary.critical_issues} Critical Security Issues Found!
                            </p>
                          </div>
                        )}

                        {prAnalysisResult.files_analyzed && prAnalysisResult.files_analyzed.length > 0 && (
                          <div className="space-y-2">
                            <p className="text-sm font-medium text-gray-700">Files with Issues:</p>
                            {prAnalysisResult.files_analyzed.map((file: any, index: number) => (
                              <div key={index} className="text-xs bg-white p-2 border rounded">
                                <p className="font-medium flex items-center">
                                  {file.filename}
                                  {file.fixes_count > 0 && (
                                    <span className="ml-2 px-1 py-0.5 bg-purple-100 text-purple-800 rounded text-xs">
                                      <Brain className="w-3 h-3 inline mr-1" />
                                      {file.fixes_count} fixes
                                    </span>
                                  )}
                                </p>
                                <p className="text-gray-600">
                                  {file.issues_count} issues • {file.additions} additions • {file.deletions} deletions
                                </p>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Environment Variables Needed */}
                        {prAnalysisResult.env_vars_needed && prAnalysisResult.env_vars_needed.length > 0 && (
                          <div className="bg-yellow-50 p-2 rounded border border-yellow-200">
                            <p className="text-yellow-800 text-xs font-medium">Environment Variables Needed:</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {prAnalysisResult.env_vars_needed.map((envVar: string, index: number) => (
                                <span key={index} className="bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded text-xs">
                                  {envVar}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Enhanced Code Analysis Panel */}
          <div className="lg:col-span-1 bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                Manual Code Analysis
                {aiStatus?.configured && (
                  <Brain className="h-4 w-4 ml-2 text-purple-500" />
                )}
              </h3>
              <p className="text-sm text-gray-600">
                Test code analysis {aiStatus?.configured ? 'with AI-powered fixes' : 'manually'}
              </p>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Paste your code here:
                  </label>
                  <textarea
                    value={codeInput}
                    onChange={(e) => setCodeInput(e.target.value)}
                    className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                    placeholder="# Example with secrets and debug statements:&#10;api_key = 'sk_live_1234567890'&#10;print(f'Debug: API key is {api_key}')&#10;password = 'secret123'&#10;console.log('Debug message')"
                  />
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={analyzeCode}
                    disabled={isLoading || !codeInput.trim()}
                    className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        {aiStatus?.configured ? <Brain className="w-4 h-4 mr-2" /> : <Activity className="w-4 h-4 mr-2" />}
                        {aiStatus?.configured ? 'Analyze with AI' : 'Analyze Code'}
                      </>
                    )}
                  </button>
                  
                  {showFixesPanel && intelligentFixes.length > 0 && (
                    <button
                      onClick={applyIntelligentFixes}
                      disabled={applyingFixes}
                      className="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {applyingFixes ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <Wand2 className="w-4 h-4" />
                      )}
                    </button>
                  )}
                </div>

                {/* Enhanced Analysis Results */}
                {analysisResult && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-md">
                    <h4 className="font-medium text-gray-900 mb-2">Analysis Results:</h4>
                    {analysisResult.status === 'error' ? (
                      <p className="text-red-600">{analysisResult.message}</p>
                    ) : (
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <p className="text-sm text-gray-600">
                            Found {analysisResult.total_issues || analysisResult.issues_found?.length || 0} issues
                          </p>
                          <div className="flex items-center space-x-2">
                            {analysisResult.security_score && (
                              <span className="text-xs font-medium text-gray-900">
                                Security: {analysisResult.security_score}/100
                              </span>
                            )}
                            {analysisResult.intelligent_fixes && (
                              <span className="text-xs font-medium text-purple-700 bg-purple-100 px-2 py-1 rounded">
                                <Brain className="w-3 h-3 inline mr-1" />
                                {analysisResult.intelligent_fixes.length} AI fixes
                              </span>
                            )}
                          </div>
                        </div>
                        
                        {/* Issues List */}
                        {(analysisResult.issues_found || []).map((issue: Issue, index: number) => (
                          <div key={index} className="flex items-start space-x-2 p-2 bg-white rounded border">
                            {getIssueTypeIcon(issue.type)}
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-900">
                                Line {issue.line}: {issue.message}
                              </p>
                              <p className="text-xs text-gray-500 font-mono mt-1">
                                {issue.match?.length > 50 ? issue.match.substring(0, 50) + '...' : issue.match}
                              </p>
                            </div>
                            <div className="flex flex-col items-end space-y-1">
                              {issue.ai_fix_available && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                  <Brain className="w-3 h-3 mr-1" />
                                  AI Fix
                                </span>
                              )}
                              {issue.fix_available && !issue.ai_fix_available && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  Fixable
                                </span>
                              )}
                              {issue.severity && (
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(issue.severity)}`}>
                                  {issue.severity}
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* AI Fixes Panel */}
                {showFixesPanel && intelligentFixes.length > 0 && (
                  <div className="mt-4 p-4 bg-purple-50 rounded-md border border-purple-200">
                    <h4 className="font-medium text-purple-900 mb-2 flex items-center">
                      <Brain className="w-4 h-4 mr-2" />
                      AI-Generated Fixes ({intelligentFixes.length})
                    </h4>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {intelligentFixes.map((fix, index) => (
                        <div key={index} className="bg-white p-3 rounded border">
                          <div className="flex items-center space-x-2 mb-2">
                            {getFixTypeIcon(fix.fix_type)}
                            <span className="text-sm font-medium text-gray-900">
                              Line {fix.line}: {fix.explanation}
                            </span>
                            <span className={`px-2 py-0.5 rounded-full text-xs ${getConfidenceColor(fix.confidence)}`}>
                              {fix.confidence}
                            </span>
                          </div>
                          
                          {fix.original_code && (
                            <div className="mt-2 text-xs">
                              <p className="text-gray-600 font-medium">Original:</p>
                              <code className="bg-red-50 text-red-800 px-2 py-1 rounded block mt-1">
                                {fix.original_code}
                              </code>
                            </div>
                          )}
                          
                          {fix.fixed_code && (
                            <div className="mt-2 text-xs">
                              <p className="text-gray-600 font-medium">Fixed:</p>
                              <code className="bg-green-50 text-green-800 px-2 py-1 rounded block mt-1">
                                {fix.fixed_code}
                              </code>
                            </div>
                          )}
                          
                          {fix.env_vars_needed && fix.env_vars_needed.length > 0 && (
                            <div className="mt-2 text-xs">
                              <p className="text-gray-600 font-medium">Environment Variables:</p>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {fix.env_vars_needed.map((envVar, envIndex) => (
                                  <span key={envIndex} className="bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                                    {envVar}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Recent PRs Panel */}
          <div className="lg:col-span-1 bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Pull Requests</h3>
              <p className="text-sm text-gray-600">Recently analyzed PRs and their status</p>
            </div>
            <div className="p-6">
              {prs.length === 0 ? (
                <div className="text-center py-8">
                  <GitPullRequest className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No PRs analyzed yet</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Use the GitHub PR Analysis tool above to analyze pull requests
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {prs.slice(0, 5).map((pr) => (
                    <div key={pr.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-gray-900">
                            #{pr.number} {pr.title}
                          </h4>
                          <p className="text-xs text-gray-500 mt-1">
                            {pr.repository} • by {pr.author}
                          </p>
                          {pr.url && (
                            <a 
                              href={pr.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-xs text-blue-600 hover:text-blue-800 mt-1 inline-flex items-center"
                            >
                              View on GitHub <ExternalLink className="w-3 h-3 ml-1" />
                            </a>
                          )}
                          <p className="text-xs text-gray-400 mt-1">
                            {pr.analyzed_at ? 
                              `Analyzed: ${new Date(pr.analyzed_at).toLocaleDateString()}` :
                              `Created: ${new Date(pr.created_at).toLocaleDateString()}`
                            }
                          </p>
                        </div>
                        <div className="text-right">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            pr.status === 'analyzed' ? 'bg-green-100 text-green-800' : 
                            pr.status === 'pending_analysis' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {pr.status.replace('_', ' ')}
                          </span>
                          {pr.risk_level && (
                            <p className={`text-xs mt-1 font-medium ${getRiskLevelColor(pr.risk_level)}`}>
                              {pr.risk_level} Risk
                            </p>
                          )}
                          {pr.ai_fixes_available && pr.ai_fixes_available > 0 && (
                            <p className="text-xs mt-1 font-medium text-purple-600">
                              <Brain className="w-3 h-3 inline mr-1" />
                              {pr.ai_fixes_available} AI fixes
                            </p>
                          )}
                        </div>
                      </div>
                      {((pr.total_issues ?? 0) > 0 || (pr.issues_found?.length ?? 0) > 0) && (
                        <div className="mt-2 text-xs text-gray-600">
                          {pr.total_issues ?? pr.issues_found?.length ?? 0} issues found
                          {pr.security_score && ` • Security Score: ${pr.security_score}/100`}
                          {pr.files_analyzed && ` • ${pr.files_analyzed} files analyzed`}
                          {pr.fixes_generated && ` • ${pr.fixes_generated} fixes generated`}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;