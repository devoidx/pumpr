/**
 * Parse a kWh price from OCM's free-text usage_cost field.
 * Returns price in pounds per kWh, or null if unparseable.
 */
export function parseKwhPrice(usageCost) {
  if (!usageCost) return null
  const s = usageCost.toLowerCase()

  // Free
  if (s.includes('free') && !s.includes('/kwh')) return 0

  // Match £X.XX/kWh or £X.XX per kWh
  const gbpMatch = s.match(/£\s*(\d+\.?\d*)\s*(?:\/|per)\s*kwh/)
  if (gbpMatch) return parseFloat(gbpMatch[1])

  // Match Xp/kWh (pence)
  const penceMatch = s.match(/(\d+\.?\d*)p\s*(?:\/|per)\s*kwh/)
  if (penceMatch) return parseFloat(penceMatch[1]) / 100

  // Match X.XX GBP/kWh
  const gbpTextMatch = s.match(/(\d+[.,]?\d*)\s*gbp\s*(?:\/|per)\s*kwh/)
  if (gbpTextMatch) return parseFloat(gbpTextMatch[1].replace(',', '.'))

  // DC: £X.XX/kWh style
  const dcMatch = s.match(/dc[^£]*£\s*(\d+\.?\d*)\s*(?:\/|per)\s*kwh/)
  if (dcMatch) return parseFloat(dcMatch[1])

  return null
}

/**
 * Estimate cost per 100 miles given price per kWh.
 * Uses default efficiency of 3.5 miles/kWh (UK average mid-size EV).
 */
export function costPer100Miles(pricePerKwh, efficiencyMilesPerKwh = 3.5) {
  if (pricePerKwh === null || pricePerKwh === undefined) return null
  if (pricePerKwh === 0) return 0
  const cost = (100 / efficiencyMilesPerKwh) * pricePerKwh
  return Math.round(cost * 100) / 100  // round to 2dp
}
