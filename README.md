# URL Shortener

A fast and efficient URL shortener service built with FastAPI, MongoDB, and Redis. This application provides a simple API to shorten long URLs and redirect to the original URLs with built-in caching for optimal performance.


## Features

- **URL Shortening**: Convert long URLs to compact short codes using base62 encoding
- **QR Code Generation**: Generate QR codes for shortened URLs for easy sharing
- **URL Expiration (TTL)**: Set custom expiration times for shortened URLs (minutes, hours, days, months)
- **Expiration Handling**: Automatic cleanup of expired URLs with HTTP 410 responses
- **Redis Caching**: Cache frequently accessed URLs for faster redirects with dynamic TTL
- **MongoDB Storage**: Persistent storage of shortened URLs with creation timestamps and expiration dates
- **Counter-based Encoding**: Sequential counter-based approach ensures unique short codes
- **Analytics Tracking**: Track the number of times each short URL is accessed (clicks)
- **Analytics Endpoint**: Retrieve click statistics and metadata for each short URL
- **Background Analytics Worker**: Asynchronous worker processes analytics events from Redis stream
- **RESTful API**: Simple and intuitive API endpoints

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- **Database**: [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) - Cloud-hosted NoSQL database
- **Cache**: [Upstash Redis](https://upstash.com/) - Serverless Redis
- **Driver**: [Motor](https://motor.readthedocs.io/) - Async MongoDB driver
- **Server**: [Uvicorn](https://www.uvicorn.org/) - ASGI web server
- **QR Code**: [QRCode](https://github.com/lincolnloop/python-qrcode) - QR code generation
- **Environment**: [Python Dotenv](https://github.com/theskumar/python-dotenv) - Environment variable management

## Prerequisites

- Python 3.14+
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) account (cloud database)
- [Upstash Redis](https://upstash.com/) account (serverless Redis)

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sharvmahajan/url-shortener.git
   cd url-shortener
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```
   MONGO_URL=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>
   REDIS_URL=<your-upstash-redis-url>
   ```
   
   To get your MongoDB Atlas URL:
   - Go to [MongoDB Atlas Console](https://cloud.mongodb.com/)
   - Create or select your cluster
   - Click "Connect" and select "Drivers"
   - Copy the connection string and add it to `MONGO_URL`
   
   To get your Upstash Redis URL:
   - Go to [Upstash Console](https://console.upstash.com/)
   - Create or select your Redis database
   - Copy the Redis URL from the connection details

4. **Run the application**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`


## Running the Analytics Worker

The analytics worker tracks click statistics for each short URL. It listens to a Redis stream and updates the click count in MongoDB asynchronously.

**To start the analytics worker:**
```bash
uv run python -m app.analytics_worker
```

This process should be run in a separate terminal alongside the main FastAPI server.

## API Endpoints
### GET /analytics/{code}

Retrieve analytics and metadata for a short URL.

**Request:**
```bash
curl "http://localhost:8000/analytics/abc123"
```

**Response (Success - HTTP 200):**
```json
{
   "short_code": "abc123",
   "long_url": "https://example.com/very/long/url/path",
   "created_at": "2024-04-07T12:34:56.789Z",
   "expire_at": "2024-05-07T12:34:56.789Z",
   "clicks": 42
}
```

**Parameters:**
- `code` (string, path parameter): The short code


### POST /shorten

Shorten a long URL with optional expiration settings.

**Request:**
```bash
curl -X POST "http://localhost:8000/shorten" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/url/path"}'
```

With expiration (30 minutes):
```bash
curl -X POST "http://localhost:8000/shorten" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/url/path", "ttl_value": 30, "ttl_unit": "minutes"}'
```

**Response:**
```json
{
  "short_code": "abc123",
  "short_url": "http://localhost:8000/abc123",
  "qr_url": "http://localhost:8000/qr/abc123"
}
```

**Request Parameters:**
- `url` (string, required): The original URL to shorten
- `ttl_value` (integer, optional): The TTL value (number of time units)
- `ttl_unit` (string, optional): The TTL unit - one of `minutes`, `hours`, `days`, `months`

**Response Fields:**
- `short_code`: The generated short code
- `short_url`: Full URL to access the shortened link
- `qr_url`: URL to access the QR code for the shortened link

**Notes:**
- If no TTL is specified, the URL will never expire
- Expired URLs return HTTP 410 (Gone) status

### GET /{code}

Redirect to the original URL.

**Request:**
```bash
curl -L "http://localhost:8000/abc123"
```

**Response (Success - HTTP 307):**
```
Location: https://example.com/very/long/url/path
```

**Response (Not Found - HTTP 404):**
```json
{
  "detail": "URL not found"
}
```

**Parameters:**
- `code` (string, path parameter): The short code

### GET /qr/{code}

Generate and retrieve a QR code for a shortened URL.

**Request:**
```bash
curl "http://localhost:8000/qr/abc123" --output qr.png
```

**Response (Success - HTTP 200):**
```
Content-Type: image/png
[Binary PNG image data]
```

**Response (Not Found - HTTP 404):**
```json
{
  "detail": "URL not found"
}
```

**Parameters:**
- `code` (string, path parameter): The short code

**Content Type:**
- `image/png`: The response is a PNG image


## How It Works

1. **URL Shortening Flow**:
   - First, the system checks if the long URL has already been shortened (reverse cache lookup using URL hash)
   - If found, it returns the existing short code immediately
   - If not found, a counter is incremented in MongoDB for each new URL
   - The counter value is encoded using base62 encoding to generate a short code
   - An optional expiration time is calculated based on provided TTL parameters
   - The mapping (short code → long URL) is stored in MongoDB with optional expiration timestamp
   - Both the URL and reverse URL-to-code mapping are cached in Redis with a dynamic TTL

2. **Redirect & Analytics Flow**:
   - First, the system checks Redis cache for a cache hit
   - Expiration is validated if the URL has an expiration timestamp
   - If URL is expired, returns HTTP 410 (Gone)
   - If found and valid, it redirects immediately (faster response)
   - On every redirect, an analytics event is pushed to a Redis stream for asynchronous processing
   - If not found (cache miss), it queries MongoDB
   - Expiration is checked again before redirecting
   - The URL is then cached in Redis for future requests with a dynamic TTL
   - User is redirected to the original URL

3. **Expiration Handling**:
   - URLs can have optional expiration times set at creation (minutes, hours, days, months)
   - Both cache and database check expiration before serving the URL
   - Expired URLs return HTTP 410 (Gone) status
   - Redis TTL is dynamically calculated as the minimum of (remaining time to expiration, 1 hour)
   - This prevents expired URLs from being served even if they remain in Redis

4. **Cache-Aside Architecture**:
   - This application implements the **Cache-Aside (Lazy Loading)** pattern
   - On each request, the application checks the cache first before querying the database
   - Cache misses trigger a database query, and the result is populated back into the cache
   - This approach reduces database load and improves response times for frequently accessed URLs
   - Redis TTL is dynamically adjusted based on remaining time to expiration

## Project Structure

```
url-shortner/
├── app/
│   ├── __init__.py            # Package marker
│   ├── analytics_worker.py    # Background analytics worker
│   ├── base62.py              # Base62 encoding utility
│   ├── cache.py               # Redis client configuration
│   ├── database.py            # MongoDB client and collections
│   ├── main.py                # FastAPI application and endpoints
│   ├── qr.py                  # QR code generation utility
│   ├── schemas.py             # Pydantic request/response models
│   └── utils.py               # Utility functions (URL hashing)
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── pyproject.toml             # Project metadata and dependencies
├── uv.lock                    # Dependency lock file
└── README.md                  # This file
```

## Performance Considerations

- **Caching**: Redis caching significantly reduces database queries for popular URLs
- **Base62 Encoding**: Generates compact, alphanumeric short codes
- **Async Operations**: FastAPI and Motor provide non-blocking I/O operations
- **Counter-based**: Sequential counter ensures no duplicate short codes

## Error Handling

- **404 Not Found**: Returned when a short code doesn't exist
- **410 Gone**: Returned when a requested URL has expired
- **500 Internal Server Error**: Returned for database or cache connection issues

## Future Enhancements

- Custom short codes support
- Advanced analytics (geolocation, referrer, device)
- Rate limiting
- Admin dashboard
- Batch URL shortening
- API authentication and usage quotas

## Contributing

Contributions are welcome! Feel free to submit issues and enhancement requests.

## License

This project is open source and available under the MIT License.
