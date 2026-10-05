"use client";

import { useState, useEffect } from 'react';
import gsap from 'gsap';
import { Users, MessageCircle, Heart, Share2, Plus, Globe, ShieldCheck, X, Send } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { api } from '../utils/api';
import { toast } from 'sonner';

interface Comment {
    id: string;
    user_name: string;
    content: string;
    timestamp: number;
}

interface Post {
    id: string;
    user_name: string;
    avatar_initials: string;
    content: string;
    likes: number;
    comments_count: number;
    liked_by_me: boolean;
    timestamp: number;
    is_official: boolean;
    achievement_text?: string | null;
    tags: string[];
}

interface ActiveUser {
    user_id: string;
    name: string;
    initials: string;
    is_online: boolean;
}

const PAGE_SIZE = 20;

export default function CommunityPage() {
    const router = useRouter();
    const [activeTab, setActiveTab] = useState<'feed' | 'liked'>('feed');
    const [posts, setPosts] = useState<Post[]>([]);
    const [hasMore, setHasMore] = useState(false);
    const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [isPostModalOpen, setIsPostModalOpen] = useState(false);
    const [newPostContent, setNewPostContent] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [tagFilter, setTagFilter] = useState<string | null>(null);
    const [openComments, setOpenComments] = useState<Record<string, Comment[] | undefined>>({});
    const [commentDrafts, setCommentDrafts] = useState<Record<string, string>>({});

    const fetchData = async () => {
        try {
            setIsLoading(true);
            const [feedData, usersData] = await Promise.all([
                api.getCommunityFeed(0, PAGE_SIZE),
                api.getActiveUsers()
            ]);
            setPosts(feedData.posts);
            setHasMore(feedData.has_more);
            setActiveUsers(usersData.users);
        } catch (error: any) {
            toast.error(error.message || 'Failed to sync with community');
        } finally {
            setIsLoading(false);
        }
    };

    const loadMore = async () => {
        try {
            setIsLoadingMore(true);
            const feedData = await api.getCommunityFeed(posts.length, PAGE_SIZE);
            setPosts((prev) => [...prev, ...feedData.posts.filter((p: Post) => !prev.some((x) => x.id === p.id))]);
            setHasMore(feedData.has_more);
        } catch (error: any) {
            toast.error(error.message || 'Failed to load more posts');
        } finally {
            setIsLoadingMore(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(() => {
            api.getActiveUsers().then(data => setActiveUsers(data.users)).catch(() => { });
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (!isLoading && posts.length > 0) {
            requestAnimationFrame(() => {
                if (document.querySelector('.community-card')) {
                    gsap.fromTo('.community-card',
                        { scale: 0.95, opacity: 0, y: 20 },
                        { scale: 1, opacity: 1, y: 0, duration: 0.5, stagger: 0.05, ease: 'power2.out' }
                    );
                }
            });
        }
    }, [isLoading]); // eslint-disable-line react-hooks/exhaustive-deps

    const handleCreatePost = async (e: React.FormEvent) => {
        e.preventDefault();
        const content = newPostContent.trim();
        if (!content) return;
        // #hashtags in the text become the post's tags
        const tags = Array.from(new Set((content.match(/#[\p{L}\p{N}_]+/gu) || []).map((t) => t.slice(1)))).slice(0, 10);

        try {
            setIsSubmitting(true);
            const post: Post = await api.createPost(content, tags);
            toast.success('Post shared with the community!');
            setNewPostContent('');
            setIsPostModalOpen(false);
            setPosts((prev) => [post, ...prev]);
        } catch (error: any) {
            toast.error(error.message || 'Failed to share post');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleLike = async (postId: string) => {
        try {
            const result = await api.likePost(postId);
            setPosts(prev => prev.map(p =>
                p.id === postId ? { ...p, likes: result.likes, liked_by_me: result.liked } : p
            ));
        } catch (error: any) {
            toast.error(error.message || 'Could not process like');
        }
    };

    const toggleComments = async (postId: string) => {
        if (openComments[postId]) {
            setOpenComments((prev) => ({ ...prev, [postId]: undefined }));
            return;
        }
        try {
            const comments: Comment[] = await api.getComments(postId);
            setOpenComments((prev) => ({ ...prev, [postId]: comments }));
        } catch (error: any) {
            toast.error(error.message || 'Could not load comments');
        }
    };

    const submitComment = async (postId: string) => {
        const content = (commentDrafts[postId] || '').trim();
        if (!content) return;
        try {
            const comment: Comment = await api.addComment(postId, content);
            setOpenComments((prev) => ({ ...prev, [postId]: [...(prev[postId] || []), comment] }));
            setCommentDrafts((prev) => ({ ...prev, [postId]: '' }));
            setPosts((prev) => prev.map((p) => (p.id === postId ? { ...p, comments_count: p.comments_count + 1 } : p)));
        } catch (error: any) {
            toast.error(error.message || 'Could not add comment');
        }
    };

    const handleShare = async (post: Post) => {
        const text = `${post.user_name} on SignVista: "${post.content}"`;
        try {
            if (navigator.share) {
                await navigator.share({ title: 'SignVista Community', text });
            } else {
                await navigator.clipboard.writeText(text);
                toast.success('Post copied to clipboard');
            }
        } catch {
            // user cancelled the share sheet
        }
    };

    const trendingTags = Object.entries(
        posts.flatMap((p) => p.tags || []).reduce<Record<string, number>>((acc, t) => {
            acc[t] = (acc[t] || 0) + 1;
            return acc;
        }, {})
    ).sort((x, y) => y[1] - x[1]).slice(0, 8).map(([t]) => t);

    const visiblePosts = posts.filter((p) =>
        (activeTab === 'feed' || p.liked_by_me) && (!tagFilter || (p.tags || []).includes(tagFilter))
    );

    const formatTime = (timestamp: number) => {
        const diff = Date.now() / 1000 - timestamp;
        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    };

    return (
        <div className="min-h-screen p-6 md:p-12 bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div>
                        <h1 className="text-4xl md:text-5xl font-black text-[#105F68] dark:text-[#63C1BB]">Community Hub</h1>
                        <p className="text-gray-500 dark:text-gray-400 mt-2">Connect, share, and learn with signers across India</p>
                    </div>
                    <button
                        onClick={() => setIsPostModalOpen(true)}
                        className="px-6 py-4 bg-gradient-to-br from-[#105F68] to-[#3A9295] text-white rounded-2xl font-bold shadow-lg hover:shadow-2xl transition-all flex items-center gap-2 hover:scale-[1.02] active:scale-95"
                    >
                        <Plus className="w-5 h-5" /> New Post
                    </button>
                </div>

                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Main Feed */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="flex gap-4 p-1.5 bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
                            <button
                                onClick={() => setActiveTab('feed')}
                                className={`flex-1 py-3 rounded-xl font-bold text-sm transition-all ${activeTab === 'feed' ? 'bg-[#105F68] text-white shadow-md' : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                            >
                                Live Feed
                            </button>
                            <button
                                onClick={() => setActiveTab('liked')}
                                className={`flex-1 py-3 rounded-xl font-bold text-sm transition-all ${activeTab === 'liked' ? 'bg-[#105F68] text-white shadow-md' : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                            >
                                Liked Posts
                            </button>
                        </div>

                        {tagFilter && (
                            <div className="flex items-center gap-2 text-sm font-bold text-[#105F68]">
                                Showing #{tagFilter}
                                <button onClick={() => setTagFilter(null)} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800" aria-label="Clear tag filter">
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        )}

                        {isLoading ? (
                            <div className="flex flex-col items-center justify-center py-20 opacity-50">
                                <div className="w-12 h-12 border-4 border-[#105F68] border-t-transparent rounded-full animate-spin mb-4" />
                                <p className="font-bold text-[#105F68]">Syncing community feed...</p>
                            </div>
                        ) : visiblePosts.length > 0 ? (
                            visiblePosts.map((item) => (
                                <div key={item.id} className="community-card bg-white dark:bg-gray-900 rounded-3xl p-8 shadow-xl border border-gray-100 dark:border-gray-800 group transition-all hover:border-[#105F68]/30">
                                    <div className="flex items-center gap-4 mb-6">
                                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#105F68] to-[#3A9295] flex items-center justify-center text-white text-xl font-black shadow-lg transform group-hover:rotate-2 transition-transform">
                                            {item.avatar_initials}
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{item.user_name}</h3>
                                                {item.is_official && (
                                                    <span title="Official SignVista Team">
                                                        <ShieldCheck className="w-5 h-5 text-[#105F68]" />
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-sm font-medium text-gray-400">{formatTime(item.timestamp)}</p>
                                        </div>
                                    </div>

                                    <p className="text-xl text-gray-700 dark:text-gray-200 mb-6 leading-relaxed font-medium">
                                        {item.content}
                                    </p>

                                    <div className="flex flex-wrap gap-2 mb-6">
                                        {item.tags?.map((tag: string) => (
                                            <button key={tag} onClick={() => setTagFilter(tag)} className="text-sm font-bold text-[#105F68] dark:text-[#63C1BB] hover:underline">
                                                #{tag}
                                            </button>
                                        ))}
                                    </div>

                                    {item.achievement_text && (
                                        <div className="mb-6 p-5 bg-[#C8E6E2]/20 dark:bg-[#105F68]/10 rounded-2xl flex items-center gap-4 border border-[#C8E6E2]/50 dark:border-[#105F68]/30">
                                            <div className="w-10 h-10 rounded-xl bg-white dark:bg-gray-800 flex items-center justify-center shadow-sm">
                                                <Globe className="w-6 h-6 text-[#105F68]" />
                                            </div>
                                            <span className="text-base font-black text-[#105F68] dark:text-[#63C1BB]">{item.achievement_text}</span>
                                        </div>
                                    )}

                                    <div className="flex items-center gap-8 pt-6 border-t border-gray-50 dark:border-gray-800">
                                        <button
                                            onClick={() => handleLike(item.id)}
                                            aria-pressed={item.liked_by_me}
                                            className={`flex items-center gap-3 transition-all font-bold group/like ${item.liked_by_me ? 'text-pink-500' : 'text-gray-400 hover:text-pink-500'}`}
                                        >
                                            <Heart className={`w-6 h-6 transition-transform group-active/like:scale-150 ${item.liked_by_me ? 'fill-pink-500 text-pink-500' : ''}`} />
                                            <span>{item.likes}</span>
                                        </button>
                                        <button onClick={() => toggleComments(item.id)} className="flex items-center gap-3 text-gray-400 hover:text-[#105F68] transition-all font-bold">
                                            <MessageCircle className="w-6 h-6" />
                                            <span>{item.comments_count}</span>
                                        </button>
                                        <button onClick={() => handleShare(item)} aria-label="Share post" className="ml-auto text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                                            <Share2 className="w-5 h-5" />
                                        </button>
                                    </div>

                                    {openComments[item.id] && (
                                        <div className="mt-6 space-y-4">
                                            {openComments[item.id]!.length === 0 && (
                                                <p className="text-sm text-gray-400">No comments yet.</p>
                                            )}
                                            {openComments[item.id]!.map((c) => (
                                                <div key={c.id} className="p-4 rounded-2xl bg-gray-50 dark:bg-gray-800">
                                                    <p className="text-sm font-bold text-gray-800 dark:text-gray-200">
                                                        {c.user_name} <span className="font-medium text-gray-400">· {formatTime(c.timestamp)}</span>
                                                    </p>
                                                    <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{c.content}</p>
                                                </div>
                                            ))}
                                            <form
                                                onSubmit={(e) => { e.preventDefault(); submitComment(item.id); }}
                                                className="flex gap-2"
                                            >
                                                <input
                                                    value={commentDrafts[item.id] || ''}
                                                    onChange={(e) => setCommentDrafts((prev) => ({ ...prev, [item.id]: e.target.value }))}
                                                    maxLength={1000}
                                                    placeholder="Write a comment..."
                                                    className="flex-1 px-4 py-3 rounded-xl bg-gray-50 dark:bg-gray-800 text-sm outline-none focus:ring-2 focus:ring-[#105F68]/30"
                                                />
                                                <button type="submit" className="px-4 rounded-xl bg-[#105F68] text-white" aria-label="Post comment">
                                                    <Send className="w-4 h-4" />
                                                </button>
                                            </form>
                                        </div>
                                    )}
                                </div>
                            ))
                        ) : (
                            <div className="bg-white dark:bg-gray-800 rounded-3xl p-12 text-center border-2 border-dashed border-gray-200 dark:border-gray-700">
                                <p className="text-xl font-bold text-gray-400">
                                    {activeTab === 'liked' ? "You haven't liked any posts yet." : 'The community is quiet... be the first to post!'}
                                </p>
                            </div>
                        )}

                        {!isLoading && hasMore && (
                            <button
                                onClick={loadMore}
                                disabled={isLoadingMore}
                                className="w-full py-4 rounded-2xl font-bold text-[#105F68] bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 disabled:opacity-50"
                            >
                                {isLoadingMore ? 'Loading...' : 'Load more'}
                            </button>
                        )}
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-8">
                        {/* Users Box */}
                        <div className="bg-white dark:bg-gray-900 rounded-3xl p-8 shadow-xl border border-gray-100 dark:border-gray-800">
                            <h3 className="text-xl font-bold mb-8 flex items-center gap-3 text-gray-900 dark:text-gray-100">
                                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-xl">
                                    <Users className="w-5 h-5 text-green-600" />
                                </div>
                                Active Now
                            </h3>

                            <div className="space-y-6">
                                {activeUsers.length === 0 && (
                                    <p className="text-sm text-gray-500">Nobody else is online right now.</p>
                                )}
                                {activeUsers.map((user) => (
                                    <button
                                        key={user.user_id}
                                        onClick={() => router.push(`/chat?to=${encodeURIComponent(user.user_id)}&name=${encodeURIComponent(user.name)}`)}
                                        title={`Message ${user.name}`}
                                        className="w-full text-left flex items-center gap-4 group cursor-pointer hover:translate-x-1 transition-transform"
                                    >
                                        <div className="relative">
                                            <div className="w-12 h-12 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center font-bold text-gray-500 group-hover:bg-[#105F68] group-hover:text-white transition-colors uppercase">
                                                {user.initials}
                                            </div>
                                            {user.is_online && (
                                                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-4 border-white dark:border-gray-900" />
                                            )}
                                        </div>
                                        <div>
                                            <p className="font-bold text-gray-800 dark:text-gray-200">{user.name}</p>
                                            <p className="text-xs font-bold text-green-500 uppercase tracking-widest">Online · Message</p>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Trending */}
                        <div className="bg-gradient-to-br from-[#105F68] to-[#3A9295] rounded-3xl p-8 text-white shadow-xl relative overflow-hidden group">
                            <div className="absolute -right-4 -bottom-4 opacity-10 group-hover:scale-110 transition-transform duration-500">
                                <Globe className="w-32 h-32" />
                            </div>
                            <h3 className="text-xl font-black mb-6 flex items-center gap-2">
                                Trending Tags
                            </h3>
                            <div className="flex flex-wrap gap-2 relative z-10">
                                {trendingTags.length === 0 && (
                                    <p className="text-sm text-white/70">Add #hashtags to your posts to start a trend.</p>
                                )}
                                {trendingTags.map(tag => (
                                    <button
                                        key={tag}
                                        onClick={() => setTagFilter(tag)}
                                        className={`px-3 py-2 rounded-xl text-sm font-bold transition-all hover:scale-105 active:scale-95 ${tagFilter === tag ? 'bg-white text-[#105F68]' : 'bg-white/10 hover:bg-white/20'}`}
                                    >
                                        #{tag}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* New Post Modal */}
            {isPostModalOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="bg-white dark:bg-gray-900 rounded-[40px] w-full max-w-xl p-8 shadow-2xl relative translate-y-0 scale-100 transition-all duration-300 border border-white/20">
                        <div className="flex items-center justify-between mb-8">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-2xl bg-[#105F68] flex items-center justify-center text-white">
                                    <Plus className="w-6 h-6" />
                                </div>
                                <h2 className="text-3xl font-black text-gray-900 dark:text-gray-100">Create Post</h2>
                            </div>
                            <button
                                onClick={() => setIsPostModalOpen(false)}
                                className="p-3 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
                            >
                                <X className="w-6 h-6 text-gray-400" />
                            </button>
                        </div>

                        <form onSubmit={handleCreatePost} className="space-y-6">
                            <textarea
                                value={newPostContent}
                                onChange={(e) => setNewPostContent(e.target.value)}
                                placeholder="What's your Sign Language update today? Use #hashtags to tag it."
                                maxLength={2000}
                                className="w-full h-40 p-6 bg-gray-50 dark:bg-gray-800/50 rounded-3xl border border-gray-100 dark:border-gray-700 outline-none focus:border-[#105F68] transition-all resize-none text-lg font-medium dark:text-white"
                                autoFocus
                            />

                            <div className="flex gap-4">
                                <button
                                    type="button"
                                    onClick={() => setIsPostModalOpen(false)}
                                    className="flex-1 h-16 rounded-2xl font-black text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all uppercase tracking-widest text-sm"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={isSubmitting || !newPostContent.trim()}
                                    className="flex-[2] h-16 rounded-2xl bg-[#105F68] text-white font-black shadow-lg hover:shadow-2xl transition-all flex items-center justify-center gap-3 disabled:opacity-50 uppercase tracking-widest text-sm"
                                >
                                    {isSubmitting ? 'Sharing...' : (
                                        <>
                                            Post Hub <Send className="w-4 h-4" />
                                        </>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
