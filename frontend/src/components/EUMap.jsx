import L from 'leaflet'
import { SPEED_COLOR } from '../constants/ev'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import { useEffect, useRef } from 'react'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

function priceColor(priceEur, minPrice, maxPrice) {
  if (!priceEur || minPrice === maxPrice) return '#f5a623'
  const ratio = (priceEur - minPrice) / (maxPrice - minPrice)
  if (ratio < 0.5) {
    const r = Math.round(46 + (245 - 46) * (ratio * 2))
    const g = Math.round(204 - (204 - 166) * (ratio * 2))
    return `rgb(${r},${g},50)`
  } else {
    const r = Math.round(245 - (245 - 231) * ((ratio - 0.5) * 2))
    const g = Math.round(166 - (166 - 76) * ((ratio - 0.5) * 2))
    return `rgb(${r},${g},50)`
  }
}

function createEUMarker(color, price, selected = false) {
  const w = selected ? 64 : 56
  const h = selected ? 30 : 26
  const fontSize = selected ? 13 : 11
  return L.divIcon({
    className: '',
    html: `<div style="position:relative;width:${w}px;">
      <div style="width:${w}px;background:${color};border-radius:6px;border:2px solid rgba(255,255,255,0.4);box-shadow:0 2px 8px rgba(0,0,0,0.45);display:flex;align-items:center;justify-content:center;padding:4px 4px 3px;cursor:pointer;">
        <span style="color:#fff;font-size:${fontSize}px;font-weight:700;font-family:'DM Mono',monospace;line-height:1.2;">€${price}</span>
      </div>
      <div style="position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid ${color};"></div>
    </div>`,
    iconSize: [w, h + 6],
    iconAnchor: [w / 2, h + 6],
    popupAnchor: [0, -(h + 6)],
  })
}

export default function EUMap({ stations = [], chargers = [], showChargers = false, center, selectedId, hoveredId, selectedFuel, eurToGbp, onSelect, onHover, onMapClick }) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef({})
  const selectedIdRef = useRef(null)
  const clusterGroupRef = useRef(null)
  const chargerLayerRef = useRef(null)

  useEffect(() => {
    if (mapInstanceRef.current) return
    mapRef.current.style.background = '#f2f0eb'
    const map = L.map(mapRef.current, {
      center: [center.lat, center.lng],
      zoom: center.zoom || 8,
      zoomControl: true,
    })
    L.tileLayer(`https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=${import.meta.env.VITE_CARTO_API_KEY}`, {
      maxZoom: 19,
      keepBuffer: 4,
      updateWhenIdle: false,
      updateWhenZooming: false,
      crossOrigin: true,
    }).addTo(map)

    map.on('click', e => {
      onMapClick({ lat: e.latlng.lat, lng: e.latlng.lng, zoom: map.getZoom() })
    })

    mapInstanceRef.current = map
    return () => { map.remove(); mapInstanceRef.current = null }
  }, [])

  const lastCenterRef = useRef({ lat: null, lng: null })
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return
    if (!center.recenter) return
    if (center.lat === lastCenterRef.current.lat && center.lng === lastCenterRef.current.lng) return
    lastCenterRef.current = { lat: center.lat, lng: center.lng }
    map.setView([center.lat, center.lng], map.getZoom())
  }, [center])

  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return

    Object.values(markersRef.current).forEach(m => m.remove())
    markersRef.current = {}
    if (clusterGroupRef.current) {
      clusterGroupRef.current.remove()
      clusterGroupRef.current = null
    }
    const clusterGroup = L.markerClusterGroup({
      maxClusterRadius: 40,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
      iconCreateFunction: (cluster) => {
        const count = cluster.getChildCount()
        const markers = cluster.getAllChildMarkers()
        const avgPrice = markers.reduce((sum, m) => sum + (m._euPrice || 0), 0) / markers.length
        return L.divIcon({
          className: '',
          html: `<div style="background:#f5a623;border-radius:50%;width:44px;height:44px;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.45);border:2px solid rgba(255,255,255,0.4);"><span style="color:#000;font-size:10px;font-weight:700;font-family:'DM Mono',monospace;">€${avgPrice.toFixed(2)}</span><span style="color:#000;font-size:9px;opacity:0.7;">${count} stn</span></div>`,
          iconSize: [44, 44],
          iconAnchor: [22, 22],
        })
      },
    })
    clusterGroupRef.current = clusterGroup

    const filtered = stations.filter(s => s.fuel_type === selectedFuel)
    const prices = filtered.map(s => s.price_eur)
    const minPrice = prices.length ? Math.min(...prices) : 0
    const maxPrice = prices.length ? Math.max(...prices) : 0

    filtered.forEach(s => {
      if (!s.latitude || !s.longitude) return
      const color = priceColor(s.price_eur, minPrice, maxPrice)
      const isSelected = s.id === selectedId
      const isHovered = s.id === hoveredId
      const priceLabel = s.price_eur.toFixed(3)

      const marker = L.marker([s.latitude, s.longitude], {
        icon: createEUMarker(color, priceLabel, isSelected || isHovered),
        zIndexOffset: isSelected ? 1000 : isHovered ? 500 : 0,
      })

      const gbpLine = s.price_gbp
        ? `<div style="font-size:13px;color:#aaa;font-family:'DM Mono',monospace;">≈ ${(s.price_gbp * 100).toFixed(1)}p/litre</div>`
        : ''

      const popup = L.popup({ closeButton: false, offset: [0, -20] }).setContent(`
        <div style="padding:6px 4px;min-width:180px;">
          <div style="font-size:13px;font-weight:600;color:#fff;margin-bottom:4px;line-height:1.3;">${s.name || s.address}</div>
          <div style="font-size:11px;color:#aaa;margin-bottom:6px;">${s.city} ${s.postcode} · ${(s.distance_km * 0.621371).toFixed(1)} mi</div>
          <div style="font-size:28px;font-weight:700;font-family:'DM Mono',monospace;color:${color};line-height:1;">€${priceLabel}</div>
          ${gbpLine}
        </div>
      `)

      marker.bindPopup(popup)
      marker.on('click', () => {
        if (selectedIdRef.current === s.id) { onSelect(null) } else { onSelect(s) }
      })
      marker.on('mouseover', () => { onHover(s.id); if (!selectedIdRef.current) marker.openPopup() })
      marker.on('mouseout', () => { onHover(null); if (!selectedIdRef.current) marker.closePopup() })
      marker._euPrice = s.price_eur
      clusterGroup.addLayer(marker)
      markersRef.current[s.id] = marker
    })
    clusterGroup.addTo(map)

  }, [stations, selectedFuel, selectedId, hoveredId])

  // Fit bounds only when stations data changes — not on hover/select
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return
    const filtered = stations.filter(s => s.fuel_type === selectedFuel)
    if (filtered.length > 0) {
      const lats = filtered.map(s => s.latitude)
      const lngs = filtered.map(s => s.longitude)
      map.fitBounds(
        [[Math.min(...lats), Math.min(...lngs)], [Math.max(...lats), Math.max(...lngs)]],
        { padding: [40, 40], maxZoom: 14 }
      )
    }
  }, [stations, selectedFuel])

  // Render EV chargers
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return
    if (chargerLayerRef.current) {
      chargerLayerRef.current.remove()
      chargerLayerRef.current = null
    }
    if (!showChargers || chargers.length === 0) return

    const chargerGroup = L.markerClusterGroup({
      maxClusterRadius: 30,
      showCoverageOnHover: false,
      iconCreateFunction: (cluster) => L.divIcon({
        className: '',
        html: `<div style="background:#2ecc71;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.4);border:2px solid rgba(255,255,255,0.4);font-size:11px;font-weight:700;color:#000;">⚡${cluster.getChildCount()}</div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      })
    })

    chargers.forEach(c => {
      if (!c.latitude || !c.longitude) return
      const marker = L.marker([c.latitude, c.longitude], {
        icon: (() => {
          const color = SPEED_COLOR(c.max_power_kw)
          const kw = c.max_power_kw
          const kwLabel = kw ? (kw >= 1000 ? `${(kw/1000).toFixed(0)}MW` : `${kw}kW`) : ''
          const w = 50, h = 28
          return L.divIcon({
            className: '',
            html: `<div style="position:relative;width:${w}px;background:${color};border-radius:6px;border:2px solid rgba(255,255,255,0.4);box-shadow:0 2px 8px rgba(0,0,0,0.45);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2px 4px;cursor:pointer;gap:1px;">
              <span style="color:#fff;font-size:10px;line-height:1;">⚡${c.total_points ? ` (${c.total_points})` : ''}</span>
              <span style="color:#fff;font-size:10px;font-weight:700;font-family:'DM Mono',monospace;line-height:1;">${kwLabel}</span>
              <div style="position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid ${color};"></div>
            </div>`,
            iconSize: [w, h + 6],
            iconAnchor: [w / 2, h + 6],
          })
        })()
      })
      marker.bindPopup(L.popup({ closeButton: false }).setContent(`
        <div style="padding:6px 4px;min-width:160px;">
          <div style="font-size:13px;font-weight:600;color:#fff;margin-bottom:4px;">${c.name}</div>
          <div style="font-size:11px;color:#aaa;margin-bottom:4px;">${c.address || ''}</div>
          ${c.max_power_kw ? `<div style="font-size:12px;color:#2ecc71;">⚡ ${c.max_power_kw}kW max</div>` : ''}
          <div style="font-size:11px;color:#aaa;">${c.total_points || 0} connector${c.total_points !== 1 ? 's' : ''}</div>
          <div style="font-size:11px;color:#aaa;">${c.network || ''}</div>
        </div>
      `))
      marker.on('mouseover', () => marker.openPopup())
      marker.on('mouseout', () => marker.closePopup())
      chargerGroup.addLayer(marker)
    })

    chargerGroup.addTo(map)
    chargerLayerRef.current = chargerGroup
  }, [chargers, showChargers])

  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return
    const filtered = stations.filter(s => s.fuel_type === selectedFuel)
    const prices = filtered.map(s => s.price_eur)
    const minPrice = prices.length ? Math.min(...prices) : 0
    const maxPrice = prices.length ? Math.max(...prices) : 0

    filtered.forEach(s => {
      const marker = markersRef.current[s.id]
      if (!marker) return
      const isSelected = s.id === selectedId
      const isHovered = s.id === hoveredId
      const color = priceColor(s.price_eur, minPrice, maxPrice)
      marker.setIcon(createEUMarker(color, s.price_eur.toFixed(3), isSelected || isHovered))
      marker.setZIndexOffset(isSelected ? 1000 : isHovered ? 500 : 0)
      if (!isSelected && !isHovered) marker.closePopup()
      if (isSelected) marker.openPopup()
    })
  }, [selectedId, hoveredId])

  useEffect(() => { selectedIdRef.current = selectedId }, [selectedId])

  return <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
}
