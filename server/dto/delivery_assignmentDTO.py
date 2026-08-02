class DeliveryAssignmentDTO:
    def __init__(self, id, DistributionCenterID, RecipientID, VolunteerID, amount_of_meals,freshness_priority):
        self.id = id
        self.DistributionCenterID = DistributionCenterID
        self.RecipientID = RecipientID
        self.VolunteerID = VolunteerID
        self.amount_of_meals = amount_of_meals
        self.freshness_priority=freshness_priority