class DCRequestDTO:
    def __init__(self, id, DistributionCenterID, amount_of_meals, request_date, freshness_priority=0):
        self.id = id
        self.DistributionCenterID = DistributionCenterID
        self.amount_of_meals = amount_of_meals
        self.request_date = request_date
        self.freshness_priority = freshness_priority
