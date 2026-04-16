import { Box, Button, Flex, Grid, Heading, Input, Spinner, Text, Badge } from '@chakra-ui/react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getCheapest } from '../api/client'
import FuelBadge from '../components/FuelBadge'

const FUEL_TYPES = ['E10', 'E5', 'B7', 'SDV', 'B10', 'HVO']

export default function StationList() {
  const [stations, setStations] = useState([])
  const [loading, setLoading] = useState(false)
  const [locating, setLocating] = useState(false)
  const [location, setLocation] = useState(null)
  const [locationError, setLocationError] = useState(null)
  const [fuel, setFuel] = useState('E10')
  const [search, setSearch] = useState('')
  const [radius, setRadius] = useState(5)

  const requestLocation = () => {
    setLocating(true)
    setLocationError(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude })
        setLocating(false)
      },
      () => {
        setLocationError('Could not get your location. Please allow location access and try again.')
        setLocating(false)
      }
    )
  }

  useEffect(() => {
    if (!location) return
    setLoading(true)
    getCheapest(fuel, { lat: location.lat, lng: location.lng, radius_km: radius, limit: 50 })
      .then((r) => setStations(r.data))
      .finally(() => setLoading(false))
  }, [location, fuel, radius])

  const filtered = stations.filter((s) =>
    !search ||
    s.station_name?.toLowerCase().includes(search.toLowerCase()) ||
    s.postcode?.toLowerCase().includes(search.toLowerCase()) ||
    s.brand?.toLowerCase().includes(search.toLowerCase())
  )

  // No location yet — show prompt
  if (!location) {
    return (
      <Box textAlign="center" py={20}>
        <Text fontSize="5xl" mb={4}>⛽</Text>
        <Heading size="lg" mb={2}>Find cheap fuel near you</Heading>
        <Text color="fg.muted" mb={8} maxW="400px" mx="auto">
          Pumpr tracks prices at {(7660).toLocaleString()}+ UK stations in real time.
          Share your location to find the cheapest fuel nearby.
        </Text>
        {locationError && (
          <Text color="red.500" mb={4} fontSize="sm">{locationError}</Text>
        )}
        <Button
          onClick={requestLocation}
          loading={locating}
          loadingText="Locating..."
          colorPalette="orange"
          size="lg"
        >
          📍 Use my location
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6} wrap="wrap" gap={3}>
        <Heading size="lg">Cheapest {fuel} nearby</Heading>
        <Button variant="ghost" size="sm" onClick={() => setLocation(null)}>
          📍 Change location
        </Button>
      </Flex>

      <Flex gap={3} mb={6} wrap="wrap">
        <Input
          placeholder="Filter by name, postcode or brand..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          maxW="320px"
        />
        <select
          value={fuel}
          onChange={(e) => setFuel(e.target.value)}
          style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #ccc', background: 'transparent' }}
        >
          {FUEL_TYPES.map((f) => (
            <option key={f} value={f}>{f}</option>
          ))}
        </select>
        <select
          value={radius}
          onChange={(e) => setRadius(Number(e.target.value))}
          style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #ccc', background: 'transparent' }}
        >
          {[2, 5, 10, 15, 25].map((r) => (
            <option key={r} value={r}>{r} km</option>
          ))}
        </select>
      </Flex>

      {loading ? (
        <Flex justify="center" mt={10}><Spinner /></Flex>
      ) : (
        <>
          <Text fontSize="sm" color="fg.muted" mb={4}>
            {filtered.length} stations within {radius}km
          </Text>
          <Grid templateColumns="repeat(auto-fill, minmax(300px, 1fr))" gap={4}>
            {filtered.map((s, i) => (
              <Box
                key={s.station_id}
                as={Link}
                to={`/stations/${s.station_id}`}
                bg="cardBg"
                p={4}
                rounded="lg"
                shadow="sm"
                _hover={{ shadow: 'md', transform: 'translateY(-1px)' }}
                transition="all 0.15s"
                position="relative"
              >
                {i < 3 && (
                  <Badge
                    position="absolute"
                    top={3}
                    right={3}
                    colorPalette={i === 0 ? 'green' : i === 1 ? 'blue' : 'gray'}
                    fontSize="xs"
                  >
                    #{i + 1} cheapest
                  </Badge>
                )}
                <Flex justify="space-between" align="start" mb={1} pr={i < 3 ? 20 : 0}>
                  <Text fontWeight="bold" fontSize="sm" lineClamp={2}>
                    {s.station_name}
                  </Text>
                </Flex>
                {s.brand && (
                  <Badge mb={2} fontSize="xs">{s.brand}</Badge>
                )}
                <Text fontSize="xs" color="fg.muted" mb={3}>
                  {s.address} {s.postcode} {s.distance_km && `· ${s.distance_km}km`}
                </Text>
                <Flex align="center" justify="space-between">
                  <FuelBadge fuel={s.fuel_type} />
                  <Text fontSize="2xl" fontWeight="black" color="brand.500">
                    {s.price_pence.toFixed(1)}p
                  </Text>
                </Flex>
              </Box>
            ))}
          </Grid>
          {filtered.length === 0 && !loading && (
            <Box textAlign="center" py={10}>
              <Text color="fg.muted">No stations found within {radius}km. Try increasing the radius.</Text>
            </Box>
          )}
        </>
      )}
    </Box>
  )
}
