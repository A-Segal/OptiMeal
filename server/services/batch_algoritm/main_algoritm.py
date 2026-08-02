from collections import deque
from datetime import date
from repository.recipient_request_repository import RecipientRequestRepository
from repository.DC_request_Repository import DCRequestRepository
from repository.delivery_assignmentRepository import DeliveryAssignmentRepository
from services.batch_algoritm.matching_algorithm import (
    build_candidates_for_centers,
    sort_center_candidates,
    build_center_usage,
    build_remaining_meals_by_center,
    build_second_phase_candidates
)

def run_full_matching(db):
    delivery_repo = DeliveryAssignmentRepository(db)
    delivery_repo.delete_all_delivery_assignments()

    # =========================
    # שלב 1: מועמדים ושיבוץ ראשוני
    # =========================
    candidates = build_candidates_for_centers(db)
    candidates = sort_center_candidates(candidates)



    queue = deque(candidates.keys())
    current_index = {center_id: 0 for center_id in candidates}
    recipient_assignment = {}
    center_recipient_count = {}  # track how many recipients each center has
    MAX_RECIPIENTS_PER_CENTER = 2
    step_counter = 0

    recipient_request_repo = RecipientRequestRepository(db)
    recipient_requests = recipient_request_repo.get_all_requests()

    today = date.today()
    today_recipient_requests = [
        request for request in recipient_requests
        if request.request_date and request.request_date.date() == today
    ]
    total_recipients = len(today_recipient_requests)

    recipient_requests_dict = {r.RecipientID: r for r in today_recipient_requests}

    # חשוב: נביא את כל ה-DS requests פעם אחת
    dc_request_repo = DCRequestRepository(db)
    dc_requests = dc_request_repo.get_all_requests()



    dc_requests_dict = {
        r.DistributionCenterID: r
        for r in dc_requests
    }

    while queue and len(recipient_assignment) < total_recipients:

        center_id = queue.popleft()

        # Skip centers that already have max recipients
        if center_recipient_count.get(center_id, 0) >= MAX_RECIPIENTS_PER_CENTER:
            continue

        idx = current_index[center_id]

        if idx >= len(candidates[center_id]):
            continue

        recipient_id, score, recipient_meals, center_meals, meal_type = candidates[center_id][idx]

        if recipient_id not in recipient_assignment:

            freshness_priority = (
                dc_requests_dict[center_id].freshness_priority
                if center_id in dc_requests_dict
                else 0
            )

            recipient_assignment[recipient_id] = {
                "center_id": center_id,
                "score": score,
                "recipient_meals": recipient_meals,
                "center_meals": center_meals,
                "meal_type": meal_type,
                "order": step_counter,
                "freshness_priority": freshness_priority
            }

            center_recipient_count[center_id] = center_recipient_count.get(center_id, 0) + 1
            step_counter += 1

        else:
            current_assignment = recipient_assignment[recipient_id]
            old_center = current_assignment["center_id"]
            old_score = current_assignment["score"]

            if score < old_score:
                # Check that the new center isn't already at max capacity
                # (don't count this recipient since we'd move them)
                if center_recipient_count.get(center_id, 0) >= MAX_RECIPIENTS_PER_CENTER:
                    current_index[center_id] += 1
                    queue.append(center_id)
                    continue

                freshness_priority = (
                    dc_requests_dict[center_id].freshness_priority
                    if center_id in dc_requests_dict
                    else 0
                )

                # Decrement old center count
                center_recipient_count[old_center] = max(0, center_recipient_count.get(old_center, 1) - 1)
                # Increment new center count
                center_recipient_count[center_id] = center_recipient_count.get(center_id, 0) + 1

                recipient_assignment[recipient_id] = {
                    "center_id": center_id,
                    "score": score,
                    "recipient_meals": recipient_meals,
                    "center_meals": center_meals,
                    "meal_type": meal_type,
                    "order": step_counter,
                    "freshness_priority": freshness_priority
                }

                step_counter += 1
                current_index[old_center] += 1
                queue.append(old_center)

            else:
                current_index[center_id] += 1
                queue.append(center_id)

    # =========================
    # שלב 2: שיבוץ משני
    # =========================
    center_usage = build_center_usage(recipient_assignment)
    remaining_meals_by_center = build_remaining_meals_by_center(center_usage, dc_requests_dict)

    all_recipients = set(recipient_requests_dict.keys())
    assigned_recipients = set(recipient_assignment.keys())
    unassigned_recipients = list(all_recipients - assigned_recipients)

    second_phase_candidates = build_second_phase_candidates(
        db,
        center_usage,
        remaining_meals_by_center,
        unassigned_recipients,
        dc_requests_dict
    )

    second_phase_candidates = sort_center_candidates(second_phase_candidates)

    queue = deque(second_phase_candidates.keys())
    current_index = {center_id: 0 for center_id in second_phase_candidates}

    while queue and unassigned_recipients:

        center_id = queue.popleft()

        # Skip centers that already have max recipients (from phase 1)
        if center_recipient_count.get(center_id, 0) >= MAX_RECIPIENTS_PER_CENTER:
            continue

        idx = current_index[center_id]

        if idx >= len(second_phase_candidates[center_id]):
            continue

        recipient_id, score, recipient_meals, remaining_meals, meal_type = second_phase_candidates[center_id][idx]

        if recipient_id not in recipient_assignment:

            freshness_priority = (
                dc_requests_dict[center_id].freshness_priority
                if center_id in dc_requests_dict
                else 0
            )

            recipient_assignment[recipient_id] = {
                "center_id": center_id,
                "score": score,
                "recipient_meals": recipient_meals,
                "center_meals": remaining_meals,
                "meal_type": meal_type,
                "order": step_counter,
                "freshness_priority": freshness_priority
            }

            center_recipient_count[center_id] = center_recipient_count.get(center_id, 0) + 1
            step_counter += 1
            unassigned_recipients.remove(recipient_id)

        current_index[center_id] += 1
        queue.append(center_id)

    return {
        "message": "שיבוץ הושלם בהצלחה",
        "created_count": len(recipient_assignment),
        "total_requested_today": total_recipients,
        "unassigned": max(total_recipients - len(recipient_assignment), 0),
        "unique_centers_used": len({assignment["center_id"] for assignment in recipient_assignment.values()}),
        "assignments": recipient_assignment,
    }