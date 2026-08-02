
import axios from "axios";
import { base_url } from "../config";
import type { DC_Request } from "../model/DC_Request";

export const addRequest = async (data: DC_Request) => {
  const res = await axios.post(`${base_url}/dc_requests`, data);
  return res.data;
};

