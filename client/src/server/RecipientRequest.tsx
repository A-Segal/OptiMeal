import axios from "axios";
import { base_url } from "../config";
import type { RecipientRequest } from "../model/RecipientRequest";

export const addRecipientRequest = async (data: RecipientRequest) => {
  const res = await axios.post(`${base_url}/recipient_request`, data);
  return res.data;
};