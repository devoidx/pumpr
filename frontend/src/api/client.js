import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 30000,
})

export const getStats = () => client.get('/api/v1/prices/stats')
export const getCheapest = (fuel, params) =>
  client.get('/api/v1/prices/cheapest', { params: { fuel, ...params } })
export const getStations = (params) => client.get('/api/v1/stations/', { params })
export const getStation = (id) => client.get(`/api/v1/stations/${id}`)
export const getPriceHistory = (id, fuel, params) =>
  client.get(`/api/v1/stations/${id}/history`, { params: { fuel, ...params } })

export default client

export const getChargers = (params) =>
  client.get('/api/v1/ev/chargers', { params })
export const getCharger = (id) =>
  client.get(`/api/v1/ev/chargers/${id}`)

export const getPriceChanges = (id) =>
  client.get(`/api/v1/stations/${id}/price-changes`)
