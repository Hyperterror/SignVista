import { useState, useEffect } from 'react';
import gsap from 'gsap';
import { MessageCircle, Heart, Share2, Send, TrendingUp, Users, Video, Award } from 'lucide-react';
import { toast } from 'sonner';

interface Post {
  id: number;
  user: {
    name: string;
    avatar: string;
    level: string;
  };
  content: string;
  type: 'video' | 'text' | 'challenge';
  likes: number;
  comments: number;
  timestamp: string;
  liked: boolean;
}

export function CommunityPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [activeTab, setActiveTab] = useState<'feed' | 'challenges' | 'forums'>('feed');
  const [newPost, setNewPost] = useState('');

  useEffect(() => {
    // Mock community posts
    const mockPosts: Post[] = [
      {
        id: 1,
        user: { name: 'Priya Sharma', avatar: '👩', level: 'Advanced' },
        content: 'Just completed the family signs lesson! Found it really helpful for daily conversations. 🙌',
        type: 'text',
        likes: 42,
        comments: 8,
        timestamp: '2 hours ago',
        liked: false
      },
      {
        id: 2,
        user: { name: 'Rahul Kumar', avatar: '👨', level: 'Intermediate' },
        content: 'Sharing my progress video - 100 signs in 30 days challenge! 🎯',
        type: 'video',
        likes: 128,
        comments: 24,
        timestamp: '5 hours ago',
        liked: true
      },
      {
        id: 3,
        user: { name: 'Ananya Patel', avatar: '👧', level: 'Beginner' },
        content: 'Anyone else struggling with the alphabet? Looking for practice partners!',
        type: 'text',
        likes: 35,
        comments: 16,
        timestamp: '1 day ago',
        liked: false
      },
      {
        id: 4,
        user: { name: 'Vikram Singh', avatar: '👦', level: 'Expert' },
        content: '🏆 Weekly Challenge: Sign your favorite song! Deadline: Sunday',
        type: 'challenge',
        likes: 215,
        comments: 47,
        timestamp: '2 days ago',
        liked: false
      },
    ];

    setPosts(mockPosts);

    // Entrance animations
    gsap.fromTo(
      '.community-card',
      { y: 50, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6, stagger: 0.15, ease: 'power3.out' }
    );
  }, [activeTab]);

  const toggleLike = (postId: number) => {
    setPosts(prev => prev.map(post => {
      if (post.id === postId) {
        const newLiked = !post.liked;
        toast.success(newLiked ? 'Post liked! ❤️' : 'Like removed');
        return {
          ...post,
          liked: newLiked,
          likes: newLiked ? post.likes + 1 : post.likes - 1
        };
      }
      return post;
    }));

    // Animate like button
    gsap.fromTo(
      `.like-btn-${postId}`,
      { scale: 1 },
      { scale: 1.3, duration: 0.2, yoyo: true, repeat: 1, ease: 'power2.out' }
    );
  };

  const handlePost = () => {
    if (!newPost.trim()) return;
    
    toast.success('Post shared with community!');
    setNewPost('');
  };

  const challenges = [
    { id: 1, title: 'Sign a Song', participants: 234, deadline: '3 days', icon: '🎵' },
    { id: 2, title: 'Daily Conversation', participants: 567, deadline: '1 week', icon: '💬' },
    { id: 3, title: 'Alphabet Speed Run', participants: 123, deadline: '2 days', icon: '⚡' },
  ];

  return (
    <div className="min-h-screen p-6 md:p-12">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
            Community
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Connect, learn, and grow together with fellow ISL learners
          </p>
        </div>

        {/* Stats Bar */}
        <div className="grid sm:grid-cols-3 gap-6 mb-8">
          <div className="community-card bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl p-6 text-white shadow-xl">
            <div className="flex items-center gap-3">
              <Users className="w-8 h-8" />
              <div>
                <div className="text-3xl font-bold">50K+</div>
                <div className="text-sm opacity-90">Active Members</div>
              </div>
            </div>
          </div>

          <div className="community-card bg-gradient-to-br from-pink-500 to-red-600 rounded-2xl p-6 text-white shadow-xl">
            <div className="flex items-center gap-3">
              <Video className="w-8 h-8" />
              <div>
                <div className="text-3xl font-bold">12K+</div>
                <div className="text-sm opacity-90">Videos Shared</div>
              </div>
            </div>
          </div>

          <div className="community-card bg-gradient-to-br from-orange-500 to-yellow-600 rounded-2xl p-6 text-white shadow-xl">
            <div className="flex items-center gap-3">
              <Award className="w-8 h-8" />
              <div>
                <div className="text-3xl font-bold">150+</div>
                <div className="text-sm opacity-90">Active Challenges</div>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-8 border-b border-gray-200 dark:border-gray-700">
          {(['feed', 'challenges', 'forums'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`
                pb-4 px-4 font-semibold text-lg capitalize transition-all duration-300
                ${activeTab === tab 
                  ? 'text-violet-600 dark:text-violet-400 border-b-2 border-violet-600' 
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }
              `}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {activeTab === 'feed' && (
              <>
                {/* Create Post */}
                <div className="community-card bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
                  <div className="flex gap-4">
                    <div className="text-4xl">👤</div>
                    <div className="flex-1">
                      <textarea
                        value={newPost}
                        onChange={(e) => setNewPost(e.target.value)}
                        placeholder="Share your ISL journey with the community..."
                        className="w-full p-4 rounded-xl bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 outline-none resize-none focus:ring-2 focus:ring-violet-500 transition-all duration-300"
                        rows={3}
                      />
                      <div className="flex justify-between items-center mt-3">
                        <div className="flex gap-2">
                          <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-300">
                            <Video className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                          </button>
                          <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-300">
                            📸
                          </button>
                        </div>
                        <button
                          onClick={handlePost}
                          disabled={!newPost.trim()}
                          className="px-6 py-2 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center gap-2"
                        >
                          <Send className="w-4 h-4" />
                          Post
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Posts Feed */}
                {posts.map((post) => (
                  <div
                    key={post.id}
                    className="community-card bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-shadow duration-300"
                  >
                    {/* User Info */}
                    <div className="flex items-center gap-3 mb-4">
                      <div className="text-4xl">{post.user.avatar}</div>
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                          {post.user.name}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                          <span className="px-2 py-0.5 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 rounded-full text-xs">
                            {post.user.level}
                          </span>
                          <span>•</span>
                          <span>{post.timestamp}</span>
                        </div>
                      </div>
                      {post.type === 'challenge' && (
                        <div className="px-3 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded-full text-sm font-medium">
                          🏆 Challenge
                        </div>
                      )}
                    </div>

                    {/* Content */}
                    <p className="text-gray-700 dark:text-gray-300 mb-4 leading-relaxed">
                      {post.content}
                    </p>

                    {/* Video Placeholder */}
                    {post.type === 'video' && (
                      <div className="mb-4 aspect-video bg-gradient-to-br from-violet-100 to-purple-100 dark:from-gray-700 dark:to-gray-800 rounded-xl flex items-center justify-center cursor-pointer hover:scale-[1.02] transition-transform duration-300">
                        <div className="text-center">
                          <div className="w-16 h-16 mx-auto mb-3 bg-white dark:bg-gray-900 rounded-full flex items-center justify-center shadow-lg">
                            <Video className="w-8 h-8 text-violet-600" />
                          </div>
                          <p className="text-gray-600 dark:text-gray-400 font-medium">Click to play video</p>
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center gap-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                      <button
                        onClick={() => toggleLike(post.id)}
                        className={`like-btn-${post.id} flex items-center gap-2 transition-colors duration-300 ${
                          post.liked ? 'text-red-500' : 'text-gray-600 dark:text-gray-400 hover:text-red-500'
                        }`}
                      >
                        <Heart className={`w-5 h-5 ${post.liked ? 'fill-current' : ''}`} />
                        <span className="font-medium">{post.likes}</span>
                      </button>

                      <button className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-violet-600 transition-colors duration-300">
                        <MessageCircle className="w-5 h-5" />
                        <span className="font-medium">{post.comments}</span>
                      </button>

                      <button className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-violet-600 transition-colors duration-300 ml-auto">
                        <Share2 className="w-5 h-5" />
                        <span className="font-medium">Share</span>
                      </button>
                    </div>
                  </div>
                ))}
              </>
            )}

            {activeTab === 'challenges' && (
              <div className="space-y-6">
                {challenges.map((challenge) => (
                  <div
                    key={challenge.id}
                    className="community-card bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all duration-300 cursor-pointer hover:scale-[1.02]"
                  >
                    <div className="flex items-start gap-4">
                      <div className="text-6xl">{challenge.icon}</div>
                      <div className="flex-1">
                        <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                          {challenge.title}
                        </h3>
                        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-4">
                          <span className="flex items-center gap-1">
                            <Users className="w-4 h-4" />
                            {challenge.participants} participants
                          </span>
                          <span>•</span>
                          <span>Ends in {challenge.deadline}</span>
                        </div>
                        <button className="px-6 py-3 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-300">
                          Join Challenge
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'forums' && (
              <div className="text-center py-20 community-card">
                <div className="text-6xl mb-4">💬</div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                  Discussion Forums
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Connect with learners, ask questions, and share knowledge
                </p>
                <button className="px-8 py-3 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-300">
                  Browse Forums
                </button>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Trending Topics */}
            <div className="community-card bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-violet-600" />
                Trending Topics
              </h3>
              <div className="space-y-3">
                {['#ISLChallenge', '#BeginnersHelp', '#SignOfTheDay', '#WeeklyGoals', '#ISLTips'].map((topic, index) => (
                  <div
                    key={index}
                    className="p-3 bg-violet-50 dark:bg-violet-900/20 rounded-xl hover:bg-violet-100 dark:hover:bg-violet-900/30 transition-colors duration-300 cursor-pointer"
                  >
                    <div className="font-semibold text-violet-700 dark:text-violet-300 text-sm">
                      {topic}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {Math.floor(Math.random() * 500) + 100} posts
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Contributors */}
            <div className="community-card bg-gradient-to-br from-violet-100 to-purple-100 dark:from-gray-800 dark:to-gray-900 rounded-2xl p-6 border-2 border-violet-200 dark:border-violet-800">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                🌟 Top Contributors
              </h3>
              <div className="space-y-3">
                {[
                  { name: 'Priya S.', points: 2450, avatar: '👩' },
                  { name: 'Rahul K.', points: 2180, avatar: '👨' },
                  { name: 'Ananya P.', points: 1890, avatar: '👧' },
                ].map((user, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className={`
                      w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm
                      ${index === 0 ? 'bg-yellow-500' : index === 1 ? 'bg-gray-400' : 'bg-orange-500'}
                    `}>
                      {index + 1}
                    </div>
                    <div className="text-2xl">{user.avatar}</div>
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
                        {user.name}
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        {user.points} points
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Community Guidelines */}
            <div className="community-card bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-3">
                📋 Community Guidelines
              </h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                <li>• Be respectful and supportive</li>
                <li>• Share constructive feedback</li>
                <li>• Celebrate everyone's progress</li>
                <li>• Keep content relevant to ISL</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
