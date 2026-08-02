export type DC_Request = {
  id: number;
  DistributionCenterID: number;
  amount_of_meals: number;
  request_date: Date;
  type: number;
  freshness_priority?: number;
};