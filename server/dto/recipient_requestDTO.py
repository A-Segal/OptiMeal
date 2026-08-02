class RecipientRequestDTO:
    def __init__(self, id, RecipientID, amount_of_meals, request_date):
        self.id = id
        self.RecipientID = RecipientID
        self.amount_of_meals = amount_of_meals
        self.request_date = request_date