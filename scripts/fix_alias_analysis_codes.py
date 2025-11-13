import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# scripts/fix_alias_analysis_codes.py
from app import create_app, db
from app.models import AnalysisType, AnalysisResult

def main():
    app = create_app()
    with app.app_context():
        # 1) Base Ñ‚Ó©Ñ€Ð»Ò¯Ò¯Ð´Ð¸Ð¹Ð³ Ð±Ð°Ñ‚Ð°Ð»Ð³Ð°Ð°Ð¶ÑƒÑƒÐ»Ð½Ð° (TS, CV)
        ts = AnalysisType.query.filter_by(code='TS').first()
        if not ts:
            ts = AnalysisType(code='TS', name='Total sulfur', order_num=5, required_role='himich')
            db.session.add(ts)

        cv = AnalysisType.query.filter_by(code='CV').first()
        if not cv:
            cv = AnalysisType(code='CV', name='Calorific value', order_num=6, required_role='himich')
            db.session.add(cv)

        db.session.commit()

        # 2) Alias ÐºÐ¾Ð´Ñ‚Ð¾Ð¹ Ò¯Ñ€ Ð´Ò¯Ð½Ð³Ò¯Ò¯Ð´Ð¸Ð¹Ð³ base ÐºÐ¾Ð´ Ñ€ÑƒÑƒ ÑˆÐ¸Ð»Ð¶Ò¯Ò¯Ð»Ð½Ñ
        db.session.query(AnalysisResult).filter_by(analysis_code='St,ad')\
            .update({'analysis_code': 'TS'}, synchronize_session=False)
        db.session.query(AnalysisResult).filter_by(analysis_code='Qgr,ad')\
            .update({'analysis_code': 'CV'}, synchronize_session=False)
        db.session.commit()

        # 3) Alias Ñ‚Ó©Ñ€Ð»Ò¯Ò¯Ð´Ð¸Ð¹Ð³ ÑƒÑÑ‚Ð³Ð°Ð½Ð° (Ñ…ÑÑ€Ð²ÑÑ Ð±Ð°Ð¹Ð²Ð°Ð»)
        st_ad = AnalysisType.query.filter_by(code='St,ad').first()
        qgr_ad = AnalysisType.query.filter_by(code='Qgr,ad').first()
        if st_ad:
            db.session.delete(st_ad)
        if qgr_ad:
            db.session.delete(qgr_ad)
        db.session.commit()

        print("âœ… Done: alias â†’ base migration complete.")

if __name__ == "__main__":
    main()

