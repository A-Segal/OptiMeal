export type Recipient = {
  id: number;
  fname: string;
  lname: string;
  username: string;
  password: string;
  mail?: string;
  phone?: string;
  location_lat?: number;
  location_lng?: number;
};