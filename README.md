# VidIQ Scraper

A Python-based web scraper that provides programmatic access to VidIQ's keyword analysis and trending video data through a REST API. This tool automates browser interactions with VidIQ using Playwright and exposes the functionality via FastAPI endpoints.

## Features

- **Keyword Analysis**: Get comprehensive keyword metrics including overall score, search volume, and competition data
- **Trending Videos**: Retrieve VidIQ's "outlier" videos for specific keywords with performance metrics
- **Automated Authentication**: Handles Google OAuth and VidIQ login automatically
- **Persistent Sessions**: Maintains login state across API calls using browser user data
- **REST API**: Clean HTTP endpoints for easy integration with other applications

## Project Structure

```
vidiq_scraper/
├── api.py              # FastAPI application with REST endpoints
├── VidIQ.py           # Core scraping logic and browser automation
├── requirements.txt   # Python dependencies
├── .env-template     # Environment variables template
├── .gitignore        # Git ignore rules
└── README.md         # This documentation
```

## Requirements

- Python 3.7+
- Google account with access to VidIQ
- Valid VidIQ subscription (for full functionality)

## Installation

1. **Navigate to the vidiq-scraper directory**
   ```bash
   cd vidiq-scraper
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

4. **Set up environment variables**
   ```bash
   cp .env-template .env
   ```
   
   Edit the `.env` file and add your Google account credentials:
   ```
   EMAIL_USER=your-email@gmail.com
   EMAIL_PASS=your-app-password
   ```

   **Note**: For Gmail accounts with 2FA enabled, you'll need to generate an [App Password](https://support.google.com/accounts/answer/185833) instead of using your regular password.

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `EMAIL_USER` | Google account email address | Yes |
| `EMAIL_PASS` | Google account password or app password | Yes |

### Browser Data

The application stores browser session data in the `vidiq_user_data` directory to maintain login state between runs. This directory is automatically created and should not be committed to version control.

## Usage

### Starting the Server

```bash
python api.py
```

The server will start on `http://localhost:9090` by default.

### API Documentation

Once the server is running, you can access the interactive API documentation at:
- **Swagger UI**: [http://localhost:9090/docs](http://localhost:9090/docs)
- **ReDoc**: [http://localhost:9090/redoc](http://localhost:9090/redoc)

### API Endpoints

#### Get Keyword Metrics

```http
GET /vidiq/keyword/{keyword}
```

Returns comprehensive VidIQ metrics for a given keyword.

**Parameters:**
- `keyword` (string): The keyword to analyze

**Response:**
```json
{
  "score": "75",
  "score_label": "Good",
  "search_volume": "1.2K",
  "search_label": "High",
  "competition": "45",
  "competition_label": "Medium"
}
```

**Example:**
```bash
curl http://localhost:9090/vidiq/keyword/python%20tutorial
```

#### Get Trending Videos

```http
GET /vidiq/most_popular/{keyword}
```

Returns a list of trending/outlier videos for a specific keyword.

**Parameters:**
- `keyword` (string): The keyword to search for trending videos

**Response:**
```json
[
  {
    "title": "Complete Python Tutorial for Beginners",
    "video_url": "https://www.youtube.com/watch?v=example123",
    "stats": "1.2M views, 2 weeks ago",
    "VPH": "134 VPH",
    "VidIQ_Score": "26x"
  }
]
```

**Example:**
```bash
curl http://localhost:9090/vidiq/most_popular/python%20tutorial
```

## Core Components

### VidIQLogin Class ([`VidIQ.py`](VidIQ.py))

The main scraping class that handles:

- **Browser Management**: Uses Playwright with persistent context for session management
- **Authentication**: Automated Google OAuth and VidIQ login process
- **Data Extraction**: BeautifulSoup-based HTML parsing for metrics and video data
- **Error Handling**: Robust error handling with timeout management

Key methods:
- [`create()`](VidIQ.py:20): Factory method to initialize browser and context
- [`login_to_email()`](VidIQ.py:38): Handles Google account authentication
- [`login_to_vidiq()`](VidIQ.py:56): Manages VidIQ platform login
- [`find_keywords()`](VidIQ.py:237): Scrapes keyword analysis data
- [`find_trending_videos()`](VidIQ.py:162): Extracts trending video information

### FastAPI Application ([`api.py`](api.py))

REST API server that provides:

- **Lifespan Management**: Automatic login handling during application startup
- **Endpoint Routing**: Clean REST endpoints for keyword and video data
- **Error Responses**: Proper HTTP status codes and error messages

## Authentication Flow

1. **Startup**: Application attempts to check existing login status
2. **Email Login**: If not logged in, authenticates with Google account
3. **VidIQ Login**: Uses Google OAuth to access VidIQ platform
4. **Session Persistence**: Saves browser state for future requests
5. **Skip Modals**: Automatically handles VidIQ onboarding and promotional modals

## Error Handling

The application includes comprehensive error handling for:

- **Network timeouts**: Configurable timeout values for page loads
- **Authentication failures**: Detailed error messages for login issues
- **Missing elements**: Graceful handling of page structure changes
- **Rate limiting**: Built-in delays to avoid triggering anti-bot measures

## Development

### Running in Development Mode

For development with auto-reload:

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 9090
```

### Browser Debugging

To run with visible browser for debugging:

1. Modify the `headless=False` parameter in [`VidIQ.py`](VidIQ.py:26)
2. The browser window will be visible during scraping operations

### Adding New Endpoints

To add new scraping functionality:

1. Add the scraping method to the [`VidIQLogin`](VidIQ.py:10) class
2. Create a corresponding endpoint in [`api.py`](api.py)
3. Update this documentation with the new endpoint details

## Troubleshooting

### Common Issues

**Login Failures**
- Verify Google account credentials in `.env` file
- Check if 2FA is enabled and use App Password instead
- Ensure VidIQ account has necessary permissions

**Browser Issues**
- Run `playwright install chromium` to ensure browser is installed
- Check if `vidiq_user_data` directory has proper permissions
- Clear browser data by deleting `vidiq_user_data` directory

**Scraping Failures**
- VidIQ may have updated their page structure
- Check browser screenshots saved during errors
- Verify VidIQ subscription status

**Port Conflicts**
- Default port 9090 may be in use
- Modify the port in [`api.py`](api.py:66) if needed

### Debug Mode

Enable debug logging by modifying the application to include more verbose output. Screenshots are automatically saved during errors to help diagnose issues.

## Security Considerations

- Store credentials securely using environment variables
- Never commit `.env` file or browser data to version control
- Consider using encrypted credential storage for production deployments
- Monitor for unusual login patterns that might trigger account security measures

## Limitations

- Requires active VidIQ subscription for full functionality
- Subject to VidIQ's terms of service and rate limiting
- Browser automation may be detected by anti-bot measures
- Page structure changes may require code updates
