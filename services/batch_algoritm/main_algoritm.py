from collections import deque
from repository.recipient_request_repository import RecipientRequestRepository
from repository.DC_request_Repository import DCRequestRepository
from services.batch_algoritm.matching_algorithm import (
    build_candidates_for_centers,
    sort_center_candidates,
    build_center_usage,
    build_remaining_meals_by_center,
    build_second_phase_candidates
)

MAX_RECIPIENTS_PER_CENTER = 2  # הגבלה: עד 2 נזקקים למרכז


def run_full_matching(db):

    # =========================
    # שלב 1: מועמדים ושיבוץ ראשוני
    # =========================
    candidates = build_candidates_for_centers(db)
    candidates = sort_center_candidates(candidates)

    queue = deque(candidates.keys())
    current_index = {center_id: 0 for center_id in candidates}
    recipient_assignment = {}
    step_counter = 0

    # track meals used per center + recipient count
    center_used_meals = {cid: 0 for cid in candidates}
    center_recipient_count = {cid: 0 for cid in candidates}

    recipient_request_repo = RecipientRequestRepository(db)
    recipient_requests = recipient_request_repo.get_all_requests()
    total_recipients = len(recipient_requests)

    recipient_requests_dict = {r.RecipientID: r for r in recipient_requests}

    dc_request_repo = DCRequestRepository(db)
    dc_requests = dc_request_repo.get_all_requests()
    dc_requests_dict = {r.DistributionCenterID: r for r in dc_requests}

    while queue and len(recipient_assignment) < total_recipients:
        center_id = queue.popleft()
        idx = current_index[center_id]

        if idx >= len(candidates[center_id]):
            continue

        recipient_id, score, recipient_meals, center_meals = candidates[center_id][idx]

        # check: center has enough remaining meals
        dc_req = dc_requests_dict.get(center_id)
        original_meals = dc_req.amount_of_meals if dc_req else center_meals
        used = center_used_meals.get(center_id, 0)
        if used + recipient_meals > original_meals:
            current_index[center_id] += 1
            queue.append(center_id)
            continue

        # check: center hasn't reached max recipients (unless stealing)
        current_count = center_recipient_count.get(center_id, 0)

        if recipient_id not in recipient_assignment:
            # new assignment — must be under max
            if current_count >= MAX_RECIPIENTS_PER_CENTER:
                current_index[center_id] += 1
                queue.append(center_id)
                continue

            freshness_priority = (
                dc_requests_dict[center_id].freshness_priority
                if center_id in dc_requests_dict else 0
            )

            recipient_assignment[recipient_id] = {
                "center_id": center_id,
                "score": score,
                "recipient_meals": recipient_meals,
                "center_meals": center_meals,
                "order": step_counter,
                "freshness_priority": freshness_priority
            }
            center_used_meals[center_id] = used + recipient_meals
            center_recipient_count[center_id] = current_count + 1
            step_counter += 1

        else:
            # existing assignment — replace if better
            current_assignment = recipient_assignment[recipient_id]
            old_center = current_assignment["center_id"]
            old_score = current_assignment["score"]

            if score < old_score:
                # check meals for new center
                if center_recipient_count.get(center_id, 0) >= MAX_RECIPIENTS_PER_CENTER:
                    current_index[center_id] += 1
                    queue.append(center_id)
                    continue

                if center_used_meals.get(center_id, 0) + recipient_meals > original_meals:
                    current_index[center_id] += 1
                    queue.append(center_id)
                    continue

                freshness_priority = (
                    dc_requests_dict[center_id].freshness_priority
                    if center_id in dc_requests_dict else 0
                )

                # free old center
                old_meals = current_assignment["recipient_meals"]
                center_used_meals[old_center] -= old_meals
                center_recipient_count[old_center] -= 1

                # assign to new center
                recipient_assignment[recipient_id] = {
                    "center_id": center_id,
                    "score": score,
                    "recipient_meals": recipient_meals,
                    "center_meals": center_meals,
                    "order": step_counter,
                    "freshness_priority": freshness_priority
                }
                center_used_meals[center_id] = center_used_meals.get(center_id, 0) + recipient_meals
                center_recipient_count[center_id] = center_recipient_count.get(center_id, 0) + 1

                step_counter += 1
                current_index[old_center] += 1
                queue.append(old_center)

            else:
                current_index[center_id] += 1
                queue.append(center_id)

    # =========================
    # שלב 2: ניצול עודפי מנות
    # =========================
    center_usage = build_center_usage(recipient_assignment)
    remaining_meals_by_center = build_remaining_meals_by_center(center_usage, dc_requests_dict)

    all_recipients = set(recipient_requests_dict.keys())
    assigned_recipients = set(recipient_assignment.keys())
    unassigned_recipients = list(all_recipients - assigned_recipients)

    second_phase_candidates = build_second_phase_candidates(
        db, center_usage, remaining_meals_by_center, unassigned_recipients
    )
    second_phase_candidates = sort_center_candidates(second_phase_candidates)

    queue = deque(second_phase_candidates.keys())
    current_index = {center_id: 0 for center_id in second_phase_candidates}

    while queue and unassigned_recipients:
        center_id = queue.popleft()

        # don't exceed MAX
        if center_recipient_count.get(center_id, 0) >= MAX_RECIPIENTS_PER_CENTER:
            continue

        idx = current_index[center_id]
        if idx >= len(second_phase_candidates[center_id]):
            continue

        recipient_id, score, recipient_meals, remaining_meals = second_phase_candidates[center_id][idx]

        # check meals
        if center_used_meals.get(center_id, 0) + recipient_meals > dc_requests_dict[center_id].amount_of_meals:
            current_index[center_id] += 1
            queue.append(center_id)
            continue

        if recipient_id not in recipient_assignment:
            freshness_priority = (
                dc_requests_dict[center_id].freshness_priority
                if center_id in dc_requests_dict else 0
            )

            recipient_assignment[recipient_id] = {
                "center_id": center_id,
                "score": score,
                "recipient_meals": recipient_meals,
                "center_meals": remaining_meals,
                "order": step_counter,
                "freshness_priority": freshness_priority
            }
            center_used_meals[center_id] = center_used_meals.get(center_id, 0) + recipient_meals
            center_recipient_count[center_id] = center_recipient_count.get(center_id, 0) + 1
            step_counter += 1
            unassigned_recipients.remove(recipient_id)

        current_index[center_id] += 1
        queue.append(center_id)

    return recipient_assignment
