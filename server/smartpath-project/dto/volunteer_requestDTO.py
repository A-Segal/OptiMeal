class VolunteerRequestDTO:
    def __init__(self, id, volunteer_id, location_lat, location_lng, available_time):
        self.id = id
        self.volunteer_id = volunteer_id
        self.location_lat = location_lat
        self.location_lng = location_lng
        self.available_time = available_time