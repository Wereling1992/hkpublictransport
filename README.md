# HK Public Transport

Home Assistant custom integration that provides real-time Hong Kong bus ETA sensors.

**Domain:** `hkpublictransport`  
**Current version:** 0.1.0 (MVP)

## Features

- Real-time bus ETA (minutes until next arrival)
- Config Flow (UI setup, no YAML required)
- Add by Bus Route → choose direction/service → choose stop
- Shared caching across multiple monitored stops
- Graceful degradation (`ok` / `no_service` / `cached` / `api_error`)
- English-first (Traditional Chinese translation can be added later)

### Supported operators

| Operator | Status |
|----------|--------|
| **KMB / LWB** | Fully working |
| Citybus | Structure ready (stub) |
| NLB | Structure ready (stub) |

## Installation via HACS (recommended)

1. Open **HACS → Integrations**
2. Click the three dots (⋮) in the top right → **Custom repositories**
3. Add repository URL:
   ```
   https://github.com/YOUR_USERNAME/hkpublictransport
   ```
   Category: **Integration**
4. Click **Add**
5. Search for **HK Public Transport** and install it
6. Restart Home Assistant
7. Go to **Settings → Devices & Services → Add Integration** → search **HK Public Transport**

## Manual Installation

1. Download / clone this repository
2. Copy the folder `custom_components/hkpublictransport` into your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Add the integration via the UI

## Usage

1. Add Integration → **HK Public Transport**
2. Choose **Add by Bus Route**
3. Enter a route number (e.g. `72X`, `1A`, `A41`, `962X`)
4. Select the correct direction / service type
5. Select the bus stop you want to monitor

The sensor state shows **minutes until the next bus**.  
Attributes include next/second/third arrival times, destination, status, etc.

## Example Sensor Attributes

- `route`, `operator`, `direction`, `destination`
- `stop_id`, `stop_name`, `stop_seq`
- `next_arrival`, `second_arrival`, `third_arrival`
- `upcoming_arrivals` (list)
- `status_reason`, `last_updated`, `is_scheduled`, `remark`

## Data Sources

Uses official open data APIs from data.gov.hk / etabus (no API key required):

- KMB / LWB: `https://data.etabus.gov.hk/v1/transport/kmb/...`

## Development Status

This is an early MVP. Roadmap:

- [x] KMB / LWB live ETA
- [x] Config Flow (Add by Route)
- [ ] Complete Citybus provider
- [ ] Complete NLB provider
- [ ] Improve “Add by Stop” flow
- [ ] Traditional Chinese translations
- [ ] HACS default repository listing (optional)

## License

MIT
