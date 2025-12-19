/*
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Upload, Video, FileText, Image as ImageIcon, Loader2, Play, Sparkles, LayoutDashboard, BookOpen, Network } from 'lucide-react';

const API_URL = 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('main');
  const [headerInfo, setHeaderInfo] = useState({ description: '', icon_url: '' });
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [videoData, setVideoData] = useState({ original: null, processed: null, summary: '', advice_url: null });
  const [readme, setReadme] = useState('');
  const [archImage, setArchImage] = useState('');
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    fetchHeaderInfo();
  }, []);

  useEffect(() => {
    if (activeTab === 'readme' && !readme) fetchReadme();
    if (activeTab === 'architecture' && !archImage) fetchArchImage();
  }, [activeTab]);

  const fetchHeaderInfo = async () => {
    try {
      const res = await axios.get(`${API_URL}/header-info`);
      setHeaderInfo(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchReadme = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_URL}/readme`);
      setReadme(res.data.content);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const fetchArchImage = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_URL}/architecture-image`);
      setArchImage(res.data.image_url);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post(`${API_URL}/upload`, formData);
      setVideoData({ ...videoData, original: res.data.signed_url, file_id: res.data.file_id, gcs_uri: res.data.gcs_uri });
    } catch (err) {
      console.error(err);
    }
    setUploading(false);
  };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUpload(e.dataTransfer.files[0]);
    }
  }, []);

  const handleAnalyze = async () => {
    if (!videoData.gcs_uri) return;
    setAnalyzing(true);
    try {
      const res = await axios.post(`${API_URL}/analyze_video?gcs_uri=${videoData.gcs_uri}&file_id=${videoData.file_id}`);
      setVideoData({ ...videoData, processed: res.data.processed_url, summary: res.data.summary, advice_url: res.data.advice_url });
    } catch (err) {
      console.error(err);
    }
    setAnalyzing(false);
  };

  const navItems = [
    { id: 'main', label: 'Main Page', icon: LayoutDashboard },
    { id: 'readme', label: 'Read Me', icon: BookOpen },
    { id: 'architecture', label: 'Architecture', icon: Network },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white antialiased">
      {/* Sidebar */}
      <aside className="fixed top-0 left-0 h-full w-60 bg-slate-900/80 backdrop-blur-xl border-r border-slate-800 flex flex-col z-50">
        <div className="p-5 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center">
              <Video className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight">SportAI</span>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === item.id
                  ? 'bg-gradient-to-r from-cyan-500/20 to-purple-600/20 text-white border border-cyan-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </nav>

        {/* Upload Section in Sidebar */}
        <div className="p-3 border-t border-slate-800">
          <div
            className={`relative border-2 border-dashed rounded-lg p-3 text-center transition-all cursor-pointer ${
              dragActive
                ? 'border-cyan-500 bg-cyan-500/10'
                : uploading
                ? 'border-purple-500 bg-purple-500/5'
                : videoData.original
                ? 'border-green-500/50 bg-green-500/5'
                : 'border-slate-700 hover:border-slate-600'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept="video/mp4"
              onChange={(e) => handleUpload(e.target.files[0])}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            {uploading ? (
              <div className="flex items-center gap-2 justify-center">
                <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
                <span className="text-xs text-white">Uploading...</span>
              </div>
            ) : videoData.original ? (
              <div className="flex items-center gap-2 justify-center">
                <Play className="w-4 h-4 text-green-400" />
                <span className="text-xs text-white">Video Ready</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 justify-center">
                <Upload className="w-4 h-4 text-slate-400" />
                <span className="text-xs text-slate-400">Upload Video</span>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="ml-60 min-h-screen">
        <div className="max-w-6xl mx-auto p-8 space-y-8">
          {activeTab === 'main' && (
            <>
              {/* Header Section - 20/80 Split */}
              <section className="bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-slate-800 p-6">
                <div className="flex items-center gap-6">
                  {/* Icon - 20% */}
                  <div className="shrink-0">
                    <div className="w-24 h-24 rounded-xl bg-gradient-to-br from-cyan-500/20 to-purple-600/20 border border-slate-700 flex items-center justify-center overflow-hidden">
                      {headerInfo.icon_url ? (
                        <img src={headerInfo.icon_url} alt="App Icon" className="w-full h-full object-cover" />
                      ) : (
                        <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
                      )}
                    </div>
                  </div>
                  {/* Description - 80% */}
                  <div className="flex-1">
                    <h1 className="text-2xl font-bold mb-1 bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                      Sports Video Analysis
                    </h1>
                    <p className="text-slate-400 text-sm leading-relaxed">
                      {headerInfo.description || 'Your AI-powered pocket coach. Capture, analyze, and perfect your form in seconds.'}
                    </p>
                  </div>
                </div>
              </section>

              {/* Video Analysis Section - 50/50 Split */}
              <section className="bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-slate-800 p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-400" />
                    Player Tracker
                  </h2>
                  <button
                    onClick={handleAnalyze}
                    disabled={!videoData.original || analyzing}
                    className={`px-5 py-2 rounded-lg font-medium text-sm flex items-center gap-2 transition-all ${
                      !videoData.original || analyzing
                        ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                        : 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white hover:shadow-lg hover:shadow-cyan-500/25'
                    }`}
                  >
                    {analyzing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        Analyze Video
                      </>
                    )}
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  {/* Original Video */}
                  <div>
                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">Original</p>
                    <div className="aspect-video bg-black rounded-xl overflow-hidden border border-slate-800">
                      {videoData.original ? (
                        <video src={videoData.original} controls className="w-full h-full object-contain" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-700">
                          <Video className="w-12 h-12" />
                        </div>
                      )}
                    </div>
                  </div>
                  {/* Processed Video */}
                  <div>
                    <p className="text-xs font-medium text-cyan-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                      AI Processed
                    </p>
                    <div className="aspect-video bg-black rounded-xl overflow-hidden border border-cyan-500/30">
                      {analyzing ? (
                        <div className="w-full h-full flex flex-col items-center justify-center bg-slate-900/80">
                          <Loader2 className="w-10 h-10 text-cyan-400 animate-spin mb-3" />
                          <p className="text-white font-medium">Processing...</p>
                        </div>
                      ) : videoData.processed ? (
                        <video src={videoData.processed} controls className="w-full h-full object-contain" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-700">
                          <Video className="w-12 h-12" />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </section>

              {/* Strategic Summary */}
              <section className="bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-slate-800 p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-purple-400" />
                  Strategic Summary
                </h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
                    {analyzing ? (
                      <div className="space-y-3">
                        <div className="h-4 bg-slate-700 rounded animate-pulse"></div>
                        <div className="h-4 bg-slate-700 rounded w-5/6 animate-pulse"></div>
                        <div className="h-4 bg-slate-700 rounded w-4/6 animate-pulse"></div>
                      </div>
                    ) : videoData.summary ? (
                      <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown>{videoData.summary}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-slate-500 text-sm">Summary will appear after analysis.</p>
                    )}
                  </div>
                  <div>
                    {videoData.advice_url ? (
                      <img src={videoData.advice_url} alt="Key Frame" className="rounded-xl border border-purple-500/30 w-full" />
                    ) : (
                      <div className="aspect-video bg-slate-800/50 rounded-xl border border-dashed border-slate-700 flex items-center justify-center text-slate-600 text-sm">
                        Key frame annotation
                      </div>
                    )}
                  </div>
                </div>
              </section>
            </>
          )}

          {activeTab === 'readme' && (
            <section className="bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-slate-800 p-8">
              <h1 className="text-2xl font-bold mb-6 bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                Read Me
              </h1>
              {loading ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="w-10 h-10 text-cyan-400 animate-spin" />
                </div>
              ) : (
                <div className="prose prose-invert max-w-none prose-headings:text-white prose-p:text-slate-300 prose-a:text-cyan-400">
                  <ReactMarkdown>{readme}</ReactMarkdown>
                </div>
              )}
            </section>
          )}

          {activeTab === 'architecture' && (
            <section className="bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-slate-800 p-8">
              <h1 className="text-2xl font-bold mb-6 bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                System Architecture
              </h1>
              {loading ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="w-10 h-10 text-cyan-400 animate-spin" />
                </div>
              ) : archImage ? (
                <div className="rounded-xl overflow-hidden border border-slate-700">
                  <img src={archImage} alt="Architecture" className="w-full" />
                </div>
              ) : (
                <p className="text-slate-500">Failed to load architecture image.</p>
              )}
            </section>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
