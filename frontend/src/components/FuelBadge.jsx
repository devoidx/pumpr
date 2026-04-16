import { Badge } from '@chakra-ui/react'

const FUEL_COLORS = {
  E10: 'green',
  E5: 'blue',
  B7: 'orange',
  SDV: 'purple',
  B10: 'teal',
  HVO: 'cyan',
}

const FUEL_LABELS = {
  E10: 'E10 Unleaded',
  E5: 'E5 Super',
  B7: 'B7 Diesel',
  SDV: 'Super Diesel',
  B10: 'B10',
  HVO: 'HVO',
}

export default function FuelBadge({ fuel }) {
  return (
    <Badge colorPalette={FUEL_COLORS[fuel] || 'gray'}>
      {FUEL_LABELS[fuel] || fuel}
    </Badge>
  )
}
