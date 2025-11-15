from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.feature import Feature as FeatureModel

client = TestClient(app)


class TestFeatureEndpoints:
    def create_mock_feature(
        self, feature_id=1, title="Test Feature", description="Test Description"
    ):
        mock_feature = FeatureModel()
        mock_feature.feature_id = feature_id
        mock_feature.title = title
        mock_feature.description = description
        return mock_feature

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_create_feature_success(self, mock_repo):
        mock_feature = self.create_mock_feature(1, "New Feature", "Feature for testing")
        mock_repo.create_feature = AsyncMock(return_value=mock_feature)

        feature_data = {"title": "New Feature", "description": "Feature for testing"}
        response = client.post("/api/v1/feature/", json=feature_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == feature_data["title"]
        assert data["description"] == feature_data["description"]
        assert data["feature_id"] == 1

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_create_feature_duplicate_title(self, mock_repo):
        mock_repo.create_feature = AsyncMock(
            side_effect=ValueError(
                "Feature с названием 'Duplicate Title' уже существует"
            )
        )

        feature_data = {
            "title": "Duplicate Title",
            "description": "Another description",
        }
        response = client.post("/api/v1/feature/", json=feature_data)

        assert response.status_code == 400
        print(response.json())
        assert "уже существует" in response.json()["detail"]

    def test_create_feature_invalid_data(self):
        response = client.post("/api/v1/feature/", json={"description": "Test"})
        assert response.status_code == 400
        assert "Request validation failed" in response.json()["detail"]

        response = client.post("/api/v1/feature/", json={"title": "Test"})
        assert response.status_code == 400
        assert "Request validation failed" in response.json()["detail"]

        response = client.post(
            "/api/v1/feature/", json={"title": "", "description": ""}
        )
        assert response.status_code == 400
        assert "Request validation failed" in response.json()["detail"]

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_get_features_empty(self, mock_repo):
        mock_repo.get_multi = AsyncMock(return_value=[])

        response = client.get("/api/v1/feature/")

        assert response.status_code == 200
        assert response.json() == []

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_get_features_with_data(self, mock_repo):
        mock_features = [
            self.create_mock_feature(1, "Feature 1", "Description 1"),
            self.create_mock_feature(2, "Feature 2", "Description 2"),
        ]
        mock_repo.get_multi = AsyncMock(return_value=mock_features)

        response = client.get("/api/v1/feature/")

        assert response.status_code == 200
        features = response.json()
        assert len(features) == 2
        assert features[0]["feature_id"] == 1
        assert features[0]["title"] == "Feature 1"
        assert features[1]["feature_id"] == 2
        assert features[1]["title"] == "Feature 2"

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_get_features_with_pagination(self, mock_repo):
        mock_features = [
            self.create_mock_feature(1, "Feature 1", "Description 1"),
            self.create_mock_feature(2, "Feature 2", "Description 2"),
        ]
        mock_repo.get_multi = AsyncMock(return_value=mock_features)

        response = client.get("/api/v1/feature/?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

        mock_repo.get_multi.assert_called_with(
            mock_repo.get_multi.call_args[0][0], 0, 2
        )

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_get_feature_by_id_success(self, mock_repo):
        mock_feature = self.create_mock_feature(1, "Test Feature", "Test Description")
        mock_repo.get = AsyncMock(return_value=mock_feature)

        response = client.get("/api/v1/feature/1")

        assert response.status_code == 200
        data = response.json()
        assert data["feature_id"] == 1
        assert data["title"] == "Test Feature"
        assert data["description"] == "Test Description"

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_get_feature_by_id_not_found(self, mock_repo):
        mock_repo.get = AsyncMock(return_value=None)

        response = client.get("/api/v1/feature/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Feature not found"

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_update_feature_success(self, mock_repo):
        updated_feature = self.create_mock_feature(
            1, "Updated Title", "Updated Description"
        )
        mock_repo.update_feature = AsyncMock(return_value=updated_feature)

        update_data = {"title": "Updated Title", "description": "Updated Description"}
        response = client.put("/api/v1/feature/1", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["feature_id"] == 1
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_update_feature_partial(self, mock_repo):
        updated_feature = self.create_mock_feature(1, "Updated Title", "Original Desc")
        mock_repo.update_feature = AsyncMock(return_value=updated_feature)

        update_data = {"title": "Updated Title"}
        response = client.put("/api/v1/feature/1", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Original Desc"

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_update_feature_not_found(self, mock_repo):
        mock_repo.update_feature = AsyncMock(return_value=None)

        update_data = {"title": "New Title"}
        response = client.put("/api/v1/feature/99999", json=update_data)

        assert response.status_code == 404
        assert response.json()["detail"] == "Feature not found"

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_update_feature_duplicate_title(self, mock_repo):
        mock_repo.update_feature = AsyncMock(
            side_effect=ValueError("Feature с названием 'Feature 1' уже существует")
        )

        update_data = {"title": "Feature 1"}
        response = client.put("/api/v1/feature/2", json=update_data)

        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_delete_feature_success(self, mock_repo):
        deleted_feature = self.create_mock_feature(
            1, "Test Feature", "Test Description"
        )
        mock_repo.remove = AsyncMock(return_value=deleted_feature)

        response = client.delete("/api/v1/feature/1")

        assert response.status_code == 200
        data = response.json()
        assert data["feature_id"] == 1

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_delete_feature_not_found(self, mock_repo):
        mock_repo.remove = AsyncMock(return_value=None)

        response = client.delete("/api/v1/feature/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Feature not found"

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_search_feature_by_title_success(self, mock_repo):
        mock_feature = self.create_mock_feature(1, "Unique Feature", "Description")
        mock_repo.find_by_title = AsyncMock(return_value=[mock_feature])

        response = client.get("/api/v1/feature/search?title=Unique Feature")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Unique Feature"

    @patch("app.api.v1.endpoints.feature.feature_repository")
    def test_search_feature_by_title_not_found(self, mock_repo):
        mock_repo.find_by_title = AsyncMock(return_value=[])

        response = client.get("/api/v1/feature/search?title=Nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
