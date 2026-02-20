import { Link } from 'react-router';
import { Home, ArrowLeft } from 'lucide-react';
import { useEffect } from 'react';
import gsap from 'gsap';

export function NotFound() {
  useEffect(() => {
    gsap.fromTo('.not-found-content', { scale: 0.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.8, ease: 'back.out(1.7)' });
    gsap.to('.float-hand', { y: -20, duration: 2, ease: 'power1.inOut', yoyo: true, repeat: -1 });
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="not-found-content max-w-2xl mx-auto text-center">
        <div className="float-hand text-9xl mb-8">👋</div>

        <h1 className="text-8xl font-bold mb-4 bg-clip-text text-transparent"
          style={{ backgroundImage: 'linear-gradient(to right, #344C3D, #105F68)' }}
        >
          404
        </h1>

        <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">Page Not Found</h2>

        <p className="text-xl text-gray-600 dark:text-gray-400 mb-12">
          Oops! The page you're looking for doesn't exist in sign language... or in our app.
        </p>

        <div className="flex flex-wrap gap-4 justify-center">
          <Link
            to="/"
            className="flex items-center gap-2 px-8 py-4 text-white rounded-2xl font-semibold shadow-lg hover:shadow-2xl transition-all duration-300 hover:scale-105"
            style={{ background: 'linear-gradient(135deg, #344C3D, #105F68)' }}
          >
            <Home className="w-5 h-5" />
            Go Home
          </Link>

          <button
            onClick={() => window.history.back()}
            className="flex items-center gap-2 px-8 py-4 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-2xl font-semibold shadow-lg hover:shadow-2xl transition-all duration-300 border-2"
            style={{ borderColor: '#9ED5D1' }}
          >
            <ArrowLeft className="w-5 h-5" />
            Go Back
          </button>
        </div>
      </div>
    </div>
  );
}
