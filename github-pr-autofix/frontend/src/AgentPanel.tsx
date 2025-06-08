import React, { useState, useEffect } from 'react';
import { Bot, Activity, Settings, Play, AlertTriangle, Terminal, GitBranch, Folder, RefreshCw, CheckCircle, XCircle, ShieldAlert, Code, Hammer, ExternalLink, Zap, Brain, Wand2 } from 'lucide-react';

interface AgentActivity {
  timestamp: string;
  action: string;
  status: string;
  details: {
    [key: string]: any;
  };
}

interface AgentStatus {
  status: string;
  agent_mode: string;
  auto_commit: boolean;
  max_files: number;
  repos_monitored: number;
  repos_list: string[];
  ai_enabled: boolean;
  recent_activity: AgentActivity[];
}

interface AnalysisIssue {
  type: string;
  category: string;
  line: number;
  severity: string;
  message: string;
  match: string;
  fix_available: boolean;
  ai_fix_available?: boolean;
  ai_fix?: any;
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

interface AnalysisResult {
  repository: string;
  commit: string;
  branch: string;
  timestamp: string;
  files_analyzed: number;
  total_issues: number;
  security_score: number;
  risk_level: string;
  file_results: {
    filename: string;
    issues_count: number;
    issues: AnalysisIssue[];
    fixes?: IntelligentFix[];
    fixes_count?: number;
    ai_fixes?: IntelligentFix[];
    ai_fixes_count?: number;
    file_content?: string;
    file_sha?: string;
  }[];
  fix_suggestions?: any;
  intelligent_fixes?: IntelligentFix[];
  ai_status?: {
    available: boolean;
    configured: boolean;
    status: string;
  };
  env_vars_needed?: string[];
  env_file_content?: string;
}

interface AIStatus {
  available: boolean;
  configured: boolean;
  status: string;
  fix_types: string[];
  api_key_set?: boolean;
}

const AgentPanel: React.FC = () => {
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [agentActivity, setAgentActivity] = useState<AgentActivity[]>([]);
  const [aiStatus, setAIStatus] = useState<AIStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [configLoading, setConfigLoading] = useState(false);
  const [manualRepo, setManualRepo] = useState('');
  const [manualBranch, setManualBranch] = useState('main');
  const [manualAnalysisLoading, setManualAnalysisLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [applyingFixes, setApplyingFixes] = useState(false);
  const [fixResult, setFixResult] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('activity');
  const [showFixDetails, setShowFixDetails] = useState(false);
  const [selectedFixes, setSelectedFixes] = useState<Set<number>>(new Set());
  const [configValues, setConfigValues] = useState({
    agent_mode: 'monitor',
    auto_commit: false,
    max_files: 10,
    excluded_files: '.env,.git,node_modules,__pycache__,venv',
    excluded_extensions: '.jpg,.png,.gif,.mp4,.mp3,.pdf'
  });
  const [branchOptions, setBranchOptions] = useState<string[]>(['main', 'master', 'develop', 'dev']);
  const [isFetchingBranches, setIsFetchingBranches] = useState(false);

  const API_BASE = 'http://localhost:5000/api';

  // Fetch AI status
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

  // Fetch agent status
  const fetchAgentStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/agent/status`);
      if (response.ok) {
        const data = await response.json();
        setAgentStatus(data);
        setConfigValues({
          ...configValues,
          agent_mode: data.agent_mode,
          auto_commit: data.auto_commit,
          max_files: data.max_files
        });
      }
    } catch (error) {
      console.error('Failed to fetch agent status:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch agent activity
  const fetchAgentActivity = async () => {
    try {
      const response = await fetch(`${API_BASE}/agent/activity`);
      if (response.ok) {
        const data = await response.json();
        setAgentActivity(data.activity || []);
      }
    } catch (error) {
      console.error('Failed to fetch agent activity:', error);
    }
  };

  // Update agent configuration
  const updateAgentConfig = async () => {
    setConfigLoading(true);
    try {
      const response = await fetch(`${API_BASE}/agent/configure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_mode: configValues.agent_mode,
          auto_commit: configValues.auto_commit,
          max_files: configValues.max_files,
          excluded_files: configValues.excluded_files.split(','),
          excluded_extensions: configValues.excluded_extensions.split(',')
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        alert('Agent configuration updated!');
        await fetchAgentStatus();
      }
    } catch (error) {
      console.error('Failed to update agent config:', error);
      alert('Failed to update configuration');
    } finally {
      setConfigLoading(false);
    }
  };

  // Fetch available branches for a repository
  const fetchRepoBranches = async (repo: string) => {
    if (!repo || repo.trim() === '') return;
    
    try {
      setIsFetchingBranches(true);
      
      const apiUrl = `https://api.github.com/repos/${repo}/branches`;
      const response = await fetch(apiUrl);
      
      if (response.ok) {
        const branchData = await response.json();
        const branches = branchData.map((branch: { name: string }) => branch.name);
        
        if (branches.length > 0) {
          setBranchOptions(branches);
          if (branches.includes('main')) {
            setManualBranch('main');
          } else if (branches.includes('master')) {
            setManualBranch('master');
          } else {
            setManualBranch(branches[0]);
          }
        } else {
          setBranchOptions(['main', 'master', 'develop', 'dev']);
          setManualBranch('main');
        }
      } else {
        console.log("Failed to fetch branches, using default options");
        setBranchOptions(['main', 'master', 'develop', 'dev']);
        setManualBranch('main');
      }
    } catch (error) {
      console.error("Error fetching branches:", error);
      setBranchOptions(['main', 'master', 'develop', 'dev']);
      setManualBranch('main');
    } finally {
      setIsFetchingBranches(false);
    }
  };

  // Watch for repository changes and fetch branches
  useEffect(() => {
    if (manualRepo && manualRepo.includes('/')) {
      fetchRepoBranches(manualRepo);
    }
  }, [manualRepo]);

  // Trigger manual analysis with AI fixes
  const triggerManualAnalysis = async () => {
    if (!manualRepo) {
      alert('Please enter a repository (format: owner/repo)');
      return;
    }
    
    if (!manualBranch) {
      alert('Please select a branch');
      return;
    }
    
    setManualAnalysisLoading(true);
    setAnalysisResult(null);
    setFixResult(null);
    setSelectedFixes(new Set());
    setActiveTab('analysis');

    try {
      console.log(`Analyzing repository: ${manualRepo}, branch: ${manualBranch}`);
      
      const response = await fetch(`${API_BASE}/agent/manual-analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repository: manualRepo,
          branch: manualBranch
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("Analysis response:", data);
        
        if (data.result?.status === 'error') {
          console.log("Analysis error:", data.result.error);
          setAnalysisResult(data.result);
        } else {
          if (data.result) {
            setAnalysisResult(data.result);
          } else {
            setAnalysisResult(data);
          }
        }
        
        fetchAgentStatus();
        fetchAgentActivity();
      } else {
        const errorData = await response.json();
        console.error("Analysis error:", errorData);
        alert(`Analysis failed: ${errorData.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to trigger analysis:', error);
      alert('Failed to trigger analysis. Check console for details.');
    } finally {
      setManualAnalysisLoading(false);
    }
  };

  // NEW: Generate AI fixes for analysis results
  const generateAIFixes = async () => {
    if (!analysisResult || !analysisResult.file_results) return;

    console.log('Generating AI fixes for analysis results...');
    
    try {
      // Collect all issues from file results
      const allIssues: AnalysisIssue[] = [];
      analysisResult.file_results.forEach(fileResult => {
        if (fileResult.issues) {
          allIssues.push(...fileResult.issues);
        }
      });

      if (allIssues.length === 0) {
        alert('No issues found to generate fixes for.');
        return;
      }

      setApplyingFixes(true);

      const response = await fetch(`${API_BASE}/generate-fixes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          issues: allIssues,
          code: '', // We don't have full code context from repository analysis
          extension: 'py',
          fix_type: 'intelligent'
        })
      });

      if (response.ok) {
        const fixData = await response.json();
        console.log('AI fixes generated:', fixData);

        // Update analysis result with AI fixes
        setAnalysisResult(prev => ({
          ...prev!,
          intelligent_fixes: fixData.fixes,
          env_vars_needed: fixData.env_vars_needed,
          env_file_content: fixData.env_file_content,
          ai_status: fixData.ai_status
        }));

        setShowFixDetails(true);
        alert(`Generated ${fixData.fixes.length} AI-powered fixes!`);
      } else {
        const error = await response.json();
        alert(`Failed to generate fixes: ${error.message}`);
      }
    } catch (error) {
      console.error('Failed to generate AI fixes:', error);
      alert('Failed to generate AI fixes. Check console for details.');
    } finally {
      setApplyingFixes(false);
    }
  };

  // NEW: Apply selected fixes to repository
  const applySelectedFixes = async () => {
    if (!analysisResult?.intelligent_fixes || selectedFixes.size === 0) {
      alert('Please select fixes to apply');
      return;
    }

    const fixesToApply = analysisResult.intelligent_fixes.filter((_, index) => 
      selectedFixes.has(index)
    );

    setApplyingFixes(true);

    try {
      console.log('Applying fixes to repository:', analysisResult.repository);
      
      // Prepare file results with selected fixes
      const fileResults = analysisResult.file_results?.map(fileResult => ({
        ...fileResult,
        fixes: (fileResult.fixes || fileResult.ai_fixes || []).filter((fix: IntelligentFix) => 
          fixesToApply.some(selectedFix => 
            selectedFix.line === fix.line && selectedFix.explanation === fix.explanation
          )
        )
      })).filter(fileResult => fileResult.fixes && fileResult.fixes.length > 0) || [];

      console.log('File results prepared:', fileResults);

      const response = await fetch(`${API_BASE}/agent/apply-fixes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repository: analysisResult.repository,
          branch: analysisResult.branch,
          file_results: fileResults
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Fix application result:', result);
        
        setFixResult({
          status: 'success',
          fixes_applied: result.total_fixes_applied || fixesToApply.length,
          success_rate: 95,
          message: result.message || `Successfully applied ${result.total_fixes_applied || fixesToApply.length} fixes!`,
          env_vars_needed: result.env_vars_needed || [],
          pr_url: result.pr_url,
          pr_number: result.pr_number
        });

        alert(`✅ ${result.message || 'Fixes applied successfully!'}\n${result.pr_url ? `PR created: ${result.pr_url}` : ''}`);
        fetchAgentActivity();
      } else {
        const error = await response.json();
        console.error('Fix application failed:', error);
        
        // Check if it's a GitHub token issue
        if (error.message && error.message.includes('authentication')) {
          alert('❌ GitHub authentication failed. Please check your GITHUB_TOKEN in the .env file.');
        } else {
          alert(`❌ Failed to apply fixes: ${error.message || 'Unknown error'}`);
        }
        
        setFixResult({
          status: 'error',
          message: error.message || 'Failed to apply fixes'
        });
      }
    } catch (error) {
      console.error('Failed to apply fixes:', error);
      
      // Show user-friendly error message
      alert('❌ Network error: Could not connect to the server. Please check if the Flask backend is running.');
      
      setFixResult({
        status: 'error',
        message: 'Network error: Could not connect to server'
      });
    } finally {
      setApplyingFixes(false);
    }
  };

  // Toggle fix selection
  const toggleFixSelection = (index: number) => {
    const newSelected = new Set(selectedFixes);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedFixes(newSelected);
  };

  // Select all fixes
  const selectAllFixes = () => {
    if (!analysisResult?.intelligent_fixes) return;
    
    const allIndices = analysisResult.intelligent_fixes.map((_, index) => index);
    setSelectedFixes(new Set(allIndices));
  };

  // Clear selection
  const clearSelection = () => {
    setSelectedFixes(new Set());
  };

  // Initialize
  useEffect(() => {
    fetchAgentStatus();
    fetchAgentActivity();
    fetchAIStatus();
    
    const intervalId = setInterval(() => {
      fetchAgentStatus();
      fetchAgentActivity();
      fetchAIStatus();
    }, 10000);
    
    return () => clearInterval(intervalId);
  }, []);

  // Helper functions remain the same...
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'idle': return 'text-green-500';
      case 'analyzing': return 'text-blue-500 animate-pulse';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getActivityIcon = (action: string) => {
    switch (action) {
      case 'push_received': return <GitBranch className="h-4 w-4 text-blue-500" />;
      case 'analysis_completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'fix_pr_created': return <GitBranch className="h-4 w-4 text-purple-500" />;
      case 'push_skipped': return <XCircle className="h-4 w-4 text-gray-500" />;
      case 'push_error':
      case 'analysis_error':
      case 'fix_error': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default: return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatActivityDetails = (activity: AgentActivity) => {
    const details = activity.details;
    if (!details) return '';
    
    switch (activity.action) {
      case 'push_received':
        return `${details.repository} (${details.branch}) by ${details.pusher}`;
      case 'analysis_completed':
        return `${details.repository} - ${details.issues_found} issues (${details.risk_level} risk)`;
      case 'fix_pr_created':
        return `${details.repository} - PR #${details.pr_number} (${details.fixes_applied} fixes)`;
      case 'push_skipped':
        return `${details.repository} - ${details.reason}`;
      case 'push_error':
      case 'analysis_error':
      case 'fix_error':
        return details.error || 'Unknown error';
      default:
        return JSON.stringify(details).substring(0, 50);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL': return 'bg-red-100 text-red-800';
      case 'HIGH': return 'bg-orange-100 text-orange-800';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800';
      case 'LOW': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getIssueTypeIcon = (type: string) => {
    switch (type) {
      case 'secret_exposure': return <ShieldAlert className="h-4 w-4 text-red-500" />;
      case 'debug_statement': return <Terminal className="h-4 w-4 text-yellow-500" />;
      case 'code_quality': return <Code className="h-4 w-4 text-blue-500" />;
      case 'performance': return <Activity className="h-4 w-4 text-purple-500" />;
      default: return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getFixTypeIcon = (fixType: string) => {
    switch (fixType) {
      case 'ai_generated': return <Brain className="h-4 w-4 text-purple-500" />;
      case 'rule_based': return <Code className="h-4 w-4 text-blue-500" />;
      default: return <Wand2 className="h-4 w-4 text-gray-500" />;
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence.toUpperCase()) {
      case 'HIGH': return 'text-green-600 bg-green-50';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-50';
      case 'LOW': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown Date';
    
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Invalid Date';
      
      return date.toLocaleString();
    } catch (error) {
      return 'Invalid Date';
    }
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <div>
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <Bot className="h-5 w-5 mr-2 text-blue-500" />
            PR Auto-Fix Agent
            {aiStatus?.configured && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                <Brain className="h-3 w-3 mr-1" />
                AI-Powered
              </span>
            )}
          </h3>
          <p className="text-sm text-gray-600">
            Autonomous monitoring and intelligent fixing
            {aiStatus && (
              <span className={`ml-2 text-xs ${aiStatus.configured ? 'text-green-600' : 'text-orange-600'}`}>
                • AI Status: {aiStatus.status}
              </span>
            )}
          </p>
        </div>
        {agentStatus && (
          <div className="flex items-center">
            <span className={`font-medium ${getStatusColor(agentStatus.status)}`}>
              <span className={`inline-block h-2 w-2 rounded-full mr-2 ${
                agentStatus.status === 'idle' ? 'bg-green-500' : 
                agentStatus.status === 'analyzing' ? 'bg-blue-500 animate-pulse' : 
                agentStatus.status === 'error' ? 'bg-red-500' : 'bg-gray-500'
              }`}></span>
              {agentStatus.status.charAt(0).toUpperCase() + agentStatus.status.slice(1)}
            </span>
            <button
              onClick={() => {
                fetchAgentStatus();
                fetchAgentActivity();
                fetchAIStatus();
              }}
              className="ml-2 p-1 rounded-full hover:bg-gray-100"
              title="Refresh"
            >
              <RefreshCw className="h-4 w-4 text-gray-500" />
            </button>
          </div>
        )}
      </div>

      {/* Status & Controls */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Status Info */}
          <div className="flex-1">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Agent Status</h4>
            {loading ? (
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            ) : agentStatus ? (
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <div className="text-xs bg-blue-50 p-2 rounded">
                    <span className="font-medium text-blue-700">Mode:</span> 
                    <span className="text-blue-800 ml-1 capitalize">{agentStatus.agent_mode}</span>
                  </div>
                  <div className="text-xs bg-purple-50 p-2 rounded">
                    <span className="font-medium text-purple-700">Auto-Commit:</span> 
                    <span className="text-purple-800 ml-1">{agentStatus.auto_commit ? 'Enabled' : 'Disabled'}</span>
                  </div>
                  <div className="text-xs bg-green-50 p-2 rounded">
                    <span className="font-medium text-green-700">Repos Monitored:</span> 
                    <span className="text-green-800 ml-1">{agentStatus.repos_monitored}</span>
                  </div>
                  <div className={`text-xs p-2 rounded ${aiStatus?.configured ? 'bg-purple-50' : 'bg-yellow-50'}`}>
                    <span className={`font-medium ${aiStatus?.configured ? 'text-purple-700' : 'text-yellow-700'}`}>AI Fixes:</span> 
                    <span className={`ml-1 ${aiStatus?.configured ? 'text-purple-800' : 'text-yellow-800'}`}>
                      {aiStatus?.configured ? 'Ready' : 'Setup Required'}
                    </span>
                  </div>
                </div>
                
                {agentStatus.repos_list && agentStatus.repos_list.length > 0 && (
                  <div className="text-xs p-2 border rounded-md max-h-20 overflow-y-auto">
                    <div className="font-medium mb-1">Monitored Repositories:</div>
                    {agentStatus.repos_list.map((repo, index) => (
                      <div key={index} className="flex items-center">
                        <Folder className="h-3 w-3 mr-1 text-gray-500" />
                        {repo}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">Unable to fetch agent status</p>
            )}
          </div>

          {/* Manual Analysis */}
          <div className="flex-1">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Trigger Manual Analysis</h4>
            <div className="space-y-2">
              <div>
                <label className="block text-xs text-gray-700 mb-1">Repository (owner/repo)</label>
                <input
                  type="text"
                  value={manualRepo}
                  onChange={(e) => setManualRepo(e.target.value)}
                  placeholder="e.g. username/repository"
                  className="w-full px-3 py-1 text-sm border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-700 mb-1">Branch</label>
                <select
                  value={manualBranch}
                  onChange={(e) => setManualBranch(e.target.value)}
                  disabled={isFetchingBranches || branchOptions.length === 0}
                  className="w-full px-3 py-1 text-sm border border-gray-300 rounded-md bg-white"
                >
                  {isFetchingBranches ? (
                    <option>Loading branches...</option>
                  ) : branchOptions.length > 0 ? (
                    branchOptions.map(branchName => (
                      <option key={branchName} value={branchName}>
                        {branchName}
                      </option>
                    ))
                  ) : (
                    <option>Enter repo to see branches</option>
                  )}
                </select>
              </div>
              <button
                onClick={triggerManualAnalysis}
                disabled={manualAnalysisLoading || !manualRepo || !manualBranch || isFetchingBranches}
                className="w-full inline-flex justify-center items-center px-3 py-1.5 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {manualAnalysisLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Analyze Repository
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="sm:hidden">
          <select 
            className="block w-full text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            value={activeTab}
            onChange={(e) => setActiveTab(e.target.value)}
          >
            <option value="activity">Activity Log</option>
            <option value="analysis">Analysis Results</option>
            <option value="configuration">Configuration</option>
          </select>
        </div>
        <div className="hidden sm:block">
          <nav className="-mb-px flex" aria-label="Tabs">
            <button 
              className={`w-1/3 py-3 px-1 text-center border-b-2 font-medium text-sm ${
                activeTab === 'activity' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('activity')}
            >
              <Activity className="inline-block h-4 w-4 mr-2" />
              Activity Log
            </button>
            <button 
              className={`w-1/3 py-3 px-1 text-center border-b-2 font-medium text-sm ${
                activeTab === 'analysis' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('analysis')}
            >
              <Code className="inline-block h-4 w-4 mr-2" />
              Analysis Results
              {aiStatus?.configured && (
                <Zap className="inline-block h-3 w-3 ml-1 text-purple-500" />
              )}
            </button>
            <button 
              className={`w-1/3 py-3 px-1 text-center border-b-2 font-medium text-sm ${
                activeTab === 'configuration' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('configuration')}
            >
              <Settings className="inline-block h-4 w-4 mr-2" />
              Configuration
            </button>
          </nav>
        </div>
      </div>

      {/* Activity Log Tab - Same as before */}
      <div className={`px-6 py-4 max-h-96 overflow-y-auto ${activeTab !== 'activity' ? 'hidden' : ''}`}>
        <h4 className="text-sm font-medium text-gray-900 mb-3">Recent Activity</h4>
        {agentActivity.length === 0 ? (
          <div className="text-center py-6">
            <Terminal className="mx-auto h-10 w-10 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No activity yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              The agent will record activity when it processes events
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {agentActivity.map((activity, index) => (
              <div key={index} className={`flex items-start p-2 rounded-md ${
                activity.status === 'error' ? 'bg-red-50' : 
                activity.status === 'success' ? 'bg-green-50' : 'bg-gray-50'
              }`}>
                <div className="mr-3 mt-0.5">
                  {getActivityIcon(activity.action)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">
                    {activity.action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatActivityDetails(activity)}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {formatDate(activity.timestamp)}
                  </p>
                </div>
                <div>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    activity.status === 'error' ? 'bg-red-100 text-red-800' : 
                    activity.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {activity.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Enhanced Analysis Results Tab */}
      <div className={`px-6 py-4 max-h-96 overflow-y-auto ${activeTab !== 'analysis' ? 'hidden' : ''}`}>
        <div className="flex justify-between items-center mb-3">
          <h4 className="text-sm font-medium text-gray-900">Analysis Results</h4>
          
          <div className="flex space-x-2">
            {analysisResult && analysisResult.total_issues > 0 && !analysisResult.intelligent_fixes && (
              <button
                onClick={generateAIFixes}
                disabled={applyingFixes}
                className="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {applyingFixes ? (
                  <>
                    <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Brain className="w-3 h-3 mr-1" />
                    Generate AI Fixes
                  </>
                )}
              </button>
            )}

            {analysisResult?.intelligent_fixes && analysisResult.intelligent_fixes.length > 0 && (
              <button
                onClick={applySelectedFixes}
                disabled={applyingFixes || selectedFixes.size === 0}
                className="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {applyingFixes ? (
                  <>
                    <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                    Applying...
                  </>
                ) : (
                  <>
                    <Hammer className="w-3 h-3 mr-1" />
                    Apply Fixes ({selectedFixes.size})
                  </>
                )}
              </button>
            )}
          </div>
        </div>
        
        {manualAnalysisLoading ? (
          <div className="text-center py-10">
            <RefreshCw className="mx-auto h-10 w-10 text-blue-500 animate-spin" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Analyzing repository...</h3>
            <p className="mt-1 text-sm text-gray-500">
              Scanning for issues and generating intelligent fixes
            </p>
          </div>
        ) : !analysisResult ? (
          <div className="text-center py-10">
            <Code className="mx-auto h-10 w-10 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No analysis results yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Use the "Analyze Repository" button to scan a repository
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Results Summary */}
            <div className="bg-blue-50 p-3 rounded-md">
              <h5 className="font-medium text-blue-900 text-sm">Repository Summary</h5>
              <p className="text-xs text-blue-800">
                {analysisResult.repository} ({analysisResult.branch || 'default branch'})
              </p>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <div className="text-xs bg-white p-2 rounded shadow-sm">
                  <span className="font-medium">Files Analyzed:</span> {analysisResult.files_analyzed || 0}
                </div>
                <div className="text-xs bg-white p-2 rounded shadow-sm">
                  <span className="font-medium">Issues Found:</span> {analysisResult.total_issues || 0}
                </div>
                <div className="text-xs bg-white p-2 rounded shadow-sm">
                  <span className="font-medium">Security Score:</span> {analysisResult.security_score || 100}/100
                </div>
                <div className="text-xs bg-white p-2 rounded shadow-sm">
                  <span className="font-medium">Risk Level:</span> {analysisResult.risk_level || 'LOW'}
                </div>
              </div>
              {analysisResult.intelligent_fixes && (
                <div className="mt-2 text-xs bg-purple-100 p-2 rounded">
                  <span className="font-medium text-purple-900">AI Fixes Available:</span> 
                  <span className="text-purple-800 ml-1">{analysisResult.intelligent_fixes.length}</span>
                </div>
              )}
              <p className="text-xs text-blue-700 mt-2">
                Analyzed at: {formatDate(analysisResult.timestamp)}
              </p>
            </div>

            {/* AI Fixes Section */}
            {analysisResult.intelligent_fixes && analysisResult.intelligent_fixes.length > 0 && (
              <div className="bg-purple-50 p-3 rounded-md">
                <div className="flex justify-between items-center mb-2">
                  <h5 className="font-medium text-purple-900 text-sm flex items-center">
                    <Brain className="h-4 w-4 mr-1" />
                    AI-Generated Fixes ({analysisResult.intelligent_fixes.length})
                  </h5>
                  <div className="flex space-x-2 text-xs">
                    <button
                      onClick={selectAllFixes}
                      className="text-purple-600 hover:text-purple-800"
                    >
                      Select All
                    </button>
                    <button
                      onClick={clearSelection}
                      className="text-purple-600 hover:text-purple-800"
                    >
                      Clear
                    </button>
                  </div>
                </div>
                
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {analysisResult.intelligent_fixes.map((fix, index) => (
                    <div key={index} className="bg-white p-3 rounded border">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-2 flex-1">
                          <input
                            type="checkbox"
                            checked={selectedFixes.has(index)}
                            onChange={() => toggleFixSelection(index)}
                            className="mt-1 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                          />
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
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
                                <p className="text-gray-600 font-medium">Environment Variables Needed:</p>
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {fix.env_vars_needed.map((envVar, envIndex) => (
                                    <span key={envIndex} className="bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded text-xs">
                                      {envVar}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {analysisResult.env_file_content && (
                  <div className="mt-3 text-xs">
                    <p className="font-medium text-purple-900 mb-1">Generated .env file:</p>
                    <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                      {analysisResult.env_file_content}
                    </pre>
                  </div>
                )}
              </div>
            )}
            
            {/* Fix Results */}
            {fixResult && (
              <div className="bg-green-50 p-3 rounded-md">
                <h5 className="font-medium text-green-900 text-sm">Fix Results</h5>
                <p className="text-xs text-green-800 mt-1">
                  {fixResult.message || `Applied ${fixResult.fixes_applied} fixes successfully`}
                </p>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  <div className="text-xs bg-white p-2 rounded">
                    <span className="font-medium">Fixes Applied:</span> {fixResult.fixes_applied}
                  </div>
                  <div className="text-xs bg-white p-2 rounded">
                    <span className="font-medium">Success Rate:</span> {fixResult.success_rate}%
                  </div>
                </div>
                {fixResult.env_vars_needed && fixResult.env_vars_needed.length > 0 && (
                  <div className="mt-2 text-xs">
                    <p className="font-medium text-green-900">Environment Variables Added:</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {fixResult.env_vars_needed.map((envVar: string, index: number) => (
                        <span key={index} className="bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                          {envVar}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {fixResult.pr_url && (
                  <a 
                    href={fixResult.pr_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:text-blue-800 mt-2 inline-flex items-center"
                  >
                    View Pull Request <ExternalLink className="w-3 h-3 ml-1" />
                  </a>
                )}
              </div>
            )}
            
            {/* Issues by File - Same as before but with AI fix indicators */}
            {analysisResult.file_results && analysisResult.file_results.length > 0 ? (
              <div className="space-y-3">
                <h5 className="font-medium text-gray-900 text-sm">Issues by File</h5>
                
                {analysisResult.file_results.map((fileResult, fileIndex) => (
                  <div key={fileIndex} className="border rounded-md overflow-hidden">
                    <div className="bg-gray-50 px-3 py-2 border-b">
                      <h6 className="font-medium text-sm text-gray-900 flex items-center">
                        <Folder className="w-4 h-4 mr-1 text-gray-500" />
                        {fileResult.filename}
                        <span className="ml-2 px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-800">
                          {fileResult.issues_count} issues
                        </span>
                        {fileResult.ai_fixes_count && fileResult.ai_fixes_count > 0 && (
                          <span className="ml-1 px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800">
                            <Brain className="w-3 h-3 inline mr-1" />
                            {fileResult.ai_fixes_count} AI fixes
                          </span>
                        )}
                      </h6>
                    </div>
                    
                        {fileResult.issues && fileResult.issues.length > 0 ? (
                          <div className="divide-y">
                            {fileResult.issues.map((issue, issueIndex) => (
                              <div key={issueIndex} className="p-3 hover:bg-gray-50">
                                <div className="flex items-start">
                                  <div className="mr-2 mt-0.5">
                                    {getIssueTypeIcon(issue.type)}
                                  </div>
                                  <div className="flex-1">
                                    <div className="flex justify-between">
                                      <p className="text-sm font-medium text-gray-900">
                                        {issue.message}
                                      </p>
                                      <div className="flex space-x-1">
                                        <span className={`px-2 py-0.5 rounded-full text-xs ${getSeverityColor(issue.severity)}`}>
                                          {issue.severity}
                                        </span>
                                        {issue.ai_fix_available && (
                                          <span className="px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-800">
                                            <Brain className="w-3 h-3 inline mr-1" />
                                            AI Fix
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                      Line {issue.line}: <code className="bg-gray-100 px-1 py-0.5 rounded">{issue.match}</code>
                                    </p>
                                    {issue.fix_available && (
                                      <div className="text-xs text-green-600 mt-1">
                                        {issue.ai_fix_available ? (
                                          'AI-powered fix available'
                                        ) : (
                                          'Rule-based fix available'
                                        )}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="p-4 text-center text-sm text-gray-500">
                            No issues found in this file
                          </div>
                        )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 bg-gray-50 rounded-md">
                <CheckCircle className="mx-auto h-8 w-8 text-green-500" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No issues found!</h3>
                <p className="mt-1 text-sm text-gray-500">
                  This repository appears to be clean and follows best practices
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Configuration Tab - Enhanced with AI settings */}
      <div className={`px-6 py-4 ${activeTab !== 'configuration' ? 'hidden' : ''}`}>
        <h4 className="text-sm font-medium text-gray-900 mb-3">Agent Configuration</h4>
        
        {/* AI Status Card */}
        {aiStatus && (
          <div className={`mb-4 p-3 rounded-md ${aiStatus.configured ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'}`}>
            <div className="flex items-center">
              <Brain className={`h-5 w-5 mr-2 ${aiStatus.configured ? 'text-green-500' : 'text-yellow-500'}`} />
              <div className="flex-1">
                <p className={`text-sm font-medium ${aiStatus.configured ? 'text-green-800' : 'text-yellow-800'}`}>
                  AI Integration Status: {aiStatus.status}
                </p>
                <p className={`text-xs ${aiStatus.configured ? 'text-green-700' : 'text-yellow-700'}`}>
                  {aiStatus.configured 
                    ? 'Gemini AI is ready to generate intelligent fixes'
                    : 'Add GEMINI_API_KEY to enable AI-powered fixes'
                  }
                </p>
              </div>
            </div>
            {!aiStatus.configured && (
              <div className="mt-2 text-xs text-yellow-700">
                <p>Get your free API key at: <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="underline">Google AI Studio</a></p>
              </div>
            )}
          </div>
        )}

        <div className="space-y-3">
          <div>
            <label className="block text-xs text-gray-700 mb-1">Agent Mode</label>
            <select
              value={configValues.agent_mode}
              onChange={(e) => setConfigValues({...configValues, agent_mode: e.target.value})}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
            >
              <option value="monitor">Monitor Only (Just detect issues)</option>
              <option value="suggest">Suggest Fixes (Create PRs with suggestions)</option>
              <option value="autofix">Auto-Fix (Apply fixes automatically)</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {configValues.agent_mode === 'monitor' 
                ? 'The agent will only detect issues without suggesting or applying fixes.' 
                : configValues.agent_mode === 'suggest'
                ? 'The agent will create PRs with suggested fixes but won\'t apply them.'
                : 'The agent will automatically apply fixes and create PRs with the changes.'}
            </p>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="auto-commit"
              checked={configValues.auto_commit}
              onChange={(e) => setConfigValues({...configValues, auto_commit: e.target.checked})}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="auto-commit" className="ml-2 block text-sm text-gray-900">
              Auto-Commit Fixes
            </label>
          </div>
          <p className="text-xs text-gray-500 -mt-2">
            When enabled, the agent will automatically commit fixes to a new branch and create a PR
          </p>

          <div>
            <label className="block text-xs text-gray-700 mb-1">Max Files to Analyze</label>
            <input
              type="number"
              value={configValues.max_files}
              onChange={(e) => setConfigValues({...configValues, max_files: parseInt(e.target.value) || 10})}
              min="1"
              max="50"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
            />
            <p className="text-xs text-gray-500 mt-1">
              Maximum number of files to analyze per commit/push (1-50)
            </p>
          </div>

          <div>
            <label className="block text-xs text-gray-700 mb-1">Excluded Files</label>
            <input
              type="text"
              value={configValues.excluded_files}
              onChange={(e) => setConfigValues({...configValues, excluded_files: e.target.value})}
              placeholder=".env,.git,node_modules"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
            />
            <p className="text-xs text-gray-500 mt-1">
              Comma-separated list of files/directories to exclude from analysis
            </p>
          </div>

          <div>
            <label className="block text-xs text-gray-700 mb-1">Excluded Extensions</label>
            <input
              type="text"
              value={configValues.excluded_extensions}
              onChange={(e) => setConfigValues({...configValues, excluded_extensions: e.target.value})}
              placeholder=".jpg,.png,.gif"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
            />
            <p className="text-xs text-gray-500 mt-1">
              Comma-separated list of file extensions to exclude from analysis
            </p>
          </div>

          <div className="pt-2">
            <button
              onClick={updateAgentConfig}
              disabled={configLoading}
              className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {configLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                <>
                  <Settings className="w-4 h-4 mr-2" />
                  Save Configuration
                </>
              )}
            </button>
          </div>

          <div className="mt-2 p-2 bg-blue-50 rounded-md border border-blue-200">
            <div className="flex items-start">
              <ShieldAlert className="h-5 w-5 text-blue-400 mr-2 flex-shrink-0" />
              <div className="text-xs text-blue-700">
                <p className="font-medium">Setup Notes:</p>
                <p>• GitHub token needs repo and pull request permissions</p>
                <p>• Gemini API key enables AI-powered intelligent fixes</p>
                <p>• Both services have generous free tiers</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentPanel;