import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'

export default function Portal({ children }) {
  const el = useRef(document.createElement('div'))

  useEffect(() => {
    const target = document.body
    target.appendChild(el.current)
    return () => target.removeChild(el.current)
  }, [])

  return createPortal(children, el.current)
}
