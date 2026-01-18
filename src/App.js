import React, { useState } from 'react';
import { Upload, FileText, Briefcase, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function ResumeAnalyzer() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const handleResumeUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type === 'application/pdf' || file.type.startsWith('image/')) {
        setResumeFile(file);
        setError('');
      } else {
        setError('Please upload a PDF or image file');
      }
    }
  };

  const analyzeResume = async () => {
    if (!resumeFile || !jobDescription.trim()) {
      setError('Please upload a resume and paste a job description');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('resume', resumeFile);
      formData.append('job_description', jobDescription);

      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError('Failed to analyze resume. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-6xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Resume Job Matcher
          </h1>
          <p className="text-lg text-gray-600">
            Upload your resume and job description to get an ATS-optimized match score
          </p>
        </div>

        {!results ? (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
                <AlertCircle className="text-red-500 flex-shrink-0" size={20} />
                <p className="text-red-700">{error}</p>
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-8 mb-8">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  <FileText className="inline mr-2" size={18} />
                  Upload Resume (PDF or Image)
                </label>
                <div className="relative">
                  <input
                    type="file"
                    accept=".pdf,image/*"
                    onChange={handleResumeUpload}
                    className="hidden"
                    id="resume-upload"
                  />
                  <label
                    htmlFor="resume-upload"
                    className="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-indigo-500 transition-colors bg-gray-50 hover:bg-gray-100"
                  >
                    <Upload className="text-gray-400 mb-3" size={40} />
                    <p className="text-sm text-gray-600">
                      {resumeFile ? resumeFile.name : 'Click to upload resume'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      PDF, PNG, JPG up to 10MB
                    </p>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  <Briefcase className="inline mr-2" size={18} />
                  Job Description
                </label>
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the full job description here..."
                  className="w-full h-48 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                />
              </div>
            </div>

            <button
              onClick={analyzeResume}
              disabled={loading || !resumeFile || !jobDescription.trim()}
              className="w-full bg-indigo-600 text-white py-4 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  Analyzing Resume...
                </>
              ) : (
                <>
                  <CheckCircle2 size={20} />
                  Analyze Resume
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <div className="text-center mb-8">
                <div className={`inline-flex items-center justify-center w-32 h-32 rounded-full ${getScoreBg(results.overall_score)} mb-4`}>
                  <span className={`text-5xl font-bold ${getScoreColor(results.overall_score)}`}>
                    {results.overall_score}
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Resume Match Score
                </h2>
                <p className="text-gray-600">
                  {results.overall_score >= 80 ? 'Excellent match!' : 
                   results.overall_score >= 60 ? 'Good match with room for improvement' : 
                   'Needs significant optimization'}
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-6 mb-8">
                <div className="bg-blue-50 rounded-lg p-6">
                  <h3 className="font-semibold text-gray-900 mb-2">Keyword Match</h3>
                  <p className="text-3xl font-bold text-blue-600">{results.keyword_score}%</p>
                </div>
                <div className="bg-purple-50 rounded-lg p-6">
                  <h3 className="font-semibold text-gray-900 mb-2">Hard Skills</h3>
                  <p className="text-3xl font-bold text-purple-600">{results.hard_skills_score}%</p>
                </div>
                <div className="bg-green-50 rounded-lg p-6">
                  <h3 className="font-semibold text-gray-900 mb-2">Coverage</h3>
                  <p className="text-3xl font-bold text-green-600">{results.coverage_score}%</p>
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-3">Missing Keywords</h3>
                  <div className="flex flex-wrap gap-2">
                    {results.missing_keywords.slice(0, 15).map((kw, idx) => (
                      <span key={idx} className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-3">Matched Keywords</h3>
                  <div className="flex flex-wrap gap-2">
                    {results.matched_keywords.slice(0, 15).map((kw, idx) => (
                      <span key={idx} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-3">Recommendations</h3>
                  <ul className="space-y-2">
                    {results.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <AlertCircle className="text-indigo-600 flex-shrink-0 mt-1" size={18} />
                        <span className="text-gray-700">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <button
              onClick={() => {
                setResults(null);
                setResumeFile(null);
                setJobDescription('');
              }}
              className="w-full bg-gray-600 text-white py-4 rounded-lg font-semibold hover:bg-gray-700 transition-colors"
            >
              Analyze Another Resume
            </button>
          </div>
        )}
      </div>
    </div>
  );
}