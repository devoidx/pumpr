import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import './BlogPage.css'

export default function BlogPostPage() {
  const { slug } = useParams()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    if (typeof umami !== 'undefined') umami.track('blog-post-viewed', { slug })
    fetch(`/api/v1/blog/${slug}`)
      .then(r => { if (!r.ok) throw new Error('not found'); return r.json() })
      .then(data => { setPost(data); setLoading(false) })
      .catch(() => { setNotFound(true); setLoading(false) })
  }, [slug])

  if (loading) return <div className="blog-page"><div className="blog-inner blog-loading">Loading...</div></div>
  if (notFound) return <div className="blog-page"><div className="blog-inner blog-empty">Post not found. <button onClick={() => navigate('/blog')}>Back to blog</button></div></div>

  return (
    <div className="blog-page">
      <div className="blog-inner blog-post">
        <button className="blog-back" onClick={() => navigate('/blog')}>← Back to Insights</button>
        <div className="blog-post-meta">
          <span className="blog-card-type">{post.post_type === 'weekly_prices' ? '⛽ Weekly Update' : '📰 News'}</span>
          <span className="blog-card-date">{new Date(post.published_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
        </div>
        <h1 className="blog-post-title">{post.title}</h1>
        <div className="blog-post-content">
          {post.content.split('\n').map((para, i) => para.trim() ? <p key={i}>{para}</p> : null)}
        </div>
        {post.source_name && post.source_url && (
          <div className="blog-post-source">
            <strong>Source:</strong> <a href={post.source_url} target="_blank" rel="noopener noreferrer">{post.source_name}</a>
          </div>
        )}
      </div>
    </div>
  )
}
