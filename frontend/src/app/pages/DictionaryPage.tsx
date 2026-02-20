import { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import { Search, Filter, Play, Star, BookmarkPlus, BookmarkCheck } from 'lucide-react';
import { toast } from 'sonner';

interface DictionaryWord {
  id: number;
  word: string;
  category: string;
  gesture: string;
  description: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  bookmarked: boolean;
}

export function DictionaryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [words, setWords] = useState<DictionaryWord[]>([]);
  const [filteredWords, setFilteredWords] = useState<DictionaryWord[]>([]);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Generate mock dictionary data
    const categories = ['Greetings', 'Family', 'Food', 'Numbers', 'Colors', 'Actions', 'Emotions', 'Places'];
    const difficulties: ('Easy' | 'Medium' | 'Hard')[] = ['Easy', 'Medium', 'Hard'];
    const gestures = ['👋', '🤟', '👍', '✌️', '🤘', '👌', '🖐️', '✋', '👊', '🤝', '🙏', '💪', '🤲', '👏', '🤞'];
    
    const mockWords: DictionaryWord[] = Array.from({ length: 50 }, (_, i) => ({
      id: i + 1,
      word: `Sign Word ${i + 1}`,
      category: categories[Math.floor(Math.random() * categories.length)],
      gesture: gestures[Math.floor(Math.random() * gestures.length)],
      description: 'A common ISL sign used in daily conversation',
      difficulty: difficulties[Math.floor(Math.random() * difficulties.length)],
      bookmarked: false
    }));

    setWords(mockWords);
    setFilteredWords(mockWords);

    // Entrance animation
    gsap.fromTo(
      '.search-bar',
      { y: -50, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }
    );

    gsap.fromTo(
      '.category-filter',
      { y: -30, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6, delay: 0.1, ease: 'power3.out' }
    );
  }, []);

  useEffect(() => {
    // Filter words
    let filtered = words;

    if (searchQuery) {
      filtered = filtered.filter(word =>
        word.word.toLowerCase().includes(searchQuery.toLowerCase()) ||
        word.category.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (selectedCategory !== 'All') {
      filtered = filtered.filter(word => word.category === selectedCategory);
    }

    setFilteredWords(filtered);

    // Animate cards
    gsap.fromTo(
      '.word-card',
      { scale: 0.9, opacity: 0, y: 20 },
      { 
        scale: 1, 
        opacity: 1, 
        y: 0, 
        duration: 0.4, 
        stagger: 0.05,
        ease: 'back.out(1.7)'
      }
    );
  }, [searchQuery, selectedCategory, words]);

  const toggleBookmark = (id: number) => {
    setWords(prev => prev.map(word =>
      word.id === id ? { ...word, bookmarked: !word.bookmarked } : word
    ));
    
    const word = words.find(w => w.id === id);
    if (word) {
      toast.success(word.bookmarked ? 'Removed from bookmarks' : 'Added to bookmarks');
    }
  };

  const playSign = (word: string) => {
    toast.success(`Playing sign for "${word}"`);
  };

  const categories = ['All', 'Greetings', 'Family', 'Food', 'Numbers', 'Colors', 'Actions', 'Emotions', 'Places'];

  return (
    <div className="min-h-screen p-6 md:p-12">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
            ISL Dictionary
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Explore 1000+ Indian Sign Language words with video demonstrations
          </p>
        </div>

        {/* Search Bar */}
        <div className="search-bar mb-8">
          <div className="relative">
            <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-gray-400" />
            <input
              ref={searchRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for signs, words, or categories..."
              className="w-full pl-16 pr-6 py-5 rounded-2xl bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 focus:border-violet-500 dark:focus:border-violet-500 outline-none text-lg shadow-lg transition-all duration-300"
            />
          </div>
        </div>

        {/* Category Filter */}
        <div className="category-filter mb-12">
          <div className="flex items-center gap-3 mb-4">
            <Filter className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            <span className="font-semibold text-gray-900 dark:text-gray-100">Categories</span>
          </div>
          <div className="flex flex-wrap gap-3">
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`
                  px-6 py-3 rounded-xl font-medium transition-all duration-300
                  ${selectedCategory === category
                    ? 'bg-gradient-to-r from-violet-600 to-purple-600 text-white shadow-lg scale-105'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'
                  }
                `}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-6 text-gray-600 dark:text-gray-400">
          Showing {filteredWords.length} {filteredWords.length === 1 ? 'sign' : 'signs'}
        </div>

        {/* Dictionary Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredWords.map((word, index) => (
            <div
              key={word.id}
              className="word-card group relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg hover:shadow-2xl border border-gray-200 dark:border-gray-700 transition-all duration-300 cursor-pointer overflow-hidden"
            >
              {/* Background gradient on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-violet-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

              {/* Content */}
              <div className="relative z-10">
                {/* Category Badge */}
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs px-3 py-1 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 rounded-full font-medium">
                    {word.category}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleBookmark(word.id);
                    }}
                    className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-300"
                  >
                    {word.bookmarked ? (
                      <BookmarkCheck className="w-5 h-5 text-violet-600" />
                    ) : (
                      <BookmarkPlus className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                </div>

                {/* Gesture */}
                <div className="text-7xl text-center mb-4 group-hover:scale-110 transition-transform duration-300">
                  {word.gesture}
                </div>

                {/* Word */}
                <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 text-center">
                  {word.word}
                </h3>

                {/* Description */}
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 text-center">
                  {word.description}
                </p>

                {/* Difficulty */}
                <div className="flex items-center justify-center gap-2 mb-4">
                  <span className={`
                    text-xs px-3 py-1 rounded-full font-medium
                    ${word.difficulty === 'Easy' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : ''}
                    ${word.difficulty === 'Medium' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' : ''}
                    ${word.difficulty === 'Hard' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' : ''}
                  `}>
                    {word.difficulty}
                  </span>
                </div>

                {/* Play Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    playSign(word.word);
                  }}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl font-semibold opacity-0 group-hover:opacity-100 transition-all duration-300 hover:scale-105"
                >
                  <Play className="w-4 h-4" />
                  Play Video
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {filteredWords.length === 0 && (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              No signs found
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Try adjusting your search or filter criteria
            </p>
          </div>
        )}

        {/* Info Section */}
        <div className="mt-16 p-8 bg-gradient-to-br from-violet-100 to-purple-100 dark:from-gray-800 dark:to-gray-900 rounded-3xl border-2 border-violet-200 dark:border-violet-800">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            💡 How to use the dictionary
          </h2>
          <ul className="space-y-2 text-gray-700 dark:text-gray-300">
            <li className="flex items-start gap-3">
              <span className="text-violet-600 font-bold">1.</span>
              Search for any word or browse by category
            </li>
            <li className="flex items-start gap-3">
              <span className="text-violet-600 font-bold">2.</span>
              Click on a card to see detailed video demonstration
            </li>
            <li className="flex items-start gap-3">
              <span className="text-violet-600 font-bold">3.</span>
              Bookmark words to save them for later practice
            </li>
            <li className="flex items-start gap-3">
              <span className="text-violet-600 font-bold">4.</span>
              Practice regularly to improve your ISL vocabulary
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
