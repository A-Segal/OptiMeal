from db_connection import get_session
from services.batch_algoritm.main_algoritm import run_full_matching
from services.batch_algoritm.print_results import print_matching_results

def execute_full_matching():
    """
    מריץ את האלגוריתם ומדפיס תוצאות לצורך בדיקה.
    """
    db = get_session()
    try:
        # מריצים את האלגוריתם
        recipient_assignment = run_full_matching(db)

        # הדפסת תוצאות (debug בלבד)
        # print_matching_results(db, recipient_assignment)

        # מחזירים רק את מה שהפונקציה באמת מחזירה
        return recipient_assignment

    finally:
        db.close()


if __name__ == "__main__":
    # קריאה לפונקציה הראשית
    result = execute_full_matching()