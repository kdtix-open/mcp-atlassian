"""Unit tests for ConfluenceV2Adapter class."""

from unittest.mock import MagicMock, Mock

import pytest
import requests
from requests.exceptions import HTTPError

from mcp_atlassian.confluence.v2_adapter import ConfluenceV2Adapter


class TestConfluenceV2Adapter:
    """Test cases for ConfluenceV2Adapter."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return MagicMock(spec=requests.Session)

    @pytest.fixture
    def v2_adapter(self, mock_session):
        """Create a ConfluenceV2Adapter instance."""
        return ConfluenceV2Adapter(
            session=mock_session, base_url="https://example.atlassian.net/wiki"
        )

    def test_get_page_success(self, v2_adapter, mock_session):
        """Test successful page retrieval."""
        # Mock the v2 API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123456",
            "status": "current",
            "title": "Test Page",
            "spaceId": "789",
            "version": {"number": 5},
            "body": {
                "storage": {"value": "<p>Test content</p>", "representation": "storage"}
            },
            "_links": {"webui": "/pages/viewpage.action?pageId=123456"},
        }
        mock_session.get.return_value = mock_response

        # Mock space key lookup
        space_response = Mock()
        space_response.status_code = 200
        space_response.json.return_value = {"key": "TEST"}
        mock_session.get.side_effect = [mock_response, space_response]

        # Call the method
        result = v2_adapter.get_page("123456")

        # Verify the API call
        assert mock_session.get.call_count == 2
        mock_session.get.assert_any_call(
            "https://example.atlassian.net/wiki/api/v2/pages/123456",
            params={"body-format": "storage"},
        )

        # Verify the response format
        assert result["id"] == "123456"
        assert result["type"] == "page"
        assert result["title"] == "Test Page"
        assert result["space"]["key"] == "TEST"
        assert result["space"]["id"] == "789"
        assert result["version"]["number"] == 5
        assert result["body"]["storage"]["value"] == "<p>Test content</p>"
        assert result["body"]["storage"]["representation"] == "storage"

    def test_get_page_not_found(self, v2_adapter, mock_session):
        """Test page retrieval when page doesn't exist."""
        # Mock a 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Page not found"
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_session.get.return_value = mock_response

        # Call the method and expect an exception
        with pytest.raises(ValueError, match="Failed to get page '999999'"):
            v2_adapter.get_page("999999")

    def test_get_page_with_minimal_response(self, v2_adapter, mock_session):
        """Test page retrieval with minimal v2 response."""
        # Mock the v2 API response without optional fields
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123456",
            "status": "current",
            "title": "Minimal Page",
        }
        mock_session.get.return_value = mock_response

        # Call the method
        result = v2_adapter.get_page("123456")

        # Verify the response handles missing fields gracefully
        assert result["id"] == "123456"
        assert result["type"] == "page"
        assert result["title"] == "Minimal Page"
        assert result["space"]["key"] == "unknown"  # Fallback when no spaceId
        assert result["version"]["number"] == 1  # Default version

    def test_get_page_network_error(self, v2_adapter, mock_session):
        """Test page retrieval with network error."""
        # Mock a network error
        mock_session.get.side_effect = requests.RequestException("Network error")

        # Call the method and expect an exception
        with pytest.raises(ValueError, match="Failed to get page '123456'"):
            v2_adapter.get_page("123456")

    def test_get_page_with_expand_parameter(self, v2_adapter, mock_session):
        """Test that expand parameter is accepted but not used."""
        # Mock the v2 API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123456",
            "status": "current",
            "title": "Test Page",
        }
        mock_session.get.return_value = mock_response

        # Call with expand parameter
        result = v2_adapter.get_page("123456", expand="body.storage,version")

        # Verify the API call doesn't include expand in params
        mock_session.get.assert_called_once_with(
            "https://example.atlassian.net/wiki/api/v2/pages/123456",
            params={"body-format": "storage"},
        )

        # Verify we still get a result
        assert result["id"] == "123456"


class TestConfluenceV2AdapterFullWidth:
    """Test cases for ConfluenceV2Adapter full-width layout functionality."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return MagicMock(spec=requests.Session)

    @pytest.fixture
    def v2_adapter(self, mock_session):
        """Create a ConfluenceV2Adapter instance."""
        return ConfluenceV2Adapter(
            session=mock_session, base_url="https://example.atlassian.net/wiki"
        )

    def test_get_page_full_width_true(self, v2_adapter, mock_session):
        """Test getting full-width setting when page is full-width."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"key": "content-appearance-published", "value": "full-width"},
            ]
        }
        mock_session.get.return_value = mock_response

        result = v2_adapter.get_page_full_width("123456")

        assert result is True
        mock_session.get.assert_called_once_with(
            "https://example.atlassian.net/wiki/api/v2/pages/123456/properties"
        )

    def test_get_page_full_width_false_default(self, v2_adapter, mock_session):
        """Test getting full-width setting when page uses default layout."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"key": "content-appearance-published", "value": "default"},
            ]
        }
        mock_session.get.return_value = mock_response

        result = v2_adapter.get_page_full_width("123456")

        assert result is False

    def test_get_page_full_width_no_property(self, v2_adapter, mock_session):
        """Test getting full-width setting when property is absent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_session.get.return_value = mock_response

        result = v2_adapter.get_page_full_width("123456")

        assert result is False

    def test_get_page_full_width_api_error(self, v2_adapter, mock_session):
        """Test getting full-width setting when API raises an error."""
        mock_session.get.side_effect = Exception("API error")

        result = v2_adapter.get_page_full_width("123456")

        assert result is False

    def test_set_page_full_width_enable(self, v2_adapter, mock_session):
        """Test enabling full-width layout via v2 API."""
        # Mock GET for _get_property (property doesn't exist)
        not_found_response = Mock()
        not_found_response.status_code = 404

        # Mock POST for creating new property
        created_response = Mock()
        created_response.status_code = 200
        created_response.raise_for_status.return_value = None

        mock_session.get.return_value = not_found_response
        mock_session.post.return_value = created_response

        result = v2_adapter.set_page_full_width("123456", full_width=True)

        assert result is True
        # Should have posted both published and draft properties
        assert mock_session.post.call_count == 2
        posted_data = [call[1]["json"] for call in mock_session.post.call_args_list]
        keys = [d["key"] for d in posted_data]
        values = [d["value"] for d in posted_data]
        assert "content-appearance-published" in keys
        assert "content-appearance-draft" in keys
        assert all(v == "full-width" for v in values)

    def test_set_page_full_width_disable(self, v2_adapter, mock_session):
        """Test disabling full-width layout (setting to default) via v2 API."""
        # Mock GET for _get_property (property doesn't exist)
        not_found_response = Mock()
        not_found_response.status_code = 404

        # Mock POST for creating new property
        created_response = Mock()
        created_response.status_code = 200
        created_response.raise_for_status.return_value = None

        mock_session.get.return_value = not_found_response
        mock_session.post.return_value = created_response

        result = v2_adapter.set_page_full_width("123456", full_width=False)

        assert result is True
        posted_data = [call[1]["json"] for call in mock_session.post.call_args_list]
        values = [d["value"] for d in posted_data]
        assert all(v == "default" for v in values)
