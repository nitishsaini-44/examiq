'use client';
import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import UploadPage from './components/UploadPage';
import DashboardPage from './components/DashboardPage';
import PlannerPage from './components/PlannerPage';
import PracticePage from './components/PracticePage';
import { getResults } from '../lib/api';

export default function Home() {
  const [page, setPage] = useState('upload');
  const [analysisData, setAnalysisData] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Try to load cached results from backend on mount
  useEffect(() => {
    if (!analysisData) {
      getResults()
        .then(data => {
          if (data) {
            setAnalysisData(data);
          }
        })
        .catch(() => {
          // No cached results — that's fine
        });
    }
  }, []);

  return (
    <>
      <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
        {sidebarOpen ? '✕' : '☰'}
      </button>
      <div className="app-layout">
        <Sidebar activePage={page} onNavigate={(p) => { setPage(p); setSidebarOpen(false); }} isOpen={sidebarOpen} hasData={!!analysisData} />
        <main className="main-content">
          {page === 'upload' && <UploadPage onAnalysisComplete={(data) => { setAnalysisData(data); setPage('dashboard'); }} />}
          {page === 'dashboard' && <DashboardPage data={analysisData} />}
          {page === 'planner' && <PlannerPage data={analysisData} />}
          {page === 'practice' && <PracticePage data={analysisData} />}
        </main>
      </div>
    </>
  );
}
