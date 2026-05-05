import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './BlogPage.css'

export default function BlogPage() {
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    if (typeof umami !== 'undefined') umami.track('blog-listing-viewed')
    fetch('/api/v1/blog?limit=20')
      .then(r => r.json())
      .then(data => { setPosts(data.posts || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div className="blog-page">
      <div className="blog-inner">
        <div className="blog-hero">
          <h1>Fuel Price Insights</h1>
          <p>Weekly analysis, market trends and fuel news for UK drivers</p>
        </div>
        {loading ? (
          <div className="blog-loading">Loading posts...</div>
        ) : posts.length === 0 ? (
          <div className="blog-empty">No posts yet — check back soon.</div>
        ) : (
          <div className="blog-list">
            {posts.map(post => (
              <article key={post.id} className="blog-card" onClick={() => navigate(`/blog/${post.slug}`)}>
                <div className="blog-card-meta">
                  <span className="blog-card-type">{post.post_type === 'weekly_prices' ? '⛽ Weekly Update' : '📰 News'}</span>
                  <span className="blog-card-date">{new Date(post.published_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
                </div>
                <h2 className="blog-card-title">{post.title}</h2>
                <p className="blog-card-summary">{post.summary}</p>
                {post.source_name && (
                  <div className="blog-card-source">Source: {post.source_name}</div>
                )}
                <span className="blog-card-read">Read more →</span>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
