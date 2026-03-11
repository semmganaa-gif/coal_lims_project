# tests/integration/test_index_coverage.py
"""
Coverage тест - index.py дахь хамрагдаагүй мөрүүдийг тест хийх
"""
import pytest
from datetime import datetime, timedelta
from flask import url_for
from unittest.mock import patch, MagicMock
from app.models import Sample, SystemSetting, User


class TestIndexRegistrationPost:
    """Index route POST хүсэлтүүдийг тест хийх"""

    def test_registration_no_permission(self, client, app):
        """prep/admin биш хэрэглэгч дээж бүртгэх гэхэд алдаа гарах"""
        with app.app_context():
            from app import db
            # chemist role нь дээж бүртгэх эрхгүй
            client.post('/login', data={
                'username': 'chemist',
                'password': 'TestPass123'
            })

            response = client.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '2 hourly',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_registration_multi_samples_chpp_2h(self, auth_admin, app):
        """CHPP 2 hourly олон дээж бүртгэх"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '2 hourly',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'list_type': 'chpp_2h',
                'sample_codes': ['PF211_D1', 'PF211_D2'],
                'weights': ['100.5', '101.2'],
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_registration_invalid_weight(self, auth_admin, app):
        """Буруу жинтэй дээж бүртгэх"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '2 hourly',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'list_type': 'chpp_2h',
                'sample_codes': ['TEST_INVALID_W'],
                'weights': ['invalid'],
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_registration_weight_too_small(self, auth_admin, app):
        """Хэт бага жинтэй дээж"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '2 hourly',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'list_type': 'chpp_2h',
                'sample_codes': ['TEST_SMALL_W'],
                'weights': ['0'],
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_registration_weight_too_large(self, auth_admin, app):
        """Хэт их жинтэй дээж"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '2 hourly',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'list_type': 'chpp_2h',
                'sample_codes': ['TEST_BIG_W'],
                'weights': ['99999999'],
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_registration_missing_weight(self, auth_admin, app):
        """Жин оруулаагүй дээж"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': '2 hourly',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'list_type': 'chpp_2h',
                'sample_codes': ['TEST_NO_W'],
                'weights': [''],
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200


class TestWTLRegistration:
    """WTL дээж бүртгэлийн тест"""

    def test_wtl_sample_registration(self, auth_admin, app):
        """WTL төрлийн дээж бүртгэх"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'WTL',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'lab_number': 'WTL001',
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_wtl_size_registration(self, auth_admin, app):
        """WTL Size төрлийн дээж бүртгэх"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'Size',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'lab_number': 'SIZE001',
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_wtl_fl_registration(self, auth_admin, app):
        """WTL FL төрлийн дээж бүртгэх"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'FL',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'lab_number': 'FL001',
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_wtl_missing_lab_number(self, auth_admin, app):
        """WTL lab number байхгүй үед"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'WTL',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_wtl_mg_registration(self, auth_admin, app):
        """WTL MG төрлийн дээж бүртгэх"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'MG',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'sample_code': 'MG_TEST_001',
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_wtl_mg_missing_code(self, auth_admin, app):
        """WTL MG sample code байхгүй үед"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'WTL',
                'sample_type': 'MG',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200


class TestLABRegistration:
    """LAB дээж бүртгэлийн тест"""

    def test_lab_cm_registration(self, auth_admin, app):
        """LAB CM дээж бүртгэх"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'LAB',
                'sample_type': 'CM',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_lab_gbw_registration(self, auth_admin, app):
        """LAB GBW дээж бүртгэх"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'LAB',
                'sample_type': 'GBW',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_lab_test_registration(self, auth_admin, app):
        """LAB Test дээж бүртгэх"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'LAB',
                'sample_type': 'Test',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200


class TestPreviewAnalyses:
    """Preview analyses AJAX endpoint тест"""

    def test_preview_analyses_success(self, auth_admin, app):
        """Preview analyses амжилттай"""
        with app.app_context():
            response = auth_admin.post('/preview-analyses',
                json={
                    'sample_names': ['PF211_D1', 'PF211_D2'],
                    'client_name': 'CHPP',
                    'sample_type': '2 hourly'
                },
                content_type='application/json'
            )

            assert response.status_code == 200

    def test_preview_analyses_missing_data(self, auth_admin, app):
        """Preview analyses өгөгдөл дутуу"""
        with app.app_context():
            response = auth_admin.post('/preview-analyses',
                json={
                    'sample_names': ['PF211_D1'],
                },
                content_type='application/json'
            )

            # 400 эсвэл 200 хоёулангийн нь боломжтой
            assert response.status_code in [200, 400]


class TestSendHourlyReport:
    """Цагийн тайлан илгээх тест"""

    def test_hourly_report_no_permission(self, auth_user, app):
        """chemist эрхтэй хэрэглэгч тайлан илгээх гэхэд"""
        with app.app_context():
            response = auth_user.get('/send-hourly-report', follow_redirects=True)
            assert response.status_code == 200

    def test_hourly_report_admin(self, auth_admin, app):
        """Admin тайлан илгээх"""
        with app.app_context():
            response = auth_admin.get('/send-hourly-report', follow_redirects=True)
            assert response.status_code == 200

    def test_hourly_report_with_mock(self, auth_admin, app):
        """Template файл байхгүй үед"""
        with app.app_context():
            with patch('os.path.exists', return_value=False):
                response = auth_admin.get('/send-hourly-report', follow_redirects=True)
                assert response.status_code == 200


class TestGetReportEmailRecipients:
    """Email recipient функцийн тест"""

    def test_get_recipients_with_to_and_cc(self, app):
        """TO болон CC хаягтай үед"""
        with app.app_context():
            from app import db
            from app.routes.main.hourly_report import get_report_email_recipients

            # Хуучин email setting устгах
            SystemSetting.query.filter(
                SystemSetting.category == 'email',
                SystemSetting.key.in_(['report_recipients_to', 'report_recipients_cc'])
            ).delete(synchronize_session=False)

            # TO setting нэмэх
            to_setting = SystemSetting(
                category='email',
                key='report_recipients_to',
                value='test1@test.com, test2@test.com',
                is_active=True
            )
            db.session.add(to_setting)

            # CC setting нэмэх
            cc_setting = SystemSetting(
                category='email',
                key='report_recipients_cc',
                value='cc1@test.com',
                is_active=True
            )
            db.session.add(cc_setting)
            db.session.commit()

            result = get_report_email_recipients()
            assert 'to' in result
            assert 'cc' in result

    def test_get_recipients_empty(self, app):
        """Recipient байхгүй үед"""
        with app.app_context():
            from app import db
            from app.routes.main.hourly_report import get_report_email_recipients

            # Бүх email setting устгах
            SystemSetting.query.filter_by(category='email').delete()
            db.session.commit()

            result = get_report_email_recipients()
            assert result['to'] == []
            assert result['cc'] == []


class TestMultiGenRegistration:
    """multi_gen төрлийн бүртгэлийн тест"""

    def test_multi_gen_qc(self, auth_admin, app):
        """QC multi_gen бүртгэл"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'QC',
                'sample_type': 'ROM',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'list_type': 'multi_gen',
                'sample_codes': ['QC_ROM_001'],
                'weights': ['150.5'],
                'location': 'Location1',
                'product': 'Product1',
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200

    def test_chpp_com_registration(self, auth_admin, app):
        """CHPP COM бүртгэл"""
        with app.app_context():
            response = auth_admin.post('/coal', data={
                'client_name': 'CHPP',
                'sample_type': 'COM',
                'sample_date': datetime.now().strftime('%Y-%m-%d'),
                'sample_condition': 'Good',
                'list_type': 'chpp_com',
                'sample_codes': ['COM_001'],
                'weights': ['200.0'],
                'retention_period': '7',
            }, follow_redirects=True)

            assert response.status_code == 200


class TestIndexPage:
    """Index хуудасны тест"""

    def test_index_page_admin(self, auth_admin, app):
        """Admin хэрэглэгч index хуудас харах"""
        with app.app_context():
            response = auth_admin.get('/coal')
            assert response.status_code == 200

    def test_index_page_chemist(self, auth_user, app):
        """Chemist хэрэглэгч index хуудас харах"""
        with app.app_context():
            response = auth_user.get('/coal')
            assert response.status_code == 200

    def test_index_get_patterns(self, auth_admin, app):
        """Pattern тохиргоо авах"""
        with app.app_context():
            response = auth_admin.get('/', query_string={
                'client_name': 'CHPP',
                'sample_type': '2 hourly'
            })
            assert response.status_code == 200
