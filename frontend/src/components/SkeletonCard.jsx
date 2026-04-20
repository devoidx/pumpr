import './SkeletonCard.css'

export default function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton-left">
        <div className="skeleton-line short" />
        <div className="skeleton-line long" />
        <div className="skeleton-line medium" />
      </div>
      <div className="skeleton-price" />
    </div>
  )
}
