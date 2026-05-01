import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect, useRef } from 'react'
import { FUEL_COLORS } from '../constants/fuels'
import { SPEED_COLOR } from '../constants/ev'
import { parseKwhPrice, costPer100Miles } from '../utils/evCost'

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

function createFuelMarker(color, selected = false, rank = null, price = '', price_flagged = false) {
  const w = selected ? 64 : 56
  const h = selected ? 30 : 26
  const fontSize = selected ? 13 : 11
  const star = (rank === 0 && !price_flagged) ? '★' : ''
  return L.divIcon({
    className: '',
    html: `<div style="
      position:relative;
      width:${w}px;
      background:${color};
      border-radius:6px;
      border:2px solid rgba(255,255,255,0.4);
      box-shadow:0 2px 8px rgba(0,0,0,0.45);
      display:flex;flex-direction:column;
      align-items:center;justify-content:center;
      padding:2px 4px;
      cursor:pointer;">
      ${star ? `<span style="color:#fff;font-size:10px;line-height:1;text-align:center;width:100%;display:block;">★</span>` : ''}
      <span style="color:#fff;font-size:${fontSize}px;font-weight:700;font-family:'DM Mono',monospace;line-height:1.2;text-align:center;display:block;">${price_flagged ? '⚠️ ' : ''}${price}p</span>
      <div style="
        position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);
        width:0;height:0;
        border-left:5px solid transparent;
        border-right:5px solid transparent;
        border-top:6px solid ${color};">
      </div>
    </div>`,
    iconSize: [w, h + 6],
    iconAnchor: [w / 2, h + 6],
    popupAnchor: [0, -(h + 6)],
  })
}

function createEvMarker(color, selected = false, kw = null, points = null) {
  const w = selected ? 58 : 50
  const h = selected ? 32 : 28
  const kwLabel = kw ? (kw >= 1000 ? `${(kw/1000).toFixed(0)}MW` : `${kw}kW`) : ''
  return L.divIcon({
    className: '',
    html: `<div style="
      position:relative;
      width:${w}px;
      background:${color};
      border-radius:6px;
      border:2px solid rgba(255,255,255,0.4);
      box-shadow:0 2px 8px rgba(0,0,0,0.45);
      display:flex;flex-direction:column;
      align-items:center;justify-content:center;
      padding:2px 4px;
      cursor:pointer;gap:1px;">
      <span style="color:#fff;font-size:10px;line-height:1;">⚡${points ? ` (${points})` : ''}</span>
      <span style="color:#fff;font-size:${selected?12:10}px;font-weight:700;font-family:'DM Mono',monospace;line-height:1;">${kwLabel}</span>
      <div style="
        position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);
        width:0;height:0;
        border-left:5px solid transparent;
        border-right:5px solid transparent;
        border-top:6px solid ${color};">
      </div>
    </div>`,
    iconSize: [w, h + 6],
    iconAnchor: [w / 2, h + 6],
    popupAnchor: [0, -(h + 6)],
  })
}

export default function Map({ stations = [], chargers = [], center, selectedId, hoveredId, fuel, mode = 'fuel', onSelect, onHover, minPrice, maxPrice, units = 'miles', useDriving = false, isPro = false, avgPrice = 0, activeVehicle = null, vehicleFuelMatch = true, economyUnits = 'mpg' }) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef({})
  const selectedIdRef = useRef(null)

  useEffect(() => {
    if (mapInstanceRef.current) return
    const initialZoom = window._pumprZoomHint || 13
    window._pumprZoomHint = null
    const map = L.map(mapRef.current, {
      center: [center.lat, center.lng],
      zoom: initialZoom,
      zoomControl: true,
    })
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
    }).addTo(map)
    const locationMarker = L.divIcon({
      className: '',
      html: `<div style="
        width:20px;height:20px;
        background:#4a9eff;
        border-radius:50%;
        border:3px solid #fff;
        box-shadow:0 0 0 3px rgba(74,158,255,0.4);
        animation:pulse-loc 2s ease-in-out infinite;
        position:relative;">
      </div>
      <style>
        @keyframes pulse-loc {
          0%,100%{box-shadow:0 0 0 3px rgba(74,158,255,0.4)}
          50%{box-shadow:0 0 0 8px rgba(74,158,255,0.1)}
        }
      </style>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    })
    L.marker([center.lat, center.lng], { icon: locationMarker, zIndexOffset: 2000 }).addTo(map)
    mapInstanceRef.current = map
    return () => { map.remove(); mapInstanceRef.current = null }
  }, [])

  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return
    const zoom = window._pumprZoomHint || map.getZoom()
    window._pumprZoomHint = null
    map.setView([center.lat, center.lng], zoom)
  }, [center])

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
          icon: createFuelMarker(color, isSelected || isHovered, i, s.price_pence?.toFixed(1) || '', s.price_flagged),
          zIndexOffset: isSelected ? 1000 : isHovered ? 500 : 0,
        })
        const popup = L.popup({ closeButton: false, offset: [0, -28] }).setContent((() => {
          const pricePerLitre = s.price_pence / 100

          // Distance/time header info
          const hasDriving = useDriving && s.driving_km != null
          const distDisplay = hasDriving
            ? `<span style="color:#f5a623;">🚗 ${(s.driving_km * 0.621371).toFixed(1)} mi${s.driving_mins ? ' · ' + Math.round(s.driving_mins) + 'min' : ''}</span>`
            : s.distance_km != null
              ? `<span style="color:#aaa;">${(s.distance_km * 0.621371).toFixed(1)} mi</span>`
              : null

          // Price change
          const priceChangeLine = s.price_change_pence != null
            ? Math.abs(s.price_change_pence) < 0.05
              ? `<div style="font-size:11px;margin-top:2px;color:#888;">— same as yesterday</div>`
              : `<div style="font-size:11px;margin-top:2px;color:${s.price_change_pence > 0 ? '#e74c3c' : '#2ecc71'};">
                ${s.price_change_pence > 0 ? '▲' : '▼'} ${Math.abs(s.price_change_pence).toFixed(1)}p since yesterday
               </div>`
            : ''

          // Vehicle label
          const vehicleLabel = activeVehicle
            ? activeVehicle.nickname
              ? activeVehicle.nickname
              : (activeVehicle.make && activeVehicle.model)
                ? `${activeVehicle.make} ${activeVehicle.model}`
                : 'Your vehicle'
            : null

          // Pro savings block
          let savingsBlock = ''
          if (isPro && vehicleFuelMatch) {
            const fillLitres = activeVehicle?.tank_litres ? activeVehicle.tank_litres - 5 : 50
            const fillCost = (fillLitres * pricePerLitre).toFixed(2)
            const rawMpg = activeVehicle?.mpg || null
            const effectiveMpg = rawMpg
              ? (economyUnits === 'l100km' ? (282.48 / rawMpg) : rawMpg)
              : null
            const economyLabel = rawMpg
              ? economyUnits === 'l100km'
                ? `${(282.48 / rawMpg).toFixed(1)}L/100km`
                : `${rawMpg}mpg`
              : null
            const vehicleLine = vehicleLabel ? `
                <div style="font-size:11px;color:#aaa;margin-bottom:3px;">🚗 In your ${vehicleLabel}</div>` : ''
            const fillLabel = vehicleLabel
              ? `${fillLitres}L${economyLabel ? ' · ' + economyLabel : ''}`
              : `${fillLitres}L fill`

            let grossSavingLine = ''
            if (avgPrice > 0) {
              const diff = ((avgPrice - s.price_pence) / 100) * fillLitres
              const sign = diff >= 0 ? 'save' : 'extra'
              grossSavingLine = `
                <div style="display:flex;justify-content:space-between;font-size:11px;color:#aaa;margin-top:4px;">
                  <span>vs local avg</span>
                  <span style="color:${diff >= 0 ? '#2ecc71' : '#e74c3c'};">${sign} £${Math.abs(diff).toFixed(2)}</span>
                </div>`
            }

            let netSavingLines = ''
            if (effectiveMpg && hasDriving && avgPrice > 0) {
              const distMiles = s.driving_km * 0.621371
              const roundTripMiles = distMiles * 2
              const costToGetThere = economyUnits === 'l100km'
                ? (roundTripMiles * 1.60934 * effectiveMpg / 100) * pricePerLitre
                : (roundTripMiles / effectiveMpg) * pricePerLitre
              const grossSaving = ((avgPrice - s.price_pence) / 100) * fillLitres
              const netSaving = grossSaving - costToGetThere
              const netColor = netSaving >= 0 ? '#2ecc71' : '#e74c3c'
              const netSign = netSaving >= 0 ? '✓' : '✗'
              netSavingLines = `
                <div style="display:flex;justify-content:space-between;font-size:12px;font-weight:600;color:${netColor};margin-top:6px;">
                  <span>Net after driving</span>
                  <span>${netSign} £${Math.abs(netSaving).toFixed(2)}</span>
                </div>`
              if (netSaving >= 0 && grossSaving > 0) {
                const breakEvenMiles = grossSaving / (pricePerLitre / activeVehicle.mpg) / 2
                netSavingLines += `
                  <div style="display:flex;justify-content:space-between;font-size:10px;color:#888;margin-top:2px;">
                    <span>Break-even at</span>
                    <span>${breakEvenMiles.toFixed(1)} mi</span>
                  </div>`
              }
            }

            savingsBlock = `
              <div style="border-top:1px solid #2d2d2d;margin-top:8px;padding-top:8px;">
                ${vehicleLine}
                <div style="display:flex;justify-content:space-between;font-size:12px;color:#ccc;">
                  <span>${fillLabel}</span>
                  <span style="font-weight:600;color:#fff;">£${fillCost}</span>
                </div>
                ${grossSavingLine}
                ${netSavingLines}
              </div>`
          }

          return `
            <div style="padding:6px 4px;min-width:200px;max-width:240px;">
              <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:2px;">
                <div style="font-size:11px;color:#aaa;font-family:'DM Mono',monospace;text-transform:uppercase;">${s.brand||''}</div>
                ${distDisplay ? `<div style="font-size:11px;color:#aaa;">${distDisplay}</div>` : ''}
              </div>
              <div style="font-size:13px;font-weight:600;color:#fff;margin-bottom:6px;line-height:1.3;">${s.station_name}</div>
              <div style="font-size:30px;font-weight:500;font-family:'DM Mono',monospace;color:${color};line-height:1;">
                ${s.price_pence.toFixed(1)}<span style="font-size:14px;opacity:0.7">p</span>${s.price_flagged ? '<span style="font-size:12px;color:#e74c3c;margin-left:4px;">⚠</span>' : ''}
              </div>
              ${s.price_flagged ? '<div style="font-size:10px;color:#e74c3c;margin-top:2px;">⚠ Price may be unreliable</div>' : ''}
              ${priceChangeLine}
              ${savingsBlock}
            </div>`
        })())
        marker.bindPopup(popup)
        marker.on('click', () => { if (selectedIdRef.current === s.station_id) { onSelect(null); } else { onSelect(s); } })
        marker.on('mouseover', () => { onHover(s.station_id); if (!selectedIdRef.current) marker.openPopup() })
        marker.on('mouseout', () => { onHover(null); if (!selectedIdRef.current) marker.closePopup() })
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
          icon: createEvMarker(color, isSelected || isHovered, c.max_power_kw, c.total_points),
          zIndexOffset: isSelected ? 1000 : isHovered ? 500 : 0,
        })
        const popup = L.popup({ closeButton: false, offset: [0, -28] }).setContent(`
          <div style="padding:4px;min-width:160px;">
            <div style="font-size:11px;color:#aaa;font-family:'DM Mono',monospace;text-transform:uppercase;margin-bottom:4px;">${c.network}</div>
            <div style="font-size:13px;font-weight:600;color:#fff;margin-bottom:6px;line-height:1.3;">${c.name}</div>
            ${c.max_power_kw?`<div style="font-size:24px;font-weight:500;font-family:'DM Mono',monospace;color:${color};">${c.max_power_kw}<span style="font-size:12px;opacity:0.7">kW</span></div>`:''}
${(() => { const kp = parseKwhPrice(c.usage_cost); const c100 = costPer100Miles(kp); if (c100 !== null) return `<div style="font-size:11px;color:#aaa;margin-top:2px;">${c100 === 0 ? 'Free' : '~£' + c100.toFixed(2) + '/100mi'}</div>`; if (c.usage_cost) return `<div style="font-size:11px;color:#aaa;margin-top:2px;">${c.usage_cost}</div>`; return ''; })()}
            
            ${c.distance_km!=null?`<div style="font-size:11px;color:#aaa;margin-top:2px;">${units === 'miles' ? (c.distance_km * 0.621371).toFixed(1) + ' mi' : c.distance_km + ' km'} away</div>`:''}
          </div>
        `)
        marker.bindPopup(popup)
        marker.on('click', () => { if (selectedIdRef.current === c.id) { onSelect(null); } else { onSelect(c); } })
        marker.on('mouseover', () => { onHover(c.id); if (!selectedIdRef.current) marker.openPopup() })
        marker.on('mouseout', () => { onHover(null); if (!selectedIdRef.current) marker.closePopup() })
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
        ? createFuelMarker(color, isSelected || isHovered, i, item.price_pence?.toFixed(1) || '', item.price_flagged)
        : createEvMarker(color, isSelected || isHovered, item.max_power_kw, item.total_points)
      )
      marker.setZIndexOffset(isSelected ? 1000 : isHovered ? 500 : 0)
      if (!isSelected && !isHovered) marker.closePopup()
      if (isSelected) marker.openPopup()
    })
  }, [selectedId, hoveredId])

  useEffect(() => {
    selectedIdRef.current = selectedId
  }, [selectedId])

  return <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
}
