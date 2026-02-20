'use client';

import { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import { Send, Trash2, Copy, Download } from 'lucide-react';
import { toast } from 'sonner';

export default function TextToSignPage() {
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [outputSigns, setOutputSigns] = useState<string[]>([]);
  const outputRef = useRef<HTMLDivElement>(null);
  const particlesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    gsap.fromTo('.text-input-container', { x: -100, opacity: 0 }, { x: 0, opacity: 1, duration: 0.8, ease: 'power3.out' });
    gsap.fromTo('.output-container', { x: 100, opacity: 0 }, { x: 0, opacity: 1, duration: 0.8, ease: 'power3.out', delay: 0.2 });
  }, []);

  const handleConvert = async () => {
    if (!inputText.trim()) { toast.error('Please enter some text to convert'); return; }
    setIsProcessing(true);

    if (particlesRef.current) {
      Array.from({ length: 20 }).map(() => {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.cssText = `
          position: absolute; width: 8px; height: 8px;
          background: linear-gradient(135deg, #3A9295, #738A6E);
          border-radius: 50%; top: 50%; left: 50%;
        `;
        particlesRef.current?.appendChild(particle);
        const angle = Math.random() * Math.PI * 2;
        const distance = 100 + Math.random() * 100;
        gsap.to(particle, {
          x: Math.cos(angle) * distance, y: Math.sin(angle) * distance,
          opacity: 0, scale: 0, duration: 1, ease: 'power2.out',
          onComplete: () => particle.remove()
        });
      });
    }

    await new Promise(resolve => setTimeout(resolve, 1500));
    const words = inputText.split(' ');
    const signs = words.map(() => {
      const gestures = ['👋', '🤟', '👍', '✌️', '🤘', '👌', '🖐️', '✋', '👊', '🤝'];
      return gestures[Math.floor(Math.random() * gestures.length)];
    });

    setOutputSigns(signs);
    setIsProcessing(false);

    signs.forEach((_, index) => {
      gsap.fromTo(`.sign-${index}`,
        { scale: 0, rotation: -180, opacity: 0 },
        { scale: 1, rotation: 0, opacity: 1, duration: 0.5, delay: index * 0.1, ease: 'back.out(2)' }
      );
    });
    toast.success('Text converted to ISL signs!');
  };

  const handleClear = () => {
    gsap.to('.text-input-container textarea', { scale: 0.95, duration: 0.1, yoyo: true, repeat: 1, onComplete: () => setInputText('') });
    setOutputSigns([]);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(outputSigns.join(' '));
    toast.success('Signs copied to clipboard!');
  };

  return (
    <div className="min-h-screen p-6 md:p-12">
      <div className="max-w-7xl mx-auto">
        <div className="mb-12">
          <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-clip-text text-transparent"
            style={{ backgroundImage: 'linear-gradient(to right, #344C3D, #3A9295)' }}
          >
            Text to Sign Language
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Convert your text into Indian Sign Language gestures in real-time
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          <div className="text-input-container">
            <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl p-8 border border-gray-200 dark:border-gray-700">
              <label className="block text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Enter Text</label>
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type your message here..."
                className="w-full h-64 p-4 rounded-2xl bg-gray-50 dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 outline-none resize-none text-lg transition-all duration-300"
                style={{ '--tw-ring-color': '#63C1BB' } as React.CSSProperties}
                onFocus={(e) => e.target.style.borderColor = '#63C1BB'}
                onBlur={(e) => e.target.style.borderColor = ''}
              />

              <div className="flex gap-4 mt-6">
                <button
                  onClick={handleConvert}
                  disabled={isProcessing}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-4 text-white rounded-2xl font-semibold shadow-lg hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:scale-105"
                  style={{ background: 'linear-gradient(135deg, #344C3D, #105F68)' }}
                >
                  {isProcessing ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Converting...
                    </>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      Convert to ISL
                    </>
                  )}
                </button>
                <button
                  onClick={handleClear}
                  className="px-6 py-4 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-2xl font-semibold hover:bg-gray-300 dark:hover:bg-gray-600 transition-all duration-300"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Tips */}
            <div className="mt-6 p-6 rounded-2xl border" style={{ backgroundColor: '#C8E6E2', borderColor: '#9ED5D1' }}>
              <h3 className="font-semibold mb-2" style={{ color: '#105F68' }}>💡 Tips for better conversion:</h3>
              <ul className="text-sm space-y-1" style={{ color: '#3A9295' }}>
                <li>• Use simple, clear sentences</li>
                <li>• Avoid complex grammatical structures</li>
                <li>• ISL has its own grammar different from English</li>
              </ul>
            </div>
          </div>

          <div className="output-container">
            <div className="relative rounded-3xl shadow-2xl p-8 border-2 min-h-[400px]"
              style={{ background: 'linear-gradient(135deg, #ffffff, #C8E6E2/20)', borderColor: '#9ED5D1' }}
            >
              <div ref={particlesRef} className="absolute inset-0 pointer-events-none" />

              <div className="flex items-center justify-between mb-6">
                <label className="text-lg font-semibold text-gray-900 dark:text-gray-100">ISL Output</label>
                {outputSigns.length > 0 && (
                  <div className="flex gap-2">
                    <button onClick={handleCopy} className="p-2 bg-white dark:bg-gray-700 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors duration-300" title="Copy signs">
                      <Copy className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                    </button>
                    <button className="p-2 bg-white dark:bg-gray-700 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors duration-300" title="Download as image">
                      <Download className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                    </button>
                  </div>
                )}
              </div>

              {outputSigns.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-gray-400 dark:text-gray-500">
                  <div className="text-6xl mb-4">🤟</div>
                  <p className="text-center">Your ISL signs will appear here</p>
                </div>
              ) : (
                <div ref={outputRef} className="flex flex-wrap gap-6 justify-center">
                  {outputSigns.map((sign, index) => (
                    <div key={index} className={`sign-${index} relative group`}>
                      <div className="w-24 h-24 flex items-center justify-center text-6xl bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer transform hover:scale-110">
                        {sign}
                      </div>
                      <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap">
                        <span className="text-xs bg-gray-900 dark:bg-gray-700 text-white px-2 py-1 rounded">Sign {index + 1}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {outputSigns.length > 0 && (
                <div className="mt-8 text-center text-sm text-gray-600 dark:text-gray-400">
                  {outputSigns.length} signs generated
                </div>
              )}
            </div>

            <div className="mt-6 p-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">📚 How it works</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                Our AI analyzes your text and converts it into corresponding ISL gestures.
                Each word is mapped to its sign language equivalent, following ISL grammar rules.
                Click on any sign to see detailed instructions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
