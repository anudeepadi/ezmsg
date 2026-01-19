'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout';
import { testing, TestRunResponse, TestHealthResponse, ApiError } from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  Play,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  FileCode,
  Terminal,
  BarChart3,
  ChevronDown,
  ChevronRight,
  Loader2,
} from 'lucide-react';

export default function TestingPage() {
  const { addToast } = useToastStore();

  const [health, setHealth] = useState<TestHealthResponse | null>(null);
  const [results, setResults] = useState<TestRunResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [showRawOutput, setShowRawOutput] = useState(false);
  const [groupByFile, setGroupByFile] = useState(true);

  useEffect(() => {
    loadHealth();
  }, []);

  async function loadHealth() {
    setLoading(true);
    try {
      const data = await testing.health();
      setHealth(data);
    } catch (err) {
      const error = err as ApiError;
      const errorData = error.data as { detail?: string } | undefined;
      addToast('error', errorData?.detail || 'Failed to load test health');
    } finally {
      setLoading(false);
    }
  }

  async function runTests() {
    setRunning(true);
    try {
      const data = await testing.run();
      setResults(data);
      if (data.summary.failed === 0 && data.summary.errors === 0) {
        addToast('success', `All ${data.summary.passed} tests passed!`);
      } else {
        addToast(
          'warning',
          `${data.summary.passed} passed, ${data.summary.failed} failed`
        );
      }
    } catch (err) {
      const error = err as ApiError;
      const errorData = error.data as { detail?: string } | undefined;
      addToast('error', errorData?.detail || 'Failed to run tests');
    } finally {
      setRunning(false);
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircle2 className="h-4 w-4 text-success" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-error" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-error" />;
      case 'skipped':
        return <Clock className="h-4 w-4 text-warning" />;
      default:
        return null;
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'passed':
        return 'badge-success';
      case 'failed':
      case 'error':
        return 'badge-error';
      case 'skipped':
        return 'badge-warning';
      default:
        return 'badge-default';
    }
  };

  // Group tests by file
  const testsByFile = results?.tests.reduce(
    (acc, test) => {
      const file = test.file;
      if (!acc[file]) {
        acc[file] = [];
      }
      acc[file].push(test);
      return acc;
    },
    {} as Record<string, typeof results.tests>
  );

  return (
    <>
      <Header
        title="API Testing"
        description="Run and view API test results"
        actions={
          <div className="flex items-center gap-3">
            <Link href="/admin" className="btn-secondary">
              <ArrowLeft className="h-4 w-4" />
              Dashboard
            </Link>
            <button
              onClick={runTests}
              disabled={running}
              className="btn-primary"
            >
              {running ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Run Tests
                </>
              )}
            </button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Test Infrastructure Health */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-title text-text flex items-center gap-2">
              <FileCode className="h-5 w-5 text-accent" />
              Test Infrastructure
            </h3>
            <button
              onClick={loadHealth}
              disabled={loading}
              className="btn-ghost p-1.5"
            >
              <RefreshCw
                className={cn('h-4 w-4', loading && 'animate-spin')}
              />
            </button>
          </div>

          {health ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-3 bg-surface rounded-lg">
                <p className="text-caption text-text-muted">Status</p>
                <p className="text-body font-medium text-success capitalize">
                  {health.status}
                </p>
              </div>
              <div className="p-3 bg-surface rounded-lg">
                <p className="text-caption text-text-muted">Test Files</p>
                <p className="text-body font-medium text-text">
                  {health.test_files_count}
                </p>
              </div>
              <div className="p-3 bg-surface rounded-lg">
                <p className="text-caption text-text-muted">Files</p>
                <p className="text-body-sm font-mono text-text-secondary">
                  {health.test_files.join(', ')}
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <Loader2 className="h-6 w-6 animate-spin mx-auto text-accent" />
            </div>
          )}
        </div>

        {/* Test Results */}
        {results && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-accent/10 rounded-lg">
                    <BarChart3 className="h-5 w-5 text-accent" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Total</p>
                    <p className="text-title text-text">
                      {results.summary.total}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-success/10 rounded-lg">
                    <CheckCircle2 className="h-5 w-5 text-success" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Passed</p>
                    <p className="text-title text-success">
                      {results.summary.passed}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-error/10 rounded-lg">
                    <XCircle className="h-5 w-5 text-error" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Failed</p>
                    <p className="text-title text-error">
                      {results.summary.failed}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-warning/10 rounded-lg">
                    <AlertCircle className="h-5 w-5 text-warning" />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Errors</p>
                    <p className="text-title text-warning">
                      {results.summary.errors}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-4">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      'p-2 rounded-lg',
                      results.summary.pass_rate >= 80
                        ? 'bg-success/10'
                        : results.summary.pass_rate >= 50
                          ? 'bg-warning/10'
                          : 'bg-error/10'
                    )}
                  >
                    <BarChart3
                      className={cn(
                        'h-5 w-5',
                        results.summary.pass_rate >= 80
                          ? 'text-success'
                          : results.summary.pass_rate >= 50
                            ? 'text-warning'
                            : 'text-error'
                      )}
                    />
                  </div>
                  <div>
                    <p className="text-caption text-text-muted">Pass Rate</p>
                    <p
                      className={cn(
                        'text-title',
                        results.summary.pass_rate >= 80
                          ? 'text-success'
                          : results.summary.pass_rate >= 50
                            ? 'text-warning'
                            : 'text-error'
                      )}
                    >
                      {results.summary.pass_rate}%
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Pass Rate Progress Bar */}
            <div className="card p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-body-sm text-text-secondary">
                  Test Run: {new Date(results.timestamp).toLocaleString()}
                </span>
                <span className="text-body-sm font-mono text-text-muted">
                  Exit code: {results.exit_code}
                </span>
              </div>
              <div className="h-3 bg-surface rounded-full overflow-hidden">
                <div
                  className={cn(
                    'h-full transition-all duration-500',
                    results.summary.pass_rate >= 80
                      ? 'bg-success'
                      : results.summary.pass_rate >= 50
                        ? 'bg-warning'
                        : 'bg-error'
                  )}
                  style={{ width: `${results.summary.pass_rate}%` }}
                />
              </div>
            </div>

            {/* Test Results Table */}
            <div className="card overflow-hidden">
              <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                <h3 className="text-title text-text">Test Results</h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setGroupByFile(!groupByFile)}
                    className={cn(
                      'btn-ghost text-body-sm',
                      groupByFile && 'bg-surface'
                    )}
                  >
                    Group by File
                  </button>
                </div>
              </div>

              {groupByFile && testsByFile ? (
                <div className="divide-y divide-border">
                  {Object.entries(testsByFile).map(([file, tests]) => {
                    const passedCount = tests.filter(
                      (t) => t.status === 'passed'
                    ).length;
                    const allPassed = passedCount === tests.length;

                    return (
                      <div key={file}>
                        <div
                          className={cn(
                            'px-4 py-3 flex items-center gap-3',
                            allPassed ? 'bg-success/5' : 'bg-error/5'
                          )}
                        >
                          <FileCode className="h-4 w-4 text-text-muted" />
                          <span className="font-mono text-body-sm text-text">
                            {file}
                          </span>
                          <span
                            className={cn(
                              'ml-auto text-body-sm',
                              allPassed ? 'text-success' : 'text-text-secondary'
                            )}
                          >
                            {passedCount}/{tests.length} passed
                          </span>
                        </div>
                        <div className="divide-y divide-border/50">
                          {tests.map((test) => (
                            <div
                              key={test.full_name}
                              className="px-4 py-2 pl-10 flex items-center gap-3"
                            >
                              {getStatusIcon(test.status)}
                              <span className="font-mono text-body-sm text-text-secondary">
                                {test.name}
                              </span>
                              <span
                                className={cn(
                                  'ml-auto badge',
                                  getStatusBadgeClass(test.status)
                                )}
                              >
                                {test.status}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Status</th>
                      <th>Test Name</th>
                      <th>File</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.tests.map((test) => (
                      <tr key={test.full_name}>
                        <td>
                          <div className="flex items-center gap-2">
                            {getStatusIcon(test.status)}
                            <span
                              className={cn(
                                'badge',
                                getStatusBadgeClass(test.status)
                              )}
                            >
                              {test.status}
                            </span>
                          </div>
                        </td>
                        <td className="font-mono text-body-sm">{test.name}</td>
                        <td className="text-text-muted text-body-sm">
                          {test.file}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Raw Output */}
            <div className="card overflow-hidden">
              <button
                onClick={() => setShowRawOutput(!showRawOutput)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-surface transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-text-muted" />
                  <span className="text-title text-text">Raw Output</span>
                </div>
                {showRawOutput ? (
                  <ChevronDown className="h-4 w-4 text-text-muted" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-text-muted" />
                )}
              </button>

              {showRawOutput && (
                <div className="border-t border-border p-4 bg-gray-900">
                  <pre className="text-body-sm font-mono text-green-400 whitespace-pre-wrap overflow-x-auto">
                    {results.raw_output}
                  </pre>
                </div>
              )}
            </div>
          </>
        )}

        {/* No Results Yet */}
        {!results && !running && (
          <div className="card p-8 text-center">
            <Play className="h-12 w-12 text-text-muted mx-auto mb-4" />
            <p className="text-body text-text-secondary mb-4">
              Click &quot;Run Tests&quot; to execute the API test suite
            </p>
            <button onClick={runTests} className="btn-primary">
              <Play className="h-4 w-4" />
              Run Tests
            </button>
          </div>
        )}

        {/* Running State */}
        {running && !results && (
          <div className="card p-8 text-center">
            <Loader2 className="h-12 w-12 animate-spin text-accent mx-auto mb-4" />
            <p className="text-body text-text-secondary">
              Running tests... This may take a moment.
            </p>
          </div>
        )}
      </div>
    </>
  );
}
