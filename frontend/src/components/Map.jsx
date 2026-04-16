import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect, useRef } from 'react'
import { FUEL_COLORS } from '../constants/fuels'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

function createMarkerIcon(color, selected = false, rank = null) {
  const size = selected ? 36 : 28
  const fontSize = selected ? 13 : 11
  const rankLabel = rank !== null && rank < 3 ? ['★', '2', '3'][rank] : ''

  return L.divIcon({
    className: '',
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: 2px solid rgba(255,255,255,0.3);
        box-shadow: 0 2px 8px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <span style="
          transform: rotate(45deg);
          color: #000;
          font-size: ${fontSize}px;
          font-weight: 700;
          font-family: 'DM Mono', monospace;
          line-height: 1;
        ">${rankLabel}</span>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size],
  })
}

export default function Map({ stations, center, selectedId, hoveredId, fuel, onSelect, onHover }) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef({})

  // Init map once
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

    // User location dot
    L.circleMarker([center.lat, center.lng], {
      radius: 8,
      fillColor: '#fff',
      fillOpacity: 1,
      color: 'rgba(255,255,255,0.3)',
      weight: 6,
    }).addTo(map)

    mapInstanceRef.current = map

    return () => {
      map.remove()
      mapInstanceRef.current = null
    }
  }, [])

  // Update markers when stations/fuel changes
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return

    const color = FUEL_COLORS[fuel] || '#f5a623'

    Object.values(markersRef.current).forEach(m => m.remove())
    markersRef.current = {}

    stations.forEach((s, i) => {
      if (!s.latitude || !s.longitude) return

      const isSelected = s.station_id === selectedId
      const isHovered = s.station_id === hoveredId

      const marker = L.marker([s.latitude, s.longitude], {
        icon: createMarkerIcon(color, isSelected || isHovered, i),
        zIndexOffset: isSelected ? 1000 : isHovered ? 500 : 0,
      })

      const popup = L.popup({ closeButton: false, offset: [0, -28] }).setContent(`
        <div style="padding: 4px; min-width: 160px;">
          <div style="font-size: 11px; color: #aaaaaa; font-family: 'DM Mono', monospace; text-transform: uppercase; margin-bottom: 4px;">
            ${s.brand || ''}
          </div>
          <div style="font-size: 13px; font-weight: 600; color: #ffffff; margin-bottom: 8px; line-height: 1.3;">
            ${s.station_name}
          </div>
          <div style="font-size: 28px; font-weight: 500; font-family: 'DM Mono', monospace; color: ${color};">
            ${s.price_pence.toFixed(1)}<span style="font-size: 14px; opacity: 0.7">p</span>
          </div>
          ${s.distance_km != null ? `<div style="font-size: 11px; color: #aaaaaa; margin-top: 4px;">${s.distance_km}km away</div>` : ''}
        </div>
      `)

      marker.bindPopup(popup)
      marker.on('click', () => onSelect(s))
      marker.on('mouseover', () => { onHover(s.station_id); marker.openPopup() })
      marker.on('mouseout', () => { onHover(null); marker.closePopup() })
      marker.addTo(map)
      markersRef.current[s.station_id] = marker
    })

    // Fit bounds to markers
    if (stations.length > 0) {
      const lats = stations.filter(s => s.latitude).map(s => s.latitude)
      const lngs = stations.filter(s => s.longitude).map(s => s.longitude)
      if (lats.length > 0) {
        map.fitBounds([
          [Math.min(...lats), Math.min(...lngs)],
          [Math.max(...lats), Math.max(...lngs)],
        ], { padding: [40, 40], maxZoom: 14 })
      }
    }
  }, [stations, fuel])

  // Update selected/hovered markers without full redraw
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return
    const color = FUEL_COLORS[fuel] || '#f5a623'

    stations.forEach((s, i) => {
      const marker = markersRef.current[s.station_id]
      if (!marker) return
      const isSelected = s.station_id === selectedId
      const isHovered = s.station_id === hoveredId
      marker.setIcon(createMarkerIcon(color, isSelected || isHovered, i))
      marker.setZIndexOffset(isSelected ? 1000 : isHovered ? 500 : 0)
      if (isSelected) marker.openPopup()
    })
  }, [selectedId, hoveredId])

  return <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
}

