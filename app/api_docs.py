# app/api_docs.py
# -*- coding: utf-8 -*-
"""
API Documentation configuration (Swagger/Flasgger)

Swagger UI-ийг /api/docs endpoint дээр харуулна
"""

from flasgger import Swagger


def setup_api_docs(app):
    """
    Swagger API documentation тохируулах

    Usage:
        pip install flasgger

        from app.api_docs import setup_api_docs
        setup_api_docs(app)

        Дараа нь http://localhost:5000/api/docs руу очих
    """
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/api/docs/apispec.json',
                "rule_filter": lambda _rule: True,  # Бүх API-г харуулах
                "model_filter": lambda _tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs/"
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Coal LIMS API",
            "description": "Нүүрсний лабораторийн мэдээллийн удирдлагын системийн API",
            "version": "1.0.0",
            "contact": {
                "name": "Coal LIMS",
                "email": "support@energyresources.mn"
            },
            "license": {
                "name": "Proprietary",
            }
        },
        "host": "localhost:5000",  # Production-д өөрчлөх
        "basePath": "/",
        "schemes": [
            "http",
            "https"
        ],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. "
                               "Example: \"Authorization: Bearer {token}\""
            },
            "SessionAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "session"
            }
        },
        "tags": [
            {
                "name": "Samples",
                "description": "Дээжний API endpoints"
            },
            {
                "name": "Analysis",
                "description": "Шинжилгээний API endpoints"
            },
            {
                "name": "Mass",
                "description": "Массын ажлын талбарын endpoints"
            },
            {
                "name": "Equipment",
                "description": "Хэрэгслийн удирдлагын endpoints"
            }
        ]
    }

    swagger = Swagger(app, config=swagger_config, template=swagger_template)

    app.logger.info("Swagger API documentation initialized at /api/docs/")

    return swagger


# Жишээ docstring - API endpoint-д энэ хэлбэрээр нэмнэ
"""
API Endpoint Docstring Example:

@bp.route("/data", methods=["GET"])
@login_required
@limiter.limit("30 per minute")
def data():
    '''
    Get samples for DataTables
    ---
    tags:
      - Samples
    parameters:
      - name: draw
        in: query
        type: integer
        required: true
        description: DataTables draw counter
      - name: start
        in: query
        type: integer
        required: false
        description: Starting record number
      - name: length
        in: query
        type: integer
        required: false
        description: Number of records to return
      - name: dateFilterStart
        in: query
        type: string
        format: date
        required: false
        description: Filter by start date
      - name: dateFilterEnd
        in: query
        type: string
        format: date
        required: false
        description: Filter by end date
    responses:
      200:
        description: Sample list with pagination info
        schema:
          type: object
          properties:
            draw:
              type: integer
            recordsTotal:
              type: integer
            recordsFiltered:
              type: integer
            data:
              type: array
              items:
                type: array
      401:
        description: Unauthorized - login required
      429:
        description: Too many requests - rate limit exceeded
    security:
      - SessionAuth: []
    '''
    # ... implementation
"""
