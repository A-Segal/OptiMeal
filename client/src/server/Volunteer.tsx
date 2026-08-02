

import axios from "axios";
import { base_url } from "../config";
import type { Volunteer } from "../model/Volunteer";

export const addVolunteer = async (data: Volunteer) => {
  const res = await axios.post(`${base_url}/volunteers`, data);
  return res.data;
};