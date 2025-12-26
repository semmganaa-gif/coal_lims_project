# -*- coding: utf-8 -*-
"""
Tests for app/api_docs.py
Swagger API documentation tests
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSetupApiDocs:
    """setup_api_docs function tests"""

    def test_import(self):
        """Import function"""
        from app.api_docs import setup_api_docs
        assert callable(setup_api_docs)

    def test_returns_swagger_instance(self):
        """Returns Swagger instance"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        with patch('app.api_docs.Swagger') as mock_swagger:
            mock_swagger_instance = MagicMock()
            mock_swagger.return_value = mock_swagger_instance

            result = setup_api_docs(mock_app)

            assert result == mock_swagger_instance

    def test_swagger_called_with_app(self):
        """Swagger called with app"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        with patch('app.api_docs.Swagger') as mock_swagger:
            setup_api_docs(mock_app)

            mock_swagger.assert_called_once()
            args, kwargs = mock_swagger.call_args
            assert args[0] == mock_app

    def test_swagger_config_has_specs_route(self):
        """Config has specs_route"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        with patch('app.api_docs.Swagger') as mock_swagger:
            setup_api_docs(mock_app)

            args, kwargs = mock_swagger.call_args
            config = kwargs.get('config', {})
            assert config.get('specs_route') == '/api/docs/'

    def test_swagger_config_has_swagger_ui(self):
        """Config has swagger_ui enabled"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        with patch('app.api_docs.Swagger') as mock_swagger:
            setup_api_docs(mock_app)

            args, kwargs = mock_swagger.call_args
            config = kwargs.get('config', {})
            assert config.get('swagger_ui') is True

    def test_swagger_template_has_info(self):
        """Template has info section"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        with patch('app.api_docs.Swagger') as mock_swagger:
            setup_api_docs(mock_app)

            args, kwargs = mock_swagger.call_args
            template = kwargs.get('template', {})
            assert 'info' in template
            assert template['info']['title'] == 'Coal LIMS API'

    def test_swagger_template_has_version(self):
        """Template has version"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        with patch('app.api_docs.Swagger') as mock_swagger:
            setup_api_docs(mock_app)

            args, kwargs = mock_swagger.call_args
            template = kwargs.get('template', {})
            assert template['info']['version'] == '1.0.0'

    def test_swagger_template_has_security_definitions(self):
        """Template has security definitions"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        with patch('app.api_docs.Swagger') as mock_swagger:
            setup_api_docs(mock_app)

            args, kwargs = mock_swagger.call_args
            template = kwargs.get('template', {})
            assert 'securityDefinitions' in template
            assert 'Bearer' in template['securityDefinitions']
            assert 'SessionAuth' in template['securityDefinitions']

    def test_swagger_template_has_tags(self):
        """Template has tags"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        with patch('app.api_docs.Swagger') as mock_swagger:
            setup_api_docs(mock_app)

            args, kwargs = mock_swagger.call_args
            template = kwargs.get('template', {})
            assert 'tags' in template
            tag_names = [t['name'] for t in template['tags']]
            assert 'Samples' in tag_names
            assert 'Analysis' in tag_names

    def test_logs_initialization(self):
        """Logs initialization message"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_logger = MagicMock()
        mock_app.logger = mock_logger

        with patch('app.api_docs.Swagger'):
            setup_api_docs(mock_app)

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert 'Swagger' in call_args or 'api/docs' in call_args

    def test_swagger_config_has_specs(self):
        """Config has specs"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        with patch('app.api_docs.Swagger') as mock_swagger:
            setup_api_docs(mock_app)

            args, kwargs = mock_swagger.call_args
            config = kwargs.get('config', {})
            assert 'specs' in config
            assert len(config['specs']) > 0

    def test_swagger_template_has_schemes(self):
        """Template has http/https schemes"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        with patch('app.api_docs.Swagger') as mock_swagger:
            setup_api_docs(mock_app)

            args, kwargs = mock_swagger.call_args
            template = kwargs.get('template', {})
            assert 'schemes' in template
            assert 'http' in template['schemes']
            assert 'https' in template['schemes']

    def test_swagger_template_swagger_version(self):
        """Template has swagger version 2.0"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        with patch('app.api_docs.Swagger') as mock_swagger:
            setup_api_docs(mock_app)

            args, kwargs = mock_swagger.call_args
            template = kwargs.get('template', {})
            assert template.get('swagger') == '2.0'

    def test_swagger_config_static_url_path(self):
        """Config has static_url_path"""
        from app.api_docs import setup_api_docs

        mock_app = MagicMock()
        mock_app.logger = MagicMock()

        with patch('app.api_docs.Swagger') as mock_swagger:
            setup_api_docs(mock_app)

            args, kwargs = mock_swagger.call_args
            config = kwargs.get('config', {})
            assert config.get('static_url_path') == '/flasgger_static'
