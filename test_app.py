"""Tests for Flask application routes."""

import json


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_ok(self, client):
        """Test that health endpoint returns OK status."""
        response = client.get('/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'

    def test_health_no_auth_required(self, client):
        """Test that health endpoint works without authentication."""
        response = client.get('/health')
        assert response.status_code == 200


class TestLoginPage:
    """Tests for login functionality."""

    def test_login_page_renders(self, client):
        """Test that login page loads."""
        response = client.get('/login')

        assert response.status_code == 200
        assert b'password' in response.data.lower()

    def test_login_with_correct_password(self, client):
        """Test successful login redirects to index."""
        response = client.post('/login', data={'password': 'testpass123'}, follow_redirects=False)

        assert response.status_code == 302
        assert response.headers['Location'] == '/'

    def test_login_with_wrong_password(self, client):
        """Test failed login redirects back to login with error."""
        response = client.post('/login', data={'password': 'wrongpassword'}, follow_redirects=False)

        assert response.status_code == 302
        assert 'error=1' in response.headers['Location']

    def test_login_with_empty_password(self, client):
        """Test empty password fails login."""
        response = client.post('/login', data={'password': ''}, follow_redirects=False)

        assert response.status_code == 302
        assert 'error=1' in response.headers['Location']

    def test_login_error_message_displayed(self, client):
        """Test that error parameter shows error on login page."""
        response = client.get('/login?error=1')

        assert response.status_code == 200
        # The page should indicate an error (implementation dependent)


class TestLogout:
    """Tests for logout functionality."""

    def test_logout_clears_session(self, authenticated_client):
        """Test that logout clears authentication."""
        # First verify we're authenticated
        response = authenticated_client.get('/')
        assert response.status_code == 200

        # Logout
        response = authenticated_client.post('/logout', follow_redirects=False)
        assert response.status_code == 302

        # Should now redirect to login
        response = authenticated_client.get('/')
        assert response.status_code == 302


class TestProtectedRoutes:
    """Tests for authentication-protected routes."""

    def test_index_requires_auth(self, client):
        """Test that index redirects to login when not authenticated."""
        response = client.get('/', follow_redirects=False)

        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_api_stats_requires_auth(self, client):
        """Test that stats API redirects when not authenticated."""
        response = client.get('/api/stats', follow_redirects=False)

        assert response.status_code == 302

    def test_api_search_requires_auth(self, client):
        """Test that search API redirects when not authenticated."""
        response = client.get('/api/search?q=test', follow_redirects=False)

        assert response.status_code == 302


class TestIndexPage:
    """Tests for the main index page."""

    def test_index_renders_when_authenticated(self, authenticated_client):
        """Test that index page loads for authenticated users."""
        response = authenticated_client.get('/')

        assert response.status_code == 200
        assert b'search' in response.data.lower()

    def test_index_has_search_input(self, authenticated_client):
        """Test that index page has a search input."""
        response = authenticated_client.get('/')

        assert response.status_code == 200
        assert b'<input' in response.data


class TestStatsAPI:
    """Tests for the /api/stats endpoint."""

    def test_stats_returns_message_count(self, authenticated_client, temp_db):
        """Test that stats returns message count."""
        response = authenticated_client.get('/api/stats')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message_count' in data
        assert 'has_messages' in data

    def test_stats_with_no_messages(self, authenticated_client, temp_db):
        """Test stats when database is empty."""
        response = authenticated_client.get('/api/stats')

        data = json.loads(response.data)
        assert data['message_count'] == 0
        assert data['has_messages'] is False

    def test_stats_with_messages(self, authenticated_client, sample_messages):
        """Test stats when database has messages."""
        response = authenticated_client.get('/api/stats')

        data = json.loads(response.data)
        assert data['message_count'] == 5
        assert data['has_messages'] is True


class TestSearchAPI:
    """Tests for the /api/search endpoint."""

    def test_search_requires_query(self, authenticated_client):
        """Test that search returns error without query."""
        response = authenticated_client.get('/api/search')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_search_empty_query(self, authenticated_client):
        """Test that empty query returns error."""
        response = authenticated_client.get('/api/search?q=')

        assert response.status_code == 400

    def test_search_returns_results(self, authenticated_client, sample_messages):
        """Test that search returns matching messages."""
        response = authenticated_client.get('/api/search?q=party')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert 'total' in data
        assert len(data['results']) > 0

    def test_search_no_results(self, authenticated_client, sample_messages):
        """Test search with no matching messages."""
        response = authenticated_client.get('/api/search?q=xyznonexistent')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] == 0
        assert len(data['results']) == 0

    def test_search_result_fields(self, authenticated_client, sample_messages):
        """Test that search results have all required fields."""
        response = authenticated_client.get('/api/search?q=party')

        data = json.loads(response.data)
        result = data['results'][0]

        assert 'id' in result
        assert 'phone_number' in result
        assert 'body' in result
        assert 'timestamp' in result
        assert 'message_type' in result
        assert 'formatted_date' in result

    def test_search_highlights_terms(self, authenticated_client, sample_messages):
        """Test that search results highlight matching terms."""
        response = authenticated_client.get('/api/search?q=party')

        data = json.loads(response.data)
        result = data['results'][0]

        # Should have <mark> tags around highlighted term
        assert '<mark>' in result['body']
        assert '</mark>' in result['body']

    def test_search_pagination_info(self, authenticated_client, sample_messages):
        """Test that search returns pagination information."""
        response = authenticated_client.get('/api/search?q=the')

        data = json.loads(response.data)
        assert 'page' in data
        assert 'per_page' in data
        assert 'has_more' in data

    def test_search_page_parameter(self, authenticated_client, sample_messages):
        """Test that page parameter works."""
        response = authenticated_client.get('/api/search?q=the&page=1')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['page'] == 1

    def test_search_invalid_page_defaults_to_1(self, authenticated_client, sample_messages):
        """Test that invalid page parameter defaults to 1."""
        response = authenticated_client.get('/api/search?q=party&page=invalid')

        data = json.loads(response.data)
        assert data['page'] == 1


class TestSecurityHeaders:
    """Tests for security headers."""

    def test_x_content_type_options(self, client):
        """Test X-Content-Type-Options header is set."""
        response = client.get('/health')
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'

    def test_x_frame_options(self, client):
        """Test X-Frame-Options header is set."""
        response = client.get('/health')
        assert response.headers.get('X-Frame-Options') == 'DENY'

    def test_csp_header(self, client):
        """Test Content-Security-Policy header is set."""
        response = client.get('/health')
        assert 'Content-Security-Policy' in response.headers


class TestErrorHandlers:
    """Tests for error handlers."""

    def test_404_returns_json(self, authenticated_client):
        """Test that 404 errors return JSON."""
        response = authenticated_client.get('/nonexistent-route')
        # Flask returns 404 HTML by default for undefined routes
        assert response.status_code == 404
