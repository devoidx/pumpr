import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect, useRef } from 'react'
import { FUEL_COLORS } from '../constants/fuels'
import { SPEED_COLOR } from '../constants/ev'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

function priceColor(pricePence, minPrice, maxPrice) {
  if (!pricePence || minPrice === maxPrice) return '#f5a623'
  const ratio = (pricePence - minPrice) / (maxPrice - minPrice)
  // green (cheap) → amber (mid) → red (expensive)
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

function createFuelMarker(color, selected = false, rank = null) {
  const size = selected ? 36 : 28
  const rankLabel = rank !== null && rank < 3 ? ['★', '2', '3'][rank] : ''
  return L.divIcon({
    className: '',
    html: `<div style="
      width:${size}px;height:${size}px;background:${color};
      border-radius:50% 50% 50% 0;transform:rotate(-45deg);
      border:2px solid rgba(255,255,255,0.3);
      box-shadow:0 2px 8px rgba(0,0,0,0.5);
      display:flex;align-items:center;justify-content:center;">
      <span style="transform:rotate(45deg);color:#000;font-size:${selected?13:11}px;
        font-weight:700;font-family:'DM Mono',monospace;">${rankLabel}</span>
    </div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size],
  })
}

function createEvMarker(color, selected = false) {
  const size = selected ? 36 : 28
  return L.divIcon({
    className: '',
    html: `<div style="
      width:${size}px;height:${size}px;background:${color};
      border-radius:8px;
      border:2px solid rgba(255,255,255,0.3);
      box-shadow:0 2px 8px rgba(0,0,0,0.5);
      display:flex;align-items:center;justify-content:center;
      font-size:${selected?16:13}px;">
      ⚡
    </div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size],
  })
}

export default function Map({ stations = [], chargers = [], center, selectedId, hoveredId, fuel, mode = 'fuel', onSelect, onHover, minPrice, maxPrice }) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef({})

  useEffect(() => {
    if (mapInstanceRef.current) return
    const map = L.map(mapRef.current, {
      center: [center.lat, center.lng],
      zoom: 13,
      zoomControl: true,
    })
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
    }).addTo(map)
    L.circleMarker([center.lat, center.lng], {
      radius: 8, fillColor: '#fff', fillOpacity: 1,
      color: 'rgba(255,255,255,0.3)', weight: 6,
    }).addTo(map)
    mapInstanceRef.current = map
    return () => { map.remove(); mapInstanceRef.current = null }
  }, [])

  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return

    Object.values(markersRef.current).forEach(m => m.remove())
    markersRef.current = {}

    if (mode === 'fuel') {
      stations.forEach((s, i) => {
        if (!s.latitude || !s.longitude) return
        const color = priceColor(s.price_pence, minPrice, maxPrice)
        const isSelected = s.station_id === selectedId
        const isHovered = s.station_id === hoveredId
        const marker = L.marker([s.latitude, s.longitude], {
          icon: createFuelMarker(color, isSelected || isHovered, i),
          zIndexOffset: isSelected ? 1000 : isHovered ? 500 : 0,
        })
        const popup = L.popup({ closeButton: false, offset: [0, -28] }).setContent(`
          <div style="padding:4px;min-width:160px;">
            <div style="font-size:11px;color:#aaa;font-family:'DM Mono',monospace;text-transform:uppercase;margin-bottom:4px;">${s.brand||''}</div>
            <div style="font-size:13px;font-weight:600;color:#fff;margin-bottom:8px;line-height:1.3;">${s.station_name}</div>
            <div style="font-size:28px;font-weight:500;font-family:'DM Mono',monospace;color:${color};">
              ${s.price_pence.toFixed(1)}<span style="font-size:14px;opacity:0.7">p</span>
            </div>
            ${s.distance_km!=null?`<div style="font-size:11px;color:#aaa;margin-top:4px;">${s.distance_km}km away</div>`:''}
          </div>
        `)
        marker.bindPopup(popup)
        marker.on('click', () => onSelect(s))
        marker.on('mouseover', () => { onHover(s.station_id); marker.openPopup() })
        marker.on('mouseout', () => { onHover(null); marker.closePopup() })
        marker.addTo(map)
        markersRef.current[s.station_id] = marker
      })

      if (stations.length > 0) {
        const lats = stations.filter(s => s.latitude).map(s => s.latitude)
        const lngs = stations.filter(s => s.longitude).map(s => s.longitude)
        if (lats.length > 0) map.fitBounds([[Math.min(...lats),Math.min(...lngs)],[Math.max(...lats),Math.max(...lngs)]], { padding:[40,40], maxZoom:14 })
      }
    } else {
      chargers.forEach(c => {
        if (!c.latitude || !c.longitude) return
        const isSelected = c.id === selectedId
        const isHovered = c.id === hoveredId
        const color = SPEED_COLOR(c.max_power_kw)
        const marker = L.marker([c.latitude, c.longitude], {
          icon: createEvMarker(color, isSelected || isHovered),
          zIndexOffset: isSelected ? 1000 : isHovered ? 500 : 0,
        })
        const popup = L.popup({ closeButton: false, offset: [0, -28] }).setContent(`
          <div style="padding:4px;min-width:160px;">
            <div style="font-size:11px;color:#aaa;font-family:'DM Mono',monospace;text-transform:uppercase;margin-bottom:4px;">${c.network}</div>
            <div style="font-size:13px;font-weight:600;color:#fff;margin-bottom:6px;line-height:1.3;">${c.name}</div>
            ${c.max_power_kw?`<div style="font-size:24px;font-weight:500;font-family:'DM Mono',monospace;color:${color};">${c.max_power_kw}<span style="font-size:12px;opacity:0.7">kW</span></div>`:''}
            ${c.usage_cost?`<div style="font-size:12px;color:#aaa;margin-top:4px;">${c.usage_cost}</div>`:''}
            ${c.distance_km!=null?`<div style="font-size:11px;color:#aaa;margin-top:2px;">${c.distance_km}km away</div>`:''}
          </div>
        `)
        marker.bindPopup(popup)
        marker.on('click', () => onSelect(c))
        marker.on('mouseover', () => { onHover(c.id); marker.openPopup() })
        marker.on('mouseout', () => { onHover(null); marker.closePopup() })
        marker.addTo(map)
        markersRef.current[c.id] = marker
      })

      if (chargers.length > 0) {
        const lats = chargers.filter(c => c.latitude).map(c => c.latitude)
        const lngs = chargers.filter(c => c.longitude).map(c => c.longitude)
        if (lats.length > 0) map.fitBounds([[Math.min(...lats),Math.min(...lngs)],[Math.max(...lats),Math.max(...lngs)]], { padding:[40,40], maxZoom:14 })
      }
    }
  }, [stations, chargers, fuel, mode, minPrice, maxPrice])

  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return
    const items = mode === 'fuel' ? stations : chargers
    const getId = mode === 'fuel' ? s => s.station_id : c => c.id
    const getColor = mode === 'fuel'
      ? (_, i) => priceColor(items[i]?.price_pence, minPrice, maxPrice)
      : (c) => SPEED_COLOR(c.max_power_kw)

    items.forEach((item, i) => {
      const id = getId(item)
      const marker = markersRef.current[id]
      if (!marker) return
      const isSelected = id === selectedId
      const isHovered = id === hoveredId
      const color = getColor(item, i)
      marker.setIcon(mode === 'fuel'
        ? createFuelMarker(color, isSelected || isHovered, i)
        : createEvMarker(color, isSelected || isHovered)
      )
      marker.setZIndexOffset(isSelected ? 1000 : isHovered ? 500 : 0)
      if (isSelected) marker.openPopup()
    })
  }, [selectedId, hoveredId])

  return <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
}
