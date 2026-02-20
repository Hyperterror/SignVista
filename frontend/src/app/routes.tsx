import { createBrowserRouter } from "react-router";
import { Layout } from "./components/Layout";
import { HomePage } from "./pages/HomePage";
import { TextToSignPage } from "./pages/TextToSignPage";
import { VoiceToSignPage } from "./pages/VoiceToSignPage";
import { NotFound } from "./pages/NotFound";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: HomePage },
      { path: "text-to-sign", Component: TextToSignPage },
      { path: "voice-to-sign", Component: VoiceToSignPage },
      { path: "*", Component: NotFound },
    ],
  },
]);
