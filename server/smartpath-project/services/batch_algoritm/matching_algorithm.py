from repository.distribution_centerRepository import DistributionCenterRepository
from repository.recipientRepository import RecipientRepository
from repository.DC_request_Repository import DCRequestRepository
from repository.recipient_request_repository import RecipientRequestRepository
from services.utils.googleMaps import distance_between_points
from datetime import date




#the func get the params and return the score
def calculate_match_score(
    center_meals: int,
    recipient_meals: int,
    distance: float,
    meal_type: int = 0
) -> float:
    """
    Calculate match score.

    Lower score = better match.
    """

    distance_ratio = distance / 100

    remaining_meals_ratio = (
        center_meals - recipient_meals
    ) / center_meals

    if meal_type == 1:
        meal_type_weight = 0.35
        meal_type_distance_bias = min(distance_ratio, 1.0) * 0.2
    else:
        meal_type_weight = 0.12
        meal_type_distance_bias = min(distance_ratio, 1.0) * 0.05

    score = (
        distance_ratio * (0.8 + meal_type_distance_bias)
        +
        remaining_meals_ratio * (0.2 - meal_type_weight)
        +
        meal_type_weight
    )

    return score


#the func create Dictionary of the filter meals and max dist that the key:CenterID and the value is: not sort list of object :(RecipientID, Score)
def build_candidates_for_centers(db,max_distance_km=100):
    """
    Dictionary<
        CenterID,
        List<
            (
                RecipientID,
                Score,
                RecipientMeals,
                CenterMeals
            )
        >
    >
    """

    center_repo = DistributionCenterRepository(db)
    recipient_repo = RecipientRepository(db)
    ds_request_repo = DCRequestRepository(db)
    recipient_request_repo = RecipientRequestRepository(db)

    centers = center_repo.get_all_distribution_centers()
    recipients = recipient_repo.get_all_recipients()

    center_requests = ds_request_repo.get_all_requests()
    recipient_requests = recipient_request_repo.get_all_requests()
    today = date.today()

    recipient_requests = [
        request for request in recipient_requests
        if request.request_date and request.request_date.date() == today
    ]

    center_requests_dict = {
        request.DistributionCenterID: request
        for request in center_requests
    }

    recipient_requests_dict = {
        request.RecipientID: request
        for request in recipient_requests
    }

    candidates_by_center = {}

    for center in centers:

        candidates_by_center[center.id] = []

        center_request = center_requests_dict.get(center.id)

        if center_request is None:
            continue

        center_meals = center_request.amount_of_meals

        for recipient in recipients:

            recipient_request = recipient_requests_dict.get(
                recipient.id
            )

            if recipient_request is None:
                continue

            if recipient.location_lat is None or recipient.location_lng is None:
                continue

            recipient_meals = (
                recipient_request.amount_of_meals
            )

            meal_type = getattr(center_request, "type", 0) or 0

            if recipient_meals > center_meals:
                continue

            distance = distance_between_points(
                float(center.location_lat),
                float(center.location_lng),
                float(recipient.location_lat),
                float(recipient.location_lng)
            )

            if distance > max_distance_km:
                continue

            score = calculate_match_score(
                center_meals=center_meals,
                recipient_meals=recipient_meals,
                distance=distance,
                meal_type=meal_type
            )

            candidates_by_center[center.id].append(
                (
                    recipient.id,
                    score,
                    recipient_meals,
                    center_meals,
                    meal_type
                )
            )

    return candidates_by_center

#the func get the all candidates_by_center and sort to every center their list.
def sort_center_candidates(candidates_by_center):
    """
    Sort each center's candidates list by score (ascending).
    Lower score = better match.
    """

    for center_id, candidates in candidates_by_center.items():

        # sort only this center's list
        candidates.sort(key=lambda x: x[1])

    return candidates_by_center






#############################step 2 in algorithm#########################

## the func Builds a summary for each center containing its first assigned recipient and the total meals already allocated.
def build_center_usage(recipient_assignment):
    """
    Build summary for each center containing:
    - the first assigned recipient (based on the actual assignment order)
    - total meals already allocated

    recipient_assignment must include 'order' for each recipient:
    {
        recipient_id: {
            "center_id": CenterID,
            "recipient_meals": int,
            "score": float,
            "center_meals": int,
            "order": int  # order of assignment
        }
    }

    Returns:
        Dictionary<
            CenterID,
            {
                "first_recipient_id": RecipientID,
                "used_meals": int
            }
        >
    """

    center_usage = {}

    # Sort assignments by the order of shibutz (step_counter)
    sorted_assignments = sorted(
        recipient_assignment.items(),
        key=lambda x: x[1].get("order", 0)
    )

    for recipient_id, assignment in sorted_assignments:
        center_id = assignment["center_id"]
        recipient_meals = assignment["recipient_meals"]

        if center_id not in center_usage:
            center_usage[center_id] = {
                "first_recipient_id": recipient_id,
                "used_meals": recipient_meals
            }
        else:
            center_usage[center_id]["used_meals"] += recipient_meals

    return center_usage



# the func build list of recipients that did not get assignment
def get_unassigned_recipients(
    recipient_requests_dict,
    recipient_assignment
):
    """
    Return all recipients that were not assigned
    in the first Gale-Shapley phase.
    """

    return [
        r_id
        for r_id in recipient_requests_dict.keys()
        if r_id not in recipient_assignment
    ]


#the func calculate how many meals remain in each used center
def build_remaining_meals_by_center(
    center_usage,
    ds_requests_dict
):
    """
    Dictionary<
        CenterID,
        RemainingMeals
    >
    """

    remaining_meals_by_center = {}

    for center_id, usage in center_usage.items():

        ds_request = ds_requests_dict.get(center_id)

        if ds_request is None:
            continue

        original_meals = ds_request.amount_of_meals
        used_meals = usage["used_meals"]

        remaining_meals_by_center[center_id] = (
            original_meals - used_meals
        )

    return remaining_meals_by_center





#the func calc the score

def calculate_second_phase_score(
    remaining_meals: int,
    recipient_meals: int,
    distance: float,
    meal_type: int = 0
) -> float:

    # אם אין מספיק ארוחות → סקור גבוה מאוד כדי למנוע הקצאה
    if remaining_meals < recipient_meals:
        return float('inf')

    # נורמליזציה למרחק (עד 100 ק"מ)
    distance_ratio = min(distance / 100, 1.0)

    # כמה מהארוחות נשארו אחרי ההקצאה
    remaining_ratio = (remaining_meals - recipient_meals) / remaining_meals

    if meal_type == 1:
        meal_type_weight = 0.3
        distance_bias = min(distance / 100, 1.0) * 0.2
    else:
        meal_type_weight = 0.1
        distance_bias = min(distance / 100, 1.0) * 0.05

    # ציון קטן = טוב יותר
    score = distance_ratio * (0.8 + distance_bias) + (1 - remaining_ratio) * (0.2 - meal_type_weight) + meal_type_weight

    return score



# Build all valid second-phase recipient candidates for each already-used center based on remaining meals, distance from the first assigned recipient, and recalculated score.
def build_second_phase_candidates(
    db,
    center_usage,
    remaining_meals_by_center,
    unassigned_recipients,
    ds_requests_dict,
    max_distance_km=10
):

    center_repo = DistributionCenterRepository(db)
    recipient_repo = RecipientRepository(db)
    recipient_request_repo = RecipientRequestRepository(db)

    recipients = recipient_repo.get_all_recipients()
    recipient_requests = recipient_request_repo.get_all_requests()
    today = date.today()

    recipient_requests = [
        request for request in recipient_requests
        if request.request_date and request.request_date.date() == today
    ]

    recipients_dict = {r.id: r for r in recipients}
    recipient_requests_dict = {r.RecipientID: r for r in recipient_requests}

    new_candidates_by_center = {}

    for center_id, usage in center_usage.items():

        new_candidates_by_center[center_id] = []

        remaining_meals = remaining_meals_by_center.get(center_id, 0)
        if remaining_meals <= 0:
            continue

        first_recipient_id = usage["first_recipient_id"]
        first_recipient = recipients_dict[first_recipient_id]

        if first_recipient.location_lat is None or first_recipient.location_lng is None:
            continue

        for recipient_id in unassigned_recipients:

            recipient_request = recipient_requests_dict.get(recipient_id)
            if recipient_request is None:
                continue

            recipient_meals = recipient_request.amount_of_meals
            meal_type = getattr(ds_requests_dict.get(center_id), "type", 0) or 0




            if recipient_meals > remaining_meals:
                continue

            recipient = recipients_dict[recipient_id]

            if recipient.location_lat is None or recipient.location_lng is None:
                continue

            distance = distance_between_points(
                float(first_recipient.location_lat),
                float(first_recipient.location_lng),
                float(recipient.location_lat),
                float(recipient.location_lng)
            )



            if distance > max_distance_km:
                continue

            # ✔️ תיקון score (זהה לרעיון של שלב 1)
            distance_ratio = distance / 100
            meals_ratio = (remaining_meals - recipient_meals) / remaining_meals

            score = distance_ratio * 0.8 + meals_ratio * 0.2
            if meal_type == 1:
                score += 0.15 * min(distance / 100, 1.0)
                score -= 0.05 * (1 - meals_ratio)
            else:
                score += 0.04 * min(distance / 100, 1.0)

            new_candidates_by_center[center_id].append(
                (
                    recipient_id,
                    score,
                    recipient_meals,
                    remaining_meals,
                    meal_type
                )
            )

    return new_candidates_by_center