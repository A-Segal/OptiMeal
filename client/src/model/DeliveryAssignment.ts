
export type DeliveryAssignment = {
  id: number;
  DistributionCenterID: number;
  RecipientID: number;
  VolunteerID?: number;
  amount_of_meals?: number;
  type: number;
}