import { createContext, useContext, useEffect, useState } from 'react'

export const BRAND_ALIASES = {
  'BP HARVEST ENERGY': 'BP',
  'SHELL HARVEST ENERGY': 'SHELL',
  'TOTAL HARVEST ENERGY': 'TOTAL ENERGIES',
  'HARVEST ENERGY': 'SHELL',
  'HARVEST': 'SHELL',
  'COSTCO': 'COSTCO WHOLESALE',
  'JET / LONDIS': 'JET',
  'GULF PETROL STATION': 'GULF',
  'EAST OF ENGLAND CO-OP': 'SPAR',
}

const BrandsContext = createContext({})

export function BrandsProvider({ children }) {
  const [logos, setLogos] = useState({})

  useEffect(() => {
    fetch('/api/v1/stations/brands/logos')
      .then(r => r.ok ? r.json() : [])
      .then(data => {
        const map = {}
        data.forEach(b => { map[b.name.toUpperCase()] = b.logo })
        setLogos(map)
      })
      .catch(() => {})
  }, [])

  return (
    <BrandsContext.Provider value={logos}>
      {children}
    </BrandsContext.Provider>
  )
}

export function useBrandLogos() {
  return useContext(BrandsContext)
}
