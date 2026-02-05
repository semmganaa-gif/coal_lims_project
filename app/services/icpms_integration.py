# -*- coding: utf-8 -*-
"""
ICPMS Integration Service

LIMS-ээс ICPMS систем рүү өгөгдөл илгээх service.
- CHPP нэгжийн дээж болон шинжилгээний үр дүн
- Washability (Float-Sink) өгөгдөл
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from requests.exceptions import RequestException, Timeout

from app import db
from app.models import Sample, AnalysisResult
from app.utils.conversions import calculate_all_conversions
from app.utils.parameters import PARAMETER_DEFINITIONS, get_canonical_name

logger = logging.getLogger(__name__)


class ICPMSIntegrationError(Exception):
    """ICPMS интеграцийн алдаа"""
    pass


class ICPMSIntegration:
    """
    ICPMS системтэй холбогдох интеграцийн класс.

    Тохиргоо (.env):
        ICPMS_API_URL: ICPMS API-ийн URL (default: http://localhost:8000)
        ICPMS_API_KEY: API key (optional)
        ICPMS_TIMEOUT: Timeout секундээр (default: 30)
    """

    def __init__(self):
        self.base_url = os.getenv('ICPMS_API_URL', 'http://localhost:8000')
        self.api_key = os.getenv('ICPMS_API_KEY', '')
        self.timeout = int(os.getenv('ICPMS_TIMEOUT', '30'))
        self._token = None

    def _get_headers(self) -> Dict[str, str]:
        """HTTP headers"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Source': 'COAL-LIMS'
        }
        if self._token:
            headers['Authorization'] = f'Bearer {self._token}'
        elif self.api_key:
            headers['X-API-Key'] = self.api_key
        return headers

    def authenticate(self, username: str = None, password: str = None) -> bool:
        """
        ICPMS API-д нэвтрэх.

        Args:
            username: Хэрэглэгчийн нэр (default: env ICPMS_USERNAME)
            password: Нууц үг (default: env ICPMS_PASSWORD)

        Returns:
            True амжилттай бол
        """
        username = username or os.getenv('ICPMS_USERNAME', 'lims_service')
        password = password or os.getenv('ICPMS_PASSWORD', '')

        try:
            response = requests.post(
                f'{self.base_url}/api/auth/login',
                json={'username': username, 'password': password},
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                self._token = data.get('access_token')
                logger.info("ICPMS-д амжилттай нэвтэрлээ")
                return True
            else:
                logger.error(f"ICPMS нэвтрэх алдаа: {response.status_code}")
                return False

        except RequestException as e:
            logger.error(f"ICPMS холболтын алдаа: {e}")
            return False

    def check_connection(self) -> Dict[str, Any]:
        """
        ICPMS холболтыг шалгах.

        Returns:
            {"status": "ok/error", "message": str, "version": str}
        """
        try:
            # ICPMS root endpoint шалгах (/ эсвэл /health)
            response = requests.get(
                f'{self.base_url}/',
                timeout=5
            )

            if response.status_code == 200:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                return {
                    "status": "ok",
                    "message": "ICPMS холболт амжилттай",
                    "url": self.base_url,
                    "version": data.get("version", "unknown")
                }
            else:
                return {
                    "status": "error",
                    "message": f"ICPMS хариу: {response.status_code}",
                    "url": self.base_url
                }

        except Timeout:
            return {
                "status": "error",
                "message": "ICPMS холболт timeout",
                "url": self.base_url
            }
        except RequestException as e:
            return {
                "status": "error",
                "message": f"Холбогдож чадсангүй: {str(e)}",
                "url": self.base_url
            }

    def send_sample_results(
        self,
        sample_ids: List[int],
        include_washability: bool = True
    ) -> Dict[str, Any]:
        """
        Дээж болон шинжилгээний үр дүнг ICPMS руу илгээх.

        Args:
            sample_ids: Илгээх дээжний ID-ууд
            include_washability: Washability өгөгдөл оруулах эсэх

        Returns:
            {"success": bool, "sent_count": int, "errors": list}
        """
        if not sample_ids:
            return {"success": False, "sent_count": 0, "errors": ["Дээж сонгоогүй байна"]}

        results = {
            "success": True,
            "sent_count": 0,
            "errors": [],
            "icpms_ids": []
        }

        # Дээжүүдийг авах
        samples = Sample.query.filter(Sample.id.in_(sample_ids)).all()

        if not samples:
            results["success"] = False
            results["errors"].append("Дээж олдсонгүй")
            return results

        for sample in samples:
            try:
                payload = self._build_sample_payload(sample, include_washability)

                response = requests.post(
                    f'{self.base_url}/api/lims/samples',
                    headers=self._get_headers(),
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    results["sent_count"] += 1
                    results["icpms_ids"].append(data.get('id'))
                    logger.info(f"Дээж #{sample.id} ICPMS руу илгээгдлээ")
                else:
                    error_msg = f"Дээж #{sample.id}: {response.status_code} - {response.text[:200]}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            except RequestException as e:
                error_msg = f"Дээж #{sample.id}: Холболтын алдаа - {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)

        if results["errors"]:
            results["success"] = results["sent_count"] > 0

        return results

    def _build_sample_payload(
        self,
        sample: Sample,
        include_washability: bool = True
    ) -> Dict[str, Any]:
        """
        Дээжний өгөгдлийг ICPMS форматруу хөрвүүлэх.

        Args:
            sample: Sample объект
            include_washability: Washability оруулах эсэх

        Returns:
            ICPMS API-д зориулсан payload
        """
        # Батлагдсан шинжилгээний үр дүнгүүд
        analysis_results = AnalysisResult.query.filter(
            AnalysisResult.sample_id == sample.id,
            AnalysisResult.status == 'approved'
        ).all()

        # Үр дүнгүүдийг dict руу хөрвүүлэх
        results_dict = {}
        canonical_results = {}
        for r in analysis_results:
            results_dict[r.analysis_code] = {
                'value': r.final_result,
                'approved_at': r.updated_at.isoformat() if r.updated_at else None
            }
            # Canonical нэрээр мөн хадгалах (тооцоолол хийхэд хэрэглэгдэнэ)
            canonical_name = get_canonical_name(r.analysis_code)
            if canonical_name:
                canonical_results[canonical_name] = {
                    'value': r.final_result,
                    'id': r.id,
                    'status': r.status
                }

        # Тооцоологдсон утгууд (Ad, Vdaf, St,d гэх мэт)
        calculated_values = calculate_all_conversions(canonical_results, PARAMETER_DEFINITIONS)

        # Тооцоологдсон утгуудыг results_dict-д нэмэх
        calculated_mapping = {
            'Ad': 'ash_d',
            'Vdaf': 'volatile_matter_daf',
            'FC,ad': 'fixed_carbon_ad',
            'FC,d': 'fixed_carbon_d',
            'St,d': 'total_sulfur_d',
            'TRD,d': 'relative_density_d',
            'Qgr,d': 'calorific_value_d',
            'Qnet,ar': 'qnet_ar',
            'P,d': 'phosphorus_d'
        }
        for display_code, calc_key in calculated_mapping.items():
            if calc_key in calculated_values:
                val = calculated_values[calc_key]
                if isinstance(val, dict):
                    results_dict[display_code] = val
                elif val is not None:
                    results_dict[display_code] = {'value': val, 'status': 'calculated'}

        payload = {
            'source': 'COAL-LIMS',
            'lims_sample_id': sample.id,
            'sample_code': sample.sample_code,
            'client_name': sample.client_name,
            'sample_type': sample.sample_type,
            'sample_date': sample.received_date.isoformat() if sample.received_date else None,
            'prepared_date': sample.prepared_date.isoformat() if sample.prepared_date else None,
            'weight': sample.weight,
            'notes': sample.notes,
            'analysis_results': results_dict,
            'sent_at': datetime.utcnow().isoformat()
        }

        # Washability өгөгдөл нэмэх (хэрэв байвал)
        if include_washability:
            washability_data = self._get_washability_data(sample.id)
            if washability_data:
                payload['washability'] = washability_data

        return payload

    def _get_washability_data(self, sample_id: int) -> Optional[Dict[str, Any]]:
        """
        Washability (Float-Sink) өгөгдөл авах.

        LIMS-д washability өгөгдөл JSON эсвэл тусдаа хүснэгтэд хадгалагдсан байж болно.
        """
        # TODO: Washability өгөгдлийн бүтцээс хамаарч тохируулах
        # Одоогоор Sample.notes эсвэл тусдаа хүснэгтээс авч болно

        sample = Sample.query.get(sample_id)
        if not sample:
            return None

        # Хэрэв JSON форматтай washability өгөгдөл байвал
        if hasattr(sample, 'washability_data') and sample.washability_data:
            try:
                return json.loads(sample.washability_data)
            except json.JSONDecodeError:
                pass

        return None

    def send_batch_results(
        self,
        client_name: str = 'CHPP',
        days_back: int = 7,
        status: str = 'approved'
    ) -> Dict[str, Any]:
        """
        Тодорхой нэгжийн сүүлийн хэдэн хоногийн үр дүнг илгээх.

        Args:
            client_name: Нэгжийн нэр (default: CHPP)
            days_back: Хэдэн хоногийн өмнөх өгөгдөл
            status: Шинжилгээний статус

        Returns:
            Илгээлтийн үр дүн
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Батлагдсан үр дүнтэй дээжүүдийг олох
        sample_ids = db.session.query(Sample.id).join(
            AnalysisResult,
            AnalysisResult.sample_id == Sample.id
        ).filter(
            Sample.client_name == client_name,
            AnalysisResult.status == status,
            AnalysisResult.updated_at >= cutoff_date
        ).distinct().all()

        sample_ids = [s[0] for s in sample_ids]

        if not sample_ids:
            return {
                "success": True,
                "sent_count": 0,
                "message": f"{client_name} нэгжийн илгээх үр дүн олдсонгүй"
            }

        return self.send_sample_results(sample_ids)

    def get_optimization_result(self, scenario_id: int) -> Optional[Dict[str, Any]]:
        """
        ICPMS-ээс оновчлолын үр дүн авах.

        Args:
            scenario_id: ICPMS дээрх scenario ID

        Returns:
            Оновчлолын үр дүн эсвэл None
        """
        try:
            response = requests.get(
                f'{self.base_url}/api/optimization/scenarios/{scenario_id}',
                headers=self._get_headers(),
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Optimization result авахад алдаа: {response.status_code}")
                return None

        except RequestException as e:
            logger.error(f"ICPMS холболтын алдаа: {e}")
            return None


# Singleton instance
_icpms = None


def get_icpms_integration() -> ICPMSIntegration:
    """ICPMS integration singleton авах"""
    global _icpms
    if _icpms is None:
        _icpms = ICPMSIntegration()
    return _icpms
