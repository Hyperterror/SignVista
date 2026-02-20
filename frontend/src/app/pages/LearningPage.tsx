import { useState, useEffect } from 'react';
import gsap from 'gsap';
import { Trophy, Target, BookOpen, CheckCircle, Lock, Play, Star, TrendingUp } from 'lucide-react';
import { Progress } from '../components/ui/progress';

interface Lesson {
  id: number;
  title: string;
  category: string;
  progress: number;
  totalSteps: number;
  completedSteps: number;
  locked: boolean;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  icon: string;
}

interface Quiz {
  id: number;
  title: string;
  questions: number;
  score: number | null;
  difficulty: string;
}

export function LearningPage() {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [overallProgress, setOverallProgress] = useState(0);
  const [streak, setStreak] = useState(7);

  useEffect(() => {
    // Mock lessons data
    const mockLessons: Lesson[] = [
      { id: 1, title: 'ISL Alphabet', category: 'Basics', progress: 100, totalSteps: 26, completedSteps: 26, locked: false, difficulty: 'Beginner', icon: '🔤' },
      { id: 2, title: 'Common Greetings', category: 'Basics', progress: 80, totalSteps: 10, completedSteps: 8, locked: false, difficulty: 'Beginner', icon: '👋' },
      { id: 3, title: 'Family Members', category: 'Vocabulary', progress: 60, totalSteps: 15, completedSteps: 9, locked: false, difficulty: 'Beginner', icon: '👨‍👩‍👧‍👦' },
      { id: 4, title: 'Numbers 1-100', category: 'Basics', progress: 40, totalSteps: 20, completedSteps: 8, locked: false, difficulty: 'Intermediate', icon: '🔢' },
      { id: 5, title: 'Colors & Shapes', category: 'Vocabulary', progress: 0, totalSteps: 12, completedSteps: 0, locked: true, difficulty: 'Beginner', icon: '🎨' },
      { id: 6, title: 'Daily Activities', category: 'Conversation', progress: 0, totalSteps: 18, completedSteps: 0, locked: true, difficulty: 'Intermediate', icon: '🏃' },
    ];

    const mockQuizzes: Quiz[] = [
      { id: 1, title: 'Alphabet Challenge', questions: 26, score: 24, difficulty: 'Beginner' },
      { id: 2, title: 'Greetings Quiz', questions: 10, score: 9, difficulty: 'Beginner' },
      { id: 3, title: 'Family Quiz', questions: 15, score: null, difficulty: 'Beginner' },
    ];

    setLessons(mockLessons);
    setQuizzes(mockQuizzes);

    // Calculate overall progress
    const totalProgress = mockLessons.reduce((acc, lesson) => acc + lesson.progress, 0);
    setOverallProgress(Math.round(totalProgress / mockLessons.length));

    // Entrance animations
    gsap.fromTo(
      '.stats-card',
      { y: 50, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6, stagger: 0.1, ease: 'back.out(1.7)' }
    );

    gsap.fromTo(
      '.lesson-card',
      { x: -50, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.6, stagger: 0.1, delay: 0.3, ease: 'power3.out' }
    );
  }, []);

  const startLesson = (lesson: Lesson) => {
    if (!lesson.locked) {
      // Animation for starting lesson
      gsap.to(`.lesson-${lesson.id}`, {
        scale: 0.95,
        duration: 0.1,
        yoyo: true,
        repeat: 1,
      });
    }
  };

  return (
    <div className="min-h-screen p-6 md:p-12">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
            Learning Hub
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Track your progress and master ISL step by step
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="stats-card bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl p-6 text-white shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <Trophy className="w-8 h-8" />
              <div className="text-3xl font-bold">{overallProgress}%</div>
            </div>
            <div className="text-sm opacity-90">Overall Progress</div>
          </div>

          <div className="stats-card bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl p-6 text-white shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <Target className="w-8 h-8" />
              <div className="text-3xl font-bold">{streak}</div>
            </div>
            <div className="text-sm opacity-90">Day Streak 🔥</div>
          </div>

          <div className="stats-card bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-6 text-white shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <BookOpen className="w-8 h-8" />
              <div className="text-3xl font-bold">{lessons.filter(l => l.progress === 100).length}</div>
            </div>
            <div className="text-sm opacity-90">Lessons Completed</div>
          </div>

          <div className="stats-card bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl p-6 text-white shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <Star className="w-8 h-8" />
              <div className="text-3xl font-bold">850</div>
            </div>
            <div className="text-sm opacity-90">Total Points</div>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Lessons Section */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                Your Learning Path
              </h2>
              <button className="px-4 py-2 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 rounded-xl font-medium hover:bg-violet-200 dark:hover:bg-violet-900/50 transition-colors duration-300">
                View All
              </button>
            </div>

            <div className="space-y-4">
              {lessons.map((lesson) => (
                <div
                  key={lesson.id}
                  className={`
                    lesson-card lesson-${lesson.id}
                    relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700
                    transition-all duration-300 cursor-pointer
                    ${lesson.locked ? 'opacity-60' : 'hover:shadow-2xl hover:-translate-y-1'}
                  `}
                  onClick={() => startLesson(lesson)}
                >
                  {/* Lock overlay */}
                  {lesson.locked && (
                    <div className="absolute top-4 right-4 p-2 bg-gray-200 dark:bg-gray-700 rounded-lg">
                      <Lock className="w-5 h-5 text-gray-500" />
                    </div>
                  )}

                  <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className="text-5xl">{lesson.icon}</div>

                    {/* Content */}
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">
                            {lesson.title}
                          </h3>
                          <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                            <span className="px-2 py-1 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 rounded-full text-xs font-medium">
                              {lesson.category}
                            </span>
                            <span className={`
                              px-2 py-1 rounded-full text-xs font-medium
                              ${lesson.difficulty === 'Beginner' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : ''}
                              ${lesson.difficulty === 'Intermediate' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' : ''}
                              ${lesson.difficulty === 'Advanced' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' : ''}
                            `}>
                              {lesson.difficulty}
                            </span>
                          </div>
                        </div>

                        {!lesson.locked && lesson.progress === 100 && (
                          <CheckCircle className="w-6 h-6 text-green-500" />
                        )}
                      </div>

                      {/* Progress */}
                      <div className="mt-4">
                        <div className="flex items-center justify-between text-sm mb-2">
                          <span className="text-gray-600 dark:text-gray-400">
                            {lesson.completedSteps} / {lesson.totalSteps} steps
                          </span>
                          <span className="font-semibold text-violet-600 dark:text-violet-400">
                            {lesson.progress}%
                          </span>
                        </div>
                        <Progress value={lesson.progress} className="h-2" />
                      </div>

                      {/* Action Button */}
                      {!lesson.locked && (
                        <button className="mt-4 px-6 py-2 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all duration-300 flex items-center gap-2">
                          <Play className="w-4 h-4" />
                          {lesson.progress === 0 ? 'Start Lesson' : lesson.progress === 100 ? 'Review' : 'Continue'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quizzes Section */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                <Target className="w-6 h-6 text-violet-600" />
                Practice Quizzes
              </h3>

              <div className="space-y-3">
                {quizzes.map((quiz) => (
                  <div
                    key={quiz.id}
                    className="p-4 bg-gradient-to-br from-violet-50 to-purple-50 dark:from-gray-700 dark:to-gray-800 rounded-xl hover:shadow-md transition-shadow duration-300 cursor-pointer"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                        {quiz.title}
                      </h4>
                      {quiz.score !== null && (
                        <span className="text-sm font-bold text-green-600 dark:text-green-400">
                          {quiz.score}/{quiz.questions}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-3">
                      {quiz.questions} questions • {quiz.difficulty}
                    </div>
                    <button className="w-full px-4 py-2 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors duration-300">
                      {quiz.score !== null ? 'Retake Quiz' : 'Start Quiz'}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Achievement Board */}
            <div className="bg-gradient-to-br from-yellow-100 to-orange-100 dark:from-yellow-900/20 dark:to-orange-900/20 rounded-2xl p-6 border-2 border-yellow-200 dark:border-yellow-800">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                🏆 Recent Achievements
              </h3>

              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-yellow-500 rounded-full flex items-center justify-center">
                    🥇
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
                      First Lesson
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      Completed ISL Alphabet
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center">
                    🔥
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
                      Week Streak
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      7 days in a row!
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center">
                    ⭐
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
                      Quick Learner
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      3 lessons in one day
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Progress Chart */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-violet-600" />
                Weekly Progress
              </h3>
              
              <div className="flex items-end justify-between h-32 gap-2">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => {
                  const height = [60, 80, 70, 90, 85, 95, 100][index];
                  return (
                    <div key={day} className="flex-1 flex flex-col items-center gap-2">
                      <div 
                        className="w-full bg-gradient-to-t from-violet-600 to-purple-600 rounded-t-lg transition-all duration-500 hover:from-violet-700 hover:to-purple-700"
                        style={{ height: `${height}%` }}
                      />
                      <span className="text-xs text-gray-600 dark:text-gray-400">{day}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
