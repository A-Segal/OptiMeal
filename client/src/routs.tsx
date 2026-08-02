import { createBrowserRouter } from "react-router-dom";
import App from "./App";
import RecipientSignUp from "./components/signUp/RecipientSignUp";
import DistributionCenterSignUp from "./components/signUp/DistributionCenterSignUp";
import VolunteerSignUp from "./components/signUp/VolunteerSignUp";
import Login from "./components/Login";

// הוספנו דפים חדשים (תיצור אותם אחר כך כקומפוננטות אמיתיות)
import VolunteerHome from "./components/VolunteerHome";
import RecipientHome from "./components/RecipientHome";
import DCHome from "./components/DCHome";
import StaffHome from "./components/StaffHome";
import EzerMizionStyleGuide from "./components/EzerMizionStyleGuide";

const routes = createBrowserRouter([
  {
    path: "/",
    element: <App />,
  },
  {
    path: "/RecipientSignUp",
    element: <RecipientSignUp />,
  },
  {
    path: "/DistributionCenterSignUp",
    element: <DistributionCenterSignUp />,
  },
  {
    path: "/volunteerSignUp",
    element: <VolunteerSignUp />,
  },
  {
    path: "/login",
    element: <Login />,
  },

  // ===================== HOME ROUTES =====================
  {
    path: "/volunteer-home",
    element: <VolunteerHome />,
  },
  {
    path: "/recipient-home",
    element: <RecipientHome />,
  },
  {
    path: "/dc-home",
    element: <DCHome />,
  },
  {
    path: "/staff-home",
    element: <StaffHome />,
  },
  {
    path: "/ezer-mizion-style-guide",
    element: <EzerMizionStyleGuide />,
  },
]);

export default routes;