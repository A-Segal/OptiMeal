from db_connection import get_session
from services.batch_algoritm.main_algoritm import run_full_matching

db = get_session()
try:
    result = run_full_matching(db)
    print('RESULT_TYPE', type(result).__name__)
    print('RESULT_LEN', len(result) if hasattr(result, '__len__') else 'NA')
    if hasattr(result, 'items'):
        print('RESULT_SAMPLE', list(result.items())[:3])
    else:
        print('RESULT_SAMPLE', result)
except Exception as exc:
    print('ERROR_TYPE', type(exc).__name__)
    print('ERROR_MSG', exc)
finally:
    db.close()
