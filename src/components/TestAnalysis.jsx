import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
} from 'chart.js';
import { Bar, Pie, Line } from 'react-chartjs-2';
import { api } from '../utils/api';
import ElegantLoader from './ElegantLoader';
import './TestAnalysis.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

const TestAnalysis = () => {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [analysisData, setAnalysisData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentView, setCurrentView] = useState('overview'); // overview, divisionA, divisionB, divisionC, divisionD, nonParticipants

  useEffect(() => {
    fetchTestAnalysis();
  }, [testId, currentView]);

  const fetchTestAnalysis = async () => {
    try {
      setIsLoading(true);
      
      // Determine division parameter based on current view
      let divisionParam = null;
      if (currentView.startsWith('division')) {
        divisionParam = currentView.replace('division', '');
      } else if (currentView === 'nonParticipants') {
        divisionParam = 'non_participants';
      }
      
      // Use real API
      const data = await api.getTestAnalysis(testId, divisionParam);
      setAnalysisData(data);
      setIsLoading(false);
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <ElegantLoader message="Loading test analysis..." />;
  }

  if (error) {
    return (
      <div className="test-analysis-container">
        <div className="error-message">
          <h2>Error loading test analysis</h2>
          <p>{error}</p>
          <button className="back-button" onClick={() => navigate('/test-series')}>
            Back to Test Series
          </button>
        </div>
      </div>
    );
  }

  if (!analysisData) {
    return (
      <div className="test-analysis-container">
        <div className="no-data-message">
          <h2>No data available</h2>
          <button className="back-button" onClick={() => navigate('/test-series')}>
            Back to Test Series
          </button>
        </div>
      </div>
    );
  }

  const { test_info, overall_stats, class_stats, student_performance, non_participating, question_stats } = analysisData;

  const getDivisionColor = (division) => {
    const colors = {
      A: '#4CAF50', // Green
      B: '#1565C0', // Darker Blue
      C: '#F57C00', // Darker Orange for visibility with white text
      D: '#9C27B0'  // Purple
    };
    return colors[division] || '#8B4513'; // Brown for fallback
  };

  // Class-wise average scores chart
  const classChartData = {
    labels: Object.keys(class_stats),
    datasets: [{
      label: 'Average Score',
      data: Object.values(class_stats).map(stat => stat.average_score),
      backgroundColor: [
        '#4CAF50',
        '#2196F3',
        '#FFC107',
        '#9C27B0',
        '#FF5722'
      ],
      borderColor: [
        '#4CAF50',
        '#2196F3',
        '#FFC107',
        '#9C27B0',
        '#FF5722'
      ],
      borderWidth: 1,
    }],
  };

  const classChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#ffffff'
        }
      },
      title: {
        display: true,
        text: 'Class-wise Average Scores',
        color: '#ffffff'
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          color: '#ffffff'
        },
        grid: {
          color: '#2d3748'
        }
      },
      x: {
        ticks: {
          color: '#ffffff'
        },
        grid: {
          color: '#2d3748'
        }
      }
    },
  };

  // Participation chart
  const participationData = {
    labels: ['Participated', 'Did Not Participate'],
    datasets: [{
      data: [overall_stats.total_participants, overall_stats.total_non_participants],
      backgroundColor: ['#4CAF50', '#ff6b6b'],
      borderColor: ['#4CAF50', '#ff6b6b'],
      borderWidth: 1,
    }],
  };

  const participationOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#ffffff'
        }
      },
      title: {
        display: true,
        text: 'Student Participation',
        color: '#ffffff'
      },
    },
  };

  // Score distribution chart
  const scoreRanges = ['0-20', '21-40', '41-60', '61-80', '81-100'];
  const scoreDistribution = scoreRanges.map(() => 0);

  student_performance.forEach(student => {
    const score = student.percentage;
    if (score <= 20) scoreDistribution[0]++;
    else if (score <= 40) scoreDistribution[1]++;
    else if (score <= 60) scoreDistribution[2]++;
    else if (score <= 80) scoreDistribution[3]++;
    else scoreDistribution[4]++;
  });

  const distributionData = {
    labels: scoreRanges,
    datasets: [{
      label: 'Number of Students',
      data: scoreDistribution,
      backgroundColor: '#2196F3',
      borderColor: '#2196F3',
      borderWidth: 1,
    }],
  };
  

  const distributionOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#ffffff'
        }
      },
      title: {
        display: true,
        text: 'Score Distribution (%)',
        color: '#ffffff'
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          color: '#ffffff'
        },
        grid: {
          color: '#2d3748'
        }
      },
      x: {
        ticks: {
          color: '#ffffff'
        },
        grid: {
          color: '#2d3748'
        }
      }
    },
  };

  return (
    <motion.div
      className="test-analysis-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
    >
      {currentView !== 'overview' ? (
        <button className="back-button" onClick={() => setCurrentView('overview')}>
          ← Back to Overview
        </button>
      ) : (
        <button className="back-button" onClick={() => navigate('/test-series')}>
          ← Back to Test Series
        </button>
      )}

      <motion.div
        className="test-analysis-header"
        initial={{ y: -20 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1>Test Analysis</h1>

        <div className="test-info-card">
          <h2>{test_info.test_name || `Test ${test_info.test_id}`}</h2>
          <div className="info-grid">
            <div className="info-item">
              <div className="label">Subject</div>
              <div className="value">{test_info.subject}</div>
            </div>
            <div className="info-item">
              <div className="label">Standard</div>
              <div className="value">{test_info.standard}</div>
            </div>
            <div className="info-item">
              <div className="label">Total Questions</div>
              <div className="value">{test_info.total_questions}</div>
            </div>
            <div className="info-item">
              <div className="label">Participants</div>
              <div className="value">{overall_stats.total_participants}</div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Division navigation buttons */}
      <div className="division-nav">
        <button
          className={`nav-button ${currentView === 'overview' ? 'active' : ''}`}
          onClick={() => setCurrentView('overview')}
        >
          Overview
        </button>
        <button
          className={`nav-button ${currentView === 'divisionA' ? 'active' : ''}`}
          onClick={() => setCurrentView('divisionA')}
        >
          Division A
        </button>
        <button
          className={`nav-button ${currentView === 'divisionB' ? 'active' : ''}`}
          onClick={() => setCurrentView('divisionB')}
        >
          Division B
        </button>
        <button
          className={`nav-button ${currentView === 'divisionC' ? 'active' : ''}`}
          onClick={() => setCurrentView('divisionC')}
        >
          Division C
        </button>
        <button
          className={`nav-button ${currentView === 'divisionD' ? 'active' : ''}`}
          onClick={() => setCurrentView('divisionD')}
        >
          Division D
        </button>
        <button
          className={`nav-button ${currentView === 'nonParticipants' ? 'active' : ''}`}
          onClick={() => setCurrentView('nonParticipants')}
        >
          Non-Participants
        </button>
      </div>

      {currentView === 'overview' && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Overall Statistics</h3>
            <div className="stats-overview">
              <div className="stat-item">
                <div className="stat-value percentage-high">
                  {overall_stats.average_percentage.toFixed(1)}%
                </div>
              <div className="stat-label">Average Score</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">
                {overall_stats.highest_score}
              </div>
              <div className="stat-label">Highest Score</div>
            </div>
            <div className="stat-item">
              <div className="stat-value percentage-low">
                {overall_stats.lowest_score}
              </div>
              <div className="stat-label">Lowest Score</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">
                {overall_stats.total_participants}
              </div>
              <div className="stat-label">Total Participants</div>
            </div>
          </div>
        </div>

        <div className="stat-card">
          <h3>Participation Overview</h3>
          <div className="chart-container">
            <Pie data={participationData} options={participationOptions} />
          </div>
        </div>
      </div>
      )}


      {/* Question-wise statistics */}
      {question_stats && question_stats.length > 0 && (
        <div className="stat-card">
          <h3>Question-wise Performance</h3>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Question</th>
                  <th>Correct</th>
                  <th>Total</th>
                  <th>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {question_stats.map((question, index) => (
                  <tr key={index}>
                    <td>Q{question.question_number}</td>
                    <td>{question.correct_count}</td>
                    <td>{question.total_count}</td>
                    <td className={
                      question.percentage >= 80 ? 'percentage-high' :
                      question.percentage >= 60 ? 'percentage-medium' : 'percentage-low'
                    }>
                      {question.percentage.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card">
          <h3>{currentView !== 'overview' && currentView.startsWith('division') ? `Class ${currentView.replace('division', '')} Stats` : 'Class-wise Performance'}</h3>
          <div className="chart-container">
            <Bar data={classChartData} options={classChartOptions} />
          </div>
        </div>
      
        <div className="stat-card">
          <h3>Score Distribution</h3>
          <div className="chart-container">
            <Bar data={distributionData} options={distributionOptions} />
          </div>
        </div>
      </div>
      
      {currentView === 'overview' && (
        <div className="division-cards-grid">
          {['A', 'B', 'C', 'D'].map((division) => {
            const divisionStats = class_stats[division];
            return (
              <motion.div
                key={division}
                style={{ backgroundColor: getDivisionColor(division), color: '#ffffff' }}
                className="division-card"
                onClick={() => setCurrentView(`division${division}`)}
                whileHover={{ y: -5, boxShadow: '0 10px 20px rgba(0,0,0,0.3)' }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="division-card-header">
                  <h3 style={{ color: '#ffffff' }}>Division {division}</h3>
                </div>
                {divisionStats ? (
                  <div className="division-card-stats">
                    <div className="stat-item">
                      <div className="stat-value">{divisionStats.total_students}</div>
                      <div className="stat-label">Students</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-value percentage-high">
                        {divisionStats.average_percentage.toFixed(1)}%
                      </div>
                      <div className="stat-label">Avg Score</div>
                    </div>
                  </div>
                ) : (
                  <div className="division-card-stats">
                    <div className="stat-item">
                      <div className="stat-value">0</div>
                      <div className="stat-label">Students</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-value">0%</div>
                      <div className="stat-label">Avg Score</div>
                    </div>
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Show student performance table only in division-specific views */}
      {currentView !== 'overview' && currentView !== 'nonParticipants' && student_performance.length > 0 && (
        <div className="table-container">
          <h3>Student Performance - Class {currentView.replace('division', '')}</h3>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Student Name</th>
                  <th>Class</th>
                  <th>Score</th>
                  <th>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {student_performance.map((student, index) => (
                  <tr key={student.user_id}>
                    <td>{index + 1}</td>
                    <td>{student.name}</td>
                    <td>{student.division}</td>
                    <td>{student.score}/{student.total_questions}</td>
                    <td className={
                      student.percentage >= 80 ? 'percentage-high' :
                      student.percentage >= 60 ? 'percentage-medium' : 'percentage-low'
                    }>
                      {student.percentage.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Show non-participating students table only in nonParticipants view */}
      {currentView === 'nonParticipants' && non_participating.length > 0 && (
        <div className="table-container">
          <h3>Students Who Did Not Participate</h3>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Student ID</th>
                  <th>Student Name</th>
                  <th>Class</th>
                </tr>
              </thead>
              <tbody>
                {non_participating.map((student) => (
                  <tr key={student.user_id}>
                    <td>{student.user_id}</td>
                    <td>{student.name}</td>
                    <td>{student.division}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default TestAnalysis;