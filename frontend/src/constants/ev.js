export const CONNECTOR_COLORS = {
  'CCS (Type 2)':  '#3498db',
  'CHAdeMO':       '#e74c3c',
  'Type 2':        '#2ecc71',
  'Type 1':        '#f5a623',
  'Tesla':         '#e74c3c',
  'GB/T':          '#9b59b6',
}

export const CONNECTOR_SHORT = {
  'CCS (Type 2)':  'CCS2',
  'CHAdeMO':       'CHAdeMO',
  'Type 2':        'AC',
  'Type 1':        'AC',
  'Tesla':         'Tesla',
  'GB/T':          'GB/T',
}

export const SPEED_LABEL = (kw) => {
  if (!kw) return 'Unknown'
  if (kw >= 100) return 'Ultra-rapid'
  if (kw >= 50)  return 'Rapid'
  if (kw >= 22)  return 'Fast'
  if (kw >= 7)   return 'Fast'
  return 'Slow'
}

export const SPEED_COLOR = (kw) => {
  if (!kw) return '#555'
  if (kw >= 100) return '#e74c3c'
  if (kw >= 50)  return '#f5a623'
  if (kw >= 22)  return '#2ecc71'
  return '#3498db'
}
