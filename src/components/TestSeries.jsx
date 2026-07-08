import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import CreatableSelect from 'react-select/creatable';
import { api } from '../utils/api';
import ElegantLoader from './ElegantLoader';
import './TestSeries.css';

const TestCard = styled(motion.div)`
  background: var(--bg-raised);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  color: var(--text-primary);
  margin-bottom: var(--space-5);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-subtle);
  transition: transform var(--duration-normal) var(--ease-default),
              box-shadow var(--duration-normal) var(--ease-default);
  cursor: pointer;
  position: relative;
  z-index: var(--z-base);
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: ${props => props.$gradient || 'var(--primary)'};
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  }

  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--border-default);
  }
`;

const TestInfo = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;

  h2 {
    font-family: var(--font-display);
    font-size: var(--text-xl);
    font-weight: var(--weight-bold);
    color: var(--text-primary);
  }

  .test-id {
    color: var(--text-muted);
    font-size: var(--text-sm);
    font-family: var(--font-mono);
  }
`;

const TestDetails = styled.div`
  margin-top: var(--space-4);
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
`;

const TestDescription = styled.p`
  margin-top: var(--space-4);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: var(--leading-relaxed);
`;

const Badge = styled.span`
  background: var(--bg-surface);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  border: 1px solid var(--border-subtle);
`;

const SkeletonWrapper = styled(motion.div)`
  margin-top: 0;
  height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-base);
`;

const EmptyStateWrapper = styled(motion.div)`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  text-align: center;
  padding: var(--space-8);
`;

const EmptyStateIcon = styled(motion.div)`
  font-size: var(--text-4xl);
  margin-bottom: var(--space-6);
`;

const EmptyStateTitle = styled(motion.h2)`
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  margin-bottom: var(--space-4);
  color: var(--text-primary);
`;

const EmptyStateText = styled(motion.p)`
  font-size: var(--text-lg);
  color: var(--text-secondary);
  max-width: 500px;
  line-height: var(--leading-relaxed);
`;

const TeacherForm = styled(motion.div)`
  background: var(--bg-raised);
  padding: var(--space-8);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  margin-bottom: var(--space-8);
  position: relative;
  z-index: var(--z-dropdown);
  border: 1px solid var(--border-subtle);

  h2 {
    font-family: var(--font-display);
    color: var(--text-primary);
    margin-bottom: var(--space-6);
    font-size: var(--text-xl);
  }
`;

const FormGroup = styled.div`
  margin-bottom: var(--space-5);

  label {
    display: block;
    margin-bottom: var(--space-2);
    font-weight: var(--weight-semibold);
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  select {
    width: 100px;
    padding: var(--space-3);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-md);
    background-color: var(--bg-surface);
    color: var(--text-primary);
    font-size: var(--text-base);
    cursor: ${props => props.isDisabled ? 'not-allowed' : 'pointer'};
    transition: border-color var(--duration-fast) var(--ease-default);

    &:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--primary-glow);
    }

    &:disabled {
      background-color: var(--bg-base);
      border-color: var(--border-subtle);
      color: var(--text-muted);
      cursor: not-allowed;
    }

    option {
      background-color: var(--bg-surface);
      color: var(--text-primary);
    }
  }

  .react-select-container {
    .react-select__control {
      background-color: var(--bg-surface);
      border-color: var(--border-default);
      position: relative;
      z-index: 101;
      &:hover {
        border-color: var(--border-default);
      }
    }

    .react-select__menu {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-default);
      z-index: 102;
    }

    .react-select__option {
      background-color: var(--bg-surface);
      color: var(--text-primary);
      &:hover {
        background-color: var(--bg-hover);
      }
    }

    .react-select__multi-value {
      background-color: var(--bg-hover);
      border-radius: var(--radius-sm);

      .react-select__multi-value__label {
        color: var(--text-primary);
      }

      .react-select__multi-value__remove {
        color: var(--text-primary);
        &:hover {
          background-color: var(--error);
          color: var(--text-primary);
        }
      }
    }

    .react-select__input-container {
      color: var(--text-primary);
    }

    .react-select__placeholder {
      color: var(--text-muted);
    }
  }
`;

const DisabledInput = styled.input`
  width: 100%;
  padding: var(--space-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background-color: var(--bg-base);
  color: var(--text-muted);
  font-size: var(--text-base);
  cursor: not-allowed;
`;

const Input = styled.input`
  width: 100%;
  padding: var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background-color: var(--bg-surface);
  color: var(--text-primary);
  font-size: var(--text-base);
  transition: border-color var(--duration-fast) var(--ease-default),
              box-shadow var(--duration-fast) var(--ease-default);

  &:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--primary-glow);
  }

  &::placeholder {
    color: var(--text-muted);
  }
`;

const GenerateButton = styled.button`
  padding: var(--space-3) var(--space-6);
  background-color: var(--primary);
  color: var(--text-inverse);
  border: none;
  border-radius: var(--radius-md);
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  width: 100%;
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  transition: all var(--duration-normal) var(--ease-default);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);

  &:disabled {
    background-color: var(--bg-surface);
    color: var(--text-muted);
    opacity: 0.7;
    box-shadow: none;
  }

  &:hover:not(:disabled) {
    background-color: var(--primary-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
  }
`;

const PageHeader = styled(motion.div)`
  margin-bottom: var(--space-8);
  padding-top: var(--space-6);
  text-align: center;

  h1 {
    font-family: var(--font-display);
    font-weight: var(--weight-bold);
    font-size: var(--text-3xl);
    letter-spacing: -0.5px;
    color: var(--text-primary);
    margin-bottom: var(--space-6);
  }
`;

const LessonTag = styled(motion.span)`
  display: inline-block;
  background: var(--bg-surface);
  color: var(--text-secondary);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  margin: var(--space-1);
  border: 1px solid var(--border-subtle);
`;

const LessonsList = styled.div`
  margin-top: var(--space-4);
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
`;

function TestSeries() {
  const [tests, setTests] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showSkeletonLoading, setShowSkeletonLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const navigate = useNavigate();
  const progressInterval = useRef(null);
  const startTimeRef = useRef(null);
  const lastProgressRef = useRef(0);
  const [isTeacher, setIsTeacher] = useState(false);
  const [teacherSubject, setTeacherSubject] = useState("");
  const [teacherStandard, setTeacherStandard] = useState([]);
  const [selectedStandard, setSelectedStandard] = useState("");
  const [selectedLessons, setSelectedLessons] = useState([]);
  const [availableLessons, setAvailableLessons] = useState([]);
  const [isLessonsLoading, setIsLessonsLoading] = useState(false);
  const [customSubject, setCustomSubject] = useState("");
  const [testName, setTestName] = useState("");
  const [showSubjectWarning, setShowSubjectWarning] = useState(false);

  const getSubjectGradient = (subject) => {
    const gradients = {
      Math: 'var(--gradient-math)',
      Science: 'var(--gradient-science)',
      English: 'var(--gradient-english)',
      SS: 'var(--gradient-ss)'
    };
    return gradients[subject] || 'linear-gradient(135deg, var(--primary), var(--primary-hover))';
  };

  const getSubjectIcon = (subject) => {
    const icons = {
      Math: '📐',
      Science: '🧪',
      English: '📚',
      SS: '🌍'
    };
    return icons[subject] || '📚';
  };

  useEffect(() => {
    const fetchTests = async () => {
      try {
        const data = await api.getTests();
        setTests(data.tests);
        setIsTeacher(data.teacher);

        if (data.teacher) {
          setTeacherSubject(data.teacher_subject);
          setCustomSubject(data.teacher_subject);

          if (data.teacher_standard) {
            setTeacherStandard(data.teacher_standard);
            setSelectedStandard(data.teacher_standard[0]);
          }
        }
      } catch (error) {
        console.error('Error fetching tests:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTests();
  }, []);

  useEffect(() => {
    if (selectedStandard && teacherSubject) {
      fetchLessons();
    }
  }, [selectedStandard, teacherSubject]);

  const fetchLessons = async () => {
    setIsLessonsLoading(true);

    try {
      const data = await api.getLessons(teacherSubject, selectedStandard === 10);
      setAvailableLessons(data.map(lesson => ({ value: lesson, label: lesson })));
    } catch (error) {
      console.error('Error fetching lessons:', error);
    } finally {
      setIsLessonsLoading(false);
    }
  };

  const handleGenerateTest = async (e) => {
    e.preventDefault();
    setShowSkeletonLoading(true);

    try {
      const testData = {
        subject: customSubject,
        lessons: selectedLessons.map(l => l.value),
        class10: selectedStandard === 10,
        type: 'automatic',
        test_name: testName,
      };

      navigate('/create-test', { state: { generatedTest: testData } });
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setShowSkeletonLoading(false);
    }
  };

  const cardVariants = {
    hidden: {
      opacity: 0,
      scale: 0.8,
      y: 50,
      rotateX: -15
    },
    visible: (index) => ({
      opacity: 1,
      scale: 1,
      y: 0,
      rotateX: 0,
      transition: {
        duration: 0.8,
        delay: index * 0.15,
        type: "spring",
        stiffness: 100,
        damping: 15
      }
    }),
    hover: {
      scale: 1.03,
      rotateX: 5,
      boxShadow: "0 15px 30px rgba(0,0,0,0.2)",
      transition: {
        duration: 0.3,
        type: "spring",
        stiffness: 400,
        damping: 10
      }
    }
  };

  const fadeTransition = {
    hidden: {
      opacity: 0,
      scale: 0.95,
      filter: 'blur(10px)'
    },
    visible: {
      opacity: 1,
      scale: 1,
      filter: 'blur(0px)',
      transition: {
        duration: 0.5,
        ease: "easeOut"
      }
    },
    exit: {
      opacity: 0,
      scale: 1.05,
      filter: 'blur(10px)',
      transition: {
        duration: 0.3,
        ease: "easeIn"
      }
    }
  };

  const handleTestClick = async (testId) => {
    setShowSkeletonLoading(true);
    setProgress(0);
    startTimeRef.current = Date.now();
    lastProgressRef.current = 0;

    const updateProgress = () => {
      const elapsedTime = Date.now() - startTimeRef.current;
      const newProgress = Math.min((elapsedTime / 1000) * 100, 100);

      if (newProgress > lastProgressRef.current) {
        setProgress(newProgress);
        lastProgressRef.current = newProgress;
      }
    };

    progressInterval.current = setInterval(updateProgress, 5);

    try {
      const examResponse = await api.createExam({
        test: true,
        'test-id': testId,
      });

      clearInterval(progressInterval.current);
      setProgress(100);

      setTimeout(() => {
        const examId = examResponse['exam-id'];
        const createdExam = examResponse.exam;
        navigate(`/exam/g/${examId}`, {
          state: createdExam ? { examData: createdExam } : undefined,
        });
      }, 100);
    } catch (error) {
      console.error('Error creating exam:', error);
      clearInterval(progressInterval.current);
      setShowSkeletonLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
      className="test-series-container"
    >
      <AnimatePresence mode="wait">
        {showSkeletonLoading ? (
          <SkeletonWrapper
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <ElegantLoader
              message="Preparing Your Test..."
              subMessage="Setting up questions and generating content"
              progress={progress}
              fullHeight={true}
            />
          </SkeletonWrapper>
        ) : (
          <>
            <PageHeader
              initial={{ y: -20 }}
              animate={{ y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h1>Test Series</h1>
            </PageHeader>

            {isTeacher && (
              <TeacherForm initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
                <h2>Create New Test</h2>
                <form onSubmit={handleGenerateTest}>
                  <FormGroup>
                    <label>Subject</label>
                    <Input
                      type="text"
                      value={customSubject}
                      onChange={(e) => {
                        const newSubject = e.target.value;
                        setCustomSubject(newSubject);
                        if (newSubject !== teacherSubject) {
                          setShowSubjectWarning(true);
                          if (selectedLessons.length > 0) {
                            setSelectedLessons([]); // Clear if changed
                          }
                        } else {
                          setShowSubjectWarning(false);
                        }
                      }}
                    />
                    {showSubjectWarning && (
                      <p style={{ color: 'var(--warning)', fontSize: 'var(--text-xs)', marginTop: 'var(--space-2)' }}>
                        Changing the subject will require you to manually create all questions.
                      </p>
                    )}
                  </FormGroup>
                  <FormGroup>
                    <label>Test Name (Optional)</label>
                    <Input
                      type="text"
                      value={testName}
                      onChange={(e) => setTestName(e.target.value)}
                      placeholder="E.g., Mid-term Practice Test"
                    />
                  </FormGroup>
                  <FormGroup isDisabled={teacherStandard.length === 1}>
                    <label>Standard</label>
                    {teacherStandard.length === 1 ? (
                      <DisabledInput
                        type="text"
                        value={`Standard ${selectedStandard}`}
                        disabled
                      />
                    ) : (
                      <select
                        value={selectedStandard}
                        onChange={(e) => setSelectedStandard(Number(e.target.value))}
                        required
                      >
                        <option value="">Select Standard</option>
                        {teacherStandard.includes(9) && <option value={9}>Standard 9</option>}
                        {teacherStandard.includes(10) && <option value={10}>Standard 10</option>}
                      </select>
                    )}
                  </FormGroup>
                  <FormGroup>
                    <label>Lessons</label>
                    <CreatableSelect
                      isMulti
                      options={availableLessons}
                      value={selectedLessons}
                      onChange={setSelectedLessons}
                      isLoading={isLessonsLoading}
                      isDisabled={!selectedStandard || customSubject !== teacherSubject}
                      placeholder={
                        !selectedStandard ? "Select standard first"
                        : customSubject !== teacherSubject
                          ? "Lessons disabled for custom subject"
                          : "Select lessons"
                      }
                      className="react-select-container"
                      classNamePrefix="react-select"
                      styles={{
                        control: (base) => ({ ...base, background: 'var(--bg-surface)', borderColor: 'var(--border-default)', '&:hover': { borderColor: 'var(--border-default)' } }),
                        menu: (base) => ({ ...base, background: 'var(--bg-surface)', border: '1px solid var(--border-default)' }),
                        option: (base, state) => ({ ...base, background: state.isFocused ? 'var(--bg-hover)' : 'var(--bg-surface)', color: 'var(--text-primary)', cursor: 'pointer' }),
                        multiValue: (base) => ({ ...base, background: 'var(--bg-hover)' }),
                        multiValueLabel: (base) => ({ ...base, color: 'var(--text-primary)' }),
                        multiValueRemove: (base) => ({ ...base, color: 'var(--text-primary)', ':hover': { background: 'var(--error)', color: 'var(--text-primary)' } }),
                        input: (base) => ({ ...base, color: 'var(--text-primary)' }),
                        placeholder: (base) => ({ ...base, color: 'var(--text-muted)' }),
                      }}
                    />
                  </FormGroup>
                  <GenerateButton type="submit" disabled={!selectedStandard}>
                    Generate Test
                  </GenerateButton>
                </form>
              </TeacherForm>
            )}
            <motion.div
              key="content"
              initial="hidden"
              animate="visible"
              exit="exit"
              variants={fadeTransition}
              className="tests-grid"
            >
              {isLoading ? (
                <ElegantLoader
                  message="Loading Tests..."
                  subMessage="Fetching your test series"
                />
              ) : tests.length === 0 ? (
                <EmptyStateWrapper
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    duration: 0.8,
                    type: "spring",
                    stiffness: 100,
                    damping: 15
                  }}
                >
                  <EmptyStateIcon
                    initial={{ scale: 0, rotate: -180 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{
                      duration: 0.8,
                      delay: 0.2,
                      type: "spring",
                      stiffness: 200
                    }}
                  >
                    🎉
                  </EmptyStateIcon>
                  <EmptyStateTitle
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.3 }}
                  >
                    All Caught Up!
                  </EmptyStateTitle>
                  <EmptyStateText
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.4 }}
                  >
                    You've completed all available tests. Check back later for new challenges to tackle and keep improving!
                  </EmptyStateText>
                </EmptyStateWrapper>
              ) : (
                tests.map((test, index) => (
                  <TestCard
                    key={test['test-id']}
                    $gradient={getSubjectGradient(test.subject)}
                    variants={cardVariants}
                    initial="hidden"
                    animate="visible"
                    whileHover="hover"
                    whileTap={{ scale: 0.98 }}
                    custom={index}
                    onClick={() => handleTestClick(test['test-id'])}
                  >
                    <TestInfo>
                      <h2>{test.test_name || `${getSubjectIcon(test.subject)} ${test.subject}`}</h2>
                      <span className="test-id">#{test['test-id']}</span>
                    </TestInfo>

                    <TestDetails>
                      <Badge>
                        <span>📝</span>
                        {test.questions} Questions
                      </Badge>
                      {test.lessons.length > 0 && (
                        <Badge>
                          <span>📚</span>
                          {test.lessons.length} Lessons
                        </Badge>
                      )}
                      {test.test_name && (
                        <Badge>
                          <span>{getSubjectIcon(test.subject)}</span>
                          {test.subject}
                        </Badge>
                      )}
                    </TestDetails>

                    {test.description && (
                      <TestDescription>{test.description}</TestDescription>
                    )}

                    {test.lessons.length > 0 && (
                      <LessonsList>
                        {test.lessons.map((lesson, idx) => (
                          <LessonTag
                            key={idx}
                            initial={{ opacity: 0, scale: 0.8, x: -20 }}
                            animate={{ opacity: 1, scale: 1, x: 0 }}
                            transition={{
                              delay: index * 0.1 + idx * 0.05,
                              type: "spring",
                              stiffness: 200,
                              damping: 15
                            }}
                          >
                            {lesson}
                          </LessonTag>
                        ))}
                      </LessonsList>
                    )}
                  </TestCard>
                ))
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default TestSeries;
