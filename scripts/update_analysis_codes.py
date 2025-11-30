import json
from app import create_app, db
from app.models import Sample, AnalysisType

# Flask Ð¿Ñ€Ð¾Ð³Ñ€Ð°Ð¼Ñ‹Ð½ instance Ò¯Ò¯ÑÐ³ÑÐ¶, database context-Ð´ Ð¾Ñ€Ð¾Ñ…
app = create_app()
app_context = app.app_context()
app_context.push()

print("ÐœÑÐ´ÑÑÐ»Ð»Ð¸Ð¹Ð½ ÑÐ°Ð½Ð³ ÑˆÐ¸Ð½ÑÑ‡Ð»ÑÑ… Ð°Ð¶Ð¸Ð»Ð»Ð°Ð³Ð°Ð° ÑÑ…ÑÐ»Ð»ÑÑ...")

# Ð¥ÑƒÑƒÑ‡Ð¸Ð½ ÐºÐ¾Ð´Ñ‹Ð³ ÑˆÐ¸Ð½Ñ ÐºÐ¾Ð´ Ñ€ÑƒÑƒ Ñ…Ó©Ñ€Ð²Ò¯Ò¯Ð»ÑÑ… Ð³Ð°Ð·Ñ€Ñ‹Ð½ Ð·ÑƒÑ€Ð°Ð³ Ò¯Ò¯ÑÐ³ÑÑ…
print("Ð¥ÑƒÑƒÑ‡Ð¸Ð½ Ð±Ð° ÑˆÐ¸Ð½Ñ ÐºÐ¾Ð´Ñ‹Ð½ Ñ…Ð¾Ð»Ð±Ð¾Ð»Ñ‚Ñ‹Ð³ Ò¯Ò¯ÑÐ³ÑÐ¶ Ð±Ð°Ð¹Ð½Ð°...")
code_mapping = {}
analysis_types = AnalysisType.query.all()
for at in analysis_types:
    # Ð¥ÑƒÑƒÑ‡Ð¸Ð½ ÐºÐ¾Ð´ (analysis_X) Ð¾Ð»Ð´Ð¾Ñ…Ð³Ò¯Ð¹ Ð±Ð¾Ð» order_num-Ð³ Ð°ÑˆÐ¸Ð³Ð»Ð°Ð½ Ñ‚Ð°Ð°Ð¼Ð°Ð³Ð»Ð°Ñ…
    # Ð­Ð½Ñ Ñ…ÑÑÑÐ³ Ð½ÑŒ _seed_analysis_types Ð·Ó©Ð² Ð°Ð¶Ð¸Ð»Ð»Ð°ÑÐ°Ð½ Ð³ÑÐ¶ Ò¯Ð·ÑÐ¶ Ð±Ð°Ð¹Ð½Ð°
    old_code_key = f'analysis_{at.order_num}'
    if at.code != old_code_key: # Ð¨Ð¸Ð½Ñ ÐºÐ¾Ð´ Ñ…ÑƒÑƒÑ‡Ð¸Ð½ ÐºÐ¾Ð´Ð¾Ð¾Ñ Ó©Ó©Ñ€ Ð±Ð¾Ð»
         code_mapping[old_code_key] = at.code

if not code_mapping:
    print("ÐšÐ¾Ð´Ñ‹Ð½ Ñ…Ð¾Ð»Ð±Ð¾Ð»Ñ‚ Ð¾Ð»Ð´ÑÐ¾Ð½Ð³Ò¯Ð¹. AnalysisType Ñ…Ò¯ÑÐ½ÑÐ³Ñ‚Ð¸Ð¹Ð³ ÑˆÐ°Ð»Ð³Ð°Ð½Ð° ÑƒÑƒ.")
else:
    print(f"Ð”Ð°Ñ€Ð°Ð°Ñ… Ñ…Ð¾Ð»Ð±Ð¾Ð»Ñ‚Ñ‹Ð³ Ð°ÑˆÐ¸Ð³Ð»Ð°Ð½ ÑˆÐ¸Ð½ÑÑ‡Ð¸Ð»Ð½Ñ: {code_mapping}")

    # Ð‘Ò¯Ñ… Ð´ÑÑÐ¶Ð¸Ð¹Ð³ ÑˆÐ°Ð»Ð³Ð°Ð¶, analyses_to_perform Ñ‚Ð°Ð»Ð±Ð°Ñ€Ñ‹Ð³ ÑˆÐ¸Ð½ÑÑ‡Ð»ÑÑ…
    samples_to_update = Sample.query.filter(Sample.analyses_to_perform.like('%analysis_%')).all()
    updated_count = 0

    if not samples_to_update:
        print("Ð¨Ð¸Ð½ÑÑ‡Ð»ÑÑ… ÑˆÐ°Ð°Ñ€Ð´Ð»Ð°Ð³Ð°Ñ‚Ð°Ð¹ Ð´ÑÑÐ¶ Ð¾Ð»Ð´ÑÐ¾Ð½Ð³Ò¯Ð¹.")
    else:
        print(f"ÐÐ¸Ð¹Ñ‚ {len(samples_to_update)} Ð´ÑÑÐ¶Ð½Ð¸Ð¹ Ð´Ð°Ð°Ð»Ð³Ð°Ð²Ñ€Ñ‹Ð³ ÑˆÐ¸Ð½ÑÑ‡Ð¸Ð»Ð¶ Ð±Ð°Ð¹Ð½Ð°...")
        for sample in samples_to_update:
            try:
                # ÐžÐ´Ð¾Ð¾ Ð±Ð°Ð¹Ð³Ð°Ð° JSON string-Ð³ Python list Ð±Ð¾Ð»Ð³Ð¾Ñ…
                current_analyses = json.loads(sample.analyses_to_perform or '[]')
                
                # Ð¨Ð¸Ð½Ñ ÐºÐ¾Ð´Ð½ÑƒÑƒÐ´Ð°Ð°Ñ Ð±Ò¯Ñ€Ð´ÑÑÐ½ ÑˆÐ¸Ð½Ñ list Ò¯Ò¯ÑÐ³ÑÑ…
                new_analyses = []
                changed = False
                for code in current_analyses:
                    if code in code_mapping: # Ð¥ÑÑ€ÑÐ² Ñ…ÑƒÑƒÑ‡Ð¸Ð½ ÐºÐ¾Ð´ Ð±Ð°Ð¹Ð²Ð°Ð»
                        new_code = code_mapping[code]
                        new_analyses.append(new_code)
                        changed = True
                        print(f"  - Ð”ÑÑÐ¶ ID={sample.id}: '{code}' -> '{new_code}'")
                    else: # Ð¨Ð¸Ð½Ñ ÐºÐ¾Ð´ ÑÑÐ²ÑÐ» Ñ‚Ð°Ð½Ð¸Ð³Ð´Ð°Ñ…Ð³Ò¯Ð¹ ÐºÐ¾Ð´ Ð±Ð¾Ð» Ñ…ÑÐ²ÑÑÑ€ Ò¯Ð»Ð´ÑÑÑ…
                        new_analyses.append(code)
                
                # Ð¥ÑÑ€ÑÐ² ÑÐ´Ð°Ð¶ Ð½ÑÐ³ ÐºÐ¾Ð´ ÑÐ¾Ð»Ð¸Ð³Ð´ÑÐ¾Ð½ Ð±Ð¾Ð»
                if changed:
                    # Ð¨Ð¸Ð½Ñ list-Ð³ Ð±ÑƒÑ†Ð°Ð°Ð³Ð°Ð°Ð´ JSON string Ð±Ð¾Ð»Ð³Ð¾Ñ…
                    sample.analyses_to_perform = json.dumps(new_analyses)
                    db.session.add(sample) # Ó¨Ó©Ñ€Ñ‡Ð»Ó©Ð»Ñ‚Ð¸Ð¹Ð³ Ñ‚ÑÐ¼Ð´ÑÐ³Ð»ÑÑ…
                    updated_count += 1

            except json.JSONDecodeError:
                print(f"  - ÐÐÐ¥ÐÐÐ : Ð”ÑÑÐ¶ ID={sample.id}-Ð¸Ð¹Ð½ Ð´Ð°Ð°Ð»Ð³Ð°Ð²Ð°Ñ€ ('{sample.analyses_to_perform}') Ð±ÑƒÑ€ÑƒÑƒ Ñ„Ð¾Ñ€Ð¼Ð°Ñ‚Ñ‚Ð°Ð¹ Ñ‚ÑƒÐ» Ð°Ð»Ð³Ð°ÑÐ»Ð°Ð°.")
            except Exception as e:
                 print(f"  - ÐÐ›Ð”ÐÐ: Ð”ÑÑÐ¶ ID={sample.id}-Ð³ ÑˆÐ¸Ð½ÑÑ‡Ð»ÑÑ…ÑÐ´ Ð°Ð»Ð´Ð°Ð° Ð³Ð°Ñ€Ð»Ð°Ð°: {e}")

        # Ð¥ÑÑ€ÑÐ² ÑÐ´Ð°Ð¶ Ð½ÑÐ³ Ð´ÑÑÐ¶ ÑˆÐ¸Ð½ÑÑ‡Ð»ÑÐ³Ð´ÑÑÐ½ Ð±Ð¾Ð» Ð¼ÑÐ´ÑÑÐ»Ð»Ð¸Ð¹Ð½ ÑÐ°Ð½Ð´ Ñ…Ð°Ð´Ð³Ð°Ð»Ð°Ñ…
        if updated_count > 0:
            try:
                db.session.commit()
                print(f"\nÐÐ¼Ð¶Ð¸Ð»Ñ‚Ñ‚Ð°Ð¹: ÐÐ¸Ð¹Ñ‚ {updated_count} Ð´ÑÑÐ¶Ð½Ð¸Ð¹ Ð´Ð°Ð°Ð»Ð³Ð°Ð²Ð°Ñ€ ÑˆÐ¸Ð½ÑÑ‡Ð»ÑÐ³Ð´Ð»ÑÑ.")
            except Exception as e:
                db.session.rollback()
                print(f"\nÐÐ›Ð”ÐÐ: ÐœÑÐ´ÑÑÐ»Ð»Ð¸Ð¹Ð½ ÑÐ°Ð½Ð´ Ñ…Ð°Ð´Ð³Ð°Ð»Ð°Ñ…Ð°Ð´ Ð°Ð»Ð´Ð°Ð° Ð³Ð°Ñ€Ð»Ð°Ð°: {e}")
        else:
            print("\nÐ¨Ð¸Ð½ÑÑ‡Ð»ÑÐ³Ð´ÑÑÐ½ Ð´ÑÑÐ¶ Ð±Ð°Ð¹Ñ…Ð³Ò¯Ð¹.")

# Database context-Ð¾Ð¾Ñ Ð³Ð°Ñ€Ð°Ñ…
app_context.pop()
print("\nÐœÑÐ´ÑÑÐ»Ð»Ð¸Ð¹Ð½ ÑÐ°Ð½Ð³ ÑˆÐ¸Ð½ÑÑ‡Ð»ÑÑ… Ð°Ð¶Ð¸Ð»Ð»Ð°Ð³Ð°Ð° Ð´ÑƒÑƒÑÐ»Ð°Ð°.")
