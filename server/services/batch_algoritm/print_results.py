# services/batch_algoritm/print_matching.py

from services.utils.googleMaps import distance_between_points
from repository.distribution_centerRepository import DistributionCenterRepository
from repository.recipientRepository import RecipientRepository
from repository.recipient_request_repository import RecipientRequestRepository
from datetime import date


def print_matching_results(db, recipient_assignment):
    """
    מדפיס את תוצאות האלגוריתם לצורך בדיקות בלבד.
    """

    recipient_request_repo = RecipientRequestRepository(db)
    center_repo = DistributionCenterRepository(db)
    recipient_repo = RecipientRepository(db)

    all_requests = recipient_request_repo.get_all_requests()

    today_requests = [
        r for r in all_requests
        if r.request_date.date() == date.today()
    ]

    centers = {c.id: c for c in center_repo.get_all_distribution_centers()}
    recipients = {r.id: r for r in recipient_repo.get_all_recipients()}

    print("\n========== MATCHING RESULT ==========\n")

    for recipient_id, assignment in sorted(recipient_assignment.items()):

        center_id = assignment["center_id"]
        score = assignment["score"]
        recipient_meals = assignment["recipient_meals"]
        center_meals = assignment["center_meals"]

        recipient_obj = recipients.get(recipient_id)
        center_obj = centers.get(center_id)

        distance = distance_between_points(
            float(center_obj.location_lat),
            float(center_obj.location_lng),
            float(recipient_obj.location_lat),
            float(recipient_obj.location_lng)
        )

        print(
            f"Recipient {recipient_id} -> Center {center_id} "
            f"(Score={score:.4f}, Distance={distance:.2f} km) "
            f"| Recipient Meals={recipient_meals} "
            f"| Center Meals={center_meals}"
        )

    print("\n========== STATISTICS ==========\n")

    total_requested = len(today_requests)
    total_assigned = len(recipient_assignment)
    total_unassigned = total_requested - total_assigned

    print(f"Requested today: {total_requested}")
    print(f"Assigned: {total_assigned}")
    print(f"Unassigned: {total_unassigned}")

    assigned_centers = [a["center_id"] for a in recipient_assignment.values()]

    print(f"Unique centers used: {len(set(assigned_centers))}")