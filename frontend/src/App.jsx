import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  Map, 
  Database, 
  Code, 
  Settings, 
  Upload, 
  BookOpen, 
  Activity,
  Trophy,
  Award,
  Briefcase
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import Roadmap from './components/Roadmap';
import ProblemBank from './components/ProblemBank';
import PracticeSandbox from './components/PracticeSandbox';
import SparkProfiles from './components/SparkProfiles';
import ImportProblems from './components/ImportProblems';
import UnderstandMe from './components/UnderstandMe';
import Achievements from './components/Achievements';
import Challenges from './components/Challenges';
import CompanyExplorer from './components/CompanyExplorer';
import SparkMasterPlanner from './components/SparkMasterPlanner';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedProblemId, setSelectedProblemId] = useState(null);

  const navigateToPractice = (problemId) => {
    setSelectedProblemId(problemId);
    setActiveTab('practice');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard onSelectProblem={navigateToPractice} />;
      case 'roadmap':
        return <Roadmap onSelectProblem={navigateToPractice} />;
      case 'spark-master':
        return <SparkMasterPlanner />;
      case 'problems':
        return <ProblemBank onSelectProblem={navigateToPractice} />;
      case 'practice':
        return (
          <PracticeSandbox 
            problemId={selectedProblemId} 
            onSelectProblem={setSelectedProblemId}
          />
        );
      case 'achievements':
        return <Achievements />;
      case 'challenges':
        return <Challenges onSelectProblem={navigateToPractice} />;
      case 'companies':
        return <CompanyExplorer onSelectProblem={navigateToPractice} />;
      case 'profiles':
        return <SparkProfiles />;
      case 'import':
        return <ImportProblems />;
      case 'understand':
        return <UnderstandMe />;
      default:
        return <Dashboard onSelectProblem={navigateToPractice} />;
    }
  };

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'spark-master', label: 'Spark Master Path', icon: BookOpen },
    { id: 'roadmap', label: 'Learning Roadmaps', icon: Map },
    { id: 'problems', label: 'Problem Bank', icon: Database },
    { id: 'practice', label: 'Practice Sandbox', icon: Code },
    { id: 'achievements', label: 'Achievements', icon: Trophy },
    { id: 'challenges', label: 'Challenges', icon: Award },
    { id: 'companies', label: 'Company Explorer', icon: Briefcase },
    { id: 'profiles', label: 'Spark Profiles', icon: Settings },
    { id: 'import', label: 'Import Problems', icon: Upload },
    { id: 'understand', label: 'Understand Me', icon: BookOpen }
  ];

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '2.5rem' }}>
          <Activity size={28} color="#ff4b4b" />
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '0.05em' }}>
            ⚡ SPARK HUB
          </h2>
        </div>
        
        <nav style={{ flex: 1 }}>
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.id}
                className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab(item.id);
                  if (item.id !== 'practice') {
                    // reset practice problem if leaving practice tab
                    // but keeping state allows returning
                  }
                }}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </div>
            );
          })}
        </nav>
        
        <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textAlign: 'center', borderTop: '1px solid var(--border-glass)', paddingTop: '1rem' }}>
          Spark Practice Hub v2.0
        </div>
      </aside>

      {/* Main Content Pane */}
      <main className="main-content">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
