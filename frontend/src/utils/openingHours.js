const DAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

export function isOpenNow(openingTimes) {
  if (!openingTimes) return null
  const now = new Date()
  const dayName = DAY_NAMES[now.getDay() === 0 ? 6 : now.getDay() - 1]
  const usual = openingTimes.usual_days || {}
  const day = usual[dayName] || {}

  if (day.is_24_hours) return true

  const openStr = day.open
  const closeStr = day.close
  if (!openStr || !closeStr) return null

  const [oh, om] = openStr.split(':').map(Number)
  const [ch, cm] = closeStr.split(':').map(Number)

  if (oh === 0 && om === 0 && ch === 0 && cm === 0) return null

  const nowMins = now.getHours() * 60 + now.getMinutes()
  const openMins = oh * 60 + om
  const closeMins = ch * 60 + cm

  if (closeMins < openMins) {
    return nowMins >= openMins || nowMins <= closeMins
  }
  return nowMins >= openMins && nowMins <= closeMins
}

export function formatHours(day) {
  if (!day) return 'Unknown'
  if (day.is_24_hours) return '24 hours'
  const open = (day.open || '').slice(0, 5)
  const close = (day.close || '').slice(0, 5)
  if (!open || (open === '00:00' && close === '00:00')) return 'Closed'
  return `${open} – ${close}`
}

export function getWeekHours(openingTimes) {
  if (!openingTimes?.usual_days) return []
  return DAY_NAMES.map(day => ({
    day: day.charAt(0).toUpperCase() + day.slice(1),
    hours: formatHours(openingTimes.usual_days[day]),
    is_24_hours: openingTimes.usual_days[day]?.is_24_hours || false,
  }))
}

export function getTodayHours(openingTimes) {
  if (!openingTimes?.usual_days) return null
  const now = new Date()
  const dayName = DAY_NAMES[now.getDay() === 0 ? 6 : now.getDay() - 1]
  return formatHours(openingTimes.usual_days[dayName])
}
