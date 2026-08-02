
import axios from "axios";
import { base_url } from "../config";
import type { Vehicle } from "../model/Vehicle";

export const addVehicle = async (data: Vehicle) => {
  const res = await axios.post(`${base_url}/vehicles`, data);
  return res.data;
};

export const getVehicleByVolunteer = async (volunteerId: number): Promise<Vehicle | null> => {
  try {
    const res = await axios.post(`${base_url}/vehicles/volunteer/${volunteerId}/fetch`, {});
    return res.data;
  } catch {
    return null;
  }
};

export const updateVehicle = async (vehicleId: number, capacity: number) => {
  const res = await axios.put(`${base_url}/vehicles/id/${vehicleId}`, { capacity });
  return res.data;
};

export const upsertVehicle = async (volunteerId: number, capacity: number) => {
  const res = await axios.put(`${base_url}/vehicles/volunteer/${volunteerId}/upsert`, { capacity });
  return res.data;
};