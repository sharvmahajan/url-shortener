# URL Shortener

A fast and efficient URL shortener service built with FastAPI, MongoDB, and Redis. This application provides a simple API to shorten long URLs and redirect to the original URLs with built-in caching for optimal performance.

## Features

- **URL Shortening**: Convert long URLs to compact short codes using base62 encoding
- **QR Code Generation**: Generate QR codes for shortened URLs for easy sharing
- **Redis Caching**: Cache frequently accessed URLs for faster redirects (1-hour TTL)
- **MongoDB Storage**: Persistent storage of shortened URLs with creation timestamps
- **Counter-based Encoding**: Sequential counter-based approach ensures unique short codes
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

## API Endpoints

### POST /shorten

Shorten a long URL.

**Request:**
```bash
curl -X POST "http://localhost:8000/shorten?long_url=https://example.com/very/long/url/path"
```

**Response:**
```json
{
  "short_url": "http://localhost:8000/abc123"
}
```

**Parameters:**
- `long_url` (string, required): The original URL to shorten

**Response Fields:**
- `short_code`: The generated short code
- `short_url`: Full URL to access the shortened link
- `qr_url`: URL to access the QR code for the shortened link

### GET /{code}

Redirect to the original URL.

**Request:**
```bash
curl -L "http://localhost:8000/abc123"
```

**Response:**
- Redirects to the original long URL (HTTP 307)
- Returns 404 if the code is not found

**Parameters:**
- `code` (string, path parameter): The short code

### GET /qr/{code}

Generate and retrieve a QR code for a shortened URL.

**Request:**
```bash
curl "http://localhost:8000/qr/abc123" --output qr.png
```

**Response:**
- Returns a PNG image of the QR code encoding the short URL
- Returns 404 if the code is not found

**Parameters:**
- `code` (string, path parameter): The short code

**Content Type:**
- `image/png`: The response is a PNG image

## How It Works

1. **URL Shortening Flow**:
   - A counter is incremented in MongoDB for each new URL
   - The counter value is encoded using base62 encoding to generate a short code
   - The mapping (short code → long URL) is stored in MongoDB
   - The URL is cached in Redis with a 1-hour TTL

2. **Redirect Flow**:
   - First, the system checks Redis cache for a cache hit
   - If found, it redirects immediately (faster response)
   - If not found (cache miss), it queries MongoDB
   - The URL is then cached in Redis for future requests
   - User is redirected to the original URL

3. **Cache-Aside Architecture**:
   - This application implements the **Cache-Aside (Lazy Loading)** pattern
   - On each request, the application checks the cache first before querying the database
   - Cache misses trigger a database query, and the result is populated back into the cache
   - This approach reduces database load and improves response times for frequently accessed URLs
   - Redis entries have a 1-hour TTL to balance freshness and performance

## Project Structure

```
url-shortener/
├── app/
│   ├── main.py           # FastAPI application and endpoints
│   ├── base62.py         # Base62 encoding utility
│   ├── cache.py          # Redis client configuration
│   ├── database.py       # MongoDB client and collections
│   ├── qr.py             # QR code generation utility
│   ├── schemas.py        # Pydantic request/response models
│   ├── utils.py          # Utility functions (URL hashing)
│   └── __pycache__/
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── pyproject.toml        # Project metadata and dependencies
├── uv.lock               # Dependency lock file
└── README.md             # This file
```

## Performance Considerations

- **Caching**: Redis caching significantly reduces database queries for popular URLs
- **Base62 Encoding**: Generates compact, alphanumeric short codes
- **Async Operations**: FastAPI and Motor provide non-blocking I/O operations
- **Counter-based**: Sequential counter ensures no duplicate short codes

## Error Handling

- **404 Not Found**: Returned when a short code doesn't exist
- **500 Internal Server Error**: Returned for database or cache connection issues

## Future Enhancements

- Custom short codes support
- URL expiration and cleaning
- Analytics (click tracking, statistics)
- Rate limiting
- Admin dashboard
- Batch URL shortening
- API authentication and usage quotas

## Contributing

Contributions are welcome! Feel free to submit issues and enhancement requests.

## License

This project is open source and available under the MIT License.
