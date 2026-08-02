import axios from "axios";
import { base_url } from "../config";

export interface RunRouteRequest {
  address: string;
  available_time: number; // שעות
}

export const runVolunteerRoute = async (
  volunteerId: number,
  data: RunRouteRequest
) => {
  const res = await axios.post(
    `${base_url}/volunteer_request/run_route/${volunteerId}`,
    data
  );
  return res.data;
};
